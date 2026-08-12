from __future__ import annotations

import unittest
from pathlib import Path

from minescript.minecraft_art import _TEXTURES
from minescript.minecraft_art25 import FUZZY_TERMS
from minescript.tool_guides import NAV_SECTIONS, make_guide, nav_section, tool_art_key, workspace_group
from minescript.tool_registry import BY_ID, TOOLS

ROOT = Path(__file__).resolve().parents[1]


class TaskFirstUiDepthTests(unittest.TestCase):
    def test_visible_surface_is_compact_and_task_first(self):
        self.assertLess(len(TOOLS), 50)
        self.assertEqual(
            [label for label, _ in NAV_SECTIONS],
            ["Home", "Play & Travel", "Explore Worlds", "Plan & Build", "Mechanics & Trading", "App & Safety"],
        )
        for required in (
            "simulation.rng", "simulation.loot", "simulation.mechanics",
            "villagers.explorer", "navigation.portals", "world.spawners", "world.ores",
            "automation.macro_studio", "world.profiles", "build.recipes",
            "utilities.results", "utilities.diagnostics",
        ):
            self.assertIn(required, BY_ID)

    def test_every_workbench_has_a_task_section_and_player_group(self):
        banned = {"Gameplay", "Seed Tools", "Calculators", "RNG Tools", "Utilities & Safety"}
        for tool in TOOLS:
            self.assertIn(nav_section(tool), {label for label, _ in NAV_SECTIONS})
            self.assertNotIn(workspace_group(tool), banned)

    def test_every_workbench_has_distinct_art_recovery_identity(self):
        keys = {tool.id: tool_art_key(tool) for tool in TOOLS}
        supported = set(_TEXTURES) | set(FUZZY_TERMS)
        missing = {tool_id: key for tool_id, key in keys.items() if key not in supported}
        self.assertFalse(missing, missing)
        self.assertGreaterEqual(len(set(keys.values())), 24)

    def test_guides_are_concise_discovery_copy_not_templates(self):
        for tool in TOOLS:
            guide = make_guide(tool)
            combined = " ".join((guide.summary, guide.when, guide.how, guide.inputs, guide.output, guide.limitations)).lower()
            for banned in (
                "use this when", "what you provide", "what you get", "historical",
                "compatibility aliases", "compatibility namespace",
            ):
                self.assertNotIn(banned, combined)
            self.assertLessEqual(len(guide.summary), 260)
            self.assertNotEqual(guide.summary, guide.when)

    def test_readme_describes_current_task_structure(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# F3+\n"))
        for section in ("Play & Travel", "Explore Worlds", "Plan & Build", "Mechanics & Trading", "App & Safety"):
            self.assertIn(section, readme)
        self.assertIn("Inputs and outputs", readme)
        self.assertIn("Automation and safety", readme)
        self.assertNotIn("457 historical", readme)
        self.assertNotIn("professional desktop shell", readme.lower())
        self.assertLess(len(readme.splitlines()), 220)

    def test_task_first_desktop_is_the_runtime_ui(self):
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        shell = (ROOT / "minescript" / "desktop.py").read_text(encoding="utf-8")
        self.assertIn("from minescript.desktop import run", main)
        for marker in ("WorkbenchCardDelegate", "CommandPalette", "WorkbenchCanvas", "Inspector25", "launch_tool"):
            self.assertIn(marker, shell)
        self.assertIn('QLabel("TASKS")', shell)
        self.assertIn("def build_menu", shell)
        self.assertIn("Play & Travel", shell)
        self.assertIn("self._sync_automation_chrome(False)", shell)
        self.assertNotIn("current or historical operation", shell)


if __name__ == "__main__":
    unittest.main()
