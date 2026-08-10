from __future__ import annotations

"""2.5 generic operation explorer.

The underlying operation schemas stay canonical. This class improves the public
abstraction layer: every control receives concise operation-aware helper text, an
example/default when useful, and the same explanation as a tooltip/accessibility label.
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .async_workbench import OperationDialog as _AsyncOperationDialog
from .field_semantics import field_help
from .location_contract import LOCATION_KEYS
from .ui_dialogs import make_widget
from .workbench_forms import _operation_description


_OUTPUT_EXPLANATIONS = {
    "Ore Distribution": "Generated-world ore totals by ore type and Y level, chunks scanned, data source, and limitations. A labeled chart is shown when ore totals are available.",
    "Ore Exposure Estimate": "Generated-world exposed-ore totals by ore type plus scan coverage, data source, and exposure-model limitations.",
    "Cave Exposure Estimate": "Generated-world cave-air and cave-surface measurements, chunks scanned, data source, and tick/exposure limitations.",
    "Ancient City Area Analysis": "Ancient City area/candidate information for the selected seed and region, with the calculation source and placement limitations clearly labeled.",
    "Structure Finder": "Candidate chunk sets for the requested structure types, including coordinates and source/exactness information. Candidates are shown as points, not connected routes.",
}


def contextual_field_help(mode, key: str, label: str, default, kind: str) -> str:
    base = field_help(key, label).strip()
    operation = getattr(mode, "name", "this operation") if mode is not None else "this operation"
    label_clean = str(label or key).strip()

    if kind == "choice" and isinstance(default, (list, tuple)):
        options = ", ".join(str(value) for value in list(default)[:8])
        example = f"Choices: {options}."
    elif kind == "bool":
        example = f"Default: {'on' if bool(default) else 'off'}."
    elif kind in {"int", "float"}:
        example = f"Default: {default}."
    elif str(default).strip():
        example = f"Example: {default}."
    else:
        example = "Leave blank only when automatic/local discovery is supported."

    ambiguous = key in {"value", "secondary", "amount", "units", "hours", "level"} or "value" in label_clean.lower()
    role = f"In {operation}, “{label_clean}” is an active calculation input, not an ignored compatibility field." if ambiguous else ""
    return " ".join(part for part in (base, role, example) if part)


class OperationDialog(_AsyncOperationDialog):
    def _field_editor(self, key: str, label: str, default, kind: str):
        widget = make_widget(kind, default)
        tip = contextual_field_help(self.mode, key, label, default, kind)
        widget.setToolTip(tip); widget.setAccessibleDescription(tip)
        column = QWidget(); layout = QVBoxLayout(column); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(4)
        layout.addWidget(widget)
        hint = QLabel(tip); hint.setWordWrap(True); hint.setObjectName("Muted"); layout.addWidget(hint)
        return widget, column

    def _rebuild(self):
        # The async parent now inserts Search Center in its final spanning form-row
        # position. Do not remove/reinsert the owned widget here: native Qt on macOS can
        # dereference the removed row during later dialog construction.
        super()._rebuild()
        if self.mode is None or self.mode.legacy is None:
            return

        description = _operation_description(self.mode).strip()
        fields = self.executor.input_fields(self.mode.legacy)
        labels = []
        location_added = False
        for key, label, _default, _kind in fields:
            if str(key) in LOCATION_KEYS:
                if not location_added:
                    labels.append("Search Center")
                    location_added = True
                continue
            labels.append(str(label))
        if labels:
            names = ", ".join(labels[:6])
            if len(labels) > 6: names += f", and {len(labels) - 6} more"
            self.mode_help.setText(f"{description} Inputs: {names}.")
        else:
            self.mode_help.setText(description + " This action uses live/saved application state and does not ask for unused compatibility values.")

        explained = _OUTPUT_EXPLANATIONS.get(self.mode.name)
        if explained:
            self.output_help.setText(explained)
