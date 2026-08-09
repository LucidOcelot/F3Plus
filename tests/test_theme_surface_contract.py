from __future__ import annotations

import unittest

from minescript.ui_theme import PALETTES, palette, stylesheet


class ThemeSurfaceContractTests(unittest.TestCase):
    def test_only_supported_user_theme_palettes_remain(self):
        self.assertEqual(set(PALETTES), {"chorus", "light", "cyberpunk", "minecraft", "custom"})

    def test_every_theme_explicitly_styles_native_container_surfaces(self):
        for theme in PALETTES:
            with self.subTest(theme=theme):
                p = palette(theme)
                css = stylesheet(theme)
                self.assertIn(f"QMainWindow, QDialog {{ background: {p['bg']}; color: {p['text']}; }}", css)
                self.assertIn(f"QTabWidget::pane {{ background: {p['surface']};", css)
                self.assertIn(f"QAbstractItemView {{ background: {p['surface']}; color: {p['text']};", css)
                self.assertIn(f"QListWidget {{ background: {p['surface']}; color: {p['text']};", css)
                self.assertIn(f"QScrollArea {{ background: {p['surface']};", css)
                self.assertIn(f"QScrollArea QWidget#qt_scrollarea_viewport {{ background: {p['surface']}; }}", css)

    def test_dark_themes_never_pair_dark_text_with_native_light_surfaces(self):
        for theme in ("chorus", "cyberpunk", "minecraft", "custom"):
            with self.subTest(theme=theme):
                p = palette(theme)
                css = stylesheet(theme)
                # The key regression was themed foreground text on an unthemed/native-white
                # tab/list/scroll surface. All of those surfaces now use the same palette.
                self.assertIn(p["text"], css)
                self.assertIn(p["surface"], css)
                self.assertNotIn("background: white", css.lower())
                self.assertNotIn("background-color: white", css.lower())


if __name__ == "__main__":
    unittest.main()
