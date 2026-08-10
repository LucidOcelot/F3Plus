from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QFrame, QLabel, QLineEdit, QScrollArea,
    QSpinBox, QVBoxLayout, QWidget,
)

from .field_semantics import FIELD_HELP, field_help


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
    if isinstance(widget, (QSpinBox, QDoubleSpinBox)): return widget.value()
    if isinstance(widget, QCheckBox): return widget.isChecked()
    if isinstance(widget, QComboBox): return widget.currentText()
    return widget.text()


class ParameterDialog(QDialog):
    """Reusable inline-explained editor for small operation schemas."""

    def __init__(self, title: str, fields, parent=None, subtitle: str = "", run_label: str = "Run"):
        super().__init__(parent)
        self.setWindowTitle(title); self.resize(620, 560); self.inputs: dict[str, QWidget] = {}
        root = QVBoxLayout(self); heading = QLabel(title); heading.setObjectName("WorkspaceTitle"); root.addWidget(heading)
        if subtitle:
            note = QLabel(subtitle); note.setWordWrap(True); note.setObjectName("Muted"); root.addWidget(note)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        host = QWidget(); form = QFormLayout(host); form.setHorizontalSpacing(18); form.setVerticalSpacing(12); form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow); scroll.setWidget(host); root.addWidget(scroll, 1)
        for key, label, default, kind in fields:
            widget = make_widget(kind, default); tip = field_help(str(key), str(label)); widget.setToolTip(tip); widget.setAccessibleDescription(tip); self.inputs[str(key)] = widget
            column = QWidget(); column_layout = QVBoxLayout(column); column_layout.setContentsMargins(0, 0, 0, 0); column_layout.setSpacing(3); column_layout.addWidget(widget)
            hint = QLabel(tip); hint.setWordWrap(True); hint.setObjectName("Muted"); column_layout.addWidget(hint); form.addRow(str(label), column)

        self.search_card = QFrame(); self.search_card.setObjectName("WarningBanner"); card = QVBoxLayout(self.search_card); card.setContentsMargins(10, 8, 10, 8); kicker = QLabel("SEARCH BEHAVIOR"); kicker.setObjectName("DeckLabel"); card.addWidget(kicker); self.search_help = QLabel(); self.search_help.setWordWrap(True); self.search_help.setObjectName("Muted"); card.addWidget(self.search_help); root.insertWidget(2 if subtitle else 1, self.search_card); self.search_card.setVisible("search_mode" in self.inputs)

        mode = self.inputs.get("search_mode"); ignore = self.inputs.get("ignore_max_generation_limit")
        if isinstance(mode, QComboBox): mode.currentTextChanged.connect(lambda *_: self._sync_search())
        if isinstance(ignore, QCheckBox): ignore.setText("Continue beyond the configured maximum"); ignore.toggled.connect(lambda *_: self._sync_search())
        self._sync_search()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); buttons.button(QDialogButtonBox.Ok).setText(run_label); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def _sync_search(self):
        mode = self.inputs.get("search_mode")
        if not isinstance(mode, QComboBox): return
        until = mode.currentText() == "Search until found"; ignore = self.inputs.get("ignore_max_generation_limit"); unlimited = bool(ignore.isChecked()) if isinstance(ignore, QCheckBox) else False
        for key in ("radius_step", "max_search_radius", "ignore_max_generation_limit"):
            widget = self.inputs.get(key)
            if widget is not None: widget.setEnabled(until)
        maximum = self.inputs.get("max_search_radius")
        if maximum is not None and until: maximum.setEnabled(not unlimited)
        budget = self.inputs.get("worldgen_max_chunks")
        if budget is not None: budget.setEnabled(not (until and unlimited))
        if not until: text = "Runs one bounded search inside the selected radius. Expansion controls do not affect this mode."
        elif unlimited: text = "Expands until a real match is found while ignoring the configured maximum. Exact generation can consume substantial CPU, memory, disk space and time; backend errors and the runaway guard can still stop it."
        else: text = "Expands outward by the selected step after each empty result and stops at the configured maximum radius."
        self.search_help.setText(text)

    def values(self) -> dict[str, Any]: return {key: widget_value(widget) for key, widget in self.inputs.items()}
