#!/usr/bin/env python3
"""Small public dispatcher for the research runtime."""
import os
import sys
import supervise
import validate_all


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "supervise":
        return supervise.main(argv[1:])
    if argv and argv[0] == "validate":
        return validate_all.main(argv[1:])
    if argv and argv[0] == "view":
        import view
        return view.main(argv[1:])
    print("Usage: research.py supervise <command> [options] | validate [options] | view <query> [options]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    if sys.argv[1:2] == ["view"]:
        # Inspect only locally available objects, including when the study is a partial clone.
        os.environ.update(GIT_ALLOW_PROTOCOL="", GIT_NO_LAZY_FETCH="1",
                          GIT_NO_REPLACE_OBJECTS="1", GIT_OPTIONAL_LOCKS="0")
    raise SystemExit(main())
