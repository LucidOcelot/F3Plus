from __future__ import annotations

import inspect
import unittest


class VisualProductionRoutingTests(unittest.TestCase):
    def test_generic_workbench_owns_a_production_result_view(self):
        try:
            from minescript import workbench_forms
        except ImportError as exc:
            if "libEGL" in str(exc): self.skipTest(f"Qt GUI runtime unavailable: {exc}")
            raise
        source = inspect.getsource(workbench_forms.OperationDialog)
        self.assertIn("ResultView", source)
        self.assertIn("set_result", source)
        self.assertNotIn("QTextBrowser", source)


if __name__ == "__main__":
    unittest.main()
