from __future__ import annotations

import unittest

from minescript.structured_results import _presentation_data
from minescript.visual_data import construction_fields, construction_series


class VisualDataTests(unittest.TestCase):
    def test_private_metadata_is_not_shown_as_result_data(self):
        visible = _presentation_data({
            "blocks": 256,
            "_internal": {"width": 16, "length": 16},
        })
        self.assertEqual(visible, {"blocks": 256})

    def test_build_result_generates_footprint_from_explicit_geometry(self):
        spec = type("Spec", (), {"top": "Calculators", "submenu": "Build", "name": "Build Area Calculator"})()
        series = construction_series(spec, {"area_blocks": 360, "width": 12, "length": 30})
        self.assertTrue(series)
        self.assertEqual(series[0][0], "Footprint")
        self.assertEqual(series[0][1][0], (0, 0))
        self.assertEqual(series[0][1][-1], (0, 0))

    def test_build_operations_expose_renderer_relevant_geometry_fields(self):
        fields = construction_fields("Bridge Span")
        self.assertEqual([field[0] for field in fields], ["length", "spacing"])

    def test_nonspatial_result_does_not_invent_a_visual(self):
        spec = type("Spec", (), {"top": "Calculators", "submenu": "Storage", "name": "Storage Capacity"})()
        self.assertEqual(construction_series(spec, {"item_capacity": 3456}), [])


if __name__ == "__main__":
    unittest.main()
