from __future__ import annotations

"""Focused UX wrappers for dedicated Minecraft workbenches."""

from .async_loot_workbench import LootWorkbenchDialog
from .enchantment_catalog import grouped_summary, librarian_enchantments
from .minecraft_widgets import ExplanationCard, SeedEdit
from .simulation_workbenches import (
    MechanicsLabDialog as _MechanicsLabDialog,
    RngEnchantingDialog as _RngEnchantingDialog,
)
from .villager_workbench import VillagerExplorerDialog as _VillagerExplorerDialog


def _help(widget, text: str) -> None:
    if widget is None: return
    widget.setToolTip(text); widget.setAccessibleDescription(text)


def _replace_with_seed_edit(owner, attr: str) -> SeedEdit | None:
    old = getattr(owner, attr, None)
    if old is None: return None
    parent = old.parentWidget(); layout = parent.layout() if parent is not None else None
    replacement = SeedEdit("F3Plus", parent)
    if layout is not None: layout.replaceWidget(old, replacement)
    old.hide(); old.deleteLater(); setattr(owner, attr, replacement); return replacement


def _polish_enchantment_editor(editor) -> None:
    editor.setMinimumHeight(205); editor.choice.setMinimumWidth(170); editor.level.setMinimumWidth(72); editor.list.setMinimumHeight(88); editor.list.setMaximumHeight(112)


def _polish_anvil_grid(left_editor) -> None:
    slots = left_editor.parentWidget()
    if slots is None: return
    slots.setMinimumHeight(390); layout = slots.layout()
    if layout is None: return
    try:
        layout.setRowMinimumHeight(2, 210); layout.setRowMinimumHeight(3, 42); layout.setVerticalSpacing(10)
    except Exception: pass


def _reflow_anvil(dialog) -> None:
    left = getattr(dialog, "left_enchants", None); right = getattr(dialog, "right_enchants", None)
    if left is None or right is None: return
    _polish_enchantment_editor(left); _polish_enchantment_editor(right); _polish_anvil_grid(left)


class RngEnchantingDialog(_RngEnchantingDialog):
    def _engines_ready(self, payload):
        super()._engines_ready(payload); _reflow_anvil(self); _replace_with_seed_edit(self, "seed"); self._roll()
        self.loading_label.setText("Enchantments loaded from " + self.data.source + ("." if self.data.exact_local_data else " (fallback local data)."))
        _help(self.enchant_item, "Choose the item placed in the enchanting table.")
        _help(self.shelves, "Valid bookshelves powering the table, 0–15.")
        _help(self.seed, "Reproducibility seed for this simulator. Number or text; blank uses F3Plus.")
        _help(self.anvil_item, "Base item kept by the anvil operation.")
        _help(self.sacrifice_item, "Item or enchanted book consumed on the right side of the anvil.")
        _help(self.left_enchants, "Enchantments already on the base item.")
        _help(self.right_enchants, "Enchantments supplied by the sacrifice/book.")
        _help(self.left_ops, "Prior anvil uses already recorded on the base item.")
        _help(self.right_ops, "Prior anvil uses already recorded on the sacrifice/book.")
        _help(self.rename, "Include a rename in this anvil operation (+1 level).")
        _help(self.rng_query, "Filter RNG/recovery tools by name.")


class MechanicsLabDialog(_MechanicsLabDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.species.blockSignals(True); self.species.clear(); self.species.addItems(["Horse", "Donkey"]); self.species.blockSignals(False); self.species.setCurrentIndex(0); self._configure_species()
        _replace_with_seed_edit(self, "breed_seed"); self._breed()
        _help(self.potion, "Potion currently in the brewing-stand bottle slot.")
        _help(self.ingredient, "Ingredient placed in the brewing stand.")
        _help(self.existing, "Optional existing leather RGB color, e.g. #A06540.")
        _help(self.water, "Current cauldron water level, 0–3.")
        _help(self.species, "Horse or donkey. These are simulated because health, movement speed, and jump strength are inherited through breeding.")
        _help(self.children, "Number of offspring rolls used for the displayed stat distribution.")
        _help(self.breed_seed, "Reproducibility seed for this breeding simulation. Number or text; blank uses F3Plus.")

    def _configure_species(self):
        super()._configure_species()
        for editor_name, editor in (("Parent A", self.parent_a), ("Parent B", self.parent_b)):
            for key, widget in editor.fields.items():
                label = str(key).replace("_", " ")
                units = "health points" if key == "max_health" else ("base movement-speed attribute" if key == "movement_speed" else ("jump-strength attribute" if key == "jump_strength" else "appearance index"))
                _help(widget, f"{editor_name} {label}: {units}.")


class VillagerExplorerDialog(_VillagerExplorerDialog):
    def __init__(self, owner, profession: str | None = None, mode: str = "Trade Browser"):
        super().__init__(owner, profession=profession, mode=mode)
        self.book_enchants = ExplanationCard("Possible enchanted-book enchantments", "")
        host = self.detail_note.parentWidget(); layout = host.layout() if host is not None else None
        if layout is not None: layout.insertWidget(layout.indexOf(self.detail_note) + 1, self.book_enchants)
        self.book_enchants.hide(); self.show_selected()
        _help(self.level, "Filter offers by villager level.")
        _help(self.direction, "Filter by whether you buy, sell, or exchange items.")
        _help(self.query, "Search item, enchantment, profession, or offer text.")
        _help(self.uses, "Planned number of times to use the selected trade.")
        _help(self.favorites_only, "Show only locally favorited trades.")
        _help(self.profession_list, "Choose a villager profession.")
        _help(self.trade_view, "All matching loaded offers; selecting one opens its exact transaction and planning details.")

    def _loaded(self, payload):
        super()._loaded(payload); self.show_selected()

    def show_selected(self):
        super().show_selected()
        if not hasattr(self, "book_enchants"): return
        trade = self.selected_trade()
        show = bool(trade and trade.profession.lower() == "librarian" and "enchanted_book" in trade.gives.lower())
        self.book_enchants.setVisible(show)
        if not show: return
        self.book_enchants.set_text(grouped_summary(librarian_enchantments(self.jar), 12))
