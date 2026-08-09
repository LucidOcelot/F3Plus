from __future__ import annotations

import json
import math
import random
import re
from collections import defaultdict
from typing import Any

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QFrame, QGraphicsEllipseItem, QGraphicsScene,
    QGraphicsTextItem, QGraphicsView, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QPlainTextEdit, QScrollArea, QSpinBox, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .feature_executor import FeatureExecutor, MACRO_NAMES
from .minecraft_simulators_v234 import (
    AnimalBreedingEngine, AnvilEngine, BASE_POTIONS, BREEDABLE_ANIMALS,
    BrewingEngine, DYE_COLORS, EnchantingEngine, FALLBACK_ENCHANTMENTS,
    FALLBACK_LOOT_TABLES, HorseBreedingEngine, LEATHER_DEFAULT, LootStack,
    LootTableEngine, MinecraftJarData, _provider_value, cauldron_wash, dye_mix,
    loot_category,
)
from .rng_recovery import launch_enchantment_cracker
from .tool_registry import ToolMode, ToolSpec, modes_for, resolve_mode
from .villagers import LEVEL_NAMES, PROFESSIONS, load_for_version, search as trade_search


# ---------------------------------------------------------------------------
# Shared forms
# ---------------------------------------------------------------------------


def _widget(kind: str, default: Any):
    if kind == "int":
        w = QSpinBox(); w.setRange(-2_147_483_647, 2_147_483_647); w.setValue(int(default))
    elif kind == "float":
        w = QDoubleSpinBox(); w.setDecimals(6); w.setRange(-1e12, 1e12); w.setValue(float(default))
    elif kind == "bool":
        w = QCheckBox(); w.setChecked(bool(default))
    elif kind == "choice":
        w = QComboBox(); w.addItems([str(x) for x in default])
    else:
        w = QLineEdit(str(default))
    return w


def _value(widget):
    if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
        return widget.value()
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, QComboBox):
        return widget.currentText()
    return widget.text()


