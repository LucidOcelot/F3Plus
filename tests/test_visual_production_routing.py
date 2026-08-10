from __future__ import annotations

import inspect
import unittest

from minescript import workbench_forms


class VisualProductionRoutingTests(unittest.TestCase):
    def test_generic_workbench_owns_a_production_result_view(self):
        source = inspect.getsource(workbench_forms.OperationDialog)
        self.assertIn("ResultView", source)
        self.assertIn("set_result", source)
        self.assertNotIn("QTextBrowser", source)


if __name__ == "__main__":
    unittest.main()
