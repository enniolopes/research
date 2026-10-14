from __future__ import annotations

import copy
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from uuid import uuid4

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/research-map/scripts"
sys.path.insert(0, str(SCRIPTS))
contracts = importlib.import_module("contracts")
resources = importlib.import_module("resources")
events = importlib.import_module("events")
review = importlib.import_module("review")
supervise = importlib.import_module("supervise")
state = importlib.import_module("supervision_state")
release = importlib.import_module("release")
graph = importlib.import_module("decision_graph")


def git(root, *args):
    return resources.git(root, *args).decode().strip()


def write(root, path, obj):
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + "\n")
    return p


def commit(root, message="fixture"):
    git(root, "add", ".")
    git(root, "commit", "-m", message)
    return resources.head(root)


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init")
        git(self.root, "config", "user.name", "Test")
        git(self.root, "config", "user.email", "test@example.com")
        self.project = supervise.initialize(self.root)["project_id"]
        for directory in ("documents", "aggregates", "notebooks", "data", "analysis", ".research/executions", ".research/runs"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        self.text = "The observed mean is positive."
        (self.root / "documents/paper.md").write_text(self.text + "\n")
        (self.root / "source.txt").write_text(self.text + "\n")
        (self.root / "protocol.md").write_text("## H1\nThe mean is positive.\n")
        (self.root / "analysis-plan.md").write_text(
            "Freeze: frozen\n\n## H1\nEstimand: E1\nPrimary test: T1\nMode: confirmatory\nGenerated from: none\n"
            "Dependence: independent\nMay claim: positive observed mean\nMay not claim: causal mechanism\n"
            "CONFIRMED when: positive\nREFUTED when: negative\nINCONCLUSIVE when: zero\n"
            "| A1 | numeric data | K1 | BLOCKED |\n")
        (self.root / "data/input.txt").write_text("2\n")
        (self.root / "analysis/run.py").write_text(
            "from pathlib import Path\np=Path('aggregates/r1.txt');p.parent.mkdir(exist_ok=True);p.write_text(Path('data/input.txt').read_text())\n")
        (self.root / "decisions.md").write_text("")
        (self.root / "references.bib").write_text("")
        (self.root / "RESEARCH.map").write_text(
            "## Layout\n- protocol: protocol.md\n- decisions: decisions.md\n- aggregates: aggregates/\n"
            "- documents: documents/\n- notebooks: notebooks/\n- references: references.bib\n"
            "## Question\nRegistration: test://registered\n")
        write(self.root, ".research/executions/EXEC-1.json", {
            "id": "EXEC-1", "command": [sys.executable, "analysis/run.py"], "inputs": ["data/input.txt"],
            "outputs": ["aggregates/r1.txt"], "environment": ["analysis/run.py"],
            "capabilities": {"network_egress": False, "model_egress": False}})
        auth = supervise.attest(self.root, "REF-1", "owner", "AUTHORITY_ATTESTED", "Explicit fixture project-quality decision.")
        self.ref = {"schema_version": "references@1", "id": "REF-1", "project_id": self.project, "supersedes": None,
                    "criteria": [{"id": "QC-1", "class": "scientific", "text": "Wording stays within inspected evidence.",
                                  "applies_to": ["ADOPT_CLAIM", "REVISE_DECISION", "RELEASE"], "materiality": "required",
                                  "verification": "independent_review", "source": {"kind": "project_decision", "ref": "decisions.md"}}],
                    "authority": {"kind": "human", "identity": "owner", "attestation_ref": auth["attestation_ref"]}}
        write(self.root, ".research/references/REF-1.json", self.ref)
        self.freeze = commit(self.root, "prospective freeze")

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, action, target="C1", record=None):
        payload = {"schema_version": "action@1", "operation_id": str(uuid4()), "project_id": self.project,
                   "core_version": contracts.CORE_VERSION, "rules_sha256": contracts.RULES_SHA256,
                   "action": action, "target": target, "base_commit": resources.head(self.root), "resources": {}, "bindings": []}
        if record:
            payload["record"] = record
        if action == "FIT_CONFIRMATORY":
            payload.update(execution_id="EXEC-1", hypothesis="H1", protocol_freeze=self.freeze,
                           analysis_plan_freeze=self.freeze, registration="test://registered")
        return payload

    def create_review(self, rid="REVIEW-1", source_binding="pinned"):
        attested = supervise.attest(self.root, rid, "external-reviewer", "REVIEW_ATTESTED", "Fixture external reviewer independently examined the material.")
        report = f".research/reviews/{rid}.md"
        (self.root / report).parent.mkdir(parents=True, exist_ok=True)
        (self.root / report).write_text("VERDICT: PASS\nC1 examined against source and stated scope.\n")
        paper = resources.resource(self.root, "manuscript", "paper", "documents/paper.md", self.freeze)
        source = resources.resource(self.root, "source", "SOURCE1", "source.txt", self.freeze)
        source.update(source_uri="fixture://inspected-source", retrieved_at=events.now())
        bindings = [{"resource_ref": "RES-PAPER", "binding": "follow_current", "current_path": "documents/paper.md"},
                    {"resource_ref": "RES-SOURCE", "binding": source_binding}]
        if source_binding == "follow_current":
            bindings[1]["current_path"] = "source.txt"
        record = {"schema_version": "review@1", "id": rid, "project_id": self.project,
                  "core_version": contracts.CORE_VERSION, "rules_sha256": contracts.RULES_SHA256,
                  "reviewed_commit": self.freeze, "resources": {"RES-PAPER": paper, "RES-SOURCE": source},
                  "dependencies": bindings, "reference_set": ["REF-1"],
                  "report": {"path": report, "sha256": resources.fingerprint((self.root / report).read_bytes())},
                  "coverage": {"documents": ["RES-PAPER"], "claim_ids": ["C1"], "unexamined": [], "limitations": [], "material_complete": True},
                  "claims": [{"id": "C1", "text": self.text, "resource_ref": "RES-PAPER", "criteria": ["REF-1#QC-1"],
                              "evidence": ["RES-SOURCE"], "routes": ["J1"], "result": "adequate", "limits": ["Observed population only."]}],
                  "findings": [], "checks": [],
                  "reviewer": {"backend": "external", "identity": "external-reviewer", "procedure": "fixture@1",
                               "separation": "external_reviewer_attested", "attestation_ref": attested["attestation_ref"]}, "verdict": "PASS"}
        write(self.root, f".research/reviews/{rid}.json", record)
        commit(self.root, "review and witness")
        return record

    def decision(self, r, rid="DEC-1"):
        return {"schema_version": "decision@1", "id": rid, "project_id": self.project,
                "core_version": contracts.CORE_VERSION, "rules_sha256": contracts.RULES_SHA256,
                "action": "ADOPT_CLAIM", "target": {"kind": "claim", "id": "C1", "text": self.text,
                    "resource_ref": "RES-PAPER", "binding": "follow_current", "current_path": "documents/paper.md"},
                "references": ["REF-1#QC-1"], "resources": copy.deepcopy(r["resources"]),
                "basis": {"routes": [{"id": "J1", "all_of": [{"resource_ref": "RES-SOURCE", "binding": "pinned"}]}], "origin_refs": ["SOURCE1"]},
                "judgments": [r["id"] + "#C1"], "rationale_ref": "RES-PAPER", "disposition": "adopt",
                "limits": ["No causal conclusion."], "supersedes": None, "revision_conditions": ["Relevant evidence or formulation changes."]}

    def release_record(self, r):
        return {"schema_version": "release@1", "id": "REL-1", "project_id": self.project,
                "core_version": contracts.CORE_VERSION, "rules_sha256": contracts.RULES_SHA256,
                "snapshot_commit": self.freeze, "target": {"kind": "manuscript", "destination": "local-review", "reference_set": ["REF-1"]},
                "resources": {"RES-PAPER": copy.deepcopy(r["resources"]["RES-PAPER"])},
                "claim_inventory": [{"id": "C1", "text": self.text, "resource_ref": "RES-PAPER", "locator": "line 1"}],
                "decision_refs": ["DEC-1"], "review_refs": [r["id"]], "obligations": [], "authority_refs": [], "created_at": events.now()}

    def test_exported_schemas_equal_runtime_contracts(self):
        for name, data in contracts.schema_files().items():
            self.assertEqual(contracts.load(SCRIPTS.parent / "schemas" / name), data)

    def test_duplicate_keys_nonfinite_unknown_and_invalid_types_rejected(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}'):
            with self.assertRaises(contracts.ContractError):
                contracts.loads(raw)
        p = self.request("FIT_CONFIRMATORY")
        for key, value in (("bindings", "bad"), ("extra", True), ("rules_sha256", "0" * 64)):
            invalid = copy.deepcopy(p); invalid[key] = value
            with self.assertRaises(contracts.ContractError):
                contracts.validate(invalid)

    def test_partial_and_manual_decisions_do_not_acquire_authority(self):
        r = self.create_review(); d = self.decision(r)
        write(self.root, ".research/decisions/DEC-1.json", d)
        commit(self.root, "manual candidate")
        self.assertEqual(state.Store(self.root).state("DEC-1")[0], "CANDIDATE")

    def test_admission_consolidation_release_and_new_process(self):
        r = self.create_review(); d = self.decision(r)
        request = self.request("ADOPT_CLAIM", record=d)
        result = supervise.admit(self.root, request)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertFalse(result["consolidated"])
        self.assertEqual(state.Store(self.root).state("DEC-1")[0], "CANDIDATE")
        commit(self.root, "consolidated adoption")
        self.assertEqual(state.Store(self.root).state("DEC-1")[0], "CURRENT")
        release_request = self.request("RELEASE", "REL-1", self.release_record(r))
        result = supervise.admit(self.root, release_request)
        self.assertEqual(result["disposition"], "ALLOW", result)
        commit(self.root, "release manifest")
        process = subprocess.run([sys.executable, str(SCRIPTS / "supervise.py"), "release-inspect", "--root", str(self.root), "--id", "REL-1"], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(json.loads(process.stdout)["state"], "CURRENT")
        (self.root / "documents/paper.md").write_text("A stronger causal claim.\n")
        inspected = release.inspect(self.root, "REL-1")
        self.assertEqual(inspected["state"], "STALE")
        self.assertTrue(any(x["status"] == "STALE" for x in inspected["checks"]))

    def test_missing_separation_and_asmt_cannot_substitute_review(self):
        r = self.create_review(); d = self.decision(r)
        d["judgments"] = ["ASMT-1"]
        result = supervise.propose(self.root, self.request("ADOPT_CLAIM", record=d))
        self.assertNotEqual(result["disposition"], "ALLOW")
        r["reviewer"]["separation"] = "not_verified"
        self.assertEqual(review.separation(r, state.Store(self.root).records, state.Store(self.root).committed)[0], "NOT_VERIFIED")

    def test_pass_cannot_hide_inadequate_claim_or_material_finding(self):
        r = self.create_review()
        r["claims"][0]["result"] = "inadequate"
        self.assertTrue(review.consistency(r))
        r["claims"][0]["result"] = "adequate"
        r["findings"] = [{"id": "F1", "materiality": "material", "target": "C1", "reason": "contradiction", "action": "narrow", "disposition": "open"}]
        self.assertTrue(review.consistency(r))

    def test_pinned_history_survives_current_data_change_but_follow_current_does_not(self):
        r = self.create_review()
        store = state.Store(self.root)
        (self.root / "source.txt").write_text("New population and observations.\n")
        pinned = {"resource_ref": "RES-SOURCE", "binding": "pinned"}
        follows = {**pinned, "binding": "follow_current", "current_path": "source.txt"}
        self.assertEqual(resources.applicability(self.root, pinned, r, store.records)[0], "PASS")
        self.assertEqual(resources.applicability(self.root, follows, r, store.records)[0], "STALE")
        self.assertEqual(state.Store(self.root).state("REVIEW-1")[0], "CURRENT")

    def test_exact_claim_and_support_versions_must_match_review(self):
        r = self.create_review(); d = self.decision(r)
        d["target"]["text"] = "A causal effect exists."
        result = supervise.propose(self.root, self.request("ADOPT_CLAIM", record=d))
        self.assertEqual(result["disposition"], "BLOCK")

    def test_external_source_refresh_and_restricted_bytes_are_not_verified(self):
        r = self.create_review(); store = state.Store(self.root)
        b = {"resource_ref": "RES-SOURCE", "binding": "external_refresh", "refresh_rule": "check requirement", "refresh_at": "2000-01-01T00:00:00Z"}
        self.assertEqual(resources.applicability(self.root, b, r, store.records)[0], "NOT_VERIFIED")
        self.assertEqual(resources.verify(self.root, {"kind": "restricted_external"})[0], "NOT_VERIFIED")

    def test_false_host_context_attestation_fails(self):
        r = self.create_review(); store = state.Store(self.root)
        e = store.records[r["reviewer"]["attestation_ref"]]
        e.update(observation="instrumented", context_id="same", author_context_id="same")
        r["reviewer"]["separation"] = "host_attested"
        self.assertEqual(review.separation(r, store.records, store.committed)[0], "FAIL")

    def test_records_deleted_or_rewritten_are_detected(self):
        r = self.create_review()
        path = self.root / ".research/reviews/REVIEW-1.json"
        path.unlink(); commit(self.root, "deleted review")
        self.assertEqual(state.check_supervision(self.root).status, "FAIL")

    def test_rules_cannot_be_weakened_by_reference(self):
        bad = copy.deepcopy(self.ref); bad["id"] = "REF-2"; bad["criteria"][0]["id"] = "CORE-PROSPECTIVE"; bad["criteria"][0]["materiality"] = "advisory"
        write(self.root, ".research/references/REF-2.json", bad); commit(self.root)
        self.assertTrue(any("reserved" in why for _, why in state.Store(self.root).issues))

    def test_run_journal_preserves_clean_execution_boundary_and_idempotency(self):
        req = self.request("FIT_CONFIRMATORY", "H1")
        result = supervise.run(self.root, req)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(result["effect"], "executed")
        self.assertEqual(git(self.root, "status", "--porcelain"), "?? aggregates/")
        journal = events.runtime(self.root) / req["operation_id"] / "operation.json"
        self.assertTrue(journal.exists())
        (self.root / "aggregates/r1.txt").write_text("changed after run\n")
        self.assertTrue(supervise.run(self.root, req)["cached"])
        self.assertEqual((self.root / "aggregates/r1.txt").read_text(), "changed after run\n")
        modified = copy.deepcopy(req); modified["target"] = "H2"
        with self.assertRaises(contracts.ContractError):
            supervise.run(self.root, modified)

    def test_failed_or_unfinished_execution_does_not_erase_exposure_or_retry(self):
        req = self.request("FIT_CONFIRMATORY", "H1")
        path, _ = events.journal(self.root, req)
        events.begin(path, req, "EXECUTION_STARTED")
        with self.assertRaises(events.RecoveryRequired):
            supervise.run(self.root, req)
        self.assertFalse((self.root / "aggregates/r1.txt").exists())

    def test_commit_outputs_then_import_events_then_record_run(self):
        req = self.request("FIT_CONFIRMATORY", "H1")
        result = supervise.run(self.root, req)
        self.assertEqual(result["disposition"], "ALLOW", result)
        run_commit = commit(self.root, "outputs only")
        imported = supervise.import_execution(self.root, req["operation_id"])
        self.assertEqual(len(imported["event_ids"]), 2)
        receipt = {"id": "RUN-1", "mode": "confirmatory", "analysis_role": "primary", "hypothesis": "H1", "estimand": "E1", "test": "T1",
                   "commit": run_commit, "protocol_freeze": self.freeze, "analysis_plan_freeze": self.freeze, "execution_freeze": self.freeze,
                   "registration": "test://registered", "execution_spec": "EXEC-1", "inputs": [{"id": "DATA1", "path": "data/input.txt", "role": "confirmatory"}],
                   "outputs": [{"result": "R1", "artifact": "aggregates/r1.txt"}]}
        write(self.root, ".research/runs/RUN-1.json", receipt)
        commit(self.root, "events and run receipt")
        checks = supervise.propose(self.root, self.request("ADMIT_RESULT", "R1"))
        self.assertEqual(checks["disposition"], "ALLOW", checks)
        self.assertTrue(supervise.import_execution(self.root, req["operation_id"])["cached"])

    def test_missing_freeze_and_adaptive_plan_block_before_execution(self):
        req = self.request("FIT_CONFIRMATORY", "H1"); del req["analysis_plan_freeze"]
        result = supervise.run(self.root, req)
        self.assertNotEqual(result["disposition"], "ALLOW")
        self.assertFalse((self.root / "aggregates/r1.txt").exists())
        p = self.root / "analysis-plan.md"
        p.write_text(p.read_text().replace("Generated from: none", "Generated from: DATA1"))
        self.freeze = commit(self.root, "adaptive commitment")
        result = supervise.run(self.root, self.request("FIT_CONFIRMATORY", "H1"))
        self.assertNotEqual(result["disposition"], "ALLOW")

    def test_snapshot_staleness_lock_and_history_recovery(self):
        request = self.request("FIT_CONFIRMATORY", "H1")
        (self.root / "unrelated.txt").write_text("new\n"); commit(self.root)
        with self.assertRaises(events.RecoveryRequired):
            supervise.propose(self.root, request)
        events.anchor(self.root)
        git(self.root, "reset", "--hard", self.freeze)
        with self.assertRaises(events.RecoveryRequired):
            state.Store(self.root)

    def test_worktree_git_file_and_safe_paths(self):
        other = self.root.parent / (self.root.name + "-worktree")
        git(self.root, "worktree", "add", "--detach", str(other), self.freeze)
        try:
            self.assertEqual(events.git_dir(self.root, True), events.git_dir(other, True))
            self.assertNotEqual(events.runtime(self.root), events.runtime(other))
            with self.assertRaises(contracts.ContractError):
                resources.safe_path(self.root, "../escape")
            (self.root / "linked").symlink_to(self.root / "source.txt")
            with self.assertRaises(contracts.ContractError):
                resources.safe_path(self.root, "linked")
        finally:
            git(self.root, "worktree", "remove", "--force", str(other))

    def test_graph_is_disposable_and_versioned_with_conjunctive_routes(self):
        r = self.create_review(); d = self.decision(r)
        supervise.admit(self.root, self.request("ADOPT_CLAIM", record=d)); commit(self.root)
        store = state.Store(self.root)
        g = graph.build(store)
        source_key = graph.key(self.project, r["resources"]["RES-SOURCE"])
        self.assertIn("DEC-1", graph.affected(g, source_key)["affected_candidates"])
        new = copy.deepcopy(r["resources"]["RES-SOURCE"]); new["revision"] = resources.head(self.root)
        self.assertNotEqual(source_key, graph.key(self.project, new))
        self.assertFalse((self.root / ".research/graph.json").exists())

    def test_render_is_not_covered_by_source_only_review(self):
        r = self.create_review(); d = self.decision(r)
        supervise.admit(self.root, self.request("ADOPT_CLAIM", record=d)); commit(self.root)
        (self.root / "documents/paper.pdf").write_bytes(b"a render with changed content")
        rev = commit(self.root, "render")
        rel = self.release_record(r); rel["snapshot_commit"] = rev
        rel["resources"]["RES-RENDER"] = resources.resource(self.root, "render", "pdf", "documents/paper.pdf", rev)
        self.assertTrue(any(s != "PASS" and "not inspected" in why for s, why in release.evaluate(state.Store(self.root), rel)))

    def test_negative_review_can_withdraw_without_resurrecting_prior_claim(self):
        r = self.create_review()
        self.assertEqual(supervise.admit(self.root, self.request("ADOPT_CLAIM", record=self.decision(r)))["disposition"], "ALLOW")
        commit(self.root)
        negative = self.create_review("REVIEW-2")
        # Replace the fixture's just-created review before its immutable history
        # begins by returning HEAD to the prior commit, retaining its files.
        git(self.root, "reset", "--soft", "HEAD~1")
        negative["verdict"] = "FAIL"
        negative["claims"][0]["result"] = "inadequate"
        write(self.root, ".research/reviews/REVIEW-2.json", negative)
        commit(self.root)
        d = self.decision(negative, "DEC-2")
        d.update(action="REVISE_DECISION", disposition="withdraw", supersedes="DEC-1")
        self.assertEqual(supervise.admit(self.root, self.request("REVISE_DECISION", record=d))["disposition"], "ALLOW")
        commit(self.root)
        self.assertEqual(state.Store(self.root).state("DEC-1")[0], "WITHDRAWN")
        (self.root / "documents/paper.md").write_text("Changed after withdrawal.\n")
        self.assertEqual(state.Store(self.root).state("DEC-1")[0], "WITHDRAWN")
        (self.root / "documents/paper.md").write_text(self.text + "\n")
        self.assertEqual(state.Store(self.root).state("DEC-1")[0], "WITHDRAWN")

    def test_active_reference_cannot_be_silently_omitted(self):
        r = self.create_review()
        new = copy.deepcopy(self.ref)
        new.update(id="REF-2", supersedes="REF-1")
        witness = supervise.attest(self.root, "REF-2", "owner", "AUTHORITY_ATTESTED", "Owner explicitly changed the required criteria.")
        new["authority"]["attestation_ref"] = witness["attestation_ref"]
        write(self.root, ".research/references/REF-2.json", new)
        commit(self.root)
        result = supervise.propose(self.root, self.request("ADOPT_CLAIM", record=self.decision(r)))
        self.assertNotEqual(result["disposition"], "ALLOW")

    def test_dispatcher_reports_real_capabilities(self):
        process = subprocess.run([sys.executable, str(SCRIPTS / "research.py"), "supervise", "capabilities"], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertFalse(json.loads(process.stdout)["observes_external_exposure"])


if __name__ == "__main__":
    unittest.main()
