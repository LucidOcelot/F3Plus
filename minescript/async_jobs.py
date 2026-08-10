from __future__ import annotations

"""Small Qt background-job framework for expensive F3+ operations."""

import threading
import traceback
from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


_thread_state = threading.local()


class JobCancelled(RuntimeError):
    pass


def cancel_requested() -> bool:
    event = getattr(_thread_state, "cancel_event", None)
    return bool(event is not None and event.is_set())


def raise_if_cancelled() -> None:
    if cancel_requested():
        raise JobCancelled("Operation cancelled")


class _Signals(QObject):
    finished = Signal(object)
    failed = Signal(str, str)
    cancelled = Signal()


class _Runnable(QRunnable):
    def __init__(self, fn: Callable, cancel_event: threading.Event):
        super().__init__(); self.fn = fn; self.cancel_event = cancel_event; self.signals = _Signals(); self.setAutoDelete(True)

    def run(self):
        _thread_state.cancel_event = self.cancel_event
        try:
            raise_if_cancelled(); value = self.fn(); raise_if_cancelled(); self.signals.finished.emit(value)
        except JobCancelled:
            self.signals.cancelled.emit()
        except Exception as exc:
            self.signals.failed.emit(str(exc), traceback.format_exc())
        finally:
            try: del _thread_state.cancel_event
            except AttributeError: pass


@dataclass
class BackgroundJob:
    runnable: _Runnable
    cancel_event: threading.Event

    def cancel(self):
        self.cancel_event.set()


def start_job(fn: Callable, *, finished, failed, cancelled=None) -> BackgroundJob:
    event = threading.Event(); runnable = _Runnable(fn, event); runnable.signals.finished.connect(finished); runnable.signals.failed.connect(failed)
    if cancelled is not None: runnable.signals.cancelled.connect(cancelled)
    QThreadPool.globalInstance().start(runnable)
    return BackgroundJob(runnable, event)
