#!/usr/bin/env python3
"""Replay one recorded run from its execution freeze and compare declared outputs."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


def git(root: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=text)


def find_run(root: Path, requested: str) -> tuple[Path, dict] | None:
    run_id = requested.upper()
    run_dir = root / ".research" / "runs"
    if not run_dir.is_dir():
        return None
    for path in sorted(run_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict) and str(data.get("id", "")).upper() == run_id:
            return path, data
    return None


def argv_from(command: object) -> list[str] | None:
    if isinstance(command, str) and command.strip():
        try:
            return shlex.split(command)
        except ValueError:
            return None
    if isinstance(command, list) and command and all(isinstance(part, str) and part for part in command):
        return list(command)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay a run from execution_freeze without mutating the research checkout.")
    parser.add_argument("run", help="RUN-<n>")
    parser.add_argument("--root", default=".", help="research repository root")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    found = find_run(root, args.run)
    if found is None:
        print(f"REPLAY {args.run.upper()} NOT_VERIFIED — run manifest not found")
        return 2
    path, data = found
    run_id = str(data.get("id", args.run)).upper()
    execution_freeze = str(data.get("execution_freeze", ""))
    run_commit = str(data.get("commit", ""))
    replay = data.get("replay")

    if not execution_freeze or not run_commit:
        print(f"REPLAY {run_id} NOT_VERIFIED — execution_freeze/run commit missing")
        return 2
    if not isinstance(replay, dict):
        print(f"REPLAY {run_id} NOT_VERIFIED — no replay recipe in {path.relative_to(root)}")
        return 2
    command = argv_from(replay.get("command"))
    if command is None:
        print(f"REPLAY {run_id} ERROR — invalid replay.command")
        return 1

    environment = replay.get("environment", [])
    if not isinstance(environment, list) or not all(isinstance(item, str) and item for item in environment):
        print(f"REPLAY {run_id} ERROR — replay.environment must be a list of paths")
        return 1
    for item in environment:
        present = git(root, "cat-file", "-e", f"{execution_freeze}:{item}")
        if present.returncode != 0:
            print(f"REPLAY {run_id} ERROR — environment path missing at execution freeze: {item}")
            return 1

    outputs = data.get("outputs", [])
    artifacts = [
        str(item.get("artifact", ""))
        for item in outputs
        if isinstance(item, dict) and str(item.get("artifact", ""))
    ]
    if not artifacts:
        print(f"REPLAY {run_id} ERROR — no declared output artifacts")
        return 1

    with tempfile.TemporaryDirectory(prefix=f"research-{run_id.lower()}-") as tmp:
        worktree = Path(tmp) / "worktree"
        added = git(root, "worktree", "add", "--detach", str(worktree), execution_freeze)
        if added.returncode != 0:
            print(f"REPLAY {run_id} ERROR — could not create execution-freeze worktree")
            if added.stderr:
                print(added.stderr.strip())
            return 1
        try:
            try:
                executed = subprocess.run(command, cwd=worktree)
            except OSError as exc:
                print(f"REPLAY {run_id} ERROR — could not execute {command[0]}: {exc}")
                return 1
            if executed.returncode != 0:
                print(f"REPLAY {run_id} ERROR — command exited {executed.returncode}")
                return 1

            drift: list[str] = []
            for artifact in artifacts:
                produced = worktree / artifact
                if not produced.is_file():
                    print(f"REPLAY {run_id} ERROR — output not produced: {artifact}")
                    return 1
                expected = git(root, "show", f"{run_commit}:{artifact}", text=False)
                if expected.returncode != 0:
                    print(f"REPLAY {run_id} ERROR — output absent from run commit: {artifact}")
                    return 1
                if produced.read_bytes() != expected.stdout:
                    drift.append(artifact)

            if drift:
                print(f"REPLAY {run_id} DRIFT — {', '.join(drift)}")
                return 1
            print(f"REPLAY {run_id} EXACT — {len(artifacts)} declared output(s)")
            return 0
        finally:
            git(root, "worktree", "remove", "--force", str(worktree))


if __name__ == "__main__":
    sys.exit(main())
