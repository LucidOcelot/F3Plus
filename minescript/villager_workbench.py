from __future__ import annotations

import math
import re

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QSpinBox, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget,
)

from .catalog_ids import BY_NAME
from .minecraft_simulators import MinecraftJarData
from .tool_registry import canonical_for_legacy
from .ui_dialogs import ParameterDialog
from .villagers import LEVEL_NAMES, PROFESSIONS, load_for_version, search as trade_search, trade_direction, trade_key


def _item_token(text: str) -> str:
    value = str(text or "").lower().strip().removeprefix("minecraft:")
    value = re.sub(r"^\d+(?:\.\d+)?\s*[x×]?\s*", "", value)
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def _number(text: str, default=1.0):
    match = re.search(r"-?\d+(?:\.\d+)?", str(text or ""))
    return float(match.group()) if match else float(default)


class VillagerExplorerDialog(QDialog):
    def __init__(self, owner, profession: str | None = None, mode: str = "Trade Browser"):
        super().__init__(owner)
        self.owner = owner; self.mode = mode
        self.trades, self.source = load_for_version(owner.settings.minecraft_version)
        self.jar = MinecraftJarData(owner.settings.minecraft_version)
        self.compare_keys: list[str] = []
        self.rows = []
        self.setWindowTitle("Villager Explorer"); self.resize(1320, 840); self.setMinimumSize(1040, 680)
        root = QVBoxLayout(self)
        hero = QHBoxLayout(); self.portrait = QLabel(); self.portrait.setFixedSize(92, 92); self.portrait.setAlignment(Qt.AlignCenter); hero.addWidget(self.portrait)
        titles = QVBoxLayout(); title = QLabel("Villager Explorer"); title.setObjectName("WorkspaceTitle"); titles.addWidget(title); self.source_label = QLabel(); self.source_label.setObjectName("Muted"); titles.addWidget(self.source_label); hero.addLayout(titles, 1)
        refresh = QPushButton("Refresh installed trade data"); refresh.clicked.connect(self.reload); hero.addWidget(refresh); root.addLayout(hero)

        tabs = QTabWidget(); root.addWidget(tabs, 1)
        browser = QWidget(); bv = QVBoxLayout(browser)
        filters = QHBoxLayout(); self.prof = QComboBox(); self.prof.addItem("All professions"); self.prof.addItems([value.title() for value in PROFESSIONS]); self.level = QComboBox(); self.level.addItem("All levels"); self.level.addItems([f"{i} — {LEVEL_NAMES[i]}" for i in range(1, 6)]); self.direction = QComboBox(); self.direction.addItems(["All directions", "Villager sells to you", "Villager buys from you", "Exchange"]); self.query = QLineEdit(); self.query.setPlaceholderText("Search item, enchantment detail, profession or trade…"); self.query.setClearButtonEnabled(True); self.uses = QSpinBox(); self.uses.setRange(1, 9999); self.uses.setValue(64 if mode == "Trade Cycle Calculator" else 12); self.uses.setPrefix("Plan "); self.uses.setSuffix(" uses"); self.favorites_only = QCheckBox("Favorites only")
        for widget in (self.prof, self.level, self.direction): filters.addWidget(widget)
        filters.addWidget(self.query, 2); filters.addWidget(self.uses); filters.addWidget(self.favorites_only); bv.addLayout(filters)

        split = QSplitter(Qt.Horizontal); bv.addWidget(split, 1)
        self.table = QTableWidget(0, 8); self.table.setHorizontalHeaderLabels(["Profession", "Level", "Trade", "Wants", "Additional", "Gives", "Max uses", "XP"]); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents); self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setSelectionMode(QAbstractItemView.SingleSelection); self.table.setIconSize(QSize(30, 30)); split.addWidget(self.table)
        detail_host = QWidget(); dv = QVBoxLayout(detail_host); detail_title = QLabel("TRADE DETAILS"); detail_title.setObjectName("DeckLabel"); dv.addWidget(detail_title); self.detail = QTextBrowser(); dv.addWidget(self.detail, 1); actions = QHBoxLayout(); self.favorite = QPushButton("☆ Favorite"); self.favorite.clicked.connect(self.toggle_favorite); self.compare = QPushButton("Add to compare"); self.compare.clicked.connect(self.toggle_compare); actions.addWidget(self.favorite); actions.addWidget(self.compare); dv.addLayout(actions); compare_label = QLabel("COMPARE"); compare_label.setObjectName("DeckLabel"); dv.addWidget(compare_label); self.compare_list = QListWidget(); self.compare_list.setMaximumHeight(210); dv.addWidget(self.compare_list); clear = QPushButton("Clear comparison"); clear.clicked.connect(self.clear_compare); dv.addWidget(clear); split.addWidget(detail_host); split.setSizes([900, 380]); tabs.addTab(browser, "Trade Explorer")

        planning = QWidget(); pv = QVBoxLayout(planning); help_text = QLabel("Villager helper operations use the same canonical executor as the rest of F3+. They are grouped here so curing, halls, workstations and breeding food are available without leaving the explorer."); help_text.setWordWrap(True); help_text.setObjectName("Muted"); pv.addWidget(help_text)
        for name in ("Zombie Cure Calculator", "Villager Hall Calculator", "Workstation Count", "Breeding Food Calculator"):
            button = QPushButton(name); button.clicked.connect(lambda _=False, n=name: self.run_helper(n)); pv.addWidget(button)
        pv.addStretch(); tabs.addTab(planning, "Planning Helpers")

        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close)
        self.prof.currentTextChanged.connect(self.refresh); self.level.currentTextChanged.connect(self.refresh); self.direction.currentTextChanged.connect(self.refresh); self.query.textChanged.connect(self.refresh); self.favorites_only.toggled.connect(self.refresh); self.uses.valueChanged.connect(self.show_selected); self.table.itemSelectionChanged.connect(self.show_selected)
        target = "librarian" if mode == "Librarian Browser" else (profession or "").lower()
        if target in PROFESSIONS: self.prof.setCurrentText(target.title())
        if mode in {"Trade Search", "Trade Comparison", "Emerald Calculator", "Trade Cycle Calculator", "Librarian Browser"}: self.query.setFocus()
        self.refresh()

    def _portrait_pixmap(self, profession: str) -> QPixmap:
        size = 84; layers = ["assets/minecraft/textures/entity/villager/villager.png", "assets/minecraft/textures/entity/villager/type/plains.png"]
        if profession: layers.append(f"assets/minecraft/textures/entity/villager/profession/{profession}.png")
        canvas = QPixmap(64, 84); canvas.fill(Qt.transparent); painter = QPainter(canvas); loaded = False
        for member in layers:
            raw = self.jar.read_bytes(member); sheet = QPixmap()
            if not raw or not sheet.loadFromData(raw): continue
            loaded = True
            # Conventional Java villager skin UVs: face, hat/profession overlay and torso.
            painter.drawPixmap(QRect(12, 2, 40, 40), sheet, QRect(8, 8, 8, 8))
            painter.drawPixmap(QRect(10, 0, 44, 44), sheet, QRect(40, 8, 8, 8))
            painter.drawPixmap(QRect(16, 40, 32, 42), sheet, QRect(20, 20, 8, 12))
        painter.end(); return canvas.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation) if loaded else QPixmap()

    def _item_icon(self, text: str) -> QIcon:
        token = _item_token(text)
        raw, _ = self.jar.texture_bytes((f"assets/minecraft/textures/item/{token}.png", f"assets/minecraft/textures/block/{token}.png")); pix = QPixmap()
        return QIcon(pix) if raw and pix.loadFromData(raw) else QIcon()

    def reload(self):
        self.trades, self.source = load_for_version(self.owner.settings.minecraft_version); self.refresh()

    def refresh(self):
        profession = None if self.prof.currentText().startswith("All") else self.prof.currentText().lower(); level = None if self.level.currentText().startswith("All") else int(self.level.currentText()[0]); rows = trade_search(self.trades, self.query.text(), profession, level)
        direction = self.direction.currentText()
        if direction != "All directions": rows = [trade for trade in rows if trade_direction(trade) == direction]
        if self.favorites_only.isChecked(): rows = [trade for trade in rows if trade_key(trade) in self.owner.settings.favorite_trades]
        self.rows = rows; self.portrait.setPixmap(self._portrait_pixmap(profession or "")); exact = str(self.source).lower() == str(self.owner.settings.minecraft_version).lower(); self.source_label.setText(f"{len(self.trades)} definitions • Trade data: {self.source}" + ("" if exact else " • fallback/reference source")); self.table.setRowCount(len(rows))
        for r, trade in enumerate(rows):
            values = [trade.profession.title(), f"{trade.level} — {LEVEL_NAMES.get(trade.level, trade.level)}", trade.name, trade.wants, trade.additional_wants or "", trade.gives, "" if trade.max_uses is None else str(trade.max_uses), "" if trade.xp is None else str(trade.xp)]
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                if c in (3, 4, 5): item.setIcon(self._item_icon(value))
                if c == 0: item.setData(Qt.UserRole, trade_key(trade))
                self.table.setItem(r, c, item)
        if rows: self.table.selectRow(0)
        else: self.detail.clear()
        self.refresh_compare()

    def selected_trade(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return None
        index = rows[0].row(); return self.rows[index] if 0 <= index < len(self.rows) else None

    def show_selected(self):
        trade = self.selected_trade()
        if trade is None: return
        key = trade_key(trade); max_uses = max(1, int(trade.max_uses or self.uses.value())); planned = self.uses.value(); restocks = max(0, math.ceil(planned / max_uses) - 1)
        wants_count = _number(trade.wants); additional_count = _number(trade.additional_wants, 0) if trade.additional_wants else 0; gives_count = _number(trade.gives)
        direction = trade_direction(trade); emerald_flow = 0.0
        if "emerald" in trade.gives.lower(): emerald_flow += gives_count * planned
        if "emerald" in trade.wants.lower(): emerald_flow -= wants_count * planned
        if trade.additional_wants and "emerald" in trade.additional_wants.lower(): emerald_flow -= additional_count * planned
        self.detail.setHtml(
            f"<h2>{trade.name}</h2><p><b>{trade.profession.title()} — {LEVEL_NAMES.get(trade.level, trade.level)}</b></p>"
            f"<p>{trade.wants}{' + ' + trade.additional_wants if trade.additional_wants else ''} → {trade.gives}</p>"
            f"<p>Direction: {direction}<br>Max uses before restock: {trade.max_uses if trade.max_uses is not None else 'not specified'}<br>Villager XP: {trade.xp if trade.xp is not None else 'not specified'}<br>Planned uses: {planned}<br>Minimum restocks for planned uses: {restocks}<br>Approximate emerald flow across planned uses: {emerald_flow:g}</p>"
            f"<p>Definition: {trade.raw_path or trade.source}<br>Source: {self.source}</p><p>{trade.details or ''}</p>"
        )
        self.favorite.setText("★ Favorited" if key in self.owner.settings.favorite_trades else "☆ Favorite"); self.compare.setText("Remove from compare" if key in self.compare_keys else "Add to compare")

    def toggle_favorite(self):
        trade = self.selected_trade()
        if trade is None: return
        key = trade_key(trade); rows = list(self.owner.settings.favorite_trades)
        if key in rows: rows = [value for value in rows if value != key]
        else: rows.append(key)
        self.owner.settings.favorite_trades = rows; self.owner.settings.save(); self.refresh() if self.favorites_only.isChecked() else self.show_selected()

    def toggle_compare(self):
        trade = self.selected_trade()
        if trade is None: return
        key = trade_key(trade)
        if key in self.compare_keys: self.compare_keys.remove(key)
        else: self.compare_keys.append(key)
        self.refresh_compare(); self.show_selected()

    def clear_compare(self): self.compare_keys.clear(); self.refresh_compare(); self.show_selected()

    def refresh_compare(self):
        self.compare_list.clear(); lookup = {trade_key(trade): trade for trade in self.trades}
        for key in list(self.compare_keys):
            trade = lookup.get(key)
            if trade is None: continue
            self.compare_list.addItem(QListWidgetItem(f"{trade.profession.title()} L{trade.level}: {trade.wants} → {trade.gives} • max {trade.max_uses or '?'} uses"))

    def run_helper(self, name: str):
        specs = BY_NAME.get(name, [])
        if not specs: return QMessageBox.warning(self, name, "This helper is not present in the compatibility catalog.")
        spec = specs[0]; fields = self.owner.executor.input_fields(spec); dialog = ParameterDialog(name, fields, self, "Uses the canonical villager helper calculation.")
        if dialog.exec() != QDialog.Accepted: return
        try:
            result = self.owner.executor.execute(spec, dialog.values()); QMessageBox.information(self, name, self.owner._format(result.data))
        except Exception as exc: QMessageBox.warning(self, name, str(exc))
