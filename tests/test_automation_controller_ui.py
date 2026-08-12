from __future__ import annotations

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")


class AutomationRoutingSourceTests(unittest.TestCase):
    def test_generic_workbench_routes_automation_to_dedicated_controller(self):
        source = Path("minescript/workbench_forms.py").read_text(encoding="utf-8")
        self.assertIn('if self.tool.workspace == "Automation"', source)
        self.assertIn("AutomationControllerDialog", source)
        self.assertIn("QTreeWidget", source)
        self.assertNotIn("header = QListWidgetItem", source)

    def test_controller_uses_compact_player_categories(self):
        source = Path("minescript/automation_controller.py").read_text(encoding="utf-8")
        for expected in ("Repeated Actions", "Travel", "Mining", "Farming", "Building", "Equipment", "Macros & Setup"):
            self.assertIn(expected, source)
        for old in ("Equipment & Safety", "Hold & Continuous", "Repeat & Interaction", "Ground & Vehicle"):
            self.assertNotIn(old, source)
        self.assertIn("QTreeWidget", source)
        self.assertNotIn("QListWidgetItem", source)


try:
    from PySide6.QtWidgets import QApplication, QWidget
    from minescript.automation_controller import AutomationControllerDialog
    from minescript.feature_executor import FeatureExecutor
    from minescript.tool_registry import BY_ID, ToolMode
    _QT_ERROR = None
except Exception as exc:  # Linux runners may not provide Qt/EGL system libraries.
    QApplication = QWidget = AutomationControllerDialog = FeatureExecutor = BY_ID = ToolMode = None
    _QT_ERROR = str(exc)


@unittest.skipIf(_QT_ERROR is not None, f"Qt GUI unavailable: {_QT_ERROR}")
class AutomationControllerUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _owner(self):
        class Settings:
            safe_mode = False
            minecraft_version = "26.3 Snapshot 7"

        class Status:
            running = False
            paused = False
            name = "Automation"
            cycles = 0
            message = ""

        class Engine:
            status = Status()
            def stop(self, *_args, **_kwargs): pass

        class Capabilities:
            name = "Test Input"

        class Input:
            capabilities = Capabilities()

        class Owner(QWidget):
            def __init__(self):
                super().__init__()
                self.settings = Settings()
                self.target = None
                self.engine = Engine()
                self.input = Input()
                self.executor = FeatureExecutor()
            def start_macro(self, _name): pass
            def start_macro_callable(self, _name, _fn): pass
            def run_mode(self, _mode, _values): pass

        return Owner()

    @staticmethod
    def _groups(dialog):
        return [dialog.list.topLevelItem(i) for i in range(dialog.list.topLevelItemCount())]

    @classmethod
    def _find_mode(cls, dialog, name: str):
        for group in cls._groups(dialog):
            for row in range(group.childCount()):
                item = group.child(row)
                mode = item.data(0, 0x0100)
                if isinstance(mode, ToolMode) and mode.name == name:
                    return item
        return None

    def test_resource_guard_is_in_equipment_and_configurable(self):
        owner = self._owner()
        dialog = AutomationControllerDialog(owner, BY_ID["automation.actions"], owner.executor, owner.settings)
        groups = [item.text(0) for item in self._groups(dialog)]
        self.assertIn("Equipment", groups)
        item = self._find_mode(dialog, "Resource Guard")
        self.assertIsNotNone(item)
        dialog.list.setCurrentItem(item)
        self.assertEqual(dialog.primary.text(), "Configure & Start")
        self.assertIn("fixed number of status cycles", dialog.description.text().lower())
        dialog.close(); owner.close()

    def test_mending_grinder_copy_explains_what_the_routine_does(self):
        owner = self._owner()
        dialog = AutomationControllerDialog(owner, BY_ID["automation.actions"], owner.executor, owner.settings)
        item = self._find_mode(dialog, "Mending Grinder")
        self.assertIsNotNone(item)
        dialog.list.setCurrentItem(item)
        description = dialog.description.text().lower()
        self.assertIn("mending", description)
        self.assertIn("hotbar", description)
        self.assertIn("xp", description)
        self.assertNotIn("review the run behavior", description)
        dialog.close(); owner.close()

    def test_tree_categories_are_collapsible_and_search_expands_matches(self):
        owner = self._owner()
        dialog = AutomationControllerDialog(owner, BY_ID["automation.actions"], owner.executor, owner.settings)
        self.assertGreater(dialog.list.topLevelItemCount(), 0)
        dialog.search.setText("mending")
        self.app.processEvents()
        groups = self._groups(dialog)
        self.assertTrue(groups)
        self.assertTrue(all(group.isExpanded() for group in groups))
        self.assertIsNotNone(self._find_mode(dialog, "Mending Grinder"))
        dialog.close(); owner.close()


if __name__ == "__main__":
    unittest.main()
