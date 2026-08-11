from __future__ import annotations

"""Concise 2.5 generic operation explorer."""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .async_workbench import OperationDialog as _AsyncOperationDialog
from .field_semantics import field_help
from .ui_dialogs import make_widget
from .workbench_forms import _operation_description


_OUTPUT_EXPLANATIONS = {
    "Ore Distribution": "Ore totals by type and Y level, plus chunks scanned. A chart is shown when data is available.",
    "Ore Exposure Estimate": "Exposed ore totals by type and scan coverage.",
    "Cave Exposure Estimate": "Cave-air and exposed-surface measurements for the scanned chunks.",
    "Ancient City Area Analysis": "Ancient City candidates/area information for the selected seed and region.",
    "Structure Finder": "Candidate structure locations. Map points are independent locations, not a route.",
    "Structure Cluster Finder": "Candidate clusters with location/count information, followed by a map of the returned candidates.",
    "Biome Diversity Finder": "Biome counts and sampled locations. Repeated equal values are summarized instead of printed as duplicate rows.",
    "Island Finder": "Matched terrain locations and measurements from either the selected save or seed-generated chunks.",
    "Dungeon/Pig Spawner Locator": "Saved spawner matches, search radius, and stop reason. A seed can generate the required chunks when no save is selected.",
}


def contextual_field_help(mode, key: str, label: str, default, kind: str) -> str:
    base = field_help(key, label).strip()
    if kind == "choice" and isinstance(default, (list, tuple)):
        suffix = "Options: " + ", ".join(str(value) for value in list(default)[:6]) + "."
    elif kind == "bool":
        suffix = f"Default: {'on' if bool(default) else 'off'}."
    elif kind in {"int", "float"}:
        suffix = f"Default: {default}."
    elif str(default).strip():
        suffix = f"Default: {default}."
    else:
        suffix = "Optional."
    if not base:
        return suffix
    sentences = [part.strip().rstrip(".") for part in base.split(". ") if part.strip()]
    concise = ". ".join(sentences[:2]).rstrip(".") + "."
    return f"{concise} {suffix}"


class OperationDialog(_AsyncOperationDialog):
    def _field_editor(self, key: str, label: str, default, kind: str):
        widget = make_widget(kind, default)
        tip = contextual_field_help(self.mode, key, label, default, kind)
        widget.setToolTip(tip); widget.setAccessibleDescription(tip)
        column = QWidget(); layout = QVBoxLayout(column); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(3)
        layout.addWidget(widget)
        hint = QLabel(tip); hint.setWordWrap(True); hint.setObjectName("Muted"); layout.addWidget(hint)
        return widget, column

    def _rebuild(self):
        super()._rebuild()
        if self.mode is None or self.mode.legacy is None:
            return
        self.mode_help.setText(_operation_description(self.mode).strip())
        explained = _OUTPUT_EXPLANATIONS.get(self.mode.name)
        self.context_card.setVisible(bool(explained))
        if explained:
            self.output_help.setText(explained)
