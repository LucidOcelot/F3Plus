from __future__ import annotations

import unittest

from minescript.catalog_ids import BY_ID, SPECS
from minescript.catalog_integrity import ORIGINAL_FEATURE_COUNT, generic_placeholder_reason
from minescript.feature_executor import FeatureExecutor


class FullCatalogIntegrityTests(unittest.TestCase):
    def test_original_catalog_count_and_ids_are_preserved(self):
        self.assertEqual(len(SPECS), ORIGINAL_FEATURE_COUNT)
        self.assertEqual(len(BY_ID), ORIGINAL_FEATURE_COUNT)
        self.assertEqual(len({(s.top, s.submenu, s.name) for s in SPECS}), ORIGINAL_FEATURE_COUNT)

    def test_every_catalog_entry_has_an_honest_dry_run(self):
        # 1.21.3 is explicitly mapped by the bundled Cubiomes integration, allowing
        # seed algorithms to be exercised instead of merely returning an unsupported
        # modern-version boundary. Terrain tools still fail closed until a generated
        # world path is supplied, which is their correct dry-run behavior.
        executor = FeatureExecutor("1.21.3")
        failures = []
        for spec in SPECS:
            try:
                result = executor.dry_run(spec)
            except Exception as exc:  # aggregate so CI reports every missing family
                failures.append(f"{spec.id}: raised {type(exc).__name__}: {exc}")
                continue
            if not isinstance(result.data, dict) or not result.data:
                failures.append(f"{spec.id}: empty/non-dict result")
                continue
            contract = result.data.get("implementation")
            if not isinstance(contract, dict):
                failures.append(f"{spec.id}: missing implementation contract")
            else:
                for key in ("kind", "engine", "exactness", "prerequisite", "limitation"):
                    if key not in contract:
                        failures.append(f"{spec.id}: implementation contract missing {key}")
            reason = generic_placeholder_reason(spec, result.data)
            if reason:
                failures.append(f"{spec.id}: {reason}; data={result.data!r}")
        self.assertFalse(failures, "\n" + "\n".join(failures))

    def test_prerequisite_states_are_explicit(self):
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
