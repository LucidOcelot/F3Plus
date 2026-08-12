from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")

GUI_IMPORT_ERROR = None
try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from minescript.workbenches import OperationDialog
except ImportError as exc:
    GUI_IMPORT_ERROR = exc
    QApplication = OperationDialog = None

from minescript.feature_executor import FeatureExecutor
from minescript.tool_registry import BY_ID


class _Settings:
    minecraft_version = "26.3 Snapshot 7"
    seed = 12345
    theme = "chorus"
    custom_palette = {}


def _visible_operation_names(tree):
    names = []
    for group_row in range(tree.topLevelItemCount()):
        group = tree.topLevelItem(group_row)
        for child_row in range(group.childCount()):
            item = group.child(child_row)
            if item.data(0, Qt.UserRole) is not None:
                names.append(item.text(0))
    return names


@unittest.skipIf(GUI_IMPORT_ERROR is not None, f"Qt GUI runtime unavailable: {GUI_IMPORT_ERROR}")
class WorkbenchNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ore_explorer_can_find_ore_distribution_without_scanning_unrelated_analysis(self):
        dialog = OperationDialog(BY_ID["world.ores"], FeatureExecutor(), _Settings())
        dialog.operation_search.setText("ore distribution")
        self.app.processEvents()
        names = _visible_operation_names(dialog.mode_list)
        self.assertEqual(names, ["Ore Distribution"])
        self.assertEqual(dialog.mode_list.topLevelItemCount(), 1)
        self.assertTrue(dialog.mode_list.topLevelItem(0).isExpanded())
        self.assertIn("ORE", dialog.windowTitle().upper())
        dialog.close()


if __name__ == "__main__":
    unittest.main()
