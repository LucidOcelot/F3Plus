from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")

from PySide6.QtWidgets import QApplication

from minescript.feature_executor import FeatureExecutor
from minescript.tool_registry import BY_ID
from minescript.workbench_forms import OperationDialog


class _Settings:
    minecraft_version = "26.3 Snapshot 7"
    seed = 12345
    theme = "chorus"
    custom_palette = {}


class WorkbenchNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_world_analysis_can_find_ore_distribution_without_scanning_flat_combo(self):
        dialog = OperationDialog(BY_ID["world.analysis"], FeatureExecutor(), _Settings())
        dialog.operation_search.setText("ore distribution")
        names = [dialog.mode_list.item(i).text() for i in range(dialog.mode_list.count())]
        self.assertIn("Ore Distribution", names)
        self.assertLessEqual(sum(1 for name in names if name and not name.isupper()), 2)
        dialog.close()


if __name__ == "__main__":
    unittest.main()
