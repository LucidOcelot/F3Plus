from __future__ import annotations

import unittest

from minescript.catalog_ids import SPECS
from minescript.feature_executor import FeatureExecutor
from minescript.field_semantics import field_help
from minescript.tool_guides import NAV_SECTIONS, make_guide, nav_section, specs_for_section, workspace_group
from minescript.tool_registry import TOOLS, modes_for


class TaskFirstProductAudit(unittest.TestCase):
    def test_navigation_is_task_first_and_compact(self):
        self.assertEqual(
            [label for label, _ in NAV_SECTIONS],
            ["Home", "Play & Travel", "Explore Worlds", "Plan & Build", "Mechanics & Trading", "App & Safety"],
        )

    def test_every_workbench_is_visible_in_one_task_section(self):
        visible = []
        for section, _ in NAV_SECTIONS:
            if section == "Home":
                continue
            rows = specs_for_section(section)
            self.assertTrue(rows, section)
            visible.extend(tool.id for tool in rows)
        self.assertEqual(set(visible), {tool.id for tool in TOOLS})
        self.assertEqual(len(visible), len(set(visible)))

    def test_groups_use_player_language(self):
        banned = {"Gameplay", "Seed Tools", "Calculators", "RNG Tools", "Utilities & Safety"}
        for tool in TOOLS:
            self.assertNotIn(nav_section(tool), banned)
            self.assertNotIn(workspace_group(tool), banned)

    def test_workbench_discovery_text_is_concise(self):
        banned = (
            "use this when",
            "what you provide",
            "what you get",
            "historical",
            "compatibility",
            "does not claim",
            "never presented",
            "confidence level",
        )
        for tool in TOOLS:
            guide = make_guide(tool)
            combined = " ".join((guide.summary, guide.when, guide.how, guide.inputs, guide.output, guide.limitations)).lower()
            for phrase in banned:
                self.assertNotIn(phrase, combined, (tool.id, phrase, combined))

    def test_every_operation_still_has_an_execution_spec(self):
        executor = FeatureExecutor()
        failures = []
        for spec in SPECS:
            try:
                executor.input_fields(spec)
            except Exception as exc:
                failures.append((spec.id, str(exc)))
        self.assertFalse(failures[:20], failures[:20])

    def test_public_inputs_have_tooltip_text(self):
        executor = FeatureExecutor()
        failures = []
        for spec in SPECS:
            for key, label, default, kind in executor.input_fields(spec):
                text = field_help(str(key), str(label)).strip()
                low = text.lower()
                if len(text) < 28:
                    failures.append((spec.id, label, text))
                if "compatibility" in low or "contextual description" in low or "unused internal" in low:
                    failures.append((spec.id, label, text))
        self.assertFalse(failures[:30], failures[:30])

    def test_all_workbench_operations_remain_reachable(self):
        mode_count = sum(len(modes_for(tool)) for tool in TOOLS)
        self.assertGreaterEqual(mode_count, len(SPECS))


if __name__ == "__main__":
    unittest.main()
