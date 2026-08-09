from __future__ import annotations

import unittest
from types import SimpleNamespace

from minescript.feature_executor import FeatureExecutor
from minescript.search_modes_v234 import (
    _exact_regeneration_cap,
    _has_match,
    _run_until_found,
    _search_radii,
    supports_search_mode,
)


class SearchModes234Tests(unittest.TestCase):
    def test_search_radii_include_the_configured_maximum(self):
        self.assertEqual(_search_radii(8, 8, 31), [8, 16, 24, 31])
        self.assertEqual(_search_radii(64, 32, 64), [64])

    def test_until_found_expands_and_stops_on_first_match(self):
        spec = SimpleNamespace(top="Seed Tools", submenu="Structures", name="Village")
        attempted = []

        def execute(radius):
            attempted.append(radius)
            hits = [] if radius < 96 else [(4, -2)]
            return SimpleNamespace(status="ok", data={"candidate_chunks": hits})

        result, summary = _run_until_found(
            spec,
            {"radius": 64, "radius_step": 16, "max_search_radius": 160},
            execute,
        )
        self.assertEqual(attempted, [64, 80, 96])
        self.assertEqual(result.data["candidate_chunks"], [(4, -2)])
        self.assertTrue(summary["found"])
        self.assertEqual(summary["found_radius"], 96)
        self.assertEqual(summary["attempts"], 3)

    def test_spawner_cluster_mode_requires_a_cluster_not_just_single_hits(self):
        spec = SimpleNamespace(top="Seed Tools", submenu="Spawners", name="Double Spawner Locator")
        self.assertFalse(_has_match(spec, {"hits": [{"position": [0, 64, 0]}], "clusters": []}))
        self.assertTrue(_has_match(spec, {"hits": [], "clusters": [{"spawners": 2}]}))

    def test_exact_spawner_regeneration_respects_chunk_budget(self):
        spec = SimpleNamespace(top="Seed Tools", submenu="Spawners", name="Dungeon/Pig Spawner Locator")
        effective, reason = _exact_regeneration_cap(
            spec,
            {
                "radius": 8,
                "world_path": "",
                "regenerate_from_seed": True,
                "worldgen_max_chunks": 4096,
            },
            128,
        )
        self.assertEqual(effective, 31)
        self.assertIn("4,096-chunk", reason)

    def test_search_until_found_stops_on_missing_generated_world(self):
        spec = SimpleNamespace(top="Seed Tools", submenu="Biomes", name="Island Finder")
        attempted = []

        def execute(radius):
            attempted.append(radius)
            return SimpleNamespace(
                status="ok",
                data={"requires_generated_world": True, "reason": "Select a generated save."},
            )

        _, summary = _run_until_found(
            spec,
            {"radius": 32, "radius_step": 32, "max_search_radius": 512},
            execute,
        )
        self.assertEqual(attempted, [32])
        self.assertFalse(summary["found"])

    def test_location_families_expose_both_search_modes(self):
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
            self.assertTrue(supports_search_mode(spec), path)
            fields = {field[0]: field for field in executor.input_fields(spec)}
            self.assertIn("radius", fields, path)
            self.assertIn("search_mode", fields, path)
            self.assertEqual(fields["search_mode"][2], ["Radius search", "Search until found"])
            self.assertIn("radius_step", fields, path)
            self.assertIn("max_search_radius", fields, path)

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
            self.assertFalse(supports_search_mode(spec), path)
            keys = {field[0] for field in executor.input_fields(spec)}
            self.assertNotIn("search_mode", keys, path)


if __name__ == "__main__":
    unittest.main()
