from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validate = load("research_validate", "skills/research-map/scripts/validate.py")


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name in ("aggregates", "documents", "notebooks"):
            (self.root / name).mkdir()
        (self.root / "decisions.md").write_text(
            "### D-1 · 2026-01-01 · start\nDecision.\nRationale: test\nRevision condition: new evidence\n",
            encoding="utf-8",
        )
        (self.root / "references.bib").write_text("", encoding="utf-8")
        (self.root / "protocol.md").write_text(
            "## Question\n"
            "Claim: descriptive\nUnit of analysis: unit\nEstimand: mean\n"
            "Refutation: zero\nObjection: bias\nWho cares: owner\nNon-goals: causal\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def map_text(self, gates: list[str], layout_protocol: str = "protocol.md") -> str:
        rows = "\n".join(f"| {g} | pending | | |" for g in gates)
        return f"""# RESEARCH.map — test

## Layout
- protocol: {layout_protocol}
- decisions: decisions.md
- aggregates: aggregates/
- documents: documents/
- notebooks: notebooks/
- references: references.bib

## Question
Question → `protocol.md#question`
Problem: PENDING
Registration: none

## Hypotheses
| Id | Prediction | Refutation | State | Pointer |
|---|---|---|---|---|
| H1 | up | zero | — | `protocol.md#question` |

## Gates
| Phase | State | Blocked by | Evidence |
|---|---|---|---|
{rows}

## Deferred

## Last session
- 2026-01-01: initialized
- Next: test
"""

    def test_gate_1a_and_1b_are_distinct(self):
        gates = ["1A Problem — formulate", "2 Literature", "3 Protocol", "4 Data", "5 Analysis", "6 Writing", "7 Review", "8 Publication"]
        result, _ = validate.check_map(self.map_text(gates), self.root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("missing phase(s) 1B" in line for line in result.lines), result.lines)

    def test_duplicate_gate_is_rejected(self):
        gates = ["1A Problem — formulate", "1A duplicate", "1B Problem — establish", "2 Literature", "3 Protocol", "4 Data", "5 Analysis", "6 Writing", "7 Review", "8 Publication"]
        result, _ = validate.check_map(self.map_text(gates), self.root)
        self.assertTrue(any("duplicate phase 1A" in line for line in result.lines), result.lines)

    def test_layout_cannot_escape_repository(self):
        gates = ["1A Problem — formulate", "1B Problem — establish", "2 Literature", "3 Protocol", "4 Data", "5 Analysis", "6 Writing", "7 Review", "8 Publication"]
        result, _ = validate.check_map(self.map_text(gates, "../protocol.md"), self.root)
        self.assertTrue(any("escapes repository root" in line for line in result.lines), result.lines)

    def test_external_problem_basis_does_not_require_local_aggregate(self):
        (self.root / "problem-brief.md").write_text(
            "Construct: service deficit\n"
            "Population: target units in 2026\n"
            "Measure: externally reported rate\n"
            "Reference: threshold fixed in D-1\n"
            "Basis: external — https://example.org/source\n"
            "Magnitude: materially above the fixed reference\n"
            "Falsification: checked alternative denominator and trend\n"
            "Verdict: SHOWN — premise established by inspected external evidence\n",
            encoding="utf-8",
        )
        gates = [
            "1A Problem — formulate", "1B Problem — establish", "2 Literature", "3 Protocol",
            "4 Data", "5 Analysis", "6 Writing", "7 Review", "8 Publication",
        ]
        text = self.map_text(gates).replace(
            "Problem: PENDING",
            "Problem: SHOWN → `problem-brief.md`",
        )
        result, layout = validate.check_map(text, self.root)
        self.assertEqual(result.status, "PASS", result.lines)
        self.assertNotIn("_brief", layout)


    def test_unknown_map_section_is_rejected_but_legacy_section_is_tolerated(self):
        gates = ["1A Problem — formulate", "1B Problem — establish", "2 Literature", "3 Protocol", "4 Data", "5 Analysis", "6 Writing", "7 Review", "8 Publication"]
        base = self.map_text(gates)

        unknown = base.replace("## Deferred", "## Arbitrary\ntext\n\n## Deferred")
        result, _ = validate.check_map(unknown, self.root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("unexpected section '## Arbitrary'" in line for line in result.lines), result.lines)

        legacy = base.replace("## Deferred", "## Verification\n- legacy command\n\n## Deferred")
        result, _ = validate.check_map(legacy, self.root)
        self.assertNotEqual(result.status, "FAIL", result.lines)

    def test_layout_duplicate_and_unknown_keys_are_rejected(self):
        gates = ["1A Problem — formulate", "1B Problem — establish", "2 Literature", "3 Protocol", "4 Data", "5 Analysis", "6 Writing", "7 Review", "8 Publication"]
        text = self.map_text(gates).replace(
            "- references: references.bib",
            "- references: references.bib\n- protocol: protocol.md\n- cache: somewhere/",
        )
        result, _ = validate.check_map(text, self.root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("duplicate key 'protocol'" in line for line in result.lines), result.lines)
        self.assertTrue(any("unknown key 'cache'" in line for line in result.lines), result.lines)


    def test_last_session_requires_exactly_one_next(self):
        gates = ["1A Problem — formulate", "1B Problem — establish", "2 Literature", "3 Protocol", "4 Data", "5 Analysis", "6 Writing", "7 Review", "8 Publication"]
        text = self.map_text(gates).replace(
            "- Next: test",
            "- Next: test\n- Next: another",
        )
        result, _ = validate.check_map(text, self.root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("exactly one `Next:`" in line for line in result.lines), result.lines)

    def test_disclosure_checks_first_column_too(self):
        (self.root / "documents" / "table.csv").write_text("3,label\n", encoding="utf-8")
        layout = {"documents": ["documents/"], "floor": ["5"]}
        result = validate.check_disclosure(self.root, layout)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("cell 3" in line for line in result.lines), result.lines)


if __name__ == "__main__":
    unittest.main()
