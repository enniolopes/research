#!/usr/bin/env python3
"""Validate immutable semantic assessments recorded by Research."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ASSESSMENT_ID = re.compile(r"ASMT-\d+")
SHA256 = re.compile(r"[0-9a-f]{64}")
SPECS = {
    "citation-entailment@1": {
        "SUPPORTS",
        "CONTRADICTS",
        "INSUFFICIENT",
    }
}


@dataclass
class Result:
    name: str = "assessments"
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


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
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


def check_assessments(root: Path) -> Result:
    result = Result()
    directory = root / ".research" / "assessments"
    files = sorted(directory.glob("*.json")) if directory.is_dir() else []
    if not files:
        result.unverified("no .research/assessments/*.json records")
        return result

    have_git = git_available(root)
    temporal_unverified = 0

    for path in files:
        relative = str(path.relative_to(root))
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            result.fail(f"{relative}: invalid JSON ({exc})")
            continue
        if not isinstance(data, dict):
            result.fail(f"{relative}: assessment must be a JSON object")
            continue

        assessment_id = str(data.get("id", "")).upper()
        if not ASSESSMENT_ID.fullmatch(assessment_id):
            result.fail(f"{relative}: id must be ASMT-<n>")
        elif path.stem.upper() != assessment_id:
            result.fail(f"{relative}: filename must match assessment id {assessment_id}")

        spec = str(data.get("spec", ""))
        answers = SPECS.get(spec)
        if answers is None:
            result.fail(f"{relative}: unknown assessment spec {spec or 'missing'}")

        target = data.get("target")
        if not isinstance(target, dict):
            result.fail(f"{relative}: target must be an object")
        else:
            if not str(target.get("kind", "")).strip():
                result.fail(f"{relative}: target.kind is required")
            if not str(target.get("id", "")).strip():
                result.fail(f"{relative}: target.id is required")
            if not str(target.get("text", "")).strip():
                result.fail(f"{relative}: target.text is required")

        evidence = data.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            result.fail(f"{relative}: evidence must be a non-empty list")
            evidence = []
        for index, item in enumerate(evidence, 1):
            label = f"{relative}: evidence[{index}]"
            if not isinstance(item, dict):
                result.fail(f"{label} must be an object")
                continue
            source = str(item.get("source", "")).strip()
            text = item.get("text")
            digest = str(item.get("sha256", "")).lower()
            if not source:
                result.fail(f"{label}.source is required")
            if not isinstance(text, str) or not text.strip():
                result.fail(f"{label}.text is required")
            if not SHA256.fullmatch(digest):
                result.fail(f"{label}.sha256 must be a lowercase SHA-256 digest")
            elif isinstance(text, str):
                actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
                if actual != digest:
                    result.fail(f"{label}.sha256 does not match the recorded evidence text")
            locator = item.get("locator")
            if locator is not None and (not isinstance(locator, str) or not locator.strip()):
                result.fail(f"{label}.locator must be a non-empty string when present")

        answer = str(data.get("answer", "")).upper()
        if answers is not None and answer not in answers:
            result.fail(
                f"{relative}: answer must be one of {sorted(answers)} for {spec}"
            )

        if not str(data.get("basis", "")).strip():
            result.fail(f"{relative}: basis is required")

        evaluator = data.get("evaluator")
        if not isinstance(evaluator, dict):
            result.fail(f"{relative}: evaluator must be an object")
        else:
            for key in ("backend", "model", "procedure"):
                if not str(evaluator.get(key, "")).strip():
                    result.fail(f"{relative}: evaluator.{key} is required")

        if have_git:
            committed = first_added_commit(root, relative)
            if not committed:
                temporal_unverified += 1
                result.lines.append(
                    f"{relative}: assessment is not yet committed; append-only check NOT_VERIFIED"
                )
            else:
                original = show(root, committed, relative)
                if original is None:
                    result.fail(
                        f"{relative}: first committed assessment at {committed} cannot be read"
                    )
                elif original != raw:
                    result.fail(
                        f"{relative}: assessment changed after first commit {committed}; "
                        "record a new ASMT id instead of rewriting a semantic judgment"
                    )
        else:
            temporal_unverified += 1
            result.lines.append(
                f"{relative}: git unavailable/not a work tree; append-only check NOT_VERIFIED"
            )

    if result.status == "PASS" and temporal_unverified:
        result.unverified(
            f"{len(files)} assessment(s); {temporal_unverified} append-only check(s) NOT_VERIFIED"
        )
    elif result.status == "PASS":
        result.summary = f"{len(files)} immutable assessment(s)"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate recorded semantic assessments."
    )
    parser.add_argument("--root", default=".", help="research repository root")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 on NOT_VERIFIED too",
    )
    args = parser.parse_args(argv)

    result = check_assessments(Path(args.root).resolve())
    print(f"{result.name:<11}{result.status:<14}{result.summary}")
    for line in result.lines:
        print(f"  {line}")
    return 1 if result.status == "FAIL" or (args.strict and result.status == "NOT_VERIFIED") else 0


if __name__ == "__main__":
    sys.exit(main())
