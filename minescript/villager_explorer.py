from __future__ import annotations

from pathlib import Path
import re
import zipfile

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea,
    QSizePolicy, QSpinBox, QSplitter, QVBoxLayout, QWidget,
)

from .minecraft_art import texture_bytes
from .pixel_art import icon_pixmap
from .ui_theme import palette
from .villagers import (
    LEVEL_NAMES, PROFESSIONS, Trade, installed_versions, load_for_version, search,
    trade_direction, trade_key,
)

WORKSTATIONS = {
    "armorer": "blast_furnace_front_on",
    "butcher": "smoker_front_on",
    "cartographer": "cartography_table_side3",
    "cleric": "brewing_stand",
    "farmer": "composter_side",
    "fisherman": "barrel_side",
    "fletcher": "fletching_table_front",
    "leatherworker": "cauldron_side",
    "librarian": "lectern_front",
    "mason": "stonecutter_side",
    "shepherd": "loom_front",
    "toolsmith": "smithing_table_front",
    "weaponsmith": "grindstone_side",
}


class MinecraftTextureProvider:
    def __init__(self, source_version: str, theme: str, custom_palette: dict | None = None):
        self.source_version = source_version
        self.theme = theme
        self.colors = palette(theme, custom_palette)
        self.cache: dict[tuple[str, int], QPixmap] = {}
        self.jar = installed_versions().get(source_version)

    def _read(self, candidates: list[str]) -> bytes | None:
        if self.jar is None:
            return None
        try:
            with zipfile.ZipFile(self.jar) as archive:
                names = set(archive.namelist())
                for member in candidates:
                    if member in names:
                        return archive.read(member)
        except (OSError, zipfile.BadZipFile, KeyError):
            return None
        return None

    def pixmap(self, item_id: str, size: int = 42, fallback: str = "shulker") -> QPixmap:
        clean = str(item_id or "").removeprefix("minecraft:")
        key = (clean, int(size))
        if key in self.cache:
            return self.cache[key]
        candidates = [
            f"assets/minecraft/textures/item/{clean}.png",
            f"assets/minecraft/textures/block/{clean}.png",
            f"assets/minecraft/textures/block/{clean}_front.png",
            f"assets/minecraft/textures/block/{clean}_front_on.png",
            f"assets/minecraft/textures/block/{clean}_side.png",
        ]
        data = self._read(candidates)
        pix = QPixmap()
        if data:
            pix.loadFromData(data)
        if pix.isNull():
            data, _, _ = texture_bytes(fallback, self.source_version)
            if data:
                pix.loadFromData(data)
        if pix.isNull():
            pix = icon_pixmap(fallback, self.colors, size)
        else:
            pix = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.cache[key] = pix
        return pix

    def profession_icon(self, profession: str, size: int = 34) -> QIcon:
        block = WORKSTATIONS.get(profession, "emerald_block")
        return QIcon(self.pixmap(block, size, "villager"))


class TradeCard(QWidget):
    def __init__(self, trade: Trade, textures: MinecraftTextureProvider, parent=None):
        super().__init__(parent)
        self.trade = trade
        self.setObjectName("TradeCard")
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 8, 12, 8)
        row.setSpacing(10)

        level = QLabel(f"{trade.level}\n{LEVEL_NAMES.get(trade.level, '')}")
        level.setObjectName("TradeLevel")
        level.setAlignment(Qt.AlignCenter)
        level.setFixedWidth(78)
        row.addWidget(level)

        row.addWidget(self._stack(textures, trade.wants_id, trade.wants, 44))
        if trade.additional_wants:
            plus = QLabel("+")
            plus.setObjectName("TradeOperator")
            plus.setAlignment(Qt.AlignCenter)
            row.addWidget(plus)
            row.addWidget(self._stack(textures, trade.additional_wants_id, trade.additional_wants, 44))

        arrow = QLabel("→")
        arrow.setObjectName("TradeArrow")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setFixedWidth(34)
        row.addWidget(arrow)
        row.addWidget(self._stack(textures, trade.gives_id, trade.gives, 48))
        row.addStretch(1)

        meta = QVBoxLayout()
        direction = QLabel(trade_direction(trade))
        direction.setObjectName("Muted")
        direction.setAlignment(Qt.AlignRight)
        meta.addWidget(direction)
        uses = "—" if trade.max_uses is None else str(trade.max_uses).rstrip(".0")
        max_uses = QLabel(f"Max uses: {uses}")
        max_uses.setObjectName("Muted")
        max_uses.setAlignment(Qt.AlignRight)
        meta.addWidget(max_uses)
        row.addLayout(meta)

    @staticmethod
    def _stack(textures: MinecraftTextureProvider, item_id: str, text: str, size: int):
        box = QFrame()
        box.setObjectName("TradeStack")
        layout = QHBoxLayout(box)
        layout.setContentsMargins(6, 4, 8, 4)
        layout.setSpacing(7)
        icon = QLabel()
        icon.setFixedSize(size, size)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(textures.pixmap(item_id, size))
        layout.addWidget(icon)
        label = QLabel(_human_stack(text))
        label.setWordWrap(True)
        label.setMinimumWidth(110)
        layout.addWidget(label)
        return box


