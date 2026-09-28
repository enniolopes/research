from __future__ import annotations

import importlib.util
import sys
import json
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


graph = load("research_graph", "skills/research-graph/scripts/graph.py")


class GraphTests(unittest.TestCase):
    def test_projection_has_only_derived_entities_and_writes_no_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".research" / "runs").mkdir(parents=True)
            (root / "paper").mkdir()
            (root / "analysis-plan.md").write_text(
                "## H1\nEstimand: E1\nPrimary test: T1\nMode: confirmatory\n"
                "Generated from: DATA1\n| A1 | assumption | K1 | BLOCKED |\n",
                encoding="utf-8",
            )
            (root / ".research" / "runs" / "RUN-1.json").write_text(
                json.dumps({
                    "id": "RUN-1", "mode": "confirmatory", "hypothesis": "H1",
                    "estimand": "E1", "test": "T1",
                    "inputs": [{"id": "DATA2", "path": "data.csv", "role": "confirmatory"}],
                    "outputs": [{"result": "R1", "artifact": "aggregates/r1.csv"}],
                }),
                encoding="utf-8",
            )
            (root / "paper" / "paper.md").write_text(
                "Result. <!-- claim:C1 result:R1 -->\n"
                "Legacy. <!-- claim:C2 inference:I9 result:R1 -->\n",
                encoding="utf-8",
            )
            (root / "RESEARCH.map").write_text(
                "## Layout\n- documents: paper/\n- references: refs.bib\n",
                encoding="utf-8",
            )
            built = graph.build(root / "RESEARCH.map")
            ids = {node["id"] for node in built["nodes"]}
            self.assertIn("C1", ids)
            self.assertIn("C2", ids)
            self.assertIn("R1", ids)
            self.assertNotIn("I9", ids)
            self.assertFalse(any(node["kind"] == "SRC" for node in built["nodes"]))
            self.assertEqual(graph.main(["build", str(root / "RESEARCH.map")]), 0)
            self.assertFalse((root / ".research" / "graph.json").exists())


if __name__ == "__main__":
    unittest.main()
