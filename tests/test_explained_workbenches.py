from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")

GUI_IMPORT_ERROR = None
try:
    from PySide6.QtWidgets import QApplication
    from minescript.workbenches import OperationDialog
    from minescript.workbench_forms import _operation_description, _operation_group
except ImportError as exc:
    GUI_IMPORT_ERROR = exc
    QApplication = OperationDialog = None

from minescript.feature_executor import FeatureExecutor
from minescript.tool_registry import BY_ID, modes_for
from minescript.visual_contracts import chart_series, map_series


class _Settings:
    minecraft_version = "26.3 Snapshot 7"
    seed = 12345
    theme = "chorus"
    custom_palette = {}


def _mode(name: str):
    matches = [mode for mode in modes_for("build.planner") if mode.name == name]
    if len(matches) != 1:
        raise AssertionError((name, matches))
    return matches[0]


class ExplicitVisualContractTests(unittest.TestCase):
    def test_unrelated_numeric_data_is_not_invented_as_map_or_chart(self):
        mode = _mode("Arch")
        data = {"minimum": 64, "maximum": 128, "ratio": 2.0, "pair": [64, 128]}
        self.assertEqual(map_series(mode.legacy, data), ([], None))
        self.assertIsNone(chart_series(mode.legacy, data))

    def test_arch_declares_shape_points_as_map_data(self):
        mode = _mode("Arch")
        series, _center = map_series(mode.legacy, {"points": [[-4, 0], [-3, 2], [0, 4], [3, 2], [4, 0]]})
        self.assertEqual(series[0][0], "Points")
        self.assertEqual(len(series[0][1]), 5)


@unittest.skipIf(GUI_IMPORT_ERROR is not None, f"Qt GUI runtime unavailable: {GUI_IMPORT_ERROR}")
class ExplainedWorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_arch_is_explained_and_only_requests_radius(self):
        dialog = OperationDialog(BY_ID["build.planner"], FeatureExecutor(), _Settings(), preferred_mode="Arch")
        self.assertEqual(dialog.mode.name, "Arch")
        self.assertIn("upper half of a hollow block circle", dialog.mode_help.text())
        self.assertIn("2×radius + 1", dialog.mode_help.text())
        self.assertEqual(list(dialog.inputs), ["radius"])
        tooltip = dialog.inputs["radius"].toolTip()
        self.assertIn("build radii determine the generated block geometry", tooltip.lower())
        self.assertNotIn("ignored compatibility", tooltip.lower())
        self.assertNotIn("Value used by this operation", tooltip)
        self.assertIn("block coordinates", dialog.output_help.text().lower())
        self.assertIn("SHAPE LAYOUTS", dialog.path.text())
        dialog.close()

    def test_build_and_shapes_are_grouped_by_catalog_domain(self):
        self.assertEqual(_operation_group(_mode("Area")), "Build Calculators")
        self.assertEqual(_operation_group(_mode("Arch")), "Shape Layouts")
        self.assertNotIn("Configure values below", _operation_description(_mode("Arch")))


if __name__ == "__main__":
    unittest.main()
