from __future__ import annotations

"""Responsive wrapper for the canonical calculator/explorer workbench."""

from PySide6.QtWidgets import QMessageBox

from .async_jobs import start_job
from .feature_executor import MACRO_NAMES
from .workbench_forms import OperationDialog as _OperationDialog, _CONTROL_DELEGATES


class OperationDialog(_OperationDialog):
    """OperationDialog with background execution and cooperative cancellation.

    Stateful UI actions and automation still delegate immediately to their dedicated
    controllers. Pure/analysis executor operations run in QThreadPool so an expensive
    region scan, expanding search, or calculation cannot freeze the workbench window.
    """

    def __init__(self, *args, **kwargs):
        self._job = None
        self._job_spec = None
        super().__init__(*args, **kwargs)

    def _run(self):
        if self._job is not None:
            self._job.cancel()
            self.run_btn.setText("Cancelling…")
            self.run_btn.setEnabled(False)
            return
        if self.mode is None or self.mode.legacy is None:
            return
        legacy = self.mode.legacy
        owner = self.parent()
        values = self.values()
        name = legacy.name

        if owner is not None:
            try:
                from .state_workbenches import stateful_operation
                if stateful_operation(owner, name):
                    return
            except Exception:
                pass
            if name in MACRO_NAMES or name in _CONTROL_DELEGATES:
                if hasattr(owner, "run_mode"):
                    owner.run_mode(self.mode, values)
                return

        self._job_spec = legacy
        self.run_btn.setText("Cancel")
        self.run_btn.setEnabled(True)
        self.note.setText("Running in the background. You can cancel this operation without freezing the interface.")
        self._job = start_job(
            lambda: self.executor.execute(legacy, values),
            finished=self._job_finished,
            failed=self._job_failed,
            cancelled=self._job_cancelled,
        )

    def _reset_job_ui(self):
        self._job = None
        self._job_spec = None
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run")
        fields = bool(self.inputs)
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
