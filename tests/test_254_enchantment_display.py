from __future__ import annotations

import os
import random
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from minescript.enchantment_catalog import grouped_summary, loot_enchanted_book_enchantments
from minescript.enchantment_widgets import EnchantmentPossibilityPanel
from minescript.minecraft_simulators import EnchantingEngine, LootTableEngine


class _LootData:
    source = "test data"
    TABLE = {
        "minecraft:test/book": {
            "pools": [{
                "rolls": 1,
                "entries": [{
                    "type": "minecraft:item",
                    "name": "minecraft:book",
                    "functions": [{"function": "minecraft:enchant_randomly"}],
                }],
            }]
        }
    }

    def json_namespace(self, prefixes):
        prefixes = tuple(prefixes)
        if any("loot" in prefix for prefix in prefixes): return dict(self.TABLE)
        return {}

    def loot_tables(self): return dict(self.TABLE)
    def item_tags(self): return {}
    def enchantments(self):
        return {
            "minecraft:efficiency": {"weight": 10, "max_level": 5},
            "minecraft:mending": {"weight": 2, "max_level": 1, "treasure_only": True},
        }


class _EnchantData:
    source = "installed fixture"
    jar_path = "fixture.jar"

    def json_namespace(self, prefixes):
        prefixes = tuple(prefixes)
        if any("tags/enchantment" in prefix or "tags/enchantments" in prefix for prefix in prefixes): return {}
        if any("/enchantment/" in prefix or "/enchantments/" in prefix for prefix in prefixes):
            return {
                "minecraft:efficiency": {
                    "weight": 10,
                    "max_level": 5,
                    "min_cost": {"base": 1, "per_level_above_first": 10},
                    "max_cost": {"base": 51, "per_level_above_first": 10},
                    "supported_items": "#minecraft:enchantable/mining",
                }
            }
        return {}

    def item_tags(self):
        return {
            "minecraft:enchantable/mining": ["#minecraft:tools/pickaxes"],
            "minecraft:tools/pickaxes": ["minecraft:diamond_pickaxe"],
        }


class EnchantedBookDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_grouped_summary_explains_rarity_and_max_level(self):
        text = grouped_summary([
            {"name": "Mending", "rarity": "Very Rare", "max_level": 1},
            {"name": "Efficiency", "rarity": "Common", "max_level": 5},
            {"name": "Protection", "rarity": "Common", "max_level": 4},
        ])
        self.assertIn("vanilla enchantment weight", text)
        self.assertIn("Common: Efficiency (max 5)", text)
        self.assertIn("Protection (max 4)", text)
        self.assertIn("Very Rare: Mending", text)

    def test_scrollable_panel_keeps_every_enchantment_as_its_own_row(self):
        rows = [
            {"name": f"Enchant {index}", "rarity": "Common" if index < 12 else "Rare", "max_level": 5, "weight": 10 if index < 12 else 2}
            for index in range(30)
        ]
        panel = EnchantmentPossibilityPanel(); panel.set_rows(rows)
        self.assertEqual(panel.list.count(), 30)
        self.assertEqual(panel.count.text(), "30 possible enchantments")
        self.assertIn("Common", panel.list.item(0).text())
        self.assertIn("Rare", panel.list.item(29).text())

    def test_plain_book_plus_enchant_function_is_detected_as_enchanted_book(self):
        rows = loot_enchanted_book_enchantments(_LootData(), "minecraft:test/book")
        self.assertEqual({row["id"] for row in rows}, {"minecraft:efficiency", "minecraft:mending"})

    def test_loot_engine_reports_and_rolls_enchanted_book_not_plain_book(self):
        engine = LootTableEngine(_LootData())
        possible = engine.possible_items("minecraft:test/book")
        self.assertEqual([row["item"] for row in possible], ["minecraft:enchanted_book"])
        rolled = engine.roll("minecraft:test/book", rng=random.Random(1))
        self.assertEqual([stack.item for stack in rolled], ["minecraft:enchanted_book"])

    def test_enchanting_resolves_nested_item_tags_for_supported_items(self):
        engine = EnchantingEngine(_EnchantData())
        offers = engine.roll_offers("minecraft:diamond_pickaxe", 15, 12345)
        self.assertTrue(any(offer["enchantments"] for offer in offers), offers)
        self.assertTrue(any(row["id"] == "minecraft:efficiency" for offer in offers for row in offer["enchantments"]))


if __name__ == "__main__":
    unittest.main()
