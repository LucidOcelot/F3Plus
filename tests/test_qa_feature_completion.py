from __future__ import annotations

import unittest

from minescript.gameplay.presets import alternating_steps, grid_steps, parallel_row_steps, serpentine_steps
from minescript.qa_features import JavaRandom, navigation, portal_tool, rng_tool, world_seed_tool
from minescript.world_analysis import _packed_indices


class QAFeatureCompletionTests(unittest.TestCase):
    def test_java_random_is_deterministic(self):
        a = JavaRandom(12345)
        b = JavaRandom(12345)
        self.assertEqual([a.next_int() for _ in range(8)], [b.next_int() for _ in range(8)])

    def test_loot_simulators_are_named_profiles_not_bernoulli_aliases(self):
        fishing = rng_tool("Fishing Loot Simulator", {"seed": 1, "attempts": 100})
        barter = rng_tool("Piglin Barter Simulator", {"seed": 1, "attempts": 100})
        self.assertIn("fish", fishing["counts"])
        self.assertIn("common barter", barter["counts"])
        self.assertNotEqual(fishing["profile"], barter["profile"])

    def test_generation_rng_tools_have_distinct_outputs(self):
        ore = rng_tool("Ore Placement Simulator", {"seed": 4, "attempts": 10, "cx": 2, "cz": -3, "min_y": -64, "max_y": 64})
        tree = rng_tool("Tree Generation Simulator", {"seed": 4, "attempts": 10, "cx": 2, "cz": -3, "probability": 0.2})
        self.assertIn("candidate_positions", ore)
        self.assertIn("attempts", tree)
        self.assertNotEqual(set(ore), set(tree))

    def test_portal_tools_perform_different_jobs(self):
        params = {"x": 800.0, "z": -800.0, "other_x": 0.0, "other_z": 0.0, "radius": 4}
        cost = portal_tool("Portal Cost Optimizer", params)
        heat = portal_tool("Portal Reliability Heatmap", params)
        gate = portal_tool("Destination Gate Planner", params)
        self.assertIn("best", cost)
        self.assertIn("samples", heat)
        self.assertIn("recommended_nether_block", gate)

    def test_multistop_route_uses_user_stops(self):
        result = navigation("Multi-stop Route", {"x1": 0, "y1": 64, "z1": 0, "stops": "10,64,0,A;10,64,10,B;0,64,10,C"})
        names = [row[0] for row in result["route"]]
        self.assertIn("A", names)
        self.assertIn("B", names)
        self.assertIn("C", names)

    def test_world_analysis_names_fail_closed_without_world_save(self):
        result = world_seed_tool("Ore Distribution", "World Analysis", {"world_path": "", "cx": 0, "cz": 0, "radius": 16})
        self.assertTrue(result["requires_generated_world"])
        self.assertIn("no longer substitutes", result["reason"])

    def test_construction_patterns_are_semantically_distinct(self):
        filled = serpentine_steps(4, 1.0, 0.25, True)
        rows = parallel_row_steps(4, 1.0, 0.5)
        alternating = alternating_steps(4, 1.0, 0.5)
        grid = grid_steps(4, 1.0, 0.5)
        self.assertNotEqual(filled, rows)
        self.assertNotEqual(rows, alternating)
        self.assertGreater(len(grid), len(rows))
        self.assertTrue(any(step.get("place") is False for step in alternating if step.get("type") == "move"))

    def test_packed_block_state_decoder(self):
        # 4 bits/value, 16 values per long. Palette indices 0..15 in one long.
        value = 0
        for i in range(16):
            value |= i << (i * 4)
        decoded = _packed_indices([value], 16, 16)
        self.assertEqual(decoded, list(range(16)))


if __name__ == "__main__":
    unittest.main()
