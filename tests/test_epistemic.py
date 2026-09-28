from __future__ import annotations

import importlib.util
import sys
import json
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


epistemic = load("research_epistemic", "skills/research-map/scripts/epistemic.py")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


class EpistemicTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init")
        git(self.root, "config", "user.email", "test@example.com")
        git(self.root, "config", "user.name", "Test")
        (self.root / "aggregates").mkdir()
        (self.root / ".research" / "runs").mkdir(parents=True)
        (self.root / ".research" / "executions").mkdir(parents=True)
        (self.root / "data.csv").write_text("x\n1\n", encoding="utf-8")
        (self.root / "protocol.md").write_text("## H1\nregistered hypothesis\n", encoding="utf-8")
        (self.root / "analysis-plan.md").write_text(
            "Freeze: frozen\n\n## H1\n"
            "Estimand: E1\nPrimary test: T1\nMode: confirmatory\nGenerated from: none\n"
            "Dependence: independent\nMay claim: effect\nMay not claim: mechanism\n"
            "CONFIRMED when: positive\nREFUTED when: negative\nINCONCLUSIVE when: includes zero\n"
            "| A1 | assumption | K1 | BLOCKED |\n",
            encoding="utf-8",
        )
        (self.root / "RESEARCH.map").write_text(
            "## Layout\n- protocol: protocol.md\n- decisions: decisions.md\n"
            "- aggregates: aggregates/\n- documents: documents/\n- notebooks: notebooks/\n"
            "- references: references.bib\n",
            encoding="utf-8",
        )
        for name in ("documents", "notebooks"):
            (self.root / name).mkdir()
        (self.root / "decisions.md").write_text("", encoding="utf-8")
        (self.root / "references.bib").write_text("", encoding="utf-8")
        for execution_id, output in [
            ("EXEC-1", "aggregates/r1.txt"),
            ("EXEC-2", "aggregates/other.txt"),
        ]:
            (self.root / ".research" / "executions" / f"{execution_id}.json").write_text(
                json.dumps(
                    {
                        "id": execution_id,
                        "command": [sys.executable, "analysis.py"],
                        "inputs": ["data.csv"],
                        "outputs": [output],
                        "environment": [],
                        "capabilities": {
                            "network_egress": False,
                            "model_egress": False,
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "execution freeze")
        self.freeze = git(self.root, "rev-parse", "HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def make_confirmatory_receipt(
        self, extra_change: bool = False, execution_spec: str | None = None
    ) -> Path:
        (self.root / "aggregates" / "r1.txt").write_text("42\n", encoding="utf-8")
        if extra_change:
            (self.root / "protocol.md").write_text("## H1\nchanged after freeze\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "run outputs")
        run_commit = git(self.root, "rev-parse", "HEAD")
        receipt = {
            "id": "RUN-1",
            "mode": "confirmatory",
            "analysis_role": "primary",
            "hypothesis": "H1",
            "estimand": "E1",
            "test": "T1",
            "commit": run_commit,
            "protocol_freeze": self.freeze,
            "analysis_plan_freeze": self.freeze,
            "execution_freeze": self.freeze,
            "registration": "https://example.org/registration",
            "inputs": [{"id": "DATA1", "path": "data.csv", "role": "confirmatory"}],
            "outputs": [{"result": "R1", "artifact": "aggregates/r1.txt"}],
        }
        if execution_spec:
            receipt["execution_spec"] = execution_spec
        path = self.root / ".research" / "runs" / "RUN-1.json"
        path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        git(self.root, "add", str(path.relative_to(self.root)))
        git(self.root, "commit", "-m", "record receipt")
        return path

    def test_run_can_bind_to_frozen_execution_spec(self):
        self.make_confirmatory_receipt(execution_spec="EXEC-1")
        result, _, _ = epistemic.check_runs(self.root, self.root / "RESEARCH.map")
        self.assertEqual(result.status, "PASS", result.lines)

    def test_run_rejects_execution_spec_output_mismatch(self):
        self.make_confirmatory_receipt(execution_spec="EXEC-2")
        result, _, _ = epistemic.check_runs(self.root, self.root / "RESEARCH.map")
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("do not match frozen EXEC-2 outputs" in line for line in result.lines), result.lines)

    def test_output_only_execution_boundary_passes(self):
        self.make_confirmatory_receipt()
        plan, _, _ = epistemic.parse_plan(self.root)
        result, _, _ = epistemic.check_runs(self.root, self.root / "RESEARCH.map")
        self.assertEqual(result.status, "PASS", result.lines)

    def test_non_output_change_after_execution_freeze_fails(self):
        self.make_confirmatory_receipt(extra_change=True)
        plan, _, _ = epistemic.parse_plan(self.root)
        result, _, _ = epistemic.check_runs(self.root, self.root / "RESEARCH.map")
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("non-output path(s) changed" in line for line in result.lines), result.lines)

    def test_receipt_rewrite_is_detected(self):
        path = self.make_confirmatory_receipt()
        data = json.loads(path.read_text(encoding="utf-8"))
        data["registration"] = "rewritten"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        plan, _, _ = epistemic.parse_plan(self.root)
        result, _, _ = epistemic.check_runs(self.root, self.root / "RESEARCH.map")
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("run receipt changed after first commit" in line for line in result.lines), result.lines)

    def test_validation_input_cannot_reuse_adaptive_data(self):
        plan = {"H1": {"generated_from": ["DATA2"]}}
        runs = {
            "RUN-1": {
                "mode": "confirmatory",
                "hypothesis": "H1",
                "_frozen_generated_from": ["DATA2"],
                "_frozen_primary_test": "T1",
                "inputs": [{"id": "DATA2", "role": "validation"}],
            }
        }
        result = epistemic.check_exposure(plan, runs)
        self.assertEqual(result.status, "FAIL")



    def test_relabeling_same_committed_data_does_not_restore_independence(self):
        plan = {"H1": {"generated_from": ["DATA1"]}}
        runs = {
            "RUN-1": {
                "mode": "confirmatory",
                "hypothesis": "H1",
                "_frozen_generated_from": ["DATA1"],
                "_frozen_primary_test": "T1",
                "_data_fingerprints": {"DATA1": "blob-x", "DATA2": "blob-x"},
                "inputs": [{"id": "DATA2", "role": "validation"}],
            }
        }
        result = epistemic.check_exposure(plan, runs)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("re-labels the same committed input content" in line for line in result.lines), result.lines)

    def test_frozen_generated_none_does_not_inherit_current_exposure(self):
        plan = {"H1": {"generated_from": ["DATA2"]}}
        runs = {
            "RUN-1": {
                "mode": "confirmatory",
                "hypothesis": "H1",
                "_frozen_generated_from": [],
                "_frozen_primary_test": "T1",
                "inputs": [{"id": "DATA2", "role": "confirmatory"}],
            }
        }
        result = epistemic.check_exposure(plan, runs)
        self.assertEqual(result.status, "PASS", result.lines)

    def test_binary_result_drift_is_detected_without_text_decoding(self):
        artifact = self.root / "aggregates" / "rbin.bin"
        artifact.write_bytes(b"\xff\x00")
        git(self.root, "add", "aggregates/rbin.bin")
        git(self.root, "commit", "-m", "binary run output")
        run_commit = git(self.root, "rev-parse", "HEAD")
        receipt = {
            "id": "RUN-2",
            "mode": "confirmatory",
            "analysis_role": "primary",
            "hypothesis": "H1",
            "estimand": "E1",
            "test": "T1",
            "commit": run_commit,
            "protocol_freeze": self.freeze,
            "analysis_plan_freeze": self.freeze,
            "execution_freeze": self.freeze,
            "registration": "https://example.org/registration",
            "inputs": [{"id": "DATA1", "path": "data.csv", "role": "confirmatory"}],
            "outputs": [{"result": "R2", "artifact": "aggregates/rbin.bin"}],
        }
        path = self.root / ".research" / "runs" / "RUN-2.json"
        path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        git(self.root, "add", str(path.relative_to(self.root)))
        git(self.root, "commit", "-m", "record binary receipt")
        artifact.write_bytes(b"\xfe\x00")
        result, _, _ = epistemic.check_runs(self.root, self.root / "RESEARCH.map")
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("drifted after run commit" in line for line in result.lines), result.lines)

    def test_confirmatory_input_cannot_also_be_output(self):
        (self.root / "data.csv").write_text("x\n2\n", encoding="utf-8")
        git(self.root, "add", "data.csv")
        git(self.root, "commit", "-m", "mutate input as result")
        run_commit = git(self.root, "rev-parse", "HEAD")
        receipt = {
            "id": "RUN-3",
            "mode": "confirmatory",
            "analysis_role": "primary",
            "hypothesis": "H1",
            "estimand": "E1",
            "test": "T1",
            "commit": run_commit,
            "protocol_freeze": self.freeze,
            "analysis_plan_freeze": self.freeze,
            "execution_freeze": self.freeze,
            "registration": "https://example.org/registration",
            "inputs": [{"id": "DATA1", "path": "data.csv", "role": "confirmatory"}],
            "outputs": [{"result": "R3", "artifact": "data.csv"}],
        }
        path = self.root / ".research" / "runs" / "RUN-3.json"
        path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        git(self.root, "add", str(path.relative_to(self.root)))
        git(self.root, "commit", "-m", "record overlapping receipt")
        result, _, _ = epistemic.check_runs(self.root, self.root / "RESEARCH.map")
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("input/output path overlap" in line for line in result.lines), result.lines)

    def test_only_plan_does_not_scan_runs_or_lineage(self):
        with mock.patch.object(epistemic, "check_runs", side_effect=AssertionError("runs should not execute")):
            results = epistemic.run(self.root / "RESEARCH.map", self.root, {"plan"})
        self.assertEqual([result.name for result in results], ["plan"])

    def test_legacy_validation_mode_remains_readable(self):
        (self.root / "aggregates" / "rv.txt").write_text("validation\n", encoding="utf-8")
        git(self.root, "add", "aggregates/rv.txt")
        git(self.root, "commit", "-m", "legacy validation output")
        run_commit = git(self.root, "rev-parse", "HEAD")
        receipt = {
            "id": "RUN-8",
            "mode": "validation",
            "analysis_role": "diagnostic",
            "hypothesis": "H8",
            "estimand": "E8",
            "test": "T8",
            "commit": run_commit,
            "inputs": [{"id": "DATA1", "path": "data.csv", "role": "validation"}],
            "outputs": [{"result": "R8", "artifact": "aggregates/rv.txt"}],
        }
        path = self.root / ".research" / "runs" / "RUN-8.json"
        path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
        result, _, _ = epistemic.check_runs(self.root, self.root / "RESEARCH.map")
        self.assertNotEqual(result.status, "FAIL", result.lines)


    def test_exploratory_run_requires_commit(self):
        (self.root / "aggregates" / "rx.txt").write_text("x\n", encoding="utf-8")
        receipt = {
            "id": "RUN-6",
            "mode": "exploratory",
            "hypothesis": "H6",
            "estimand": "E6",
            "test": "T6",
            "commit": "",
            "inputs": [{"id": "DATA1", "path": "data.csv", "role": "discovery"}],
            "outputs": [{"result": "R6", "artifact": "aggregates/rx.txt"}],
        }
        (self.root / ".research" / "runs" / "RUN-6.json").write_text(json.dumps(receipt), encoding="utf-8")
        result, _, _ = epistemic.check_runs(self.root, self.root / "RESEARCH.map")
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("commit must be a git commit id" in line for line in result.lines), result.lines)

    def test_receipt_commit_must_descend_from_run_commit(self):
        base_branch = git(self.root, "branch", "--show-current")
        git(self.root, "switch", "-c", "side-run")
        artifact = self.root / "aggregates" / "side.txt"
        artifact.write_text("same\n", encoding="utf-8")
        git(self.root, "add", "aggregates/side.txt")
        git(self.root, "commit", "-m", "side run")
        side_commit = git(self.root, "rev-parse", "HEAD")

        git(self.root, "switch", base_branch)
        artifact.parent.mkdir(exist_ok=True)
        artifact.write_text("same\n", encoding="utf-8")
        receipt = {
            "id": "RUN-7",
            "mode": "exploratory",
            "hypothesis": "H7",
            "estimand": "E7",
            "test": "T7",
            "commit": side_commit,
            "inputs": [{"id": "DATA1", "path": "data.csv", "role": "discovery"}],
            "outputs": [{"result": "R7", "artifact": "aggregates/side.txt"}],
        }
        path = self.root / ".research" / "runs" / "RUN-7.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        git(self.root, "add", "aggregates/side.txt", str(path.relative_to(self.root)))
        git(self.root, "commit", "-m", "receipt on unrelated branch")
        result, _, _ = epistemic.check_runs(self.root, self.root / "RESEARCH.map")
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("is not an ancestor of first receipt commit" in line for line in result.lines), result.lines)

    def test_exploratory_history_does_not_depend_on_current_plan(self):
        (self.root / "aggregates" / "rx.txt").write_text("x\n", encoding="utf-8")
        git(self.root, "add", "aggregates/rx.txt")
        git(self.root, "commit", "-m", "exploratory output")
        exploratory_commit = git(self.root, "rev-parse", "HEAD")
        receipt = {
            "id": "RUN-9",
            "mode": "exploratory",
            "hypothesis": "H9",
            "estimand": "E9",
            "test": "T9",
            "commit": exploratory_commit,
            "inputs": [{"id": "DATA1", "path": "data.csv", "role": "discovery"}],
            "outputs": [{"result": "R9", "artifact": "aggregates/rx.txt"}],
        }
        path = self.root / ".research" / "runs" / "RUN-9.json"
        path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
        result, _, _ = epistemic.check_runs(self.root, self.root / "RESEARCH.map")
        self.assertNotEqual(result.status, "FAIL", result.lines)


if __name__ == "__main__":
    unittest.main()
