from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QFrame, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

from .feature_executor import FeatureExecutor
from .tool_registry import ToolMode, ToolSpec, modes_for


def _input_widget(kind: str, default: Any):
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


def _input_value(widget):
    if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
        return widget.value()
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, QComboBox):
        return widget.currentText()
    return widget.text()


class OperationDialog(QDialog):
    """Configure one historical operation inside a canonical workbench."""

    def __init__(self, tool: ToolSpec, executor: FeatureExecutor, settings, parent=None, preferred_mode: str = ""):
        super().__init__(parent)
        self.tool = tool
        self.executor = executor
        self.settings = settings
        self.mode: ToolMode | None = None
        self.inputs: dict[str, QWidget] = {}
        self._modes = [mode for mode in modes_for(tool) if mode.legacy is not None]
        self.setWindowTitle(tool.name)
        self.resize(720, 620)

        root = QVBoxLayout(self)
        title = QLabel(tool.name); title.setObjectName("WorkspaceTitle"); root.addWidget(title)
        summary = QLabel(tool.summary); summary.setWordWrap(True); summary.setObjectName("Muted"); root.addWidget(summary)
        selector = QHBoxLayout(); selector.addWidget(QLabel("Operation"))
        self.mode_combo = QComboBox(); self.mode_combo.addItems([mode.name for mode in self._modes]); selector.addWidget(self.mode_combo, 1); root.addLayout(selector)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        host = QWidget(); self.form = QFormLayout(host); scroll.setWidget(host); root.addWidget(scroll, 1)
        self.note = QLabel(); self.note.setWordWrap(True); self.note.setObjectName("Muted"); root.addWidget(self.note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Run"); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)
        self.mode_combo.currentIndexChanged.connect(self._rebuild)

        if preferred_mode:
            for index, mode in enumerate(self._modes):
                if preferred_mode in {mode.key, mode.name}:
                    self.mode_combo.setCurrentIndex(index); break
        self._rebuild()

    def _clear_form(self):
        while self.form.rowCount():
            self.form.removeRow(0)
        self.inputs.clear()

    def _rebuild(self):
        self._clear_form()
        if not self._modes:
            self.mode = None; self.note.setText("This workbench opens its dedicated interactive view."); return
        self.mode = self._modes[self.mode_combo.currentIndex()]
        fields = self.executor.input_fields(self.mode.legacy)
        for key, label, default, kind in fields:
            if key == "seed" and getattr(self.settings, "seed", None):
                default = self.settings.seed
            widget = _input_widget(kind, default); self.inputs[key] = widget; self.form.addRow(label, widget)
        self.note.setText("Only values used by this operation are shown." if fields else "This operation requires no additional values.")

    def values(self) -> dict[str, Any]:
        return {key: _input_value(widget) for key, widget in self.inputs.items()}
