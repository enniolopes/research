"""Cooperative, crash-visible journals outside the execution work tree."""
from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from contracts import ContractError, canonical, confirmatory_identity, digest, inquiry_link, load, validate
from resources import ancestor, git, head, safe_path


class RecoveryRequired(ContractError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def git_dir(root: Path, common=False) -> Path:
    raw = git(root, "rev-parse", "--git-common-dir" if common else "--git-dir").decode().strip()
    path = Path(raw)
    return (path if path.is_absolute() else root / path).resolve()


def runtime(root: Path) -> Path:
    return git_dir(root) / "research" / "runtime"


def atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + "." + str(uuid4()) + ".tmp")
    try:
        with tmp.open("xb") as out:
            out.write(canonical(value) + b"\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
        fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if tmp.exists():
            tmp.unlink()


class ProjectLock:
    def __init__(self, root: Path, project_id: str, operation_id: str):
        self.path = git_dir(root, True) / "research" / "locks" / (project_id + ".lock")
        self.info = {"pid": os.getpid(), "host": socket.gethostname(), "worktree": str(root.resolve()),
                     "operation_id": operation_id, "started_at": now()}
        self.acquired = False

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.path.open("xb") as out:
                out.write(canonical(self.info))
                out.flush()
                os.fsync(out.fileno())
        except FileExistsError as exc:
            raise RecoveryRequired("project lock exists; inspect owner and journal, never delete by age alone") from exc
        self.acquired = True
        return self

    def __exit__(self, *_):
        if self.acquired:
            self.path.unlink()


def check_anchor(root: Path) -> None:
    path = runtime(root) / "anchor.json"
    if path.exists():
        old = load(path)["commit"]
        if not ancestor(root, old, head(root)):
            raise RecoveryRequired("Git history diverged from the last verified local anchor")


def anchor(root: Path) -> None:
    atomic(runtime(root) / "anchor.json", {"commit": head(root), "verified_at": now()})


def journal(root: Path, request: dict) -> tuple[Path, dict | None]:
    path = runtime(root) / request["operation_id"] / "operation.json"
    if not path.exists():
        return path, None
    entry = load(path)
    if entry["request_sha256"] != digest(request):
        raise ContractError("operation_id reused with a different payload")
    if entry.get("result") is not None:
        return path, entry
    raise RecoveryRequired("unfinished operation; inspect effects/exposure before retry")


def begin(path: Path, request: dict, stage: str) -> dict:
    value = {"operation_id": request["operation_id"], "request_sha256": digest(request),
             "request": request, "stage": stage, "observed_at": now()}
    atomic(path, value)
    return value


def finish(path: Path, value: dict, result: dict, **extra) -> None:
    atomic(path, {**value, **extra, "stage": "completed", "completed_at": now(), "result": result})


def event(project_id: str, operation_id: str, kind: str, subject: str, members=None,
          observation="instrumented", origin="research-cli", observed_at=None, sequence=0, **extra) -> dict:
    return {"schema_version": "event@1", "id": "EVT-" + str(uuid4()), "project_id": project_id,
            "type": kind, "subject": subject, "operation_id": operation_id, "observation": observation,
            "origin": origin, "observed_at": observed_at or now(), "recorded_at": now(), "sequence": sequence,
            "members": members or [], **extra}


def unfinished(root: Path) -> list[str]:
    directory = runtime(root)
    return [str(p.parent.name) for p in directory.glob("*/operation.json") if load(p).get("result") is None]


def inquiry_attempt(root: Path, project_id: str, analysis: tuple[str, str]) -> bool:
    """The caller holds the project lock when rechecking before execution."""
    common = git_dir(root, True)
    directories = {runtime(root), common / "research/runtime"}
    directories.update(p / "research/runtime" for p in (common / "worktrees").glob("*") if p.is_dir())
    for directory in sorted(directories):
        for path in directory.glob("*/operation.json"):
            entry = load(path)
            request = entry.get("request")
            if not isinstance(request, dict):
                raise RecoveryRequired("Malformed operation journal. Inspect recovery before retrying a linked inquiry.")
            if (request.get("project_id") == project_id and request.get("action") == "FIT_CONFIRMATORY"
                    and inquiry_link(request) and confirmatory_identity(request) == analysis):
                if entry.get("request_sha256") != digest(request):
                    raise RecoveryRequired("Linked execution journal changed. Inspect its original request before retrying.")
                return True
    return False


def inquiry_completion(record: dict):
    if (record.get("schema_version") == "event@1" and record["type"] == "EXECUTION_COMPLETED"
            and record["observation"] == "instrumented" and record["origin"] == "research-cli"):
        return inquiry_link(record)
    return None


def write_execution_events(root: Path, expected: list[dict]) -> list[str]:
    """Reuse the events of a partially imported execution under the project lock."""
    operation_id = expected[0]["operation_id"]
    by_kind = {record["type"]: record for record in expected}
    existing = {}
    directory = safe_path(root, ".research/events")
    for path in sorted(directory.glob("*.json")):
        record = load(safe_path(root, path.relative_to(root).as_posix()))
        if record.get("operation_id") != operation_id:
            continue
        kind = record.get("type")
        if not isinstance(kind, str):
            raise RecoveryRequired("Existing import contains a malformed event type.")
        if kind not in by_kind:
            continue
        validate(record)
        candidate = by_kind[kind]
        if (path.stem != record["id"] or kind in existing
                or record != {**candidate, "id": record["id"], "recorded_at": record["recorded_at"]}):
            raise RecoveryRequired(f"Conflicting {kind} event for this operation. Inspect the existing import.")
        existing[kind] = record["id"]
    for kind, record in by_kind.items():
        if kind not in existing:
            validate(record)
            atomic(directory / (record["id"] + ".json"), record)
            existing[kind] = record["id"]
    return [existing[record["type"]] for record in expected]
