from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")


class RestoredModuleSmokeTests(unittest.TestCase):
    def test_restored_modules_import(self):
        import minescript.result_view
        import minescript.loot_workbench
        import minescript.villager_reference
        import minescript.operation_fields


if __name__ == "__main__":
    unittest.main()
