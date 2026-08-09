from __future__ import annotations

"""Tighten the desktop link state so UI state and input targeting cannot diverge."""


def install() -> None:
    from .app import F3Plus
    from .platform_input import create_focus_controller, create_input_backend, discover_minecraft_targets

    if getattr(F3Plus, "_connection_v2_installed", False):
        return

    def configure_input(self, target):
        # No linked client means no targeted backend is allowed to retain or lazily
        # rediscover an old HWND/process. Foreground mode is the safe unlinked state.
        mode = self.settings.input_mode if target is not None else "standard"
        self.input = create_input_backend(mode, self.settings.minecraft_window_title, target)
        self.focus_controller = create_focus_controller(target)
        self.engine.set_input(self.input)
        self.capture.input = self.input
        self.engine.set_position_provider(self.capture.capture)
        self.update_link_badges()

    def refresh_link_state(self):
        found = discover_minecraft_targets(self.settings.minecraft_window_title)
        if self.target is not None:
            match = next(
                (
                    candidate for candidate in found
                    if candidate.key == self.target.key
                    or (candidate.pid and self.target.pid and candidate.pid == self.target.pid)
                ),
                None,
            )
            if match is not None:
                self.target = match
                self.update_link_badges()
                return

            # The process/window that owned the link disappeared. Stop managed input
            # before clearing the target, then return to a non-targeted backend.
            self.engine.stop()
            self.target = None
            configure_input(self, None)
            if self.settings.auto_link_minecraft and len(found) == 1:
                self.link_target(found[0], quiet=True)
                return
            self.update_link_badges()
            return

        if self.settings.auto_link_minecraft and len(found) == 1:
            self.link_target(found[0], quiet=True)
            return
        self.update_link_badges()

    F3Plus._configure_input = configure_input
    F3Plus.refresh_link_state = refresh_link_state
    F3Plus._connection_v2_installed = True
