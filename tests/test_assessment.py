from __future__ import annotations

import hashlib
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


assessment = load(
    "research_assessment",
    "skills/research-map/scripts/assessment.py",
)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init")
        git(self.root, "config", "user.email", "test@example.com")
        git(self.root, "config", "user.name", "Test")
        (self.root / ".research" / "assessments").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, *, answer: str = "SUPPORTS", digest: str | None = None) -> Path:
        evidence = "The reported estimate was lower in the exposed group."
        payload = {
            "id": "ASMT-1",
            "spec": "citation-entailment@1",
            "target": {
                "kind": "claim",
                "id": "C1",
                "text": "The exposed group had a lower observed estimate.",
            },
            "evidence": [
                {
                    "source": "doi:10.example/test",
                    "locator": "p. 1",
                    "text": evidence,
                    "sha256": digest or hashlib.sha256(evidence.encode("utf-8")).hexdigest(),
                }
            ],
            "answer": answer,
            "basis": "The evidence reports the same comparison and direction.",
            "evaluator": {
                "backend": "test",
                "model": "fixture",
                "procedure": "assessor@1",
            },
        }
        path = self.root / ".research" / "assessments" / "ASMT-1.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

    def test_committed_assessment_passes(self):
        self.record()
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "record assessment")
        result = assessment.check_assessments(self.root)
        self.assertEqual(result.status, "PASS", result.lines)

        (self.root / "RESEARCH.map").write_text("# assessment-only validation\n", encoding="utf-8")
        composed = subprocess.run(
            [
                sys.executable,
                str(VALIDATE_ALL),
                "RESEARCH.map",
                "--root",
                str(self.root),
                "--only",
                "assessments",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(composed.returncode, 0, composed.stdout + composed.stderr)
        self.assertIn("assessments", composed.stdout)
        self.assertIn("RESULT PASS", composed.stdout)

    def test_evidence_digest_must_match_exact_text(self):
        self.record(digest="0" * 64)
        result = assessment.check_assessments(self.root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("does not match" in line for line in result.lines), result.lines)

    def test_answer_must_belong_to_versioned_spec(self):
        self.record(answer="PROBABLY")
        result = assessment.check_assessments(self.root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("answer must be one of" in line for line in result.lines), result.lines)

    def test_committed_assessment_is_append_only(self):
        path = self.record()
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "record assessment")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["basis"] = "rewritten after the judgment"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        result = assessment.check_assessments(self.root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("changed after first commit" in line for line in result.lines), result.lines)


if __name__ == "__main__":
    unittest.main()
