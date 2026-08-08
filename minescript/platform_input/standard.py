from __future__ import annotations
from ..input_engine import InputEngine
from .base import InputCapabilities, TargetedInputError


class StandardInputBackend(InputEngine):
    """Portable foreground input through pynput where its OS backend is available."""
    capabilities = InputCapabilities(
        name="Standard foreground",
        targeted_keyboard=False, targeted_mouse_buttons=False, targeted_relative_mouse=False,
        unfocused=False, minimized=False, notes="Minecraft must receive normal OS focus for gameplay input.",
    )


class UnavailableInputBackend:
    """Keeps the UI alive when the desktop exposes no usable injection backend."""
    capabilities = InputCapabilities(
        name="Input unavailable", targeted_keyboard=False, targeted_mouse_buttons=False,
        targeted_relative_mouse=False, unfocused=False, minimized=False, focus_switch=False,
        all_input_requires_focus=True, background_label="Unavailable", minimized_label="Unavailable",
        notes="No usable foreground input backend is available. Calculators remain available; open Connection Status for details.",
    )
    def _fail(self,*a,**k): raise TargetedInputError("No usable gameplay input backend is available on this desktop session.")
    key_down=key_up=mouse_down=mouse_up=tap=chord=click=move_relative=_fail
    def release_all(self): return None
