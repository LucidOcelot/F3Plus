from __future__ import annotations

import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")

from PySide6.QtWidgets import QApplication

from minescript.catalog_ids import BY_NAME
from minescript.result_view import ResultView, _spatial_series
from minescript.ui_theme import stylesheet


class ResultViewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(stylesheet("chorus"))

    def test_structure_result_produces_spatial_series(self):
        spec = BY_NAME["Village"][0]
        series, _center = _spatial_series(spec, {"candidate_chunks": [[1, 2], [3, 4]]})
        self.assertTrue(series)

    def test_result_view_renders_structured_data_without_plaintext_only_contract(self):
        spec = BY_NAME["Village"][0]
        result = SimpleNamespace(status="ok", note="", data={"candidate_chunks": [[1, 2], [3, 4]], "count": 2, "source": "test"})
        view = ResultView(); view.set_result(spec, result, "chorus", {})
        names = [type(view.layout.itemAt(i).widget()).__name__ for i in range(view.layout.count()) if view.layout.itemAt(i).widget()]
        self.assertIn("InteractiveMap", names)
        self.assertIn("QGroupBox", names)


if __name__ == "__main__":
    unittest.main()
