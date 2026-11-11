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

    def test_frontmatter_plain_scalars_are_valid_yaml(self):
        # Hosts parse SKILL/agent frontmatter as YAML: an unquoted value containing ": " or " #" breaks loading.
        for surface in list((ROOT / "skills").glob("*/SKILL.md")) + list((ROOT / "agents").glob("*.md")):
            frontmatter = surface.read_text().split("---\n")[1]
            for key, value in re.findall(r"^([\w-]+):[ \t]+(.+)$", frontmatter, re.M):
                if value[0] in "'\"|>[{":
                    continue
                with self.subTest(surface=surface.relative_to(ROOT), key=key):
                    self.assertNotRegex(value, r": |:$| #", "quote this frontmatter value")

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

    def test_readme_plugin_install_ids_match_marketplace(self):
        import json
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        plugin_names = {entry["name"] for entry in marketplace["plugins"]}
        install_ids = re.findall(r"(?:\bplugin\s+install\s+|\binstall\s+`)([\w-]+)@([\w.-]+)", (ROOT / "README.md").read_text())
        self.assertTrue(install_ids, "README has no plugin install IDs")
        for plugin, source in install_ids:
            with self.subTest(plugin=plugin, marketplace=source):
                self.assertIn(plugin, plugin_names)
                self.assertEqual(source, marketplace["name"])
