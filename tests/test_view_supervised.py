import copy
from datetime import datetime, timezone
import unittest
from unittest.mock import patch

import test_supervision as fixtures
import view_supervised


class Reader:
    audience = "local"
    as_of = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __init__(self):
        self.pending = []
        self.watched = set()

    def partial(self, message):
        self.pending.append(message)

    def permits(self, path):
        return True

    def has_policy(self, path):
        return False

    def watch_file(self, path):
        self.watched.add(path)

    def watch_dir(self, path, pattern):
        return sorted(path.glob(pattern))

    def read(self, path):
        self.watch_file(path)
        return path.read_bytes()


class SupervisedViewTests(unittest.TestCase):
    def setUp(self):
        self.study = fixtures.SupervisionTests()
        self.study.setUp()
        self.addCleanup(self.study.tearDown)
        self.root = self.study.root
        self.reader = Reader()

    def test_justification_routes_and_versions_remain_explainable_after_drift(self):
        review = self.study.create_review()
        decision = self.study.decision(review)
        source = decision["resources"]["RES-SOURCE"]
        paper = decision["resources"]["RES-PAPER"]
        decision["resources"]["RES-JUST"] = {
            **paper, "kind": "argument", "logical_id": "rationale", "locator": "paragraph 1",
        }
        decision["rationale_ref"] = "RES-JUST"
        decision["basis"]["routes"] = [
            {"id": "manual", "all_of": [{"resource_ref": "RES-SOURCE",
                                         "binding": "follow_current", "current_path": source["path"]}]},
            {"id": "historical", "all_of": [{"resource_ref": "RES-SOURCE", "binding": "pinned"}]},
        ]
        self.assertEqual(fixtures.supervise.admit(
            self.root, self.study.request("ADOPT_CLAIM", record=decision))["disposition"], "ALLOW")
        fixtures.commit(self.root)
        (self.root / source["path"]).write_text("The meaning of this measure has changed.\n")
        entries = view_supervised.collect(self.reader, self.root)
        decision_entry = next(e for e in entries if e["kind"] == "decision")
        self.assertEqual(decision_entry["details"]["state"], "STALE")
        self.assertEqual(decision_entry["text"], self.study.text)
        rationale = next(e for e in entries if "rationale" in e["aliases"])
        self.assertIn(decision_entry["selector"], rationale["related"])
        self.assertEqual(rationale["details"]["revision"], self.study.freeze)
        self.assertEqual(rationale["details"]["locator"], "paragraph 1")
        routes = {e["label"]: e for e in entries if e["kind"] == "route"}
        self.assertEqual(routes["manual"]["details"]["dependencies"][0]["status"], "STALE")
        self.assertEqual(routes["historical"]["details"]["dependencies"][0]["status"], "PASS")
        by_route = {item["id"]: item for item in decision_entry["details"]["support_routes"]}
        self.assertEqual(by_route["manual"]["status"], "STALE")
        self.assertEqual(by_route["historical"], {
            "id": "historical", "selector": routes["historical"]["selector"], "status": "PASS"})
        self.assertIn(decision_entry["selector"], routes["historical"]["related"])
        self.assertIn(self.root / source["path"], self.reader.watched)

    def test_pre_analysis_status_never_opens_supervised_outcomes(self):
        review = self.study.create_review()
        decision = self.study.decision(review)
        decision["resources"]["RES-SOURCE"]["kind"] = "result"
        fixtures.write(self.root, ".research/decisions/DEC-1.json", decision)
        map_path = self.root / "RESEARCH.map"
        with map_path.open("a") as target:
            target.write("## Gates\n| Phase | State |\n| --- | --- |\n| 5 Analysis | pending |\n")
        self.reader.operation = "status"
        with patch("view_supervised.Store", side_effect=AssertionError("Store would load results")):
            entries = view_supervised.collect(self.reader, self.root)
        self.assertFalse(entries)
        self.assertIn(map_path, self.reader.watched)
        self.assertNotIn(self.root / ".research/decisions/DEC-1.json", self.reader.watched)
        self.assertNotIn(self.root / "source.txt", self.reader.watched)
        self.assertTrue(any("analysis" in note for note in self.reader.pending))

    def test_two_localizers_same_resource_remain_distinct(self):
        r = self.study.create_review()
        decision = self.study.decision(r)
        for rid, locator in [("RES-JUST", "paragraph 1"), ("RES-OTHER", "paragraph 2")]:
            decision["resources"][rid] = dict(decision["resources"]["RES-SOURCE"], locator=locator)
        decision["rationale_ref"] = "RES-JUST"
        decision["basis"]["routes"][0]["all_of"][0]["resource_ref"] = "RES-OTHER"
        fixtures.write(self.root, ".research/decisions/DEC-1.json", decision)
        entries = view_supervised.collect(self.reader, self.root)
        refs = [e for e in entries if e["kind"] == "resource" and e["details"].get("locator") in ("paragraph 1", "paragraph 2")]
        self.assertEqual(len({e["selector"] for e in refs}), 2)

    def test_partial_model_read_omits_copied_supervised_prose(self):
        primary_review = self.study.create_review()
        decision = self.study.decision(primary_review)
        fixtures.write(self.root, ".research/decisions/DEC-1.json", decision)
        control_text = "A separate, publicly sourced finding."
        (self.root / "control.md").write_text(control_text)
        control_commit = fixtures.commit(self.root)
        control_doc = fixtures.resources.resource(self.root, "source", "control", "control.md", control_commit)
        control_doc.update(source_uri="fixture://public-control", retrieved_at=fixtures.events.now())
        control_review = copy.deepcopy(primary_review)
        control_review.update(id="REVIEW-2", reviewed_commit=control_commit,
                              resources={"RES-CONTROL": control_doc},
                              dependencies=[{"resource_ref": "RES-CONTROL", "binding": "pinned"}])
        control_review["reviewer"]["attestation_ref"] = fixtures.supervise.attest(
            self.root, "REVIEW-2", "external-reviewer", "REVIEW_ATTESTED", "Reviewed independent control.")["attestation_ref"]
        control_review["coverage"].update(documents=["RES-CONTROL"], claim_ids=["C2"])
        control_review["claims"][0].update(id="C2", text=control_text, resource_ref="RES-CONTROL", evidence=["RES-CONTROL"])
        report = self.root / ".research/reviews/control.md"
        report.write_text("Reviewed the control statement against control.md.")
        control_review["report"] = {"path": ".research/reviews/control.md",
                                    "sha256": fixtures.resources.fingerprint(report.read_bytes())}
        fixtures.write(self.root, ".research/reviews/REVIEW-2.json", control_review)
        fixtures.commit(self.root)
        control = copy.deepcopy(decision)
        control.update(id="DEC-2", resources={"RES-CONTROL": control_doc}, judgments=["REVIEW-2#C2"],
                       rationale_ref="RES-CONTROL")
        control["target"] = {"kind": "claim", "id": "C2", "text": control_text,
                             "resource_ref": "RES-CONTROL", "binding": "pinned"}
        control["basis"] = {"routes": [{"id": "J1", "all_of": [
            {"resource_ref": "RES-CONTROL", "binding": "pinned"}]}], "origin_refs": ["control"]}
        request = self.study.request("ADOPT_CLAIM", target="C2", record=control)
        self.assertEqual(fixtures.supervise.admit(self.root, request)["disposition"], "ALLOW")
        fixtures.commit(self.root)
        self.reader.audience = "model"
        self.reader.has_policy = lambda path: True
        self.reader.permits = lambda path: path != self.root / "source.txt"
        entries = view_supervised.collect(self.reader, self.root)
        self.assertTrue(any(e["kind"] == "decision" and e["text"] == control_text for e in entries))
        self.assertNotIn(self.study.text, str(entries) + str(self.reader.pending))
        self.assertNotIn("source.txt", str(entries) + str(self.reader.pending))
        self.assertTrue(self.reader.pending)

    def test_review_applicability_uses_one_evaluation_clock(self):
        record = self.study.create_review()
        record["id"] = "REVIEW-2"
        attestation = fixtures.supervise.attest(
            self.root, "REVIEW-2", "external-reviewer", "REVIEW_ATTESTED", "Second fixture review.")
        record["reviewer"]["attestation_ref"] = attestation["attestation_ref"]
        record["dependencies"][1] = {"resource_ref": "RES-SOURCE", "binding": "external_refresh",
                                     "refresh_at": "2030-01-01T00:00:00Z",
                                     "refresh_rule": "Inspect published definition again."}
        fixtures.write(self.root, ".research/reviews/REVIEW-2.json", record)
        fixtures.commit(self.root)
        statuses = []
        for year in (2029, 2031):
            self.reader.as_of = datetime(year, 1, 1, tzinfo=timezone.utc)
            entries = view_supervised.collect(self.reader, self.root)
            item = next(e for e in entries if "REVIEW-2" in e["aliases"])
            statuses.append(item["details"]["state"])
        self.assertEqual(statuses, ["CURRENT", "NOT_VERIFIED"])

    def test_hidden_origin_of_reference_contract_withholds_dependent_judgments(self):
        primary_review = self.study.create_review()
        decision = self.study.decision(primary_review)
        fixtures.write(self.root, ".research/decisions/DEC-1.json", decision)
        secret = "Protected criterion copied into this contract"
        reference = copy.deepcopy(self.study.ref)
        reference["criteria"][0]["text"] = secret
        fixtures.write(self.root, ".research/references/REF-1.json", reference)
        self.reader.audience = "model"
        self.reader.has_policy = lambda path: True
        self.reader.permits = lambda path: path != self.root / "decisions.md"
        entries = view_supervised.collect(self.reader, self.root)
        self.assertNotIn(secret, str(entries) + str(self.reader.pending))
        self.assertNotIn(self.study.text, str(entries) + str(self.reader.pending))
        self.assertTrue(self.reader.pending)

    def test_review_cannot_republish_a_result_with_uncleared_historical_origins(self):
        review = self.study.create_review()
        review["resources"]["RES-SOURCE"]["kind"] = "result"
        fixtures.write(self.root, ".research/reviews/REVIEW-1.json", review)
        self.reader.audience = "model"
        self.reader.has_policy = lambda path: True
        entries = view_supervised.collect(self.reader, self.root)
        self.assertNotIn(self.study.text, str(entries))
        self.assertTrue(self.reader.pending)
