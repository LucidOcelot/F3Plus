from __future__ import annotations

"""Small user-facing semantic corrections that preserve stable catalog IDs.

Some catalog names are historical and cannot be renamed internally without breaking
favorites, recents, saved references, or tests. This layer makes the result itself
precise while the UI is free to use a clearer display name.
"""


def install() -> None:
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_v2_result_semantics_installed", False):
        return

    original_execute = FeatureExecutor.execute

    def execute(self, feature, params=None, dry_run=False):
        result = original_execute(self, feature, params, dry_run)
        spec = self.spec(feature)
        if spec.name == "32-Chunk Analysis" and isinstance(getattr(result, "data", None), dict):
            data = result.data
            radius = int(data.get("radius_chunks", 16))
            width = radius * 2 + 1
            data["analysis_width_chunks"] = width
            data["analysis_height_chunks"] = width
            data["total_chunks_in_square"] = width * width
            note = (
                f"The scan uses an inclusive ±{radius}-chunk radius around the center, "
                f"so the analyzed square is {width}×{width} chunks ({width * width:,} chunks). "
                "The original catalog ID is retained for compatibility."
            )
            prior = str(getattr(result, "note", "") or "").strip()
            result.note = (prior + " " + note).strip() if prior else note
        return result

    FeatureExecutor.execute = execute
    FeatureExecutor._v2_result_semantics_installed = True
