from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import main


class JavaRuntimeDiscoveryTests(unittest.TestCase):
    def test_windows_launcher_and_store_runtime_roots_are_considered(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            appdata = root / "Roaming"; local = root / "Local"; program = root / "Program Files"; program86 = root / "Program Files x86"
            expected = [
                appdata / ".minecraft" / "runtime",
                local / "Minecraft Launcher" / "runtime",
                program / "Minecraft Launcher" / "runtime",
                program86 / "Minecraft Launcher" / "runtime",
            ]
            for path in expected: path.mkdir(parents=True, exist_ok=True)
            with mock.patch.dict(os.environ, {"APPDATA": str(appdata), "LOCALAPPDATA": str(local), "ProgramFiles": str(program), "ProgramFiles(x86)": str(program86)}, clear=False):
                roots = main._minecraft_runtime_roots()
            for path in expected: self.assertIn(path.resolve(), roots)


if __name__ == "__main__":
    unittest.main()
