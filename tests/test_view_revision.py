"""A fresh agent can locate and revise an adopted claim through the public dispatcher."""
import copy
import json
import subprocess
import sys
import unittest

import test_supervision as fixtures


class RevisionSessionTests(unittest.TestCase):
    def setUp(self):
        self.study = fixtures.SupervisionTests()
        self.study.setUp()
        self.addCleanup(self.study.tearDown)
        self.root = self.study.root

    def view(self, *args):
        cmd = [sys.executable, str(fixtures.SCRIPTS / "research.py"), "view", *args,
               "--root", str(self.root), "--audience", "model", "--format", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def admit(self, decision):
        request = self.study.request(decision["action"], decision["target"]["id"], decision)
        result = fixtures.supervise.admit(self.root, request)
        self.assertEqual(result["disposition"], "ALLOW", result)
        fixtures.commit(self.root, f"Adopt {decision['id']} and its admission event")

    def inquiry(self, identity, decision, previous=None, *, question_id="Q1", resource_path="source.txt", commit=True):
        resource = fixtures.resources.resource(self.root, "measure", "attendance",
                                               resource_path)
        record = {
            "schema_version": "inquiry@1", "id": identity, "project_id": self.study.project,
            "question_id": question_id, "question": "Does the observed mean generalize to all visits?",
            "importance": "The service needs to know which visits to include in its policy.",
            "stage": "assessment", "assessed_by": "fixture-researcher", "supersedes": previous,
            "resources": {"RES-MEASURE": resource},
            "dependencies": [{"resource_ref": "RES-MEASURE", "binding": "follow_current",
                              "current_path": resource_path}],
            "criteria": [
                {"id": "coverage", "dimension": "design",
                 "desired": "Verify that the definition includes all scheduled visits.",
                 "assessment": "limited" if previous else "unmet",
                 "reason": "Postponed visits are excluded." if previous else "Coverage is uncertain.",
                 "decision_refs": []},
                {"id": "conclusion", "dimension": "conclusion",
                 "desired": "Establish a claim at the scope supported by the observed visits.",
                 "assessment": "met", "reason": "The positive mean has an applicable review.",
                 "decision_refs": [decision]},
            ],
            "next_action": None if previous else {
                "criterion": "coverage", "kind": "investigate",
                "action": "Compare which visits count under the two definitions.",
                "expected_signal": "Determine whether postponements are excluded."},
            "observation": {"text": "The mean is still 2, but applies only to retained visits.",
                            "resource_ref": "RES-MEASURE"} if previous else None,
        }
        fixtures.write(self.root, f".research/inquiries/{identity}.json", record)
        if commit:
            fixtures.commit(self.root, f"Record {identity}")
        return record

    def adopt_independent_control(self, template):
        text = "Both clinics submitted their March reports."
        (self.root / "control.md").write_text(text + "\n")
        (self.root / "reporting-log.txt").write_text("March\nClinic A: received\nClinic B: received\n")
        revision = fixtures.commit(self.root, "Separate claim and its reporting log")
        review = copy.deepcopy(template)
        review.update(id="REVIEW-3", reviewed_commit=revision)
        witness = fixtures.supervise.attest(self.root, "REVIEW-3", "external-reviewer",
                                           "REVIEW_ATTESTED", "Control claim examined in test fixture.")
        review["reviewer"]["attestation_ref"] = witness["attestation_ref"]
        paper = fixtures.resources.resource(self.root, "manuscript", "control", "control.md", revision)
        log = fixtures.resources.resource(self.root, "source", "reports", "reporting-log.txt", revision)
        log.update(source_uri="fixture://reporting-log", retrieved_at=fixtures.events.now())
        review["resources"] = {"RES-PAPER": paper, "RES-SOURCE": log}
        review["dependencies"][0]["current_path"] = paper["path"]
        review["dependencies"][1]["current_path"] = log["path"]
        review["claims"][0].update(id="C2", text=text)
        review["coverage"]["claim_ids"] = ["C2"]
        report = self.root / ".research/reviews/REVIEW-3.md"
        report.write_text("Both clinics appear in the reporting log.\n")
        review["report"] = {"path": report.relative_to(self.root).as_posix(),
                            "sha256": fixtures.resources.fingerprint(report.read_bytes())}
        fixtures.write(self.root, ".research/reviews/REVIEW-3.json", review)
        fixtures.commit(self.root, "Review the independent claim")
        decision = self.study.decision(review, "DEC-3")
        decision["target"].update(id="C2", text=text, current_path=paper["path"])
        decision["judgments"] = ["REVIEW-3#C2"]
        decision["basis"]["origin_refs"] = ["reports"]
        self.admit(decision)

    def test_changed_measure_narrowed_after_new_review_control_remains_current(self):
        with (self.root / "RESEARCH.map").open("a") as file:
            file.write("\n## Gates\n| 5 Analysis | reached | | |\n")
        (self.root / "source.txt").write_text("Mean among scheduled visits: 2.\n")
        self.study.freeze = fixtures.commit(self.root, "Document completed analysis")
        first_review = self.study.create_review(source_binding="follow_current")
        self.admit(self.study.decision(first_review))
        self.adopt_independent_control(first_review)
        self.inquiry("INQ-1", "DEC-1")
        self.inquiry("INQ-3", "DEC-3", question_id="Q2", resource_path="reporting-log.txt")
        initial_loop = self.view("status")["inquiries"][0]
        self.assertEqual(initial_loop["question_id"], "Q1")
        self.assertEqual(initial_loop["next"]["state"], "proposed")
        self.assertIn("postponements", initial_loop["next"]["expected_signal"])
        initial = self.view("explain", "DEC-1")["entries"]
        original = initial[0]
        source = next(e for e in initial if "SOURCE1" in e["aliases"])
        self.assertEqual(original["details"]["state"], "CURRENT")

        (self.root / "source.txt").write_text("Mean among retained visits: 2. Postponed visits excluded.\n")
        impact = self.view("impact", source["selector"])["entries"]
        affected = {e["label"]: e for e in impact if e["kind"] == "decision"}
        self.assertEqual(set(affected), {"DEC-1"})
        self.assertEqual(affected["DEC-1"]["details"]["state"], "STALE")
        self.assertTrue(any(e["label"] == "INQ-1" for e in impact))
        reopened = self.view("status")["inquiries"][0]
        self.assertEqual(reopened["next"]["state"], "reassess")
        self.assertFalse(reopened["criteria"][1]["applicable"])
        self.assertEqual(self.view("explain", "DEC-3")["entries"][0]["details"]["state"], "CURRENT")
        self.assertEqual(self.view("explain", "Q2")["entries"][0]["details"]["next"]["state"], "proposed")

        self.study.text = "The observed mean is positive among retained visits."
        (self.root / "documents/paper.md").write_text(self.study.text + "\n")
        self.study.freeze = fixtures.commit(self.root, "Narrow the claim to the revised measure")
        second_review = self.study.create_review("REVIEW-2", source_binding="follow_current")
        successor = self.study.decision(second_review, "DEC-2")
        successor.update(action="REVISE_DECISION", disposition="narrow", supersedes="DEC-1")
        self.admit(successor)
        self.inquiry("INQ-2", "DEC-2", "INQ-1", commit=False)
        self.assertEqual(self.view("explain", "Q1")["entries"][0]["label"], "INQ-1")
        self.assertEqual(self.view("explain", "INQ-2")["entries"][0]["details"]["next"]["state"], "verify")
        fixtures.commit(self.root, "Document observation and response to it")

        current = self.view("explain", "DEC-2")["entries"][0]
        self.assertEqual(current["text"], self.study.text)
        self.assertEqual(current["details"]["state"], "CURRENT")
        self.assertEqual(current["details"]["supersedes"], "DEC-1")
        self.assertEqual(current["details"]["judgments"], ["REVIEW-2#C1"])
        history = self.view("explain", original["selector"])["entries"][0]
        self.assertEqual(history["text"], original["text"])
        self.assertEqual(history["details"]["state"], "SUPERSEDED")
        control = self.view("explain", "DEC-3")["entries"][0]
        self.assertEqual(control["details"]["state"], "CURRENT")
        resumed = self.view("status")["inquiries"]
        self.assertEqual([r["id"] for r in resumed], ["INQ-2", "INQ-3"])
        self.assertEqual(resumed[0]["next"]["state"], "closed")
        self.assertEqual(resumed[0]["criteria"][0]["assessment"], "limited")
        self.assertTrue(resumed[0]["criteria"][1]["applicable"])
        self.assertIn("still 2", resumed[0]["observation"]["text"])
        self.assertEqual(self.view("explain", "INQ-1")["entries"][0]["details"]["state"], "SUPERSEDED")
        self.assertEqual(self.view("explain", "Q1")["entries"][0]["label"], "INQ-2")

    def test_pre_analysis_inquiry_is_visible_without_exposing_later_assessment(self):
        plan = fixtures.resources.resource(self.root, "protocol", "question", "protocol.md")
        record = {
            "schema_version": "inquiry@1", "id": "INQ-1", "project_id": self.study.project,
            "question_id": "Q1", "question": "How should we measure attendance?",
            "importance": "The definition determines which visits can inform the service policy.",
            "stage": "planning", "assessed_by": "fixture-researcher", "supersedes": None,
            "resources": {"RES-PLAN": plan}, "dependencies": [{"resource_ref": "RES-PLAN", "binding": "pinned"}],
            "criteria": [{"id": "coverage", "dimension": "design", "desired": "Define both visit populations.",
                          "assessment": "unmet", "reason": "Definitions list only one population.", "decision_refs": []}],
            "next_action": {"criterion": "coverage", "kind": "investigate", "action": "Compare the two definitions.",
                            "expected_signal": "List the visits counted by only one definition."},
            "observation": None,
        }
        fixtures.write(self.root, ".research/inquiries/INQ-1.json", record)
        fixtures.commit(self.root, "Plan before analysis")
        report = self.view("status")
        self.assertEqual(report["inquiries"][0]["next"]["state"], "proposed")

        record.update(id="INQ-2", stage="assessment", supersedes="INQ-1",
                      observation={"text": "outcome-only-token", "resource_ref": "RES-PLAN"})
        fixtures.write(self.root, ".research/inquiries/INQ-2.json", record)
        fixtures.commit(self.root, "Record material awaiting analysis eligibility")
        report = self.view("status")
        self.assertEqual(report["inquiries"][0]["next"]["state"], "verify")
        self.assertNotIn("outcome-only-token", json.dumps(report))
        self.assertNotIn("outcome-only-token", json.dumps(self.view("explain", "Q1")))

        fixtures.write(self.root, ".research/policy.json", {
            "version": 1,
            "resources": [{"match": "RESEARCH.map", "class": "public"},
                          {"match": ".research/**", "class": "public"}],
            "rules": {"public": {"model_egress": True, "network_egress": False}},
        })
        restricted = self.view("status")
        self.assertEqual(restricted["inquiries"], [])
        self.assertNotIn(record["question"], json.dumps(restricted))

    def test_restart_recovers_possible_exposure_after_real_failed_execution(self):
        (self.root / "analysis/run.py").write_text("print('outcome-log-only')\nraise SystemExit(7)\n")
        self.study.freeze = fixtures.commit(self.root, "Freeze execution that fails after producing a log")
        request = self.study.request("FIT_CONFIRMATORY", "H1")
        execution = fixtures.supervise.run(self.root, request)
        self.assertEqual(execution["effect"], "executed", execution)
        self.assertEqual(execution["disposition"], "BLOCK")

        resumed = self.view("status")
        operation = next(e for e in resumed["entries"] if request["operation_id"] in e["aliases"])
        self.assertIn("exposure", operation["text"].lower())
        inspection = self.view("explain", operation["selector"])
        self.assertEqual(inspection["entries"][0]["details"]["state"], "failed")
        self.assertNotIn("outcome-log-only", json.dumps([resumed, inspection]))
