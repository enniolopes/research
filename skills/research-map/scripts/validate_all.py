#!/usr/bin/env python3
"""Research 0.8 validator: preserve 0.7 checks and add epistemic plan/run/lineage/exposure checks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import epistemic
import validate as legacy

LEGACY = {"map", "numbers", "decisions", "disclosure", "citations", "notebooks"}
EPISTEMIC = {"plan", "runs", "lineage", "exposure"}
ALL = LEGACY | EPISTEMIC


def run(map_path: Path, root: Path, offline: bool, min_int: int, only: set[str] | None):
    legacy_only = None if only is None else only & LEGACY
    epistemic_only = None if only is None else only & EPISTEMIC
    results = legacy.run(map_path, root, offline, min_int, legacy_only)
    results.extend(epistemic.run(map_path, root, epistemic_only))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate operational and epistemic integrity of a research repository.")
    parser.add_argument("map", nargs="?", default="RESEARCH.map")
    parser.add_argument("--root", help="repository root (default: the map's directory)")
    parser.add_argument("--offline", action="store_true", help="do not resolve citations; report NOT_VERIFIED")
    parser.add_argument("--strict", action="store_true", help="exit 1 on NOT_VERIFIED too")
    parser.add_argument("--min-int", type=int, default=20, help="integers below this are not checked (default 20)")
    parser.add_argument("--only", help="comma-separated subset: " + ",".join(sorted(ALL)))
    args = parser.parse_args(argv)

    map_path = Path(args.map).resolve()
    if not map_path.is_file():
        print(f"research validate: {map_path} not found")
        return 1
    root = Path(args.root).resolve() if args.root else map_path.parent
    only = set(args.only.split(",")) if args.only else None
    unknown = (only or set()) - ALL
    if unknown:
        print("research validate: unknown check(s): " + ", ".join(sorted(unknown)))
        return 2

    results = run(map_path, root, args.offline, args.min_int, only)
    print(f"research validate — {root}")
    for item in results:
        print(f"{item.name:<11}{item.status:<14}{item.summary}")
        for line in item.lines:
            print(f"  {line}")
    failed = any(item.status == "FAIL" for item in results)
    unverified = any(item.status == "NOT_VERIFIED" for item in results)
    verdict = "FAIL" if failed else ("NOT_VERIFIED" if unverified else "PASS")
    print(f"RESULT {verdict}")
    return 1 if failed or (args.strict and unverified) else 0


if __name__ == "__main__":
    sys.exit(main())
