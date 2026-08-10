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
        self.assertIn('Search {tool.name.lower()} operations', source)
        self.assertNotIn('Find an operation, e.g. ore distribution', source)

    def test_controller_does_not_contain_generic_analysis_taxonomy(self):
        source = Path("minescript/automation_controller.py").read_text(encoding="utf-8")
        self.assertNotIn("Analysis & Distribution", source)
        self.assertIn("Equipment & Safety", source)
        self.assertIn("Hold & Continuous", source)
        self.assertIn("Repeat & Interaction", source)
        self.assertIn("Coordinate Travel", source)


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

    def test_resource_guard_is_equipment_not_analysis_and_is_configurable(self):
        owner = self._owner()
        dialog = AutomationControllerDialog(owner, BY_ID["automation.actions"], owner.executor, owner.settings)
        labels = [dialog.list.item(i).text() for i in range(dialog.list.count())]
        self.assertIn("EQUIPMENT & SAFETY", labels)
        self.assertNotIn("ANALYSIS & DISTRIBUTION", labels)
        resource_row = labels.index("Resource Guard")
        dialog.list.setCurrentRow(resource_row)
        self.assertEqual(dialog.primary.text(), "Configure & Start")
        self.assertIn("cannot read live inventory counts", dialog.description.text().lower())
        self.assertNotIn("ore distribution", dialog.search.placeholderText().lower())
        dialog.close(); owner.close()

    def test_automation_actions_keep_real_gameplay_categories(self):
        owner = self._owner()
        dialog = AutomationControllerDialog(owner, BY_ID["automation.actions"], owner.executor, owner.settings)
        labels = [dialog.list.item(i).text() for i in range(dialog.list.count())]
        for expected in ("HOLD & CONTINUOUS", "REPEAT & INTERACTION", "FISHING", "EQUIPMENT & SAFETY"):
            self.assertIn(expected, labels)
        dialog.close(); owner.close()


if __name__ == "__main__":
    unittest.main()
