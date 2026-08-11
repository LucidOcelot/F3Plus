from __future__ import annotations

"""Player-facing wrappers for the dedicated 2.5 workbenches."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidgetItem, QPushButton,
    QScrollArea, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from .async_jobs import start_job
from .async_loot_workbench import LootWorkbenchDialog as _AsyncLootWorkbenchDialog
from .minecraft_simulators import EnchantingEngine
from .minecraft_widgets import EnchantmentEditor, ExplanationCard, ItemPicker, MetricCard
from .simulation_workbenches import (
    MechanicsLabDialog as _MechanicsLabDialog,
    RngEnchantingDialog as _RngEnchantingDialog,
    _pretty_id,
)
from .ux_semantics25 import DEFAULT_SEED_TEXT, grouped_enchantment_text, seed_value
from .villager_workbench import VillagerExplorerDialog as _VillagerExplorerDialog


def _help(widget, text: str) -> None:
    if widget is None: return
    widget.setToolTip(text); widget.setAccessibleDescription(text)


def _metric_label(card, text: str) -> None:
    for label in card.findChildren(QLabel):
        if label.objectName() == "MetricLabel":
            label.setText(text)
            return


def _polish_enchantment_editor(editor) -> None:
    editor.setMinimumHeight(178); editor.choice.setMinimumWidth(170); editor.level.setMinimumWidth(72); editor.list.setMinimumHeight(72); editor.list.setMaximumHeight(96)


def _replace_seed_widget(owner, name: str) -> QLineEdit:
    old = getattr(owner, name); field = QLineEdit(DEFAULT_SEED_TEXT); field.setClearButtonEnabled(True)
    field.setToolTip("Optional reproducibility seed. Blank uses F3Plus; numbers and text are both accepted.")
    parent = old.parentWidget(); layout = parent.layout() if parent is not None else None
    if layout is not None: layout.replaceWidget(old, field)
    old.hide(); old.deleteLater(); setattr(owner, name, field); return field


def _seed_text(widget) -> str:
    if hasattr(widget, "text"):
        return str(widget.text()).strip() or DEFAULT_SEED_TEXT
    if hasattr(widget, "value"):
        return str(widget.value())
    return DEFAULT_SEED_TEXT


def _book_text(engine: EnchantingEngine) -> str:
    return grouped_enchantment_text(engine.possible_book_enchantments())


class RngEnchantingDialog(_RngEnchantingDialog):
    def _build_anvil_tab(self):
        page = QWidget(); outer = QVBoxLayout(page); outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame); outer.addWidget(scroll)
        body = QWidget(); root = QVBoxLayout(body); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(10); scroll.setWidget(body)

        root.addWidget(ExplanationCard("Anvil planner", "Choose the kept item and sacrifice, add their enchantments, then set prior anvil uses. The result shows level cost and prior-work penalty."))

        transaction = QFrame(); transaction.setObjectName("ToolConfigCard"); tv = QVBoxLayout(transaction); tv.setContentsMargins(10, 9, 10, 9); tv.setSpacing(7)
        labels = QHBoxLayout(); left_label = QLabel("LEFT ITEM"); left_label.setObjectName("DeckLabel"); sacrifice_label = QLabel("SACRIFICE / BOOK"); sacrifice_label.setObjectName("DeckLabel"); result_label = QLabel("RESULT"); result_label.setObjectName("DeckLabel")
        labels.addWidget(left_label, 5); labels.addWidget(QLabel(""), 1); labels.addWidget(sacrifice_label, 5); labels.addWidget(QLabel(""), 1); labels.addWidget(result_label, 1); tv.addLayout(labels)
        items = QHBoxLayout(); self.anvil_item = ItemPicker(self.assets, "minecraft:diamond_pickaxe"); self.sacrifice_item = ItemPicker(self.assets, "minecraft:enchanted_book")
        plus = QLabel("+"); plus.setObjectName("TradeOperator"); plus.setAlignment(Qt.AlignCenter); plus.setFixedWidth(28)
        arrow = QLabel("→"); arrow.setObjectName("TradeArrow"); arrow.setAlignment(Qt.AlignCenter); arrow.setFixedWidth(34)
        self.anvil_result_icon = QLabel(); self.anvil_result_icon.setFixedSize(48, 48); self.anvil_result_icon.setAlignment(Qt.AlignCenter)
        items.addWidget(self.anvil_item, 5); items.addWidget(plus); items.addWidget(self.sacrifice_item, 5); items.addWidget(arrow); items.addWidget(self.anvil_result_icon); tv.addLayout(items); root.addWidget(transaction)

        enchantments = QFrame(); enchantments.setObjectName("ToolConfigCard"); ev = QVBoxLayout(enchantments); ev.setContentsMargins(10, 9, 10, 9); ev.setSpacing(7)
        title = QLabel("ENCHANTMENTS"); title.setObjectName("DeckLabel"); ev.addWidget(title); editors = QHBoxLayout(); editors.setSpacing(12)
        left_box = QVBoxLayout(); left_box.addWidget(QLabel("Existing on left item")); self.left_enchants = EnchantmentEditor(self.enchanting.enchantments); self.left_enchants.set_values({"minecraft:efficiency": 4}); _polish_enchantment_editor(self.left_enchants); left_box.addWidget(self.left_enchants)
        right_box = QVBoxLayout(); right_box.addWidget(QLabel("Supplied by sacrifice / book")); self.right_enchants = EnchantmentEditor(self.enchanting.enchantments); self.right_enchants.set_values({"minecraft:efficiency": 4, "minecraft:unbreaking": 3}); _polish_enchantment_editor(self.right_enchants); right_box.addWidget(self.right_enchants)
        editors.addLayout(left_box, 1); editors.addLayout(right_box, 1); ev.addLayout(editors); root.addWidget(enchantments)

        prior = QFrame(); prior.setObjectName("ToolConfigCard"); pv = QHBoxLayout(prior); pv.setContentsMargins(10, 8, 10, 8); pv.setSpacing(8)
        prior_title = QLabel("PRIOR WORK"); prior_title.setObjectName("DeckLabel"); pv.addWidget(prior_title); pv.addSpacing(8)
        pv.addWidget(QLabel("Left uses")); self.left_ops = QSpinBox(); self.left_ops.setRange(0, 20); self.left_ops.setMinimumWidth(74); pv.addWidget(self.left_ops)
        pv.addSpacing(12); pv.addWidget(QLabel("Sacrifice uses")); self.right_ops = QSpinBox(); self.right_ops.setRange(0, 20); self.right_ops.setMinimumWidth(74); pv.addWidget(self.right_ops)
        pv.addSpacing(12); self.rename = QCheckBox("Rename (+1 level)"); pv.addWidget(self.rename); pv.addStretch(); root.addWidget(prior)

        combine = QPushButton("Combine"); combine.setObjectName("PrimaryButton"); combine.setMinimumHeight(38); combine.clicked.connect(self._combine); root.addWidget(combine)
        metrics = QHBoxLayout(); self.cost_metric = MetricCard("Level cost"); self.penalty_metric = MetricCard("New prior-work penalty"); self.expensive_metric = MetricCard("Survival status")
        metrics.addWidget(self.cost_metric); metrics.addWidget(self.penalty_metric); metrics.addWidget(self.expensive_metric); root.addLayout(metrics)
        self.anvil_summary = ExplanationCard("Result", "Configure the two sides and press Combine."); root.addWidget(self.anvil_summary); root.addStretch(); self.tabs.addTab(page, "Anvil"); self._combine()

    def _engines_ready(self, payload):
        super()._engines_ready(payload)
        _replace_seed_widget(self, "seed"); self._roll()
        _help(self.enchant_item, "Choose the item to enchant.")
        _help(self.shelves, "Valid bookshelves around the table, 0–15.")
        _help(self.anvil_item, "Item kept by the anvil operation.")
        _help(self.sacrifice_item, "Item or enchanted book consumed by the anvil operation.")
        _help(self.left_ops, "Previous anvil uses on the kept item.")
        _help(self.right_ops, "Previous anvil uses on the sacrifice.")

    def _roll(self):
        if self.enchanting is None or not hasattr(self, "enchant_item"): return
        text = _seed_text(getattr(self, "seed", None)); numeric = seed_value(text)
        offers = self.enchanting.roll_offers(self.enchant_item.value(), self.shelves.value(), numeric)
        for index, offer in enumerate(offers[:3]):
            enchants = offer.get("enchantments", [])
            label = ", ".join(f"{_pretty_id(row.get('id', ''))} {row.get('level', 1)}" for row in enchants) if enchants else "No compatible enchantment in this roll"
            self.offer_widgets[index][0].setText(label); self.offer_widgets[index][1].setText(f"Cost: {offer.get('displayed_cost', '?')}\nLapis: {offer.get('lapis_cost', '?')}")


class MechanicsLabDialog(_MechanicsLabDialog):
    def __init__(self, owner):
        super().__init__(owner)
        _replace_seed_widget(self, "breed_seed")
        for tabs in self.findChildren(QTabWidget):
            for index in range(tabs.count()):
                if "Breeding" in tabs.tabText(index): tabs.setTabText(index, "Horse & Donkey Breeding")
        _metric_label(self.child_metric, "Sample size")
        _metric_label(self.unique_metric, "Average health")
        _metric_label(self.food_metric, "Average speed")
        self._configure_species(); self._breed()
        _help(self.potion, "Potion currently in the bottle slot.")
        _help(self.ingredient, "Ingredient placed in the brewing stand.")
        _help(self.existing, "Existing leather color as RGB hex; leave blank for undyed leather.")
        _help(self.water, "Water level remaining in the cauldron, 0–3.")
        _help(self.species, "Horse and Donkey are shown because their inherited health, movement speed, and jump strength can be compared.")
        _help(self.children, "Number of offspring rolls used for the displayed stat range.")

    def _configure_species(self):
        if not hasattr(self, "species") or not hasattr(self, "parent_a"): return
        for editor_name, editor in (("Parent A", self.parent_a), ("Parent B", self.parent_b)):
            editor.clear_fields()
            editor.add_number("max_health", "Max health", 22.5, 15.0, 30.0, 2)
            editor.add_number("movement_speed", "Movement speed", 0.225, 0.1125, 0.3375, 4)
            editor.add_number("jump_strength", "Jump strength", 0.7, 0.4, 1.0, 3)
            _help(editor.fields.get("max_health"), f"{editor_name} maximum health in health points; 2 health points = 1 heart.")
            _help(editor.fields.get("movement_speed"), f"{editor_name} movement-speed attribute. This is an entity attribute, not blocks per second.")
            _help(editor.fields.get("jump_strength"), f"{editor_name} jump-strength attribute. This is an entity attribute, not jump height in blocks.")
        self.breed_profile.setText("Inherited stats only: max health, movement speed, and jump strength. Health uses points; speed and jump are entity attributes.")

    def _breed(self):
        if not hasattr(self, "species") or not hasattr(self, "parent_a"): return
        species = self.species.currentText(); numeric = seed_value(_seed_text(getattr(self, "breed_seed", None)))
        try: result = self.animals.simulate(species, self.parent_a.values(), self.parent_b.values(), self.children.value(), numeric)
        except Exception as exc:
            from PySide6.QtWidgets import QMessageBox
            return QMessageBox.warning(self, "Breeding", str(exc))
        stats = result.get("stats", {}); health = stats.get("max_health", {}); speed = stats.get("movement_speed", {}); jump = stats.get("jump_strength", {})
        self.child_metric.set_value(result.get("children", "—")); self.unique_metric.set_value(f"{health.get('mean', 0):.2f}"); self.food_metric.set_value(f"{speed.get('mean', 0):.4f}")
        self.outcomes.clear()
        for name, row, unit in (
            ("Max health", health, "health points"),
            ("Movement speed", speed, "entity attribute"),
            ("Jump strength", jump, "entity attribute"),
        ):
            self.outcomes.addItem(QListWidgetItem(f"{name}: min {row.get('minimum', 0):.4g} • average {row.get('mean', 0):.4g} • max {row.get('maximum', 0):.4g} ({unit})"))
        self.breed_note.set_text(f"Range across {result.get('children', 0):,} simulated {species.lower()} offspring.")


class LootWorkbenchDialog(_AsyncLootWorkbenchDialog):
    def __init__(self, *args, **kwargs):
        self._book_engine = None; self._seed_label = DEFAULT_SEED_TEXT
        super().__init__(*args, **kwargs)
        self.book_enchants = ExplanationCard("Possible enchanted-book rolls", ""); self.book_enchants.hide()
        self.layout().insertWidget(max(0, self.layout().count() - 2), self.book_enchants)

    def _engine_ready(self, payload):
        super()._engine_ready(payload); self._book_engine = EnchantingEngine(self.data); _replace_seed_widget(self, "seed"); self.load_current()

    def load_current(self, *_):
        super().load_current()
        if self.engine is None or self.tables.currentItem() is None or self._book_engine is None: return
        table_id = self.tables.currentItem().data(Qt.UserRole)
        has_book = any(str(row.get("item", "")).endswith("enchanted_book") for row in self.engine.possible_items(table_id))
        self.book_enchants.setVisible(has_book)
        if has_book:
            self.book_enchants.set_text(_book_text(self._book_engine))

    def run_sim(self, pulls: int):
        if self.engine is None or self._sim_job is not None: return
        item = self.tables.currentItem()
        if item is None: return
        table_id = item.data(Qt.UserRole); self._seed_label = _seed_text(self.seed); numeric = seed_value(self._seed_label)
        context = {"killed_by_player": self.killed.isChecked(), "include_contextual_entries": self.contextual.isChecked()}
        self.summary.setText(f"Simulating {pulls:,} pulls…"); self._show_activity(f"Simulating {pulls:,} pulls…"); self.cancel_sim.setEnabled(True)
        self._sim_job = start_job(lambda: self._simulate_cancellable(table_id, pulls, numeric, context), finished=self._simulation_finished, failed=self._simulation_failed, cancelled=self._simulation_cancelled)

    def _simulation_finished(self, result):
        super()._simulation_finished(result)
        self.summary.setText(f"{result['pulls']:,} pulls • seed {self._seed_label} • {len(result.get('stats', [])):,} item types • {result['source']}")


class VillagerExplorerDialog(_VillagerExplorerDialog):
    def __init__(self, owner, profession: str | None = None, mode: str = "Trade Browser"):
        super().__init__(owner, profession=profession, mode=mode); self._book_engine = EnchantingEngine(self.jar)
        _help(self.level, "Filter by villager level."); _help(self.direction, "Filter by trade direction."); _help(self.query, "Search item, enchantment, profession, or offer text."); _help(self.uses, "Planned uses for restock and emerald totals.")

    def show_selected(self):
        super().show_selected(); trade = self.selected_trade()
        if trade is None: return
        if trade.profession.lower() == "librarian" and "enchanted_book" in str(trade.gives).lower():
            base = self.detail_note.text.text().split("Possible enchantments:", 1)[0].rstrip()
            self.detail_note.set_text(base + "\n\nPossible enchantments:\n" + _book_text(self._book_engine))
