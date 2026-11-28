import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/research-map/scripts"))
import view_native


class Reader:
    operation = "status"

    def __init__(self):
        self.issues = []
        self.opened = []

    def read(self, path):
        self.opened.append(path)
        return path.read_bytes()

    def watch_dir(self, path, glob):
        return sorted(path.glob(glob))

    def permits(self, path):
        return True

    def partial(self, message):
        self.issues.append(message)


class NativeStudyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.reader = Reader()
        self.write("study/protocol.md", "## Question\nWho changes?\nEstimand: difference\nWho cares: policy team\n")
        self.write("RESEARCH.map", "## Layout\n- protocol: study/protocol.md\n- documents: paper\n"
                   "## Question\nWho changes? → `study/protocol.md#question`\nProblem: PENDING\n"
                   "## Hypotheses\n| H1 | increases | falls | — | `study/protocol.md#h1` |\n"
                   "## Gates\n| 5 Analysis | pending | | |\n## Last session\n- Next: inspect coverage\n")
        self.write("paper/a.md", "Observed A. <!-- claim:C1 result:R1 -->\n")
        self.write("paper/b.md", "Observed B. <!-- claim:C1 result:R2 -->\n")

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    def completed(self):
        path = self.root / "RESEARCH.map"
        path.write_text(path.read_text().replace("5 Analysis | pending", "5 Analysis | reached"))

    def test_initial_question_uses_protocol_without_opening_outcomes(self):
        entries = view_native.collect(self.reader, self.root)
        protocol = next(e for e in entries if e["kind"] == "question" and e["source"] == "study/protocol.md")
        self.assertIn("policy team", str(protocol))
        self.assertIn("inspect coverage", str(entries))
        self.assertFalse(any(p.parent.name == "paper" for p in self.reader.opened))

    def test_each_claim_and_each_support_is_an_occurrence(self):
        self.completed()
        for n in [1, 2]:
            receipt = {"id": f"RUN-{n}", "test": f"T{n}", "analysis_plan_freeze": "f" * 40,
                       "outputs": [{"result": f"R{n}", "artifact": f"results/{n}.csv"}]}
            self.write(f".research/runs/RUN-{n}.json", json.dumps(receipt))
        self.write("paper/b.md", "Observed B. <!-- claim:C1 result:R2 --> Other. <!-- claim:C1 result:R2 -->\n")
        entries = view_native.collect(self.reader, self.root)
        claims = [e for e in entries if "C1" in e["aliases"]]
        self.assertEqual(len({e["selector"] for e in claims}), 3)
        r1 = next(e for e in entries if "R1" in e["aliases"])
        self.assertEqual(r1["related"], [c["selector"] for c in claims if c["source"] == "paper/a.md"])
        self.assertIn("f" * 40, str(r1))
        self.assertFalse(any(p.suffix == ".csv" for p in self.reader.opened))

    def test_pointer_symlink_never_opens_external_file(self):
        (self.root / "study/protocol.md").unlink()
        (self.root / "study/protocol.md").symlink_to(__file__)
        view_native.collect(self.reader, self.root)
        self.assertNotIn(self.root / "study/protocol.md", self.reader.opened)
        self.assertTrue(self.reader.issues)

    def test_brief_records_evidence_but_does_not_open_the_observations(self):
        path = self.root / "RESEARCH.map"
        path.write_text(path.read_text().replace("Problem: PENDING", "Problem: SHOWN → `brief.md`"))
        self.write("brief.md", "# Premise\nMeasure: activity\nBasis: local — `raw.csv`\n"
                              "Verdict: INCONCLUSIVE — missing contrast\n")
        self.write("raw.csv", "not for inspection")
        entries = view_native.collect(self.reader, self.root)
        self.assertIn("missing contrast", str(entries))
        self.assertNotIn(self.root / "raw.csv", self.reader.opened)
        self.assertTrue(any("disagree" in issue for issue in self.reader.issues))

    def test_ambiguous_receipts_do_not_claim_a_unique_source(self):
        self.completed()
        for n in [1, 2]:
            self.write(f".research/runs/RUN-{n}.json", json.dumps({
                "id": f"RUN-{n}", "outputs": [{"result": "R1", "artifact": "a.csv"}]}))
        entries = view_native.collect(self.reader, self.root)
        claim = next(e for e in entries if e["kind"] == "claim" and e["source"] == "paper/a.md")
        self.assertEqual(claim["details"]["support_status"], "ambiguous")
        self.assertIn("RUN-2", [alias for e in entries for alias in e["aliases"]])

    def test_model_does_not_emit_text_based_on_an_explicit_denied_source(self):
        self.completed()
        self.reader.audience = "model"
        self.reader.has_policy = lambda _: True
        self.reader.permits = lambda path: path.name not in {"private.csv", "protocol.md"}
        self.write(".research/runs/RUN-1.json", json.dumps({
            "id": "RUN-1", "inputs": [{"path": "private.csv"}],
            "outputs": [{"result": "R1", "artifact": "a.csv"}]}))
        entries = view_native.collect(self.reader, self.root)
        self.assertNotIn("protocol.md", str(entries))
        self.assertNotIn("Observed A", str(entries))
        self.assertNotIn("private.csv", str(self.reader.issues))
        self.assertIn("inspect coverage", str(entries))

    def test_impact_from_receipt_input_uses_receipt_not_current_plan(self):
        self.completed()
        self.write("analysis-plan.md", "## H1\nPrimary test: T9\nGenerated from: DATA9\n")
        self.write(".research/runs/RUN-1.json", json.dumps({
            "id": "RUN-1", "test": "T1", "inputs": [{"id": "DATA1", "path": "data.csv", "role": "discovery"}],
            "outputs": [{"result": "R1", "artifact": "r.csv"}]}))
        entries = view_native.collect(self.reader, self.root)
        input_item = next(e for e in entries if "data.csv" in e["aliases"])
        run = next(e for e in entries if e["kind"] == "run")
        self.assertEqual(input_item["related"], [run["selector"]])
        self.assertEqual(run["details"]["run"]["test"], "T1")
        self.assertNotIn("T9", str(run))
        self.assertNotIn(self.root / "data.csv", self.reader.opened)

    def test_claim_explains_limits_of_its_frozen_hypothesis(self):
        self.completed()
        self.write("paper/b.md", "")
        self.write("analysis-plan.md", "## H1\nPrimary test: T1\nMode: confirmatory\n"
                   "May claim: FROZEN BOUNDARY\nMay not claim: FROZEN CAUSAL LIMIT\n"
                   "## H2\nMay claim: UNRELATED LIMIT\n")
        def git(*args):
            return subprocess.check_output(["git", *args], cwd=self.root, text=True).strip()

        git("init", "-q")
        self.write(".gitattributes", "analysis-plan.md diff=plan-test\n")
        # A configured text converter that fails must never participate in a view.
        git("config", "diff.plan-test.textconv", "false")
        git("add", "analysis-plan.md", ".gitattributes")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.org", "commit", "-qm", "freeze")
        commit = git("rev-parse", "HEAD")
        self.write("analysis-plan.md", "## H1\nPrimary test: T2\nMay claim: CURRENT BOUNDARY\n"
                   "## Methods\nA currently planned survey.\n")
        self.write(".research/runs/RUN-1.json", json.dumps(
            {"id": "RUN-1", "hypothesis": "H1", "analysis_plan_freeze": commit, "test": "T1",
             "inputs": [], "outputs": [{"result": "R1", "artifact": "never-read.csv"}]}))
        from view import select
        entries = view_native.collect(self.reader, self.root)
        status, explanation = select(entries, "explain", "C1")
        self.assertEqual(status, "complete")
        self.assertIn("FROZEN BOUNDARY", str(explanation))
        self.assertIn("FROZEN CAUSAL LIMIT", str(explanation))
        self.assertNotIn("UNRELATED LIMIT", str(explanation))
        self.assertNotIn("CURRENT BOUNDARY", str(explanation))
        cli = Path(view_native.__file__).with_name("research.py")
        rendered = subprocess.check_output([sys.executable, str(cli), "view", "explain", "C1",
                                            "--root", str(self.root)], text=True)
        self.assertIn("FROZEN BOUNDARY", rendered)
        self.assertNotIn("CURRENT BOUNDARY", rendered)
        self.assertTrue(any(item["kind"] == "method" and "currently planned survey" in item["text"]
                            for item in entries))
        self.reader.audience = "model"
        self.reader.has_policy = lambda _: True
        self.reader.permits = lambda path: path.name != "analysis-plan.md"
        entries = view_native.collect(self.reader, self.root)
        self.assertNotIn("FROZEN BOUNDARY", str(entries))
        self.assertNotIn("CURRENT BOUNDARY", str(entries))

    def test_deferred_idea_can_be_resumed_with_its_entry_condition(self):
        path = self.root / "RESEARCH.map"
        path.write_text(path.read_text().replace(
            "## Last session", "## Deferred\n- 2026-09-28: Check attrition — enters when: a follow-up sample arrives\n"
            "## Last session"))
        self.assertFalse(view_native.analysis_reached(path.read_text()))
        cli = Path(view_native.__file__).with_name("research.py")
        def invoke(*args):
            raw = subprocess.check_output([sys.executable, str(cli), "view", *args, "--root",
                                           str(self.root), "--format", "json"], text=True)
            return json.loads(raw)
        report = invoke("status")
        idea = next(e for e in report["entries"] if e["kind"] == "deferred")
        resumed = invoke("explain", idea["selector"])["entries"][0]
        self.assertIn("Check attrition", resumed["text"])
        self.assertEqual(resumed["details"]["entry_condition"], "a follow-up sample arrives")
        self.assertEqual(resumed["details"]["basis"], "research map")
        self.assertEqual(resumed["details"]["recorded_date"], "2026-09-28")
        self.assertFalse(resumed["related"])
        self.completed()
        self.assertTrue(view_native.analysis_reached(path.read_text()))
