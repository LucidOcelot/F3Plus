from __future__ import annotations

"""Generic operation explorer with concise forms and concrete input help."""

from PySide6.QtWidgets import QWidget

from .async_workbench import OperationDialog as _AsyncOperationDialog
from .field_semantics import field_help
from .ui_dialogs import make_widget
from .workbench_forms import _operation_description


_OUTPUT_EXPLANATIONS = {
    "Ore Distribution": "Shows ore totals by block type and Y level for the scanned chunks, plus scan coverage and a distribution chart when multiple ore types are present.",
    "Ore Exposure Estimate": "Shows exposed ore counts by block type and the number of chunks examined so you can compare visible mining opportunities between areas.",
    "Cave Exposure Estimate": "Shows cave-air and exposed-surface measurements for the scanned chunks, including the coverage used to produce the totals.",
    "Ancient City Area Analysis": "Shows returned Ancient City area candidates and their coordinates for the selected world or generated search area.",
    "Structure Finder": "Shows candidate structure coordinates and search coverage. Each map marker is one returned location.",
    "Structure Cluster Finder": "Shows candidate clusters, the number of matching structures in each cluster, and the coordinates used for the map.",
    "Biome Diversity Finder": "Shows how many distinct biomes were found, biome frequencies, and the sampled coordinates used by the comparison.",
    "Island Finder": "Shows matched terrain locations with the measurements returned by the selected save scan or generated search.",
    "Dungeon/Pig Spawner Locator": "Shows matching spawner coordinates, the radius searched, and how many matches were found.",
}


def contextual_field_help(mode, key: str, label: str, default, kind: str) -> str:
    base = field_help(key, label).strip()
    if kind == "choice" and isinstance(default, (list, tuple)):
        options = ", ".join(str(value) for value in list(default)[:8])
        suffix = f"Choices: {options}."
    elif kind == "bool":
        suffix = f"Default: {'enabled' if bool(default) else 'disabled'}."
    elif kind == "int":
        suffix = f"Enter a whole number. Default: {default}."
    elif kind == "float":
        suffix = f"Enter a number. Default: {default}."
    elif str(default).strip():
        suffix = f"Default: {default}."
    else:
        suffix = "Optional unless this operation requires it to run."
    return f"{base} {suffix}".strip()


class OperationDialog(_AsyncOperationDialog):
    def _field_editor(self, key: str, label: str, default, kind: str):
        widget = make_widget(kind, default)
        tip = contextual_field_help(self.mode, key, label, default, kind)
        widget.setToolTip(tip)
        widget.setAccessibleDescription(tip)
        return widget, widget

    def _rebuild(self):
        super()._rebuild()
        if self.mode is None or self.mode.legacy is None:
            return
        description = _operation_description(self.mode).strip()
        self.mode_help.setText(description)
        explained = _OUTPUT_EXPLANATIONS.get(self.mode.name)
        self.context_card.setVisible(bool(explained))
        if explained:
            self.output_help.setText(explained)
