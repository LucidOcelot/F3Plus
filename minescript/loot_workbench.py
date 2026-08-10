from __future__ import annotations

"""Full canonical loot explorer UI.

This is the rich pre-rewrite workflow rebuilt against the canonical simulator engine:
installed table browsing, reachable-item inspection, context controls and repeatable
simulation stay in one workspace without any runtime installer/monkeypatch layer.
"""

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QSpinBox, QSplitter, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from .minecraft_simulators import LootTableEngine, MinecraftJarData, loot_category
from .pixel_art import icon_pixmap
from .ui_theme import palette


def _clean_item(value: str) -> str:
    return str(value or "").removeprefix("minecraft:").replace("/", "_")


def _set_headers(table: QTableWidget, headers: list[str]):
    table.setColumnCount(len(headers)); table.setHorizontalHeaderLabels(headers); table.verticalHeader().setVisible(False); table.setAlternatingRowColors(True); table.setSelectionBehavior(QAbstractItemView.SelectRows); table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    if headers: table.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.Stretch)


class _Icons:
    def __init__(self, owner, data: MinecraftJarData):
        self.owner = owner; self.data = data; self.colors = palette(owner.settings.theme, owner.settings.custom_palette); self.cache = {}

    def pixmap(self, item: str, size=26, fallback="loot"):
        key = (item, size, fallback)
        if key in self.cache: return self.cache[key]
        clean = _clean_item(item); raw, _ = self.data.texture_bytes((f"assets/minecraft/textures/item/{clean}.png", f"assets/minecraft/textures/block/{clean}.png")); pix = QPixmap()
        if raw and pix.loadFromData(raw): pix = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation)
        if pix.isNull(): pix = icon_pixmap(fallback, self.colors, size)
        self.cache[key] = pix; return pix

    def icon(self, item: str, size=26, fallback="loot"): return QIcon(self.pixmap(item, size, fallback))


