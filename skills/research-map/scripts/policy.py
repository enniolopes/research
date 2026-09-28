#!/usr/bin/env python3
"""Validate and query the optional Research capability policy."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

CLASSES = {"public", "restricted", "derived", "secret"}
CAPABILITIES = {"model_egress", "network_egress"}
WILDCARDS = {"*", "?", "[", "]"}


@dataclass
class Result:
    name: str = "policy"
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


def normalize_path(raw: str) -> str | None:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        return None
    path = Path(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return "/".join(path.parts)


def normalize_pattern(raw: object) -> tuple[str, bool] | None:
    if not isinstance(raw, str) or not raw:
        return None
    prefix = raw.endswith("/**")
    base = raw[:-3] if prefix else raw
    if any(token in base for token in WILDCARDS):
        return None
    normalized = normalize_path(base.rstrip("/"))
    if normalized is None:
        return None
    return normalized, prefix


def pattern_matches(pattern: tuple[str, bool], resource: str) -> bool:
    base, prefix = pattern
    return resource == base or (prefix and resource.startswith(base + "/"))


def patterns_overlap(left: tuple[str, bool], right: tuple[str, bool]) -> bool:
    left_base, left_prefix = left
    right_base, right_prefix = right
    if left_base == right_base:
        return True
    if left_prefix and right_base.startswith(left_base + "/"):
        return True
    if right_prefix and left_base.startswith(right_base + "/"):
        return True
    return False


def load_policy(root: Path) -> tuple[dict | None, Result]:
    result = Result()
    path = root / ".research" / "policy.json"
    if not path.is_file():
        result.unverified("no .research/policy.json")
        return None, result

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result.fail(f".research/policy.json: invalid JSON ({exc})")
        return None, result
    if not isinstance(data, dict):
        result.fail(".research/policy.json: policy must be a JSON object")
        return None, result
    if data.get("version") != 1:
        result.fail(".research/policy.json: version must be 1")

    resources = data.get("resources")
    if not isinstance(resources, list) or not resources:
        result.fail(".research/policy.json: resources must be a non-empty list")
        resources = []

    parsed: list[tuple[str, tuple[str, bool], str]] = []
    used_classes: set[str] = set()
    for index, item in enumerate(resources, 1):
        label = f".research/policy.json: resources[{index}]"
        if not isinstance(item, dict):
            result.fail(f"{label} must be an object")
            continue
        raw_pattern = item.get("match")
        pattern = normalize_pattern(raw_pattern)
        if pattern is None:
            result.fail(
                f"{label}.match must be a repository-relative exact path or prefix ending in /**"
            )
            continue
        class_name = str(item.get("class", "")).lower()
        if class_name not in CLASSES:
            result.fail(f"{label}.class must be one of {sorted(CLASSES)}")
            continue
        parsed.append((str(raw_pattern), pattern, class_name))
        used_classes.add(class_name)

    for i, (left_raw, left, _) in enumerate(parsed):
        for right_raw, right, _ in parsed[i + 1:]:
            if patterns_overlap(left, right):
                result.fail(
                    f".research/policy.json: overlapping resource rules {left_raw!r} and {right_raw!r}; "
                    "use non-overlapping rules instead of implicit precedence"
                )

    rules = data.get("rules")
    if not isinstance(rules, dict):
        result.fail(".research/policy.json: rules must be an object")
        rules = {}
    for class_name in sorted(used_classes):
        class_rules = rules.get(class_name)
        if not isinstance(class_rules, dict):
            result.fail(f".research/policy.json: rules.{class_name} is required")
            continue
        unknown = set(class_rules) - CAPABILITIES
        missing = CAPABILITIES - set(class_rules)
        if unknown:
            result.fail(
                f".research/policy.json: rules.{class_name} has unknown capabilities {sorted(unknown)}"
            )
        if missing:
            result.fail(
                f".research/policy.json: rules.{class_name} is missing {sorted(missing)}"
            )
        for capability in CAPABILITIES & set(class_rules):
            if not isinstance(class_rules[capability], bool):
                result.fail(
                    f".research/policy.json: rules.{class_name}.{capability} must be boolean"
                )

    if result.status == "PASS":
        result.summary = f"{len(parsed)} resource rule(s), {len(used_classes)} class(es)"
    return data, result


def decide(root: Path, resource: str, capability: str) -> tuple[str, str]:
    data, validation = load_policy(root)
    if validation.status == "FAIL":
        return "INVALID", ""
    if data is None:
        return "UNDECLARED", ""
    normalized = normalize_path(resource)
    if normalized is None or capability not in CAPABILITIES:
        return "INVALID", ""

    matches = []
    for item in data["resources"]:
        pattern = normalize_pattern(item["match"])
        if pattern is not None and pattern_matches(pattern, normalized):
            matches.append(str(item["class"]).lower())
    if not matches:
        return "UNDECLARED", ""
    class_name = matches[0]
    allowed = data["rules"][class_name][capability]
    return ("ALLOW" if allowed else "DENY"), class_name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate or query a Research capability policy."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--root", default=".")

    check_parser = sub.add_parser("check")
    check_parser.add_argument("resource")
    check_parser.add_argument("capability", choices=sorted(CAPABILITIES))
    check_parser.add_argument("--root", default=".")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    if args.command == "validate":
        _, result = load_policy(root)
        print(f"{result.name:<11}{result.status:<14}{result.summary}")
        for line in result.lines:
            print(f"  {line}")
        return 1 if result.status == "FAIL" else 0

    decision, class_name = decide(root, args.resource, args.capability)
    suffix = f" class={class_name}" if class_name else ""
    print(f"POLICY {decision}{suffix}")
    if decision == "ALLOW":
        return 0
    return 2 if decision == "INVALID" else 1


if __name__ == "__main__":
    sys.exit(main())
