from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from minescript.seed_worldgen import generate_reference_world
from minescript.world_analysis import _chunk_sections, _section_blocks, analyze_world, iter_region_chunks


RUN = os.environ.get("F3PLUS_RUN_MOJANG_WORLDGEN") == "1"


def _chunk_zero_fingerprint(world: Path) -> str:
    h = hashlib.sha256()
    found = False
    for region in sorted((world / "region").glob("r.*.*.mca")):
        for chunk in iter_region_chunks(region):
            if int(chunk.get("xPos", 0)) != 0 or int(chunk.get("zPos", 0)) != 0:
                continue
            found = True
            for section in sorted(_chunk_sections(chunk), key=lambda q: int(q.get("Y", q.get("y", 0)))):
                parsed = _section_blocks(section)
                if parsed is None:
                    continue
                sy, names, indices = parsed
                h.update(str(sy).encode())
                for index in indices:
                    name = names[index] if 0 <= index < len(names) else "minecraft:air"
                    h.update(name.encode())
                    h.update(b"\0")
            return h.hexdigest()
    if not found:
        raise AssertionError("Chunk 0,0 was not generated")
    raise AssertionError("Chunk 0,0 contained no readable block states")


@unittest.skipUnless(RUN, "set F3PLUS_RUN_MOJANG_WORLDGEN=1 to run the Mojang server integration test")
class MojangWorldgenIntegrationTests(unittest.TestCase):
    def test_seed_materialization_matches_independent_vanilla_generation_block_for_block(self):
        seed = 8675309
        version = os.environ.get("F3PLUS_WORLDGEN_TEST_VERSION", "26.3-snapshot-6")
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            predicted = generate_reference_world(
                seed,
                version,
                center_chunk=(0, 0),
                radius_chunks=0,
                accept_eula=True,
                cache_root=Path(a),
                max_chunks=16,
            )
            actual = generate_reference_world(
                seed,
                version,
                center_chunk=(0, 0),
                radius_chunks=0,
                accept_eula=True,
                cache_root=Path(b),
                max_chunks=16,
            )
            # Two independent vanilla server generations must produce the same block
            # sequence in chunk 0,0. This tests the seed-only materialization pipeline
            # against a separately generated control world rather than its own cache.
            self.assertEqual(_chunk_zero_fingerprint(predicted), _chunk_zero_fingerprint(actual))

            predicted_analysis = analyze_world(predicted, center_chunk=(0, 0), radius_chunks=0, max_chunks=1)
            actual_analysis = analyze_world(actual, center_chunk=(0, 0), radius_chunks=0, max_chunks=1)
            self.assertEqual(predicted_analysis["ore_counts"], actual_analysis["ore_counts"])
            self.assertEqual(predicted_analysis["ore_by_y"], actual_analysis["ore_by_y"])
            self.assertEqual(predicted_analysis["peak"], actual_analysis["peak"])
            self.assertEqual(predicted_analysis["valley"], actual_analysis["valley"])


if __name__ == "__main__":
    unittest.main()
