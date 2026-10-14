"""Versioned Git resources and binding-aware applicability; never truth inference."""
from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from contracts import ContractError, load
from git_integrity import unchanged_history


def git(root: Path, *args: str) -> bytes:
    p = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if p.returncode:
        raise ContractError(f"git {' '.join(args[:2])}: {p.stderr.decode(errors='replace').strip()}")
    return p.stdout


def head(root: Path) -> str:
    return git(root, "rev-parse", "HEAD").decode().strip()


def ancestor(root: Path, older: str, newer: str) -> bool:
    p = subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=root, capture_output=True)
    if p.returncode not in (0, 1):
        raise ContractError("invalid Git ancestry")
    return p.returncode == 0


def safe_path(root: Path, raw: str) -> Path:
    if not isinstance(raw, str) or not raw or "\x00" in raw or "\\" in raw:
        raise ContractError("invalid resource path")
    p = Path(raw)
    if p.is_absolute() or any(x in ("..", ".git") for x in p.parts) or raw.startswith("-"):
        raise ContractError(f"unsafe resource path: {raw}")
    candidate = root / p
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ContractError(f"path escapes root: {raw}") from exc
    if any(part.is_symlink() for part in [candidate, *candidate.parents] if part != root.parent):
        raise ContractError(f"symlink resource is unsupported: {raw}")
    return candidate


def frozen_bytes(root: Path, revision: str, path: str) -> bytes:
    safe_path(root, path)
    tree = git(root, "ls-tree", "-z", revision, "--", path)
    if not tree or not tree.startswith(b"100"):
        raise ContractError(f"not a committed regular file: {path}@{revision}")
    return git(root, "show", f"{revision}:{path}")


def fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def first_commit(root: Path, path: str) -> str | None:
    commits = git(root, "log", "--format=%H", "--diff-filter=A", "HEAD", "--", path).decode().splitlines()
    return commits[-1] if commits else None


def resource(root: Path, kind: str, logical_id: str, path: str, revision: str | None = None) -> dict:
    revision = revision or head(root)
    return {"kind": kind, "logical_id": logical_id, "path": path, "revision": revision,
            "sha256": fingerprint(frozen_bytes(root, revision, path))}


def resolve(ref, owner: dict, records: dict) -> dict:
    if isinstance(ref, str):
        result = owner.get("resources", {}).get(ref)
    else:
        foreign = records.get(ref["record_id"])
        result = foreign.get("resources", {}).get(ref["resource_id"]) if foreign else None
    if result is None:
        raise ContractError(f"unresolved resource: {ref}")
    return result


def verify(root: Path, value: dict) -> tuple[str, str]:
    if value["kind"] == "restricted_external":
        return "NOT_VERIFIED", "restricted resource bytes unavailable"
    try:
        actual = frozen_bytes(root, value["revision"], value["path"])
    except (ContractError, OSError) as exc:
        return "NOT_VERIFIED", str(exc)
    if fingerprint(actual) != value["sha256"]:
        return "FAIL", f"historical fingerprint mismatch: {value['path']}"
    return "PASS", "historical bytes verified"


def applicability(root: Path, binding: dict, owner: dict, records: dict, now=None) -> tuple[str, str]:
    value = resolve(binding["resource_ref"], owner, records)
    status, why = verify(root, value)
    if status != "PASS":
        return status, why
    mode = binding["binding"]
    if mode == "follow_current":
        path = binding.get("current_path")
        if binding.get("current_record"):
            current = records.get(binding["current_record"])
            if not current:
                return "NOT_VERIFIED", "current record missing"
            if any(r.get("supersedes") == binding["current_record"] for r in records.values()):
                return "STALE", "record replaced; inspect successor"
            path = value.get("path")
        try:
            actual = safe_path(root, path).read_bytes()
        except (OSError, ContractError) as exc:
            return "NOT_VERIFIED", str(exc)
        if fingerprint(actual) != value["sha256"]:
            return "STALE", f"current bytes changed: {path}"
    if mode == "external_refresh":
        deadline = datetime.fromisoformat(binding["refresh_at"].replace("Z", "+00:00"))
        if (now or datetime.now(timezone.utc)) >= deadline:
            return "NOT_VERIFIED", f"source refresh required: {binding['refresh_rule']}"
    return "PASS", "binding applicable"


def committed_unchanged(root: Path, path: str) -> tuple[str, str]:
    initial = first_commit(root, path)
    if not initial:
        return "NOT_VERIFIED", f"uncommitted record: {path}"
    try:
        if frozen_bytes(root, initial, path) != safe_path(root, path).read_bytes():
            return "FAIL", f"record rewritten after first commit: {path}"
        status, why = unchanged_history(root, path, initial)
        if status != "PASS":
            return status, why
    except (OSError, ContractError) as exc:
        return "FAIL", str(exc)
    return "PASS", initial
