from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QFrame, QLabel, QLineEdit, QScrollArea,
    QSpinBox, QVBoxLayout, QWidget,
)

from .field_semantics import field_help


_PARAMETER_COPY: dict[tuple[str, str], tuple[str, str]] = {
    ("Mending Grinder", "attack"): (
        "Seconds between attack clicks.",
        "How often F3+ clicks attack while the grinder runs. Lower values attack faster. The routine clamps this to at least 0.05 seconds.",
    ),
    ("Mending Grinder", "rotate"): (
        "Seconds before switching hotbar slots.",
        "How long each selected hotbar slot stays active before F3+ switches to the next slot. Use this to distribute collected Mending XP among several tools.",
    ),
    ("Mending Grinder", "slots"): (
        "Hotbar slots that should receive Mending XP.",
        "Enter hotbar slot numbers 1 through 9 separated by commas, for example 1,2,3,5. Slots are cycled in the order entered; invalid entries are ignored.",
    ),
    ("Crossbow Volley", "slots"): (
        "Hotbar slots containing loaded crossbows.",
        "Enter crossbow hotbar slots 1 through 9 separated by commas. F3+ cycles through these slots in order.",
    ),
    ("Crossbow Volley", "charge"): (
        "Seconds allowed for each crossbow to charge.",
        "Time F3+ holds use before firing each crossbow. Increase this if a crossbow is released before it finishes charging.",
    ),
    ("Crossbow Volley", "swap"): (
        "Delay after changing to the next crossbow.",
        "Seconds F3+ waits after selecting the next configured hotbar slot before beginning the next charge.",
    ),
    ("Tool Rotation", "slots"): (
        "Hotbar slots included in the rotation.",
        "Enter slot numbers 1 through 9 separated by commas. F3+ rotates through them in the order entered.",
    ),
    ("Tool Rotation", "interval"): (
        "Seconds each tool remains selected.",
        "Time before F3+ switches from the current configured tool slot to the next one.",
    ),
    ("Hotbar Workflow", "slots"): (
        "Hotbar slots visited by the workflow.",
        "Enter slot numbers 1 through 9 separated by commas. The workflow visits them in the order entered.",
    ),
    ("Hotbar Workflow", "delay"): (
        "Seconds between hotbar changes.",
        "Pause after selecting one configured slot before moving to the next slot.",
    ),
    ("Food Manager", "slot"): (
        "Hotbar slot containing food.",
        "Choose the hotbar slot from 1 through 9 that contains the food F3+ should select before eating.",
    ),
    ("Food Manager", "interval"): (
        "Seconds between eating attempts.",
        "Time from one eating attempt to the next. This routine uses the timer; it does not read the hunger bar.",
    ),
    ("Food Manager", "duration"): (
        "Seconds to hold the use button while eating.",
        "How long F3+ holds use after selecting the food slot. Increase this if the item is released before eating completes.",
    ),
    ("Offhand Workflow", "interval"): (
        "Seconds between offhand swaps.",
        "Time F3+ waits between presses of the configured swap key.",
    ),
    ("Custom Periodic Action", "interval"): (
        "Seconds between action cycles.",
        "Time from the start of one configured interaction cycle to the start of the next cycle.",
    ),
    ("Custom Periodic Action", "actions"): (
        "Number of clicks in each cycle.",
        "How many mouse actions F3+ performs whenever one periodic cycle begins.",
    ),
    ("Custom Periodic Action", "spacing"): (
        "Seconds between clicks inside one cycle.",
        "Delay between individual mouse actions when a cycle contains more than one action.",
    ),
    ("Livestock Breeder", "minutes"): (
        "Minutes between breeding/growth interaction cycles.",
        "Time F3+ waits before repeating the configured livestock interaction cycle. The default matches the normal 20-minute adult breeding cooldown/growth interval.",
    ),
    ("Auto Fishing", "wait"): (
        "Seconds to wait before reeling in.",
        "Delay between casting and the reel action used by this timer-based fishing routine.",
    ),
    ("Auto Fishing", "recast"): (
        "Seconds to wait before casting again.",
        "Pause after the reel action before F3+ sends the next cast.",
    ),
}


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


