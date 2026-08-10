from __future__ import annotations

"""Responsive public wrapper for calculator/explorer workbenches.

Long operations execute off the Qt event thread, world/search tools share a Minecraft-
oriented center selector, and live/control operations return visible results instead of
silently mutating state elsewhere in the application.
"""

from PySide6.QtWidgets import QLabel, QMessageBox, QProgressBar

from .async_jobs import start_job
from .feature_executor import MACRO_NAMES
from .location_input import LOCATION_KEYS, LocationInput, applies_to as location_applies
from .workbench_forms import OperationDialog as _OperationDialog, _CONTROL_DELEGATES


class OperationDialog(_OperationDialog):
    def __init__(self, *args, **kwargs):
        self._job = None
        self._job_spec = None
        self.location_panel = None
        super().__init__(*args, **kwargs)

        # Every long-running generic operation gets an unmistakable activity state.
        self.activity_label = QLabel("Working…"); self.activity_label.setObjectName("Muted"); self.activity_label.hide()
        self.activity = QProgressBar(); self.activity.setRange(0, 0); self.activity.setTextVisible(False); self.activity.hide()
        host = self.run_btn.parentWidget()
        layout = host.layout() if host is not None else None
        if layout is not None:
            insert_at = max(0, layout.count() - 1)
            layout.insertWidget(insert_at, self.activity_label)
            layout.insertWidget(insert_at + 1, self.activity)

    def _rebuild(self):
        super()._rebuild()
        self.location_panel = None

        # The historical base description called Arch a span/height tool even though
        # its actual geometry consumes one radius. Keep the public UI tied to the real
        # engine contract rather than compatibility-era copy.
        if self.mode is not None and self.mode.name == "Arch":
            self.mode_help.setText(
                "Generates the upper half of a hollow block circle from one radius. "
                "The finished arch is about 2×radius + 1 blocks wide and rises about radius blocks; "
                "the result is a discrete construction blueprint, not an in-world scan."
            )

        if self.mode is None or self.mode.legacy is None or not location_applies(self.mode.legacy):
            return

        # Hide historical x/z/cx/cz fields and replace them with one coherent center panel.
        for key in LOCATION_KEYS:
            widget = self.inputs.get(key)
            if widget is None:
                continue
            editor = widget.parentWidget()
            if editor is not None:
                label = self.form.labelForField(editor)
                if label is not None:
                    label.hide()
                editor.hide()

        self.location_panel = LocationInput(self.parent(), self)
        self.form.insertRow(0, "", self.location_panel)
        self.note.setText(
            "Choose the search center above, then set only the operation-specific limits/options below. "
            "F3+ converts the center to the coordinate form required by the underlying calculation."
        )

    def values(self):
        values = super().values()
        if self.location_panel is not None:
            for key in LOCATION_KEYS:
                values.pop(key, None)
            values.update(self.location_panel.values())
        return values

    def _show_activity(self, text: str):
        self.activity_label.setText(text)
        self.activity_label.show(); self.activity.show()

    def _hide_activity(self):
        self.activity.hide(); self.activity_label.hide()

    def _show_control_result(self, legacy, data):
        self.result_view.set_result(legacy, data, self.settings.theme, self.settings.custom_palette)
        self._show_page(1)

    def _run_control(self, owner, legacy, values) -> bool:
        name = legacy.name
        if name in {"Current Position", "Capture Position"}:
            owner.capture_position()
            pos = getattr(owner, "current_position", None)
            if pos is not None:
                self._show_control_result(legacy, {
                    "purpose": "Current player position captured from Minecraft.",
                    "x": pos.x, "y": pos.y, "z": pos.z,
                    "chunk_x": int(pos.x // 16), "chunk_z": int(pos.z // 16),
                    "dimension": owner.settings.dimension,
                    "source": "Live F3+C capture",
                })
            return True
        if name == "Copy Sister Coordinates":
            q = owner._sister_position()
            if q is not None:
                owner.copy_sister()
                self._show_control_result(legacy, {
                    "purpose": "Converted the current Overworld/Nether position using the 8:1 horizontal scale and copied it to the clipboard.",
                    "x": q[0], "y": q[1], "z": q[2], "dimension": q[3], "copied": True,
                })
            return True
        if name == "Save Sister Waypoint":
            before = set(owner.settings.waypoints)
            owner.save_sister_waypoint()
            created = [key for key in owner.settings.waypoints if key not in before]
            self._show_control_result(legacy, {
                "purpose": "Saved the converted sister coordinate as a local F3+ waypoint.",
                "saved": bool(created), "waypoint": created[-1] if created else None,
            })
            return True
        if name in _CONTROL_DELEGATES:
            if hasattr(owner, "run_mode"):
                owner.run_mode(self.mode, values)
            self._show_control_result(legacy, {
                "purpose": f"Completed the {name} application action.",
                "action": name, "completed": True,
            })
            return True
        return False

    def _run(self):
        if self._job is not None:
            self._job.cancel()
            self.run_btn.setText("Cancelling…")
            self.run_btn.setEnabled(False)
            self.activity_label.setText("Cancelling after the current safe checkpoint…")
            return
        if self.mode is None or self.mode.legacy is None:
            return
        legacy = self.mode.legacy
        owner = self.parent()
        try:
            values = self.values()
        except Exception as exc:
            QMessageBox.warning(self, legacy.name, str(exc)); return
        name = legacy.name

        if owner is not None:
            if self._run_control(owner, legacy, values):
                return
            try:
                from .state_workbenches import stateful_operation
                if stateful_operation(owner, name):
                    self._show_control_result(legacy, {
                        "purpose": f"Completed the {name} local-state operation.",
                        "action": name, "completed": True,
                    })
                    return
            except Exception:
                pass
            if name in MACRO_NAMES:
                if hasattr(owner, "run_mode"):
                    owner.run_mode(self.mode, values)
                return

        self._job_spec = legacy
        self.run_btn.setText("Cancel")
        self.run_btn.setEnabled(True)
        self.note.setText("Running in the background. The interface remains usable; Cancel is cooperative and stops at a safe checkpoint.")
        self._show_activity(f"Running {name}…")
        self._job = start_job(
            lambda: self.executor.execute(legacy, values),
            finished=self._job_finished,
            failed=self._job_failed,
            cancelled=self._job_cancelled,
        )

    def _reset_job_ui(self):
        self._job = None
        self._job_spec = None
        self._hide_activity()
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run")
        fields = bool(self.inputs) or self.location_panel is not None
        self.note.setText(
            "Only the inputs shown here are collected from you; legacy compatibility defaults remain internal."
            if fields else
            "This operation uses saved/live application state and does not require manual input."
        )

    def _job_finished(self, result):
        spec = self._job_spec
        self._reset_job_ui()
        if spec is None:
            return
        self.result_view.set_result(spec, result, self.settings.theme, self.settings.custom_palette)
        self._show_page(1)

    def _job_failed(self, message: str, detail: str):
        name = getattr(self._job_spec, "name", "Operation")
        self._reset_job_ui()
        box = QMessageBox(QMessageBox.Warning, name, message, parent=self)
        box.setDetailedText(detail)
        box.exec()

    def _job_cancelled(self):
        self._reset_job_ui()
        self.note.setText("Operation cancelled. Inputs were preserved so you can adjust them and run again.")

    def closeEvent(self, event):
        if self._job is not None:
            self._job.cancel()
        super().closeEvent(event)
