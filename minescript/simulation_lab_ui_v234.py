from __future__ import annotations

"""Advanced Qt explorers for Minecraft data/mechanic simulation.

All Minecraft artwork is read from a locally installed Java JAR at runtime. Original
F3+ pixel art is used when the selected texture is unavailable, so every control keeps
an identifiable icon without bundling Mojang assets.
"""

import json
from typing import Any


SIMULATOR_ICON_CANDIDATES = {
    "loot": (
        "assets/minecraft/textures/block/chest_front.png",
        "assets/minecraft/textures/item/chest.png",
        "assets/minecraft/textures/item/fishing_rod.png",
    ),
    "enchant": (
        "assets/minecraft/textures/item/enchanted_book.png",
        "assets/minecraft/textures/block/enchanting_table_top.png",
        "assets/minecraft/textures/item/book.png",
    ),
    "anvil": (
        "assets/minecraft/textures/block/anvil_top.png",
        "assets/minecraft/textures/item/iron_ingot.png",
    ),
    "brewing": (
        "assets/minecraft/textures/item/brewing_stand.png",
        "assets/minecraft/textures/item/blaze_powder.png",
        "assets/minecraft/textures/item/potion.png",
    ),
    "dye": (
        "assets/minecraft/textures/item/leather_chestplate.png",
        "assets/minecraft/textures/item/red_dye.png",
    ),
    "animal": (
        "assets/minecraft/textures/item/horse_spawn_egg.png",
        "assets/minecraft/textures/item/golden_carrot.png",
        "assets/minecraft/textures/item/wheat.png",
    ),
}


def _clean_item(item_id: str) -> str:
    return str(item_id or "").removeprefix("minecraft:").replace("/", "_")


