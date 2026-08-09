from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from minescript.ui_theme import PALETTES, palette
from minescript.version_context import resolve
from minescript.villagers import Trade, trade_direction, trade_key
from minescript.world.versioning import cubiomes_resolution
from updater import auto_update


class V2RegressionTests(unittest.TestCase):
    def test_new_default_themes_are_distinct(self):
        self.assertIn("aether", PALETTES)
        self.assertIn("foundry", PALETTES)
        self.assertNotEqual(palette("aether"), palette("light"))
        self.assertNotEqual(palette("foundry"), palette("cyberpunk"))
        self.assertNotEqual(palette("aether"), palette("foundry"))

    def test_snapshot_worldgen_fallback_is_explicit(self):
        result = cubiomes_resolution("26.3-snapshot-7")
        self.assertTrue(result["fallback"])
        self.assertFalse(result["exact"])
        self.assertEqual(result["calculation_version"], "1.21.3")
        self.assertEqual(result["cubiomes_enum"], 27)
        self.assertIn("not exact", result["reason"].lower())

    def test_version_context_keeps_selected_version(self):
        context = resolve("26.3-snapshot-7")
        self.assertEqual(context.selected, "26.3-snapshot-7")
        self.assertEqual(context.calculation_version, "1.21.3")
        self.assertTrue(context.uses_worldgen_fallback)

    def test_trade_direction_and_identity_use_structured_fields(self):
        buying = Trade("farmer", 1, "wheat emerald", "20 wheat", "1 emerald", wants_id="wheat", gives_id="emerald")
        selling = Trade("librarian", 1, "emerald bookshelf", "9 emerald", "1 bookshelf", wants_id="emerald", gives_id="bookshelf")
        self.assertEqual(trade_direction(buying), "Villager buys from you")
        self.assertEqual(trade_direction(selling), "Villager sells to you")
        self.assertNotEqual(trade_key(buying), trade_key(selling))

    def test_updater_can_be_disabled_without_network(self):
        with patch.dict(os.environ, {"F3PLUS_SKIP_UPDATE": "1"}, clear=False):
            changed, message = auto_update(Path("."))
        self.assertFalse(changed)
        self.assertIn("skipped", message.lower())


if __name__ == "__main__":
    unittest.main()
