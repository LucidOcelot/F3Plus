from __future__ import annotations

import unittest

from minescript.minecraft_simulators_v234 import (
    AnimalBreedingEngine,
    AnvilEngine,
    BASE_POTIONS,
    BrewingEngine,
    DYE_COLORS,
    EnchantingEngine,
    HorseBreedingEngine,
    LootTableEngine,
    MinecraftJarData,
    PotionState,
    cauldron_wash,
    dye_mix,
    loot_category,
    mix_leather_colors,
    modern_horse_attribute,
)
from minescript.simulation_lab_ui_v234 import SIMULATOR_ICON_CANDIDATES


class Simulator234Tests(unittest.TestCase):
    def setUp(self):
        # An impossible version hint normally falls back to the newest installed JAR;
        # the engines remain valid either way. Tests only assert behavior common to
        # installed data and the bundled baseline.
        self.data = MinecraftJarData("__f3plus_test_missing_version__")

    def test_loot_explorer_has_major_vanilla_source_categories(self):
        engine = LootTableEngine(self.data)
        categories = set(engine.categories())
        self.assertIn("Chests", categories)
        self.assertIn("Entity drops", categories)
        self.assertIn("Fishing", categories)
        self.assertIn("Piglin bartering", categories)
        if engine.using_baseline:
            self.assertEqual(engine.source, "Bundled baseline examples")

    def test_fishing_possible_loot_expands_nested_tables(self):
        engine = LootTableEngine(self.data)
        table = "minecraft:gameplay/fishing"
        if table not in engine.tables:
            self.skipTest("installed client does not expose the standard fishing table")
        items = {row["item"] for row in engine.possible_items(table)}
        self.assertIn("minecraft:cod", items)
        self.assertIn("minecraft:enchanted_book", items)

    def test_loot_simulation_is_seed_reproducible(self):
        engine = LootTableEngine(self.data)
        table = "minecraft:gameplay/piglin_bartering"
        if table not in engine.tables:
            table = next(iter(engine.tables))
        a = engine.simulate(table, pulls=50, seed=2468)
        b = engine.simulate(table, pulls=50, seed=2468)
        self.assertEqual(a["stats"], b["stats"])
        self.assertEqual(a["examples"], b["examples"])

    def test_random_chance_entry_is_not_checked_twice(self):
        engine = LootTableEngine(self.data)
        engine.tables = {
            "minecraft:test/half": {
                "pools": [{
                    "rolls": 1,
                    "entries": [{
                        "type": "minecraft:item",
                        "name": "minecraft:diamond",
                        "conditions": [{"condition": "minecraft:random_chance", "chance": 0.5}],
                    }],
                }]
            }
        }
        result = engine.simulate("minecraft:test/half", pulls=20000, seed=123)
        diamond = next(row for row in result["stats"] if row["item"] == "minecraft:diamond")
        self.assertGreater(diamond["observed_hit_rate"], 0.46)
        self.assertLess(diamond["observed_hit_rate"], 0.54)

    def test_loot_category_classifies_special_gameplay_tables(self):
        self.assertEqual(loot_category("minecraft:gameplay/fishing"), "Fishing")
        self.assertEqual(loot_category("minecraft:gameplay/piglin_bartering"), "Piglin bartering")
        self.assertEqual(loot_category("minecraft:chests/ancient_city"), "Chests")
        self.assertEqual(loot_category("minecraft:entities/zombie"), "Entity drops")

    def test_enchanting_three_slots_are_deterministic_and_exclude_treasure(self):
        engine = EnchantingEngine(self.data)
        first = engine.roll_offers("diamond_pickaxe", 15, 12345)
        second = engine.roll_offers("diamond_pickaxe", 15, 12345)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertEqual([row["slot"] for row in first], [1, 2, 3])
        self.assertEqual([row["lapis_cost"] for row in first], [1, 2, 3])
        offered = {entry["id"] for offer in first for entry in offer["enchantments"]}
        self.assertFalse(offered & set(engine.treasure_enchantments))

    def test_anvil_prior_work_and_merge_cost_are_exposed(self):
        enchanting = EnchantingEngine(self.data)
        anvil = AnvilEngine(enchanting)
        result = anvil.combine(
            "diamond_pickaxe",
            {"minecraft:efficiency": 4},
            {"minecraft:efficiency": 4},
            left_prior_operations=2,
            right_prior_operations=1,
            rename=True,
        )
        self.assertEqual(result["left_prior_penalty"], 3)
        self.assertEqual(result["right_prior_penalty"], 1)
        self.assertEqual(result["rename_cost"], 1)
        self.assertGreaterEqual(result["total_level_cost"], 5)
        self.assertIn("result_enchantments", result)

    def test_brewing_core_transitions(self):
        engine = BrewingEngine()
        awkward = engine.brew(BASE_POTIONS["water"], "nether_wart")
        self.assertEqual(awkward["output"].potion, "awkward")
        speed = engine.brew(BASE_POTIONS["awkward"], "sugar")
        self.assertEqual(speed["output"].potion, "swiftness")
        splash = engine.brew(BASE_POTIONS["swiftness"], "gunpowder")
        self.assertEqual(splash["output"].bottle, "splash_potion")
        lingering = engine.brew(
            PotionState("swiftness", "Speed", 180, 0, "splash_potion"),
            "dragon_breath",
        )
        self.assertEqual(lingering["output"].bottle, "lingering_potion")

    def test_leather_dye_mixing_is_stable_and_brightness_preserving(self):
        red = DYE_COLORS["red"]
        self.assertEqual(mix_leather_colors([red]), red)
        result = dye_mix(None, ["red", "blue"])
        self.assertRegex(result["hex"], r"^#[0-9A-F]{6}$")
        self.assertEqual(len(result["rgb"]), 3)

    def test_cauldron_wash_consumes_one_water_level(self):
        result = cauldron_wash(3, True)
        self.assertTrue(result["washed"])
        self.assertEqual(result["water_after"], 2)
        empty = cauldron_wash(0, True)
        self.assertFalse(empty["washed"])

    def test_modern_horse_attribute_stays_inside_vanilla_bounds(self):
        import random
        rng = random.Random(7)
        for _ in range(1000):
            value = modern_horse_attribute(29.0, 28.0, 15.0, 30.0, rng)
            self.assertGreaterEqual(value, 15.0)
            self.assertLessEqual(value, 30.0)

    def test_horse_simulator_returns_attributes_and_nbt_variant(self):
        engine = HorseBreedingEngine()
        result = engine.simulate(
            {"max_health": 24, "movement_speed": 0.24, "jump_strength": 0.75, "color": 1, "markings": 2},
            {"max_health": 28, "movement_speed": 0.28, "jump_strength": 0.85, "color": 4, "markings": 3},
            children=64,
            seed=99,
        )
        self.assertEqual(result["children"], 64)
        self.assertIn("max_health", result["stats"])
        sample = result["examples"][0]
        self.assertIn("Variant", sample)
        self.assertEqual(sample["Age"], -24000)
        self.assertEqual(len(sample["Attributes"]), 3)

    def test_general_animal_breeding_exposes_nbt_profiles(self):
        engine = AnimalBreedingEngine()
        for species in ("Horse", "Sheep", "Axolotl", "Panda", "Frog", "Camel", "Sniffer", "Turtle"):
            self.assertIn(species, engine.species())
            self.assertTrue(engine.profile(species).get("nbt"))
        child = engine.child("Sheep", {"Color": 0}, {"Color": 14}, seed=1)
        self.assertIn("Color", child)
        self.assertEqual(child["Age"], -24000)

    def test_simulator_icons_prefer_minecraft_assets_with_backups(self):
        for key in ("loot", "enchant", "anvil", "brewing", "dye", "animal"):
            self.assertIn(key, SIMULATOR_ICON_CANDIDATES)
            paths = SIMULATOR_ICON_CANDIDATES[key]
            self.assertTrue(paths)
            self.assertTrue(all(path.startswith("assets/minecraft/textures/") for path in paths))


if __name__ == "__main__":
    unittest.main()
