from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, mock
import tempfile
import zipfile

import updater
from minescript.catalog_ids import BY_NAME
from minescript.feature_executor import FeatureExecutor
from minescript.search_policy import run_until_found
from minescript.villager_reference import complete_reference
from minescript.villagers import baseline_trades
from minescript.workbench_forms import _operation_family


class RestoredWorkbenchRegressionTests(TestCase):
    def test_updates_install_by_default_but_support_explicit_check_only(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(updater._automatic_install_enabled())
        with mock.patch.dict(os.environ, {"F3PLUS_AUTO_UPDATE": "0"}, clear=True):
            self.assertFalse(updater._automatic_install_enabled())
        with mock.patch.dict(os.environ, {"F3PLUS_CHECK_ONLY_UPDATE": "1"}, clear=True):
            self.assertFalse(updater._automatic_install_enabled())

    def test_current_position_does_not_leak_generic_navigation_fields(self):
        executor = FeatureExecutor()
        current = BY_NAME["Current Position"][0]
        continuous = BY_NAME["Continuous Capture"][0]
        bearing = BY_NAME["Bearing Lock"][0]
        self.assertEqual(executor.input_fields(current), [])
        self.assertEqual([row[0] for row in executor.input_fields(continuous)], ["interval"])
        self.assertEqual([row[0] for row in executor.input_fields(bearing)], ["x1", "z1", "x2", "z2"])

    def test_until_found_does_not_count_an_unavailable_backend_as_a_search(self):
        spec = BY_NAME["Double Spawner Locator"][0]
        unavailable = SimpleNamespace(status="unavailable", data={"available": False, "reason": "Java missing"})
        result, summary = run_until_found(spec, {"radius": 8, "radius_step": 8, "max_search_radius": 64}, lambda radius: unavailable)
        self.assertIs(result, unavailable)
        self.assertEqual(summary["attempts"], 0)
        self.assertIsNone(summary["last_radius_searched"])
        self.assertIn("prerequisite", summary["stop_reason"].lower())

    def test_until_found_really_expands_until_the_first_match(self):
        spec = BY_NAME["Double Spawner Locator"][0]
        radii = []
        def execute(radius):
            radii.append(radius)
            clusters = [] if radius < 24 else [[{"x": 1, "y": 64, "z": 1}, {"x": 8, "y": 64, "z": 8}]]
            return SimpleNamespace(status="ok", data={"clusters": clusters})
        _result, summary = run_until_found(spec, {"radius": 8, "radius_step": 8, "max_search_radius": 40}, execute)
        self.assertEqual(radii, [8, 16, 24])
        self.assertEqual(summary["attempts"], 3)
        self.assertTrue(summary["found"])
        self.assertEqual(summary["found_radius"], 24)

    def test_villager_reference_is_not_the_old_sparse_56_offer_dataset(self):
        rows = complete_reference(list(baseline_trades()))
        self.assertGreater(len(rows), 120)
        armorer = {(row.level, row.gives_id) for row in rows if row.profession == "armorer"}
        self.assertIn((4, "diamond_leggings"), armorer)
        self.assertIn((4, "diamond_boots"), armorer)
        self.assertIn((5, "diamond_helmet"), armorer)
        self.assertIn((5, "diamond_chestplate"), armorer)

    def test_ore_distribution_is_grouped_as_analysis_not_buried_other(self):
        self.assertEqual(_operation_family("Ore Distribution"), "Analysis & Distribution")

    def test_public_workbench_routes_loot_to_rich_canonical_explorer(self):
        from minescript.workbenches import LootWorkbenchDialog
        self.assertEqual(LootWorkbenchDialog.__module__, "minescript.loot_workbench")

    def test_namespace_cache_decodes_a_namespace_in_one_cached_pass(self):
        from minescript.minecraft_simulators import _namespace_cache
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "client.jar"
            with zipfile.ZipFile(path, "w") as jar:
                jar.writestr("data/minecraft/loot_table/chests/test.json", '{"pools": []}')
                jar.writestr("data/minecraft/tags/item/test.json", '{"values": ["minecraft:stone"]}')
            stat = path.stat(); prefixes = ("data/minecraft/loot_table/",)
            before = _namespace_cache.cache_info().hits
            first = _namespace_cache(str(path), stat.st_mtime_ns, stat.st_size, prefixes)
            second = _namespace_cache(str(path), stat.st_mtime_ns, stat.st_size, prefixes)
            self.assertIn("minecraft:chests/test", first)
            self.assertEqual(first, second)
            self.assertGreater(_namespace_cache.cache_info().hits, before)


if __name__ == "__main__":
    import unittest
    unittest.main()
