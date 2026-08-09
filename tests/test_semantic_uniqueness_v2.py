from __future__ import annotations

import unittest
from types import SimpleNamespace

from minescript.catalog_ids import SPECS
from minescript.feature_executor import FeatureExecutor
from minescript.semantic_audit_v2 import scan_duplicate_reports
from minescript.semantic_quality_v2 import _transform_terrain


class SemanticUniquenessV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executor = FeatureExecutor("1.21.3")

    def result(self, name: str, top: str | None = None, submenu: str | None = None, params=None):
        matches = [
            spec for spec in SPECS
            if spec.name == name
            and (top is None or spec.top == top)
            and (submenu is None or spec.submenu == submenu)
        ]
        self.assertEqual(len(matches), 1, (name, top, submenu, matches))
        return self.executor.execute(matches[0], params or {}).data

    def test_catalog_wide_duplicate_report_scan(self):
        audit = scan_duplicate_reports(self.executor)
        self.assertEqual(audit["catalog_entries"], 457)
        self.assertEqual(audit["audited_entries"], 457)
        self.assertFalse(audit["errors"], audit["errors"])
        self.assertFalse(
            audit["unexplained_duplicate_groups"],
            "Different catalog entries still produce indistinguishable user-facing reports:\n"
            + "\n".join(str(group) for group in audit["unexplained_duplicate_groups"]),
        )

    def test_routes_have_different_jobs(self):
        resource = self.result("Resource Route", "Navigation", "Routes")
        tour = self.result("Structure Tour", "Navigation", "Routes")
        biome = self.result("Biome Expedition", "Navigation", "Routes")
        survey = self.result("Survey Mode", "Navigation", "Routes")
        self.assertIn("resource_order", resource)
        self.assertIn("tour_order", tour)
        self.assertIn("biome_order", biome)
        self.assertIn("survey_points", survey)

    def test_waypoint_lookup_sort_and_route_are_not_aliases(self):
        executor = FeatureExecutor("1.21.3")
        executor.settings = SimpleNamespace(waypoints={
            "Near": [10, 64, 0],
            "North": [0, 70, -40],
            "Far": [100, 64, 100],
        })
        nearest = executor.execute(("Navigation", "Waypoints", "Nearest Waypoint"), {"x1": 0, "y1": 64, "z1": 0}).data
        sorted_rows = executor.execute(("Navigation", "Waypoints", "Sort Waypoints by Distance"), {"x1": 0, "y1": 64, "z1": 0}).data
        route = executor.execute(("Navigation", "Waypoints", "Waypoint Route"), {"x1": 0, "y1": 64, "z1": 0}).data
        self.assertEqual(nearest["nearest_waypoint"]["name"], "Near")
        self.assertIn("waypoints_by_distance", sorted_rows)
        self.assertIn("route_order", route)
        self.assertIn("segments", route)
        self.assertNotIn("route_order", sorted_rows)

    def test_chunk_and_region_navigation_is_not_alias_output(self):
        border = self.result("Chunk Border", "Navigation", "Coordinates")
        line = self.result("Chunk Line Navigator", "Navigation", "Coordinates")
        region = self.result("Region", "Navigation", "Coordinates")
        region_border = self.result("Region Border", "Navigation", "Coordinates")
        self.assertIn("nearest_border", border)
        self.assertIn("line_axis", line)
        self.assertIn("block_range", region)
        self.assertIn("distance_to_region_border_blocks", region_border)

    def test_portal_reports_are_distinct(self):
        router = self.result("Asymmetric Portal Router", "Seed Tools", "Nether")
        margin = self.result("Reliability Margin", "Seed Tools", "Nether")
        matrix = self.result("Bidirectional Link Matrix", "Seed Tools", "Nether")
        graph = self.result("Portal Graph", "Seed Tools", "Nether")
        self.assertIn("routes", router)
        self.assertIn("margins", margin)
        self.assertIn("links", matrix)
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)

    def test_portal_heatmap_does_not_present_a_fake_probability(self):
        heatmap = self.result("Portal Reliability Heatmap", "Seed Tools", "Nether")
        self.assertIn("metric_warning", heatmap)
        self.assertIn("samples", heatmap)
        if heatmap["samples"]:
            self.assertIn("normalized_proximity_to_ideal", heatmap["samples"][0])
            self.assertNotIn("reliability", heatmap["samples"][0])

    def test_build_and_storage_conversions_are_focused(self):
        stacks = self.result("Stacks", "Calculators", "Build")
        shulkers = self.result("Shulkers", "Calculators", "Build")
        chests = self.result("Double Chests", "Calculators", "Build")
        self.assertIn("full_stacks", stacks)
        self.assertIn("shulkers_required", shulkers)
        self.assertIn("double_chests_required", chests)

        capacity = self.result("Storage Capacity", "Calculators", "Storage")
        bulk = self.result("Bulk Materials", "Calculators", "Storage")
        requirement = self.result("Shulker Requirement", "Calculators", "Storage")
        self.assertIn("item_capacity", capacity)
        self.assertIn("double_chests", bulk)
        self.assertIn("shulkers_required", requirement)

    def test_construction_grid_and_circle_export_have_distinct_jobs(self):
        grid = self.result("Grid", "Calculators", "Build")
        lighting = self.result("Lighting Grid", "Calculators", "Build")
        export = self.result("Circle Layer Export", "Calculators", "Build")
        self.assertIn("point_count", grid)
        self.assertNotEqual(grid.get("points"), lighting.get("positions"))
        self.assertIn("export_text", export)
        self.assertIn("format", export)

    def test_spiral_and_helix_are_not_the_same_shape(self):
        spiral = self.result("Spiral", "Calculators", "Shapes")
        helix = self.result("Helix", "Calculators", "Shapes")
        self.assertEqual(spiral.get("plane"), "XZ")
        self.assertNotIn("height_blocks", spiral)
        self.assertIn("height_blocks", helix)
        self.assertTrue(all(len(point) == 2 for point in spiral["points"]))
        self.assertTrue(all(len(point) == 3 for point in helix["points"]))

    def test_loader_and_distance_tools_are_distinct(self):
        planner = self.result("Chunk Loader Planner", "Calculators", "Technical")
        radius = self.result("Chunk Loader Radius", "Calculators", "Technical")
        render = self.result("Render Distance", "Calculators", "Technical")
        simulation = self.result("Simulation Distance", "Calculators", "Technical")
        footprint = self.result("Chunk Loading Simulator", "Seed Tools", "World Analysis")
        self.assertIn("planned_centers_relative_chunks", planner)
        self.assertIn("square_chunks", radius)
        self.assertIn("render_distance_chunks", render)
        self.assertIn("simulation_distance_chunks", simulation)
        self.assertIn("outer_ring_chunks", footprint)
        self.assertIn("chunk_bounds", footprint)

    def test_rng_views_and_generation_models_are_distinct(self):
        viewer = self.result("RNG Sequence Viewer", "RNG Tools", "Probability")
        timeline = self.result("RNG Timeline", "RNG Tools", "Probability")
        enchanting = self.result("Enchantment Sequence Simulator", "RNG Tools", "Enchanting")
        tree = self.result("Tree Generation Simulator", "RNG Tools", "Generation RNG")
        geode = self.result("Geode Generator", "RNG Tools", "Generation RNG")
        self.assertIn("values", viewer)
        self.assertIn("timeline", timeline)
        self.assertIn("simulated_attempts", enchanting)
        self.assertIn("successful_positions", tree)
        self.assertIn("modeled_geode_chunks", geode)

    def test_slime_cluster_names_explain_different_patterns(self):
        square = self.result("2x2 Cluster", "Seed Tools", "Slime")
        quad = self.result("Quad Cluster", "Seed Tools", "Slime")
        self.assertEqual(square.get("required_shape"), "2×2 square")
        self.assertEqual(quad.get("required_shape"), "any connected 4+ chunk component")

    def test_site_rankings_use_named_factors_not_opaque_scores(self):
        slime = self.result("Farm Location Ranking", "Seed Tools", "Slime")
        spawn = self.result("Spawn Chunk Optimizer", "Seed Tools", "World Analysis")
        self.assertIn("ranking_order", slime)
        self.assertIn("ranking_order", spawn)
        self.assertTrue(all("score" not in row for row in slime.get("ranked_sites", [])))
        self.assertTrue(all("score" not in row for row in spawn.get("ranked_sites", [])))

    def test_search_radius_planner_does_not_fake_candidate_prediction(self):
        report = self.result("Search Radius Optimizer", "Seed Tools", "World Analysis")
        self.assertIn("relative_chunk_work_vs_radius_8", report["options"][0])
        self.assertIn("target-specific density model", report["interpretation"])
        self.assertNotIn("target_candidates", report)

    def test_terrain_base_transform_hides_opaque_score(self):
        transformed = _transform_terrain("Terrain Base Finder", {
            "ranked": [{"chunk": (2, 3), "base_score": 50.0, "mean_y": 80.0, "relief": 15.0}],
            "formula": "mean_surface_y - 2*within_chunk_relief",
        })
        self.assertNotIn("formula", transformed)
        self.assertNotIn("base_score", transformed["ranked"][0])
        self.assertIn("within_chunk_relief_blocks", transformed["ranked"][0])
        self.assertIn("ranking_basis", transformed)


if __name__ == "__main__":
    unittest.main()
