#!/usr/bin/env python3
"""Small public dispatcher for the research runtime."""
import sys
import supervise
import validate_all


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "supervise":
        return supervise.main(argv[1:])
    if argv and argv[0] == "validate":
        return validate_all.main(argv[1:])
    print("Usage: research.py supervise <command> [options] | validate [options]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