class LootWorkbenchDialog(QDialog):
    def __init__(self, owner, mode_name: str = "Loot Table Simulator"):
        super().__init__(owner)
        self.owner = owner; self.mode_name = str(mode_name or ""); self.data = None; self.engine = None; self.icons = None
        self.setWindowTitle("Loot & Drop Workbench"); self.resize(1460, 890); self.setMinimumSize(1080, 700)
        root = QVBoxLayout(self); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(8)

        hero = QFrame(); hero.setObjectName("ExplorerHero"); hb = QHBoxLayout(hero)
        titles = QVBoxLayout(); title = QLabel("Loot Table Explorer"); title.setObjectName("WorkspaceTitle"); titles.addWidget(title)
        subtitle = QLabel("Browse installed vanilla loot tables, inspect recursively reachable items and run repeatable simulations without modifying Minecraft."); subtitle.setWordWrap(True); subtitle.setObjectName("Muted"); titles.addWidget(subtitle); hb.addLayout(titles, 1)
        self.source = QLabel("Loading installed Minecraft loot data…"); self.source.setObjectName("VersionChip"); hb.addWidget(self.source); root.addWidget(hero)

        filters = QHBoxLayout(); self.category = QComboBox(); self.category.addItem("All"); self.search = QLineEdit(); self.search.setClearButtonEnabled(True); self.search.setPlaceholderText("Search tables: chest, fishing, zombie, piglin, trial…")
        self.contextual = QCheckBox("Include context-dependent branches"); self.contextual.setChecked(True); self.killed = QCheckBox("Killed by player"); self.killed.setChecked(True)
        filters.addWidget(QLabel("Category")); filters.addWidget(self.category); filters.addWidget(self.search, 1); filters.addWidget(self.contextual); filters.addWidget(self.killed); root.addLayout(filters)

        split = QSplitter(Qt.Horizontal); split.setChildrenCollapsible(False); root.addWidget(split, 1)
        left = QFrame(); left.setObjectName("ExplorerRail"); lb = QVBoxLayout(left); lt = QLabel("LOOT TABLES"); lt.setObjectName("DeckLabel"); lb.addWidget(lt); self.tables = QListWidget(); self.tables.setIconSize(QSize(24, 24)); lb.addWidget(self.tables, 1); self.table_count = QLabel("Loading…"); self.table_count.setObjectName("Muted"); lb.addWidget(self.table_count); split.addWidget(left)

        middle = QFrame(); middle.setObjectName("ExplorerTrades"); mb = QVBoxLayout(middle); mt = QLabel("ALL POSSIBLE LOOT"); mt.setObjectName("DeckLabel"); mb.addWidget(mt); self.table_title = QLabel("Choose a loot table"); self.table_title.setObjectName("WorkspaceTitle"); self.table_title.setWordWrap(True); mb.addWidget(self.table_title)
        explanation = QLabel("Nested loot-table references and item tags are expanded. Weight is structural/nominal; context-dependent predicates and functions are shown instead of being converted into a fake universal percentage."); explanation.setWordWrap(True); explanation.setObjectName("Muted"); mb.addWidget(explanation)
        self.possible = QTableWidget(); _set_headers(self.possible, ["Item", "Weight", "Pool", "Count", "Conditions", "Functions"]); self.possible.setIconSize(QSize(28, 28)); mb.addWidget(self.possible, 1); split.addWidget(middle)

        right = QFrame(); right.setObjectName("ExplorerFilters"); rb = QVBoxLayout(right); rt = QLabel("SIMULATION"); rt.setObjectName("DeckLabel"); rb.addWidget(rt)
        sim_help = QLabel("Run deterministic pulls from the selected table. Random-chance predicates are simulated; branches requiring real game context remain potentially eligible when the context toggle is enabled."); sim_help.setWordWrap(True); sim_help.setObjectName("Muted"); rb.addWidget(sim_help)
        form = QGridLayout(); self.seed = QSpinBox(); self.seed.setRange(-2_000_000_000, 2_000_000_000); self.seed.setValue(12345); self.custom_pulls = QSpinBox(); self.custom_pulls.setRange(1, 1_000_000); self.custom_pulls.setValue(1000); form.addWidget(QLabel("Simulation seed"),0,0); form.addWidget(self.seed,0,1); form.addWidget(QLabel("Custom pulls"),1,0); form.addWidget(self.custom_pulls,1,1); rb.addLayout(form)
        buttons = QHBoxLayout()
        for text, count in (("Roll once",1),("Roll 10",10),("Roll 1,000",1000)):
            button = QPushButton(text); button.clicked.connect(lambda _=False, n=count: self.run_sim(n)); buttons.addWidget(button)
        custom = QPushButton("Run custom"); custom.setObjectName("PrimaryButton"); custom.clicked.connect(lambda: self.run_sim(self.custom_pulls.value())); buttons.addWidget(custom); rb.addLayout(buttons)
        self.summary = QLabel("Choose a table to simulate."); self.summary.setWordWrap(True); self.summary.setObjectName("Muted"); rb.addWidget(self.summary)
        self.stats = QTableWidget(); _set_headers(self.stats, ["Item", "Hit rate", "Mean / pull", "Total"]); self.stats.setIconSize(QSize(24,24)); rb.addWidget(self.stats,1); split.addWidget(right); split.setSizes([290, 690, 440])

        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close)
        self.category.currentTextChanged.connect(self.refresh_tables); self.search.textChanged.connect(self.refresh_tables); self.tables.currentItemChanged.connect(self.load_current)
        self._set_enabled(False); QTimer.singleShot(0, self._load_engine)

    def _set_enabled(self, enabled: bool):
        for widget in (self.category, self.search, self.contextual, self.killed, self.tables, self.possible, self.seed, self.custom_pulls, self.stats): widget.setEnabled(enabled)

    def _load_engine(self):
        try:
            self.data = MinecraftJarData(self.owner.settings.minecraft_version); self.engine = LootTableEngine(self.data); self.icons = _Icons(self.owner, self.data)
            self.source.setText(self.engine.source); self.category.blockSignals(True); self.category.clear(); self.category.addItems(self.engine.categories()); self.category.blockSignals(False); self._set_enabled(True); self._apply_preset(); self.refresh_tables()
        except Exception as exc:
            self.source.setText("Loot data unavailable"); self.table_count.setText(str(exc)); self.summary.setText("The loot explorer could not load the selected data source. Other F3+ workbenches remain available.")

    def _apply_preset(self):
        low = self.mode_name.lower(); wanted = ""
        if "fishing" in low: wanted = "Fishing"
        elif "piglin" in low or "barter" in low: wanted = "Piglin bartering"
        elif "mob drop" in low: wanted = "Entity drops"
        elif "archaeology" in low: wanted = "Archaeology"
        elif "trial" in low: wanted = "Trial / spawner rewards"
        elif "structure" in low: wanted = "Chests"
        if wanted:
            index = self.category.findText(wanted)
            if index >= 0: self.category.setCurrentIndex(index)

    def _category_icon(self, table_id: str):
        category = loot_category(table_id)
        item = "chest"
        if category == "Fishing": item = "fishing_rod"
        elif category == "Piglin bartering": item = "gold_ingot"
        elif category == "Entity drops": item = "rotten_flesh"
        elif category == "Archaeology": item = "brush"
        elif category == "Trial / spawner rewards": item = "trial_key"
        elif category == "Block drops": item = "diamond_pickaxe"
        return self.icons.icon(item, 24) if self.icons else QIcon()

    def refresh_tables(self):
        if self.engine is None: return
        current = self.tables.currentItem().data(Qt.UserRole) if self.tables.currentItem() else ""; rows = self.engine.table_ids(self.category.currentText(), self.search.text()); self.tables.blockSignals(True); self.tables.clear(); selected = -1
        for index, table_id in enumerate(rows):
            item = QListWidgetItem(self._category_icon(table_id), table_id.split(":",1)[-1]); item.setData(Qt.UserRole, table_id); item.setToolTip(f"{loot_category(table_id)}\n{table_id}"); self.tables.addItem(item)
            if table_id == current: selected = index
        self.tables.blockSignals(False); self.table_count.setText(f"{len(rows):,} tables shown")
        if rows: self.tables.setCurrentRow(selected if selected >= 0 else 0)
        else: self.possible.setRowCount(0); self.table_title.setText("No loot tables match the current filters")

    def load_current(self, *_):
        if self.engine is None: return
        item = self.tables.currentItem()
        if item is None: return
        table_id = item.data(Qt.UserRole); rows = self.engine.possible_items(table_id); self.table_title.setText(f"{table_id}  •  {loot_category(table_id)}  •  {len(rows):,} reachable item types"); self.possible.setRowCount(len(rows))
        for r, row in enumerate(rows):
            first = QTableWidgetItem(self.icons.icon(row["item"], 28) if self.icons else QIcon(), str(row["item"]).removeprefix("minecraft:")); self.possible.setItem(r,0,first)
            for c, key in enumerate(("weight","pools","count","conditions","functions"),1):
                value = row[key]; self.possible.setItem(r,c,QTableWidgetItem(f"{value:g}" if isinstance(value,float) else str(value)))
        self.stats.setRowCount(0); self.summary.setText("Choose a pull count to simulate this table.")

    def run_sim(self, pulls: int):
        if self.engine is None: return
        item = self.tables.currentItem()
        if item is None: return
        table_id = item.data(Qt.UserRole); self.summary.setText(f"Simulating {pulls:,} pulls…"); QApplication = None
        try:
            from PySide6.QtWidgets import QApplication as _QApplication
            QApplication = _QApplication; QApplication.processEvents()
            result = self.engine.simulate(table_id, pulls, self.seed.value(), {"killed_by_player": self.killed.isChecked(), "include_contextual_entries": self.contextual.isChecked()}); rows = result["stats"]; self.stats.setRowCount(len(rows))
            for r, row in enumerate(rows):
                first = QTableWidgetItem(self.icons.icon(row["item"],24) if self.icons else QIcon(), str(row["item"]).removeprefix("minecraft:")); self.stats.setItem(r,0,first); self.stats.setItem(r,1,QTableWidgetItem(f"{row['observed_hit_rate']*100:.3f}%")); self.stats.setItem(r,2,QTableWidgetItem(f"{row['mean_items_per_pull']:.4f}")); self.stats.setItem(r,3,QTableWidgetItem(str(row["total_items"])))
            self.summary.setText(f"{pulls:,} pulls • seed {self.seed.value()} • {len(rows):,} item types observed • {self.engine.source}")
        except Exception as exc:
            self.summary.setText(f"Simulation failed: {exc}")
