from __future__ import annotations

"""Keep UI-only geometry context available to the 2.3.4 visual renderer.

Many calculators intentionally return a scalar answer. Their configured dimensions are
still useful for a footprint/plan preview, so this layer copies only the relevant input
geometry into a private result key that the normal text renderer hides.
"""

GEOMETRY_KEYS = {
    "width", "length", "height", "radius", "secondary", "spacing", "sag",
    "x", "y", "z", "x1", "y1", "z1", "x2", "y2", "z2",
}


def _context_for(spec, values: dict) -> dict:
    if getattr(spec, "top", "") == "Calculators" and getattr(spec, "submenu", "") in {"Build", "Shapes", "Farm"}:
        return {key: values[key] for key in GEOMETRY_KEYS if key in values}
    if getattr(spec, "top", "") == "Wizards":
        return {key: values[key] for key in GEOMETRY_KEYS if key in values}
    return {}


def install() -> None:
    from .feature_executor import FeatureExecutor
    from . import visual_results_v3

    if getattr(FeatureExecutor, "_visual_context_v234_installed", False):
        return

    previous_execute = FeatureExecutor.execute
    previous_construction_series = visual_results_v3.construction_series

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        values = self.defaults(spec)
        values.update(params or {})
        result = previous_execute(self, spec, params, dry_run)
        if not dry_run and isinstance(getattr(result, "data", None), dict):
            context = _context_for(spec, values)
            if context:
                result.data["_visual_context"] = context
        return result

    def construction_series(spec, data):
        rows = previous_construction_series(spec, data)
        if rows or not isinstance(data, dict):
            return rows
        context = data.get("_visual_context")
        if not isinstance(context, dict) or not context:
            return rows
        merged = dict(data)
        merged.update(context)
        rows = previous_construction_series(spec, merged)
        if rows:
            return rows
        # One-dimensional construction operations such as bridge spans still benefit
        # from a scale-aware plan line even when no second footprint dimension exists.
        length = context.get("length")
        try:
            length = float(length)
        except (TypeError, ValueError):
            length = 0.0
        if length > 0:
            return [("Planned span", [(0.0, 0.0), (length, 0.0)])]
        return []

    FeatureExecutor.execute = execute
    visual_results_v3.construction_series = construction_series
    FeatureExecutor._visual_context_v234_installed = True
