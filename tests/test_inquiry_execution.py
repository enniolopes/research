"""Confirmatory actions follow the inquiry proposal through the public CLI."""
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_supervision as fixtures


class InquiryExecutionTests(unittest.TestCase):
    def setUp(self):
        self.study = fixtures.SupervisionTests()
        self.study.setUp()
        self.addCleanup(self.study.tearDown)
        self.root = self.study.root
        protocol = fixtures.resources.resource(self.root, "protocol", "frozen-design", "protocol.md")
        self.record = {
            "schema_version": "inquiry@1", "id": "INQ-1", "project_id": self.study.project,
            "question_id": "Q1", "question": "Is the mean positive?",
            "importance": "Decide whether the threshold has been crossed.",
            "stage": "planning", "assessed_by": "fixture", "supersedes": None,
            "resources": {"RES-PROTOCOL": protocol},
            "dependencies": [{"resource_ref": "RES-PROTOCOL", "binding": "pinned"}],
            "criteria": [{"id": "estimate", "dimension": "evidence", "desired": "Measure the mean",
                          "assessment": "unmet", "reason": "Prospective analysis", "decision_refs": []}],
            "next_action": {"criterion": "estimate", "kind": "investigate", "action": "Run the frozen analysis",
                            "expected_signal": "Mean and decision against the frozen threshold.",
                            "confirmatory": {"execution_id": "EXEC-1", "hypothesis": "H1"}},
            "observation": None,
        }
        self.path = fixtures.write(self.root, ".research/inquiries/INQ-1.json", self.record)
        fixtures.commit(self.root, "Record the pending confirmatory action")

    def cli(self, *args, request=None, root=None):
        command = [sys.executable, str(fixtures.SCRIPTS / "research.py"), *args, "--root", str(root or self.root)]
        if request is not None:
            command += ["--request", "-"]
        result = subprocess.run(command, input=json.dumps(request), text=True, capture_output=True)
        self.assertIn(result.returncode, (0, 1, 2, 3), result.stderr)
        return json.loads(result.stdout)

    def request(self, binding):
        req = self.study.request("FIT_CONFIRMATORY", "H1")
        if binding is not None:
            req["extensions"] = {"inquiry": binding}
        return req

    def test_bound_fit_runs_once_and_remains_traceable_after_import(self):
        before = self.cli("view", "status", "--audience", "model", "--format", "json")
        binding = before["inquiries"][0]["next"]["inquiry_binding"]
        self.assertEqual(binding["criterion"], "estimate")
        result = self.cli("supervise", "run", request=self.request(None))
        self.assertEqual(result["disposition"], "REQUIRE_EVIDENCE", result)

        stale = {**binding, "sha256": "0" * 64}
        self.assertEqual(self.cli("supervise", "run", request=self.request(stale))["disposition"], "REQUIRE_EVIDENCE")
        self.assertFalse((self.root / "aggregates/r1.txt").exists())

        req = self.request(binding)
        result = self.cli("supervise", "run", request=req)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(result["effect"], "executed")
        self.assertTrue(self.cli("supervise", "run", request=req)["cached"])
        after = self.cli("view", "status", "--audience", "model", "--format", "json")
        inquiry = after["inquiries"][0]
        self.assertEqual(inquiry["next"]["state"], "inspect_execution")
        self.assertEqual(inquiry["executions"][0]["operation_id"], req["operation_id"])
        other = self.root.parent / (self.root.name + "-other")
        self.addCleanup(subprocess.run, ["git", "-C", str(self.root), "worktree", "remove", str(other)],
                        capture_output=True)
        fixtures.git(self.root, "worktree", "add", "--detach", str(other))
        retry = self.cli("supervise", "run", request=self.request(binding), root=other)
        self.assertEqual(retry["disposition"], "REQUIRE_EVIDENCE", retry)
        fixtures.commit(self.root, "Record the observed output")
        imported = self.cli("supervise", "import-execution", "--id", req["operation_id"])
        self.assertEqual(imported["effect"], "admitted")
        fixtures.commit(self.root, "Consolidate execution events")

        fixtures.git(other, "switch", "--detach", fixtures.resources.head(self.root))
        resumed = self.cli("view", "status", "--audience", "model", "--format", "json", root=other)
        self.assertEqual(resumed["inquiries"][0]["next"]["state"], "inspect_execution")
        self.assertEqual(resumed["inquiries"][0]["executions"][0]["source"], "committed_event")
        with tempfile.TemporaryDirectory() as independent:
            fixtures.git(self.root, "clone", "--quiet", str(self.root), independent)
            retry = self.cli("supervise", "run", request=self.request(binding), root=independent)
            self.assertEqual(retry["disposition"], "REQUIRE_EVIDENCE", retry)

        successor = {**self.record, "id": "INQ-2", "supersedes": "INQ-1"}
        path = fixtures.write(self.root, ".research/inquiries/INQ-2.json", successor)
        fixtures.commit(self.root, "Update the inquiry after observing completion")
        new_binding = {"id": "INQ-2", "sha256": fixtures.resources.fingerprint(path.read_bytes()),
                       "criterion": "estimate"}
        blocked = self.cli("supervise", "propose", request=self.request(new_binding))
        self.assertTrue(any("already completed" in item["detail"] for item in blocked["obligations"]))
        resumed = self.cli("view", "status", "--format", "json")["inquiries"][0]
        self.assertEqual(resumed["next"], {"state": "inspect_execution"})
        self.assertEqual(resumed["executions"][0]["source"], "committed_event")

    def test_changed_inquiry_and_wrong_execution_are_denied(self):
        proposal = self.cli("view", "status", "--format", "json")["inquiries"][0]["next"]
        req = self.request(proposal["inquiry_binding"])
        req["execution_id"] = "EXEC-2"
        blocked = self.cli("supervise", "run", request=req)
        self.assertNotEqual(blocked["disposition"], "ALLOW")
        self.assertFalse((self.root / "aggregates/r1.txt").exists())

        successor = {**self.record, "id": "INQ-2", "supersedes": "INQ-1"}
        fixtures.write(self.root, ".research/inquiries/INQ-2.json", successor)
        fixtures.commit(self.root, "Supersede the proposal before running")
        blocked = self.cli("supervise", "run", request=self.request(proposal["inquiry_binding"]))
        self.assertEqual(blocked["disposition"], "REQUIRE_EVIDENCE", blocked)
        self.assertFalse((self.root / "aggregates/r1.txt").exists())

    def test_failed_execution_requires_recovery_before_resuming(self):
        (self.root / "analysis/run.py").write_text("print('log-only-token')\nraise SystemExit(7)\n")
        fixtures.commit(self.root, "Commit an analysis that fails after emitting a log")
        binding = self.cli("view", "status", "--format", "json")["inquiries"][0]["next"]["inquiry_binding"]
        req = self.request(binding)
        failed = self.cli("supervise", "run", request=req)
        self.assertEqual(failed["effect"], "executed")
        self.assertEqual(failed["disposition"], "BLOCK")

        resumed = self.cli("view", "explain", "Q1", "--audience", "model", "--format", "json")
        self.assertEqual(resumed["entries"][0]["details"]["next"]["state"], "recover_execution")
        self.assertNotIn("log-only-token", json.dumps(resumed))
        blocked = self.cli("supervise", "run", request=self.request(binding))
        self.assertEqual(blocked["disposition"], "REQUIRE_EVIDENCE", blocked)
        self.assertEqual(fixtures.events.unfinished(self.root), [])

    def test_recovery_survives_a_new_round_for_the_same_analysis(self):
        (self.root / "analysis/run.py").write_text("print('possible exposure')\nraise SystemExit(7)\n")
        fixtures.commit(self.root, "Freeze a failing analysis")
        initial = self.cli("view", "status", "--format", "json")["inquiries"][0]
        request = self.request(initial["next"]["inquiry_binding"])
        self.assertEqual(self.cli("supervise", "run", request=request)["disposition"], "BLOCK")

        successor = {**self.record, "id": "INQ-2", "supersedes": "INQ-1"}
        path = fixtures.write(self.root, ".research/inquiries/INQ-2.json", successor)
        fixtures.commit(self.root, "Revise the inquiry without changing the frozen analysis")
        new_binding = {"id": "INQ-2", "sha256": fixtures.resources.fingerprint(path.read_bytes()),
                       "criterion": "estimate"}
        decision = self.cli("supervise", "propose", request=self.request(new_binding))
        self.assertEqual(decision["disposition"], "REQUIRE_EVIDENCE", decision)
        resumed = self.cli("view", "status", "--format", "json")["inquiries"][0]
        self.assertEqual(resumed["next"], {"state": "recover_execution"})
        self.assertEqual(resumed["executions"][0]["operation_id"], request["operation_id"])

    def test_interrupted_import_reuses_existing_execution_events(self):
        binding = self.cli("view", "status", "--format", "json")["inquiries"][0]["next"]["inquiry_binding"]
        request = self.request(binding)
        self.assertEqual(self.cli("supervise", "run", request=request)["disposition"], "ALLOW")
        fixtures.commit(self.root, "Commit observed output before import")
        event_atomic = fixtures.events.atomic

        def interrupt_after_start(path, record):
            if record.get("type") == "EXECUTION_COMPLETED":
                raise OSError("fixture interruption after writing the start event")
            event_atomic(path, record)

        with patch.object(fixtures.events, "atomic", side_effect=interrupt_after_start):
            with self.assertRaises(OSError):
                fixtures.supervise.import_execution(self.root, request["operation_id"])
        events = self.root / ".research/events"
        started = {p.name: p.read_bytes() for p in events.glob("*.json")
                   if json.loads(p.read_bytes())["type"] == "EXECUTION_STARTED"}
        self.assertEqual(len(started), 1)
        atomic = fixtures.supervise.atomic

        def interrupt_after_events(path, record):
            if path.name == "operation.json" and record.get("imported_events"):
                raise OSError("fixture interruption before marking import complete")
            atomic(path, record)

        with patch.object(fixtures.supervise, "atomic", side_effect=interrupt_after_events):
            with self.assertRaises(OSError):
                fixtures.supervise.import_execution(self.root, request["operation_id"])
        before = {p.name: p.read_bytes() for p in events.glob("*.json")}
        self.assertEqual({name: before[name] for name in started}, started)
        result = self.cli("supervise", "import-execution", "--id", request["operation_id"])
        self.assertEqual(len(result["event_ids"]), 2)
        self.assertEqual({p.name: p.read_bytes() for p in events.glob("*.json")}, before)
        fixtures.commit(self.root, "Consolidate recovered import")
        resumed = self.cli("view", "status", "--format", "json")["inquiries"][0]
        self.assertEqual(len(resumed["executions"]), 1)
        self.assertEqual(resumed["executions"][0]["operation_id"], request["operation_id"])

    def test_model_does_not_offer_execution_when_policy_hides_the_journal(self):
        initial = self.cli("view", "status", "--format", "json")["inquiries"][0]
        request = self.request(initial["next"]["inquiry_binding"])
        self.assertEqual(self.cli("supervise", "run", request=request)["disposition"], "ALLOW")
        fixtures.write(self.root, ".research/policy.json", {
            "version": 1,
            "resources": [{"match": path, "class": "public"}
                          for path in ("RESEARCH.map", "protocol.md", ".research/**")],
            "rules": {"public": {"model_egress": True, "network_egress": False}},
        })
        human = self.cli("view", "status", "--format", "json")["inquiries"][0]
        self.assertEqual(human["next"], {"state": "inspect_execution"})
        model = self.cli("view", "status", "--audience", "model", "--format", "json")
        self.assertEqual(model["inquiries"][0]["next"], {"state": "verify_execution"})
        self.assertNotIn("inquiry_binding", json.dumps(model))
        self.assertNotIn(request["operation_id"], json.dumps(model))
        fixtures.git(self.root, "add", "aggregates/r1.txt")
        fixtures.git(self.root, "commit", "-m", "Commit only the observed output")
        self.assertEqual(self.cli("supervise", "import-execution", "--id",
                                  request["operation_id"])["effect"], "admitted")
        fixtures.commit(self.root, "Share the completion event and capability policy")
        model = self.cli("view", "status", "--audience", "model", "--format", "json")
        self.assertEqual(model["inquiries"][0]["next"], {"state": "inspect_execution"})
        self.assertEqual(model["inquiries"][0]["executions"][0]["source"], "committed_event")
