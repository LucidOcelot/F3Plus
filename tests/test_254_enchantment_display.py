from __future__ import annotations

import random
import unittest

from minescript.enchantment_catalog import grouped_summary, loot_enchanted_book_enchantments
from minescript.minecraft_simulators import LootTableEngine


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


class EnchantedBookDisplayTests(unittest.TestCase):
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

    def test_plain_book_plus_enchant_function_is_detected_as_enchanted_book(self):
        rows = loot_enchanted_book_enchantments(_LootData(), "minecraft:test/book")
        self.assertEqual({row["id"] for row in rows}, {"minecraft:efficiency", "minecraft:mending"})

    def test_loot_engine_reports_and_rolls_enchanted_book_not_plain_book(self):
        engine = LootTableEngine(_LootData())
        possible = engine.possible_items("minecraft:test/book")
        self.assertEqual([row["item"] for row in possible], ["minecraft:enchanted_book"])
        rolled = engine.roll("minecraft:test/book", rng=random.Random(1))
        self.assertEqual([stack.item for stack in rolled], ["minecraft:enchanted_book"])


if __name__ == "__main__":
    unittest.main()
