from __future__ import annotations

"""Connect raw FeatureResult data to the 2.x visual result renderer.

The legacy dispatcher still formats text for compatibility with CLI/tests. The desktop
UI keeps the actual result object long enough to render nested dictionaries and rows as
metrics, sections, and tables rather than flattening them into a debug-style dump.
"""


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
            self.output.show_structured(
                guide.title,
                getattr(result, "data", {}),
                note=getattr(result, "note", "") or "",
                warning=warning,
            )
            self.executor._last_visual_result = None
            return
        return original_write(self, text)

    FeatureExecutor.execute = execute
    F3Plus.write = write
    F3Plus._structured_results_installed = True
