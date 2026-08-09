from __future__ import annotations

import unittest

from minescript.catalog_ids import BY_ID as LEGACY_BY_ID, SPECS
from minescript.catalog_integrity import ORIGINAL_FEATURE_COUNT
from minescript.feature_executor import FeatureExecutor
from minescript.tool_registry import BY_ID, LEGACY_TO_CANONICAL, TOOLS, canonical_for_legacy, registry_health


class FullCatalogIntegrityTests(unittest.TestCase):
    def test_historical_ids_are_preserved_as_compatibility_aliases(self):
        self.assertEqual(len(SPECS), ORIGINAL_FEATURE_COUNT)
        self.assertEqual(len(LEGACY_BY_ID), ORIGINAL_FEATURE_COUNT)
        self.assertEqual(len(LEGACY_TO_CANONICAL), ORIGINAL_FEATURE_COUNT)
        self.assertEqual(set(LEGACY_TO_CANONICAL), set(LEGACY_BY_ID))
        self.assertLess(len(TOOLS), 50, "The visible product surface should stay consolidated.")
        self.assertEqual(len(BY_ID), len(TOOLS))
        health = registry_health()
        self.assertEqual(health["unmapped_legacy_ids"], 0)
        for legacy_id, tool_id in LEGACY_TO_CANONICAL.items():
            self.assertIn(tool_id, BY_ID, legacy_id)
            self.assertEqual(canonical_for_legacy(legacy_id).id, tool_id)

    def test_every_historical_operation_still_has_an_executable_dry_run(self):
        executor = FeatureExecutor("1.21.3")
        failures = []
        for spec in SPECS:
            try:
                result = executor.dry_run(spec)
            except Exception as exc:
                failures.append(f"{spec.id}: raised {type(exc).__name__}: {exc}")
                continue
            if not isinstance(result.data, dict) or not result.data:
                failures.append(f"{spec.id}: empty/non-dict result")
            if spec.id not in LEGACY_TO_CANONICAL:
                failures.append(f"{spec.id}: not routed to a canonical workbench")
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
