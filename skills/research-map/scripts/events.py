"""Cooperative, crash-visible journals outside the execution work tree."""
from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from contracts import ContractError, canonical, digest, load
from resources import ancestor, git, head


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
