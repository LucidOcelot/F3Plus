from __future__ import annotations

import re

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from .minecraft_simulators import MinecraftJarData
from .villagers import LEVEL_NAMES, PROFESSIONS, load_for_version, search as trade_search


def _item_token(text: str) -> str:
    value = str(text or "").lower().strip().removeprefix("minecraft:")
    value = re.sub(r"^\d+\s*[x×]?\s*", "", value)
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


class VillagerExplorerDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.trades, self.source = load_for_version(owner.settings.minecraft_version)
        self.jar = MinecraftJarData(owner.settings.minecraft_version)
        self.setWindowTitle("Villager Explorer"); self.resize(1240, 820)
        root = QVBoxLayout(self)
        hero = QHBoxLayout(); self.portrait = QLabel(); self.portrait.setFixedSize(92, 92); self.portrait.setAlignment(Qt.AlignCenter); hero.addWidget(self.portrait)
        titles = QVBoxLayout(); title = QLabel("Villager Explorer"); title.setObjectName("WorkspaceTitle"); titles.addWidget(title); source = QLabel(f"{len(self.trades)} trades • {self.source}"); source.setObjectName("Muted"); titles.addWidget(source); hero.addLayout(titles, 1); root.addLayout(hero)
        filters = QHBoxLayout(); self.prof = QComboBox(); self.prof.addItem("All professions"); self.prof.addItems([value.title() for value in PROFESSIONS]); self.level = QComboBox(); self.level.addItem("All levels"); self.level.addItems([f"{i} — {LEVEL_NAMES[i]}" for i in range(1, 6)]); self.query = QLineEdit(); self.query.setPlaceholderText("Search item or trade…"); filters.addWidget(self.prof); filters.addWidget(self.level); filters.addWidget(self.query, 1); root.addLayout(filters)
        self.table = QTableWidget(0, 8); self.table.setHorizontalHeaderLabels(["Profession", "Level", "Trade", "Wants", "Additional", "Gives", "Max uses", "XP"]); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents); self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch); self.table.setIconSize(QSize(28, 28)); root.addWidget(self.table, 1)
        self.prof.currentTextChanged.connect(self.refresh); self.level.currentTextChanged.connect(self.refresh); self.query.textChanged.connect(self.refresh); self.refresh()

    def _portrait_pixmap(self, profession: str) -> QPixmap:
        size = 84; layers = ["assets/minecraft/textures/entity/villager/villager.png", "assets/minecraft/textures/entity/villager/type/plains.png"]
        if profession: layers.append(f"assets/minecraft/textures/entity/villager/profession/{profession}.png")
        canvas = QPixmap(size, size); canvas.fill(Qt.transparent); painter = QPainter(canvas); loaded = False
        for member in layers:
            raw = self.jar.read_bytes(member); pix = QPixmap()
            if raw and pix.loadFromData(raw): loaded = True; painter.drawPixmap(0, 0, pix.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation))
        painter.end(); return canvas if loaded else QPixmap()

    def _item_icon(self, text: str) -> QIcon:
        token = _item_token(text)
        raw, _ = self.jar.texture_bytes((f"assets/minecraft/textures/item/{token}.png", f"assets/minecraft/textures/block/{token}.png")); pix = QPixmap()
        return QIcon(pix) if raw and pix.loadFromData(raw) else QIcon()

    def refresh(self):
        profession = None if self.prof.currentText().startswith("All") else self.prof.currentText().lower(); level = None if self.level.currentText().startswith("All") else int(self.level.currentText()[0]); rows = trade_search(self.trades, self.query.text(), profession, level); self.portrait.setPixmap(self._portrait_pixmap(profession or "")); self.table.setRowCount(len(rows))
        for r, trade in enumerate(rows):
            values = [trade.profession.title(), f"{trade.level} — {LEVEL_NAMES.get(trade.level, trade.level)}", trade.name, trade.wants, trade.additional_wants or "", trade.gives, "" if trade.max_uses is None else str(trade.max_uses), "" if trade.xp is None else str(trade.xp)]
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                if c in (3, 4, 5): item.setIcon(self._item_icon(value))
                self.table.setItem(r, c, item)
