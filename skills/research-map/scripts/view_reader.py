"""Read-only worktree observations shared by the scientific views."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from fnmatch import fnmatchcase
import hashlib
import json
import stat

import policy
from contracts import ContractError
from resources import git


def _plain(path: Path) -> bool:
    return ".." not in path.parts and not any(p.is_symlink() for p in (path, *path.parents))


def _bytes(path: Path) -> bytes:
    if not _plain(path):
        raise PermissionError("Unsupported symbolic link or path traversal")
    if not stat.S_ISREG(path.stat().st_mode):
        raise PermissionError("Expected a regular file")
    return path.read_bytes()


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_state(path: Path) -> str:
    try:
        return _digest(_bytes(path))
    except (FileNotFoundError, NotADirectoryError):
        return "missing"
    except OSError:
        return "unavailable"


def _members(path: Path, pattern: str) -> tuple[Path, ...]:
    if not _plain(path):
        raise PermissionError("Unsupported directory link")
    matches = [path]
    for component in Path(pattern).parts:
        found = []
        for folder in matches:
            if not _plain(folder):
                raise PermissionError("Unsupported directory link")
            try:
                found.extend(entry for entry in folder.iterdir() if fnmatchcase(entry.name, component))
            except (FileNotFoundError, NotADirectoryError):
                continue
        matches = found
    return tuple(sorted(matches))


def _git_identity(root: Path) -> tuple[Path | None, str | None]:
    try:
        toplevel = Path(git(root, "rev-parse", "--show-toplevel").decode().strip())
        if toplevel.resolve() != root:
            return None, None
        git_dir = Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip())
    except (ContractError, OSError, UnicodeError):
        return None, None
    try:
        revision = git(root, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    except (ContractError, OSError, UnicodeError):
        revision = None
    return git_dir, revision


class Reader:
    """Record bytes, enumerations, policy and Git identity for one observation."""

    def __init__(self, audience: str = "local", *, as_of: datetime | None = None):
        if audience not in {"local", "model"}:
            raise ValueError("Unknown view audience")
        self.audience = audience
        self.as_of = (as_of or datetime.now(timezone.utc)).astimezone(timezone.utc)
        self.issues: list[str] = []
        self._files: dict[Path, str] = {}
        self._directories: dict[tuple[Path, str], tuple[Path, ...]] = {}
        self._git: dict[Path, tuple[Path | None, str | None]] = {}
        self._policies: dict[Path, tuple[str, dict | None]] = {}
        self._changed = False
        self._visible: dict[tuple[str, str], str | list[str]] = {}

    def partial(self, message: str) -> None:
        if message not in self.issues:
            self.issues.append(message)

    def _remember_file(self, path: Path, value: str) -> None:
        if self._files.setdefault(path, value) != value:
            self._changed = True

    def _policy_at(self, root: Path) -> tuple[str, dict | None]:
        if root not in self._policies:
            path = root / ".research/policy.json"
            try:
                raw = _bytes(path)
            except (FileNotFoundError, NotADirectoryError):
                observed, value = "missing", None
            except OSError:
                observed, value = "unavailable", None
            else:
                observed, value = _digest(raw), None
                try:
                    captured = json.loads(raw)
                    validated, result = policy.load_policy(root)
                    if result.status == "PASS" and captured == validated:
                        value = captured
                except (ValueError, OSError):
                    pass
            self._remember_file(path, observed)
            self._policies[root] = (observed, value)
        return self._policies[root]

    def _applicable_policies(self, path: Path):
        # An explicitly supplied document and the same document found through
        # its study root must cross the same policy boundary.
        for root in path.parents:
            observed, data = self._policy_at(root)
            if observed != "missing":
                yield root, data

    def has_policy(self, path: Path) -> bool:
        path = Path(path).absolute()
        if path.is_dir():
            path = path / ".view-scope"
        return any(True for _ in self._applicable_policies(path))

    def policy_roots(self, path: Path) -> tuple[Path, ...]:
        """Return governing roots for repository-relative source citations."""
        return tuple(root for root, _ in self._applicable_policies(Path(path).absolute()))

    def permits(self, path: Path) -> bool:
        path = Path(path).absolute()
        if not _plain(path) or ".git" in path.parts:
            return False
        if self.audience == "local":
            return True
        for root, rules in self._applicable_policies(path):
            if rules is None:
                return False
            relative = path.relative_to(root).as_posix()
            for item in rules["resources"]:
                pattern = policy.normalize_pattern(item["match"])
                if pattern is not None and policy.pattern_matches(pattern, relative):
                    if not rules["rules"][item["class"].lower()]["model_egress"]:
                        return False
                    break
            else:
                return False
        return True

    def _read(self, path: Path) -> bytes:
        try:
            content = _bytes(path)
        except OSError:
            self._remember_file(path, _file_state(path))
            raise
        self._remember_file(path, _digest(content))
        return content

    def read(self, path: Path) -> bytes:
        path = Path(path).absolute()
        if not self.permits(path):
            raise PermissionError("Source unavailable for this audience")
        try:
            return self._read(path)
        finally:
            if path in self._files:
                self._visible[("file", str(path))] = self._files[path]

    def watch_file(self, path: Path) -> None:
        path = Path(path).absolute()
        if self.permits(path):
            self._remember_file(path, _file_state(path))
            self._visible[("file", str(path))] = self._files[path]

    def _watch_members(self, path: Path, pattern: str) -> tuple[Path, ...]:
        members = _members(path, pattern)
        if self._directories.setdefault((path, pattern), members) != members:
            self._changed = True
        return members

    def _can_traverse(self, path: Path) -> bool:
        """Retain a parent directory of explicitly allowed, nested documents."""
        if not _plain(path) or not path.is_dir() or ".git" in path.parts:
            return False
        for root, data in self._applicable_policies(path / ".view-scope"):
            if data is None:
                return False
            relative = path.relative_to(root).as_posix()
            allowed = [p for item in data["resources"]
                       if data["rules"][item["class"].lower()]["model_egress"]
                       if (p := policy.normalize_pattern(item["match"])) is not None]
            if relative != "." and not any(policy.pattern_matches(p, relative)
                                           or p[0].startswith(relative + "/") for p in allowed):
                return False
        return True

    def watch_dir(self, path: Path, pattern: str) -> list[Path]:
        path = Path(path).absolute()
        if ".git" in path.parts or ".." in Path(pattern).parts or Path(pattern).is_absolute():
            raise PermissionError("Unsupported directory path")
        matches = self._watch_members(path, pattern)
        visible = [entry for entry in matches if self.permits(entry) or self._can_traverse(entry)]
        if len(visible) != len(matches):
            self.partial("Some source material is unavailable for this audience.")
        self._visible[("directory", str(path / pattern))] = [str(p.relative_to(path)) for p in visible]
        return visible

    def watch_git(self, root: Path) -> str | None:
        root = Path(root).absolute()
        if not _plain(root):
            raise PermissionError("Unsupported repository path")
        identity = _git_identity(root)
        if self._git.setdefault(root, identity) != identity:
            self._changed = True
        directory, revision = identity
        if directory is None:
            return None
        anchor = directory / "research/runtime/anchor.json"
        self._remember_file(anchor, _file_state(anchor))
        if self.audience == "model" and self.has_policy(root):
            return None
        self._visible[("worktree", str(root))] = [str(directory), revision or ""]
        return revision

    def snapshot_id(self) -> str:
        """Hash observable inputs, independent of rendering and evaluation time."""
        manifest = [(kind, name, value) for (kind, name), value in sorted(self._visible.items())]
        return _digest(json.dumps(manifest, separators=(",", ":")).encode())

    def stable(self) -> bool:
        if self._changed or any(_file_state(p) != state for p, state in self._files.items()):
            return False
        try:
            if any(_members(p, glob) != members for (p, glob), members in self._directories.items()):
                return False
        except OSError:
            return False
        return all(_git_identity(root) == identity for root, identity in self._git.items())


def journal_entries(reader: Reader, root: Path) -> list[dict]:
    """Expose only operation status; argv, request payloads and logs stay local."""
    root = Path(root).absolute()
    if reader.audience == "model" and reader.has_policy(root):
        reader.partial("Operational journal withheld under study policy.")
        return []
    reader.watch_git(root)
    git_dir, _ = reader._git[root]
    if git_dir is None:
        return []
    runtime = git_dir / "research/runtime"
    entries = []
    try:
        files = reader._watch_members(runtime, "*/operation.json")
    except OSError:
        reader.partial("Operational journal unavailable.")
        return entries
    for path in files:
        try:
            operation = str(UUID(path.parent.name))
            content = reader._read(path)
            data = json.loads(content)
            if not isinstance(data, dict) or data.get("operation_id") != operation:
                raise ValueError("Invalid journal identity")
            result = data.get("result")
            if result is None:
                stage = data.get("stage")
                if stage not in {"EXECUTION_STARTED", "ADMISSION_STARTED"}:
                    raise ValueError("Unknown operation stage")
                status = "unfinished"
                if stage == "EXECUTION_STARTED":
                    message = "Execution unfinished. Inspect recovery and possible exposure before retry."
                else:
                    message = "Admission unfinished. Inspect record consolidation before retry."
            elif not isinstance(result, dict):
                raise ValueError("Invalid operation result")
            elif result.get("effect") == "executed":
                if result.get("disposition") == "ALLOW":
                    status = "executed"
                    message = "Execution completed. Result admission is a separate step."
                else:
                    status = "failed"
                    message = "Execution ended unsuccessfully. Result exposure remains possible."
            else:
                continue
        except (ValueError, OSError):
            reader.partial("Operational journal record unreadable.")
            continue
        version = _digest(content)
        selector = f"operation:{operation}@{version}"
        reader._visible[("journal_state", operation)] = version
        entries.append({
            "selector": selector, "kind": "operation", "label": "Research operation",
            "aliases": [operation], "source": "worktree operation journal", "text": message,
            "related": [], "details": {"state": status, "version": version},
        })
    return entries