class VillagerExplorer(QDialog):
    def __init__(
        self,
        selected_version: str,
        parent=None,
        profession: str | None = None,
        mode: str = "Trade Browser",
        settings=None,
    ):
        super().__init__(parent)
        self.settings = settings
        self.selected_version = selected_version
        self.mode = mode
        self.trades, self.source_version = load_for_version(selected_version)
        theme = getattr(settings, "theme", "chorus") if settings else "chorus"
        custom = getattr(settings, "custom_palette", None) if settings else None
        self.textures = MinecraftTextureProvider(self.source_version, theme, custom)
        self.compare_keys: list[str] = []
        self.rows: list[Trade] = []

        self.setWindowTitle("Villager Trade Explorer")
        self.setObjectName("VillagerExplorer")
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        self.resize(1320, 820)
        self.setMinimumSize(1060, 680)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)
        outer.addWidget(self._header())
        outer.addWidget(self._filters())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        outer.addWidget(splitter, 1)

        splitter.addWidget(self._profession_panel())
        splitter.addWidget(self._trade_panel())
        splitter.addWidget(self._detail_panel())
        splitter.setSizes([210, 720, 350])

        self.profession_list.currentItemChanged.connect(lambda *_: self.refresh())
        self.level.currentTextChanged.connect(lambda *_: self.refresh())
        self.direction.currentTextChanged.connect(lambda *_: self.refresh())
        self.query.textChanged.connect(lambda *_: self.refresh())
        self.favorites_only.toggled.connect(lambda *_: self.refresh())
        self.uses.valueChanged.connect(lambda *_: self._show_selected())
        self.trade_list.itemSelectionChanged.connect(self._show_selected)

        target = (profession or "").lower()
        if mode == "Librarian Browser":
            target = "librarian"
        self._select_profession(target)
        self.refresh()
        if mode in {"Trade Search", "Librarian Browser"}:
            self.query.setFocus()

    def _header(self):
        frame = QFrame()
        frame.setObjectName("ExplorerHero")
        layout = QHBoxLayout(frame)
        left = QVBoxLayout()
        title = QLabel("Villager Trade Explorer")
        title.setObjectName("DetailTitle")
        left.addWidget(title)
        subtitle = QLabel("Browse trades visually by profession, level, item, direction, favorites, or version source.")
        subtitle.setObjectName("Muted")
        left.addWidget(subtitle)
        layout.addLayout(left, 1)

        selected = QLabel(f"Selected: {self.selected_version}")
        selected.setObjectName("VersionChip")
        layout.addWidget(selected)
        source = QLabel(f"Trade data: {self.source_version}")
        source.setObjectName("VersionChip" if _normal(self.selected_version) == _normal(self.source_version) else "WarningChip")
        source.setToolTip(
            "Trade definitions are loaded from the exact selected version." if _normal(self.selected_version) == _normal(self.source_version)
            else "The selected version is not installed locally. The explorer is showing the newest installed stable trade definitions instead."
        )
        layout.addWidget(source)
        count = QLabel(f"{len(self.trades)} trades")
        count.setObjectName("Muted")
        layout.addWidget(count)
        return frame

    def _filters(self):
        frame = QFrame()
        frame.setObjectName("ExplorerFilters")
        row = QHBoxLayout(frame)
        self.query = QLineEdit()
        self.query.setClearButtonEnabled(True)
        self.query.setPlaceholderText("Search item, enchantment detail, profession, or trade…")
        row.addWidget(self.query, 2)
        self.level = QComboBox()
        self.level.addItem("All levels", 0)
        for number in range(1, 6):
            self.level.addItem(f"{number} — {LEVEL_NAMES[number]}", number)
        row.addWidget(self.level)
        self.direction = QComboBox()
        self.direction.addItems(["All directions", "Villager sells to you", "Villager buys from you", "Exchange"])
        row.addWidget(self.direction)
        self.uses = QSpinBox()
        self.uses.setRange(1, 9999)
        self.uses.setValue(12 if self.mode != "Trade Cycle Calculator" else 64)
        self.uses.setPrefix("Plan ")
        self.uses.setSuffix(" uses")
        self.uses.setToolTip("Used by the detail and comparison panes to estimate repeat trade totals.")
        row.addWidget(self.uses)
        self.favorites_only = QCheckBox("Favorites only")
        row.addWidget(self.favorites_only)
        return frame

    def _profession_panel(self):
        frame = QFrame()
        frame.setObjectName("ExplorerRail")
        layout = QVBoxLayout(frame)
        label = QLabel("PROFESSIONS")
        label.setObjectName("DeckLabel")
        layout.addWidget(label)
        self.profession_list = QListWidget()
        self.profession_list.setObjectName("ProfessionList")
        self.profession_list.setIconSize(QSize(32, 32))
        all_item = QListWidgetItem("All professions")
        all_item.setData(Qt.UserRole, "")
        all_item.setIcon(QIcon(self.textures.pixmap("emerald", 32, "villager")))
        self.profession_list.addItem(all_item)
        for profession in PROFESSIONS:
            item = QListWidgetItem(profession.title())
            item.setData(Qt.UserRole, profession)
            item.setIcon(self.textures.profession_icon(profession))
            self.profession_list.addItem(item)
        layout.addWidget(self.profession_list, 1)
        return frame

    def _trade_panel(self):
        frame = QFrame()
        frame.setObjectName("ExplorerTrades")
        layout = QVBoxLayout(frame)
        top = QHBoxLayout()
        self.result_label = QLabel("Trades")
        self.result_label.setObjectName("WorkspaceTitle")
        top.addWidget(self.result_label)
        top.addStretch(1)
        self.reset_button = QPushButton("Reset filters")
        self.reset_button.clicked.connect(self._reset_filters)
        top.addWidget(self.reset_button)
        layout.addLayout(top)
        self.trade_list = QListWidget()
        self.trade_list.setObjectName("TradeCardList")
        self.trade_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.trade_list.setSpacing(5)
        layout.addWidget(self.trade_list, 1)
        return frame

    def _detail_panel(self):
        frame = QFrame()
        frame.setObjectName("TradeDetail")
        layout = QVBoxLayout(frame)
        label = QLabel("TRADE DETAILS")
        label.setObjectName("DeckLabel")
        layout.addWidget(label)
        self.detail_title = QLabel("Select a trade")
        self.detail_title.setObjectName("WorkspaceTitle")
        self.detail_title.setWordWrap(True)
        layout.addWidget(self.detail_title)
        self.detail_meta = QLabel("Choose a trade card to inspect its exact inputs, output, uses, XP, and source definition.")
        self.detail_meta.setObjectName("Muted")
        self.detail_meta.setWordWrap(True)
        layout.addWidget(self.detail_meta)

        self.detail_transaction = QFrame()
        self.detail_transaction.setObjectName("TradeTransaction")
        self.detail_transaction_layout = QVBoxLayout(self.detail_transaction)
        layout.addWidget(self.detail_transaction)

        action_row = QHBoxLayout()
        self.favorite_button = QPushButton("☆ Favorite")
        self.favorite_button.clicked.connect(self._toggle_favorite)
        action_row.addWidget(self.favorite_button)
        self.compare_button = QPushButton("Add to compare")
        self.compare_button.clicked.connect(self._toggle_compare)
        action_row.addWidget(self.compare_button)
        layout.addLayout(action_row)

        compare_label = QLabel("COMPARE")
        compare_label.setObjectName("DeckLabel")
        layout.addWidget(compare_label)
        self.compare_list = QListWidget()
        self.compare_list.setObjectName("CompareList")
        self.compare_list.setMaximumHeight(190)
        layout.addWidget(self.compare_list)
        clear = QPushButton("Clear comparison")
        clear.clicked.connect(self._clear_compare)
        layout.addWidget(clear)
        layout.addStretch(1)
        return frame

    def _select_profession(self, profession: str):
        for index in range(self.profession_list.count()):
            item = self.profession_list.item(index)
            if item.data(Qt.UserRole) == profession:
                self.profession_list.setCurrentRow(index)
                return
        self.profession_list.setCurrentRow(0)

    def _reset_filters(self):
        self.profession_list.setCurrentRow(0)
        self.level.setCurrentIndex(0)
        self.direction.setCurrentIndex(0)
        self.query.clear()
        self.favorites_only.setChecked(False)

    def _favorite_keys(self) -> set[str]:
        return set(getattr(self.settings, "favorite_trades", []) or []) if self.settings is not None else set()

    def refresh(self):
        profession = ""
        item = self.profession_list.currentItem()
        if item is not None:
            profession = str(item.data(Qt.UserRole) or "")
        level = int(self.level.currentData() or 0)
        rows = search(self.trades, self.query.text(), profession or None, level or None)
        wanted_direction = self.direction.currentText()
        if wanted_direction != "All directions":
            rows = [trade for trade in rows if trade_direction(trade) == wanted_direction]
        if self.favorites_only.isChecked():
            favorites = self._favorite_keys()
            rows = [trade for trade in rows if trade_key(trade) in favorites]
        self.rows = rows
        self.result_label.setText(f"{len(rows)} matching trade{'s' if len(rows) != 1 else ''}")
        self.trade_list.setUpdatesEnabled(False)
        try:
            self.trade_list.clear()
            favorites = self._favorite_keys()
            for trade in rows:
                item = QListWidgetItem()
                item.setData(Qt.UserRole, trade_key(trade))
                item.setSizeHint(QSize(540, 86))
                if trade_key(trade) in favorites:
                    item.setToolTip("Favorited trade")
                self.trade_list.addItem(item)
                self.trade_list.setItemWidget(item, TradeCard(trade, self.textures, self.trade_list))
        finally:
            self.trade_list.setUpdatesEnabled(True)
        if self.trade_list.count():
            self.trade_list.setCurrentRow(0)
        else:
            self._clear_detail()

    def _selected_trade(self) -> Trade | None:
        items = self.trade_list.selectedItems()
        if not items:
            return None
        key = str(items[0].data(Qt.UserRole) or "")
        return next((trade for trade in self.rows if trade_key(trade) == key), None)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child = item.layout()
            if widget is not None:
                widget.deleteLater()
            if child is not None:
                self._clear_layout(child)

    def _clear_detail(self):
        self.detail_title.setText("No matching trades")
        self.detail_meta.setText("Change the profession, level, direction, favorites, or search filter.")
        self._clear_layout(self.detail_transaction_layout)
        self.favorite_button.setEnabled(False)
        self.compare_button.setEnabled(False)

    def _show_selected(self):
        trade = self._selected_trade()
        if trade is None:
            self._clear_detail()
            return
        self.favorite_button.setEnabled(True)
        self.compare_button.setEnabled(True)
        self.detail_title.setText(_human_item(trade.gives_id or trade.name))
        self.detail_meta.setText(
            f"{trade.profession.title()} • {trade.level} — {LEVEL_NAMES.get(trade.level, trade.level)} • {trade_direction(trade)}"
        )
        self._clear_layout(self.detail_transaction_layout)
        self.detail_transaction_layout.addWidget(self._detail_stack("You give", trade.wants_id, trade.wants))
        if trade.additional_wants:
            self.detail_transaction_layout.addWidget(self._detail_stack("Plus", trade.additional_wants_id, trade.additional_wants))
        arrow = QLabel("↓")
        arrow.setObjectName("TradeArrow")
        arrow.setAlignment(Qt.AlignCenter)
        self.detail_transaction_layout.addWidget(arrow)
        self.detail_transaction_layout.addWidget(self._detail_stack("You receive", trade.gives_id, trade.gives))

        uses = self.uses.value()
        summary = []
        if trade.max_uses is not None:
            summary.append(f"Max uses before restock: {str(trade.max_uses).rstrip('.0')}")
        if trade.xp is not None:
            summary.append(f"Villager XP per trade: {str(trade.xp).rstrip('.0')}")
        emeralds = _emerald_cost(trade)
        if emeralds is not None:
            summary.append(f"Planned emerald total for {uses} uses: {emeralds * uses:g}")
        if trade.details:
            summary.append("Definition detail: " + trade.details)
        summary.append("Source: " + trade.raw_path)
        note = QLabel("\n".join(summary))
        note.setObjectName("Muted")
        note.setWordWrap(True)
        note.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.detail_transaction_layout.addWidget(note)

        key = trade_key(trade)
        self.favorite_button.setText("★ Favorited" if key in self._favorite_keys() else "☆ Favorite")
        self.compare_button.setText("Remove comparison" if key in self.compare_keys else "Add to compare")
        self._refresh_compare()

    def _detail_stack(self, title: str, item_id: str, text: str):
        frame = QFrame()
        frame.setObjectName("DetailStack")
        row = QHBoxLayout(frame)
        icon = QLabel()
        icon.setFixedSize(52, 52)
        icon.setPixmap(self.textures.pixmap(item_id, 50))
        row.addWidget(icon)
        labels = QVBoxLayout()
        kicker = QLabel(title.upper())
        kicker.setObjectName("DeckLabel")
        labels.addWidget(kicker)
        value = QLabel(_human_stack(text))
        value.setWordWrap(True)
        labels.addWidget(value)
        row.addLayout(labels, 1)
        return frame

    def _toggle_favorite(self):
        trade = self._selected_trade()
        if trade is None or self.settings is None:
            return
        key = trade_key(trade)
        values = list(getattr(self.settings, "favorite_trades", []) or [])
        if key in values:
            values = [value for value in values if value != key]
        else:
            values.append(key)
        self.settings.favorite_trades = values
        self.settings.save()
        self._show_selected()
        if self.favorites_only.isChecked():
            self.refresh()

    def _toggle_compare(self):
        trade = self._selected_trade()
        if trade is None:
            return
        key = trade_key(trade)
        if key in self.compare_keys:
            self.compare_keys.remove(key)
        else:
            if len(self.compare_keys) >= 3:
                self.compare_keys.pop(0)
            self.compare_keys.append(key)
        self._show_selected()

    def _clear_compare(self):
        self.compare_keys.clear()
        self._refresh_compare()
        self._show_selected()

    def _refresh_compare(self):
        self.compare_list.clear()
        uses = self.uses.value()
        all_trades = {trade_key(trade): trade for trade in self.trades}
        for key in self.compare_keys:
            trade = all_trades.get(key)
            if trade is None:
                continue
            emeralds = _emerald_cost(trade)
            cost = f" • {emeralds * uses:g} emeralds / {uses} uses" if emeralds is not None else ""
            self.compare_list.addItem(
                f"{trade.profession.title()} {LEVEL_NAMES.get(trade.level, trade.level)} — {_human_stack(trade.gives)}{cost}"
            )


def _normal(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "-")


def _human_item(value: str) -> str:
    text = str(value or "trade").removeprefix("minecraft:").replace("_", " ").strip()
    return " ".join(word.capitalize() if word.lower() not in {"of", "the"} else word.lower() for word in text.split())


def _human_stack(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "—"
    match = re.match(r"^([^ ]+)\s+(.+)$", text)
    if not match:
        return _human_item(text)
    return f"{match.group(1)} × {_human_item(match.group(2))}"


def _numeric_count(value: str) -> float | None:
    text = str(value or "").strip()
    if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return float(text)
    return None


def _emerald_cost(trade: Trade) -> float | None:
    total = 0.0
    found = False
    if trade.wants_id == "emerald":
        value = _numeric_count(trade.wants_count)
        if value is not None:
            total += value
            found = True
    if trade.additional_wants_id == "emerald":
        value = _numeric_count(trade.additional_wants_count)
        if value is not None:
            total += value
            found = True
    return total if found else None
