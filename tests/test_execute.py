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


execute = load("research_execute", "skills/research-map/scripts/execute.py")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class ExecutionSpecTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init")
        git(self.root, "config", "user.email", "test@example.com")
        git(self.root, "config", "user.name", "Test")
        (self.root / ".research" / "executions").mkdir(parents=True)
        (self.root / "data").mkdir()
        (self.root / "analysis").mkdir()
        (self.root / "data" / "input.txt").write_text("41\n", encoding="utf-8")
        (self.root / "analysis" / "run.py").write_text(
            "from pathlib import Path\n"
            "value=int(Path('data/input.txt').read_text())+1\n"
            "out=Path('aggregates/out.txt'); out.parent.mkdir(exist_ok=True); out.write_text(str(value)+'\\n')\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def write_spec(self, *, outputs=None, capabilities=None):
        payload = {
            "id": "EXEC-1",
            "command": [sys.executable, "analysis/run.py"],
            "inputs": ["data/input.txt"],
            "outputs": outputs or ["aggregates/out.txt"],
            "environment": ["analysis/run.py"],
            "capabilities": capabilities
            or {"network_egress": False, "model_egress": False},
        }
        path = self.root / ".research" / "executions" / "EXEC-1.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

    def commit_freeze(self):
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "execution freeze")
        return git(self.root, "rev-parse", "HEAD")

    def test_committed_execution_spec_passes_and_is_append_only(self):
        path = self.write_spec()
        self.commit_freeze()
        result = execute.check_execution_specs(self.root)
        self.assertEqual(result.status, "PASS", result.lines)

        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["outputs"] = ["aggregates/other.txt"]
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        result = execute.check_execution_specs(self.root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("changed after first commit" in line for line in result.lines), result.lines)

    def test_execution_spec_rejects_unsafe_or_overlapping_paths(self):
        payload = {
            "id": "EXEC-1",
            "command": ["python", "analysis/run.py"],
            "inputs": ["../private.csv"],
            "outputs": ["analysis/run.py"],
            "environment": ["analysis/run.py"],
            "capabilities": {"network_egress": False, "model_egress": False},
        }
        result, _ = execute.validate_spec(payload, filename=".research/executions/EXEC-1.json")
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("safe repository-relative path" in line for line in result.lines), result.lines)
        self.assertTrue(any("also declared" in line for line in result.lines), result.lines)

    def test_local_runner_produces_only_declared_output(self):
        self.write_spec()
        freeze = self.commit_freeze()
        code, outcome = execute.run_local(self.root, "EXEC-1")
        self.assertEqual(code, 0, outcome)
        self.assertEqual(outcome["status"], "OK")
        self.assertEqual(outcome["execution_freeze"], freeze)
        self.assertEqual(outcome["enforcement"]["network_egress"], "not_enforced")
        self.assertEqual(
            (self.root / "aggregates" / "out.txt").read_text(encoding="utf-8"),
            "42\n",
        )

    def test_local_runner_rejects_undeclared_changes(self):
        (self.root / "analysis" / "run.py").write_text(
            "from pathlib import Path\n"
            "Path('aggregates').mkdir(exist_ok=True)\n"
            "Path('aggregates/out.txt').write_text('42\\n')\n"
            "Path('surprise.txt').write_text('undeclared\\n')\n",
            encoding="utf-8",
        )
        self.write_spec()
        self.commit_freeze()
        code, outcome = execute.run_local(self.root, "EXEC-1")
        self.assertEqual(code, 1)
        self.assertEqual(outcome["status"], "ERROR")
        self.assertIn("surprise.txt", outcome["extra"])

    def test_local_runner_blocks_policy_it_cannot_enforce(self):
        self.write_spec()
        (self.root / ".research" / "policy.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "resources": [
                        {"match": "data/**", "class": "restricted"},
                        {"match": "analysis/**", "class": "restricted"},
                    ],
                    "rules": {
                        "restricted": {
                            "model_egress": False,
                            "network_egress": False,
                        }
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.commit_freeze()
        code, outcome = execute.run_local(self.root, "EXEC-1")
        self.assertEqual(code, 3, outcome)
        self.assertEqual(outcome["status"], "NOT_ENFORCEABLE")


if __name__ == "__main__":
    unittest.main()
