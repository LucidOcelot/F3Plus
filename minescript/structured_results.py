from __future__ import annotations

"""Connect raw FeatureResult data to the 2.x visual result renderer.

The executor keeps complete technical result dictionaries for tests, library callers,
and debugging. The desktop presentation intentionally removes internal dispatch and
implementation-contract metadata so the normal result view answers the user's question
instead of reading like a backend dump.
"""


_HIDDEN_PRESENTATION_KEYS = {
    "implementation",   # internal integrity contract; explained by the Inspector
    "operation",        # normally just repeats the selected tool name
    "display_name",     # already used as the visible guide/result title
    "mc_enum",          # Cubiomes implementation detail; version text is shown instead
    "bundled_newest_enum",
    "_visual_context",  # private renderer input copied from the user's configured geometry
}


def _presentation_data(value):
    if isinstance(value, dict):
        out = {}
        for key, child in value.items():
            if str(key) in _HIDDEN_PRESENTATION_KEYS:
                continue
            out[key] = _presentation_data(child)
        return out
    if isinstance(value, list):
        return [_presentation_data(child) for child in value]
    if isinstance(value, tuple):
        return tuple(_presentation_data(child) for child in value)
    return value


def install() -> None:
    from .app import F3Plus
    from .feature_executor import FeatureExecutor

    if getattr(F3Plus, "_structured_results_installed", False):
        return

    original_execute = FeatureExecutor.execute
    original_write = F3Plus.write

    def execute(self, feature, params=None, dry_run=False):
        result = original_execute(self, feature, params, dry_run)
        if not dry_run:
            self._last_visual_result = result
        return result

    def write(self, text):
        result = getattr(self.executor, "_last_visual_result", None)
        spec = self.selected_spec() if hasattr(self, "selected_spec") else None
        if (
            result is not None
            and spec is not None
            and getattr(result, "feature_id", None) == spec.id
            and hasattr(self.output, "show_structured")
        ):
            try:
                from .ux_v2 import _result_warning
                warning = _result_warning(self)
            except Exception:
                warning = ""
            guide = self._guide_for(spec)
            raw_data = getattr(result, "data", {})
            visible_data = _presentation_data(raw_data)
            self.output.show_structured(
                guide.title,
                visible_data,
                note=getattr(result, "note", "") or "",
                warning=warning,
            )
            try:
                from .visual_results import attach_visual_preview
                # Previews use the complete raw structure because internal technical
                # keys can still contain useful coordinate collections.
                attach_visual_preview(
                    self.output,
                    spec,
                    raw_data,
                    self.settings.theme,
                    self.settings.custom_palette,
                )
            except Exception as exc:
                # A visual is supplemental, but silently swallowing renderer defects made
                # missing maps/plans indistinguishable from genuinely non-spatial results.
                # Keep the exact result and expose one compact, actionable UI note.
                message = str(exc).strip().splitlines()[0] if str(exc).strip() else exc.__class__.__name__
                if len(message) > 220:
                    message = message[:217] + "..."
                try:
                    self.output._add_warning(
                        "The numeric/text result is still valid, but its visual preview could not be rendered: " + message,
                        label="VISUAL PREVIEW",
                    )
                except Exception:
                    pass
            self.executor._last_visual_result = None
            return
        return original_write(self, text)

    FeatureExecutor.execute = execute
    F3Plus.write = write
    F3Plus._structured_results_installed = True
