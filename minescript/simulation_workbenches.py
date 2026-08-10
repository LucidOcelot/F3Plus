from __future__ import annotations

"""Minecraft-oriented simulator workbenches.

The engines remain data/model focused; this module is the player-facing abstraction
layer.  Users select items, enchantments, traits, ingredients and colors rather than
editing JSON/NBT.  Expensive installed-JAR initialization happens after the window is
visible and reports activity instead of making the dialog appear not to open.
"""

from collections import Counter

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QProgressBar, QPushButton, QScrollArea, QSpinBox, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .async_jobs import start_job
from .async_workbench import OperationDialog
from .feature_executor import FeatureExecutor
from .minecraft_simulators import (
    AnimalBreedingEngine, AnvilEngine, BASE_POTIONS, BrewingEngine, DYE_COLORS,
    EnchantingEngine, MinecraftJarData, cauldron_wash, dye_mix,
)
from .minecraft_widgets import AssetProvider, EnchantmentEditor, ExplanationCard, ItemPicker, MetricCard
from .rng_recovery import launch_enchantment_cracker
from .tool_registry import ToolSpec, modes_for


def _pretty_id(value: str) -> str:
    return str(value).removeprefix("minecraft:").replace("_", " ").title()


def _human_traits(row: dict) -> str:
    if not isinstance(row, dict):
        return str(row)
    hidden = {"Age", "InLove", "Attributes", "Health", "simulation_profile"}
    parts = []
    for key, value in row.items():
        if key in hidden:
            continue
        if isinstance(value, (dict, list)):
            continue
        if isinstance(value, float): value = f"{value:.4g}"
        parts.append(f"{str(key).replace('_', ' ').title()}: {value}")
    return " • ".join(parts) or "Default inherited traits"


