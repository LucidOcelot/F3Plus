from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from minescript.catalog_ids import SPECS as LEGACY_SPECS
from minescript.feature_executor import FeatureExecutor
from minescript.field_semantics import field_help
from minescript.launch_contract import DEDICATED_LAUNCHERS, has_launch_owner, launch_kind
from minescript.minecraft_art import _TEXTURES
from minescript.minecraft_art25 import FUZZY_TERMS
from minescript.tool_guides import make_guide, tool_art_key
from minescript.tool_registry import LEGACY_TO_CANONICAL, TOOLS, modes_for
from minescript.ui_theme import PALETTES
from minescript.version import VERSION


class FullRelease254Audit(unittest.TestCase):
    def test_release_identity(self):
        self.assertEqual(VERSION, "2.5.4")
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("from minescript.app25 import run", main)
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('version = "2.5.4"', pyproject)

    def test_all_457_historical_ids_still_resolve(self):
        self.assertEqual(len(LEGACY_SPECS), 457)
        self.assertEqual(len(LEGACY_TO_CANONICAL), len(LEGACY_SPECS))
        self.assertEqual(set(LEGACY_TO_CANONICAL), {spec.id for spec in LEGACY_SPECS})

    def test_every_visible_workbench_has_one_launch_owner(self):
        missing = [tool.id for tool in TOOLS if not has_launch_owner(tool)]
        self.assertFalse(missing, missing)
        for tool in TOOLS:
            kind = launch_kind(tool.id)
            if not modes_for(tool): self.assertIn(tool.id, DEDICATED_LAUNCHERS)
            self.assertTrue(kind == "operation_explorer" or tool.id in DEDICATED_LAUNCHERS)

    def test_special_workbenches_cannot_fall_into_empty_generic_dialogs(self):
        required = {
            "automation.macro_studio", "world.profiles", "build.recipes",
            "simulation.rng", "simulation.loot", "simulation.mechanics",
            "villagers.explorer", "utilities.settings", "utilities.safety",
            "utilities.results", "utilities.diagnostics",
        }
        self.assertTrue(required.issubset(DEDICATED_LAUNCHERS))

    def test_every_public_input_has_nontrivial_help(self):
        executor = FeatureExecutor(); failures = []
        banned = ("value used by this operation", "configure and run", "operation-specific input. its meaning is defined")
        for spec in LEGACY_SPECS:
            try: fields = executor.input_fields(spec)
            except Exception as exc:
                failures.append((spec.id, "schema error", str(exc))); continue
            for key, label, default, kind in fields:
                text = field_help(str(key), str(label)).strip(); low = text.lower()
                if len(text) < 45 or any(token in low for token in banned): failures.append((spec.id, str(label), text))
        self.assertFalse(failures[:30], failures[:30])

    def test_workbench_guides_are_user_facing_not_catalog_metadata(self):
        failures = []
        for tool in TOOLS:
            guide = make_guide(tool); combined = " ".join((guide.summary, guide.when, guide.inputs, guide.output, guide.limitations)).lower()
            if len(guide.summary) < 30: failures.append((tool.id, "short summary"))
            if "implementation" in combined or "dispatch" in combined or "feature id" in combined: failures.append((tool.id, "internal wording"))
            if "choose an operation" not in guide.inputs.lower() and launch_kind(tool.id) == "operation_explorer": failures.append((tool.id, "missing operation guidance"))
        self.assertFalse(failures, failures)

    def test_every_workbench_art_identity_has_minecraft_recovery_contract(self):
        missing = {}; keys = []
        for tool in TOOLS:
            key = tool_art_key(tool); keys.append(key)
            if key not in _TEXTURES and key not in FUZZY_TERMS: missing[tool.id] = key
        self.assertFalse(missing, missing)
        self.assertGreaterEqual(len(set(keys)), 24)

    def test_current_five_themes_remain_available(self):
        self.assertEqual(set(PALETTES), {"chorus", "light", "cyberpunk", "minecraft", "custom"})
        source = (ROOT / "minescript" / "app.py").read_text(encoding="utf-8")
        for label in ("Chorus", "Light", "Cyber", "Vanilla", "Custom"): self.assertIn(f'"{label}"', source)

    def test_new_shell_uses_professional_information_hierarchy(self):
        source = (ROOT / "minescript" / "app25.py").read_text(encoding="utf-8")
        for required in (
            'setObjectName("TopBar")', 'setObjectName("StatusBar25")',
            'setObjectName("NavRail25")', 'setObjectName("WorkbenchCanvas")',
            'setObjectName("Inspector25")', 'class WorkbenchCardDelegate',
            'class CommandPalette25', 'def launch_tool(',
        ):
            self.assertIn(required, source)
        self.assertNotIn("QInputDialog.getItem", source)
        self.assertNotIn("from PySide6.QtWidgets import QInputDialog", source)

    def test_contextual_operation_dialog_is_concise_but_keeps_tooltips(self):
        source = (ROOT / "minescript" / "operation_dialog25.py").read_text(encoding="utf-8")
        self.assertIn("setToolTip", source)
        self.assertIn("setAccessibleDescription", source)
        self.assertIn('"Ore Distribution"', source)
        self.assertIn('"Data source"', source)
        self.assertIn('"Seed", "World save"', source)
        self.assertNotIn("active calculation input", source)
        self.assertNotIn("EXPECTED OUTPUT", source)

    def test_no_new_runtime_monkeypatch_layer(self):
        for relative in ("minescript/app25.py", "minescript/operation_dialog25.py", "minescript/minecraft_art25.py", "minescript/launch_contract.py"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn(".install()", source, relative)
            self.assertNotIn("setattr(", source, relative)
            self.assertNotIn("__class__", source, relative)


if __name__ == "__main__":
    unittest.main()
