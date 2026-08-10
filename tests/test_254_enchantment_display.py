from __future__ import annotations

import unittest

from minescript.enchantment_catalog import grouped_summary


class EnchantedBookDisplayTests(unittest.TestCase):
    def test_grouped_summary_explains_rarity_and_max_level(self):
        text = grouped_summary([
            {"name": "Mending", "rarity": "Very Rare", "max_level": 1},
            {"name": "Efficiency", "rarity": "Common", "max_level": 5},
            {"name": "Protection", "rarity": "Common", "max_level": 4},
        ])
        self.assertIn("Common: Efficiency (max 5)", text)
        self.assertIn("Protection (max 4)", text)
        self.assertIn("Very Rare: Mending", text)


if __name__ == "__main__":
    unittest.main()
