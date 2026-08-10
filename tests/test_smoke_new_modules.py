from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")


class RestoredModuleSmokeTests(unittest.TestCase):
    def test_non_gui_restored_modules_import(self):
        import minescript.villager_reference
        import minescript.operation_fields
        import minescript.minecraft_simulators

    def test_gui_restored_modules_import_when_qt_runtime_is_available(self):
        try:
            import minescript.result_view
            import minescript.loot_workbench
        except ImportError as exc:
            if "libEGL" in str(exc): self.skipTest(f"Qt GUI runtime unavailable: {exc}")
            raise


if __name__ == "__main__":
    unittest.main()
