from __future__ import annotations

import unittest
from pathlib import Path

from minescript.tool_guides import make_guide, tool_art_key
from minescript.tool_registry import BY_ID, LEGACY_TO_CANONICAL, TOOLS

ROOT = Path(__file__).resolve().parents[1]


class CanonicalUiDepthTests(unittest.TestCase):
    def test_visible_surface_is_workbench_scale_not_historical_catalog_scale(self):
        self.assertLess(len(TOOLS), 50)
        self.assertEqual(len(LEGACY_TO_CANONICAL), 457)
        for required in (
            "simulation.rng", "simulation.loot", "simulation.mechanics",
            "villagers.explorer", "navigation.portals", "world.spawners", "world.ores",
            "automation.macro_studio", "world.profiles", "build.recipes",
            "utilities.results", "utilities.diagnostics",
        ):
            self.assertIn(required, BY_ID)

    def test_task_specific_icons_cover_major_workbench_families(self):
        cases = {
            "world.spawners": "spawner", "world.biomes": "biome", "world.ores": "ore",
            "navigation.portals": "map", "build.planner": "building",
            "build.farming": "farm", "simulation.rng": "enchant",
            "simulation.loot": "loot", "simulation.mechanics": "brewing",
            "villagers.explorer": "villager",
        }
        for tool_id, expected in cases.items():
            self.assertEqual(tool_art_key(BY_ID[tool_id]), expected, tool_id)

    def test_guides_explain_operation_selection_and_limits(self):
        guide = make_guide(BY_ID["world.spawners"])
        self.assertIn("Choose an operation", guide.inputs)
        self.assertIn("generated", (guide.summary + guide.limitations).lower())
        rng = make_guide(BY_ID["simulation.rng"])
        self.assertIn("world-seed recovery", rng.limitations.lower())
        ore = make_guide(BY_ID["world.ores"])
        self.assertIn("generated", (ore.summary + ore.limitations).lower())

    def test_readme_is_product_overview_not_changelog_or_internal_feature_dump(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("# F3+ 2.4.2", readme)
        self.assertIn("## Workbenches", readme)
        self.assertIn("Ignore maximum search / generation limit", readme)
        self.assertIn("validated **Stable** updates", readme)
        self.assertIn("villager explorer", readme.lower())
        self.assertIn("minecraft-style enchanting table", readme.lower())
        self.assertIn("ore & cave explorer", readme.lower())
        self.assertIn("recolorable f3+ svg", readme.lower())
        self.assertIn("macro studio", readme.lower())
        self.assertNotIn("F3+ was unfortunately developed", readme)
        self.assertNotIn("## What 2.4.0 focuses on", readme)
        self.assertLess(len(readme.splitlines()), 210)


if __name__ == "__main__":
    unittest.main()