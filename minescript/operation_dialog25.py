from __future__ import annotations

"""2.5 generic operation explorer.

The underlying operation schemas stay canonical.  This class improves the public
abstraction layer: every control receives operation-aware helper text, an example/default
when useful, and the same explanation as an accessible tooltip/description.
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .async_workbench import OperationDialog as _AsyncOperationDialog
from .field_semantics import field_help
from .ui_dialogs import make_widget
from .workbench_forms import _operation_description


def contextual_field_help(mode, key: str, label: str, default, kind: str) -> str:
    base = field_help(key, label).strip()
    operation = getattr(mode, "name", "this operation") if mode is not None else "this operation"
    legacy = getattr(mode, "legacy", None) if mode is not None else None
    context = _operation_description(mode) if mode is not None else ""
    label_clean = str(label or key).strip()

    if kind == "choice" and isinstance(default, (list, tuple)):
        options = ", ".join(str(value) for value in list(default)[:8])
        example = f"Available choices: {options}."
    elif kind == "bool":
        example = f"Default: {'enabled' if bool(default) else 'disabled'}. Toggle it only when you want the named behavior to apply."
    elif kind in {"int", "float"}:
        example = f"Example/default: {default}."
    elif str(default).strip():
        example = f"Example/default: {default}."
    else:
        example = "Leave this blank only when the operation explicitly supports automatic/local-state discovery."

    # Do not repeat a full paragraph when the base explanation already names the
    # operation-specific concept.  The context line is especially important for old
    # compatibility fields named simply value/secondary.
    if key in {"value", "secondary", "amount", "units", "hours", "level"} or "value" in label_clean.lower():
        role = f"For {operation}, this control supplies “{label_clean}” to the calculation; it is not an ignored legacy placeholder."
    else:
        role = f"For {operation}, this is the {label_clean.lower()} input."
    concise_context = context.rstrip(".") + "." if context else ""
    return " ".join(part for part in (base, role, example, concise_context) if part)


class OperationDialog(_AsyncOperationDialog):
    def _field_editor(self, key: str, label: str, default, kind: str):
        widget = make_widget(kind, default)
        tip = contextual_field_help(self.mode, key, label, default, kind)
        widget.setToolTip(tip); widget.setAccessibleDescription(tip)
        column = QWidget(); layout = QVBoxLayout(column); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(4)
        layout.addWidget(widget)
        hint = QLabel(tip); hint.setWordWrap(True); hint.setObjectName("Muted"); hint.setTextInteractionFlags(hint.textInteractionFlags())
        layout.addWidget(hint)
        return widget, column

    def _rebuild(self):
        super()._rebuild()
        if self.mode is None or self.mode.legacy is None:
            return
        description = _operation_description(self.mode).strip()
        fields = self.executor.input_fields(self.mode.legacy)
        if fields:
            names = ", ".join(str(row[1]) for row in fields[:6])
            if len(fields) > 6: names += f", and {len(fields) - 6} more"
            self.mode_help.setText(f"{description} Inputs used by this operation: {names}.")
        else:
            self.mode_help.setText(description + " This action uses live/saved application state and does not ask for unused compatibility values.")