def _generic_hint(key: str, label: str) -> str:
    low = f"{key} {label}".lower()
    if "slots" in low: return "Hotbar slots 1–9, separated by commas."
    if "interval" in low: return "Time between repetitions."
    if "delay" in low or "wait" in low: return "Time to wait before the next action."
    if "duration" in low: return "How long the action remains active."
    if "spacing" in low: return "Distance or time between repeated elements."
    if "rows" in low: return "Number of rows to process."
    if "steps" in low: return "Number of steps to process."
    if "branches" in low: return "Number of branches to process."
    if "click" in low or "swings" in low or "actions" in low: return "Number of actions in each cycle."
    if "radius" in low: return "Distance from the selected center."
    if label.strip().lower().endswith(" x"): return "Minecraft X coordinate."
    if label.strip().lower().endswith(" y"): return "Minecraft Y coordinate."
    if label.strip().lower().endswith(" z"): return "Minecraft Z coordinate."
    return ""


def _requirement(default, kind: str) -> str:
    if kind == "choice" and isinstance(default, (list, tuple)):
        return "Choices: " + ", ".join(str(value) for value in default[:8]) + "."
    if kind == "bool":
        return f"Default: {'enabled' if bool(default) else 'disabled'}."
    if kind == "int":
        return f"Enter a whole number. Default: {default}."
    if kind == "float":
        return f"Enter a number. Default: {default}."
    if str(default).strip():
        return f"Default: {default}."
    return ""


def parameter_copy(title: str, key: str, label: str, default, kind: str) -> tuple[str, str]:
    specific = _PARAMETER_COPY.get((str(title), str(key)))
    if specific:
        hint, tooltip = specific
    else:
        hint = _generic_hint(str(key), str(label))
        tooltip = field_help(str(key), str(label)).strip()
    requirement = _requirement(default, kind)
    if requirement and requirement.lower() not in tooltip.lower():
        tooltip = f"{tooltip} {requirement}".strip()
    if hint.strip() == tooltip.strip():
        hint = ""
    return hint, tooltip


def _configure_parameter_widget(widget, key: str, label: str):
    low = f"{key} {label}".lower()
    if isinstance(widget, QLineEdit) and "slots" in low:
        widget.setPlaceholderText("1,2,3")
    if isinstance(widget, QSpinBox) and any(token in low for token in ("slot", "hotbar")):
        widget.setRange(1, 9)
    if isinstance(widget, QDoubleSpinBox):
        time_field = any(token in low for token in ("interval", "delay", "duration", "wait", "spacing", "seconds", "time", "recast"))
        minute_field = "minute" in low or key == "minutes"
        if time_field or minute_field:
            widget.setDecimals(2)
            widget.setSingleStep(0.05 if abs(widget.value()) < 10 else 1.0)
            widget.setMinimum(0.0)
            widget.setMaximum(86400.0)
            widget.setSuffix(" min" if minute_field else " s")


class ParameterDialog(QDialog):
    """Small configuration editor with short inline hints and detailed tooltips."""

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
        host = QWidget(); form = QFormLayout(host); form.setHorizontalSpacing(18); form.setVerticalSpacing(12); form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow); scroll.setWidget(host); root.addWidget(scroll, 1)
        for key, label, default, kind in fields:
            key = str(key); label = str(label)
            widget = make_widget(kind, default)
            _configure_parameter_widget(widget, key, label)
            hint_text, tooltip = parameter_copy(title, key, label, default, kind)
            widget.setToolTip(tooltip); widget.setAccessibleDescription(tooltip); self.inputs[key] = widget

            label_widget = QLabel(label); label_widget.setAlignment(Qt.AlignLeft | Qt.AlignTop); label_widget.setToolTip(tooltip)
            column = QWidget(); column_layout = QVBoxLayout(column); column_layout.setContentsMargins(0, 0, 0, 0); column_layout.setSpacing(3); column_layout.addWidget(widget)
            if hint_text:
                hint = QLabel(hint_text); hint.setWordWrap(True); hint.setObjectName("Muted"); column_layout.addWidget(hint)
            form.addRow(label_widget, column)

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
        if not until: text = "Searches once inside the selected radius."
        elif unlimited: text = "Keeps expanding after empty passes until a match is found or the job is stopped."
        else: text = "Expands by the selected step after each empty pass and stops at the maximum radius."
        self.search_help.setText(text)

    def values(self) -> dict[str, Any]: return {key: widget_value(widget) for key, widget in self.inputs.items()}
