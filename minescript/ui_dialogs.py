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
    "x1": "X coordinate of the starting/current position.",
    "y1": "Y coordinate of the starting/current position.",
    "z1": "Z coordinate of the starting/current position.",
    "x2": "X coordinate of the target/second position.",
    "y2": "Y coordinate of the target/second position.",
    "z2": "Z coordinate of the target/second position.",
    "dx": "Signed X offset added to the starting coordinate.",
    "dy": "Signed Y offset added to the starting coordinate.",
    "dz": "Signed Z offset added to the starting coordinate.",
    "radius": "Radius used by this operation. The field label states whether this is measured in blocks or chunks.",
    "width": "Horizontal build width in blocks.",
    "length": "Horizontal build length/span in blocks.",
    "height": "Vertical build height in blocks unless the field label states a mechanic-specific meaning.",
    "spacing": "Spacing between repeated elements, samples, supports, or steps. Read the field label for the specific unit used by this operation.",
    "sag": "Vertical drop from the endpoints toward the center of the catenary planning curve.",
    "secondary": "Second shape dimension or count. The field label identifies its exact role for the selected shape.",
    "stops": "Semicolon-separated destinations. Each stop is x,y,z,label. Example: 80,64,0,Mine;120,70,50,Village.",
    "points": "Semicolon-separated recorded path points. Coordinates are x,y,z, with an optional fourth label when the selected operation supports labels.",
    "sample_interval": "Time between recorded position samples. Used to estimate recording duration; it does not change the coordinates themselves.",
    "epsilon": "Maximum distance between non-adjacent path points that counts as revisiting the same place for loop detection.",
    "return_to_start": "Add a final route leg back to the starting point.",
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
    return FIELD_HELP.get(str(key), f"Value used by this operation: {label}." if label else "")


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
        host = QWidget(); form = QFormLayout(host); form.setHorizontalSpacing(18); form.setVerticalSpacing(12); form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        scroll.setWidget(host); root.addWidget(scroll, 1)
        for key, label, default, kind in fields:
            widget = make_widget(kind, default)
            tip = field_help(str(key), str(label))
            if tip:
                widget.setToolTip(tip); widget.setAccessibleDescription(tip)
            self.inputs[str(key)] = widget
            column = QWidget(); column_layout = QVBoxLayout(column); column_layout.setContentsMargins(0, 0, 0, 0); column_layout.setSpacing(3); column_layout.addWidget(widget)
            if tip:
                hint = QLabel(tip); hint.setWordWrap(True); hint.setObjectName("Muted"); column_layout.addWidget(hint)
            form.addRow(str(label), column)

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
