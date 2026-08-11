from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")

from minescript.minecraft_simulators import AnimalBreedingEngine, EnchantingEngine, MinecraftJarData
from minescript.ux_semantics25 import DEFAULT_SEED_TEXT, rarity_from_weight, seed_value


class UxClarity254Contracts(unittest.TestCase):
    def test_blank_seed_defaults_to_f3plus(self):
        self.assertEqual(seed_value(""), seed_value(DEFAULT_SEED_TEXT))
        self.assertEqual(seed_value("F3Plus"), 2053630951)
        self.assertEqual(seed_value("12345"), 12345)

    def test_enchantment_rarity_labels_are_stable(self):
        self.assertEqual(rarity_from_weight(10), "Common")
        self.assertEqual(rarity_from_weight(5), "Uncommon")
        self.assertEqual(rarity_from_weight(2), "Rare")
        self.assertEqual(rarity_from_weight(1), "Very rare")

    def test_breeding_ui_only_exposes_stat_inheritance_species(self):
        self.assertEqual(AnimalBreedingEngine().species(), ["Horse", "Donkey"])

    def test_enchanted_book_reference_includes_rarity_and_level(self):
        engine = EnchantingEngine(MinecraftJarData("definitely-not-installed"))
        rows = engine.possible_book_enchantments()
        self.assertTrue(rows)
        self.assertTrue(all("rarity" in row and "max_level" in row for row in rows))

    def test_item_picker_is_dropdown_not_freeform_registry_input(self):
        source = open("minescript/minecraft_widgets.py", encoding="utf-8").read()
        self.assertIn("self.combo.setEditable(False)", source)
        self.assertIn("self.combo.itemData", source)

    def test_generic_operation_copy_does_not_repeat_input_inventory(self):
        source = open("minescript/operation_dialog25.py", encoding="utf-8").read()
        self.assertNotIn('f"{description} Inputs:', source)
        self.assertIn("self.context_card.setVisible(bool(explained))", source)
        self.assertIn("widget.setToolTip(tip)", source)
        self.assertNotIn("layout.addWidget(hint)", source)

    def test_result_surface_explains_maps_and_hides_internal_metadata(self):
        source = open("minescript/result_view25.py", encoding="utf-8").read()
        self.assertIn("Each marker is one returned structure location", source)
        self.assertIn('"confidence"', source)
        self.assertIn('"exactness"', source)
        self.assertNotIn('f"Exactness:', source)
        self.assertNotIn('f"Status: {status}', source)
        self.assertNotIn("does not claim", source.lower())

    def test_seed_backed_analyzers_accept_save_or_seed(self):
        source = open("minescript/seed_generation.py", encoding="utf-8").read()
        self.assertIn("Use seed when no save folder is selected", source)
        self.assertIn("Maximum chunks to generate", source)

    def test_enchanted_books_are_explained_in_loot_and_librarian_surfaces(self):
        source = open("minescript/dedicated_workbenches25.py", encoding="utf-8").read()
        self.assertIn("Possible enchanted-book rolls", source)
        self.assertIn("Possible enchantments", source)
        self.assertIn("possible_book_enchantments", source)


if __name__ == "__main__":
    unittest.main()