class OperationDialog(QDialog):
    """One canonical tool, many historical operations, one dynamic parameter form."""

    def __init__(self, tool: ToolSpec, executor: FeatureExecutor, settings, parent=None, preferred_mode: str = ""):
        super().__init__(parent)
        self.tool = tool
        self.executor = executor
        self.settings = settings
        self.inputs: dict[str, QWidget] = {}
        self.mode: ToolMode | None = None
        self.setWindowTitle(tool.name)
        self.resize(700, 620)

        root = QVBoxLayout(self)
        title = QLabel(tool.name); title.setObjectName("WorkspaceTitle"); root.addWidget(title)
        summary = QLabel(tool.summary); summary.setWordWrap(True); summary.setObjectName("Muted"); root.addWidget(summary)

        row = QHBoxLayout(); row.addWidget(QLabel("Operation"))
        self.mode_combo = QComboBox()
        self._modes = [mode for mode in modes_for(tool) if mode.legacy is not None]
        self.mode_combo.addItems([mode.name for mode in self._modes])
        row.addWidget(self.mode_combo, 1); root.addLayout(row)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        self.form_host = QWidget(); self.form = QFormLayout(self.form_host)
        scroll.setWidget(self.form_host); root.addWidget(scroll, 1)

        self.note = QLabel(); self.note.setWordWrap(True); self.note.setObjectName("Muted"); root.addWidget(self.note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Run")
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

        self.mode_combo.currentIndexChanged.connect(self._rebuild)
        if preferred_mode:
            for index, mode in enumerate(self._modes):
                if preferred_mode in {mode.key, mode.name}:
                    self.mode_combo.setCurrentIndex(index); break
        self._rebuild()

    def _clear_form(self):
        while self.form.rowCount():
            self.form.removeRow(0)
        self.inputs.clear()

    def _rebuild(self):
        self._clear_form()
        if not self._modes:
            self.mode = None; return
        self.mode = self._modes[self.mode_combo.currentIndex()]
        spec = self.mode.legacy
        fields = self.executor.input_fields(spec)
        if not fields:
            self.note.setText("This operation does not require additional values.")
        else:
            self.note.setText("Only values used by this operation are shown.")
        for key, label, default, kind in fields:
            if key == "seed" and getattr(self.settings, "seed", None):
                default = self.settings.seed
            w = _widget(kind, default)
            self.inputs[key] = w
            self.form.addRow(label, w)

    def values(self) -> dict[str, Any]:
        return {key: _value(widget) for key, widget in self.inputs.items()}


# ---------------------------------------------------------------------------
# Correct, instance-local simulator engines.  No package-wide monkey patching.
# ---------------------------------------------------------------------------


def _normalized_item_tags(data: MinecraftJarData) -> dict[str, list[str]]:
    raw_tags = data.json_namespace(("data/minecraft/tags/item/", "data/minecraft/tags/items/"))
    out: dict[str, list[str]] = {}
    for tag_id, payload in raw_tags.items():
        if not isinstance(payload, dict) or not isinstance(payload.get("values"), list):
            continue
        values: list[str] = []
        for raw in payload["values"]:
            value = raw.get("id", "") if isinstance(raw, dict) else raw
            value = str(value)
            if value:
                values.append(value)
        out[tag_id] = values
    return out


class CanonicalLootEngine(LootTableEngine):
    def __init__(self, data: MinecraftJarData):
        self.data = data
        raw = data.json_namespace(("data/minecraft/loot_table/", "data/minecraft/loot_tables/"))
        self.using_baseline = not bool(raw)
        self.tables = {key: value for key, value in raw.items() if isinstance(value, dict)} if raw else dict(FALLBACK_LOOT_TABLES)
        self.tags = _normalized_item_tags(data)

    @property
    def source(self) -> str:
        return "Bundled baseline examples" if self.using_baseline else self.data.source

    def _resolve_tag(self, tag_id: str, seen: set[str] | None = None) -> list[str]:
        tag_id = str(tag_id).removeprefix("#")
        if ":" not in tag_id:
            tag_id = "minecraft:" + tag_id
        seen = set() if seen is None else seen
        if tag_id in seen:
            return []
        seen.add(tag_id)
        out: list[str] = []
        for raw in self.tags.get(tag_id, []):
            value = str(raw)
            if value.startswith("#"):
                out.extend(self._resolve_tag(value, seen))
            elif value:
                out.append(value if ":" in value else "minecraft:" + value)
        return list(dict.fromkeys(out))

    def roll(self, table_id: str, *, rng=None, context=None, depth: int = 0):
        rng = rng or random.Random()
        context = dict(context or {})
        if depth > 12:
            return []
        table = self.tables.get(table_id)
        if not isinstance(table, dict):
            return []
        stacks: list[LootStack] = []
        for pool in table.get("pools", []):
            if not isinstance(pool, dict):
                continue
            if not all(self._condition_passes(cond, rng, context) for cond in pool.get("conditions", [])):
                continue
            rolls = max(0, int(round(_provider_value(pool.get("rolls", 1), rng))))
            for _ in range(rolls):
                eligible, weights = [], []
                for entry in pool.get("entries", []):
                    if not isinstance(entry, dict):
                        continue
                    if not all(self._condition_passes(cond, rng, context) for cond in entry.get("conditions", [])):
                        continue
                    weight = max(0.0, float(entry.get("weight", 1) or 1))
                    if weight > 0:
                        eligible.append(entry); weights.append(weight)
                if not eligible:
                    continue
                chosen = dict(rng.choices(eligible, weights=weights, k=1)[0])
                # Entry predicates were already evaluated for pool eligibility.  The
                # recursive expander must not evaluate the same random predicate again.
                chosen["conditions"] = []
                stacks.extend(self._entry_stacks(chosen, rng, context, depth + 1))
            stacks = self._apply_functions(stacks, pool.get("functions"), rng)
        stacks = self._apply_functions(stacks, table.get("functions"), rng)
        grouped: dict[tuple[str, str], int] = defaultdict(int)
        for stack in stacks:
            if stack.count > 0:
                grouped[(stack.item, stack.detail)] += stack.count
        return [LootStack(item, count, detail) for (item, detail), count in grouped.items()]


class CanonicalEnchantingEngine(EnchantingEngine):
    def __init__(self, data: MinecraftJarData):
        self.data = data
        raw = data.json_namespace(("data/minecraft/enchantment/", "data/minecraft/enchantments/"))
        self.using_baseline = not bool(raw)
        self.enchantments = (
            {key: value for key, value in raw.items() if isinstance(value, dict)}
            if raw else {f"minecraft:{key}": dict(value) for key, value in FALLBACK_ENCHANTMENTS.items()}
        )
        self.tags = _normalized_item_tags(data)
        raw_tags = data.json_namespace(("data/minecraft/tags/enchantment/", "data/minecraft/tags/enchantments/"))
        treasure = raw_tags.get("minecraft:treasure", {})
        self.treasure_enchantments: set[str] = set()
        if isinstance(treasure, dict):
            for raw_value in treasure.get("values", []):
                value = raw_value.get("id", "") if isinstance(raw_value, dict) else raw_value
                value = str(value)
                if value and not value.startswith("#"):
                    self.treasure_enchantments.add(value if ":" in value else "minecraft:" + value)
        if self.using_baseline:
            self.treasure_enchantments.update(
                enchant_id for enchant_id, definition in self.enchantments.items()
                if isinstance(definition, dict) and definition.get("treasure_only")
            )

    def roll_offers(self, *args, **kwargs):
        offers = super().roll_offers(*args, **kwargs)
        for offer in offers:
            offer["enchantments"] = [row for row in offer.get("enchantments", []) if row.get("id") not in self.treasure_enchantments]
            if self.using_baseline:
                offer["source"] = "Bundled enchanting baseline"
        return offers


# ---------------------------------------------------------------------------
# Simulation workbenches
# ---------------------------------------------------------------------------


def _pretty(value: Any) -> str:
    def default(obj):
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)
    return json.dumps(value, indent=2, ensure_ascii=False, default=default)


