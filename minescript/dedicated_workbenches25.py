from __future__ import annotations

"""2.5 UX wrappers for dedicated workbenches.

The underlying dedicated workbenches provide the mechanic engines. These wrappers make
compact controls self-explanatory and correct layout problems without changing
simulation logic.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget,
)

from .async_loot_workbench import LootWorkbenchDialog
from .minecraft_widgets import EnchantmentEditor, ExplanationCard, ItemPicker, MetricCard
from .simulation_workbenches import (
    MechanicsLabDialog as _MechanicsLabDialog,
    RngEnchantingDialog as _RngEnchantingDialog,
)
from .villager_workbench import VillagerExplorerDialog as _VillagerExplorerDialog


def _help(widget, text: str) -> None:
    if widget is None: return
    widget.setToolTip(text)
    widget.setAccessibleDescription(text)


def _polish_enchantment_editor(editor) -> None:
    editor.setMinimumHeight(178)
    editor.choice.setMinimumWidth(170)
    editor.level.setMinimumWidth(72)
    editor.list.setMinimumHeight(72)
    editor.list.setMaximumHeight(96)


class RngEnchantingDialog(_RngEnchantingDialog):
    def _build_anvil_tab(self):
        """Minecraft-style anvil planner with independent vertical sections."""
        page = QWidget(); outer = QVBoxLayout(page); outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame); outer.addWidget(scroll)
        body = QWidget(); root = QVBoxLayout(body); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(10); scroll.setWidget(body)

        root.addWidget(ExplanationCard(
            "What this planner models",
            "Build an enchantment combination visually: choose the item and sacrifice/book, add their existing enchantments, set prior anvil uses, then compare level cost and prior-work penalty. Durability repair/material consumption is deliberately not invented by this planner."
        ))

        transaction = QFrame(); transaction.setObjectName("ToolConfigCard"); tv = QVBoxLayout(transaction); tv.setContentsMargins(10, 9, 10, 9); tv.setSpacing(7)
        labels = QHBoxLayout(); left_label = QLabel("LEFT ITEM"); left_label.setObjectName("DeckLabel"); sacrifice_label = QLabel("SACRIFICE / BOOK"); sacrifice_label.setObjectName("DeckLabel"); result_label = QLabel("RESULT"); result_label.setObjectName("DeckLabel")
        labels.addWidget(left_label, 5); labels.addWidget(QLabel(""), 1); labels.addWidget(sacrifice_label, 5); labels.addWidget(QLabel(""), 1); labels.addWidget(result_label, 1); tv.addLayout(labels)
        items = QHBoxLayout(); self.anvil_item = ItemPicker(self.assets, "minecraft:diamond_pickaxe"); self.sacrifice_item = ItemPicker(self.assets, "minecraft:enchanted_book")
        plus = QLabel("+"); plus.setObjectName("TradeOperator"); plus.setAlignment(Qt.AlignCenter); plus.setFixedWidth(28)
        arrow = QLabel("→"); arrow.setObjectName("TradeArrow"); arrow.setAlignment(Qt.AlignCenter); arrow.setFixedWidth(34)
        self.anvil_result_icon = QLabel(); self.anvil_result_icon.setFixedSize(48, 48); self.anvil_result_icon.setAlignment(Qt.AlignCenter)
        items.addWidget(self.anvil_item, 5); items.addWidget(plus); items.addWidget(self.sacrifice_item, 5); items.addWidget(arrow); items.addWidget(self.anvil_result_icon); tv.addLayout(items); root.addWidget(transaction)

        enchantments = QFrame(); enchantments.setObjectName("ToolConfigCard"); ev = QVBoxLayout(enchantments); ev.setContentsMargins(10, 9, 10, 9); ev.setSpacing(7)
        enchant_title = QLabel("ENCHANTMENTS ON EACH SIDE"); enchant_title.setObjectName("DeckLabel"); ev.addWidget(enchant_title)
        editors = QHBoxLayout(); editors.setSpacing(12)
        left_box = QVBoxLayout(); left_hint = QLabel("Existing on left item"); left_hint.setObjectName("Muted"); left_box.addWidget(left_hint)
        self.left_enchants = EnchantmentEditor(self.enchanting.enchantments); self.left_enchants.set_values({"minecraft:efficiency": 4}); _polish_enchantment_editor(self.left_enchants); left_box.addWidget(self.left_enchants)
        right_box = QVBoxLayout(); right_hint = QLabel("Supplied by sacrifice / book"); right_hint.setObjectName("Muted"); right_box.addWidget(right_hint)
        self.right_enchants = EnchantmentEditor(self.enchanting.enchantments); self.right_enchants.set_values({"minecraft:efficiency": 4, "minecraft:unbreaking": 3}); _polish_enchantment_editor(self.right_enchants); right_box.addWidget(self.right_enchants)
        editors.addLayout(left_box, 1); editors.addLayout(right_box, 1); ev.addLayout(editors); root.addWidget(enchantments)

        prior = QFrame(); prior.setObjectName("ToolConfigCard"); pv = QHBoxLayout(prior); pv.setContentsMargins(10, 8, 10, 8); pv.setSpacing(8)
        prior_title = QLabel("PRIOR WORK"); prior_title.setObjectName("DeckLabel"); pv.addWidget(prior_title); pv.addSpacing(8)
        pv.addWidget(QLabel("Left prior anvil uses")); self.left_ops = QSpinBox(); self.left_ops.setRange(0, 20); self.left_ops.setMinimumWidth(74); pv.addWidget(self.left_ops)
        pv.addSpacing(12); pv.addWidget(QLabel("Sacrifice prior anvil uses")); self.right_ops = QSpinBox(); self.right_ops.setRange(0, 20); self.right_ops.setMinimumWidth(74); pv.addWidget(self.right_ops)
        pv.addSpacing(12); self.rename = QCheckBox("Rename result (+1 level)"); pv.addWidget(self.rename); pv.addStretch(); root.addWidget(prior)

        combine = QPushButton("Combine in anvil"); combine.setObjectName("PrimaryButton"); combine.setMinimumHeight(38); combine.clicked.connect(self._combine); root.addWidget(combine)
        metrics = QHBoxLayout(); self.cost_metric = MetricCard("Level cost"); self.penalty_metric = MetricCard("New prior-work penalty"); self.expensive_metric = MetricCard("Survival status")
        metrics.addWidget(self.cost_metric); metrics.addWidget(self.penalty_metric); metrics.addWidget(self.expensive_metric); root.addLayout(metrics)
        self.anvil_summary = ExplanationCard("Result", "Configure the two sides and press Combine in anvil."); root.addWidget(self.anvil_summary)
        root.addStretch(); self.tabs.addTab(page, "Anvil"); self._combine()

    def _engines_ready(self, payload):
        super()._engines_ready(payload)
        _help(self.enchant_item, "Item placed into the enchanting table. The simulator filters offers to enchantments compatible with this item.")
        _help(self.shelves, "Number of valid bookshelves powering the table, from 0 to the Java Edition maximum of 15. This changes displayed enchantment levels and available offers.")
        _help(self.seed, "Reproducibility seed for the enchanting simulation only. It is not the Minecraft world seed and does not recover one.")
        _help(self.anvil_item, "Left/base item being kept by the anvil operation. Its existing enchantments and prior-work count contribute to the result cost.")
        _help(self.sacrifice_item, "Right/sacrifice item or enchanted book consumed by the anvil operation. Choose the visual item here, then add its enchantments below.")
        _help(self.left_enchants, "Enchantments already present on the left/base item. Add only the levels actually present before this combine operation.")
        _help(self.right_enchants, "Enchantments supplied by the right/sacrifice item or book. Incompatible or over-level combinations are handled by the anvil model.")
        _help(self.left_ops, "Number of prior anvil operations already recorded on the left item. Prior work increases the anvil penalty exponentially.")
        _help(self.right_ops, "Number of prior anvil operations already recorded on the sacrifice item/book. This contributes to the combined prior-work penalty.")
        _help(self.rename, "Add the vanilla rename action to this combine operation. Renaming adds one level to the modeled cost.")
        _help(self.rng_query, "Filter advanced RNG, probability, sequence, and recovery operations by task name. Selecting one shows its purpose before it opens.")


class MechanicsLabDialog(_MechanicsLabDialog):
    def __init__(self, owner):
        super().__init__(owner)
        _help(self.potion, "Potion currently in the brewing-stand bottle slot. The ingredient is applied to this exact potion state.")
        _help(self.ingredient, "Ingredient placed in the brewing stand. The output panel shows the modeled Java Edition transition or explains why no valid transition exists.")
        _help(self.existing, "Optional existing leather color as six-digit RGB hex, for example #A06540. Leave blank when dyeing undyed/default leather.")
        _help(self.water, "Current cauldron water level from 0 to 3. Washing dyed leather consumes one level when water is available.")
        _help(self.species, "Animal species being modeled. Parent controls below change to show only traits that affect inheritance for that species.")
        _help(self.children, "Number of modeled offspring used to estimate the outcome distribution. Larger samples take longer but reduce sampling noise.")
        _help(self.breed_seed, "Reproducibility seed for this breeding simulation only. It is not a Minecraft world seed.")

    def _configure_species(self):
        super()._configure_species()
        for editor_name, editor in (("Parent A", self.parent_a), ("Parent B", self.parent_b)):
            for key, widget in editor.fields.items():
                label = str(key).replace("_", " ").replace("MainGene", "main gene").replace("HiddenGene", "hidden gene")
                _help(widget, f"{editor_name} {label} used by the selected species' inheritance model. Only breeding-relevant traits are exposed; unrelated entity NBT is intentionally omitted.")


class VillagerExplorerDialog(_VillagerExplorerDialog):
    def __init__(self, owner, profession: str | None = None, mode: str = "Trade Browser"):
        super().__init__(owner, profession=profession, mode=mode)
        _help(self.level, "Filter offers by villager trade level. All levels leaves Novice through Master visible.")
        _help(self.direction, "Filter by transaction direction: items you buy from the villager, items the villager buys from you, or exchange-style offers.")
        _help(self.query, "Search every loaded trade by item, enchantment detail, profession, or offer text. Filtering does not truncate the underlying trade dataset.")
        _help(self.uses, "Number of times you plan to perform the selected trade. F3+ uses this to estimate required restocks and emerald flow.")
        _help(self.favorites_only, "Show only trades you previously marked as favorites. This is a local F3+ preference and does not change the Minecraft villager.")
        _help(self.profession_list, "Choose a profession or show all professions. Profession artwork is recovered from the installed Minecraft client when available.")
        _help(self.trade_view, "Virtualized list of every matching loaded offer. Selecting a trade opens its complete wants → gives transaction and planning details on the right.")
