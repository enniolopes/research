from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATE = ROOT / "skills" / "research-map" / "scripts" / "validate_all.py"
GRAPH = ROOT / "skills" / "research-graph" / "scripts" / "graph.py"
REPLAY = ROOT / "skills" / "research-map" / "scripts" / "replay.py"


def run(root: Path, *argv: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=root,
        check=check,
        capture_output=True,
        text=True,
    )


def git(root: Path, *args: str) -> str:
    return run(root, "git", *args).stdout.strip()


class MinimumScientificLoopTests(unittest.TestCase):
    def test_research_state_survives_process_loss_and_reconstructs_why(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git(root, "init")
            git(root, "config", "user.email", "test@example.com")
            git(root, "config", "user.name", "Test")

            for directory in (
                "aggregates",
                "documents",
                "notebooks",
                ".research/runs",
                ".research/reviews",
            ):
                (root / directory).mkdir(parents=True)

            (root / "data.csv").write_text("value\n1\n2\n3\n", encoding="utf-8")
            (root / "analysis.py").write_text(
                "import csv, json\n"
                "from pathlib import Path\n"
                "with open('data.csv', newline='', encoding='utf-8') as handle:\n"
                "    values = [float(row['value']) for row in csv.DictReader(handle)]\n"
                "out = Path('aggregates/r1.json')\n"
                "out.parent.mkdir(exist_ok=True)\n"
                "out.write_text(json.dumps({'mean': sum(values) / len(values)}, sort_keys=True) + '\\n', encoding='utf-8')\n",
                encoding="utf-8",
            )
            (root / "protocol.md").write_text(
                "## Question\n"
                "Claim: The observed mean is positive.\n"
                "Unit of analysis: row\n"
                "Estimand: mean value\n"
                "Refutation: a non-positive mean\n"
                "Objection: this fixture tests mechanics, not substantive generalization\n"
                "Who cares: end-to-end integrity\n"
                "Non-goals: external validity\n\n"
                "## H1\n"
                "The mean value is positive.\n",
                encoding="utf-8",
            )
            (root / "analysis-plan.md").write_text(
                "Freeze: frozen\n\n"
                "## H1\n"
                "Estimand: E1\n"
                "Primary test: T1\n"
                "Mode: confirmatory\n"
                "Generated from: none\n"
                "Dependence: independent\n"
                "May claim: the observed mean is positive\n"
                "May not claim: mechanism or generalization\n"
                "CONFIRMED when: mean > 0\n"
                "REFUTED when: mean <= 0\n"
                "INCONCLUSIVE when: result cannot be computed\n"
                "| A1 | input parses as numeric | K1 | BLOCKED |\n",
                encoding="utf-8",
            )
            (root / "decisions.md").write_text("", encoding="utf-8")
            (root / "references.bib").write_text("", encoding="utf-8")
            (root / "RESEARCH.map").write_text(
                "# RESEARCH.map — minimum-loop\n\n"
                "## Layout\n"
                "- protocol: protocol.md\n"
                "- decisions: decisions.md\n"
                "- aggregates: aggregates/\n"
                "- documents: documents/\n"
                "- notebooks: notebooks/\n"
                "- references: references.bib\n\n"
                "## Question\n"
                "Does the fixture preserve a valid confirmatory result? → `protocol.md#question`\n"
                "Problem: PENDING\n"
                "Registration: test://minimum-loop\n\n"
                "## Hypotheses\n"
                "| Id | Prediction | Refutation | State | Pointer |\n"
                "|---|---|---|---|---|\n"
                "| H1 | mean > 0 | mean <= 0 | CONFIRMED | `protocol.md#h1` |\n\n"
                "## Gates\n"
                "| Phase | State | Blocked by | Evidence |\n"
                "|---|---|---|---|\n"
                "| 1A Problem — formulate | pending | | |\n"
                "| 1B Problem — establish | pending | | |\n"
                "| 2 Literature | pending | | |\n"
                "| 3 Protocol | pending | | |\n"
                "| 4 Data | pending | | |\n"
                "| 5 Analysis | pending | | |\n"
                "| 6 Writing | pending | | |\n"
                "| 7 Review | pending | | |\n"
                "| 8 Publication | pending | | |\n\n"
                "## Deferred\n"
                "- 2026-09-28: external-validity extension — enters when: a real target population exists\n\n"
                "## Last session\n"
                "- 2026-09-28: minimum loop fixture created\n"
                "- Next: reconstruct the accepted result from durable artifacts\n",
                encoding="utf-8",
            )

            git(root, "add", ".")
            git(root, "commit", "-m", "freeze scientific and executable state")
            freeze = git(root, "rev-parse", "HEAD")

            run(root, sys.executable, "analysis.py")
            git(root, "add", "aggregates/r1.json")
            git(root, "commit", "-m", "produce R1")
            run_commit = git(root, "rev-parse", "HEAD")

            receipt = {
                "id": "RUN-1",
                "mode": "confirmatory",
                "analysis_role": "primary",
                "hypothesis": "H1",
                "estimand": "E1",
                "test": "T1",
                "commit": run_commit,
                "protocol_freeze": freeze,
                "analysis_plan_freeze": freeze,
                "execution_freeze": freeze,
                "registration": "test://minimum-loop",
                "inputs": [
                    {"id": "DATA1", "path": "data.csv", "role": "confirmatory"}
                ],
                "outputs": [
                    {"result": "R1", "artifact": "aggregates/r1.json"}
                ],
                "replay": {
                    "command": [sys.executable, "analysis.py"],
                    "environment": ["analysis.py"],
                },
            }
            (root / ".research" / "runs" / "RUN-1.json").write_text(
                json.dumps(receipt, indent=2) + "\n",
                encoding="utf-8",
            )
            (root / "documents" / "paper.md").write_text(
                "The observed mean is positive. <!-- claim:C1 result:R1 decides:H1 -->\n",
                encoding="utf-8",
            )
            (root / ".research" / "reviews" / "REVIEW-1.md").write_text(
                "VERDICT: PASS\n\n"
                "C1 was challenged against the frozen primary result and no material contradiction was found.\n",
                encoding="utf-8",
            )
            git(root, "add", ".research/runs/RUN-1.json", ".research/reviews/REVIEW-1.md", "documents/paper.md")
            git(root, "commit", "-m", "record run, claim, and challenge")

            # These are separate Python processes with no imported state from the construction phase.
            validated = run(
                root,
                sys.executable,
                str(VALIDATE),
                "RESEARCH.map",
                "--root",
                str(root),
                "--offline",
                "--only",
                "plan,runs,lineage,exposure",
            )
            self.assertIn("RESULT PASS", validated.stdout, validated.stdout + validated.stderr)

            why = run(
                root,
                sys.executable,
                str(GRAPH),
                "why",
                "C1",
                "RESEARCH.map",
            )
            for identity in ("C1", "R1", "RUN-1", "T1"):
                self.assertIn(identity, why.stdout, why.stdout + why.stderr)

            replayed = run(
                root,
                sys.executable,
                str(REPLAY),
                "RUN-1",
                "--root",
                str(root),
            )
            self.assertIn("REPLAY RUN-1 EXACT", replayed.stdout, replayed.stdout + replayed.stderr)

            # A new process must still reject history that drifted after the recorded run.
            (root / "aggregates" / "r1.json").write_text('{"mean": 999}\n', encoding="utf-8")
            drift = run(
                root,
                sys.executable,
                str(VALIDATE),
                "RESEARCH.map",
                "--root",
                str(root),
                "--offline",
                "--only",
                "runs",
                check=False,
            )
            self.assertEqual(drift.returncode, 1, drift.stdout + drift.stderr)
            self.assertIn("drifted after run commit", drift.stdout, drift.stdout + drift.stderr)


if __name__ == "__main__":
    unittest.main()
