from __future__ import annotations
from .base import InputCapabilities
from .standard import StandardInputBackend


class HybridTargetedInput:
    """Target keyboard/buttons at Minecraft; use normal OS input for camera movement.

    The UI must focus Minecraft before a relative-mouse step. Keeping this behavior in
    one backend means macro code does not need platform-specific branches.
    """
    def __init__(self, targeted):
        self.targeted = targeted
        self.foreground = StandardInputBackend()
        base = targeted.capabilities
        self.capabilities = InputCapabilities(
            name=base.name,
            targeted_keyboard=base.targeted_keyboard,
            targeted_mouse_buttons=base.targeted_mouse_buttons,
            targeted_relative_mouse=False,
            unfocused=base.unfocused,
            minimized=base.minimized,
            focus_switch=True,
            relative_requires_focus=True,
            all_input_requires_focus=False,
            session=base.session,
            background_label=base.background_label,
            minimized_label=base.minimized_label,
            notes=base.notes + " Camera turns use foreground relative mouse input after the user approves focus switching.",
        )

    @property
    def target(self):
        return getattr(self.targeted, "target", None)

    @target.setter
    def target(self, value):
        self.targeted.target = value

    def key_down(self, name): return self.targeted.key_down(name)
    def key_up(self, name): return self.targeted.key_up(name)
    def tap(self, name, hold=.05): return self.targeted.tap(name, hold)
    def chord(self, *names, hold=.04): return self.targeted.chord(*names, hold=hold)
    def mouse_down(self, button): return self.targeted.mouse_down(button)
    def mouse_up(self, button): return self.targeted.mouse_up(button)
    def click(self, button, hold=.05): return self.targeted.click(button, hold)
    def move_relative(self, dx, dy=0): return self.foreground.move_relative(dx, dy)

    def release_all(self):
        try: self.targeted.release_all()
        finally: self.foreground.release_all()


class FocusRequiredInput(StandardInputBackend):
    """Foreground input used when the compositor offers no arbitrary target API."""
    def __init__(self, name="Focus-switch input", session=""):
        super().__init__()
        self.capabilities = InputCapabilities(
            name=name,
            targeted_keyboard=False,
            targeted_mouse_buttons=False,
            targeted_relative_mouse=False,
            unfocused=False,
            minimized=False,
            focus_switch=True,
            relative_requires_focus=True,
            all_input_requires_focus=True,
            session=session,
            background_label="Focus switching",
            minimized_label="Restores/focuses window first",
            notes="This desktop session does not expose a portable arbitrary-window input API. F3+ can focus Minecraft before automation, with user approval.",
        )
