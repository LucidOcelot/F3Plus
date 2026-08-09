from __future__ import annotations

import unittest

from minescript.structured_results import _presentation_data
from minescript.visual_context_v234 import _context_for
from minescript.visual_results_v3 import construction_series


class VisualContext234Tests(unittest.TestCase):
    def test_private_visual_context_is_not_shown_as_result_data(self):
        visible = _presentation_data({
            "blocks": 256,
            "_visual_context": {"width": 16, "length": 16},
        })
        self.assertEqual(visible, {"blocks": 256})

    def test_scalar_build_result_can_recover_footprint_from_configured_geometry(self):
        spec = type("Spec", (), {"top": "Calculators", "submenu": "Build", "name": "Build Area Calculator"})()
        context = _context_for(spec, {"width": 12, "length": 30, "height": 4})
        merged = {"area_blocks": 360, **context}
        series = construction_series(spec, merged)
        self.assertTrue(series)
        self.assertEqual(series[0][0], "Footprint")
        self.assertEqual(series[0][1][0], (0, 0))
        self.assertEqual(series[0][1][-1], (0, 0))

    def test_build_geometry_context_keeps_only_renderer_relevant_inputs(self):
        spec = type("Spec", (), {"top": "Calculators", "submenu": "Build", "name": "Bridge Span"})()
        context = _context_for(spec, {"length": 64, "spacing": 8, "seed": 123, "probability": 0.5})
        self.assertEqual(context, {"length": 64, "spacing": 8})

    def test_nonspatial_calculator_does_not_receive_visual_context(self):
        spec = type("Spec", (), {"top": "Calculators", "submenu": "Storage", "name": "Storage Capacity"})()
        self.assertEqual(_context_for(spec, {"width": 12, "length": 12}), {})


if __name__ == "__main__":
    unittest.main()
