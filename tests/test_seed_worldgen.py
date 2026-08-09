from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from minescript.feature_executor import FeatureExecutor
from minescript.seed_worldgen import WorldgenError, canonical_version_id, generate_reference_world
from minescript.seed_worldgen_patch import SEED_REGENERATABLE


class SeedWorldgenTests(unittest.TestCase):
    def test_display_snapshot_normalizes_to_launcher_id(self):
        self.assertEqual(canonical_version_id("26.3 Snapshot 7"), "26.3-snapshot-7")
        self.assertEqual(canonical_version_id("26.2"), "26.2")

    def test_generation_requires_explicit_eula_acceptance(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(WorldgenError):
                generate_reference_world(1, "26.2", cache_root=Path(td), accept_eula=False)

    def test_generated_world_tools_expose_seed_regeneration_controls(self):
        executor = FeatureExecutor("26.3 Snapshot 7")
        fields = {row[0]: row for row in executor.input_fields("Ore Distribution")}
        self.assertIn("world_path", fields)
        self.assertIn("regenerate_from_seed", fields)
        self.assertIn("accept_minecraft_eula", fields)
        self.assertIn("worldgen_max_chunks", fields)
        self.assertEqual(fields["radius"][2], 8)

    def test_dry_run_never_launches_or_downloads_minecraft(self):
        executor = FeatureExecutor("26.3 Snapshot 7")
        with patch("minescript.seed_worldgen_patch.resolve_world_source", side_effect=AssertionError("network/worldgen called")):
            for name in SEED_REGENERATABLE:
                result = executor.dry_run(name)
                self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
