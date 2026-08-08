from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable

from .control_bindings import BoundInput
from .input_state import IntentTrackingInput


@dataclass
class MacroStatus:
    name: str = "None"
    running: bool = False
    paused: bool = False
    started: float = 0.0
    cycles: int = 0
    message: str = ""


class MacroEngine:
    def __init__(self, input_engine, settings=None):
        self.settings = settings
        self.input = self._wrap_input(input_engine)
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.status = MacroStatus()
        self.on_status: Callable[[MacroStatus], None] | None = None
        self.position_provider = None
        self.focus_checker: Callable[[], bool] | None = None
        self._stop_reason = ""

    def _wrap_input(self, input_engine):
        if isinstance(input_engine, IntentTrackingInput):
            return input_engine
        backend = input_engine
        if self.settings is not None:
            backend = BoundInput(input_engine, self.settings.keybinds)
        return IntentTrackingInput(backend)

    def _emit(self) -> None:
        if self.on_status:
            self.on_status(self.status)

    def set_input(self, input_engine) -> None:
        self.stop()
        self.input = self._wrap_input(input_engine)

    def set_settings(self, settings) -> None:
        self.settings = settings
        backend = getattr(self.input, "backend", self.input)
        if isinstance(backend, BoundInput):
            backend.keybinds = settings.keybinds

    def set_position_provider(self, provider) -> None:
        self.position_provider = provider

    def set_focus_checker(self, checker: Callable[[], bool] | None) -> None:
        self.focus_checker = checker

    def get_position(self):
        if not self.position_provider:
            raise RuntimeError("Coordinate capture is required for this macro.")
        return self.position_provider()

    def coordinate_policy(self):
        from .gameplay.coordinate_control import CoordinatePolicy
        if self.settings is None:
            return CoordinatePolicy()
        interval = max(0.1, float(self.settings.movement_check_ms) / 1000.0)
        stuck_samples = max(1, round(float(self.settings.stuck_window_seconds) / interval))
        return CoordinatePolicy(
            check_interval=interval,
            stuck_samples=stuck_samples,
            max_failures=max(1, int(self.settings.recovery_attempts)),
            min_progress=max(0.0, float(self.settings.stuck_min_displacement)),
        )

    def turn_degrees(self, degrees: float) -> None:
        units_per_90 = 900
        if self.settings is not None:
            units_per_90 = max(1, int(self.settings.turn_units_per_90))
        self.input.move_relative(round(float(degrees) * units_per_90 / 90.0), 0)
        self.record_action()

    def start(self, name: str, fn: Callable) -> None:
        self.stop()
        self.stop_event.clear()
        self.pause_event.clear()
        self._stop_reason = ""
        self.status = MacroStatus(name=name, running=True, started=time.monotonic())
        self._emit()

        def runner() -> None:
            natural_completion = False
            try:
                delay = int(getattr(self.settings, "delayed_start_seconds", 0) or 0)
                if delay and self.wait(delay):
                    return
                fn(self)
                natural_completion = not self.stop_event.is_set()
            except Exception as exc:
                self.status.message = str(exc)
            finally:
                self.input.release_all(clear_intent=True)
                if natural_completion:
                    slot = int(getattr(self.settings, "restore_hotbar_slot", 0) or 0)
                    if 1 <= slot <= 9:
                        try:
                            self.input.tap(str(slot))
                        except (OSError, RuntimeError, ValueError):
                            pass
                if self._stop_reason and not self.status.message:
                    self.status.message = self._stop_reason
                self.status.running = False
                self.status.paused = False
                self._emit()

        self.thread = threading.Thread(target=runner, daemon=True)
        self.thread.start()

    def stop(self, reason: str = "") -> None:
        if reason:
            self._stop_reason = reason
        self.stop_event.set()
        self.input.release_all(clear_intent=True)
        thread = self.thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=0.5)
        self.status.running = False
        self.status.paused = False
        if reason:
            self.status.message = reason
        self._emit()

    def toggle_pause(self) -> None:
        if not self.status.running:
            return
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.input.resume()
            self.status.paused = False
        else:
            self.pause_event.set()
            self.input.suspend()
            self.status.paused = True
        self._emit()

    def record_action(self, count: int = 1) -> bool:
        self.status.cycles += max(1, int(count))
        self._emit()
        limit = int(getattr(self.settings, "action_limit", 0) or 0)
        if limit and self.status.cycles >= limit:
            self.stop_event.set()
            self._stop_reason = f"Action limit reached ({limit})."
            return False
        return True

    def _guard(self) -> bool:
        if self.stop_event.is_set():
            return False
        limit = int(getattr(self.settings, "runtime_limit_seconds", 0) or 0)
        if limit and self.status.started and time.monotonic() - self.status.started >= limit:
            self.stop_event.set()
            self._stop_reason = f"Runtime limit reached ({limit} seconds)."
            return False
        check_focus = bool(getattr(self.settings, "focus_loss_stop", False))
        if check_focus and self.focus_checker is not None:
            try:
                focused = bool(self.focus_checker())
            except (OSError, RuntimeError):
                focused = True
            if not focused:
                self.stop_event.set()
                self._stop_reason = "Minecraft lost focus; automation stopped and held inputs were released."
                return False
        return True

    def wait(self, seconds: float) -> bool:
        remaining = max(0.0, float(seconds))
        last = time.monotonic()
        while remaining > 0 and self._guard():
            if self.pause_event.is_set():
                time.sleep(0.025)
                last = time.monotonic()
                continue
            now = time.monotonic()
            remaining -= max(0.0, now - last)
            last = now
            time.sleep(min(0.025, max(0.0, remaining)))
        return not self._guard()
