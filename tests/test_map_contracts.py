from __future__ import annotations

import unittest

from minescript.map_contracts import extract_coordinate_layers


class LegacyMapContractTests(unittest.TestCase):
    def test_unrelated_numeric_pairs_are_not_coordinates(self):
        self.assertEqual(extract_coordinate_layers({"minimum": [64, 128], "maximum": [256, 512], "range": [0, 100]}), {})

    def test_explicit_candidate_chunks_are_mapped_to_block_centers(self):
        layers = extract_coordinate_layers({"candidate_chunks": [[1, 2], [4, -3]]})
        self.assertIn("Candidate Chunks", layers)
        points = [(x, z) for x, z, _detail in layers["Candidate Chunks"]]
        self.assertEqual(points, [(24.0, 40.0), (72.0, -40.0)])

    def test_coordinate_dictionaries_remain_supported(self):
        layers = extract_coordinate_layers({"nearest": {"x": 160, "y": 64, "z": -80}})
        self.assertTrue(layers)
        self.assertIn((160.0, -80.0), [(x, z) for values in layers.values() for x, z, _detail in values])


if __name__ == "__main__":
    unittest.main()
