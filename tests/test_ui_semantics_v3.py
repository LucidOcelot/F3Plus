from __future__ import annotations

import unittest
from unittest.mock import patch

from minescript.feature_executor import FeatureExecutor
from minescript.seed_worldgen import resolve_java_runtime
from minescript.spawner_v3 import _entity_ids, _matches
from minescript.ui_polish_v3 import _coordinate_rows, _construction_fields
from minescript.villagers import BASELINE_SOURCE, _version_key, load_for_version
from minescript.visual_results_v3 import construction_series, seed_series


class UiSemanticsV3Tests(unittest.TestCase):
    def test_villager_explorer_never_falls_back_to_empty_when_no_trade_json_exists(self):
        with patch("minescript.villagers.installed_versions", return_value={}):
            rows, source = load_for_version("26.3 Snapshot 7")
        self.assertEqual(source, BASELINE_SOURCE)
        self.assertGreater(len(rows), 30)
        self.assertTrue(any(row.profession == "librarian" for row in rows))
        self.assertTrue(any(row.profession == "fletcher" for row in rows))

    def test_weekly_snapshot_does_not_sort_as_a_modern_stable_release(self):
        self.assertGreater(_version_key("1.21.8"), _version_key("23w18a"))

    def test_spawner_nbt_extracts_common_spawn_data_forms(self):
        self.assertEqual(
            _entity_ids({"SpawnData": {"entity": {"id": "minecraft:zombie"}}}),
            ["minecraft:zombie"],
        )
        ids = _entity_ids({
            "SpawnPotentials": [
                {"data": {"entity": {"id": "minecraft:skeleton"}}},
                {"data": {"entity": {"id": "minecraft:spider"}}},
            ]
        })
        self.assertEqual(ids, ["minecraft:skeleton", "minecraft:spider"])

    def test_spawner_filter_distinguishes_mob_types(self):
        hit = {"spawner_kind": "Mob Spawner", "mobs": ["Zombie"]}
        self.assertTrue(_matches(hit, "Zombie"))
        self.assertFalse(_matches(hit, "Skeleton"))
        self.assertTrue(_matches(hit, "All mob spawners"))

    def test_spawner_dry_run_keeps_integrity_contract(self):
        executor = FeatureExecutor("1.21.3")
        result = executor.dry_run(("Seed Tools", "Spawners", "Dungeon/Pig Spawner Locator"))
        self.assertTrue(result.data.get("requires_generated_world"))
        self.assertIn("implementation", result.data)
        self.assertEqual(result.data["implementation"]["kind"], "generated-world-analysis")

    def test_java_runtime_selects_a_compatible_candidate(self):
        with patch("minescript.seed_worldgen._java_candidates", return_value=["java17", "java25"]), patch(
            "minescript.seed_worldgen._java_major", side_effect=lambda value: {"java17": 17, "java25": 25}[value]
        ):
            executable, major = resolve_java_runtime(25)
        self.assertEqual(executable, "java25")
        self.assertEqual(major, 25)

    def test_raw_structure_pairs_are_translated_to_chunk_columns(self):
        rows = _coordinate_rows("Trial Chamber", [(0, 14), (19, -19)])
        self.assertEqual(rows[0]["Chunk X"], 0)
        self.assertEqual(rows[0]["Chunk Z"], 14)
        self.assertEqual(rows[0]["Block center X"], 8)
        self.assertNotIn("Value 1", rows[0])

    def test_seed_candidate_sets_generate_map_series(self):
        series, center = seed_series({
            "center_chunk": [0, 0],
            "candidate_sets": {
                "Trial Chamber": [(0, 14), (19, -19)],
                "Ocean Monument": [(-18, 20)],
            },
        })
        labels = {label for label, _ in series}
        self.assertIn("Trial Chamber", labels)
        self.assertIn("Ocean Monument", labels)
        self.assertEqual(center, (8.0, 8.0))
        trial = next(points for label, points in series if label == "Trial Chamber")
        self.assertEqual(trial[0], (8.0, 232.0))

    def test_construction_tools_have_focused_fields_and_footprint_visuals(self):
        bridge = _construction_fields("Bridge Span")
        self.assertEqual([field[0] for field in bridge], ["length", "spacing"])
        spec = type("Spec", (), {"submenu": "Build"})()
        series = construction_series(spec, {"width": 12, "length": 30})
        self.assertEqual(series[0][0], "Footprint")
        self.assertEqual(series[0][1][-1], (0, 0))


if __name__ == "__main__":
    unittest.main()
