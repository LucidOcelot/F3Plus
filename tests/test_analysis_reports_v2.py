from __future__ import annotations

import unittest

from minescript.analysis_reports_v2 import (
    _humanize_biome_result,
    _ore_summary,
    _render_local_report,
    biome_id,
    biome_name,
)


class AnalysisReportsV2Tests(unittest.TestCase):
    def setUp(self):
        self.context = {
            "seed": 123,
            "center_chunk": [0, 0],
            "center_block": [8, 8],
            "requested_radius_chunks": 16,
            "radius_chunks": 16,
            "radius_was_limited": False,
            "area": {
                "width_chunks": 33,
                "height_chunks": 33,
                "total_chunks": 1089,
                "chunk_bounds": {"min_x": -16, "max_x": 16, "min_z": -16, "max_z": 16},
                "block_bounds": {"min_x": -256, "max_x": 271, "min_z": -256, "max_z": 271},
            },
            "slime": {
                "count": 111,
                "density_percent": 10.19,
                "difference_from_10_percent_points": 0.19,
                "largest_connected_cluster_chunks": 4,
                "nearest": {
                    "type": "Slime chunk",
                    "candidate_chunk": [1, 0],
                    "candidate_block_center": [24, 8],
                    "distance_chunks": 1.0,
                    "approx_distance_blocks": 16,
                    "direction": "east",
                },
                "chunks": [[1, 0], [1, 1]],
            },
            "structures": [
                {
                    "type": "Village", "candidate_count": 2, "candidates_per_1000_chunks": 1.837,
                    "candidate_chunk": [3, 4], "candidate_block_center": [56, 72],
                    "distance_chunks": 5.0, "approx_distance_blocks": 80, "direction": "southeast",
                },
                {
                    "type": "Trial Chamber", "candidate_count": 1, "candidates_per_1000_chunks": 0.918,
                    "candidate_chunk": [-4, 0], "candidate_block_center": [-56, 8],
                    "distance_chunks": 4.0, "approx_distance_blocks": 64, "direction": "west",
                },
                {"type": "Ocean Monument", "candidate_count": 0, "candidates_per_1000_chunks": 0.0},
            ],
            "structure_error": "",
            "biomes": {
                "available": True,
                "sample_count": 1089,
                "sample_step_blocks": 16,
                "distinct_count": 4,
                "dominant": {"biome": "Plains", "biome_id": 1, "sample_count": 600, "estimated_share_percent": 55.1},
                "mix": [
                    {"biome": "Plains", "biome_id": 1, "sample_count": 600, "estimated_share_percent": 55.1},
                    {"biome": "Forest", "biome_id": 4, "sample_count": 300, "estimated_share_percent": 27.55},
                    {"biome": "River", "biome_id": 7, "sample_count": 100, "estimated_share_percent": 9.18},
                    {"biome": "Cherry Grove", "biome_id": 185, "sample_count": 89, "estimated_share_percent": 8.17},
                ],
            },
            "worldgen": {
                "selected_version": "26.3 Snapshot 7",
                "calculation_version": "1.21.3",
                "exact_for_selected_version": False,
                "version_note": "fallback",
            },
        }

    def test_biome_ids_are_translated_to_readable_names(self):
        self.assertEqual(biome_name(1), "Plains")
        self.assertEqual(biome_name(185), "Cherry Grove")
        self.assertEqual(biome_id("cherry grove"), 185)
        self.assertEqual(biome_id("minecraft:plains"), 1)

    def test_local_reports_have_distinct_user_jobs(self):
        overview = _render_local_report("32-Chunk Analysis", self.context)
        composition = _render_local_report("Biome Composition", self.context)
        structures = _render_local_report("Structure Counts", self.context)
        slime = _render_local_report("Slime Distribution", self.context)
        highlights = _render_local_report("Notable Locations", self.context)
        technical = _render_local_report("Technical Score", self.context)
        build = _render_local_report("Build Score", self.context)
        exploration = _render_local_report("Exploration Score", self.context)

        self.assertIn("summary", overview)
        self.assertIn("biome_mix", composition)
        self.assertIn("structures", structures)
        self.assertIn("density_context", slime)
        self.assertIn("highlights", highlights)
        self.assertIn("factors", technical)
        self.assertIn("not_known_from_seed", build)
        self.assertIn("suggested_first_stops", exploration)
        self.assertNotIn("score", technical)
        self.assertNotIn("score", build)
        self.assertNotIn("score", exploration)

    def test_nearest_biome_result_keeps_id_but_adds_name_and_distance(self):
        data = {"center": (0, 0), "target_biome_id": 185, "nearest": (32, 48, 185)}
        _humanize_biome_result("Nearest Biome", data)
        self.assertEqual(data["target_biome_name"], "Cherry Grove")
        self.assertEqual(data["nearest"]["biome"], "Cherry Grove")
        self.assertGreater(data["nearest"]["distance_blocks"], 0)

    def test_resource_survey_groups_deepslate_variants(self):
        data = {
            "chunks_scanned": 2,
            "ore_counts": {"minecraft:diamond_ore": 3, "minecraft:deepslate_diamond_ore": 5},
            "exposed_ore_counts": {"minecraft:diamond_ore": 1, "minecraft:deepslate_diamond_ore": 2},
            "ore_by_y": {"minecraft:diamond_ore": {12: 3}, "minecraft:deepslate_diamond_ore": {-54: 5}},
        }
        rows = _ore_summary(data)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["resource"], "Diamond Ore")
        self.assertEqual(rows[0]["blocks_counted"], 8)
        self.assertEqual(rows[0]["exposed_blocks_counted"], 3)
        self.assertEqual(rows[0]["most_common_counted_y"], -54)


if __name__ == "__main__":
    unittest.main()
