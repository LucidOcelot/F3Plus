from __future__ import annotations

import unittest

from minescript.catalog_ids import SPECS
from minescript.feature_executor import FeatureExecutor
from minescript.semantic_audit_v2 import scan_duplicate_reports


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
        self.assertIn("planned_centers_relative_chunks", planner)
        self.assertIn("square_chunks", radius)
        self.assertIn("render_distance_chunks", render)
        self.assertIn("simulation_distance_chunks", simulation)

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


if __name__ == "__main__":
    unittest.main()
