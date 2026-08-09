from __future__ import annotations

import unittest
from types import SimpleNamespace

from minescript.catalog_ids import SPECS
from minescript.feature_executor import FeatureExecutor
from minescript.tool_registry import LEGACY_TO_CANONICAL, TOOLS


class CanonicalOperationSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executor = FeatureExecutor("1.21.3")

    def result(self, name: str, top: str | None = None, submenu: str | None = None, params=None):
        matches = [spec for spec in SPECS if spec.name == name and (top is None or spec.top == top) and (submenu is None or spec.submenu == submenu)]
        self.assertEqual(len(matches), 1, (name, top, submenu, matches))
        return self.executor.execute(matches[0], params or {}).data

    def test_legacy_catalog_is_alias_namespace_not_visible_product_surface(self):
        self.assertEqual(len(LEGACY_TO_CANONICAL), len(SPECS))
        self.assertLess(len(TOOLS), len(SPECS) // 5)
        self.assertTrue(all(tool_id for tool_id in LEGACY_TO_CANONICAL.values()))

    def test_routes_preserve_distinct_jobs_inside_one_workbench(self):
        params = {"stops": "80,64,0,A;80,64,80,B;0,64,80,C"}
        resource = self.result("Resource Route", "Navigation", "Routes", params)
        tour = self.result("Structure Tour", "Navigation", "Routes", params)
        biome = self.result("Biome Expedition", "Navigation", "Routes", params)
        survey = self.result("Survey Mode", "Navigation", "Routes")
        self.assertIn("resource_order", resource); self.assertIn("tour_order", tour); self.assertIn("biome_order", biome); self.assertIn("survey_points", survey)

    def test_waypoint_lookup_sort_and_route_are_distinct_modes(self):
        executor = FeatureExecutor("1.21.3")
        executor.settings = SimpleNamespace(waypoints={"Near": [10, 64, 0], "North": [0, 70, -40], "Far": [100, 64, 100]})
        nearest = executor.execute(("Navigation", "Waypoints", "Nearest Waypoint"), {"x1": 0, "y1": 64, "z1": 0}).data
        sorted_rows = executor.execute(("Navigation", "Waypoints", "Sort Waypoints by Distance"), {"x1": 0, "y1": 64, "z1": 0}).data
        route = executor.execute(("Navigation", "Waypoints", "Waypoint Route"), {"x1": 0, "y1": 64, "z1": 0}).data
        self.assertEqual(nearest["nearest_waypoint"]["name"], "Near")
        self.assertIn("waypoints_by_distance", sorted_rows); self.assertNotIn("route_order", sorted_rows)
        self.assertIn("route_order", route); self.assertIn("segments", route)

    def test_chunk_and_region_modes_answer_different_questions(self):
        border = self.result("Chunk Border", "Navigation", "Coordinates")
        line = self.result("Chunk Line Navigator", "Navigation", "Coordinates")
        region = self.result("Region", "Navigation", "Coordinates")
        region_border = self.result("Region Border", "Navigation", "Coordinates")
        self.assertIn("nearest_border", border); self.assertIn("line_axis", line); self.assertIn("block_range", region); self.assertIn("distance_to_region_border_blocks", region_border)

    def test_portal_network_modes_are_distinct(self):
        router = self.result("Asymmetric Portal Router", "Seed Tools", "Nether")
        margin = self.result("Reliability Margin", "Seed Tools", "Nether")
        matrix = self.result("Bidirectional Link Matrix", "Seed Tools", "Nether")
        graph = self.result("Portal Graph", "Seed Tools", "Nether")
        self.assertIn("routes", router); self.assertIn("margins", margin); self.assertIn("links", matrix); self.assertIn("nodes", graph); self.assertIn("edges", graph)

    def test_portal_heatmap_does_not_claim_probability(self):
        heatmap = self.result("Portal Reliability Heatmap", "Seed Tools", "Nether")
        self.assertIn("metric_warning", heatmap)
        if heatmap.get("samples"):
            self.assertIn("normalized_proximity_to_ideal", heatmap["samples"][0]); self.assertNotIn("reliability", heatmap["samples"][0])

    def test_build_storage_and_shape_modes_keep_meaningful_differences(self):
        self.assertIn("full_stacks", self.result("Stacks", "Calculators", "Build"))
        self.assertIn("shulkers_required", self.result("Shulkers", "Calculators", "Build"))
        self.assertIn("double_chests_required", self.result("Double Chests", "Calculators", "Build"))
        self.assertIn("item_capacity", self.result("Storage Capacity", "Calculators", "Storage"))
        self.assertIn("double_chests", self.result("Bulk Materials", "Calculators", "Storage"))
        self.assertIn("shulkers_required", self.result("Shulker Requirement", "Calculators", "Storage"))
        spiral = self.result("Spiral", "Calculators", "Shapes"); helix = self.result("Helix", "Calculators", "Shapes")
        self.assertEqual(spiral.get("plane"), "XZ"); self.assertNotIn("height_blocks", spiral); self.assertIn("height_blocks", helix)

    def test_loader_and_distance_modes_keep_distinct_output(self):
        self.assertIn("planned_centers_relative_chunks", self.result("Chunk Loader Planner", "Calculators", "Technical"))
        self.assertIn("square_chunks", self.result("Chunk Loader Radius", "Calculators", "Technical"))
        self.assertIn("render_distance_chunks", self.result("Render Distance", "Calculators", "Technical"))
        self.assertIn("simulation_distance_chunks", self.result("Simulation Distance", "Calculators", "Technical"))
        footprint = self.result("Chunk Loading Simulator", "Seed Tools", "World Analysis")
        self.assertIn("outer_ring_chunks", footprint); self.assertIn("chunk_bounds", footprint)

    def test_rng_views_and_generation_models_remain_distinct_modes(self):
        viewer = self.result("RNG Sequence Viewer", "RNG Tools", "Probability")
        timeline = self.result("RNG Timeline", "RNG Tools", "Probability")
        enchanting = self.result("Enchantment Sequence Simulator", "RNG Tools", "Enchanting")
        tree = self.result("Tree Generation Simulator", "RNG Tools", "Generation RNG")
        geode = self.result("Geode Generator", "RNG Tools", "Generation RNG")
        self.assertIn("values", viewer); self.assertIn("timeline", timeline); self.assertIn("simulated_attempts", enchanting); self.assertIn("successful_positions", tree); self.assertIn("modeled_geode_chunks", geode)

    def test_named_rankings_do_not_expose_opaque_scores(self):
        slime = self.result("Farm Location Ranking", "Seed Tools", "Slime")
        spawn = self.result("Spawn Chunk Optimizer", "Seed Tools", "World Analysis")
        self.assertIn("ranking_order", slime); self.assertIn("ranking_order", spawn)
        self.assertTrue(all("score" not in row for row in slime.get("ranked_sites", [])))
        self.assertTrue(all("score" not in row for row in spawn.get("ranked_sites", [])))

    def test_search_radius_optimizer_is_cost_planning_not_fake_prediction(self):
        report = self.result("Search Radius Optimizer", "Seed Tools", "World Analysis")
        self.assertIn("relative_chunk_work_vs_radius_8", report["options"][0])
        self.assertIn("target-specific density model", report["interpretation"])
        self.assertNotIn("target_candidates", report)


if __name__ == "__main__":
    unittest.main()
