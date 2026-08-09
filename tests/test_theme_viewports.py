from __future__ import annotations

import unittest

from minescript.ui_theme import PALETTES, stylesheet


class NativeItemViewThemeTests(unittest.TestCase):
    def test_supported_themes_style_item_views_and_viewports(self):
        self.assertEqual(set(PALETTES), {"chorus", "light", "cyberpunk", "minecraft", "custom"})
        for theme in PALETTES:
            css = stylesheet(theme)
            self.assertIn("QAbstractScrollArea QWidget#qt_scrollarea_viewport", css)
            self.assertIn("QListView, QTreeView, QTableView, QListWidget, QTableWidget", css)
            self.assertIn("QListView::item:selected", css)
            self.assertIn("QListWidget#NavList", css)
            self.assertIn("QListWidget#ToolList", css)

    def test_named_navigation_and_tool_lists_are_not_transparent(self):
        for theme in PALETTES:
            css = stylesheet(theme)
            block = css.split("QListWidget#NavList", 1)[1].split("}", 1)[0]
            self.assertNotIn("background: transparent", block)


if __name__ == "__main__":
    unittest.main()
