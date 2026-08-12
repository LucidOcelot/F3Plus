from __future__ import annotations

import unittest

from minescript.catalog_ids import SPECS
from minescript.feature_executor import FeatureExecutor
from minescript.tool_registry import TOOLS, modes_for


class OperationCoverageTests(unittest.TestCase):
    def test_every_operation_is_reachable_from_a_visible_workbench(self):
        routed = {
            mode.legacy.id
            for tool in TOOLS
            for mode in modes_for(tool)
            if mode.legacy is not None
        }
        expected = {spec.id for spec in SPECS}
        self.assertEqual(routed, expected)
        self.assertLess(len(TOOLS), 50, "The visible product surface should stay consolidated.")

    def test_every_operation_has_an_executable_dry_run(self):
        executor = FeatureExecutor("1.21.3")
        failures = []
        for spec in SPECS:
            try:
                result = executor.dry_run(spec)
            except Exception as exc:
                failures.append(f"{spec.name}: raised {type(exc).__name__}: {exc}")
                continue
            if not isinstance(result.data, dict) or not result.data:
                failures.append(f"{spec.name}: empty/non-dict result")
        self.assertFalse(failures, "\n" + "\n".join(failures))

    def test_generated_world_prerequisites_remain_explicit(self):
        executor = FeatureExecutor("1.21.3")
        for name in (
            "Ore Distribution", "Ore Exposure Estimate", "Cave Exposure Estimate",
            "Largest Mountain Chain", "Largest Cave Region", "Flat Terrain Finder",
            "Peninsula Detector", "River Crossing Finder", "Lake Density",
        ):
            spec = next(s for s in SPECS if s.name == name)
            result = executor.dry_run(spec)
            self.assertTrue(result.data.get("requires_generated_world"), name)
            self.assertIn("reason", result.data, name)


if __name__ == "__main__":
    unittest.main()
