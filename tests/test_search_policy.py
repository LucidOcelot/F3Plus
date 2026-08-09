from __future__ import annotations

import unittest
from types import SimpleNamespace

from minescript.feature_executor import FeatureExecutor
from minescript.search_policy import (
    IGNORE_LIMIT_KEY,
    SEARCH_MODES,
    exact_regeneration_cap,
    has_match,
    prepare_attempt,
    run_until_found,
    supports,
)


class SearchPolicyTests(unittest.TestCase):
    def test_until_found_includes_configured_maximum_when_step_does_not_land_on_it(self):
        spec = SimpleNamespace(top="Seed Tools", submenu="Structures", name="Village")
        attempted = []

        def execute(radius):
            attempted.append(radius)
            return SimpleNamespace(status="ok", data={"candidate_chunks": []})

        _, summary = run_until_found(
            spec,
            {"radius": 8, "radius_step": 8, "max_search_radius": 31},
            execute,
        )
        self.assertEqual(attempted, [8, 16, 24, 31])
        self.assertEqual(summary["last_radius_searched"], 31)

    def test_until_found_expands_and_stops_on_first_match(self):
        spec = SimpleNamespace(top="Seed Tools", submenu="Structures", name="Village")
        attempted = []

        def execute(radius):
            attempted.append(radius)
            hits = [] if radius < 96 else [(4, -2)]
            return SimpleNamespace(status="ok", data={"candidate_chunks": hits})

        result, summary = run_until_found(
            spec,
            {"radius": 64, "radius_step": 16, "max_search_radius": 160},
            execute,
        )
        self.assertEqual(attempted, [64, 80, 96])
        self.assertEqual(result.data["candidate_chunks"], [(4, -2)])
        self.assertTrue(summary["found"])
        self.assertEqual(summary["found_radius"], 96)
        self.assertEqual(summary["attempts"], 3)
        self.assertFalse(summary["ignore_maximum_limit"])

    def test_ignore_limit_continues_past_configured_maximum(self):
        spec = SimpleNamespace(top="Seed Tools", submenu="Structures", name="Village")
        attempted = []

        def execute(radius):
            attempted.append(radius)
            return SimpleNamespace(status="ok", data={"candidate_chunks": [(1, 1)] if radius >= 96 else []})

        _, summary = run_until_found(
            spec,
            {"radius": 32, "radius_step": 16, "max_search_radius": 48, IGNORE_LIMIT_KEY: True},
            execute,
        )
        self.assertEqual(attempted, [32, 48, 64, 80, 96])
        self.assertTrue(summary["found"])
        self.assertEqual(summary["found_radius"], 96)
        self.assertTrue(summary["ignore_maximum_limit"])
        self.assertIsNone(summary["effective_maximum_radius"])

    def test_spawner_cluster_mode_requires_a_cluster_not_just_single_hits(self):
        spec = SimpleNamespace(top="Seed Tools", submenu="Spawners", name="Double Spawner Locator")
        self.assertFalse(has_match(spec, {"hits": [{"position": [0, 64, 0]}], "clusters": []}))
        self.assertTrue(has_match(spec, {"hits": [], "clusters": [{"spawners": 2}]}))

    def test_exact_spawner_regeneration_respects_chunk_budget(self):
        spec = SimpleNamespace(top="Seed Tools", submenu="Spawners", name="Dungeon/Pig Spawner Locator")
        effective, reason = exact_regeneration_cap(
            spec,
            {"radius": 8, "world_path": "", "regenerate_from_seed": True, "worldgen_max_chunks": 4096},
            128,
        )
        self.assertEqual(effective, 31)
        self.assertIn("4,096-chunk", reason)

    def test_exact_spawner_ignore_toggle_raises_attempt_budget(self):
        spec = SimpleNamespace(top="Seed Tools", submenu="Spawners", name="Dungeon/Pig Spawner Locator")
        values = {
            "radius": 8,
            "world_path": "",
            "regenerate_from_seed": True,
            "worldgen_max_chunks": 4096,
            IGNORE_LIMIT_KEY: True,
        }
        effective, reason = exact_regeneration_cap(spec, values, 128)
        self.assertEqual(effective, 128)
        self.assertIn("ignored", reason.lower())
        attempt = prepare_attempt(spec, values, 40)
        self.assertEqual(attempt["worldgen_max_chunks"], 81 * 81)

    def test_search_until_found_stops_on_missing_generated_world(self):
        spec = SimpleNamespace(top="Seed Tools", submenu="Biomes", name="Island Finder")
        attempted = []

        def execute(radius):
            attempted.append(radius)
            return SimpleNamespace(status="ok", data={"requires_generated_world": True, "reason": "Select a generated save."})

        _, summary = run_until_found(
            spec,
            {"radius": 32, "radius_step": 32, "max_search_radius": 512},
            execute,
        )
        self.assertEqual(attempted, [32])
        self.assertFalse(summary["found"])

    def test_location_families_expose_search_modes_and_ignore_toggle(self):
        executor = FeatureExecutor("1.21.3")
        paths = [
            ("Seed Tools", "Spawners", "Dungeon/Pig Spawner Locator"),
            ("Seed Tools", "Structures", "Village"),
            ("Seed Tools", "Biomes", "Nearest Biome"),
            ("Seed Tools", "Biomes", "Island Finder"),
            ("Seed Tools", "Slime", "2x2 Cluster"),
        ]
        for path in paths:
            spec = executor.spec(path)
            self.assertTrue(supports(spec), path)
            fields = {field[0]: field for field in executor.input_fields(spec)}
            self.assertIn("radius", fields, path)
            self.assertEqual(fields["search_mode"][2], SEARCH_MODES)
            self.assertIn("radius_step", fields, path)
            self.assertIn("max_search_radius", fields, path)
            self.assertIn(IGNORE_LIMIT_KEY, fields, path)
            self.assertEqual(fields[IGNORE_LIMIT_KEY][3], "bool", path)

    def test_generated_terrain_finders_use_chunk_coordinates_and_chunk_radius(self):
        executor = FeatureExecutor("1.21.3")
        spec = executor.spec(("Seed Tools", "Biomes", "Island Finder"))
        fields = {field[0]: field for field in executor.input_fields(spec)}
        self.assertIn("cx", fields)
        self.assertIn("cz", fields)
        self.assertIn("chunks", fields["radius"][1].lower())
        self.assertNotIn("target_biome", fields)
        self.assertNotIn("x", fields)
        self.assertNotIn("z", fields)

    def test_non_locator_reports_do_not_get_search_controls(self):
        executor = FeatureExecutor("1.21.3")
        for path in (
            ("Seed Tools", "Structures", "Structure Density"),
            ("Seed Tools", "Biomes", "Rare Biome Search"),
            ("Seed Tools", "World Analysis", "Search Radius Optimizer"),
        ):
            spec = executor.spec(path)
            self.assertFalse(supports(spec), path)
            keys = {field[0] for field in executor.input_fields(spec)}
            self.assertNotIn("search_mode", keys, path)
            self.assertNotIn(IGNORE_LIMIT_KEY, keys, path)


if __name__ == "__main__":
    unittest.main()
