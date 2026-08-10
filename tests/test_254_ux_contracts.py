from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")

from minescript.catalog_ids import SPECS as LEGACY_SPECS
from minescript.enchantment_catalog import rarity_from_weight
from minescript.feature_executor import FeatureExecutor
from minescript.seed_generation import SEED_REGENERATABLE
from minescript.seed_text import DEFAULT_SEED_TEXT, java_string_hash, seed_number

GUI_IMPORT_ERROR = None
try:
    from PySide6.QtWidgets import QApplication, QComboBox
    from minescript.minecraft_simulators import MinecraftJarData
    from minescript.minecraft_widgets import AssetProvider, ItemPicker, SeedEdit
    from minescript.operation_dialog25 import OperationDialog
    from minescript.result_view254 import ResultView
    from minescript.tool_registry import BY_ID
except ImportError as exc:
    GUI_IMPORT_ERROR = exc
    QApplication = QComboBox = MinecraftJarData = AssetProvider = ItemPicker = SeedEdit = OperationDialog = ResultView = BY_ID = None


class SeedAndRarityContracts(unittest.TestCase):
    def test_blank_seed_defaults_to_f3plus_text_seed(self):
        self.assertEqual(DEFAULT_SEED_TEXT, "F3Plus")
        self.assertEqual(seed_number(""), seed_number("F3Plus"))
        self.assertEqual(seed_number("F3Plus"), java_string_hash("F3Plus"))

    def test_numeric_seed_is_not_rehashed(self):
        self.assertEqual(seed_number("-12345"), -12345)
        self.assertEqual(seed_number(0), 0)

    def test_enchantment_weight_has_human_rarity(self):
        self.assertEqual(rarity_from_weight(10), "Common")
        self.assertEqual(rarity_from_weight(5), "Uncommon")
        self.assertEqual(rarity_from_weight(2), "Rare")
        self.assertEqual(rarity_from_weight(1), "Very Rare")

    def test_generated_world_analyzers_accept_both_save_and_seed(self):
        executor = FeatureExecutor(); failures = []
        specs = [spec for spec in LEGACY_SPECS if spec.top == "Seed Tools" and spec.name in SEED_REGENERATABLE]
        self.assertEqual({spec.name for spec in specs}, set(SEED_REGENERATABLE))
        required = {"world_path", "seed", "regenerate_from_seed", "accept_minecraft_eula"}
        for spec in specs:
            keys = {field[0] for field in executor.input_fields(spec)}
            missing = sorted(required - keys)
            if missing: failures.append((spec.name, missing))
        self.assertFalse(failures, f"Generated-world analyzers missing a save/seed source: {failures}")


@unittest.skipIf(GUI_IMPORT_ERROR is not None, f"Qt GUI runtime unavailable: {GUI_IMPORT_ERROR}")
class PublicUx254Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_item_picker_shows_name_not_registry_id(self):
        picker = ItemPicker(AssetProvider(MinecraftJarData("26.3 Snapshot 7")), "minecraft:diamond_pickaxe")
        self.assertNotIn("minecraft:", picker.combo.currentText())
        self.assertEqual(picker.value(), "minecraft:diamond_pickaxe")
        self.assertFalse(picker.combo.isEditable())

    def test_seed_edit_is_text_capable_and_defaults_to_f3plus(self):
        widget = SeedEdit("")
        self.assertEqual(widget.seed_text(), "F3Plus")
        self.assertEqual(widget.value(), seed_number("F3Plus"))
        widget.setText("hello world")
        self.assertEqual(widget.value(), java_string_hash("hello world"))

    def test_generated_world_analyzer_has_explicit_save_or_seed_source(self):
        class Settings:
            minecraft_version = "26.3 Snapshot 7"
            seed = None
            theme = "chorus"
            custom_palette = {}
        tool = BY_ID["world.ores"]
        dialog = OperationDialog(tool, FeatureExecutor(), Settings(), preferred_mode="Ore Distribution")
        self.assertIsInstance(dialog.result_view, ResultView)
        self.assertIsInstance(dialog.world_source_mode, QComboBox)
        self.assertEqual([dialog.world_source_mode.itemText(i) for i in range(dialog.world_source_mode.count())], ["Seed", "World save"])
        self.assertEqual(dialog.world_source_mode.currentText(), "Seed")
        seed_widget = dialog.inputs.get("seed"); world_widget = dialog.inputs.get("world_path")
        self.assertEqual(seed_widget.text(), "F3Plus")
        self.assertTrue(world_widget.parentWidget().isHidden())
        self.assertFalse(seed_widget.parentWidget().isHidden())
        values = dialog.values()
        self.assertTrue(values["regenerate_from_seed"]); self.assertEqual(values["world_path"], "")
        dialog.world_source_mode.setCurrentText("World save")
        self.assertFalse(world_widget.parentWidget().isHidden())
        self.assertTrue(seed_widget.parentWidget().isHidden())
        values = dialog.values(); self.assertFalse(values["regenerate_from_seed"])
        dialog.close()

    def test_operation_copy_does_not_restore_redundant_ai_style_boilerplate(self):
        source = __import__("pathlib").Path(__file__).resolve().parents[1].joinpath("minescript", "operation_dialog25.py").read_text(encoding="utf-8")
        self.assertNotIn("will not pretend", source.lower())
        self.assertNotIn("active calculation input", source.lower())
        self.assertIn('label.setText("RESULT")', source)

    def test_simulator_source_restricts_breeding_ui_to_horse_stats(self):
        source = __import__("pathlib").Path(__file__).resolve().parents[1].joinpath("minescript", "dedicated_workbenches25.py").read_text(encoding="utf-8")
        self.assertIn('self.species.addItem("Horse")', source)
        self.assertIn("self.species.hide()", source)
        self.assertIn("Set both parent horses' health, movement speed, and jump strength", source)
        for excluded in ("Cat", "Ocelot", "Fox", "Panda", "Bee", "Goat", "Hoglin", "Strider"):
            self.assertNotIn(f'self.species.addItem("{excluded}")', source)
        self.assertIn("Average health", source); self.assertIn("Average speed", source); self.assertIn("Jump strength", source)


if __name__ == "__main__":
    unittest.main()