def install() -> None:
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QAction, QColor, QIcon, QPixmap
    from PySide6.QtWidgets import (
        QAbstractItemView, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFrame,
        QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
        QListWidget, QListWidgetItem, QMenu, QPushButton, QPlainTextEdit, QScrollArea,
        QSpinBox, QSplitter, QStackedWidget, QTabWidget, QTableWidget,
        QTableWidgetItem, QVBoxLayout, QWidget,
    )

    from .app import F3Plus
    from .minecraft_simulators_v234 import (
        AnimalBreedingEngine, AnvilEngine, BASE_POTIONS, BREEDABLE_ANIMALS,
        BrewingEngine, DYE_COLORS, EnchantingEngine, HorseBreedingEngine,
        LEATHER_DEFAULT, LootTableEngine, MinecraftJarData, PotionState,
        cauldron_wash, dye_mix, loot_category,
    )
    from .pixel_art import icon_pixmap
    from .ui_theme import palette

    if getattr(F3Plus, "_simulation_lab_v234_installed", False):
        return

    class AssetIcons:
        def __init__(self, owner):
            self.owner = owner
            self.data = MinecraftJarData(owner.settings.minecraft_version)
            self.colors = palette(owner.settings.theme, owner.settings.custom_palette)
            self.cache: dict[tuple[str, int], QPixmap] = {}

        def _fallback(self, kind: str, size: int) -> QPixmap:
            fallback = {
                "loot": "loot", "enchant": "enchant", "anvil": "anvil",
                "brewing": "brewing", "dye": "dye", "animal": "animal",
            }.get(kind, kind)
            return icon_pixmap(fallback, self.colors, size)

        def pixmap(self, kind: str, size: int = 32) -> QPixmap:
            key = (str(kind), int(size))
            if key in self.cache:
                return self.cache[key]
            data, _member = self.data.texture_bytes(SIMULATOR_ICON_CANDIDATES.get(str(kind), ()))
            pix = QPixmap()
            if data and pix.loadFromData(data):
                pix = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation)
            if pix.isNull():
                pix = self._fallback(kind, size)
            self.cache[key] = pix
            return pix

        def item(self, item_id: str, size: int = 28, fallback: str = "loot") -> QPixmap:
            clean = _clean_item(item_id)
            key = (f"item:{clean}:{fallback}", int(size))
            if key in self.cache:
                return self.cache[key]
            candidates = (
                f"assets/minecraft/textures/item/{clean}.png",
                f"assets/minecraft/textures/block/{clean}.png",
            )
            data, _member = self.data.texture_bytes(candidates)
            pix = QPixmap()
            if data and pix.loadFromData(data):
                pix = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation)
            if pix.isNull():
                pix = self._fallback(fallback, size)
            self.cache[key] = pix
            return pix

        def icon(self, kind: str, size: int = 28) -> QIcon:
            return QIcon(self.pixmap(kind, size))

        def item_icon(self, item_id: str, size: int = 28, fallback: str = "loot") -> QIcon:
            return QIcon(self.item(item_id, size, fallback))

    def section(title: str, subtitle: str = "") -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("ResultSection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 12)
        heading = QLabel(title)
        heading.setObjectName("WorkspaceTitle")
        layout.addWidget(heading)
        if subtitle:
            note = QLabel(subtitle)
            note.setObjectName("Muted")
            note.setWordWrap(True)
            layout.addWidget(note)
        return frame, layout

    def metric(label: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("MetricCard")
        box = QVBoxLayout(card)
        box.setContentsMargins(8, 6, 8, 6)
        a = QLabel(label.upper()); a.setObjectName("DeckLabel")
        b = QLabel(value); b.setObjectName("MetricValue")
        box.addWidget(a); box.addWidget(b)
        return card

    def set_table_headers(table: QTableWidget, headers: list[str]) -> None:
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        if headers:
            table.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    class LootTableExplorer(QDialog):
        def __init__(self, owner, preset: str = ""):
            super().__init__(owner)
            self.owner = owner
            self.icons = AssetIcons(owner)
            self.engine = LootTableEngine(self.icons.data)
            self.preset = str(preset or "")
            self.setWindowTitle("F3+ Loot Table Explorer")
            self.setWindowIcon(self.icons.icon("loot", 40))
            self.resize(1480, 900)
            root = QVBoxLayout(self)
            root.setContentsMargins(12, 12, 12, 12)
            root.setSpacing(8)

            hero = QFrame(); hero.setObjectName("ExplorerHero")
            hero_box = QHBoxLayout(hero)
            icon = QLabel(); icon.setPixmap(self.icons.pixmap("loot", 54)); hero_box.addWidget(icon)
            titles = QVBoxLayout()
            h = QLabel("Loot Table Explorer"); h.setObjectName("WorkspaceTitle")
            s = QLabel("Browse every installed vanilla loot table, inspect all recursively reachable loot, and run repeatable simulated pulls without modifying Minecraft.")
            s.setWordWrap(True); s.setObjectName("Muted")
            titles.addWidget(h); titles.addWidget(s); hero_box.addLayout(titles, 1)
            self.source_badge = QLabel(self.engine.source); self.source_badge.setObjectName("VersionChip")
            self.source_badge.setToolTip("Loot definitions are read directly from the installed client JAR when available. Bundled examples are labeled as baseline data.")
            hero_box.addWidget(self.source_badge)
            root.addWidget(hero)

            filters = QHBoxLayout()
            self.category = QComboBox(); self.category.addItems(self.engine.categories())
            self.search = QLineEdit(); self.search.setPlaceholderText("Search loot tables: chest, fishing, zombie, piglin, trial…")
            self.contextual = QCheckBox("Include context-dependent branches"); self.contextual.setChecked(True)
            self.killed_by_player = QCheckBox("Killed by player"); self.killed_by_player.setChecked(True)
            filters.addWidget(QLabel("Category")); filters.addWidget(self.category)
            filters.addWidget(self.search, 1); filters.addWidget(self.contextual); filters.addWidget(self.killed_by_player)
            root.addLayout(filters)

            splitter = QSplitter(Qt.Horizontal); splitter.setChildrenCollapsible(False)
            root.addWidget(splitter, 1)

            left, left_box = section("Loot tables", "Installed data is grouped by source type; fishing and referenced tables remain individually inspectable.")
            self.tables = QListWidget(); self.tables.setIconSize(QSize(24, 24)); left_box.addWidget(self.tables, 1)
            splitter.addWidget(left)

            middle, middle_box = section("All possible loot", "This list expands nested loot-table references and item tags. Weight is structural/nominal; conditions and functions are shown separately instead of being hidden inside a fake exact percentage.")
            self.table_title = QLabel("Choose a loot table")
            self.table_title.setObjectName("DeckLabel")
            middle_box.addWidget(self.table_title)
            self.possible = QTableWidget(); set_table_headers(self.possible, ["Item", "Weight", "Pool", "Count", "Conditions", "Functions"])
            self.possible.setIconSize(QSize(28, 28)); middle_box.addWidget(self.possible, 1)
            splitter.addWidget(middle)

            right, right_box = section("Simulation", "Run one pull or a large Monte Carlo sample. Random-chance predicates are simulated; predicates that require a real loot context remain eligible when the context toggle is enabled.")
            controls = QGridLayout()
            self.seed = QSpinBox(); self.seed.setRange(-2_000_000_000, 2_000_000_000); self.seed.setValue(12345)
            self.custom_pulls = QSpinBox(); self.custom_pulls.setRange(1, 1_000_000); self.custom_pulls.setValue(1000)
            controls.addWidget(QLabel("Simulation seed"), 0, 0); controls.addWidget(self.seed, 0, 1)
            controls.addWidget(QLabel("Custom pulls"), 1, 0); controls.addWidget(self.custom_pulls, 1, 1)
            right_box.addLayout(controls)
            button_row = QHBoxLayout()
            for text, count in (("Roll once", 1), ("Roll 10", 10), ("Roll 1,000", 1000)):
                button = QPushButton(text); button.setIcon(self.icons.icon("loot", 18)); button.clicked.connect(lambda _=False, n=count: self.run_sim(n)); button_row.addWidget(button)
            custom = QPushButton("Run custom"); custom.clicked.connect(lambda: self.run_sim(self.custom_pulls.value())); button_row.addWidget(custom)
            right_box.addLayout(button_row)
            self.sim_summary = QLabel("No simulation has been run."); self.sim_summary.setObjectName("Muted"); self.sim_summary.setWordWrap(True); right_box.addWidget(self.sim_summary)
            self.stats = QTableWidget(); set_table_headers(self.stats, ["Item", "Hit rate", "Mean / pull", "Total"]); self.stats.setIconSize(QSize(24,24)); right_box.addWidget(self.stats, 1)
            self.examples = QPlainTextEdit(); self.examples.setReadOnly(True); self.examples.setPlaceholderText("Example pulls appear here."); self.examples.setMaximumHeight(190); right_box.addWidget(self.examples)
            splitter.addWidget(right)
            splitter.setSizes([280, 690, 470])

            self.category.currentTextChanged.connect(self.refresh_tables)
            self.search.textChanged.connect(self.refresh_tables)
            self.tables.currentItemChanged.connect(self.load_current)
            self.refresh_tables()
            self.apply_preset()

        def _category_icon(self, table_id: str) -> QIcon:
            category = loot_category(table_id)
            if category == "Fishing": return self.icons.item_icon("fishing_rod", 24, "loot")
            if category == "Piglin bartering": return self.icons.item_icon("gold_ingot", 24, "loot")
            if category == "Entity drops": return self.icons.item_icon("rotten_flesh", 24, "animal")
            if category == "Archaeology": return self.icons.item_icon("brush", 24, "loot")
            if category == "Trial / spawner rewards": return self.icons.item_icon("trial_key", 24, "loot")
            if category == "Block drops": return self.icons.item_icon("diamond_pickaxe", 24, "loot")
            return self.icons.icon("loot", 24)

        def refresh_tables(self):
            current = self.tables.currentItem().data(Qt.UserRole) if self.tables.currentItem() else ""
            rows = self.engine.table_ids(self.category.currentText(), self.search.text())
            self.tables.blockSignals(True); self.tables.clear()
            selected = -1
            for index, table_id in enumerate(rows):
                item = QListWidgetItem(self._category_icon(table_id), table_id.split(":", 1)[-1])
                item.setData(Qt.UserRole, table_id)
                item.setToolTip(f"{loot_category(table_id)}\n{table_id}")
                self.tables.addItem(item)
                if table_id == current: selected = index
            self.tables.blockSignals(False)
            if rows:
                self.tables.setCurrentRow(selected if selected >= 0 else 0)

        def apply_preset(self):
            preset = self.preset.lower()
            if not preset:
                return
            category = ""
            query = ""
            if "fishing" in preset: category = "Fishing"
            elif "piglin" in preset or "barter" in preset: category = "Piglin bartering"
            elif "mob drop" in preset: category = "Entity drops"
            elif "archaeology" in preset: category = "Archaeology"
            elif "trial" in preset: category = "Trial / spawner rewards"
            elif "structure" in preset: category = "Chests"
            if category:
                index = self.category.findText(category)
                if index >= 0: self.category.setCurrentIndex(index)
            if query: self.search.setText(query)

        def load_current(self):
            item = self.tables.currentItem()
            if item is None: return
            table_id = item.data(Qt.UserRole)
            rows = self.engine.possible_items(table_id)
            self.table_title.setText(f"{table_id}  •  {loot_category(table_id)}  •  {len(rows)} reachable item types")
            self.possible.setRowCount(len(rows))
            for r, row in enumerate(rows):
                name = QTableWidgetItem(self.icons.item_icon(row["item"], 28, "loot"), row["item"].removeprefix("minecraft:"))
                name.setData(Qt.UserRole, row["item"])
                self.possible.setItem(r, 0, name)
                for c, key in enumerate(("weight", "pools", "count", "conditions", "functions"), start=1):
                    value = row[key]
                    self.possible.setItem(r, c, QTableWidgetItem(f"{value:g}" if isinstance(value, float) else str(value)))
            self.stats.setRowCount(0); self.examples.clear(); self.sim_summary.setText("Choose a pull count to simulate this table.")

        def run_sim(self, pulls: int):
            item = self.tables.currentItem()
            if item is None: return
            table_id = item.data(Qt.UserRole)
            context = {"killed_by_player": self.killed_by_player.isChecked(), "include_contextual_entries": self.contextual.isChecked()}
            result = self.engine.simulate(table_id, pulls, self.seed.value(), context)
            rows = result["stats"]
            self.stats.setRowCount(len(rows))
            for r, row in enumerate(rows):
                first = QTableWidgetItem(self.icons.item_icon(row["item"], 24, "loot"), row["item"].removeprefix("minecraft:")); self.stats.setItem(r, 0, first)
                self.stats.setItem(r, 1, QTableWidgetItem(f"{row['observed_hit_rate'] * 100:.3f}%"))
                self.stats.setItem(r, 2, QTableWidgetItem(f"{row['mean_items_per_pull']:.4f}"))
                self.stats.setItem(r, 3, QTableWidgetItem(f"{row['total_items']:,}"))
            example_lines = []
            for index, pull in enumerate(result["examples"], start=1):
                text = ", ".join(f"{row['count']}× {row['item'].removeprefix('minecraft:')}" + (f" ({row['detail']})" if row['detail'] else "") for row in pull) or "nothing"
                example_lines.append(f"#{index}: {text}")
            self.examples.setPlainText("\n".join(example_lines))
            self.sim_summary.setText(f"{result['pulls']:,} pulls with seed {result['seed']}. {result['context_note']}")

    class EnchantAnvilSimulator(QDialog):
        def __init__(self, owner, start_tab: str = "enchant"):
            super().__init__(owner)
            self.owner = owner; self.icons = AssetIcons(owner)
            self.enchant = EnchantingEngine(self.icons.data); self.anvil = AnvilEngine(self.enchant)
            self.setWindowTitle("F3+ Enchanting Table + Anvil Simulator")
            self.setWindowIcon(self.icons.icon("enchant", 40)); self.resize(1120, 820)
            root = QVBoxLayout(self)
            hero = QFrame(); hero.setObjectName("ExplorerHero"); hb = QHBoxLayout(hero)
            icon = QLabel(); icon.setPixmap(self.icons.pixmap("enchant", 52)); hb.addWidget(icon)
            title_box = QVBoxLayout(); title = QLabel("Enchanting Table + Anvil Simulator"); title.setObjectName("WorkspaceTitle")
            note = QLabel("Roll enchanting-table offers from the installed enchantment registry when available, then plan deterministic anvil enchant merges and prior-work penalties."); note.setWordWrap(True); note.setObjectName("Muted")
            title_box.addWidget(title); title_box.addWidget(note); hb.addLayout(title_box, 1)
            source = QLabel(self.icons.data.source if self.icons.data.jar_path else "Bundled enchanting baseline"); source.setObjectName("VersionChip"); hb.addWidget(source); root.addWidget(hero)
            self.tabs = QTabWidget(); root.addWidget(self.tabs, 1)
            self.tabs.addTab(self._enchant_tab(), self.icons.icon("enchant", 22), "Enchanting Table")
            self.tabs.addTab(self._anvil_tab(), self.icons.icon("anvil", 22), "Anvil")
            if start_tab == "anvil": self.tabs.setCurrentIndex(1)
            self.roll_enchants()

        def _enchant_tab(self):
            page = QWidget(); layout = QVBoxLayout(page)
            controls, cb = section("Table setup", "Bookshelves cap at 15 for the normal table. Seeded rerolls make comparisons repeatable; 0 enchantability means use F3+'s material default for the entered item.")
            form = QGridLayout()
            self.enchant_item = QComboBox(); self.enchant_item.setEditable(True); self.enchant_item.addItems(["diamond_pickaxe", "diamond_sword", "diamond_chestplate", "bow", "fishing_rod", "book"])
            self.bookshelves = QSpinBox(); self.bookshelves.setRange(0,15); self.bookshelves.setValue(15)
            self.enchant_seed = QSpinBox(); self.enchant_seed.setRange(-2_000_000_000,2_000_000_000); self.enchant_seed.setValue(12345)
            self.enchantability = QSpinBox(); self.enchantability.setRange(0,100); self.enchantability.setValue(0)
            form.addWidget(QLabel("Item ID"),0,0); form.addWidget(self.enchant_item,0,1)
            form.addWidget(QLabel("Bookshelves"),0,2); form.addWidget(self.bookshelves,0,3)
            form.addWidget(QLabel("Seed"),1,0); form.addWidget(self.enchant_seed,1,1)
            form.addWidget(QLabel("Enchantability override"),1,2); form.addWidget(self.enchantability,1,3)
            reroll=QPushButton("Roll table offers"); reroll.setIcon(self.icons.icon("enchant",18)); reroll.clicked.connect(self.roll_enchants); form.addWidget(reroll,2,0,1,4)
            cb.addLayout(form); layout.addWidget(controls)
            offers = QHBoxLayout(); self.offer_cards=[]
            for slot in range(1,4):
                card, box=section(f"Slot {slot}")
                icon=QLabel(); icon.setPixmap(self.icons.pixmap("enchant",36)); box.addWidget(icon)
                label=QLabel(); label.setWordWrap(True); box.addWidget(label,1)
                self.offer_cards.append(label); offers.addWidget(card,1)
            layout.addLayout(offers)
            ref, rb=section("Available enchantment definitions", "Installed enchantment JSON supplies weight, max level, anvil cost and supported-item tags where the selected version exposes them.")
            self.enchant_ref=QTableWidget(); set_table_headers(self.enchant_ref,["Enchantment","Weight","Max","Anvil","Supported items"]); rb.addWidget(self.enchant_ref,1); layout.addWidget(ref,1)
            return page

        def roll_enchants(self):
            item=self.enchant_item.currentText().strip() or "book"; override=self.enchantability.value() or None
            offers=self.enchant.roll_offers(item,self.bookshelves.value(),self.enchant_seed.value(),override)
            for label,offer in zip(self.offer_cards,offers):
                names = ", ".join(f"{row['id'].removeprefix('minecraft:').replace('_',' ').title()} {row['level']}" for row in offer['enchantments']) or "No valid enchantment candidates"
                label.setText(f"Displayed level: {offer['displayed_cost']}\nLapis / levels spent: {offer['lapis_cost']} / {offer['levels_spent']}\nModified power: {offer['modified_power']}\nEnchantability: {offer['enchantability']}\n\n{names}")
            rows=self.enchant.enchantment_rows(item); self.enchant_ref.setRowCount(len(rows))
            for r,row in enumerate(rows):
                values=[row['id'].removeprefix('minecraft:'),row['weight'],row['max_level'],row['anvil_cost'],row['supported_items']]
                for c,value in enumerate(values): self.enchant_ref.setItem(r,c,QTableWidgetItem(json.dumps(value,separators=(',',':')) if isinstance(value,(dict,list)) else str(value)))

        def _anvil_tab(self):
            page=QWidget(); layout=QVBoxLayout(page)
            setup, sb=section("Anvil inputs", "Enter enchantments as JSON objects such as {\"minecraft:efficiency\":4}. Prior work is the number of previous anvil operations, not the already-expanded penalty value.")
            grid=QGridLayout()
            self.anvil_item=QLineEdit("diamond_pickaxe")
            self.left_json=QPlainTextEdit('{"minecraft:efficiency":4,"minecraft:unbreaking":3}')
            self.right_json=QPlainTextEdit('{"minecraft:efficiency":4,"minecraft:fortune":3}')
            self.left_json.setMaximumHeight(90); self.right_json.setMaximumHeight(90)
            self.left_prior=QSpinBox(); self.left_prior.setRange(0,20)
            self.right_prior=QSpinBox(); self.right_prior.setRange(0,20)
            self.rename=QCheckBox("Rename item (+1 level)")
            grid.addWidget(QLabel("Item"),0,0); grid.addWidget(self.anvil_item,0,1,1,3)
            grid.addWidget(QLabel("Left item enchantments"),1,0); grid.addWidget(self.left_json,1,1,1,3)
            grid.addWidget(QLabel("Right/book enchantments"),2,0); grid.addWidget(self.right_json,2,1,1,3)
            grid.addWidget(QLabel("Left prior operations"),3,0); grid.addWidget(self.left_prior,3,1)
            grid.addWidget(QLabel("Right prior operations"),3,2); grid.addWidget(self.right_prior,3,3)
            grid.addWidget(self.rename,4,0,1,2)
            run=QPushButton("Simulate anvil merge"); run.setIcon(self.icons.icon("anvil",18)); run.clicked.connect(self.run_anvil); grid.addWidget(run,4,2,1,2)
            sb.addLayout(grid); layout.addWidget(setup)
            metrics=QHBoxLayout(); self.anvil_total=metric("Total level cost","—"); self.anvil_penalty=metric("New prior-work penalty","—"); self.anvil_status=metric("Survival status","—")
            metrics.addWidget(self.anvil_total); metrics.addWidget(self.anvil_penalty); metrics.addWidget(self.anvil_status); layout.addLayout(metrics)
            result, rb=section("Merge details")
            self.anvil_changes=QTableWidget(); set_table_headers(self.anvil_changes,["Enchantment","Current","Incoming","Result","Cost multiplier"]); rb.addWidget(self.anvil_changes,1)
            self.anvil_note=QLabel(); self.anvil_note.setWordWrap(True); self.anvil_note.setObjectName("Muted"); rb.addWidget(self.anvil_note); layout.addWidget(result,1)
            return page

        def run_anvil(self):
            left=json.loads(self.left_json.toPlainText() or "{}"); right=json.loads(self.right_json.toPlainText() or "{}")
            result=self.anvil.combine(self.anvil_item.text(),left,right,self.left_prior.value(),self.right_prior.value(),self.rename.isChecked())
            self.anvil_total.findChildren(QLabel)[1].setText(str(result['total_level_cost']))
            self.anvil_penalty.findChildren(QLabel)[1].setText(str(result['new_prior_work_penalty']))
            self.anvil_status.findChildren(QLabel)[1].setText("Too Expensive (survival)" if result['survival_too_expensive'] else "Available in survival")
            self.anvil_changes.setRowCount(len(result['changes']))
            for r,row in enumerate(result['changes']):
                vals=[row['enchantment'].removeprefix('minecraft:'),row['from'],row['incoming'],row['result'],row['anvil_multiplier']]
                for c,v in enumerate(vals): self.anvil_changes.setItem(r,c,QTableWidgetItem(str(v)))
            self.anvil_note.setText(result['note']+" Source: "+result['source'])

    class BrewingSimulator(QDialog):
        def __init__(self, owner):
            super().__init__(owner); self.owner=owner; self.icons=AssetIcons(owner); self.engine=BrewingEngine()
            self.setWindowTitle("F3+ Brewing Stand Simulator"); self.setWindowIcon(self.icons.icon("brewing",40)); self.resize(980,720)
            root=QVBoxLayout(self)
            hero=QFrame(); hero.setObjectName("ExplorerHero"); hb=QHBoxLayout(hero)
            icon=QLabel(); icon.setPixmap(self.icons.pixmap("brewing",52)); hb.addWidget(icon)
            titles=QVBoxLayout(); h=QLabel("Brewing Stand Simulator"); h.setObjectName("WorkspaceTitle"); n=QLabel("Preview potion transitions, modifiers, splash/lingering conversion, durations and strength without consuming ingredients."); n.setObjectName("Muted"); n.setWordWrap(True); titles.addWidget(h); titles.addWidget(n); hb.addLayout(titles,1); root.addWidget(hero)
            setup, sb=section("Brewing setup", "Brewing rules are code-defined in Java Edition rather than ordinary loot/recipe JSON, so F3+ labels this as its vanilla brewing-rule baseline.")
            grid=QGridLayout(); self.potion=QComboBox(); self.potion.addItems(sorted(BASE_POTIONS)); self.bottle=QComboBox(); self.bottle.addItems(["potion","splash_potion","lingering_potion"]); self.ingredient=QComboBox(); self.ingredient.addItems(self.engine.ingredients())
            grid.addWidget(QLabel("Input potion"),0,0); grid.addWidget(self.potion,0,1); grid.addWidget(QLabel("Bottle"),0,2); grid.addWidget(self.bottle,0,3); grid.addWidget(QLabel("Ingredient"),1,0); grid.addWidget(self.ingredient,1,1,1,2)
            brew=QPushButton("Brew"); brew.setIcon(self.icons.icon("brewing",18)); brew.clicked.connect(self.run_brew); grid.addWidget(brew,1,3); sb.addLayout(grid); root.addWidget(setup)
            flow=QHBoxLayout(); self.brew_input=section("Input")[0]; self.brew_ingredient=section("Ingredient")[0]; self.brew_output=section("Output")[0]
            for widget in (self.brew_input,self.brew_ingredient,self.brew_output): flow.addWidget(widget,1)
            root.addLayout(flow)
            result, rb=section("Result details"); self.brew_details=QLabel(); self.brew_details.setWordWrap(True); rb.addWidget(self.brew_details); root.addWidget(result)
            recipes, rbox=section("Ingredient reference", "Select any row above to test it; invalid transitions remain unchanged instead of inventing an output.")
            self.recipe_table=QTableWidget(); set_table_headers(self.recipe_table,["Ingredient","Primary use"]); ingredients=self.engine.ingredients(); self.recipe_table.setRowCount(len(ingredients))
            uses={"nether_wart":"Water → Awkward","fermented_spider_eye":"Weakness / corruption","redstone":"Extend duration","glowstone_dust":"Increase strength","gunpowder":"Potion → Splash","dragon_breath":"Splash → Lingering"}
            from .minecraft_simulators_v234 import AWKWARD_RECIPES
            for r,ing in enumerate(ingredients):
                first=QTableWidgetItem(self.icons.item_icon(ing,24,"brewing"),ing.replace('_',' ').title()); self.recipe_table.setItem(r,0,first); self.recipe_table.setItem(r,1,QTableWidgetItem(uses.get(ing,"Awkward → "+AWKWARD_RECIPES.get(ing,"effect").replace('_',' ').title())))
            rbox.addWidget(self.recipe_table,1); root.addWidget(recipes,1); self.run_brew()

        def _fill_card(self, card: QFrame, item_id: str, title: str, text: str, kind="brewing"):
            box=card.layout();
            while box.count():
                child=box.takeAt(0); w=child.widget();
                if w is not None: w.deleteLater()
            icon=QLabel(); icon.setPixmap(self.icons.item(item_id,48,kind)); icon.setAlignment(Qt.AlignCenter); box.addWidget(icon)
            h=QLabel(title); h.setObjectName("DeckLabel"); h.setAlignment(Qt.AlignCenter); box.addWidget(h)
            t=QLabel(text); t.setWordWrap(True); t.setAlignment(Qt.AlignCenter); box.addWidget(t)

        def run_brew(self):
            base=BASE_POTIONS[self.potion.currentText()]; state=PotionState(base.potion,base.effect,base.duration_seconds,base.amplifier,self.bottle.currentText())
            result=self.engine.brew(state,self.ingredient.currentText()); out=result['output']
            self._fill_card(self.brew_input,state.bottle,state.potion.replace('_',' ').title(),f"{state.effect}\n{state.duration_seconds if state.duration_seconds is not None else '—'} s")
            self._fill_card(self.brew_ingredient,self.ingredient.currentText(),self.ingredient.currentText().replace('_',' ').title(),"Brewing ingredient")
            self._fill_card(self.brew_output,out.bottle,out.potion.replace('_',' ').title(),f"{out.effect}\nAmplifier {out.amplifier + 1 if out.effect != 'None' else '—'}\n{out.duration_seconds if out.duration_seconds is not None else '—'} s")
            self.brew_details.setText(result['note']+"\n\nSource: "+result['source'])

    class DyeCauldronSimulator(QDialog):
        def __init__(self, owner):
            super().__init__(owner); self.owner=owner; self.icons=AssetIcons(owner); self.sequence=[]
            self.setWindowTitle("F3+ Cauldron + Leather Dye Mixer"); self.setWindowIcon(self.icons.icon("dye",40)); self.resize(960,720)
            root=QVBoxLayout(self)
            hero=QFrame(); hero.setObjectName("ExplorerHero"); hb=QHBoxLayout(hero); icon=QLabel(); icon.setPixmap(self.icons.pixmap("dye",52)); hb.addWidget(icon)
            tb=QVBoxLayout(); h=QLabel("Cauldron + Leather Dye Mixer"); h.setObjectName("WorkspaceTitle"); n=QLabel("Mix Java Edition leather RGB colors using the brightness-preserving dye formula, then model water-cauldron washing separately."); n.setObjectName("Muted"); n.setWordWrap(True); tb.addWidget(h); tb.addWidget(n); hb.addLayout(tb,1); root.addWidget(hero)
            tabs=QTabWidget(); root.addWidget(tabs,1)
            tabs.addTab(self._dye_tab(),self.icons.icon("dye",22),"Leather dye mixing")
            tabs.addTab(self._cauldron_tab(),self.icons.item_icon("cauldron",22,"dye"),"Cauldron")
            self.update_mix()

        def _dye_tab(self):
            page=QWidget(); layout=QVBoxLayout(page)
            setup, sb=section("Dye sequence", "Add dyes in any quantity. Repeated dyes count repeatedly in the average. Enable existing color when recoloring already-dyed leather; otherwise the new color is produced from the selected dyes alone.")
            row=QHBoxLayout(); self.use_existing=QCheckBox("Include existing leather color"); self.existing=QLineEdit(f"#{LEATHER_DEFAULT:06X}"); self.dye_combo=QComboBox()
            for name in DYE_COLORS: self.dye_combo.addItem(self.icons.item_icon(name+"_dye",22,"dye"),name.replace('_',' ').title(),name)
            add=QPushButton("Add dye"); add.clicked.connect(self.add_dye); remove=QPushButton("Remove last"); remove.clicked.connect(self.remove_dye); clear=QPushButton("Clear"); clear.clicked.connect(self.clear_dyes)
            row.addWidget(self.use_existing); row.addWidget(self.existing); row.addWidget(self.dye_combo,1); row.addWidget(add); row.addWidget(remove); row.addWidget(clear); sb.addLayout(row)
            self.sequence_label=QLabel("No dyes selected."); self.sequence_label.setWordWrap(True); sb.addWidget(self.sequence_label); layout.addWidget(setup)
            result, rb=section("Result color")
            self.color_preview=QFrame(); self.color_preview.setMinimumHeight(190); rb.addWidget(self.color_preview)
            self.color_text=QLabel(); self.color_text.setAlignment(Qt.AlignCenter); self.color_text.setObjectName("MetricValue"); rb.addWidget(self.color_text); layout.addWidget(result,1)
            self.use_existing.toggled.connect(self.update_mix); self.existing.textChanged.connect(self.update_mix)
            return page

        def _cauldron_tab(self):
            page=QWidget(); layout=QVBoxLayout(page); setup,sb=section("Water cauldron", "Java Edition water cauldrons wash dyed leather; they do not store a persistent mixed dye color like Bedrock-style colored water mechanics.")
            row=QHBoxLayout(); self.water=QSpinBox(); self.water.setRange(0,3); self.water.setValue(3); self.dyed=QCheckBox("Leather item is dyed"); self.dyed.setChecked(True); wash=QPushButton("Wash leather"); wash.setIcon(self.icons.item_icon("water_bucket",18,"dye")); wash.clicked.connect(self.wash)
            row.addWidget(QLabel("Water level")); row.addWidget(self.water); row.addWidget(self.dyed); row.addWidget(wash); row.addStretch(1); sb.addLayout(row); layout.addWidget(setup)
            result,rb=section("Cauldron result"); self.cauldron_result=QLabel("Choose a water level and wash state."); self.cauldron_result.setWordWrap(True); rb.addWidget(self.cauldron_result); layout.addWidget(result); return page

        def add_dye(self): self.sequence.append(self.dye_combo.currentData()); self.update_mix()
        def remove_dye(self):
            if self.sequence: self.sequence.pop()
            self.update_mix()
        def clear_dyes(self): self.sequence.clear(); self.update_mix()
        def update_mix(self):
            existing=None
            if hasattr(self,"use_existing") and self.use_existing.isChecked():
                try: existing=int(self.existing.text().strip().lstrip('#'),16)
                except ValueError: existing=LEATHER_DEFAULT
            result=dye_mix(existing,self.sequence)
            self.sequence_label.setText(" → ".join(name.replace('_',' ').title() for name in self.sequence) if self.sequence else "No dyes selected.")
            self.color_preview.setStyleSheet(f"background:{result['hex']}; border:2px solid rgba(255,255,255,0.35); border-radius:8px;")
            self.color_text.setText(f"{result['hex']}   RGB {result['rgb'][0]}, {result['rgb'][1]}, {result['rgb'][2]}   decimal {result['decimal']}")
        def wash(self):
            result=cauldron_wash(self.water.value(),self.dyed.isChecked()); self.cauldron_result.setText(f"Water: {result['water_before']} → {result['water_after']}\nWashed: {'Yes' if result['washed'] else 'No'}\n{result['reason']}")

    class BreedingSimulator(QDialog):
        def __init__(self, owner, start_tab: str = "animals"):
            super().__init__(owner); self.owner=owner; self.icons=AssetIcons(owner); self.horses=HorseBreedingEngine(); self.animals=AnimalBreedingEngine()
            self.setWindowTitle("F3+ Animal + Horse Breeding Simulator"); self.setWindowIcon(self.icons.icon("animal",40)); self.resize(1160,840)
            root=QVBoxLayout(self); hero=QFrame(); hero.setObjectName("ExplorerHero"); hb=QHBoxLayout(hero); icon=QLabel(); icon.setPixmap(self.icons.pixmap("animal",52)); hb.addWidget(icon)
            tb=QVBoxLayout(); h=QLabel("Animal + Horse Breeding Simulator"); h.setObjectName("WorkspaceTitle"); n=QLabel("Simulate horse attribute/coat inheritance and inspect breeding-relevant NBT outcomes for the broader Java breedable-animal roster."); n.setObjectName("Muted"); n.setWordWrap(True); tb.addWidget(h); tb.addWidget(n); hb.addLayout(tb,1); root.addWidget(hero)
            self.tabs=QTabWidget(); root.addWidget(self.tabs,1); self.tabs.addTab(self._horse_tab(),self.icons.item_icon("horse_spawn_egg",22,"animal"),"Horse breeding"); self.tabs.addTab(self._animal_tab(),self.icons.icon("animal",22),"All animals / NBT")
            if start_tab=="animals": self.tabs.setCurrentIndex(1)
            self.refresh_species()

        def _horse_fields(self, prefix, grid, row):
            widgets={}
            defaults={"max_health":22.5,"movement_speed":0.225,"jump_strength":0.7}
            for offset,(key,label) in enumerate((("max_health","Max health (HP)"),("movement_speed","Movement speed"),("jump_strength","Jump strength"))):
                spin=QDoubleSpinBox(); spin.setDecimals(5); lo,hi=self.horses.LIMITS[key]; spin.setRange(lo,hi); spin.setValue(defaults[key]); widgets[key]=spin; grid.addWidget(QLabel(label),row+offset,0 if prefix=="A" else 2); grid.addWidget(spin,row+offset,1 if prefix=="A" else 3)
            color=QSpinBox(); color.setRange(0,6); markings=QSpinBox(); markings.setRange(0,4); widgets['color']=color; widgets['markings']=markings
            grid.addWidget(QLabel("Coat color 0–6"),row+3,0 if prefix=="A" else 2); grid.addWidget(color,row+3,1 if prefix=="A" else 3); grid.addWidget(QLabel("Markings 0–4"),row+4,0 if prefix=="A" else 2); grid.addWidget(markings,row+4,1 if prefix=="A" else 3)
            return widgets

        def _horse_tab(self):
            page=QWidget(); layout=QVBoxLayout(page); setup,sb=section("Parent horses", "The attribute model is parent-centered and bounded to vanilla horse attribute limits. Coat color and markings favor either parent with a smaller mutation/random outcome.")
            grid=QGridLayout(); grid.addWidget(QLabel("PARENT A"),0,0,1,2); grid.addWidget(QLabel("PARENT B"),0,2,1,2); self.horse_a=self._horse_fields("A",grid,1); self.horse_b=self._horse_fields("B",grid,1)
            self.horse_children=QSpinBox(); self.horse_children.setRange(1,100000); self.horse_children.setValue(1000); self.horse_seed=QSpinBox(); self.horse_seed.setRange(-2_000_000_000,2_000_000_000); self.horse_seed.setValue(12345); run=QPushButton("Simulate offspring"); run.setIcon(self.icons.item_icon("golden_carrot",18,"animal")); run.clicked.connect(self.run_horses)
            grid.addWidget(QLabel("Children"),6,0); grid.addWidget(self.horse_children,6,1); grid.addWidget(QLabel("Seed"),6,2); grid.addWidget(self.horse_seed,6,3); grid.addWidget(run,7,0,1,4); sb.addLayout(grid); layout.addWidget(setup)
            result,rb=section("Offspring statistics"); self.horse_stats=QTableWidget(); set_table_headers(self.horse_stats,["Attribute","Minimum","Mean","Maximum"]); rb.addWidget(self.horse_stats); self.horse_examples=QPlainTextEdit(); self.horse_examples.setReadOnly(True); self.horse_examples.setMaximumHeight(220); rb.addWidget(self.horse_examples); layout.addWidget(result,1); return page

        def run_horses(self):
            a={k:w.value() for k,w in self.horse_a.items()}; b={k:w.value() for k,w in self.horse_b.items()}; result=self.horses.simulate(a,b,self.horse_children.value(),self.horse_seed.value()); self.horse_stats.setRowCount(len(result['stats']))
            for r,(key,row) in enumerate(result['stats'].items()):
                vals=[key.replace('_',' ').title(),f"{row['minimum']:.5f}",f"{row['mean']:.5f}",f"{row['maximum']:.5f}"]
                for c,v in enumerate(vals): self.horse_stats.setItem(r,c,QTableWidgetItem(v))
            self.horse_examples.setPlainText(result['model']+"\n\nExample offspring NBT:\n"+"\n".join(json.dumps(row,separators=(',',':')) for row in result['examples'][:10]))

        def _animal_tab(self):
            page=QWidget(); layout=QVBoxLayout(page); setup,sb=section("Species + parent NBT", "Parent NBT accepts JSON. F3+ intentionally models breeding-relevant state instead of copying runtime UUIDs, positions, brain memories or unrelated timers into a fictional child.")
            grid=QGridLayout(); self.species=QComboBox()
            for name in self.animals.species(): self.species.addItem(self.icons.item_icon(_clean_item(name)+"_spawn_egg",22,"animal"),name)
            self.food=QLabel(); self.nbt_fields=QLabel(); self.nbt_fields.setWordWrap(True)
            self.parent_a=QPlainTextEdit('{}'); self.parent_b=QPlainTextEdit('{}'); self.parent_a.setMaximumHeight(110); self.parent_b.setMaximumHeight(110)
            self.animal_children=QSpinBox(); self.animal_children.setRange(1,100000); self.animal_children.setValue(100); self.animal_seed=QSpinBox(); self.animal_seed.setRange(-2_000_000_000,2_000_000_000); self.animal_seed.setValue(12345)
            run=QPushButton("Simulate NBT offspring"); run.setIcon(self.icons.icon("animal",18)); run.clicked.connect(self.run_animals)
            grid.addWidget(QLabel("Species"),0,0); grid.addWidget(self.species,0,1); grid.addWidget(QLabel("Breeding food"),0,2); grid.addWidget(self.food,0,3); grid.addWidget(QLabel("Relevant NBT"),1,0); grid.addWidget(self.nbt_fields,1,1,1,3); grid.addWidget(QLabel("Parent A NBT (JSON)"),2,0); grid.addWidget(self.parent_a,2,1,1,3); grid.addWidget(QLabel("Parent B NBT (JSON)"),3,0); grid.addWidget(self.parent_b,3,1,1,3); grid.addWidget(QLabel("Children"),4,0); grid.addWidget(self.animal_children,4,1); grid.addWidget(QLabel("Seed"),4,2); grid.addWidget(self.animal_seed,4,3); grid.addWidget(run,5,0,1,4); sb.addLayout(grid); layout.addWidget(setup)
            result,rb=section("Offspring outcomes"); self.animal_summary=QLabel(); self.animal_summary.setObjectName("Muted"); self.animal_summary.setWordWrap(True); rb.addWidget(self.animal_summary); self.animal_results=QPlainTextEdit(); self.animal_results.setReadOnly(True); rb.addWidget(self.animal_results,1); layout.addWidget(result,1)
            self.species.currentTextChanged.connect(self.refresh_species); return page

        def refresh_species(self):
            if not hasattr(self,"species"): return
            profile=self.animals.profile(self.species.currentText()); self.food.setText(profile.get('food','—')); self.nbt_fields.setText(profile.get('nbt','—'))
            defaults={
                "Horse":('{"max_health":24,"movement_speed":0.24,"jump_strength":0.75,"color":0,"markings":0}','{"max_health":28,"movement_speed":0.28,"jump_strength":0.85,"color":4,"markings":2}'),
                "Sheep":('{"Color":0}','{"Color":14}'), "Axolotl":('{"Variant":0}','{"Variant":2}'), "Rabbit":('{"RabbitType":0}','{"RabbitType":1}'),
            }
            pair=defaults.get(self.species.currentText())
            if pair and self.parent_a.toPlainText().strip()=='{}' and self.parent_b.toPlainText().strip()=='{}': self.parent_a.setPlainText(pair[0]); self.parent_b.setPlainText(pair[1])

        def run_animals(self):
            result=self.animals.simulate(self.species.currentText(),self.parent_a.toPlainText(),self.parent_b.toPlainText(),self.animal_children.value(),self.animal_seed.value()); self.animal_summary.setText(f"{result['children']:,} simulated breeding outcomes • {result['unique_outcomes']:,} unique modeled NBT outcomes. {result['note']}")
            lines=[]
            for row in result['most_common_outcomes']:
                lines.append(f"{row['count']}×  {json.dumps(row['nbt'],sort_keys=True,separators=(',',':'))}")
            self.animal_results.setPlainText("\n".join(lines))

    # ---- app integration -------------------------------------------------

    def open_loot(self, preset=""):
        dialog=LootTableExplorer(self,preset); dialog.exec()

    def open_enchant(self, tab="enchant"):
        dialog=EnchantAnvilSimulator(self,tab); dialog.exec()

    def open_brewing(self):
        dialog=BrewingSimulator(self); dialog.exec()

    def open_dye(self):
        dialog=DyeCauldronSimulator(self); dialog.exec()

    def open_breeding(self, tab="animals"):
        dialog=BreedingSimulator(self,tab); dialog.exec()

    F3Plus.open_loot_table_explorer = open_loot
    F3Plus.open_enchant_anvil_simulator = open_enchant
    F3Plus.open_brewing_simulator = open_brewing
    F3Plus.open_dye_cauldron_simulator = open_dye
    F3Plus.open_breeding_simulator = open_breeding

    previous_build_menu=F3Plus.build_menu
    def build_menu(self):
        previous_build_menu(self)
        icons=AssetIcons(self)
        menu=self.menuBar().addMenu("Simulation Lab")
        entries=(
            ("Loot Table Explorer",icons.icon("loot",20),lambda: self.open_loot_table_explorer()),
            ("Enchanting Table + Anvil",icons.icon("enchant",20),lambda: self.open_enchant_anvil_simulator()),
            ("Brewing Stand",icons.icon("brewing",20),self.open_brewing_simulator),
            ("Cauldron + Leather Dye",icons.icon("dye",20),self.open_dye_cauldron_simulator),
            ("Animal + Horse Breeding",icons.icon("animal",20),lambda: self.open_breeding_simulator("animals")),
        )
        for text,icon,fn in entries:
            action=QAction(icon,text,self); action.triggered.connect(fn); menu.addAction(action)
    F3Plus.build_menu=build_menu

    previous_run=F3Plus.run_selected
    loot_names={"Loot Table Simulator","Structure Loot Simulator","Trial Chamber Loot Simulator","Fishing Loot Simulator","Archaeology Loot Simulator","Piglin Barter Simulator","Trial Spawner Reward Simulator","Mob Drop Simulator"}
    enchant_names={"Enchanting Simulator","Enchantment Sequence Simulator","Best Enchantment Search","Enchantment Table Layout"}
    def run_selected(self):
        spec=self.selected_spec()
        if spec is not None:
            name=spec.name
            if name in loot_names: return self.open_loot_table_explorer(name)
            if name in enchant_names: return self.open_enchant_anvil_simulator("enchant")
            if name=="Anvil Prior-Work Planner": return self.open_enchant_anvil_simulator("anvil")
            if name=="Animal Breeding": return self.open_breeding_simulator("animals")
        return previous_run(self)
    F3Plus.run_selected=run_selected

    # Expose classes for smoke tests and future dialog reuse without changing catalog IDs.
    F3Plus.LootTableExplorer=LootTableExplorer
    F3Plus.EnchantAnvilSimulator=EnchantAnvilSimulator
    F3Plus.BrewingSimulator=BrewingSimulator
    F3Plus.DyeCauldronSimulator=DyeCauldronSimulator
    F3Plus.BreedingSimulator=BreedingSimulator
    F3Plus._simulation_lab_v234_installed=True
