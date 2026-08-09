from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from .feature_executor import FeatureExecutor
from .tool_registry import ToolMode, ToolSpec, modes_for
from .ui_dialogs import field_help, make_widget, widget_value


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
        self.resize(760, 680)

        root = QVBoxLayout(self)
        title = QLabel(tool.name); title.setObjectName("WorkspaceTitle"); root.addWidget(title)
        summary = QLabel(tool.summary); summary.setWordWrap(True); summary.setObjectName("Muted"); root.addWidget(summary)
        selector = QHBoxLayout(); selector.addWidget(QLabel("Operation"))
        self.mode_combo = QComboBox(); self.mode_combo.addItems([mode.name for mode in self._modes]); selector.addWidget(self.mode_combo, 1); root.addLayout(selector)

        self.search_card = QFrame(); self.search_card.setObjectName("WarningBanner")
        sc = QVBoxLayout(self.search_card); sc.setContentsMargins(10, 8, 10, 8)
        kicker = QLabel("SEARCH BEHAVIOR"); kicker.setObjectName("DeckLabel"); sc.addWidget(kicker)
        self.search_help = QLabel(); self.search_help.setWordWrap(True); self.search_help.setObjectName("Muted"); sc.addWidget(self.search_help)
        root.addWidget(self.search_card); self.search_card.hide()

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        host = QWidget(); self.form = QFormLayout(host); self.form.setHorizontalSpacing(18); self.form.setVerticalSpacing(10); scroll.setWidget(host); root.addWidget(scroll, 1)
        self.note = QLabel(); self.note.setWordWrap(True); self.note.setObjectName("Muted"); root.addWidget(self.note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Run"); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)
        self.mode_combo.currentIndexChanged.connect(self._rebuild)

        if preferred_mode:
            for index, mode in enumerate(self._modes):
                if preferred_mode in {mode.key, mode.name}:
                    self.mode_combo.setCurrentIndex(index); break
        self._rebuild()

    def exec(self):
        if self._modes:
            return super().exec()
        owner = self.parent()
        if owner is None:
            return QDialog.Rejected
        if self.tool.id == "automation.macro_studio":
            from .automation_workbench import MacroStudioDialog
            MacroStudioDialog(owner).exec()
        elif self.tool.id == "world.profiles":
            from .state_workbenches import WorldProfilesDialog
            WorldProfilesDialog(owner).exec()
        elif self.tool.id == "build.recipes":
            from .recipe_workbench import RecipeExplorerDialog
            RecipeExplorerDialog(owner).exec()
        elif self.tool.id == "utilities.results":
            from .state_workbenches import ResultHistoryDialog
            ResultHistoryDialog(owner).exec()
        elif self.tool.id == "utilities.diagnostics":
            from .state_workbenches import DiagnosticsDialog
            DiagnosticsDialog(owner).exec()
        return QDialog.Rejected

    def _clear_form(self):
        while self.form.rowCount():
            self.form.removeRow(0)
        self.inputs.clear()

    def _rebuild(self):
        self._clear_form()
        if not self._modes:
            self.mode = None; self.note.setText("This workbench opens its dedicated interactive view."); self.search_card.hide(); return
        self.mode = self._modes[self.mode_combo.currentIndex()]
        fields = self.executor.input_fields(self.mode.legacy)
        for key, label, default, kind in fields:
            if key == "seed" and getattr(self.settings, "seed", None): default = self.settings.seed
            widget = make_widget(kind, default)
            tip = field_help(str(key), str(label))
            if tip:
                widget.setToolTip(tip); widget.setAccessibleDescription(tip)
            self.inputs[str(key)] = widget; self.form.addRow(label, widget)
        self.note.setText("Only values used by this operation are shown." if fields else "This operation requires no additional values.")
        mode = self.inputs.get("search_mode")
        ignore = self.inputs.get("ignore_max_generation_limit")
        if isinstance(mode, QComboBox): mode.currentTextChanged.connect(lambda *_: self._sync_search())
        if isinstance(ignore, QCheckBox):
            ignore.setText("Continue beyond the configured maximum")
            ignore.toggled.connect(lambda *_: self._sync_search())
        self.search_card.setVisible(isinstance(mode, QComboBox)); self._sync_search()

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
            text = "Runs one bounded search inside the selected radius. Expansion controls are disabled because they do not affect this mode."
        elif unlimited:
            text = "Expands until a real match is found while ignoring the configured maximum. Exact reference generation can become expensive; backend failures and the runaway guard can still stop it."
        else:
            text = "Expands outward after each empty result and stops at the configured maximum radius."
        self.search_help.setText(text)

    def values(self) -> dict[str, Any]:
        return {key: widget_value(widget) for key, widget in self.inputs.items()}