class RngEnchantingDialog(QDialog):
    """Game-like enchanting/anvil surface plus canonical RNG operation explorer."""

    def __init__(self, owner, executor: FeatureExecutor, tool: ToolSpec):
        super().__init__(owner)
        self.owner = owner; self.executor = executor; self.tool = tool
        self.data = None; self.assets = None; self.enchanting = None; self.anvil = None; self._load_job = None
        self.setWindowTitle("RNG & Enchanting Workbench"); self.resize(1180, 820); self.setMinimumSize(980, 700)

        root = QVBoxLayout(self); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(8)
        hero = QFrame(); hero.setObjectName("ExplorerHero"); hv = QVBoxLayout(hero)
        title = QLabel("RNG & Enchanting"); title.setObjectName("WorkspaceTitle"); hv.addWidget(title)
        help_text = QLabel("Use Minecraft-style item/enchantment controls for table and anvil planning. Advanced probability/recovery tools remain grouped in the RNG explorer below; gameplay RNG is never presented as a world seed.")
        help_text.setWordWrap(True); help_text.setObjectName("Muted"); hv.addWidget(help_text); root.addWidget(hero)

        self.loading_label = QLabel("Reading installed Minecraft enchantment data…"); self.loading_label.setObjectName("Muted"); root.addWidget(self.loading_label)
        self.loading = QProgressBar(); self.loading.setRange(0, 0); self.loading.setTextVisible(False); root.addWidget(self.loading)
        self.tabs = QTabWidget(); root.addWidget(self.tabs, 1)
        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close)

        # Do not parse/index the JAR before the dialog can paint.
        self._load_job = start_job(self._load_engines, finished=self._engines_ready, failed=self._engines_failed)

    def _load_engines(self):
        data = MinecraftJarData(self.owner.settings.minecraft_version)
        enchanting = EnchantingEngine(data)
        return data, enchanting, AnvilEngine(enchanting)

    def _engines_failed(self, message: str, detail: str):
        self.loading.hide(); self.loading_label.setText("Could not initialize installed-version enchanting data. See details below.")
        box = QMessageBox(QMessageBox.Warning, "RNG & Enchanting", message, parent=self); box.setDetailedText(detail); box.exec()

    def _engines_ready(self, payload):
        self.data, self.enchanting, self.anvil = payload; self.assets = AssetProvider(self.data)
        self.loading.hide(); self.loading_label.setText(
            f"Data source: {self.data.source}" + (" • exact selected-version local data" if self.data.exact_local_data else " • fallback/other local version; source shown with results")
        )
        self._build_enchanting_tab(); self._build_anvil_tab(); self._build_rng_tab()

    # ----- Enchanting table -------------------------------------------------
    def _build_enchanting_tab(self):
        page = QWidget(); root = QVBoxLayout(page); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(10)
        expl = ExplanationCard("How to use this", "Choose the item you would place in an enchanting table, set the number of valid bookshelves, then roll the three displayed offers. The seed is exposed as an advanced reproducibility control; ordinary players can ignore it.")
        root.addWidget(expl)

        table = QFrame(); table.setObjectName("ToolConfigCard"); tv = QVBoxLayout(table)
        top = QHBoxLayout(); self.enchant_item = ItemPicker(self.assets, "minecraft:diamond_pickaxe"); top.addWidget(self.enchant_item, 1)
        shelf_box = QVBoxLayout(); shelf_box.addWidget(QLabel("Bookshelves")); self.shelves = QSpinBox(); self.shelves.setRange(0, 15); self.shelves.setValue(15); self.shelves.setToolTip("Number of valid bookshelves powering the table, from 0 to the vanilla maximum of 15."); shelf_box.addWidget(self.shelves); top.addLayout(shelf_box)
        seed_box = QVBoxLayout(); seed_label = QLabel("Simulation seed (advanced)"); seed_box.addWidget(seed_label); self.seed = QSpinBox(); self.seed.setRange(-2_147_483_647, 2_147_483_647); self.seed.setValue(12345); self.seed.setToolTip("Deterministic simulator seed used to reproduce the same three offers. This is not the world seed."); seed_box.addWidget(self.seed); top.addLayout(seed_box); tv.addLayout(top)
        roll = QPushButton("Refresh table offers"); roll.setObjectName("PrimaryButton"); roll.clicked.connect(self._roll); tv.addWidget(roll)

        self.offer_widgets = []
        for slot in range(1, 4):
            card = QFrame(); card.setObjectName("TradeCard"); row = QHBoxLayout(card); row.setContentsMargins(12, 9, 12, 9)
            number = QLabel(str(slot)); number.setObjectName("MetricValue"); number.setFixedWidth(34); row.addWidget(number)
            text = QLabel("Roll offers to preview this slot."); text.setWordWrap(True); row.addWidget(text, 1)
            cost = QLabel("— levels\n— lapis"); cost.setAlignment(Qt.AlignRight | Qt.AlignVCenter); cost.setObjectName("Accent"); row.addWidget(cost)
            tv.addWidget(card); self.offer_widgets.append((text, cost))
        root.addWidget(table)
        source = ExplanationCard("Model/source", "Installed enchantment definitions are preferred. The simulator reports a labeled baseline when selected-version data is unavailable; treasure-only enchantments are excluded from normal table rolls.")
        root.addWidget(source); root.addStretch(); self.tabs.addTab(page, "Enchanting Table"); self._roll()

    def _roll(self):
        if self.enchanting is None: return
        offers = self.enchanting.roll_offers(self.enchant_item.value(), self.shelves.value(), self.seed.value())
        for index, offer in enumerate(offers[:3]):
            enchants = offer.get("enchantments", [])
            if enchants:
                label = ", ".join(f"{_pretty_id(row.get('id', ''))} {row.get('level', 1)}" for row in enchants)
            else:
                label = "No compatible enchantment produced by this model roll"
            self.offer_widgets[index][0].setText(label)
            self.offer_widgets[index][1].setText(f"Displayed: {offer.get('displayed_cost', '?')}\nLapis: {offer.get('lapis_cost', '?')}")

    # ----- Anvil ------------------------------------------------------------
    def _build_anvil_tab(self):
        page = QWidget(); root = QVBoxLayout(page); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(10)
        root.addWidget(ExplanationCard("What this planner models", "Build an enchantment combination visually: choose the item, add enchantments to the left item and the sacrifice/book, then compare level cost and prior-work penalty. Durability repair/material consumption is deliberately not invented by this planner."))

        slots = QFrame(); slots.setObjectName("ToolConfigCard"); grid = QGridLayout(slots); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)
        grid.addWidget(QLabel("LEFT ITEM"), 0, 0); grid.addWidget(QLabel("SACRIFICE / BOOK"), 0, 2); grid.addWidget(QLabel("RESULT"), 0, 4)
        self.anvil_item = ItemPicker(self.assets, "minecraft:diamond_pickaxe"); self.sacrifice_item = ItemPicker(self.assets, "minecraft:enchanted_book")
        arrow1 = QLabel("+"); arrow1.setObjectName("TradeOperator"); arrow1.setAlignment(Qt.AlignCenter); arrow2 = QLabel("→"); arrow2.setObjectName("TradeArrow"); arrow2.setAlignment(Qt.AlignCenter)
        self.anvil_result_icon = QLabel(); self.anvil_result_icon.setFixedSize(48, 48); self.anvil_result_icon.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.anvil_item, 1, 0); grid.addWidget(arrow1, 1, 1); grid.addWidget(self.sacrifice_item, 1, 2); grid.addWidget(arrow2, 1, 3); grid.addWidget(self.anvil_result_icon, 1, 4)
        self.left_enchants = EnchantmentEditor(self.enchanting.enchantments); self.right_enchants = EnchantmentEditor(self.enchanting.enchantments)
        self.left_enchants.set_values({"minecraft:efficiency": 4}); self.right_enchants.set_values({"minecraft:efficiency": 4, "minecraft:unbreaking": 3})
        grid.addWidget(self.left_enchants, 2, 0, 1, 2); grid.addWidget(self.right_enchants, 2, 2, 1, 3)
        advanced = QHBoxLayout(); self.left_ops = QSpinBox(); self.left_ops.setRange(0, 20); self.right_ops = QSpinBox(); self.right_ops.setRange(0, 20); self.rename = QCheckBox("Rename result (+1 level)")
        advanced.addWidget(QLabel("Left prior anvil uses")); advanced.addWidget(self.left_ops); advanced.addWidget(QLabel("Sacrifice prior anvil uses")); advanced.addWidget(self.right_ops); advanced.addWidget(self.rename); advanced.addStretch(); grid.addLayout(advanced, 3, 0, 1, 5)
        combine = QPushButton("Combine"); combine.setObjectName("PrimaryButton"); combine.clicked.connect(self._combine); grid.addWidget(combine, 4, 0, 1, 5); root.addWidget(slots)

        metrics = QHBoxLayout(); self.cost_metric = MetricCard("Level cost"); self.penalty_metric = MetricCard("New prior-work penalty"); self.expensive_metric = MetricCard("Survival status")
        metrics.addWidget(self.cost_metric); metrics.addWidget(self.penalty_metric); metrics.addWidget(self.expensive_metric); root.addLayout(metrics)
        self.anvil_summary = ExplanationCard("Result", "Configure the two sides and press Combine."); root.addWidget(self.anvil_summary); root.addStretch(); self.tabs.addTab(page, "Anvil"); self._combine()

    def _combine(self):
        if self.anvil is None: return
        try:
            result = self.anvil.combine(
                self.anvil_item.value(), self.left_enchants.values(), self.right_enchants.values(),
                self.left_ops.value(), self.right_ops.value(), self.rename.isChecked(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Anvil", str(exc)); return
        self.anvil_result_icon.setPixmap(self.assets.icon(self.anvil_item.value(), 44).pixmap(QSize(44, 44)))
        self.cost_metric.set_value(result.get("total_level_cost", "—")); self.penalty_metric.set_value(result.get("new_prior_work_penalty", "—")); self.expensive_metric.set_value("Too expensive" if result.get("survival_too_expensive") else "Allowed")
        enchants = result.get("result_enchantments", {})
        enchant_text = ", ".join(f"{_pretty_id(key)} {value}" for key, value in enchants.items()) or "No enchantments"
        sacrifice = self.sacrifice_item.value()
        self.anvil_summary.set_text(
            f"{_pretty_id(self.anvil_item.value())} + {_pretty_id(sacrifice)} → {enchant_text}. "
            f"Level cost {result.get('total_level_cost', '?')}; new prior-work penalty {result.get('new_prior_work_penalty', '?')}. "
            f"Source: {result.get('source', 'F3+ model')}. {result.get('note', '')}"
        )

    # ----- RNG explorer -----------------------------------------------------
    def _build_rng_tab(self):
        page = QWidget(); root = QVBoxLayout(page); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(8)
        root.addWidget(ExplanationCard("RNG tools", "Choose a task below. Probability, timelines, Java LCG state recovery and EnchantmentCracker stay in this workbench, but each opens its own explained input/result panel instead of dumping raw dictionaries here."))
        split = QSplitter(Qt.Horizontal); root.addWidget(split, 1)
        left = QWidget(); lv = QVBoxLayout(left); self.rng_query = QLineEdit(); self.rng_query.setPlaceholderText("Search probability/recovery tools…"); lv.addWidget(self.rng_query)
        self.rng_list = QListWidget(); lv.addWidget(self.rng_list, 1); split.addWidget(left)
        right = QFrame(); right.setObjectName("ExplorerTrades"); rv = QVBoxLayout(right); self.rng_title = QLabel("Choose an RNG operation"); self.rng_title.setObjectName("WorkspaceTitle"); rv.addWidget(self.rng_title); self.rng_help = QLabel(); self.rng_help.setWordWrap(True); self.rng_help.setObjectName("Muted"); rv.addWidget(self.rng_help); self.rng_open = QPushButton("Open operation"); self.rng_open.setObjectName("PrimaryButton"); rv.addWidget(self.rng_open); rv.addStretch(); split.addWidget(right); split.setSizes([390, 650])
        self.rng_modes = [mode for mode in modes_for(self.tool) if mode.legacy is not None]
        self.rng_query.textChanged.connect(self._refresh_rng); self.rng_list.itemSelectionChanged.connect(self._rng_selected); self.rng_open.clicked.connect(self._run_rng); self._refresh_rng(); self.tabs.addTab(page, "RNG / Recovery / Probability")

    def _refresh_rng(self):
        query = self.rng_query.text().strip().lower(); self.rng_list.clear()
        for index, mode in enumerate(self.rng_modes):
            if query and query not in mode.name.lower(): continue
            item = QListWidgetItem(mode.name); item.setData(Qt.UserRole, index); self.rng_list.addItem(item)
        if self.rng_list.count(): self.rng_list.setCurrentRow(0)

    def _rng_selected(self):
        item = self.rng_list.currentItem()
        if item is None: return
        mode = self.rng_modes[int(item.data(Qt.UserRole))]; self.rng_title.setText(mode.name)
        if mode.name == "Enchantment RNG Seed Cracker":
            text = "Launches the pinned/verified community EnchantmentCracker for gameplay/player enchanting RNG recovery. This is not world-seed recovery."
        elif "Recovery" in mode.name or "Inspector" in mode.name:
            text = "Advanced Java/player RNG state tool. The opened panel explains every observation/state field before execution."
        elif "Probability" in mode.name or "Odds" in mode.name:
            text = "Probability planner showing attempts, chance of at least one success, and confidence thresholds where supported."
        else:
            text = "Deterministic RNG/enchanting helper. Open it for operation-specific inputs and a structured result."
        self.rng_help.setText(text)

    def _run_rng(self):
        item = self.rng_list.currentItem()
        if item is None: return
        mode = self.rng_modes[int(item.data(Qt.UserRole))]
        if mode.name == "Enchantment RNG Seed Cracker":
            try: launch_enchantment_cracker()
            except Exception as exc: QMessageBox.warning(self, "RNG Cracker", str(exc))
            return
        OperationDialog(self.tool, self.executor, self.owner.settings, self, mode.key).exec()

    def closeEvent(self, event):
        if self._load_job is not None:
            try: self._load_job.cancel()
            except Exception: pass
        super().closeEvent(event)


class ParentTraits(QFrame):
    """Breeding trait editor that produces the engine's compact parent dictionary."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent); self.setObjectName("ToolConfigCard"); self.title = QLabel(title); self.title.setObjectName("DeckLabel")
        self.root = QVBoxLayout(self); self.root.setContentsMargins(9, 8, 9, 8); self.root.addWidget(self.title); self.fields = {}

    def clear_fields(self):
        while self.root.count() > 1:
            item = self.root.takeAt(1); widget = item.widget()
            if widget is not None: widget.deleteLater()
        self.fields = {}

    def add_number(self, key: str, label: str, value: float, minimum: float, maximum: float, decimals=3):
        row = QWidget(); layout = QHBoxLayout(row); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(QLabel(label)); spin = QDoubleSpinBox(); spin.setRange(minimum, maximum); spin.setDecimals(decimals); spin.setValue(value); layout.addWidget(spin, 1); self.root.addWidget(row); self.fields[key] = spin

    def add_choice(self, key: str, label: str, options, value=None):
        row = QWidget(); layout = QHBoxLayout(row); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(QLabel(label)); combo = QComboBox(); combo.addItems([str(v) for v in options]);
        if value is not None: combo.setCurrentText(str(value))
        layout.addWidget(combo, 1); self.root.addWidget(row); self.fields[key] = combo

    def values(self):
        out = {}
        for key, widget in self.fields.items():
            if isinstance(widget, QDoubleSpinBox): out[key] = widget.value()
            elif isinstance(widget, QSpinBox): out[key] = widget.value()
            elif isinstance(widget, QComboBox):
                text = widget.currentText(); out[key] = int(text) if text.lstrip("-").isdigit() else text
        return out


class MechanicsLabDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner; self.brewing = BrewingEngine(); self.animals = AnimalBreedingEngine(); self.data = MinecraftJarData(owner.settings.minecraft_version); self.assets = AssetProvider(self.data)
        self.setWindowTitle("Minecraft Mechanics Lab"); self.resize(1120, 800); self.setMinimumSize(940, 680)
        root = QVBoxLayout(self); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(8)
        hero = QFrame(); hero.setObjectName("ExplorerHero"); hv = QVBoxLayout(hero); title = QLabel("Minecraft Mechanics Lab"); title.setObjectName("WorkspaceTitle"); hv.addWidget(title); intro = QLabel("Interact with brewing, leather dyeing/cauldrons, and breeding through game concepts. Internal NBT/JSON is never required for normal use."); intro.setObjectName("Muted"); intro.setWordWrap(True); hv.addWidget(intro); root.addWidget(hero)
        tabs = QTabWidget(); root.addWidget(tabs, 1); self._build_brewing(tabs); self._build_dye(tabs); self._build_breeding(tabs)
        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close)

    def _build_brewing(self, tabs):
        page = QWidget(); root = QVBoxLayout(page); root.setContentsMargins(12, 12, 12, 12); root.addWidget(ExplanationCard("Brewing stand", "Choose the potion currently in the bottle slot and the ingredient placed above it. The result shows the exact transition modeled by the vanilla-rule baseline and explains when the combination is invalid."))
        stand = QFrame(); stand.setObjectName("ToolConfigCard"); grid = QGridLayout(stand)
        grid.addWidget(QLabel("INPUT BOTTLE"), 0, 0); grid.addWidget(QLabel("INGREDIENT"), 0, 2); grid.addWidget(QLabel("OUTPUT"), 0, 4)
        self.potion = QComboBox(); self.potion.addItems(sorted(BASE_POTIONS)); self.ingredient = QComboBox(); self.ingredient.addItems(self.brewing.ingredients())
        for index in range(self.ingredient.count()): self.ingredient.setItemIcon(index, self.assets.icon("minecraft:" + self.ingredient.itemText(index), 22))
        self.brew_result_icon = QLabel(); self.brew_result_icon.setFixedSize(48, 48); self.brew_result_icon.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.potion, 1, 0); plus = QLabel("+"); plus.setObjectName("TradeOperator"); plus.setAlignment(Qt.AlignCenter); grid.addWidget(plus, 1, 1); grid.addWidget(self.ingredient, 1, 2); arrow = QLabel("→"); arrow.setObjectName("TradeArrow"); arrow.setAlignment(Qt.AlignCenter); grid.addWidget(arrow, 1, 3); grid.addWidget(self.brew_result_icon, 1, 4)
        run = QPushButton("Brew"); run.setObjectName("PrimaryButton"); grid.addWidget(run, 2, 0, 1, 5); root.addWidget(stand)
        self.brew_name = MetricCard("Output potion"); self.brew_effect = MetricCard("Effect"); self.brew_duration = MetricCard("Duration"); metrics = QHBoxLayout(); metrics.addWidget(self.brew_name); metrics.addWidget(self.brew_effect); metrics.addWidget(self.brew_duration); root.addLayout(metrics); self.brew_explain = ExplanationCard("Transition", "Choose an input and ingredient."); root.addWidget(self.brew_explain); root.addStretch(); run.clicked.connect(self._brew); tabs.addTab(page, "Brewing Stand"); self._brew()

    def _brew(self):
        result = self.brewing.brew(BASE_POTIONS[self.potion.currentText()], self.ingredient.currentText()); out = result.get("output"); potion = getattr(out, "potion", "unknown"); effect = getattr(out, "effect", "—"); duration = getattr(out, "duration_seconds", None)
        self.brew_name.set_value(_pretty_id(potion)); self.brew_effect.set_value(effect); self.brew_duration.set_value("Instant" if duration == 0 else (f"{duration}s" if duration is not None else "—")); self.brew_result_icon.setPixmap(self.assets.icon("minecraft:potion", 42).pixmap(QSize(42, 42))); self.brew_explain.set_text(f"{result.get('note', '')} Source: {result.get('source', 'F3+ brewing model')}.")

    def _build_dye(self, tabs):
        page = QWidget(); root = QVBoxLayout(page); root.setContentsMargins(12, 12, 12, 12); root.addWidget(ExplanationCard("Leather dye & cauldron", "Select dye colors to preview the resulting leather color. Washing is a separate cauldron action: it removes the custom leather color and consumes one water level; Java Edition does not mix dye in cauldron water."))
        self.existing = QLineEdit(); self.existing.setPlaceholderText("Optional existing leather color, e.g. #A06540"); root.addWidget(self.existing)
        dyes = QFrame(); dyes.setObjectName("ToolConfigCard"); grid = QGridLayout(dyes); self.dye_checks = {}
        for index, (name, rgb) in enumerate(DYE_COLORS.items()):
            check = QCheckBox(name.replace("_", " ").title()); check.setStyleSheet(f"QCheckBox {{ padding: 7px; border-left: 14px solid #{rgb:06X}; }}"); grid.addWidget(check, index // 4, index % 4); self.dye_checks[name] = check
        root.addWidget(dyes); actions = QHBoxLayout(); mix = QPushButton("Mix selected dyes"); mix.setObjectName("PrimaryButton"); self.water = QSpinBox(); self.water.setRange(0, 3); self.water.setValue(3); wash = QPushButton("Wash dyed leather"); actions.addWidget(mix); actions.addStretch(); actions.addWidget(QLabel("Cauldron water level")); actions.addWidget(self.water); actions.addWidget(wash); root.addLayout(actions)
        self.color_preview = QFrame(); self.color_preview.setMinimumHeight(90); self.color_preview.setObjectName("ResultSection"); root.addWidget(self.color_preview); self.dye_explain = ExplanationCard("Result", "Select one or more dyes."); root.addWidget(self.dye_explain); root.addStretch(); mix.clicked.connect(self._dye); wash.clicked.connect(self._wash); tabs.addTab(page, "Leather Dye & Cauldron")

    def _dye(self):
        existing = self.existing.text().strip(); current = None
        if existing:
            try: current = int(existing.removeprefix("#"), 16)
            except ValueError: return QMessageBox.warning(self, "Leather Dye", "Existing color must be a six-digit RGB hex value such as #A06540.")
        names = [name for name, check in self.dye_checks.items() if check.isChecked()]; result = dye_mix(current, names); color = result.get("hex", "#A06540"); self.color_preview.setStyleSheet(f"QFrame#ResultSection {{ background: {color}; border: 2px solid #000000; }}"); self.dye_explain.set_text(f"Resulting leather color: {color}. Selected dyes: {', '.join(name.replace('_', ' ').title() for name in result.get('dyes', [])) or 'none' }.")

    def _wash(self):
        result = cauldron_wash(self.water.value(), True); self.water.setValue(int(result.get("water_after", self.water.value()))); self.color_preview.setStyleSheet(f"QFrame#ResultSection {{ background: {result.get('result_color', '#A06540')}; border: 2px solid #000000; }}"); self.dye_explain.set_text(result.get("reason", ""))

    def _build_breeding(self, tabs):
        page = QWidget(); root = QVBoxLayout(page); root.setContentsMargins(12, 12, 12, 12); root.addWidget(ExplanationCard("Breeding simulator", "Pick an animal and edit only breeding-relevant traits. F3+ converts these controls to the compact engine representation internally; UUIDs, brain memories, positions, timers and raw NBT are not part of this UI."))
        species_row = QHBoxLayout(); species_row.addWidget(QLabel("Species")); self.species = QComboBox(); self.species.addItems(self.animals.species()); species_row.addWidget(self.species, 1); self.children = QSpinBox(); self.children.setRange(1, 100000); self.children.setValue(1000); self.children.setToolTip("Number of simulated offspring used to estimate the distribution."); species_row.addWidget(QLabel("Offspring")); species_row.addWidget(self.children); self.breed_seed = QSpinBox(); self.breed_seed.setRange(-2_147_483_647, 2_147_483_647); self.breed_seed.setValue(12345); self.breed_seed.setToolTip("Reproducibility seed for this simulator, not the world seed."); species_row.addWidget(QLabel("Simulation seed")); species_row.addWidget(self.breed_seed); root.addLayout(species_row)
        parents = QHBoxLayout(); self.parent_a = ParentTraits("PARENT A"); self.parent_b = ParentTraits("PARENT B"); parents.addWidget(self.parent_a); parents.addWidget(self.parent_b); root.addLayout(parents)
        profile = QLabel(); profile.setObjectName("Muted"); profile.setWordWrap(True); self.breed_profile = profile; root.addWidget(profile); run = QPushButton("Simulate offspring"); run.setObjectName("PrimaryButton"); run.clicked.connect(self._breed); root.addWidget(run)
        metrics = QHBoxLayout(); self.child_metric = MetricCard("Offspring simulated"); self.unique_metric = MetricCard("Distinct outcomes"); self.food_metric = MetricCard("Breeding food"); metrics.addWidget(self.child_metric); metrics.addWidget(self.unique_metric); metrics.addWidget(self.food_metric); root.addLayout(metrics)
        self.outcomes = QListWidget(); root.addWidget(self.outcomes, 1); self.breed_note = ExplanationCard("Interpretation", "Run the simulation to see common trait outcomes."); root.addWidget(self.breed_note); self.species.currentTextChanged.connect(self._configure_species); tabs.addTab(page, "Animal & Horse Breeding"); self._configure_species(); self._breed()

    def _configure_species(self):
        species = self.species.currentText(); profile = self.animals.profile(species); mode = profile.get("mode", "parent_variant")
        for editor in (self.parent_a, self.parent_b):
            editor.clear_fields()
            if mode == "horse":
                editor.add_number("max_health", "Max health", 22.5, 15.0, 30.0, 2); editor.add_number("movement_speed", "Movement speed", 0.225, 0.1125, 0.3375, 4); editor.add_number("jump_strength", "Jump strength", 0.7, 0.4, 1.0, 3); editor.add_choice("color", "Coat color index", range(7), 0); editor.add_choice("markings", "Markings index", range(5), 0)
            elif mode == "sheep": editor.add_choice("Color", "Wool color index", range(16), 0)
            elif mode == "rabbit": editor.add_choice("RabbitType", "Rabbit type", range(6), 0)
            elif mode == "panda":
                genes = ["normal", "lazy", "worried", "playful", "brown", "weak", "aggressive"]; editor.add_choice("MainGene", "Main gene", genes, "normal"); editor.add_choice("HiddenGene", "Hidden gene", genes, "normal")
            elif mode == "axolotl": editor.add_choice("Variant", "Variant", range(5), 0)
            else: editor.add_choice("variant", "Parent variant", ["default", "parent variant A", "parent variant B"], "default")
        self.breed_profile.setText(f"Food: {profile.get('food', 'varies')} • Inheritance model: {mode.replace('_', ' ')}. Only traits that influence this simulator are shown.")

    def _breed(self):
        species = self.species.currentText()
        try: result = self.animals.simulate(species, self.parent_a.values(), self.parent_b.values(), self.children.value(), self.breed_seed.value())
        except Exception as exc: return QMessageBox.warning(self, "Breeding", str(exc))
        self.child_metric.set_value(result.get("children", "—")); self.unique_metric.set_value(result.get("unique_outcomes", "—")); self.food_metric.set_value(result.get("profile", {}).get("food", "—")); self.outcomes.clear()
        for row in result.get("most_common_outcomes", [])[:50]:
            item = QListWidgetItem(f"{row.get('count', 0):,} ×  {_human_traits(row.get('nbt', {}))}"); self.outcomes.addItem(item)
        self.breed_note.set_text("The list shows the most common modeled offspring trait combinations. Internal entity bookkeeping is intentionally omitted. " + str(result.get("note", "")))
