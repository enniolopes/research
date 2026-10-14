"""One append-only history check for typed records, RUN, EXEC and ASMT.

A later restoration does not undo a committed mutation. Callers own path safety,
working-copy checks and the meaning of a missing first commit.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def unchanged_history(root: Path, path: str, initial: str) -> tuple[str, str]:
    def read(*args):
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
        if result.returncode:
            raise ValueError(result.stderr.strip())
        return result.stdout

    try:
        original = read("rev-parse", f"{initial}:{path}").strip()
        changes = read("log", "--full-history", "-m", "--format=", "--raw", "--no-abbrev", "--no-renames", "HEAD", "--", path)
        for line in changes.splitlines():
            if line.startswith(":"):
                fields = line.split()
                if not fields[1].startswith("100") or fields[3] != original:
                    return "FAIL", f"record altered in committed history: {path}"
        if read("rev-parse", f"HEAD:{path}").strip() != original:
            return "FAIL", f"record differs at HEAD: {path}"
    except (OSError, ValueError) as exc:
        return "FAIL", f"cannot verify immutable history for {path}: {exc}"
    return "PASS", "committed history unchanged"
