from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")

ROOT = Path(__file__).resolve().parents[1]

from minescript.feature_executor import FeatureExecutor
from minescript.rng_compat import JavaRandom as CompatRandom
from minescript.seed.java_rng import JavaRandom
from minescript.tool_registry import BY_ID, modes_for
from minescript.visual_contracts import chart_series, map_series
from updater import update_channel


class RepairArchitectureContracts(unittest.TestCase):
    def test_runtime_no_longer_depends_on_qa_rng_or_installer(self):
        import minescript.qa_features as qa

        self.assertIs(qa.JavaRandom, JavaRandom)
        self.assertIs(CompatRandom, JavaRandom)
        self.assertFalse(hasattr(qa, "install"))
        self.assertFalse((ROOT / "minescript" / "catalog_direct.py").exists())

    def test_public_workbench_exports_responsive_controllers(self):
        source = (ROOT / "minescript" / "workbenches.py").read_text(encoding="utf-8")
        explained = (ROOT / "minescript" / "operation_dialog25.py").read_text(encoding="utf-8")
        dedicated = (ROOT / "minescript" / "dedicated_workbenches25.py").read_text(encoding="utf-8")
        self.assertIn("from .operation_dialog25 import OperationDialog", source)
        self.assertIn("from .dedicated_workbenches25 import", source)
        self.assertIn("from .async_workbench import OperationDialog as _AsyncOperationDialog", explained)
        self.assertIn("from .async_loot_workbench import LootWorkbenchDialog", dedicated)

    def test_stable_channel_is_default_and_preview_is_explicit(self):
        old = os.environ.pop("F3PLUS_UPDATE_CHANNEL", None)
        try:
            self.assertEqual(update_channel(), ("stable", "stable"))
            os.environ["F3PLUS_UPDATE_CHANNEL"] = "preview"
            self.assertEqual(update_channel(), ("preview", "main"))
        finally:
            if old is None:
                os.environ.pop("F3PLUS_UPDATE_CHANNEL", None)
            else:
                os.environ["F3PLUS_UPDATE_CHANNEL"] = old

    def test_arch_ui_contract_is_narrower_than_legacy_internal_defaults(self):
        mode = next(mode for mode in modes_for(BY_ID["build.planner"]) if mode.name == "Arch")
        executor = FeatureExecutor()
        visible = executor.input_fields(mode.legacy)
        self.assertEqual([field[0] for field in visible], ["radius"])
        base = executor._base_defaults(mode.legacy)
        self.assertIn("secondary", base)
        self.assertIn("height", base)

    def test_route_defaults_from_real_ui_schema_execute(self):
        executor = FeatureExecutor("1.21.3")
        names = {"Resource Route": "resource_order", "Structure Tour": "tour_order", "Biome Expedition": "biome_order", "Breadcrumb Recorder": "points_recorded", "Expedition Recorder": "distance_walked_blocks", "Survey Mode": "survey_points", "Loop Detection": "has_loop"}
        route_modes = {mode.name: mode for mode in modes_for(BY_ID["navigation.routes"]) if mode.legacy is not None}
        for name, expected in names.items():
            with self.subTest(name=name):
                spec = route_modes[name].legacy
                values = {}
                for key, _label, default, kind in executor.input_fields(spec):
                    values[key] = default[0] if kind == "choice" and isinstance(default, list) and default else default
                result = executor.execute(spec, values)
                self.assertEqual(result.status, "ok", result.data)
                self.assertIn(expected, result.data, result.data)
                self.assertFalse(result.data.get("available") is False, result.data)

    def test_visuals_require_operation_semantics(self):
        arch = next(mode for mode in modes_for(BY_ID["build.planner"]) if mode.name == "Arch").legacy
        fake = {"min": 64, "max": 128, "numbers": [64, 128]}
        self.assertEqual(map_series(arch, fake), ([], None))
        self.assertIsNone(chart_series(arch, fake))
        series, _ = map_series(arch, {"points": [[-3, 0], [0, 4], [3, 0]]})
        self.assertTrue(series)

    def test_main_sources_do_not_restore_import_time_install_stack(self):
        init_text = (ROOT / "minescript" / "__init__.py").read_text(encoding="utf-8")
        main_text = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertNotIn(".install()", init_text)
        self.assertNotIn(".install()", main_text)


if __name__ == "__main__":
    unittest.main()
