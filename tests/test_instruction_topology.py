"""Instruction navigation must resolve in the installed plugin, not the project."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstructionTopologyTests(unittest.TestCase):
    def test_phase_and_skill_reference_paths_resolve(self):
        surfaces = list((ROOT / "skills").glob("*/SKILL.md"))
        surfaces += list((ROOT / "skills/scientific-method/reference").glob("*.md"))
        surfaces += list((ROOT / "agents").glob("*.md"))
        for surface in surfaces:
            # Phase references are written relative to their parent skill.
            home = surface.parent.parent if surface.parent.name == "reference" else surface.parent
            pattern = r"(?<![\w/])(?:skills/[\w-]+/|research-map/|(?:\.\./)+[\w-]+/)?(?:reference|scripts|templates)/[\w./-]+\.(?:md|py|json|map)"
            for target in re.findall(pattern, surface.read_text()):
                base = ROOT if target.startswith("skills/") else surface.parent if target.startswith("../") else home
                with self.subTest(surface=surface.relative_to(ROOT), target=target):
                    self.assertTrue((base / target).is_file(), f"unreachable instruction: {target}")

    def test_runtime_contracts_do_not_import_orchestration(self):
        import ast
        low_level = ["contracts.py", "git_integrity.py", "resources.py", "events.py", "review.py", "decision_graph.py"]
        forbidden = {"supervise", "research", "validate_all", "release", "supervision_state"}
        for name in low_level:
            tree = ast.parse((ROOT / "skills/research-map/scripts" / name).read_text())
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(x.name.split(".")[0] for x in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertFalse(imports & forbidden, f"{name}: domain depends on orchestration")
