from __future__ import annotations

"""2.5 UX wrappers for dedicated workbenches.

The underlying dedicated workbenches already provide the correct Minecraft-oriented
controls. These wrappers make compact controls self-explanatory and correct cramped
layouts without changing simulation logic.
"""

from .async_loot_workbench import LootWorkbenchDialog
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
    """Give anvil enchantment controls enough room to render labels at Windows DPI."""
    editor.setMinimumHeight(205)
    editor.choice.setMinimumWidth(170)
    editor.level.setMinimumWidth(72)
    editor.list.setMinimumHeight(88)
    editor.list.setMaximumHeight(112)


def _polish_anvil_grid(left_editor) -> None:
    """Reserve distinct rows for enchantments and prior-work controls."""
    slots = left_editor.parentWidget()
    if slots is None: return
    slots.setMinimumHeight(390)
    layout = slots.layout()
    if layout is None: return
    try:
        layout.setRowMinimumHeight(2, 210)
        layout.setRowMinimumHeight(3, 42)
        layout.setVerticalSpacing(10)
    except Exception:
        pass


class RngEnchantingDialog(_RngEnchantingDialog):
    def _engines_ready(self, payload):
        super()._engines_ready(payload)
        _polish_enchantment_editor(self.left_enchants); _polish_enchantment_editor(self.right_enchants); _polish_anvil_grid(self.left_enchants)
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
