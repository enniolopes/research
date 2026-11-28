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

    def test_existing_file_selector_finds_a_later_rationale_citing_its_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "protocol.md").write_text("## Question\nWhich timetable?\n")
            (root / "RESEARCH.map").write_text(
                "## Layout\n- protocol: protocol.md\n- decisions: log.md\n"
                "## Question\nTiming? → `protocol.md#question`\n")
            log = root / "log.md"
            log.touch()
            manual = root / "manual.md"
            manual.write_text("Definitions, edition 1.")

            def impact(target):
                return json.loads(self.invoke("impact", target, "--root", root, "--audience", "model",
                                              "--format", "json").stdout)

            initial = impact(manual.name)
            self.assertEqual(initial["impact"], "no_declared_dependents")
            selector = initial["target"]
            log.write_text("### D-1 · Definition\nRationale: See `manual.md`.\n")
            self.assertIn("D-1", [e["label"] for e in impact(selector)["entries"]])
            manual.write_text("Definitions, edition 2.")
            self.assertFalse(impact(selector)["entries"])
            self.assertIn("D-1", [e["label"] for e in impact(manual.name)["entries"]])

    def test_decision_citations_explain_and_limit_impact_before_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "RESEARCH.map").write_text(
                "## Layout\n- protocol: protocol.md\n- decisions: decisions.md\n"
                "## Question\nTiming? → `protocol.md#question`\n")
            (root / "protocol.md").write_text("## Question\nAre buses late?\n")
            (root / "decisions.md").write_text(
                "### D-1 · Route B\nKeep the published timetable.\n"
                "Rationale: The timetable is documented in `route-b.md`.\n"
                "Revision condition: A corrected B timetable arrives.\n"
                "### D-2 · Route C\n" + "Interpret the times as forecasts. " * 12 + "\n"
                "Rationale: The operator distinguishes forecasts from departures in\n"
                "At 10:30 the operator supplied `adendo.md#route-c`. See also `adendo.md`.\n"
                "Revision condition: The operator provides the original timetable.\n"
                "- **D-3 · Comparing routes**\nDefer the comparison.\n"
                "Rationale: The classification in `adendo.md` differs across routes.\n"
                "**Revise when:** Obtain comparable records.\n"
                "### D-4 · Future work\nSeek observed trips.\n"
                "Revision condition: We receive `adendo.md`.\n"
                "### D-5 · Restricted decision\n"
                "Rationale: Both `route-b.md` and `field notes.parquet` apply.\n")

            def query(operation, *target):
                response = self.invoke(operation, *target, "--root", root,
                                       "--audience", "model", "--format", "json")
                self.assertEqual(response.returncode, 0, response.stderr)
                return json.loads(response.stdout)

            report = query("impact", "adendo.md")
            self.assertEqual([e["label"] for e in report["entries"] if e["kind"] == "finding"],
                             ["D-2", "D-3"])
            citation = report["entries"][0]
            self.assertEqual(citation["source"], "decisions.md")
            (root / "adendo.md").write_text("UNINSPECTED SOURCE CONTENT\n")
            explanation = query("explain", "D-2")
            self.assertIn(citation["selector"], [e["selector"] for e in explanation["entries"]])
            self.assertNotIn("UNINSPECTED SOURCE CONTENT", str(explanation))
            compact = next(e for e in query("status")["entries"] if e["label"] == "D-2")
            self.assertIn("original timetable", str(compact["details"]["revision_conditions"]))
            self.assertIn("adendo.md", str(compact["details"]["rationale"]))

            (root / ".research").mkdir()
            (root / ".research/policy.json").write_text(json.dumps({
                "version": 1, "resources": [{"match": name, "class": "public"}
                    for name in ("RESEARCH.map", "protocol.md", "decisions.md", "route-b.md")],
                "rules": {"public": {"model_egress": True, "network_egress": False}}}))
            limited = query("status")
            self.assertEqual(limited["status"], "partial")
            self.assertNotIn("adendo.md", str(limited))
            self.assertNotIn("D-2", str(limited))
            self.assertIn("D-1", str(limited))
            self.assertNotIn("field notes.parquet", str(limited))
            traced = query("impact", "route-b.md")
            self.assertEqual([e["label"] for e in traced["entries"] if e["kind"] == "finding"], ["D-1"])
            self.assertFalse(query("impact", citation["selector"])["entries"])

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

    def test_external_review_resumes_from_root_and_traces_only_cited_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "RESEARCH-REVIEW.md"
            report.write_text("## Pergunta\nQuem respondeu?\n## Conclusão\n75 lojas. "
                              "[Dados](original.dat)\n## Incerteza\nCobertura parcial.\n"
                              "## Próxima ação\nConferir a cobertura.")
            def query(operation, *target):
                answer = self.invoke(operation, *target, "--root", root, "--audience", "model",
                                     "--format", "json")
                return json.loads(answer.stdout)

            status = query("status")
            self.assertEqual(status["status"], "complete")
            action, = (e for e in status["entries"] if e["kind"] == "next_action")
            self.assertEqual(query("explain", action["selector"])["entries"][0]["text"],
                             "Conferir a cobertura.")
            impact = query("impact", "original.dat")
            self.assertEqual(impact["impact"], "candidates")
            self.assertEqual([e["kind"] for e in impact["entries"]], ["resource", "claim"])
            (root / "RESEARCH.map").write_text("## Question\nSee `protocol.md#question`\n")
            (root / "protocol.md").write_text("## Question\nWhich population?")
            self.assertNotIn("75 lojas", str(query("status")))

    def test_external_review_withheld_material_is_not_projected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".research").mkdir()
            report = root / "RESEARCH-REVIEW.md"
            report.write_text("## Conclusion\nRestricted finding [source](private.csv)\n"
                              "## Next action\nCheck the protocol.\n")
            rules = {"version": 1, "resources": [{"match": report.name, "class": "public"}],
                     "rules": {"public": {"model_egress": True, "network_egress": False}}}
            (root / ".research/policy.json").write_text(json.dumps(rules))
            def status():
                response = self.invoke("status", "--root", root, "--audience", "model", "--format", "json")
                return json.loads(response.stdout)

            answer = status()
            self.assertEqual(answer["status"], "partial")
            self.assertNotIn("Restricted finding", str(answer))
            self.assertNotIn("private.csv", str(answer))
            self.assertIn("Check the protocol", str(answer))
            (root / "RESEARCH.map").write_text("Hidden native study")
            self.assertNotIn("Check the protocol", str(status()))

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
