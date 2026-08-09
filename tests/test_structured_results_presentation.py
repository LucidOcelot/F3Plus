from __future__ import annotations

import unittest

from minescript.structured_results import _presentation_data


class StructuredResultPresentationTests(unittest.TestCase):
    def test_internal_contract_metadata_is_hidden_from_normal_result_view(self):
        raw = {
            "operation": "Biome Composition",
            "display_name": "Biome Composition",
            "mc_enum": 27,
            "summary": "Useful result",
            "implementation": {
                "kind": "analysis",
                "engine": "cubiomes",
                "exactness": "sampled",
                "prerequisite": "seed",
                "limitation": "sampling",
            },
            "nested": {"biome": "Plains", "biome_id": 1},
        }
        visible = _presentation_data(raw)
        self.assertEqual(visible["summary"], "Useful result")
        self.assertEqual(visible["nested"]["biome"], "Plains")
        self.assertEqual(visible["nested"]["biome_id"], 1)
        self.assertNotIn("operation", visible)
        self.assertNotIn("display_name", visible)
        self.assertNotIn("mc_enum", visible)
        self.assertNotIn("implementation", visible)


if __name__ == "__main__":
    unittest.main()
