from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


replay = load("research_replay", "skills/research-map/scripts/replay.py")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


class ReplayTests(unittest.TestCase):
    def test_exact_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git(root, "init")
            git(root, "config", "user.email", "test@example.com")
            git(root, "config", "user.name", "Test")
            (root / ".research" / "runs").mkdir(parents=True)
            (root / "make_result.py").write_text(
                "from pathlib import Path\n"
                "p=Path('aggregates/out.txt'); p.parent.mkdir(exist_ok=True); p.write_text('42\\n')\n",
                encoding="utf-8",
            )
            git(root, "add", ".")
            git(root, "commit", "-m", "freeze")
            freeze = git(root, "rev-parse", "HEAD")
            subprocess.run([sys.executable, "make_result.py"], cwd=root, check=True)
            git(root, "add", "aggregates/out.txt")
            git(root, "commit", "-m", "run")
            run_commit = git(root, "rev-parse", "HEAD")
            receipt = {
                "id": "RUN-1",
                "execution_freeze": freeze,
                "commit": run_commit,
                "replay": {"command": [sys.executable, "make_result.py"], "environment": []},
                "outputs": [{"result": "R1", "artifact": "aggregates/out.txt"}],
            }
            (root / ".research" / "runs" / "RUN-1.json").write_text(json.dumps(receipt), encoding="utf-8")
            self.assertEqual(replay.main(["RUN-1", "--root", str(root)]), 0)


if __name__ == "__main__":
    unittest.main()
