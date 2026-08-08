from __future__ import annotations


def install() -> None:
    from .app import F3Plus
    from .gameplay import coordinate_control, macros

    if getattr(F3Plus, "_engine_guards_installed", False):
        return

    # All existing macros call this helper after a discrete cycle/action. Route it
    # through MacroEngine.record_action so the configured action limit is actually
    # enforceable across legacy and new presets.
    def guarded_cycle(engine):
        if hasattr(engine, "record_action"):
            return engine.record_action()
        engine.status.cycles += 1
        engine._emit()
        return True

    macros._cycle = guarded_cycle

    # Existing coordinate routines instantiate CoordinateController without an
    # explicit policy. Resolve the current settings-backed policy from MacroEngine
    # so stuck detection/recovery values are universal rather than UI-only.
    original_controller_init = coordinate_control.CoordinateController.__init__

    def controller_init(self, engine, policy=None):
        if policy is None and hasattr(engine, "coordinate_policy"):
            policy = engine.coordinate_policy()
        original_controller_init(self, engine, policy)

    coordinate_control.CoordinateController.__init__ = controller_init

    # ui_extensions already wraps F3Plus.__init__. Add focus-state wiring after that
    # wrapper finishes. capture_current() is intentionally used instead of a new
    # platform API so Windows/macOS/Wayland controllers keep ownership of the native
    # representation of a foreground token.
    prior_init = F3Plus.__init__

    def guarded_init(self, *args, **kwargs):
        prior_init(self, *args, **kwargs)

        def minecraft_is_focused():
            target = getattr(self, "target", None)
            controller = getattr(self, "focus_controller", None)
            if target is None or controller is None or not getattr(controller, "available", False):
                # If this platform cannot inspect focus reliably, do not invent a
                # negative result. Existing foreground-only input checks still apply.
                return True
            try:
                token = controller.capture_current()
            except Exception:
                return True
            candidates = {getattr(target, "native_id", None), getattr(target, "pid", None), getattr(target, "key", None)}
            if token in candidates:
                return True
            # Some controllers return lightweight objects/strings. Compare stable
            # textual IDs as a final cross-platform path.
            return str(token) in {str(v) for v in candidates if v is not None}

        self.engine.set_focus_checker(minecraft_is_focused)

    F3Plus.__init__ = guarded_init
    F3Plus._engine_guards_installed = True