class RngEnchantingDialog(QDialog):
    def __init__(self, owner, executor: FeatureExecutor, tool: ToolSpec):
        super().__init__(owner)
        self.owner = owner; self.executor = executor; self.tool = tool
        self.data = MinecraftJarData(owner.settings.minecraft_version)
        self.enchanting = CanonicalEnchantingEngine(self.data)
        self.anvil = AnvilEngine(self.enchanting)
        self.setWindowTitle("RNG & Enchanting Workbench"); self.resize(1100, 780)
        root = QVBoxLayout(self)
        tabs = QTabWidget(); root.addWidget(tabs, 1)

        enchanting = QWidget(); form = QFormLayout(enchanting)
        self.item = QLineEdit("minecraft:diamond_pickaxe")
        self.shelves = QSpinBox(); self.shelves.setRange(0, 15); self.shelves.setValue(15)
        self.enchant_seed = QSpinBox(); self.enchant_seed.setRange(-2_147_483_647, 2_147_483_647); self.enchant_seed.setValue(12345)
        run = QPushButton("Roll all three table slots")
        self.enchant_out = QPlainTextEdit(); self.enchant_out.setReadOnly(True)
        form.addRow("Item", self.item); form.addRow("Bookshelves", self.shelves); form.addRow("RNG seed", self.enchant_seed); form.addRow(run); form.addRow(self.enchant_out)
        run.clicked.connect(self._roll_enchanting); tabs.addTab(enchanting, "Enchanting Table")

        anvil = QWidget(); af = QFormLayout(anvil)
        self.anvil_item = QLineEdit("minecraft:diamond_pickaxe")
        self.left = QLineEdit('{"minecraft:efficiency": 4}')
        self.right = QLineEdit('{"minecraft:efficiency": 4, "minecraft:unbreaking": 3}')
        self.left_ops = QSpinBox(); self.left_ops.setRange(0, 20)
        self.right_ops = QSpinBox(); self.right_ops.setRange(0, 20)
        self.rename = QCheckBox("Rename item")
        arun = QPushButton("Combine")
        self.anvil_out = QPlainTextEdit(); self.anvil_out.setReadOnly(True)
        for label, widget in (("Item", self.anvil_item), ("Left enchantments JSON", self.left), ("Right enchantments JSON", self.right), ("Left prior operations", self.left_ops), ("Right prior operations", self.right_ops), ("", self.rename)):
            af.addRow(label, widget)
        af.addRow(arun); af.addRow(self.anvil_out); arun.clicked.connect(self._run_anvil); tabs.addTab(anvil, "Anvil")

        rng = QWidget(); rv = QVBoxLayout(rng)
        note = QLabel("All historical enchanting, probability, sequence/timeline, and Java LCG recovery entries are operations of this workbench. Player RNG remains separate from the world seed.")
        note.setWordWrap(True); note.setObjectName("Muted"); rv.addWidget(note)
        self.rng_mode = QComboBox()
        self.rng_modes = [mode for mode in modes_for(tool) if mode.legacy is not None]
        self.rng_mode.addItems([mode.name for mode in self.rng_modes]); rv.addWidget(self.rng_mode)
        rrun = QPushButton("Configure & run selected RNG operation"); rrun.clicked.connect(self._run_legacy_rng); rv.addWidget(rrun)
        self.rng_out = QPlainTextEdit(); self.rng_out.setReadOnly(True); rv.addWidget(self.rng_out, 1)
        tabs.addTab(rng, "RNG / Recovery / Probability")

        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close)
        self._roll_enchanting()

    def _roll_enchanting(self):
        result = self.enchanting.roll_offers(self.item.text().strip(), self.shelves.value(), self.enchant_seed.value())
        self.enchant_out.setPlainText(_pretty({"source": self.data.source if self.data.jar_path else "Bundled enchanting baseline", "offers": result}))

    def _run_anvil(self):
        try:
            result = self.anvil.combine(self.anvil_item.text().strip(), json.loads(self.left.text() or "{}"), json.loads(self.right.text() or "{}"), self.left_ops.value(), self.right_ops.value(), self.rename.isChecked())
            self.anvil_out.setPlainText(_pretty(result))
        except Exception as exc:
            QMessageBox.warning(self, "Anvil", str(exc))

    def _run_legacy_rng(self):
        if not self.rng_modes:
            return
        mode = self.rng_modes[self.rng_mode.currentIndex()]
        if mode.name == "Enchantment RNG Seed Cracker":
            try:
                launch_enchantment_cracker(); self.rng_out.setPlainText("Opened the verified community EnchantmentCracker. This recovers gameplay/player RNG, not the world seed.")
            except Exception as exc:
                QMessageBox.warning(self, "RNG Cracker", str(exc))
            return
        dialog = OperationDialog(self.tool, self.executor, self.owner.settings, self, mode.key)
        # Lock the workbench selector to the chosen operation for this invocation.
        dialog.mode_combo.setEnabled(False)
        if dialog.exec() != QDialog.Accepted or dialog.mode is None or dialog.mode.legacy is None:
            return
        try:
            result = self.executor.execute(dialog.mode.legacy, dialog.values())
            self.rng_out.setPlainText(_pretty({"operation": dialog.mode.name, "status": result.status, "result": result.data, "note": result.note}))
        except Exception as exc:
            QMessageBox.warning(self, dialog.mode.name, str(exc))


class LootWorkbenchDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.data = MinecraftJarData(owner.settings.minecraft_version)
        self.engine = CanonicalLootEngine(self.data)
        self.setWindowTitle("Loot & Drop Workbench"); self.resize(1250, 820)
        root = QVBoxLayout(self)
        badge = QLabel(self.engine.source); badge.setObjectName("Muted"); root.addWidget(badge)
        filters = QHBoxLayout(); self.category = QComboBox(); self.category.addItems(self.engine.categories()); self.query = QLineEdit(); self.query.setPlaceholderText("Search loot tables…")
        filters.addWidget(QLabel("Category")); filters.addWidget(self.category); filters.addWidget(self.query, 1); root.addLayout(filters)
        split = QSplitter(Qt.Horizontal); root.addWidget(split, 1)
        self.tables = QListWidget(); split.addWidget(self.tables)
        right = QWidget(); rv = QVBoxLayout(right)
        self.possible = QTableWidget(0, 6); self.possible.setHorizontalHeaderLabels(["Item", "Weight", "Pool", "Count", "Conditions", "Functions"]); self.possible.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents); self.possible.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch); rv.addWidget(self.possible, 1)
        controls = QHBoxLayout(); self.pulls = QSpinBox(); self.pulls.setRange(1, 1_000_000); self.pulls.setValue(1000); self.seed = QSpinBox(); self.seed.setRange(-2_147_483_647, 2_147_483_647); self.seed.setValue(12345); run = QPushButton("Simulate")
        controls.addWidget(QLabel("Pulls")); controls.addWidget(self.pulls); controls.addWidget(QLabel("Seed")); controls.addWidget(self.seed); controls.addWidget(run); rv.addLayout(controls)
        self.output = QPlainTextEdit(); self.output.setReadOnly(True); rv.addWidget(self.output, 1); split.addWidget(right); split.setSizes([330, 900])
        self.category.currentTextChanged.connect(self._refresh_tables); self.query.textChanged.connect(self._refresh_tables); self.tables.itemSelectionChanged.connect(self._select); run.clicked.connect(self._simulate)
        self._refresh_tables()

    def _refresh_tables(self):
        current = self.tables.currentItem().data(Qt.UserRole) if self.tables.currentItem() else ""
        self.tables.clear()
        for table_id in self.engine.table_ids(self.category.currentText(), self.query.text()):
            item = QListWidgetItem(table_id.removeprefix("minecraft:")); item.setData(Qt.UserRole, table_id); self.tables.addItem(item)
        if self.tables.count():
            row = next((i for i in range(self.tables.count()) if self.tables.item(i).data(Qt.UserRole) == current), 0); self.tables.setCurrentRow(row)

    def _selected_id(self):
        item = self.tables.currentItem(); return item.data(Qt.UserRole) if item else ""

    def _select(self):
        table_id = self._selected_id()
        if not table_id:
            return
        rows = self.engine.possible_items(table_id); self.possible.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, key in enumerate(("item", "weight", "pools", "count", "conditions", "functions")):
                self.possible.setItem(r, c, QTableWidgetItem(str(row.get(key, ""))))

    def _simulate(self):
        table_id = self._selected_id()
        if not table_id:
            return
        result = self.engine.simulate(table_id, self.pulls.value(), self.seed.value(), {"include_contextual_entries": True, "killed_by_player": True})
        self.output.setPlainText(_pretty(result))


class MechanicsLabDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner); self.setWindowTitle("Minecraft Mechanics Lab"); self.resize(980, 760)
        self.brewing = BrewingEngine(); self.animals = AnimalBreedingEngine(); self.horses = HorseBreedingEngine()
        root = QVBoxLayout(self); tabs = QTabWidget(); root.addWidget(tabs, 1)

        brew = QWidget(); bf = QFormLayout(brew)
        self.potion = QComboBox(); self.potion.addItems(sorted(BASE_POTIONS))
        self.ingredient = QComboBox(); self.ingredient.addItems(self.brewing.ingredients())
        brun = QPushButton("Brew"); self.brew_out = QPlainTextEdit(); self.brew_out.setReadOnly(True)
        bf.addRow("Input potion", self.potion); bf.addRow("Ingredient", self.ingredient); bf.addRow(brun); bf.addRow(self.brew_out); brun.clicked.connect(self._brew); tabs.addTab(brew, "Brewing")

        dye = QWidget(); dv = QVBoxLayout(dye)
        self.existing = QLineEdit(); self.existing.setPlaceholderText("Existing leather color, e.g. #A06540 (optional)"); dv.addWidget(self.existing)
        self.dyes = QListWidget(); self.dyes.setSelectionMode(QAbstractItemView.MultiSelection); [self.dyes.addItem(name.replace("_", " ").title()) for name in DYE_COLORS]; dv.addWidget(self.dyes, 1)
        drow = QHBoxLayout(); drun = QPushButton("Mix selected dyes"); self.water = QSpinBox(); self.water.setRange(0, 3); self.water.setValue(3); wash = QPushButton("Wash dyed leather")
        drow.addWidget(drun); drow.addStretch(); drow.addWidget(QLabel("Cauldron level")); drow.addWidget(self.water); drow.addWidget(wash); dv.addLayout(drow)
        self.dye_out = QPlainTextEdit(); self.dye_out.setReadOnly(True); dv.addWidget(self.dye_out); drun.clicked.connect(self._dye); wash.clicked.connect(self._wash); tabs.addTab(dye, "Leather Dye & Cauldron")

        breeding = QWidget(); pf = QFormLayout(breeding)
        self.species = QComboBox(); self.species.addItems(self.animals.species())
        self.parent_a = QPlainTextEdit('{}'); self.parent_a.setMaximumHeight(110)
        self.parent_b = QPlainTextEdit('{}'); self.parent_b.setMaximumHeight(110)
        self.children = QSpinBox(); self.children.setRange(1, 100000); self.children.setValue(1000)
        self.breed_seed = QSpinBox(); self.breed_seed.setRange(-2_147_483_647, 2_147_483_647); self.breed_seed.setValue(12345)
        br = QPushButton("Simulate offspring"); self.breed_out = QPlainTextEdit(); self.breed_out.setReadOnly(True)
        for label, widget in (("Species", self.species), ("Parent A breeding NBT (JSON)", self.parent_a), ("Parent B breeding NBT (JSON)", self.parent_b), ("Children", self.children), ("Seed", self.breed_seed)):
            pf.addRow(label, widget)
        pf.addRow(br); pf.addRow(self.breed_out); br.clicked.connect(self._breed); tabs.addTab(breeding, "Animal & Horse Breeding")
        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close)
        self._brew()

    def _brew(self):
        self.brew_out.setPlainText(_pretty(self.brewing.brew(self.potion.currentText(), self.ingredient.currentText())))

    def _dye(self):
        existing = self.existing.text().strip(); existing_value = None
        if existing:
            existing_value = int(existing.removeprefix("#"), 16)
        names = [item.text().lower().replace(" ", "_") for item in self.dyes.selectedItems()]
        self.dye_out.setPlainText(_pretty(dye_mix(existing_value, names)))

    def _wash(self):
        self.dye_out.setPlainText(_pretty(cauldron_wash(self.water.value(), True)))

    def _breed(self):
        try:
            result = self.animals.simulate(self.species.currentText(), self.parent_a.toPlainText(), self.parent_b.toPlainText(), self.children.value(), self.breed_seed.value())
            self.breed_out.setPlainText(_pretty(result))
        except Exception as exc:
            QMessageBox.warning(self, "Breeding", str(exc))


