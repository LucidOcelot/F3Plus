from __future__ import annotations

"""2.0 display-only corrections for historical catalog labels."""


def install() -> None:
    from . import descriptions, tool_guides

    tool_guides.DISPLAY_NAMES[("Seed Tools", "Local Area", "32-Chunk Analysis")] = "Local 33×33 Chunk Analysis"
    descriptions.SPECIAL["32-Chunk Analysis"] = (
        "Analyzes the inclusive ±16-chunk square around a center chunk: 33×33 chunks "
        "or 1,089 chunks total. The historical internal catalog ID is retained for "
        "saved favorites and compatibility."
    )
    tool_guides._OUTPUT_EXACT["32-Chunk Analysis"] = (
        "Returns the exact 33×33 scan dimensions, total chunk count, slime-chunk count, "
        "nearby structure placement-candidate counts, and biome analysis using the "
        "active version-aware world-generation backend."
    )
