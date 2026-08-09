from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from minescript.feature_executor import FeatureExecutor
from minescript.ui_depth_v234 import field_help, task_art_key
from minescript.villager_portraits_v234 import profession_texture_members
from minescript.visual_results_v3 import visual_ui_capabilities


ROOT = Path(__file__).resolve().parents[1]


class UiDepth234Tests(unittest.TestCase):
    def test_villager_profession_art_uses_villager_skin_layers_not_workstations(self):
        members = profession_texture_members("librarian")
        self.assertIn("assets/minecraft/textures/entity/villager/villager.png", members)
        self.assertIn("assets/minecraft/textures/entity/villager/type/plains.png", members)
        self.assertIn("assets/minecraft/textures/entity/villager/profession/librarian.png", members)
        joined = "\n".join(members)
        self.assertNotIn("lectern", joined)
        self.assertNotIn("textures/block/", joined)

    def test_visual_ui_exposes_interaction_controls_not_only_a_static_preview(self):
        capabilities = set(visual_ui_capabilities())
        self.assertTrue({
            "wheel zoom", "drag pan", "fit to data", "series visibility",
            "grid toggle", "point labels", "cursor coordinates", "copy visible coordinates",
        }.issubset(capabilities))

    def test_interactive_map_widget_constructs_headlessly(self):
        from PySide6.QtWidgets import QApplication
        from minescript import visual_results
        from minescript.ui_theme import palette
        from minescript.visual_results_v3 import install

        app = QApplication.instance() or QApplication([])
        install()
        widget = visual_results.MapPreview(
            "Test map",
            [("Village", [(8.0, 8.0), (168.0, -72.0)]), ("Route", [(0.0, 0.0), (64.0, 32.0)])],
            palette("chorus"),
            center=(8.0, 8.0),
        )
        self.assertEqual(len(widget.layer_checks), 2)
        self.assertTrue(widget.grid_toggle.isChecked())
        self.assertEqual(widget.fit_button.text(), "Fit")
        self.assertIn("Copy visible", widget.copy_button.text())
        widget.deleteLater()
        app.processEvents()

    def test_task_specific_icons_cover_visual_and_technical_families(self):
        executor = FeatureExecutor("1.21.3")
        cases = {
            ("Seed Tools", "Spawners", "Dungeon/Pig Spawner Locator"): "spawner",
            ("Seed Tools", "Biomes", "Nearest Biome"): "biome",
            ("Navigation", "Portal Helpers", "Sister Portal"): "portal",
            ("Calculators", "Shapes", "Circle"): "shape",
            ("Calculators", "Farm", "Crop Yield"): "farm",
        }
        for path, expected in cases.items():
            self.assertEqual(task_art_key(executor.spec(path)), expected, path)

    def test_search_override_help_is_explicit_about_cost_and_generation_budget(self):
        help_text = field_help("ignore_max_generation_limit").lower()
        self.assertIn("cpu", help_text)
        self.assertIn("disk", help_text)
        self.assertIn("chunk-generation budget", help_text)

    def test_readme_is_project_overview_not_release_changelog(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("## What 2.3.4 focuses on", readme)
        self.assertNotIn("## Validation and documentation", readme)
        self.assertIn("# F3+ 2.3.4", readme)
        self.assertIn("F3+ was unfortunately developed with generative AI assistance.", readme)
        self.assertIn("Ignore maximum search / generation limit", readme)
        self.assertIn("villager profession skin layers", readme.lower())
        self.assertLess(len(readme.splitlines()), 125)


if __name__ == "__main__":
    unittest.main()
