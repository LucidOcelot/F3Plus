from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")
os.environ.setdefault("F3PLUS_SKIP_UPDATE", "1")

try:
    from PySide6.QtWidgets import QApplication
    from minescript.app import F3Plus
    from minescript.tool_registry import TOOLS
    from minescript.workbenches import ResultMapDialog, extract_coordinate_layers
    GUI_IMPORT_ERROR = None
except ImportError as exc:
    GUI_IMPORT_ERROR = exc
    QApplication = F3Plus = ResultMapDialog = None
    from minescript.tool_registry import TOOLS


@unittest.skipIf(GUI_IMPORT_ERROR is not None, f"runner does not provide Qt GUI system libraries: {GUI_IMPORT_ERROR}")
class CanonicalUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_constructs_without_patch_installers(self):
        window = F3Plus()
        self.assertEqual(window.nav.count(), 8)
        self.assertLess(len(TOOLS), 50)
        self.assertGreater(window.tool_list.count(), 0)
        self.assertTrue(window.run_btn.text())
        window.close(); window.deleteLater(); self.app.processEvents()

    def test_coordinate_results_open_interactive_map(self):
        data = {"candidate_chunks": [[1, 2], [4, -3]], "nearest": {"x": 160, "z": -80}}
        layers = extract_coordinate_layers(data)
        self.assertTrue(layers)
        dialog = ResultMapDialog(data)
        self.assertGreater(dialog.layer_list.count(), 0)
        dialog.close(); dialog.deleteLater(); self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