# ---------------------------------------------------------------------------
# Villager explorer
# ---------------------------------------------------------------------------


def _item_token(text: str) -> str:
    value = str(text or "").lower().strip().removeprefix("minecraft:")
    value = re.sub(r"^\d+\s*[x×]?\s*", "", value)
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value


class VillagerExplorerDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner); self.owner = owner
        self.trades, self.source = load_for_version(owner.settings.minecraft_version)
        self.jar = MinecraftJarData(owner.settings.minecraft_version)
        self.setWindowTitle("Villager Explorer"); self.resize(1240, 820)
        root = QVBoxLayout(self)
        hero = QHBoxLayout(); self.portrait = QLabel(); self.portrait.setFixedSize(92, 92); self.portrait.setAlignment(Qt.AlignCenter); hero.addWidget(self.portrait)
        title = QVBoxLayout(); h = QLabel("Villager Explorer"); h.setObjectName("WorkspaceTitle"); title.addWidget(h); self.source_label = QLabel(f"{len(self.trades)} trades • {self.source}"); self.source_label.setObjectName("Muted"); title.addWidget(self.source_label); hero.addLayout(title, 1); root.addLayout(hero)
        filters = QHBoxLayout(); self.prof = QComboBox(); self.prof.addItem("All professions"); self.prof.addItems([p.title() for p in PROFESSIONS]); self.level = QComboBox(); self.level.addItem("All levels"); self.level.addItems([f"{i} — {LEVEL_NAMES[i]}" for i in range(1, 6)]); self.query = QLineEdit(); self.query.setPlaceholderText("Search item or trade…")
        filters.addWidget(self.prof); filters.addWidget(self.level); filters.addWidget(self.query, 1); root.addLayout(filters)
        self.table = QTableWidget(0, 8); self.table.setHorizontalHeaderLabels(["Profession", "Level", "Trade", "Wants", "Additional", "Gives", "Max uses", "XP"]); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents); self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch); self.table.setIconSize(self.portrait.size() / 3); root.addWidget(self.table, 1)
        self.prof.currentTextChanged.connect(self.refresh); self.level.currentTextChanged.connect(self.refresh); self.query.textChanged.connect(self.refresh); self.refresh()

    def _portrait_pixmap(self, profession: str) -> QPixmap:
        size = 84
        layers = ["assets/minecraft/textures/entity/villager/villager.png", "assets/minecraft/textures/entity/villager/type/plains.png"]
        if profession and profession != "all professions":
            layers.append(f"assets/minecraft/textures/entity/villager/profession/{profession}.png")
        canvas = QPixmap(size, size); canvas.fill(Qt.transparent); painter = QPainter(canvas)
        loaded = False
        for member in layers:
            raw = self.jar.read_bytes(member); pix = QPixmap()
            if raw and pix.loadFromData(raw):
                loaded = True; painter.drawPixmap(0, 0, pix.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation))
        painter.end()
        if loaded:
            return canvas
        return QPixmap()

    def refresh(self):
        p = None if self.prof.currentText().startswith("All") else self.prof.currentText().lower()
        level = None if self.level.currentText().startswith("All") else int(self.level.currentText()[0])
        rows = trade_search(self.trades, self.query.text(), p, level)
        portrait = self._portrait_pixmap((p or "")); self.portrait.setPixmap(portrait)
        self.table.setRowCount(len(rows))
        for r, trade in enumerate(rows):
            values = [trade.profession.title(), f"{trade.level} — {LEVEL_NAMES.get(trade.level, trade.level)}", trade.name, trade.wants, trade.additional_wants or "", trade.gives, "" if trade.max_uses is None else str(trade.max_uses), "" if trade.xp is None else str(trade.xp)]
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                if c in (3, 4, 5):
                    token = _item_token(value); raw, _ = self.jar.texture_bytes((f"assets/minecraft/textures/item/{token}.png", f"assets/minecraft/textures/block/{token}.png")); pix = QPixmap()
                    if raw and pix.loadFromData(raw):
                        item.setIcon(QIcon(pix))
                self.table.setItem(r, c, item)


