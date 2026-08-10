from __future__ import annotations

"""Visual, virtualized villager trade explorer.

The previous implementation rebuilt an eight-column QTableWidget (and its item icons)
on every filter keystroke.  This version keeps all matching trades in a lightweight
model and paints only visible rows, while the detail panel represents the actual
villager transaction rather than another table.
"""

import math
import re

from PySide6.QtCore import QAbstractListModel, QModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListView, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QSpinBox, QSplitter, QTabWidget, QVBoxLayout, QWidget,
    QStyledItemDelegate,
)

from .catalog_ids import BY_NAME
from .minecraft_simulators import MinecraftJarData
from .minecraft_widgets import AssetProvider, ExplanationCard, MetricCard
from .ui_dialogs import ParameterDialog
from .villager_reference import REFERENCE_SOURCE, complete_reference
from .villagers import BASELINE_SOURCE, LEVEL_NAMES, PROFESSIONS, load_for_version, search as trade_search, trade_direction, trade_key


def _item_token(text: str) -> str:
    value = str(text or "").lower().strip().removeprefix("minecraft:")
    value = re.sub(r"^\d+(?:\.\d+)?\s*[x×]?\s*", "", value)
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def _number(text: str, default=1.0):
    match = re.search(r"-?\d+(?:\.\d+)?", str(text or ""))
    return float(match.group()) if match else float(default)


def _load_trade_data(version: str):
    trades, source = load_for_version(version)
    if source == BASELINE_SOURCE:
        trades = complete_reference(trades); source = REFERENCE_SOURCE
    return trades, source


class TradeModel(QAbstractListModel):
    TradeRole = Qt.UserRole + 1

    def __init__(self, rows=None, parent=None):
        super().__init__(parent); self.rows = list(rows or [])

    def set_rows(self, rows):
        self.beginResetModel(); self.rows = list(rows); self.endResetModel()

    def rowCount(self, parent=QModelIndex()): return 0 if parent.isValid() else len(self.rows)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.rows)): return None
        trade = self.rows[index.row()]
        if role == self.TradeRole: return trade
        if role == Qt.DisplayRole: return trade.name
        if role == Qt.ToolTipRole: return f"{trade.wants}{' + ' + trade.additional_wants if trade.additional_wants else ''} → {trade.gives}"
        return None


class TradeDelegate(QStyledItemDelegate):
    def __init__(self, assets: AssetProvider, parent=None):
        super().__init__(parent); self.assets = assets

    def sizeHint(self, option, index): return QSize(option.rect.width(), 76)

    def paint(self, painter: QPainter, option, index):
        trade = index.data(TradeModel.TradeRole)
        if trade is None: return
        painter.save(); rect = option.rect.adjusted(4, 3, -4, -3)
        selected = bool(option.state & option.state.State_Selected)
        base = option.palette.highlight().color() if selected else option.palette.base().color()
        painter.fillRect(rect, base)

        wants = self.assets.icon("minecraft:" + _item_token(trade.wants), 30).pixmap(QSize(30, 30))
        gives = self.assets.icon("minecraft:" + _item_token(trade.gives), 30).pixmap(QSize(30, 30))
        painter.drawPixmap(rect.left() + 8, rect.top() + 22, wants)
        painter.drawPixmap(rect.left() + 244, rect.top() + 22, gives)
        painter.setPen(option.palette.text().color() if not selected else option.palette.highlightedText().color())
        font = painter.font(); font.setBold(True); painter.setFont(font); painter.drawText(QRect(rect.left() + 48, rect.top() + 7, 420, 20), Qt.AlignLeft | Qt.AlignVCenter, f"{trade.profession.title()} • {LEVEL_NAMES.get(trade.level, trade.level)}")
        font.setBold(False); painter.setFont(font)
        left = trade.wants + (" + " + trade.additional_wants if trade.additional_wants else "")
        painter.drawText(QRect(rect.left() + 48, rect.top() + 29, 185, 32), Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, left)
        painter.drawText(QRect(rect.left() + 210, rect.top() + 28, 26, 32), Qt.AlignCenter, "→")
        painter.drawText(QRect(rect.left() + 282, rect.top() + 29, max(80, rect.width() - 430), 32), Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, trade.gives)
        painter.setPen(option.palette.mid().color()); painter.drawText(QRect(rect.right() - 135, rect.top() + 7, 125, 20), Qt.AlignRight | Qt.AlignVCenter, f"max {trade.max_uses if trade.max_uses is not None else '?'} • XP {trade.xp if trade.xp is not None else '?'}")
        painter.restore()


