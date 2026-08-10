from __future__ import annotations

"""Reusable Minecraft-oriented controls for simulator/explorer UIs.

These controls intentionally hide registry/NBT/JSON representation details.  Users pick
items, enchantments, levels, and colors; engines still receive the compact dictionaries
they already understand.
"""

from functools import lru_cache

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from .minecraft_simulators import MinecraftJarData


class AssetProvider:
    def __init__(self, data: MinecraftJarData):
        self.data = data
        self._icon_cache: dict[tuple[str, int], QIcon] = {}
        self._items: list[str] | None = None

    def item_ids(self) -> list[str]:
        if self._items is not None:
            return self._items
        rows = set()
        try:
            members = self.data._members()
        except Exception:
            members = ()
        prefix = "assets/minecraft/textures/item/"
        for member in members:
            if member.startswith(prefix) and member.endswith(".png"):
                token = member[len(prefix):-4]
                # Exclude animation frames/legacy clock-compass frames from the chooser.
                if "/" not in token and not token.rsplit("_", 1)[-1].isdigit():
                    rows.add("minecraft:" + token)
        self._items = sorted(rows) or [
            "minecraft:book", "minecraft:enchanted_book", "minecraft:diamond_pickaxe",
            "minecraft:diamond_sword", "minecraft:diamond_axe", "minecraft:diamond_shovel",
            "minecraft:diamond_helmet", "minecraft:diamond_chestplate", "minecraft:diamond_leggings",
            "minecraft:diamond_boots", "minecraft:bow", "minecraft:crossbow", "minecraft:trident",
            "minecraft:fishing_rod", "minecraft:elytra",
        ]
        return self._items

    def icon(self, item_id: str, size: int = 32) -> QIcon:
        key = (str(item_id), int(size))
        if key in self._icon_cache:
            return self._icon_cache[key]
        token = str(item_id).removeprefix("minecraft:")
        raw, _ = self.data.texture_bytes((
            f"assets/minecraft/textures/item/{token}.png",
            f"assets/minecraft/textures/block/{token}.png",
        ))
        pix = QPixmap()
        if raw and pix.loadFromData(raw):
            pix = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation)
        icon = QIcon(pix) if not pix.isNull() else QIcon()
        self._icon_cache[key] = icon
        return icon


class ItemPicker(QFrame):
    """Minecraft item chooser with a single selected-item slot preview."""

    def __init__(self, assets: AssetProvider, default: str = "minecraft:book", parent=None):
        super().__init__(parent)
        self.assets = assets; self.setObjectName("TradeStack")
        row = QHBoxLayout(self); row.setContentsMargins(8, 7, 8, 7); row.setSpacing(8)
        self.slot = QLabel(); self.slot.setFixedSize(42, 42); self.slot.setAlignment(Qt.AlignCenter); row.addWidget(self.slot)
        self.combo = QComboBox(); self.combo.setEditable(True); self.combo.setInsertPolicy(QComboBox.NoInsert)
        self.combo.addItems(self.assets.item_ids()); row.addWidget(self.combo, 1)
        self.combo.currentTextChanged.connect(self._sync)
        self.set_value(default)

    def set_value(self, item_id: str):
        text = str(item_id or "minecraft:book")
        index = self.combo.findText(text)
        if index < 0:
            self.combo.addItem(text); index = self.combo.findText(text)
        self.combo.setCurrentIndex(index); self._sync(text)

    def value(self) -> str:
        text = self.combo.currentText().strip()
        return text if ":" in text else "minecraft:" + text

    def _sync(self, text: str):
        icon = self.assets.icon(text, 36); self.slot.setPixmap(icon.pixmap(QSize(36, 36)))


class EnchantmentEditor(QFrame):
    """Add/remove enchantments without exposing JSON dictionaries."""

    def __init__(self, enchantments: dict[str, dict], parent=None):
        super().__init__(parent); self.enchantments = enchantments; self.setObjectName("ToolConfigCard")
        root = QVBoxLayout(self); root.setContentsMargins(8, 7, 8, 7); root.setSpacing(6)
        row = QHBoxLayout(); self.choice = QComboBox(); self.choice.addItems(sorted(enchantments)); self.level = QSpinBox(); self.level.setRange(1, 255); add = QPushButton("Add enchantment")
        row.addWidget(self.choice, 1); row.addWidget(QLabel("Level")); row.addWidget(self.level); row.addWidget(add); root.addLayout(row)
        self.list = QListWidget(); self.list.setMaximumHeight(150); root.addWidget(self.list)
        remove = QPushButton("Remove selected"); root.addWidget(remove)
        add.clicked.connect(self._add); remove.clicked.connect(self._remove)

    def _max_level(self, enchant_id: str) -> int:
        definition = self.enchantments.get(enchant_id, {})
        try:
            return max(1, int(definition.get("max_level", 5)))
        except Exception:
            return 5

    def _add(self):
        enchant_id = self.choice.currentText(); level = min(self.level.value(), self._max_level(enchant_id))
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item.data(Qt.UserRole) == enchant_id:
                item.setData(Qt.UserRole + 1, level); item.setText(f"{enchant_id.removeprefix('minecraft:').replace('_', ' ').title()} {level}"); return
        item = QListWidgetItem(f"{enchant_id.removeprefix('minecraft:').replace('_', ' ').title()} {level}")
        item.setData(Qt.UserRole, enchant_id); item.setData(Qt.UserRole + 1, level); self.list.addItem(item)

    def _remove(self):
        for item in self.list.selectedItems(): self.list.takeItem(self.list.row(item))

    def set_values(self, values: dict[str, int]):
        self.list.clear()
        for enchant_id, level in values.items():
            item = QListWidgetItem(f"{str(enchant_id).removeprefix('minecraft:').replace('_', ' ').title()} {int(level)}")
            item.setData(Qt.UserRole, str(enchant_id)); item.setData(Qt.UserRole + 1, int(level)); self.list.addItem(item)

    def values(self) -> dict[str, int]:
        return {str(self.list.item(i).data(Qt.UserRole)): int(self.list.item(i).data(Qt.UserRole + 1)) for i in range(self.list.count())}


class MetricCard(QFrame):
    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent); self.setObjectName("ResultMetric")
        box = QVBoxLayout(self); box.setContentsMargins(10, 8, 10, 8)
        self.value = QLabel(str(value)); self.value.setObjectName("MetricValue"); self.value.setAlignment(Qt.AlignCenter); box.addWidget(self.value)
        name = QLabel(label); name.setObjectName("MetricLabel"); name.setAlignment(Qt.AlignCenter); box.addWidget(name)

    def set_value(self, value): self.value.setText(str(value))


class ExplanationCard(QFrame):
    def __init__(self, title: str, text: str = "", parent=None):
        super().__init__(parent); self.setObjectName("ResultSection")
        box = QVBoxLayout(self); box.setContentsMargins(10, 8, 10, 8)
        heading = QLabel(title.upper()); heading.setObjectName("DeckLabel"); box.addWidget(heading)
        self.text = QLabel(text); self.text.setWordWrap(True); self.text.setObjectName("Muted"); box.addWidget(self.text)

    def set_text(self, text): self.text.setText(str(text))
