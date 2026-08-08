from __future__ import annotations
import threading
import time
from dataclasses import dataclass
from typing import Callable
from .input_state import IntentTrackingInput

@dataclass
class MacroStatus:
    name: str = "None"
    running: bool = False
    paused: bool = False
    started: float = 0.0
    cycles: int = 0
    message: str = ''

class MacroEngine:
    def __init__(self, input_engine):
        self.input = input_engine if isinstance(input_engine,IntentTrackingInput) else IntentTrackingInput(input_engine)
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.status = MacroStatus()
        self.on_status: Callable[[MacroStatus], None] | None = None
        self.position_provider=None

    def _emit(self):
        if self.on_status:self.on_status(self.status)

    def set_input(self,input_engine):
        self.stop(); self.input=IntentTrackingInput(input_engine)

    def set_position_provider(self,provider): self.position_provider=provider
    def get_position(self):
        if not self.position_provider: raise RuntimeError('Coordinate capture is required for this macro.')
        return self.position_provider()

    def start(self, name: str, fn: Callable):
        self.stop(); self.stop_event.clear(); self.pause_event.clear()
        self.status = MacroStatus(name=name, running=True, started=time.time()); self._emit()
        def runner():
            try: fn(self)
            except Exception as exc:
                self.status.message=str(exc)
            finally:
                self.input.release_all(clear_intent=True)
                self.status.running=False; self.status.paused=False; self._emit()
        self.thread=threading.Thread(target=runner,daemon=True); self.thread.start()

    def stop(self):
        self.stop_event.set(); self.input.release_all(clear_intent=True)
        t=self.thread
        if t and t.is_alive() and t is not threading.current_thread(): t.join(timeout=.5)
        self.status.running=False; self.status.paused=False; self._emit()

    def toggle_pause(self):
        if not self.status.running:return
        if self.pause_event.is_set():
            self.pause_event.clear(); self.input.resume(); self.status.paused=False
        else:
            self.pause_event.set(); self.input.suspend(); self.status.paused=True
        self._emit()

    def wait(self, seconds: float) -> bool:
        remaining=max(0,float(seconds)); last=time.monotonic()
        while not self.stop_event.is_set() and remaining>0:
            if self.pause_event.is_set():
                time.sleep(.025); last=time.monotonic(); continue
            now=time.monotonic(); remaining-=max(0,now-last); last=now
            time.sleep(min(.025,max(0,remaining)))
        return self.stop_event.is_set()
