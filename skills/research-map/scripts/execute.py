#!/usr/bin/env python3
"""Validate prospective execution specs and run the local integrity backend."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import policy
except ModuleNotFoundError:
    _policy_spec = importlib.util.spec_from_file_location(
        "policy", Path(__file__).with_name("policy.py")
    )
    assert _policy_spec and _policy_spec.loader
    policy = importlib.util.module_from_spec(_policy_spec)
    sys.modules["policy"] = policy
    _policy_spec.loader.exec_module(policy)

EXECUTION_ID = re.compile(r"EXEC-\d+")
CAPABILITIES = {"network_egress", "model_egress"}


@dataclass
class Result:
    name: str = "executions"
    status: str = "PASS"
    summary: str = ""
    lines: list[str] = field(default_factory=list)

    def fail(self, line: str) -> None:
        self.status = "FAIL"
        self.lines.append(line)

    def unverified(self, summary: str) -> None:
        if self.status == "PASS":
            self.status = "NOT_VERIFIED"
        self.summary = summary


def git(root: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=text,
    )


def git_available(root: Path) -> bool:
    result = git(root, "rev-parse", "--is-inside-work-tree")
    return result.returncode == 0 and result.stdout.strip() == "true"


def first_added_commit(root: Path, relative: str) -> str:
    result = git(root, "log", "--diff-filter=A", "--format=%H", "--", relative)
    if result.returncode != 0:
        return ""
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return commits[-1] if commits else ""


def show(root: Path, ref: str, relative: str) -> str | None:
    result = git(root, "show", f"{ref}:{relative}")
    return result.stdout if result.returncode == 0 else None


def repo_path(root: Path, raw: str) -> Path | None:
    normalized = policy.normalize_path(raw)
    if normalized is None:
        return None
    root = root.resolve()
    resolved = (root / normalized).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def _path_list(data: dict, key: str, *, nonempty: bool, result: Result, label: str) -> list[str]:
    raw = data.get(key)
    if not isinstance(raw, list) or (nonempty and not raw):
        qualifier = "non-empty " if nonempty else ""
        result.fail(f"{label}: {key} must be a {qualifier}list of repository-relative paths")
        return []
    paths: list[str] = []
    for index, value in enumerate(raw, 1):
        normalized = policy.normalize_path(value) if isinstance(value, str) else None
        if normalized is None:
            result.fail(f"{label}: {key}[{index}] must be a safe repository-relative path")
            continue
        paths.append(normalized)
    if len(paths) != len(set(paths)):
        result.fail(f"{label}: {key} contains duplicate paths")
    return paths


def validate_spec(data: object, *, filename: str = "") -> tuple[Result, dict | None]:
    result = Result()
    label = filename or "execution spec"
    if not isinstance(data, dict):
        result.fail(f"{label}: execution spec must be a JSON object")
        return result, None

    execution_id = str(data.get("id", "")).upper()
    if not EXECUTION_ID.fullmatch(execution_id):
        result.fail(f"{label}: id must be EXEC-<n>")
    elif filename and Path(filename).stem.upper() != execution_id:
        result.fail(f"{label}: filename must match execution id {execution_id}")

    command = data.get("command")
    if not (
        isinstance(command, list)
        and command
        and all(isinstance(part, str) and part for part in command)
    ):
        result.fail(f"{label}: command must be a non-empty argv list")

    inputs = _path_list(data, "inputs", nonempty=False, result=result, label=label)
    outputs = _path_list(data, "outputs", nonempty=True, result=result, label=label)
    environment = _path_list(data, "environment", nonempty=False, result=result, label=label)

    overlap = set(outputs) & (set(inputs) | set(environment))
    if overlap:
        result.fail(
            f"{label}: output path(s) also declared as input/environment: "
            + ", ".join(sorted(overlap))
        )

    capabilities = data.get("capabilities")
    if not isinstance(capabilities, dict):
        result.fail(f"{label}: capabilities must be an object")
    else:
        unknown = set(capabilities) - CAPABILITIES
        missing = CAPABILITIES - set(capabilities)
        if unknown:
            result.fail(f"{label}: unknown capabilities {sorted(unknown)}")
        if missing:
            result.fail(f"{label}: missing capabilities {sorted(missing)}")
        for name in CAPABILITIES & set(capabilities):
            if not isinstance(capabilities[name], bool):
                result.fail(f"{label}: capabilities.{name} must be boolean")

    normalized = dict(data)
    normalized["id"] = execution_id
    normalized["inputs"] = inputs
    normalized["outputs"] = outputs
    normalized["environment"] = environment
    return result, normalized


def load_spec(root: Path, requested: str) -> tuple[Path, dict] | None:
    execution_id = requested.upper()
    if not EXECUTION_ID.fullmatch(execution_id):
        return None
    path = root / ".research" / "executions" / f"{execution_id}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return path, data


def check_execution_specs(root: Path) -> Result:
    result = Result()
    directory = root / ".research" / "executions"
    files = sorted(directory.glob("*.json")) if directory.is_dir() else []
    if not files:
        result.unverified("no .research/executions/*.json specs")
        return result

    have_git = git_available(root)
    temporal_unverified = 0
    seen_ids: set[str] = set()

    for path in files:
        relative = str(path.relative_to(root))
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            result.fail(f"{relative}: invalid JSON ({exc})")
            continue

        spec_result, normalized = validate_spec(data, filename=relative)
        for line in spec_result.lines:
            result.fail(line)
        if normalized:
            execution_id = normalized["id"]
            if execution_id in seen_ids:
                result.fail(f"{relative}: duplicate execution id {execution_id}")
            seen_ids.add(execution_id)

        if have_git:
            committed = first_added_commit(root, relative)
            if not committed:
                temporal_unverified += 1
                result.lines.append(
                    f"{relative}: execution spec is not yet committed; append-only check NOT_VERIFIED"
                )
            else:
                original = show(root, committed, relative)
                if original is None:
                    result.fail(
                        f"{relative}: first committed execution spec at {committed} cannot be read"
                    )
                elif original != raw:
                    result.fail(
                        f"{relative}: execution spec changed after first commit {committed}; "
                        "record a new EXEC id instead of rewriting a prospective execution"
                    )
        else:
            temporal_unverified += 1
            result.lines.append(
                f"{relative}: git unavailable/not a work tree; append-only check NOT_VERIFIED"
            )

    if result.status == "PASS" and temporal_unverified:
        result.unverified(
            f"{len(files)} execution spec(s); {temporal_unverified} append-only check(s) NOT_VERIFIED"
        )
    elif result.status == "PASS":
        result.summary = f"{len(files)} immutable execution spec(s)"
    return result


def changed_paths(root: Path) -> set[str] | None:
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status.returncode != 0:
        return None
    changed: set[str] = set()
    for line in status.stdout.splitlines():
        if len(line) < 4:
            continue
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        changed.add(raw.strip().strip('"'))
    return changed


def policy_preflight(root: Path, spec: dict) -> tuple[str, str]:
    policy_path = root / ".research" / "policy.json"
    if not policy_path.is_file():
        return "ALLOW", "policy_not_declared"

    _, validation = policy.load_policy(root)
    if validation.status == "FAIL":
        return "INVALID", "; ".join(validation.lines)

    resources = list(dict.fromkeys(spec["inputs"] + spec["environment"]))
    capabilities = spec["capabilities"]

    for resource in resources:
        for capability in sorted(CAPABILITIES):
            decision, class_name = policy.decide(root, resource, capability)
            if decision in {"INVALID", "UNDECLARED"}:
                return decision, f"{resource} {capability}"
            requested = capabilities[capability]
            if requested and decision != "ALLOW":
                return "DENY", f"{resource} class={class_name} forbids requested {capability}"
            if not requested and decision == "DENY":
                return (
                    "NOT_ENFORCEABLE",
                    f"local backend cannot prove {capability}=false for {resource} class={class_name}",
                )
    return "ALLOW", "policy_authorized"


def run_local(root: Path, execution_id: str) -> tuple[int, dict]:
    if not git_available(root):
        return 2, {"status": "INVALID", "reason": "repository is not a Git work tree"}

    found = load_spec(root, execution_id)
    if found is None:
        return 2, {"status": "INVALID", "reason": f"{execution_id.upper()} not found"}
    path, data = found
    spec_result, spec = validate_spec(data, filename=str(path.relative_to(root)))
    if spec is None or spec_result.status == "FAIL":
        return 2, {"status": "INVALID", "reason": "; ".join(spec_result.lines)}

    before = changed_paths(root)
    if before is None:
        return 2, {"status": "INVALID", "reason": "could not inspect Git work tree"}
    if before:
        return 1, {
            "status": "ERROR",
            "reason": "work tree must be clean before execution",
            "changed": sorted(before),
        }

    head = git(root, "rev-parse", "HEAD")
    if head.returncode != 0:
        return 2, {"status": "INVALID", "reason": "could not resolve HEAD"}
    execution_freeze = head.stdout.strip()
    relative_spec = str(path.relative_to(root))
    committed_spec = show(root, execution_freeze, relative_spec)
    if committed_spec is None:
        return 2, {
            "status": "INVALID",
            "reason": f"{relative_spec} is not committed at execution freeze",
        }

    for resource in spec["inputs"] + spec["environment"]:
        resolved = repo_path(root, resource)
        if resolved is None or not resolved.is_file():
            return 2, {
                "status": "INVALID",
                "reason": f"declared resource does not exist as a file: {resource}",
            }
        tracked = git(root, "cat-file", "-e", f"{execution_freeze}:{resource}")
        if tracked.returncode != 0:
            return 2, {
                "status": "INVALID",
                "reason": f"declared resource is not tracked at execution freeze: {resource}",
            }

    authorization, reason = policy_preflight(root, spec)
    if authorization != "ALLOW":
        return 3, {"status": authorization, "reason": reason}

    try:
        executed = subprocess.run(spec["command"], cwd=root)
    except OSError as exc:
        return 1, {"status": "ERROR", "reason": f"could not execute {spec['command'][0]}: {exc}"}
    if executed.returncode != 0:
        return 1, {
            "status": "ERROR",
            "reason": f"command exited {executed.returncode}",
        }

    after = changed_paths(root)
    if after is None:
        return 1, {"status": "ERROR", "reason": "could not inspect post-execution work tree"}
    declared = set(spec["outputs"])
    extra = after - declared
    missing = declared - after
    if extra or missing:
        return 1, {
            "status": "ERROR",
            "reason": "execution changed paths outside its declared output boundary",
            "extra": sorted(extra),
            "missing": sorted(missing),
        }

    absent = [
        output
        for output in spec["outputs"]
        if (repo_path(root, output) is None or not repo_path(root, output).is_file())
    ]
    if absent:
        return 1, {
            "status": "ERROR",
            "reason": "declared output was not produced",
            "missing": absent,
        }

    return 0, {
        "status": "OK",
        "execution_spec": spec["id"],
        "execution_freeze": execution_freeze,
        "backend": "local",
        "outputs": spec["outputs"],
        "authorization": reason,
        "enforcement": {
            "filesystem_changes": "verified_after_execution",
            "network_egress": "not_enforced",
            "model_egress": "not_enforced",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate execution specs or execute one with the local integrity backend."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--root", default=".")

    run_parser = sub.add_parser("run")
    run_parser.add_argument("execution", help="EXEC-<n>")
    run_parser.add_argument("--root", default=".")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    if args.command == "validate":
        result = check_execution_specs(root)
        print(f"{result.name:<11}{result.status:<14}{result.summary}")
        for line in result.lines:
            print(f"  {line}")
        return 1 if result.status == "FAIL" else 0

    code, outcome = run_local(root, args.execution)
    print("EXECUTION " + json.dumps(outcome, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
