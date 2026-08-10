from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")

ROOT = Path(__file__).resolve().parents[1]

from minescript.catalog_ids import BY_NAME
from minescript.minecraft_art import _TEXTURES
from minescript.location_input import LOCATION_KEYS, applies_to
from minescript.tool_registry import BY_ID, modes_for
from minescript.ui_dialogs import field_help
from minescript.visual_contracts import map_series


class MinecraftNativeUxContracts(unittest.TestCase):
    def test_search_families_use_shared_location_abstraction(self):
        for tool_id in ("world.structures", "world.spawners", "world.biomes", "world.area", "world.analysis", "world.nether", "world.slime"):
            tool = BY_ID[tool_id]
            modes = [mode.legacy for mode in modes_for(tool) if mode.legacy is not None]
            self.assertTrue(any(applies_to(spec) for spec in modes), tool_id)
        self.assertTrue({"x", "z", "cx", "cz", "center_x", "center_z"}.issubset(LOCATION_KEYS))

    def test_seed_help_distinguishes_world_and_simulation_seed(self):
        world = field_help("seed", "Known Java world seed")
        sim = field_help("seed", "Simulation seed")
        self.assertIn("world seed", world.lower())
        self.assertIn("not the minecraft world seed", sim.lower())
        self.assertNotEqual(world, sim)

    def test_common_technical_fields_have_real_explanations(self):
        cases = {
            ("probability", "Probability"): "0 to 1",
            ("attempts", "Attempts"): "independent",
            ("observed_long", "Observed nextLong"): "64-bit",
            ("worldgen_max_chunks", "Maximum exact chunks"): "safety budget",
            ("stack_size", "Stack size"): "64",
        }
        for (key, label), expected in cases.items():
            text = field_help(key, label)
            self.assertIn(expected.lower(), text.lower(), (key, text))
            self.assertNotIn("value used by this operation", text.lower())

    def test_semantic_art_keys_can_recover_minecraft_assets(self):
        required = {"map", "route", "portal", "spawner", "biome", "ore", "shape", "farm", "redstone", "storage", "enchant", "anvil", "loot", "brewing", "horse", "trade"}
        self.assertTrue(required.issubset(_TEXTURES), required - set(_TEXTURES))
        for key in required:
            self.assertTrue(_TEXTURES[key], key)

    def test_simulator_ui_does_not_ask_players_for_raw_nbt_or_enchantment_json(self):
        source = (ROOT / "minescript" / "simulation_workbenches.py").read_text(encoding="utf-8")
        for forbidden in ("Parent A breeding NBT (JSON)", "Parent B breeding NBT (JSON)", "Left enchantments JSON", "Right enchantments JSON"):
            self.assertNotIn(forbidden, source)
        self.assertIn("ItemPicker", source)
        self.assertIn("EnchantmentEditor", source)
        self.assertIn("ParentTraits", source)
        self.assertIn("reading installed minecraft enchantment data", source.lower())

    def test_villager_explorer_is_virtualized_not_table_backed(self):
        source = (ROOT / "minescript" / "villager_workbench.py").read_text(encoding="utf-8")
        self.assertIn("QAbstractListModel", source)
        self.assertIn("QListView", source)
        self.assertIn("setUniformItemSizes", source)
        self.assertNotIn("QTableWidget(", source)
        self.assertNotIn("trades[:25]", source)

    def test_long_running_workbenches_have_activity_indicators(self):
        generic = (ROOT / "minescript" / "async_workbench.py").read_text(encoding="utf-8")
        loot = (ROOT / "minescript" / "async_loot_workbench.py").read_text(encoding="utf-8")
        for source in (generic, loot):
            self.assertIn("QProgressBar", source)
            self.assertIn("setRange(0, 0)", source)
        self.assertIn("Cancel", generic)
        self.assertIn("Cancel simulation", loot)

    def test_structure_and_spawn_candidate_layers_are_unordered(self):
        village = BY_NAME["Village"][0]
        series, _ = map_series(village, {"candidate_chunks": [[1, 2], [4, -3], [7, 5]]})
        self.assertTrue(series)
        self.assertFalse(series[0][2])
        spawn = BY_NAME["Spawn Analysis"][0]
        series, _ = map_series(spawn, {"candidate_sets": {"Village": [[1, 2], [4, -3]]}, "slime_chunks": [[0, 0], [1, 0]]})
        self.assertTrue(series)
        self.assertTrue(all(not row[2] for row in series))

    def test_live_position_async_wrapper_has_visible_result_contract(self):
        source = (ROOT / "minescript" / "async_workbench.py").read_text(encoding="utf-8")
        self.assertIn('"Current Position", "Capture Position"', source)
        self.assertIn('"chunk_x"', source)
        self.assertIn('"Live F3+C capture"', source)


if __name__ == "__main__":
    unittest.main()
