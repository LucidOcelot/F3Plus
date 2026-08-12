from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QFrame, QLabel, QLineEdit, QScrollArea,
    QSpinBox, QVBoxLayout, QWidget,
)

from .input_help import parameter_copy, parameter_label, wrapped_tooltip


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


def set_help_tooltip(widget, text: str, width: int = 360) -> None:
    """Use wrapped visual help while keeping accessibility text plain."""
    plain = str(text).strip()
    widget.setToolTip(wrapped_tooltip(plain, width))
    if hasattr(widget, "setAccessibleDescription"):
        widget.setAccessibleDescription(plain)


def _configure_parameter_widget(widget, key: str, label: str):
    low = f"{key} {label}".lower()
    if isinstance(widget, QLineEdit) and "slots" in low:
        widget.setPlaceholderText("1,2,3")
    if isinstance(widget, QSpinBox) and any(token in low for token in ("slot", "hotbar")):
        widget.setRange(1, 9)
    if isinstance(widget, QDoubleSpinBox):
        time_field = any(token in low for token in (
            "interval", "delay", "duration", "wait", "spacing", "seconds", "time",
            "recast", "every", "switch",
        ))
        minute_field = "minute" in low or key == "minutes"
        if time_field or minute_field:
            widget.setDecimals(2)
            widget.setSingleStep(0.05 if abs(widget.value()) < 10 else 1.0)
            widget.setMinimum(0.0)
            widget.setMaximum(86400.0)
            widget.setSuffix(" min" if minute_field else " s")


class ParameterDialog(QDialog):
    """Small configuration editor with short hints and detailed wrapped tooltips."""

    def __init__(self, title: str, fields, parent=None, subtitle: str = "", run_label: str = "Run"):
        super().__init__(parent)
        fields = list(fields)
        self.setWindowTitle(title)
        self.setMinimumWidth(520)
        target_height = 170 + len(fields) * 72 + (58 if subtitle else 0)
        self.resize(600, max(280, min(680, target_height)))
        self.inputs: dict[str, QWidget] = {}

        root = QVBoxLayout(self); root.setContentsMargins(14, 12, 14, 12); root.setSpacing(10)
        heading = QLabel(title); heading.setObjectName("WorkspaceTitle"); root.addWidget(heading)
        if subtitle:
            note = QLabel(subtitle); note.setWordWrap(True); note.setObjectName("Muted"); root.addWidget(note)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        host = QWidget(); form = QFormLayout(host)
        form.setHorizontalSpacing(18); form.setVerticalSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        scroll.setWidget(host); root.addWidget(scroll, 1)

        for key, label, default, kind in fields:
            key = str(key); label = str(label); display_label = parameter_label(title, key, label)
            widget = make_widget(kind, default)
            _configure_parameter_widget(widget, key, display_label)
            hint_text, tooltip = parameter_copy(title, key, label, default, kind)
            set_help_tooltip(widget, tooltip); self.inputs[key] = widget

            label_widget = QLabel(display_label)
            label_widget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            label_widget.setToolTip(wrapped_tooltip(tooltip))
            column = QWidget(); column_layout = QVBoxLayout(column)
            column_layout.setContentsMargins(0, 0, 0, 0); column_layout.setSpacing(3)
            column_layout.addWidget(widget)
            if hint_text:
                hint = QLabel(hint_text); hint.setWordWrap(True); hint.setObjectName("Muted")
                column_layout.addWidget(hint)
            form.addRow(label_widget, column)

        self.search_card = QFrame(); self.search_card.setObjectName("WarningBanner")
        card = QVBoxLayout(self.search_card); card.setContentsMargins(10, 8, 10, 8)
        kicker = QLabel("SEARCH BEHAVIOR"); kicker.setObjectName("DeckLabel"); card.addWidget(kicker)
        self.search_help = QLabel(); self.search_help.setWordWrap(True); self.search_help.setObjectName("Muted")
        card.addWidget(self.search_help)
        root.insertWidget(2 if subtitle else 1, self.search_card)
        self.search_card.setVisible("search_mode" in self.inputs)

        mode = self.inputs.get("search_mode"); ignore = self.inputs.get("ignore_max_generation_limit")
        if isinstance(mode, QComboBox): mode.currentTextChanged.connect(lambda *_: self._sync_search())
        if isinstance(ignore, QCheckBox):
            ignore.setText("Continue beyond the configured maximum")
            ignore.toggled.connect(lambda *_: self._sync_search())
        self._sync_search()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(run_label)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

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
        if not until: text = "Searches once inside the selected radius."
        elif unlimited: text = "Keeps expanding after empty passes until a match is found or the job is stopped."
        else: text = "Expands by the selected step after each empty pass and stops at the maximum radius."
        self.search_help.setText(text)

    def values(self) -> dict[str, Any]:
        return {key: widget_value(widget) for key, widget in self.inputs.items()}
