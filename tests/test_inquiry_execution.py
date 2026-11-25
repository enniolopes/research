"""Confirmatory actions follow the inquiry proposal through the public CLI."""
import json
import subprocess
import sys
import tempfile
import unittest

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
