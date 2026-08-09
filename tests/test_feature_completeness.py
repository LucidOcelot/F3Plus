from __future__ import annotations

import gzip
from pathlib import Path
import struct
import tempfile
import unittest

from minescript.coordinates import Position
from minescript.feature_executor import FeatureExecutor
from minescript.tool_registry import BY_ID, LEGACY_TO_CANONICAL, modes_for
from minescript.world_profiles import read_level_dat


def _name(value: str) -> bytes:
    raw = value.encode("utf-8")
    return struct.pack(">H", len(raw)) + raw


def _string(name: str, value: str) -> bytes:
    raw = value.encode("utf-8")
    return b"\x08" + _name(name) + struct.pack(">H", len(raw)) + raw


def _int(name: str, value: int) -> bytes:
    return b"\x03" + _name(name) + struct.pack(">i", value)


def _long(name: str, value: int) -> bytes:
    return b"\x04" + _name(name) + struct.pack(">q", value)


def _compound(name: str, payload: bytes) -> bytes:
    return b"\x0a" + _name(name) + payload + b"\x00"


def _level_dat() -> bytes:
    version = _compound("Version", _string("Name", "1.21.3"))
    worldgen = _compound("WorldGenSettings", _long("seed", 123456789012345678))
    data = _compound(
        "Data",
        _string("LevelName", "Regression World")
        + _int("DataVersion", 4189)
        + version
        + worldgen
        + _int("SpawnX", 12)
        + _int("SpawnY", 72)
        + _int("SpawnZ", -44)
        + _long("LastPlayed", 1234567890),
    )
    root = b"\x0a" + _name("") + data + b"\x00"
    return gzip.compress(root)


class FeatureCompletenessTests(unittest.TestCase):
    def test_special_workbenches_are_real_registry_entries(self):
        expected = {
            "automation.macro_studio": "Macro Studio",
            "world.profiles": "World Profiles & Local Saves",
            "build.recipes": "Recipe & Material Explorer",
            "utilities.results": "Result History",
            "utilities.diagnostics": "Diagnostics",
        }
        for tool_id, title in expected.items():
            self.assertIn(tool_id, BY_ID)
            self.assertEqual(BY_ID[tool_id].name, title)
            self.assertTrue(any(mode.special for mode in modes_for(tool_id)), tool_id)
        self.assertEqual(len(LEGACY_TO_CANONICAL), 457)

    def test_end_has_no_sister_coordinate_conversion(self):
        with self.assertRaises(ValueError):
            Position(64, 70, 64).sister("End")

    def test_portal_reliability_heatmap_is_labeled_as_geometry_not_probability(self):
        executor = FeatureExecutor("1.21.3")
        spec = next(spec for spec in executor.all_specs() if spec.name == "Portal Reliability Heatmap") if hasattr(executor, "all_specs") else None
        if spec is None:
            from minescript.catalog_ids import SPECS
            spec = next(row for row in SPECS if row.name == "Portal Reliability Heatmap")
        result = executor.execute(spec, {"x": 800.0, "z": -800.0, "other_x": 0.0, "other_z": 0.0, "radius": 4})
        self.assertIn("metric_warning", result.data)
        self.assertIn("not a probability", result.data["metric_warning"].lower())
        for row in result.data.get("samples", []):
            self.assertNotIn("reliability", row)
            self.assertIn("normalized_proximity_to_ideal", row)

    def test_level_dat_profile_extracts_seed_version_spawn_and_name(self):
        with tempfile.TemporaryDirectory() as temp:
            world = Path(temp) / "World"
            world.mkdir()
            (world / "level.dat").write_bytes(_level_dat())
            row = read_level_dat(world)
        self.assertTrue(row["readable"])
        self.assertEqual(row["name"], "Regression World")
        self.assertEqual(row["version_name"], "1.21.3")
        self.assertEqual(row["seed"], 123456789012345678)
        self.assertEqual(row["spawn"], [12, 72, -44])
        self.assertEqual(row["data_version"], 4189)


if __name__ == "__main__":
    unittest.main()
