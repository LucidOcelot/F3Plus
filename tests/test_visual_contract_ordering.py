from __future__ import annotations

import unittest

from minescript.catalog_ids import BY_NAME
from minescript.visual_contracts import chart_series, map_series


class VisualOrderingContracts(unittest.TestCase):
    def test_structure_candidates_are_unordered_points(self):
        spec = BY_NAME["Village"][0]
        series, _center = map_series(spec, {"candidate_chunks": [[1, 2], [4, -3], [7, 5]]})
        self.assertEqual(len(series), 1)
        self.assertEqual(series[0][0], "Candidate Chunks")
        self.assertFalse(series[0][2])

    def test_navigation_route_is_an_ordered_path(self):
        spec = BY_NAME["Coordinate Route"][0]
        series, _center = map_series(spec, {
            "start": {"x": 0, "y": 64, "z": 0},
            "target": {"x": 100, "y": 70, "z": 100},
        })
        self.assertEqual(len(series), 1)
        self.assertEqual(series[0][0], "Route")
        self.assertTrue(series[0][2])

    def test_ore_chart_preserves_category_labels(self):
        spec = BY_NAME["Ore Distribution"][0]
        chart = chart_series(spec, {"ore_counts": {"diamond_ore": 12, "iron_ore": 85, "coal_ore": 140}})
        self.assertIsNotNone(chart)
        title, rows, kind = chart
        self.assertEqual(kind, "bars")
        self.assertEqual(title, "Ore Counts")
        self.assertEqual([label for label, _value in rows], ["diamond_ore", "iron_ore", "coal_ore"])


if __name__ == "__main__":
    unittest.main()