class VillagerExplorerDialog(QDialog):
    def __init__(self, owner, profession: str | None = None, mode: str = "Trade Browser"):
        super().__init__(owner)
        self.owner = owner; self.mode = mode; self.trades, self.source = _load_trade_data(owner.settings.minecraft_version)
        self.jar = MinecraftJarData(owner.settings.minecraft_version); self.assets = AssetProvider(self.jar); self.compare_keys: list[str] = []; self.rows = []; self._portrait_cache = {}
        self.setWindowTitle("Villager Explorer"); self.resize(1460, 900); self.setMinimumSize(1100, 720)
        root = QVBoxLayout(self); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(8)

        hero = QFrame(); hero.setObjectName("ExplorerHero"); hh = QHBoxLayout(hero)
        self.portrait = QLabel(); self.portrait.setFixedSize(88, 88); self.portrait.setAlignment(Qt.AlignCenter); hh.addWidget(self.portrait)
        titles = QVBoxLayout(); title = QLabel("Villager Explorer"); title.setObjectName("WorkspaceTitle"); titles.addWidget(title); intro = QLabel("Browse every loaded offer by profession and level, search by item/enchantment, compare trades, and plan repeated use without rebuilding a giant table."); intro.setWordWrap(True); intro.setObjectName("Muted"); titles.addWidget(intro); self.source_label = QLabel(); self.source_label.setWordWrap(True); self.source_label.setObjectName("Muted"); titles.addWidget(self.source_label); hh.addLayout(titles, 1)
        refresh = QPushButton("Reload installed trade data"); refresh.clicked.connect(self.reload); hh.addWidget(refresh); root.addWidget(hero)

        tabs = QTabWidget(); root.addWidget(tabs, 1); self._build_browser(tabs); self._build_planning(tabs)
        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close)

        target = "librarian" if mode == "Librarian Browser" else (profession or "").lower()
        if target in PROFESSIONS:
            for row in range(self.profession_list.count()):
                if self.profession_list.item(row).data(Qt.UserRole) == target: self.profession_list.setCurrentRow(row); break
        self.refresh()

    def _build_browser(self, tabs):
        page = QWidget(); root = QVBoxLayout(page); root.setContentsMargins(8, 8, 8, 8); root.setSpacing(8)
        filters = QHBoxLayout(); self.level = QComboBox(); self.level.addItem("All levels"); self.level.addItems([f"{i} — {LEVEL_NAMES[i]}" for i in range(1, 6)]); self.direction = QComboBox(); self.direction.addItems(["All directions", "Villager sells to you", "Villager buys from you", "Exchange"]); self.query = QLineEdit(); self.query.setPlaceholderText("Search item, enchantment, profession or offer…"); self.query.setClearButtonEnabled(True); self.uses = QSpinBox(); self.uses.setRange(1, 9999); self.uses.setValue(64 if self.mode == "Trade Cycle Calculator" else 12); self.uses.setPrefix("Plan "); self.uses.setSuffix(" uses"); self.favorites_only = QCheckBox("Favorites only")
        filters.addWidget(self.level); filters.addWidget(self.direction); filters.addWidget(self.query, 2); filters.addWidget(self.uses); filters.addWidget(self.favorites_only); root.addLayout(filters)

        split = QSplitter(Qt.Horizontal); split.setChildrenCollapsible(False); root.addWidget(split, 1)
        professions = QFrame(); professions.setObjectName("ExplorerRail"); pv = QVBoxLayout(professions); label = QLabel("PROFESSIONS"); label.setObjectName("DeckLabel"); pv.addWidget(label); self.profession_list = QListWidget(); self.profession_list.setIconSize(QSize(36, 36)); pv.addWidget(self.profession_list, 1); split.addWidget(professions); self._populate_professions()

        trades = QFrame(); trades.setObjectName("ExplorerTrades"); tv = QVBoxLayout(trades); head = QHBoxLayout(); title = QLabel("TRADES"); title.setObjectName("DeckLabel"); head.addWidget(title); head.addStretch(); self.trade_count = QLabel(); self.trade_count.setObjectName("Muted"); head.addWidget(self.trade_count); tv.addLayout(head); self.trade_view = QListView(); self.trade_view.setUniformItemSizes(True); self.trade_view.setSelectionMode(QListView.SingleSelection); self.trade_model = TradeModel(parent=self.trade_view); self.trade_view.setModel(self.trade_model); self.trade_view.setItemDelegate(TradeDelegate(self.assets, self.trade_view)); tv.addWidget(self.trade_view, 1); split.addWidget(trades)

        detail = QFrame(); detail.setObjectName("TradeDetail"); dv = QVBoxLayout(detail); self.detail_title = QLabel("Choose a trade"); self.detail_title.setObjectName("WorkspaceTitle"); dv.addWidget(self.detail_title); self.detail_meta = QLabel(); self.detail_meta.setWordWrap(True); self.detail_meta.setObjectName("Muted"); dv.addWidget(self.detail_meta)
        transaction = QFrame(); transaction.setObjectName("TradeTransaction"); tr = QHBoxLayout(transaction); self.want_icon = QLabel(); self.want_icon.setFixedSize(44, 44); self.want_text = QLabel(); self.want_text.setWordWrap(True); plus = QLabel("→"); plus.setObjectName("TradeArrow"); self.give_icon = QLabel(); self.give_icon.setFixedSize(44, 44); self.give_text = QLabel(); self.give_text.setWordWrap(True); tr.addWidget(self.want_icon); tr.addWidget(self.want_text, 1); tr.addWidget(plus); tr.addWidget(self.give_icon); tr.addWidget(self.give_text, 1); dv.addWidget(transaction)
        metrics = QHBoxLayout(); self.restocks = MetricCard("Restocks"); self.emeralds = MetricCard("Emerald flow"); self.max_uses = MetricCard("Max uses"); metrics.addWidget(self.restocks); metrics.addWidget(self.emeralds); metrics.addWidget(self.max_uses); dv.addLayout(metrics)
        self.detail_note = ExplanationCard("Offer details", "Select a trade from the center panel."); dv.addWidget(self.detail_note)
        actions = QHBoxLayout(); self.favorite = QPushButton("☆ Favorite"); self.compare = QPushButton("Add to compare"); actions.addWidget(self.favorite); actions.addWidget(self.compare); dv.addLayout(actions); compare_label = QLabel("COMPARE"); compare_label.setObjectName("DeckLabel"); dv.addWidget(compare_label); self.compare_list = QListWidget(); self.compare_list.setMaximumHeight(170); dv.addWidget(self.compare_list); clear = QPushButton("Clear comparison"); clear.clicked.connect(self.clear_compare); dv.addWidget(clear); split.addWidget(detail); split.setSizes([210, 760, 430])

        self.level.currentTextChanged.connect(self.refresh); self.direction.currentTextChanged.connect(self.refresh); self.query.textChanged.connect(self.refresh); self.favorites_only.toggled.connect(self.refresh); self.uses.valueChanged.connect(self.show_selected); self.profession_list.currentItemChanged.connect(lambda *_: self.refresh()); self.trade_view.selectionModel().selectionChanged.connect(lambda *_: self.show_selected()); self.favorite.clicked.connect(self.toggle_favorite); self.compare.clicked.connect(self.toggle_compare)
        tabs.addTab(page, "Trade Explorer")

    def _build_planning(self, tabs):
        page = QWidget(); root = QVBoxLayout(page); root.setContentsMargins(12, 12, 12, 12); root.addWidget(ExplanationCard("Villager planning", "Curing, halls, workstation counts and breeding food stay beside the trade explorer. Each helper opens an explained parameter/result panel rather than a raw calculator popup."))
        for name in ("Zombie Cure Calculator", "Villager Hall Calculator", "Workstation Count", "Breeding Food Calculator"):
            button = QPushButton(name); button.clicked.connect(lambda _=False, n=name: self.run_helper(n)); root.addWidget(button)
        root.addStretch(); tabs.addTab(page, "Planning Helpers")

    def _portrait_pixmap(self, profession: str) -> QPixmap:
        key = profession or "none"
        if key in self._portrait_cache: return self._portrait_cache[key]
        size = 84; layers = ["assets/minecraft/textures/entity/villager/villager.png", "assets/minecraft/textures/entity/villager/type/plains.png"]
        if profession: layers.append(f"assets/minecraft/textures/entity/villager/profession/{profession}.png")
        canvas = QPixmap(64, 84); canvas.fill(Qt.transparent); painter = QPainter(canvas); loaded = False
        for member in layers:
            raw = self.jar.read_bytes(member); sheet = QPixmap()
            if not raw or not sheet.loadFromData(raw): continue
            loaded = True; painter.drawPixmap(QRect(12, 2, 40, 40), sheet, QRect(8, 8, 8, 8)); painter.drawPixmap(QRect(10, 0, 44, 44), sheet, QRect(40, 8, 8, 8)); painter.drawPixmap(QRect(16, 40, 32, 42), sheet, QRect(20, 20, 8, 12))
        painter.end(); pix = canvas.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation) if loaded else QPixmap(); self._portrait_cache[key] = pix; return pix

    def _populate_professions(self):
        self.profession_list.clear(); all_item = QListWidgetItem("All professions"); all_item.setData(Qt.UserRole, ""); self.profession_list.addItem(all_item)
        for profession in PROFESSIONS:
            pix = self._portrait_pixmap(profession); item = QListWidgetItem(QIcon(pix) if not pix.isNull() else QIcon(), profession.title()); item.setData(Qt.UserRole, profession); self.profession_list.addItem(item)
        self.profession_list.setCurrentRow(0)

    def selected_profession(self):
        item = self.profession_list.currentItem(); return str(item.data(Qt.UserRole) or "") if item else ""

    def reload(self):
        self.trades, self.source = _load_trade_data(self.owner.settings.minecraft_version); self.jar = MinecraftJarData(self.owner.settings.minecraft_version); self.assets = AssetProvider(self.jar); self.trade_view.setItemDelegate(TradeDelegate(self.assets, self.trade_view)); self._portrait_cache.clear(); self._populate_professions(); self.refresh()

    def refresh(self):
        profession = self.selected_profession() or None; level = None if self.level.currentText().startswith("All") else int(self.level.currentText()[0]); rows = trade_search(self.trades, self.query.text(), profession, level)
        direction = self.direction.currentText()
        if direction != "All directions": rows = [trade for trade in rows if trade_direction(trade) == direction]
        if self.favorites_only.isChecked(): rows = [trade for trade in rows if trade_key(trade) in self.owner.settings.favorite_trades]
        self.rows = rows; self.trade_model.set_rows(rows); self.trade_count.setText(f"{len(rows):,} matching trades • {len(self.trades):,} loaded")
        self.portrait.setPixmap(self._portrait_pixmap(profession or "")); exact = str(self.source).lower() == str(self.owner.settings.minecraft_version).lower(); self.source_label.setText(f"Trade data: {self.source}" + (" • selected-version source" if exact else " • labeled reference/fallback; install matching version data for exact offers"))
        if rows: self.trade_view.setCurrentIndex(self.trade_model.index(0, 0))
        else: self.detail_title.setText("No matching trades"); self.detail_note.set_text("Change profession, level, direction, favorites, or search text.")
        self.refresh_compare()

    def selected_trade(self):
        index = self.trade_view.currentIndex(); return index.data(TradeModel.TradeRole) if index.isValid() else None

    def show_selected(self):
        trade = self.selected_trade()
        if trade is None: return
        key = trade_key(trade); planned = self.uses.value(); max_uses = max(1, int(trade.max_uses or planned)); restocks = max(0, math.ceil(planned / max_uses) - 1); wants_count = _number(trade.wants); additional_count = _number(trade.additional_wants, 0) if trade.additional_wants else 0; gives_count = _number(trade.gives); emerald_flow = 0.0
        if "emerald" in trade.gives.lower(): emerald_flow += gives_count * planned
        if "emerald" in trade.wants.lower(): emerald_flow -= wants_count * planned
        if trade.additional_wants and "emerald" in trade.additional_wants.lower(): emerald_flow -= additional_count * planned
        self.detail_title.setText(trade.name); self.detail_meta.setText(f"{trade.profession.title()} • {LEVEL_NAMES.get(trade.level, trade.level)} • {trade_direction(trade)} • source {self.source}")
        wants = trade.wants + (" + " + trade.additional_wants if trade.additional_wants else ""); self.want_text.setText(wants); self.give_text.setText(trade.gives); self.want_icon.setPixmap(self.assets.icon("minecraft:" + _item_token(trade.wants), 38).pixmap(QSize(38, 38))); self.give_icon.setPixmap(self.assets.icon("minecraft:" + _item_token(trade.gives), 38).pixmap(QSize(38, 38)))
        self.restocks.set_value(restocks); self.emeralds.set_value(f"{emerald_flow:+g}"); self.max_uses.set_value(trade.max_uses if trade.max_uses is not None else "—"); details = trade.details or "No additional version-specific description is stored for this offer."; self.detail_note.set_text(f"Planning {planned} uses requires at least {restocks} restock(s) under the listed max-use value. Villager XP: {trade.xp if trade.xp is not None else 'not specified'}. {details}")
        self.favorite.setText("★ Favorited" if key in self.owner.settings.favorite_trades else "☆ Favorite"); self.compare.setText("Remove from compare" if key in self.compare_keys else "Add to compare")

    def toggle_favorite(self):
        trade = self.selected_trade()
        if trade is None: return
        key = trade_key(trade); rows = list(self.owner.settings.favorite_trades)
        rows = [value for value in rows if value != key] if key in rows else rows + [key]
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
        for key in self.compare_keys:
            trade = lookup.get(key)
            if trade is not None: self.compare_list.addItem(f"{trade.profession.title()} L{trade.level}: {trade.wants} → {trade.gives} • max {trade.max_uses or '?'}")

    def run_helper(self, name: str):
        specs = BY_NAME.get(name, [])
        if not specs: return QMessageBox.warning(self, name, "This helper is not present in the compatibility catalog.")
        spec = specs[0]; fields = self.owner.executor.input_fields(spec); dialog = ParameterDialog(name, fields, self, "Configure the villager planning values below. Internal compatibility defaults are not shown.")
        if dialog.exec() != QDialog.Accepted: return
        try:
            result = self.owner.executor.execute(spec, dialog.values()); QMessageBox.information(self, name, self.owner._format(result.data))
        except Exception as exc: QMessageBox.warning(self, name, str(exc))
