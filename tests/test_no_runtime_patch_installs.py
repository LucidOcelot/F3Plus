from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NoRuntimePatchInstallTests(unittest.TestCase):
    def test_production_sources_never_invoke_install_patch_hooks(self):
        calls = []
        for path in sorted((ROOT / "minescript").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                fn = node.func
                if isinstance(fn, ast.Attribute) and fn.attr == "install":
                    calls.append(f"{path.relative_to(ROOT)}:{node.lineno}")
                elif isinstance(fn, ast.Name) and fn.id == "install":
                    calls.append(f"{path.relative_to(ROOT)}:{node.lineno}")
        self.assertEqual(calls, [], "Runtime installer calls must not return: " + ", ".join(calls))

    def test_package_and_launcher_have_no_import_time_patch_stack(self):
        for relative in ("minescript/__init__.py", "main.py"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn(".install()", text, relative)


if __name__ == "__main__":
    unittest.main()
