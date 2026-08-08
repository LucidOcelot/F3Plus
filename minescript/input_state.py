from __future__ import annotations
import threading

class IntentTrackingInput:
    """Tracks macro intent separately from the physical held state.

    pause() can release the physical keys without forgetting what the macro intended
    to hold. resume() then reacquires exactly that state.
    """
    def __init__(self, backend):
        self.backend=backend
        self._intended_keys=set()
        self._intended_buttons=set()
        self._lock=threading.RLock()
        self.suspended=False

    @property
    def capabilities(self): return getattr(self.backend,'capabilities',None)

    def key_down(self,name):
        n=str(name)
        with self._lock:
            self._intended_keys.add(n)
            if not self.suspended:self.backend.key_down(n)
    def key_up(self,name):
        n=str(name)
        with self._lock:
            self._intended_keys.discard(n)
            if not self.suspended:self.backend.key_up(n)
    def mouse_down(self,button):
        b=str(button)
        with self._lock:
            self._intended_buttons.add(b)
            if not self.suspended:self.backend.mouse_down(b)
    def mouse_up(self,button):
        b=str(button)
        with self._lock:
            self._intended_buttons.discard(b)
            if not self.suspended:self.backend.mouse_up(b)
    def tap(self,name,hold=.05):
        if self.suspended:return
        return self.backend.tap(name,hold)
    def chord(self,*names,hold=.04):
        if self.suspended:return
        return self.backend.chord(*names,hold=hold)
    def click(self,button,hold=.05):
        if self.suspended:return
        return self.backend.click(button,hold)
    def move_relative(self,dx,dy=0):
        if self.suspended:return
        return self.backend.move_relative(dx,dy)

    def suspend(self):
        with self._lock:
            self.suspended=True
            self.backend.release_all()

    def resume(self):
        with self._lock:
            self.suspended=False
            for key in sorted(self._intended_keys): self.backend.key_down(key)
            for button in sorted(self._intended_buttons): self.backend.mouse_down(button)

    def release_all(self,clear_intent=True):
        with self._lock:
            self.backend.release_all()
            if clear_intent:
                self._intended_keys.clear(); self._intended_buttons.clear()

    @property
    def intended_keys(self): return frozenset(self._intended_keys)
    @property
    def intended_buttons(self): return frozenset(self._intended_buttons)
