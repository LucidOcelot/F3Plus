from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from minescript.seed_worldgen_reuse import (
    _radius_key,
    generate_reusable_reference_world,
    prepare_expansion_cache,
)
from minescript.seed_worldgen import canonical_version_id


class SeedWorldgenReuseTests(unittest.TestCase):
    def _cache(self, root: Path, *, version="26.2", seed=123, center=(0, 0), radius=8):
        version_id = canonical_version_id(version); cx, cz = center
        key = _radius_key(version_id, seed, cx, cz, radius)
        target = root / "worlds" / version_id / str(seed) / key
        region = target / "world" / "region"; region.mkdir(parents=True)
        (region / "r.0.0.mca").write_bytes(b"existing generated chunks")
        marker = target / ".f3plus-worldgen.json"
        marker.write_text(json.dumps({
            "version": version_id,
            "seed": seed,
            "center_chunk": [cx, cz],
            "radius_chunks": radius,
            "server_sha1": "fixture",
            "source": "official Mojang server reference generation",
            "world_relative": "world",
        }), encoding="utf-8")
        return target

    def test_larger_radius_promotes_existing_world_instead_of_copying_it(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); old = self._cache(root, radius=8)
            state = prepare_expansion_cache(root, "26.2", 123, (0, 0), 16)
            self.assertTrue(state["reused"])
            self.assertEqual(state["promoted_from_radius"], 8)
            target = Path(state["target"])
            self.assertFalse(old.exists())
            self.assertTrue((target / "world" / "region" / "r.0.0.mca").is_file())
            self.assertFalse((target / ".f3plus-worldgen.json").exists())

    def test_existing_larger_coverage_is_reused_without_server_launch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); target = self._cache(root, radius=32)
            with patch("minescript.seed_worldgen_reuse.generate_reference_world", side_effect=AssertionError("server should not launch")):
                world, meta = generate_reusable_reference_world(123, "26.2", center_chunk=(0, 0), radius_chunks=16, accept_eula=True, cache_root=root)
            self.assertEqual(world, target / "world")
            self.assertTrue(meta["cache_reused"])
            self.assertEqual(meta["cached_radius_chunks"], 32)
            self.assertFalse(meta["reference_world_extended"])

    def test_smaller_coverage_is_extended_in_promoted_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); self._cache(root, radius=8)
            version_id = canonical_version_id("26.2")
            target = root / "worlds" / version_id / "123" / _radius_key(version_id, 123, 0, 0, 16)

            def fake_generate(seed, version, **kwargs):
                self.assertEqual(seed, 123)
                self.assertEqual(kwargs["radius_chunks"], 16)
                self.assertTrue((target / "world" / "region" / "r.0.0.mca").is_file())
                self.assertFalse((target / ".f3plus-worldgen.json").exists())
                marker = target / ".f3plus-worldgen.json"
                marker.write_text(json.dumps({
                    "version": version_id,
                    "seed": 123,
                    "center_chunk": [0, 0],
                    "radius_chunks": 16,
                    "world_relative": "world",
                }), encoding="utf-8")
                return target / "world"

            with patch("minescript.seed_worldgen_reuse.generate_reference_world", side_effect=fake_generate):
                world, meta = generate_reusable_reference_world(123, "26.2", center_chunk=(0, 0), radius_chunks=16, accept_eula=True, cache_root=root)
            self.assertEqual(world, target / "world")
            self.assertTrue(meta["cache_reused"])
            self.assertTrue(meta["reference_world_extended"])
            self.assertEqual(meta["previous_radius_chunks"], 8)


if __name__ == "__main__":
    unittest.main()
