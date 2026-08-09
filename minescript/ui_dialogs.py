from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QScrollArea,
    QSpinBox, QVBoxLayout, QWidget,
)


FIELD_HELP = {
    "world_path": "Choose an existing Java world save when you want F3+ to inspect generated chunks instead of regenerating them from a seed.",
    "seed": "Java Edition world seed used by deterministic calculations or reference generation.",
    "cx": "Chunk X at the center of this operation.",
    "cz": "Chunk Z at the center of this operation.",
    "x": "Block X coordinate.",
    "y": "Block Y coordinate.",
    "z": "Block Z coordinate.",
    "radius": "Initial or bounded search radius. The field label states whether this is measured in blocks or chunks.",
    "search_mode": "Radius search evaluates one bounded area. Search until found expands outward until a match or stopping condition.",
    "radius_step": "Amount added to the search radius after an unsuccessful Search until found attempt.",
    "max_search_radius": "Normal stopping radius for Search until found.",
    "ignore_max_generation_limit": "Continue beyond the configured maximum. Exact reference generation can become expensive in CPU, memory, disk space and time.",
    "regenerate_from_seed": "Generate bounded reference chunks with Mojang's matching Java server when no existing save is selected.",
    "accept_minecraft_eula": "Explicit acceptance required before F3+ launches Mojang's server for local reference generation.",
    "worldgen_max_chunks": "Normal chunk budget for exact reference generation.",
    "dimension": "Minecraft dimension used by this calculation.",
    "target_biome": "Target biome used by the search.",
    "world": "World/save path used by the selected operation.",
}


def field_help(key: str, label: str = "") -> str:
    return FIELD_HELP.get(str(key), f"Input used by this operation: {label}" if label else "")


def make_widget(kind: str, default: Any):
    if kind == "int":
        widget = QSpinBox(); widget.setRange(-2_147_483_647, 2_147_483_647); widget.setValue(int(default))
    elif kind == "float":
        widget = QDoubleSpinBox(); widget.setDecimals(6); widget.setRange(-1e12, 1e12); widget.setValue(float(default))
    elif kind == "bool":
        widget = QCheckBox(); widget.setChecked(bool(default))
    elif kind == "choice":
        widget = QComboBox(); widget.addItems([str(value) for value in default])
    else:
        widget = QLineEdit(str(default))
    return widget


def widget_value(widget):
    if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
        return widget.value()
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, QComboBox):
        return widget.currentText()
    return widget.text()


class ParameterDialog(QDialog):
    """Reusable, tooltip-rich editor for a small operation schema."""

    def __init__(self, title: str, fields, parent=None, subtitle: str = "", run_label: str = "Run"):
        super().__init__(parent)
        self.setWindowTitle(title); self.resize(620, 560)
        self.inputs: dict[str, QWidget] = {}
        root = QVBoxLayout(self)
        heading = QLabel(title); heading.setObjectName("WorkspaceTitle"); root.addWidget(heading)
        if subtitle:
            note = QLabel(subtitle); note.setWordWrap(True); note.setObjectName("Muted"); root.addWidget(note)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        host = QWidget(); form = QFormLayout(host); form.setHorizontalSpacing(18); form.setVerticalSpacing(10)
        scroll.setWidget(host); root.addWidget(scroll, 1)
        for key, label, default, kind in fields:
            widget = make_widget(kind, default)
            tip = field_help(str(key), str(label))
            if tip:
                widget.setToolTip(tip); widget.setAccessibleDescription(tip)
            self.inputs[str(key)] = widget
            form.addRow(str(label), widget)

        self.search_card = QFrame(); self.search_card.setObjectName("WarningBanner")
        card = QVBoxLayout(self.search_card); card.setContentsMargins(10, 8, 10, 8)
        kicker = QLabel("SEARCH BEHAVIOR"); kicker.setObjectName("DeckLabel"); card.addWidget(kicker)
        self.search_help = QLabel(); self.search_help.setWordWrap(True); self.search_help.setObjectName("Muted"); card.addWidget(self.search_help)
        root.insertWidget(2 if subtitle else 1, self.search_card)
        self.search_card.setVisible("search_mode" in self.inputs)

        mode = self.inputs.get("search_mode")
        ignore = self.inputs.get("ignore_max_generation_limit")
        if isinstance(mode, QComboBox): mode.currentTextChanged.connect(lambda *_: self._sync_search())
        if isinstance(ignore, QCheckBox):
            ignore.setText("Continue beyond the configured maximum")
            ignore.toggled.connect(lambda *_: self._sync_search())
        self._sync_search()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(run_label)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def _sync_search(self):
        mode = self.inputs.get("search_mode")
        if not isinstance(mode, QComboBox): return
        until = mode.currentText() == "Search until found"
        ignore = self.inputs.get("ignore_max_generation_limit")
        unlimited = bool(ignore.isChecked()) if isinstance(ignore, QCheckBox) else False
        for key in ("radius_step", "max_search_radius", "ignore_max_generation_limit"):
            widget = self.inputs.get(key)
            if widget is not None: widget.setEnabled(until)
        maximum = self.inputs.get("max_search_radius")
        if maximum is not None and until: maximum.setEnabled(not unlimited)
        budget = self.inputs.get("worldgen_max_chunks")
        if budget is not None: budget.setEnabled(not (until and unlimited))
        if not until:
            text = "Runs one bounded search inside the selected radius. Expansion controls do not affect this mode."
        elif unlimited:
            text = "Expands until a real match is found while ignoring the configured maximum. Exact generation can consume substantial CPU, memory, disk space and time; backend errors and the runaway guard can still stop it."
        else:
            text = "Expands outward by the selected step after each empty result and stops at the configured maximum radius."
        self.search_help.setText(text)

    def values(self) -> dict[str, Any]:
        return {key: widget_value(widget) for key, widget in self.inputs.items()}
