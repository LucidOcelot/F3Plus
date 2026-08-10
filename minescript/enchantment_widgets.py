from __future__ import annotations

"""Compact UI for complete enchanted-book possibility sets."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout


_RARITY_ORDER = {"Common": 0, "Uncommon": 1, "Rare": 2, "Very Rare": 3, "Unknown": 4}


class EnchantmentPossibilityPanel(QGroupBox):
    def __init__(self, title: str = "Possible enchanted-book enchantments", parent=None):
        super().__init__(title, parent)
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 8, 10, 8); layout.setSpacing(5)
        self.note = QLabel("Rarity is the vanilla enchantment weight class; exact trade/table odds can differ.")
        self.note.setWordWrap(True); self.note.setObjectName("Muted"); layout.addWidget(self.note)
        self.list = QListWidget(); self.list.setUniformItemSizes(True); self.list.setMinimumHeight(105); self.list.setMaximumHeight(170); layout.addWidget(self.list)
        self.count = QLabel(); self.count.setObjectName("Muted"); layout.addWidget(self.count)

    def set_rows(self, rows):
        ordered = sorted(
            list(rows or []),
            key=lambda row: (_RARITY_ORDER.get(str(row.get("rarity", "Unknown")), 9), str(row.get("name", ""))),
        )
        self.list.clear()
        for row in ordered:
            rarity = str(row.get("rarity", "Unknown")); name = str(row.get("name", row.get("id", "Unknown")))
            max_level = row.get("max_level", 1); weight = row.get("weight", "?")
            level_text = f"max {max_level}" if int(max_level or 1) > 1 else "max 1"
            item = QListWidgetItem(f"{rarity}  •  {name}  •  {level_text}")
            item.setData(Qt.UserRole, row)
            item.setToolTip(f"{name}: {rarity}; vanilla enchantment weight {weight}; maximum level {max_level}.")
            self.list.addItem(item)
        count = len(ordered); self.count.setText(f"{count} possible enchantment{'s' if count != 1 else ''}")
        self.setVisible(bool(ordered))