# ---------------------------------------------------------------------------
# Generic interactive coordinate result map
# ---------------------------------------------------------------------------


def extract_coordinate_layers(data: Any) -> dict[str, list[tuple[float, float, str]]]:
    layers: dict[str, list[tuple[float, float, str]]] = defaultdict(list)

    def walk(value: Any, path: str):
        if isinstance(value, dict):
            if isinstance(value.get("x"), (int, float)) and isinstance(value.get("z"), (int, float)):
                layers[path or "Results"].append((float(value["x"]), float(value["z"]), path))
            elif isinstance(value.get("chunk_x"), (int, float)) and isinstance(value.get("chunk_z"), (int, float)):
                layers[path or "Results"].append((float(value["chunk_x"]) * 16 + 8, float(value["chunk_z"]) * 16 + 8, path + " (chunk center)"))
            for key, child in value.items():
                walk(child, f"{path}.{key}" if path else str(key))
        elif isinstance(value, (list, tuple)):
            if len(value) in (2, 3) and all(isinstance(x, (int, float)) for x in value):
                x, z = (value[0], value[1]) if len(value) == 2 else (value[0], value[2])
                layers[path or "Results"].append((float(x), float(z), path))
            else:
                for index, child in enumerate(value):
                    walk(child, f"{path}[{index}]")

    walk(data, "")
    # Merge overly-specific indexed paths by their first meaningful key.
    compact: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
    for path, points in layers.items():
        key = path.split(".", 1)[0].split("[", 1)[0] or "Results"
        compact[key].extend(points)
    return {key: value for key, value in compact.items() if value}


