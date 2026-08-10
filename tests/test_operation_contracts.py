from __future__ import annotations

import unittest

from minescript.catalog_ids import SPECS
from minescript.feature_executor import FeatureExecutor


class OperationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executor = FeatureExecutor("1.21.3")

    def spec(self, name: str):
        matches = [row for row in SPECS if row.top == "Navigation" and row.submenu == "Routes" and row.name == name]
        self.assertEqual(len(matches), 1, name)
        return matches[0]

    def field_keys(self, name: str):
        return [row[0] for row in self.executor.input_fields(self.spec(name))]

    def defaults(self, name: str):
        fields = self.executor.input_fields(self.spec(name))
        return {key: default[0] if kind == "choice" and isinstance(default, list) and default else default for key, _label, default, kind in fields}

    def test_route_ui_exposes_every_handler_input(self):
        self.assertEqual(self.field_keys("Coordinate Route"), ["x1", "y1", "z1", "x2", "y2", "z2"])
        self.assertIn("stops", self.field_keys("Resource Route"))
        self.assertIn("stops", self.field_keys("Structure Tour"))
        self.assertIn("return_to_start", self.field_keys("Structure Tour"))
        self.assertIn("stops", self.field_keys("Biome Expedition"))
        self.assertIn("points", self.field_keys("Breadcrumb Recorder"))
        self.assertIn("sample_interval", self.field_keys("Breadcrumb Recorder"))
        self.assertIn("points", self.field_keys("Expedition Recorder"))
        self.assertIn("sample_interval", self.field_keys("Expedition Recorder"))
        self.assertIn("radius", self.field_keys("Survey Mode"))
        self.assertIn("spacing", self.field_keys("Survey Mode"))
        self.assertIn("points", self.field_keys("Loop Detection"))
        self.assertIn("epsilon", self.field_keys("Loop Detection"))

    def test_default_ui_values_execute_as_real_workflows(self):
        expected_keys = {
            "Coordinate Route": "horizontal_blocks",
            "Resource Route": "resource_order",
            "Structure Tour": "tour_order",
            "Biome Expedition": "biome_order",
            "Breadcrumb Recorder": "points_recorded",
            "Expedition Recorder": "distance_walked_blocks",
            "Survey Mode": "survey_points",
            "Loop Detection": "has_loop",
        }
        for name, key in expected_keys.items():
            with self.subTest(name=name):
                result = self.executor.execute(self.spec(name), self.defaults(name))
                self.assertEqual(result.status, "ok", result.data)
                self.assertIn(key, result.data, result.data)
                self.assertFalse(result.data.get("available") is False, result.data)


if __name__ == "__main__":
    unittest.main()
