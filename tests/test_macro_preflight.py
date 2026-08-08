from __future__ import annotations

import time

from minescript.config import Settings
from minescript.macro_engine import MacroEngine


class FailingBackend:
    def __init__(self):
        self.released = False

    def preflight(self):
        raise RuntimeError("backend probe failed")

    def release_all(self):
        self.released = True

    def key_down(self, *_):
        raise AssertionError("macro input must not run after failed preflight")

    key_up = mouse_down = mouse_up = key_down

    def tap(self, *_args, **_kwargs):
        raise AssertionError("macro input must not run after failed preflight")

    chord = click = move_relative = tap


def test_macro_preflight_failure_is_reported_and_releases_input():
    backend = FailingBackend()
    engine = MacroEngine(backend, Settings())
    engine.start("Probe", lambda e: e.input.key_down("w"))
    engine.thread.join(timeout=2)
    assert not engine.status.running
    assert "backend probe failed" in engine.status.message
    assert "failed" in engine.status.name.lower()
    assert backend.released
