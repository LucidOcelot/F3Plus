from __future__ import annotations

"""2.0 display-only corrections for historical catalog labels."""


def install() -> None:
    from . import descriptions, tool_guides

    names = {
        ("Seed Tools", "Local Area", "32-Chunk Analysis"): "Local 33×33 Chunk Analysis",
        ("Seed Tools", "Local Area", "Structure Counts"): "Structure Candidate Summary",
        ("Seed Tools", "Local Area", "Notable Locations"): "Nearby Seed Highlights",
        ("Seed Tools", "Local Area", "Technical Score"): "Technical Site Report",
        ("Seed Tools", "Local Area", "Build Score"): "Build Site Context",
        ("Seed Tools", "Local Area", "Exploration Score"): "Exploration Report",
        ("Seed Tools", "World Analysis", "Technical World Score"): "Technical World Report",
        ("Seed Tools", "World Analysis", "Resource Score"): "Resource Survey",
    }
    tool_guides.DISPLAY_NAMES.update(names)

    descriptions.SPECIAL.update({
        "32-Chunk Analysis": (
            "Analyzes the inclusive ±16-chunk square around a center chunk: 33×33 chunks "
            "or 1,089 chunks total. It summarizes biome composition, structure placement "
            "candidates, and slime chunks without pretending those are generated-terrain facts."
        ),
        "Biome Composition": (
            "Samples the requested local area and converts biome IDs into readable biome names, "
            "sample counts, and estimated sample-share percentages."
        ),
        "Structure Counts": (
            "Summarizes tracked structure placement candidates by type, including candidate count, "
            "candidate density, nearest candidate chunk/block center, distance, and direction."
        ),
        "Slime Distribution": (
            "Reports local slime-chunk density, comparison with the normal 10% expectation, nearest "
            "slime chunk, largest connected cluster, and coordinates for map preview."
        ),
        "Notable Locations": (
            "Turns nearby seed data into readable highlights: nearest tracked structure candidates, "
            "nearest slime chunk, approximate block distances/directions, and biome context."
        ),
        "Technical Score": (
            "A seed-level technical site report. It shows concrete slime-cluster and structure-access "
            "factors instead of collapsing unrelated measurements into an opaque 0–100 score."
        ),
        "Build Score": (
            "A build-site context report that separates what the seed can actually tell you from "
            "terrain facts that require generated chunks, such as flatness, cliffs, water, and caves."
        ),
        "Exploration Score": (
            "An exploration report based on sampled biome variety and nearby structure candidate types, "
            "with readable first-stop coordinates rather than an unexplained numeric score."
        ),
        "Technical World Score": (
            "Analyzes a generated world save and reports terrain relief, cave-space measurements, and "
            "resource density separately instead of combining them into an opaque score."
        ),
        "Resource Score": (
            "Surveys recognized ore blocks in generated chunks, grouping normal/deepslate variants and "
            "showing counts per scanned chunk, exposed counts, and the most-common counted Y level."
        ),
        "Compound Search": (
            "Finds neighborhoods where different structure placement candidates occur within a chosen "
            "maximum separation. It ranks actual multi-structure groupings rather than duplicating the locator report."
        ),
        "Multi-Target Locator": (
            "Finds the nearest placement candidate for each tracked structure type independently from "
            "one center point. It is intentionally different from Compound Search."
        ),
    })

    tool_guides._OUTPUT_EXACT.update({
        "32-Chunk Analysis": (
            "Returns the exact 33×33 scan dimensions, readable biome summary, nearest structure "
            "placement-candidate details, slime density/cluster information, and explicit version context."
        ),
        "Biome Composition": "Returns biome names, raw IDs, sample counts, estimated sample shares, and sampling resolution.",
        "Structure Counts": "Returns one distinct row per tracked structure type with count, density, nearest candidate, distance, and direction.",
        "Slime Distribution": "Returns density percent, comparison with the 10% expectation, nearest slime chunk, connected-cluster size, and chunk coordinates.",
        "Notable Locations": "Returns readable nearby highlights plus nearest structure/slime coordinates and biome context.",
        "Technical Score": "Returns named technical factors and an explained qualitative assessment; no hidden aggregate score is used.",
        "Build Score": "Returns seed-known build context and explicitly lists terrain questions that require generated-world data.",
        "Exploration Score": "Returns biome/structure variety plus nearest candidate stops with block coordinates, distance, and direction.",
        "Technical World Score": "Returns generated-world terrain, cave, and resource measurements as separate sections with per-chunk context.",
        "Resource Score": "Returns grouped ore/resource rows with counts, exposed counts, per-chunk density, and most-common counted Y.",
        "Compound Search": "Returns ranked close multi-structure candidate neighborhoods within the configured separation.",
        "Multi-Target Locator": "Returns the nearest candidate for each tracked structure type independently.",
    })
