from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from minescript.seed_worldgen import generate_reference_world
from minescript.seed_worldgen_reuse import generate_reusable_reference_world
from minescript.world_analysis import ORE_NAMES, _chunk_sections, _section_blocks, analyze_world, iter_region_chunks


RUN = os.environ.get("F3PLUS_RUN_MOJANG_WORLDGEN") == "1"


def _chunk_zero_blocks(world: Path):
    """Return stable generation-derived block coordinates for chunk 0,0.

    A running server can legitimately mutate foliage, fluids, fire, snow and
    gravity/scheduled-update blocks after chunk generation. Ore coordinates and the
    non-gravity underground geology are world-generation outputs, so those are the
    appropriate block-level oracle for F3+'s seed-derived terrain/ore analyzers.
    """
    geology = {
        "minecraft:stone", "minecraft:deepslate", "minecraft:tuff", "minecraft:bedrock",
        "minecraft:granite", "minecraft:diorite", "minecraft:andesite", "minecraft:calcite",
        "minecraft:dripstone_block",
        *ORE_NAMES,
    }
    ores = set(); stable = set()
    for region in sorted((world / "region").glob("r.*.*.mca")):
        for chunk in iter_region_chunks(region):
            if int(chunk.get("xPos", 0)) != 0 or int(chunk.get("zPos", 0)) != 0: continue
            for section in _chunk_sections(chunk):
                parsed = _section_blocks(section)
                if parsed is None: continue
                sy, names, indices = parsed
                for index, palette_index in enumerate(indices):
                    name = names[palette_index] if 0 <= palette_index < len(names) else "minecraft:air"
                    if name not in geology: continue
                    ly = index // 256; rem = index % 256; lz = rem // 16; lx = rem % 16; pos = (lx, sy * 16 + ly, lz, name); stable.add(pos)
                    if name in ORE_NAMES: ores.add(pos)
            return stable, ores
    raise AssertionError("Chunk 0,0 was not generated")


@unittest.skipUnless(RUN, "set F3PLUS_RUN_MOJANG_WORLDGEN=1 to run the Mojang server integration test")
class MojangWorldgenIntegrationTests(unittest.TestCase):
    def test_seed_materialization_matches_independent_vanilla_generation(self):
        seed = 8675309; version = os.environ.get("F3PLUS_WORLDGEN_TEST_VERSION", "26.3-snapshot-7")
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            predicted, reuse = generate_reusable_reference_world(seed, version, center_chunk=(0, 0), radius_chunks=0, accept_eula=True, cache_root=Path(a), max_chunks=16)
            actual = generate_reference_world(seed, version, center_chunk=(0, 0), radius_chunks=0, accept_eula=True, cache_root=Path(b), max_chunks=16)
            self.assertFalse(reuse["reference_world_extended"])

            predicted_stable, predicted_ores = _chunk_zero_blocks(predicted); actual_stable, actual_ores = _chunk_zero_blocks(actual)
            self.assertEqual(predicted_ores, actual_ores); self.assertEqual(predicted_stable, actual_stable); self.assertGreater(len(predicted_stable), 1000)

            predicted_analysis = analyze_world(predicted, center_chunk=(0, 0), radius_chunks=0, max_chunks=1); actual_analysis = analyze_world(actual, center_chunk=(0, 0), radius_chunks=0, max_chunks=1)
            self.assertEqual(predicted_analysis["ore_counts"], actual_analysis["ore_counts"]); self.assertEqual(predicted_analysis["ore_by_y"], actual_analysis["ore_by_y"]); self.assertEqual(predicted_analysis["exposed_ore_counts"], actual_analysis["exposed_ore_counts"])


if __name__ == "__main__":
    unittest.main()
