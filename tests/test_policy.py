from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATE_ALL = ROOT / "skills" / "research-map" / "scripts" / "validate_all.py"


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


policy = load("research_policy", "skills/research-map/scripts/policy.py")


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".research").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, resources=None):
        payload = {
            "version": 1,
            "resources": resources
            or [
                {"match": "data/raw/**", "class": "restricted"},
                {"match": "aggregates/**", "class": "derived"},
            ],
            "rules": {
                "restricted": {
                    "model_egress": False,
                    "network_egress": False,
                },
                "derived": {
                    "model_egress": True,
                    "network_egress": True,
                },
            },
        }
        (self.root / ".research" / "policy.json").write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_valid_policy_is_deterministic_and_fail_closed_for_unmatched_resources(self):
        self.write()
        _, result = policy.load_policy(self.root)
        self.assertEqual(result.status, "PASS", result.lines)
        self.assertEqual(
            policy.decide(self.root, "data/raw/patients.csv", "model_egress"),
            ("DENY", "restricted"),
        )
        self.assertEqual(
            policy.decide(self.root, "aggregates/table.csv", "model_egress"),
            ("ALLOW", "derived"),
        )
        self.assertEqual(
            policy.decide(self.root, "notes/private.txt", "model_egress"),
            ("UNDECLARED", ""),
        )

        (self.root / "RESEARCH.map").write_text("# policy-only validation\n", encoding="utf-8")
        composed = subprocess.run(
            [
                sys.executable,
                str(VALIDATE_ALL),
                "RESEARCH.map",
                "--root",
                str(self.root),
                "--only",
                "policy",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(composed.returncode, 0, composed.stdout + composed.stderr)
        self.assertIn("policy", composed.stdout)
        self.assertIn("RESULT PASS", composed.stdout)

    def test_overlapping_resource_rules_are_rejected(self):
        self.write(
            [
                {"match": "data/**", "class": "restricted"},
                {"match": "data/raw/**", "class": "restricted"},
            ]
        )
        _, result = policy.load_policy(self.root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("overlapping resource rules" in line for line in result.lines), result.lines)

    def test_resource_rules_cannot_escape_or_use_implicit_glob_precedence(self):
        self.write([{"match": "../secret/**", "class": "restricted"}])
        _, result = policy.load_policy(self.root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("repository-relative exact path" in line for line in result.lines), result.lines)

        self.write([{"match": "data/*.csv", "class": "restricted"}])
        _, result = policy.load_policy(self.root)
        self.assertEqual(result.status, "FAIL")

    def test_missing_policy_is_not_implicit_permission(self):
        self.assertEqual(
            policy.decide(self.root, "data/raw/patients.csv", "network_egress"),
            ("UNDECLARED", ""),
        )


if __name__ == "__main__":
    unittest.main()