class ZoomView(QGraphicsView):
    def wheelEvent(self, event):
        factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        self.scale(factor, factor)


class ResultMapDialog(QDialog):
    def __init__(self, data: Any, parent=None):
        super().__init__(parent); self.layers = extract_coordinate_layers(data); self.setWindowTitle("Interactive X/Z Result View"); self.resize(1000, 760)
        root = QVBoxLayout(self); toolbar = QHBoxLayout(); fit = QPushButton("Fit"); self.labels = QCheckBox("Point labels"); copy = QPushButton("Copy visible coordinates"); toolbar.addWidget(fit); toolbar.addWidget(self.labels); toolbar.addStretch(); toolbar.addWidget(copy); root.addLayout(toolbar)
        split = QSplitter(Qt.Horizontal); root.addWidget(split, 1); self.layer_list = QListWidget(); split.addWidget(self.layer_list); self.scene = QGraphicsScene(self); self.view = ZoomView(self.scene); self.view.setDragMode(QGraphicsView.ScrollHandDrag); self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse); split.addWidget(self.view); split.setSizes([220, 780])
        for layer in self.layers:
            item = QListWidgetItem(layer); item.setFlags(item.flags() | Qt.ItemIsUserCheckable); item.setCheckState(Qt.Checked); self.layer_list.addItem(item)
        self.layer_list.itemChanged.connect(self.redraw); self.labels.toggled.connect(self.redraw); fit.clicked.connect(self.fit); copy.clicked.connect(self.copy_visible); self.redraw(); self.fit()

    def visible_layers(self):
        return {self.layer_list.item(i).text() for i in range(self.layer_list.count()) if self.layer_list.item(i).checkState() == Qt.Checked}

    def redraw(self):
        self.scene.clear(); active = self.visible_layers()
        points = [point for layer, values in self.layers.items() if layer in active for point in values]
        if not points:
            return
        xs = [p[0] for p in points]; zs = [p[1] for p in points]; step = max(16.0, (max(max(xs)-min(xs), max(zs)-min(zs), 64.0) / 12.0))
        left = math.floor(min(xs) / step) * step; right = math.ceil(max(xs) / step) * step; top = math.floor(min(zs) / step) * step; bottom = math.ceil(max(zs) / step) * step
        pen = QPen(); pen.setCosmetic(True)
        x = left
        while x <= right:
            self.scene.addLine(x, top, x, bottom, pen); x += step
        z = top
        while z <= bottom:
            self.scene.addLine(left, z, right, z, pen); z += step
        for layer, values in self.layers.items():
            if layer not in active:
                continue
            for x, z, label in values:
                dot = self.scene.addEllipse(x-2, z-2, 4, 4); dot.setToolTip(f"{layer}: X {x:g}, Z {z:g}")
                if self.labels.isChecked():
                    text = self.scene.addText(f"{x:g}, {z:g}"); text.setPos(x+3, z+3); text.setFlag(QGraphicsTextItem.ItemIgnoresTransformations, True)

    def fit(self):
        rect = self.scene.itemsBoundingRect()
        if not rect.isNull():
            self.view.fitInView(rect.adjusted(-20, -20, 20, 20), Qt.KeepAspectRatio)

    def copy_visible(self):
        from PySide6.QtWidgets import QApplication
        active = self.visible_layers(); lines = []
        for layer, values in self.layers.items():
            if layer in active:
                lines.extend(f"{layer}: {x:g}, {z:g}" for x, z, _ in values)
        QApplication.clipboard().setText("\n".join(lines))
