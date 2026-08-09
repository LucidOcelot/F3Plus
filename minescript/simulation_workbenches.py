from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QMessageBox,
    QPushButton, QPlainTextEdit, QSpinBox, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from .feature_executor import FeatureExecutor
from .minecraft_simulators import (
    AnimalBreedingEngine, AnvilEngine, BASE_POTIONS, BrewingEngine, DYE_COLORS,
    EnchantingEngine, LootTableEngine, MinecraftJarData, cauldron_wash, dye_mix,
)
from .rng_recovery import launch_enchantment_cracker
from .tool_registry import ToolSpec, modes_for
from .workbench_forms import OperationDialog


def _pretty(value) -> str:
    def default(obj):
        return obj.__dict__ if hasattr(obj, "__dict__") else str(obj)
    return json.dumps(value, indent=2, ensure_ascii=False, default=default)


class RngEnchantingDialog(QDialog):
    def __init__(self, owner, executor: FeatureExecutor, tool: ToolSpec):
        super().__init__(owner)
        self.owner = owner; self.executor = executor; self.tool = tool
        self.data = MinecraftJarData(owner.settings.minecraft_version)
        self.enchanting = EnchantingEngine(self.data); self.anvil = AnvilEngine(self.enchanting)
        self.setWindowTitle("RNG & Enchanting Workbench"); self.resize(1080, 760)
        root = QVBoxLayout(self); tabs = QTabWidget(); root.addWidget(tabs, 1)

        enchanting = QWidget(); ef = QFormLayout(enchanting)
        self.item = QLineEdit("minecraft:diamond_pickaxe"); self.shelves = QSpinBox(); self.shelves.setRange(0, 15); self.shelves.setValue(15)
        self.seed = QSpinBox(); self.seed.setRange(-2_147_483_647, 2_147_483_647); self.seed.setValue(12345)
        erun = QPushButton("Roll all three table slots"); self.enchant_out = QPlainTextEdit(); self.enchant_out.setReadOnly(True)
        ef.addRow("Item", self.item); ef.addRow("Bookshelves", self.shelves); ef.addRow("RNG seed", self.seed); ef.addRow(erun); ef.addRow(self.enchant_out); erun.clicked.connect(self._roll)
        tabs.addTab(enchanting, "Enchanting Table")

        anvil = QWidget(); af = QFormLayout(anvil)
        self.anvil_item = QLineEdit("minecraft:diamond_pickaxe")
        self.left = QLineEdit('{"minecraft:efficiency": 4}'); self.right = QLineEdit('{"minecraft:efficiency": 4, "minecraft:unbreaking": 3}')
        self.left_ops = QSpinBox(); self.left_ops.setRange(0, 20); self.right_ops = QSpinBox(); self.right_ops.setRange(0, 20); self.rename = QCheckBox("Rename item")
        arun = QPushButton("Combine"); self.anvil_out = QPlainTextEdit(); self.anvil_out.setReadOnly(True)
        for label, widget in (("Item", self.anvil_item), ("Left enchantments JSON", self.left), ("Right enchantments JSON", self.right), ("Left prior operations", self.left_ops), ("Right prior operations", self.right_ops), ("", self.rename)):
            af.addRow(label, widget)
        af.addRow(arun); af.addRow(self.anvil_out); arun.clicked.connect(self._combine); tabs.addTab(anvil, "Anvil")

        rng = QWidget(); rv = QVBoxLayout(rng)
        note = QLabel("Enchanting probability, sequences/timelines, Java LCG recovery, and player-RNG recovery are modes of this workbench. Player RNG is not world-seed recovery.")
        note.setWordWrap(True); note.setObjectName("Muted"); rv.addWidget(note)
        self.rng_modes = [mode for mode in modes_for(tool) if mode.legacy is not None]
        self.rng_mode = QComboBox(); self.rng_mode.addItems([mode.name for mode in self.rng_modes]); rv.addWidget(self.rng_mode)
        rrun = QPushButton("Configure & run selected RNG operation"); rrun.clicked.connect(self._run_rng); rv.addWidget(rrun)
        self.rng_out = QPlainTextEdit(); self.rng_out.setReadOnly(True); rv.addWidget(self.rng_out, 1); tabs.addTab(rng, "RNG / Recovery / Probability")
        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close); self._roll()

    def _roll(self):
        offers = self.enchanting.roll_offers(self.item.text().strip(), self.shelves.value(), self.seed.value())
        source = "Bundled enchanting baseline" if self.enchanting.using_baseline else self.data.source
        self.enchant_out.setPlainText(_pretty({"source": source, "offers": offers}))

    def _combine(self):
        try:
            result = self.anvil.combine(self.anvil_item.text().strip(), json.loads(self.left.text() or "{}"), json.loads(self.right.text() or "{}"), self.left_ops.value(), self.right_ops.value(), self.rename.isChecked())
            self.anvil_out.setPlainText(_pretty(result))
        except Exception as exc:
            QMessageBox.warning(self, "Anvil", str(exc))

    def _run_rng(self):
        if not self.rng_modes: return
        mode = self.rng_modes[self.rng_mode.currentIndex()]
        if mode.name == "Enchantment RNG Seed Cracker":
            try:
                launch_enchantment_cracker(); self.rng_out.setPlainText("Opened the verified community EnchantmentCracker. This recovers gameplay/player RNG, not the world seed.")
            except Exception as exc:
                QMessageBox.warning(self, "RNG Cracker", str(exc))
            return
        dialog = OperationDialog(self.tool, self.executor, self.owner.settings, self, mode.key); dialog.mode_combo.setEnabled(False)
        if dialog.exec() != QDialog.Accepted or dialog.mode is None or dialog.mode.legacy is None: return
        try:
            result = self.executor.execute(dialog.mode.legacy, dialog.values())
            self.rng_out.setPlainText(_pretty({"operation": dialog.mode.name, "status": result.status, "result": result.data, "note": result.note}))
        except Exception as exc:
            QMessageBox.warning(self, dialog.mode.name, str(exc))


class LootWorkbenchDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.data = MinecraftJarData(owner.settings.minecraft_version); self.engine = LootTableEngine(self.data)
        self.setWindowTitle("Loot & Drop Workbench"); self.resize(1240, 820)
        root = QVBoxLayout(self); source = QLabel(self.engine.source); source.setObjectName("Muted"); root.addWidget(source)
        filters = QHBoxLayout(); self.category = QComboBox(); self.category.addItems(self.engine.categories()); self.query = QLineEdit(); self.query.setPlaceholderText("Search loot tables…")
        filters.addWidget(QLabel("Category")); filters.addWidget(self.category); filters.addWidget(self.query, 1); root.addLayout(filters)
        split = QSplitter(Qt.Horizontal); root.addWidget(split, 1); self.tables = QListWidget(); split.addWidget(self.tables)
        right = QWidget(); rv = QVBoxLayout(right); self.possible = QTableWidget(0, 6); self.possible.setHorizontalHeaderLabels(["Item", "Weight", "Pool", "Count", "Conditions", "Functions"]); self.possible.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents); self.possible.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch); rv.addWidget(self.possible, 1)
        controls = QHBoxLayout(); self.pulls = QSpinBox(); self.pulls.setRange(1, 1_000_000); self.pulls.setValue(1000); self.roll_seed = QSpinBox(); self.roll_seed.setRange(-2_147_483_647, 2_147_483_647); self.roll_seed.setValue(12345); run = QPushButton("Simulate")
        controls.addWidget(QLabel("Pulls")); controls.addWidget(self.pulls); controls.addWidget(QLabel("Seed")); controls.addWidget(self.roll_seed); controls.addWidget(run); rv.addLayout(controls); self.output = QPlainTextEdit(); self.output.setReadOnly(True); rv.addWidget(self.output, 1); split.addWidget(right); split.setSizes([320, 900])
        self.category.currentTextChanged.connect(self._refresh); self.query.textChanged.connect(self._refresh); self.tables.itemSelectionChanged.connect(self._select); run.clicked.connect(self._simulate); self._refresh()

    def _refresh(self):
        current = self.tables.currentItem().data(Qt.UserRole) if self.tables.currentItem() else ""; self.tables.clear()
        for table_id in self.engine.table_ids(self.category.currentText(), self.query.text()):
            item = QListWidgetItem(table_id.removeprefix("minecraft:")); item.setData(Qt.UserRole, table_id); self.tables.addItem(item)
        if self.tables.count():
            row = next((index for index in range(self.tables.count()) if self.tables.item(index).data(Qt.UserRole) == current), 0); self.tables.setCurrentRow(row)

    def _table_id(self):
        item = self.tables.currentItem(); return item.data(Qt.UserRole) if item else ""

    def _select(self):
        table_id = self._table_id()
        if not table_id: return
        rows = self.engine.possible_items(table_id); self.possible.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, key in enumerate(("item", "weight", "pools", "count", "conditions", "functions")):
                self.possible.setItem(r, c, QTableWidgetItem(str(row.get(key, ""))))

    def _simulate(self):
        table_id = self._table_id()
        if table_id:
            self.output.setPlainText(_pretty(self.engine.simulate(table_id, self.pulls.value(), self.roll_seed.value(), {"include_contextual_entries": True, "killed_by_player": True})))


class MechanicsLabDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.brewing = BrewingEngine(); self.animals = AnimalBreedingEngine(); self.setWindowTitle("Minecraft Mechanics Lab"); self.resize(980, 760)
        root = QVBoxLayout(self); tabs = QTabWidget(); root.addWidget(tabs, 1)

        brew = QWidget(); bf = QFormLayout(brew); self.potion = QComboBox(); self.potion.addItems(sorted(BASE_POTIONS)); self.ingredient = QComboBox(); self.ingredient.addItems(self.brewing.ingredients()); brun = QPushButton("Brew"); self.brew_out = QPlainTextEdit(); self.brew_out.setReadOnly(True)
        bf.addRow("Input potion", self.potion); bf.addRow("Ingredient", self.ingredient); bf.addRow(brun); bf.addRow(self.brew_out); brun.clicked.connect(self._brew); tabs.addTab(brew, "Brewing")

        dye = QWidget(); dv = QVBoxLayout(dye); self.existing = QLineEdit(); self.existing.setPlaceholderText("Existing leather color #RRGGBB (optional)"); dv.addWidget(self.existing); self.dyes = QListWidget(); self.dyes.setSelectionMode(QAbstractItemView.MultiSelection)
        for name in DYE_COLORS: self.dyes.addItem(name.replace("_", " ").title())
        dv.addWidget(self.dyes, 1); controls = QHBoxLayout(); mix = QPushButton("Mix selected dyes"); self.water = QSpinBox(); self.water.setRange(0, 3); self.water.setValue(3); wash = QPushButton("Wash dyed leather"); controls.addWidget(mix); controls.addStretch(); controls.addWidget(QLabel("Cauldron level")); controls.addWidget(self.water); controls.addWidget(wash); dv.addLayout(controls); self.dye_out = QPlainTextEdit(); self.dye_out.setReadOnly(True); dv.addWidget(self.dye_out); mix.clicked.connect(self._dye); wash.clicked.connect(self._wash); tabs.addTab(dye, "Leather Dye & Cauldron")

        breed = QWidget(); pf = QFormLayout(breed); self.species = QComboBox(); self.species.addItems(self.animals.species()); self.parent_a = QPlainTextEdit('{}'); self.parent_a.setMaximumHeight(110); self.parent_b = QPlainTextEdit('{}'); self.parent_b.setMaximumHeight(110); self.children = QSpinBox(); self.children.setRange(1, 100000); self.children.setValue(1000); self.breed_seed = QSpinBox(); self.breed_seed.setRange(-2_147_483_647, 2_147_483_647); self.breed_seed.setValue(12345); br = QPushButton("Simulate offspring"); self.breed_out = QPlainTextEdit(); self.breed_out.setReadOnly(True)
        for label, widget in (("Species", self.species), ("Parent A breeding NBT (JSON)", self.parent_a), ("Parent B breeding NBT (JSON)", self.parent_b), ("Children", self.children), ("Seed", self.breed_seed)): pf.addRow(label, widget)
        pf.addRow(br); pf.addRow(self.breed_out); br.clicked.connect(self._breed); tabs.addTab(breed, "Animal & Horse Breeding")
        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close); self._brew()

    def _brew(self):
        self.brew_out.setPlainText(_pretty(self.brewing.brew(BASE_POTIONS[self.potion.currentText()], self.ingredient.currentText())))

    def _dye(self):
        existing = self.existing.text().strip(); current = int(existing.removeprefix("#"), 16) if existing else None; names = [item.text().lower().replace(" ", "_") for item in self.dyes.selectedItems()]; self.dye_out.setPlainText(_pretty(dye_mix(current, names)))

    def _wash(self):
        self.dye_out.setPlainText(_pretty(cauldron_wash(self.water.value(), True)))

    def _breed(self):
        try:
            self.breed_out.setPlainText(_pretty(self.animals.simulate(self.species.currentText(), self.parent_a.toPlainText(), self.parent_b.toPlainText(), self.children.value(), self.breed_seed.value())))
        except Exception as exc:
            QMessageBox.warning(self, "Breeding", str(exc))
