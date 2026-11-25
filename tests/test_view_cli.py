"""Contract tests through the installed runtime's public dispatcher."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

CLI = Path(__file__).resolve().parents[1] / "skills/research-map/scripts/research.py"
sys.path.insert(0, str(CLI.parent))
import view


class ViewCliTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, str(CLI), "view", *map(str, args)],
                              capture_output=True, text=True)

    def test_standalone_document_in_two_processes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "paper.md"
            document.write_text("# Study\n\nThe observed count was six.\n")
            response = self.invoke("status", "--document", document, "--format", "json")
            self.assertEqual(response.returncode, 0, response.stderr)
            report = json.loads(response.stdout)
            self.assertEqual(report["schema_version"], "research-view@1")
            self.assertTrue(report["entries"])
            self.assertEqual(report["status"], "complete")
            self.assertIn("No separate review supplied.", str(report["entries"]))
            self.assertIn("No next action", str(report["overview"]))
            item = report["entries"][0]
            explanation = self.invoke("explain", item["selector"], "--document", document)
            self.assertEqual(explanation.returncode, 0, explanation.stderr)
            self.assertIn(item["selector"], explanation.stdout)
            fresh = self.invoke("status", "--document", document, "--format", "json")
            self.assertEqual(report["snapshot"]["id"], json.loads(fresh.stdout)["snapshot"]["id"])
            self.assertEqual(list(root.iterdir()), [document])

    def test_unlinked_source_and_unknown_target_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "RESEARCH.map").write_text(
                "## Layout\n- protocol: protocol.md\n## Question\nMeasure? → `protocol.md#question`\n")
            (root / "protocol.md").write_text("## Question\nHow is attendance measured?")
            (root / "manual.md").write_text("A newly supplied description.")

            def impact(target):
                answer = self.invoke("impact", target, "--root", root, "--format", "json")
                return json.loads(answer.stdout)

            report = impact("manual.md")
            self.assertEqual(report["impact"], "no_declared_dependents")
            item = report["entries"][0]
            self.assertEqual(impact(item["selector"])["target"], item["selector"])
            self.assertEqual(impact("missing.md")["status"], "not_found")

    def test_worktree_and_git_state_stay_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "RESEARCH.map").write_text("## Question\nSee `protocol.md#question`\n")
            (root / "protocol.md").write_text("## Question\nWho was included?\n")

            def files():
                return {p.relative_to(root): p.read_bytes() if p.is_file() else None
                        for p in root.rglob("*")}

            before = files()
            response = self.invoke("status", "--root", root, "--audience", "model", "--format", "json")
            self.assertEqual(response.returncode, 0, response.stderr)
            report = json.loads(response.stdout)
            self.assertIn("Who was included?", str(report["entries"]))
            self.assertIsNone(report["snapshot"]["revision"])
            self.assertEqual(before, files())

    def test_retry_discards_a_mixed_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "paper.md"
            path.write_text("Question: First question")
            args = view.argparse.Namespace(audience="model", operation="status", document=path,
                                           root=None, target=None, review=None)
            collect = view.view_document.collect

            def read_then_change(reader, document, review):
                entries = collect(reader, document, review)
                document.write_text(document.read_text() + " changed")
                return entries

            with patch.object(view.view_document, "collect", side_effect=read_then_change) as reader:
                report = view.query(args)
            self.assertEqual(reader.call_count, 2)
            self.assertEqual(report["status"], "partial")
            self.assertEqual(report["entries"], [])
            self.assertIsNone(report["snapshot"]["id"])
            self.assertNotIn("First question", str(report))

    def test_unknown_target_has_distinct_machine_readable_outcome(self):
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "paper.md"
            document.write_text("A reported observation.")
            answer = self.invoke("explain", "C999", "--document", document, "--format", "json")
            self.assertEqual(answer.returncode, 1, answer.stderr)
            self.assertEqual(json.loads(answer.stdout)["status"], "not_found")

    def test_unrelated_document_options_are_rejected(self):
        result = self.invoke("status", "--root", ".", "--review", "report.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--review", result.stderr)


if __name__ == "__main__":
    unittest.main()
