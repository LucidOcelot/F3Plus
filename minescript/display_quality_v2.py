from __future__ import annotations

"""Display names and guides for final semantic-quality corrections."""


def install() -> None:
    from . import descriptions, tool_guides

    tool_guides.DISPLAY_NAMES.update({
        ("Seed Tools", "Slime", "Farm Location Ranking"): "Slime Farm Site Ranking",
        ("Seed Tools", "Nether", "Portal Reliability Heatmap"): "Portal Proximity Heatmap",
        ("Seed Tools", "World Analysis", "Spawn Analysis"): "Spawn-Origin Area Analysis",
        ("Seed Tools", "World Analysis", "Spawn Chunk Optimizer"): "Spawn-Area Technical Site Ranking",
        ("Seed Tools", "World Analysis", "Chunk Loading Simulator"): "Simulation-Distance Footprint",
        ("Seed Tools", "World Analysis", "Search Radius Optimizer"): "Search Radius Cost Planner",
        ("Seed Tools", "World Analysis", "Ancient City Area Analysis"): "Ancient City Candidate Area Analysis",
        ("Seed Tools", "Biomes", "Terrain Base Finder"): "Generated Terrain Base-Site Ranking",
        ("Calculators", "Build", "Circle Layer Export"): "Circle Layer Coordinate Export",
        ("Navigation", "Waypoints", "Nearest Waypoint"): "Nearest Saved Waypoint",
        ("Navigation", "Waypoints", "Sort Waypoints by Distance"): "Saved Waypoints by Distance",
        ("Navigation", "Waypoints", "Waypoint Route"): "Saved Waypoint Route",
    })

    descriptions.SPECIAL.update({
        "Farm Location Ranking": (
            "Ranks slime-farm candidate chunks by explicit factors: slime chunks in a centered 3×3 neighborhood, "
            "cardinal cluster size, then distance from the reference. No hidden composite score is used."
        ),
        "Portal Reliability Heatmap": (
            "Visualizes geometric proximity to an ideal Nether coordinate. The displayed proximity value is not a portal-link probability; "
            "vanilla search rules, Y level, active portals, and competition still determine actual links."
        ),
        "Spawn Analysis": (
            "Analyzes seed-level context around coordinate origin. It does not claim that Minecraft's final player spawn is exactly chunk 0,0."
        ),
        "Spawn Chunk Optimizer": (
            "Ranks nearby technical-site candidates by explicit slime access and distance from the reference. It does not optimize or change Minecraft spawn chunks."
        ),
        "Chunk Loading Simulator": (
            "Shows the square simulation-distance footprint around a chosen center chunk, including chunk/block bounds and the outer ring. "
            "It is more detailed than the general Simulation Distance calculator and does not claim ticket-level exactness."
        ),
        "Search Radius Optimizer": (
            "Compares square scan sizes and relative geometric work for common radii. F3+ does not pretend a target candidate count can predict a radius without a target-specific density model."
        ),
        "Terrain Base Finder": (
            "Ranks generated chunks that combine higher mean surface elevation with lower within-chunk relief. The old opaque base-score number is no longer shown as a meaningful game statistic."
        ),
        "Circle Layer Export": (
            "Generates one circle layer as copy/export-ready coordinate text in CSV, semicolon, or Minecraft-relative format rather than duplicating the Circle shape preview."
        ),
        "Structure Heatmap": (
            "Groups placement candidates into chunk-grid cells and reports readable chunk bounds and candidate counts for each cell."
        ),
        "Structure Cluster Finder": (
            "Finds local placement-candidate groups and de-duplicates identical member sets. Results name structure types and give chunk/block-center coordinates."
        ),
        "Isolated Structure Finder": (
            "Ranks tracked placement candidates by distance to the nearest other tracked candidate, with chunk and approximate block distances."
        ),
        "Structure Chains": (
            "Builds a greedy nearest-next chain through placement candidates and translates each stop to structure, chunk, and block-center coordinates."
        ),
        "Structure Corridor": (
            "Lists placement candidates inside the configured chunk corridor with structure names and block-center coordinates instead of raw tuples."
        ),
        "Seed Comparison": (
            "Compares two seeds over the same radius and explicitly reports second-minus-first deltas for slime chunks and tracked structure candidates."
        ),
        "Lake Density": (
            "Reports enclosed sampled water components and translates the raw density fraction into a percentage of scanned generated chunks."
        ),
        "Largest Cave Region": (
            "Explains the cave-air threshold used to decide which generated chunks join the connected cave-region map."
        ),
        "Nearest Waypoint": (
            "Finds only the single saved waypoint nearest to the supplied/current position and reports straight-line distance, vertical change, and direction."
        ),
        "Sort Waypoints by Distance": (
            "Ranks every saved waypoint independently by straight-line distance from the same origin. It does not reuse the multi-stop route order."
        ),
        "Waypoint Route": (
            "Builds a greedy nearest-next route through all saved waypoints, reports each leg and total horizontal route length, and can return to the origin."
        ),
    })

    tool_guides._OUTPUT_EXACT.update({
        "Farm Location Ranking": "Returns ranked slime sites with 3×3 slime concentration, connected-cluster size, block-center coordinates, distance, and direction.",
        "Portal Reliability Heatmap": "Returns Nether candidate positions with distance from ideal, Overworld-equivalent error, normalized proximity, and an explicit non-probability warning.",
        "Spawn Chunk Optimizer": "Returns ranked nearby technical sites using named slime-access and distance factors; no composite score is returned.",
        "Chunk Loading Simulator": "Returns center chunk, simulation radius, exact square chunk/block bounds, total chunks, and outer-ring coordinates.",
        "Search Radius Optimizer": "Returns common scan-radius options, square chunk counts, relative geometric work, and the smallest listed radius covering the request.",
        "Terrain Base Finder": "Returns ranked generated chunks with mean surface Y, local relief, and a readable finding rather than an opaque base score.",
        "Circle Layer Export": "Returns circle coordinates plus copy/export-ready text in the selected format.",
        "Seed Comparison": "Returns both seed summaries plus explicit second-minus-first deltas for the metrics actually measured.",
        "Nearest Waypoint": "Returns one nearest saved waypoint with coordinates, horizontal/3D distance, vertical change, and direction.",
        "Sort Waypoints by Distance": "Returns all saved waypoints ranked by distance from the same origin; it is not a route.",
        "Waypoint Route": "Returns greedy route order, per-leg distances/directions, total horizontal route length, and optional return-to-origin state.",
    })
