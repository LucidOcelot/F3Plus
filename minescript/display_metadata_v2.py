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
        ("Navigation", "Routes", "Survey Mode"): "Survey Grid Route",
        ("Calculators", "Build", "Grid"): "Construction Grid",
        ("Calculators", "Build", "Stacks"): "Build Stack Requirement",
        ("Calculators", "Build", "Shulkers"): "Build Shulker Requirement",
        ("Calculators", "Build", "Double Chests"): "Build Double-Chest Requirement",
        ("Calculators", "Shapes", "Spiral"): "Planar Spiral Layout",
        ("Calculators", "Shapes", "Helix"): "3D Helix Layout",
        ("Calculators", "Technical", "Mob Cap"): "Mob Cap Reference",
        ("RNG Tools", "Loot", "Loot Table Simulator"): "Custom Weighted Loot Simulator",
        ("RNG Tools", "Generation RNG", "Tree Generation Simulator"): "Tree Attempt Probability Model",
        ("RNG Tools", "Generation RNG", "Geode Generator"): "Geode Frequency Model",
        ("Seed Tools", "Spawners", "Spawner Cluster Ranking"): "Spawner Cluster Ranking",
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
        "Coordinate Route": "Plans one direct coordinate leg with distance, bearing, vertical change, and direction.",
        "Resource Route": "Orders supplied resource locations using a nearest-next route and reports each travel segment.",
        "Structure Tour": "Builds a multi-stop structure tour and can close the route back to the starting point.",
        "Biome Expedition": "Orders supplied biome destinations as an expedition route instead of reusing the generic coordinate-route report.",
        "Breadcrumb Recorder": "Summarizes a recorded path: samples, path length, start/end positions, and covered coordinate span.",
        "Expedition Recorder": "Summarizes expedition progress from recorded positions, including distance walked, displacement, and elapsed recording time.",
        "Survey Mode": "Generates a repeatable serpentine survey grid around a center point with explicit spacing and route length.",
        "Chunk Border": "Finds the nearest edge of the current chunk and how many blocks away it is.",
        "Chunk Line Navigator": "Produces a movement target on the nearest 16-block chunk grid line; it is not another chunk-bounds report.",
        "Region Border": "Finds the nearest edge of the current 32×32-chunk Anvil region and the distance to that edge.",
        "Asymmetric Portal Router": "Shows the selected modeled exit for each portal in an asymmetric network.",
        "Reliability Margin": "Ranks portal links by the gap between the selected exit and its nearest competitor; it is a confidence/separation report, not a link table.",
        "Bidirectional Link Matrix": "Checks whether modeled portal links return to the originating portal in the reverse direction.",
        "Portal Graph": "Presents modeled portals as graph nodes and directed link edges, including detected cycles.",
        "Grid": "Creates a regular construction grid at the requested spacing. Unlike Lighting Grid, it does not force a final point onto every far edge.",
        "Lighting Grid": "Places lighting-plan points across a footprint and includes far edges so boundary coverage is not silently omitted.",
        "Spiral": "Generates a flat spiral on the X/Z plane.",
        "Helix": "Generates a three-dimensional spiral that rises along Y. It is intentionally different from the planar Spiral tool.",
        "Storage Capacity": "Calculates how many items a chosen number/type of containers can hold; it does not calculate containers required for a target item count.",
        "Bulk Materials": "Summarizes an arbitrary item count as stacks, shulkers, and double chests for logistics planning.",
        "Shulker Requirement": "Calculates only the number of shulker boxes required for a target item count and the fill of the final box.",
        "Chest Requirement": "Calculates the selected chest/barrel count required for a target item count and the fill of the final container.",
        "Chunk Loader Planner": "Lays out relative loader centers needed to cover a rectangular chunk footprint.",
        "Chunk Loader Radius": "Shows the square planning footprint represented by one loader coverage radius; it is not a multi-loader layout.",
        "Loaded Chunk Area": "Reports a generic geometric loaded-area square. Actual ticket state may differ.",
        "Render Distance": "Reports the client render-distance footprint and explicitly does not equate rendering with entity simulation.",
        "Simulation Distance": "Reports the configured simulation-distance footprint, separate from client render distance.",
        "Mob Cap": "Quick vanilla mob-category cap reference. Use Mob Cap Calculator for eligible-chunk scaling.",
        "Mob Cap Calculator": "Scales a supplied mob-category cap by eligible spawning chunks and player count assumptions.",
        "Loot Table Simulator": "Simulates a weighted table supplied by the user as label:weight entries instead of silently inventing one generic loot table.",
        "Tree Generation Simulator": "Models user-supplied tree-attempt probability and reports successful modeled positions; biome/configured-feature rules are not invented.",
        "Geode Generator": "Models chunk-level geode frequency over a deterministic sample grid; it no longer shares the tree-attempt report.",
        "Decoration RNG": "Displays deterministic decoration-stage random draws without pretending those draws are finished world features.",
        "Feature Placement RNG": "Displays deterministic candidate positions from a placement-position model, with an explicit warning that a candidate is not a generated feature.",
        "Ore Placement Simulator": "Models triangular-height ore candidate placement for a supplied Y range instead of returning generic random coordinates.",
        "RNG Sequence Viewer": "Displays indexed raw Java RNG values in decimal and hexadecimal.",
        "RNG Timeline": "Displays Java RNG values as a normalized timeline with deltas and summary statistics.",
        "Enchantment Sequence Simulator": "Groups deterministic Java RNG draws into enchanting-attempt-sized bundles without claiming they are exact modern enchantment offers.",
        "2x2 Cluster": "Finds exact 2×2 squares of slime chunks.",
        "Quad Cluster": "Finds any cardinally connected slime component of four or more chunks; it does not require a 2×2 square.",
        "Double Spawner Locator": "Finds generated-world spawner groups meeting a two-spawner minimum within the cluster scan distance.",
        "Triple Spawner Locator": "Finds generated-world spawner groups meeting a three-spawner minimum within the cluster scan distance.",
        "Quad Spawner Locator": "Finds generated-world spawner groups meeting a four-spawner minimum within the cluster scan distance.",
        "Spawner Cluster Ranking": "Ranks larger nearby-spawner groups using a wider ranking radius rather than duplicating the double-spawner result.",
        "Branch Mine Wizard": "Automation shortcut to the canonical Branch Mine Setup. The shared planning engine is intentional and is labeled instead of presented as a second algorithm.",
        "Quarry Wizard": "Automation shortcut to the canonical Quarry Setup. Use Quarry Planner for a planning-only report.",
        "Tree Farm Wizard": "Automation shortcut to the canonical Tree Farm Setup.",
        "Crop Farm Wizard": "Automation shortcut to the canonical Crop Farm Setup.",
        "Nether Highway Wizard": "Automation shortcut to the canonical Nether Highway Setup.",
    })

    tool_guides._OUTPUT_EXACT.update({
        "32-Chunk Analysis": "Returns the exact 33×33 scan dimensions, readable biome summary, nearest structure placement-candidate details, slime density/cluster information, and explicit version context.",
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
        "Resource Route": "Returns ordered resource stops, per-leg directions/distances, total distance, and the declared routing method.",
        "Structure Tour": "Returns ordered structure stops, route segments, total distance, and whether the route closes back to the start.",
        "Biome Expedition": "Returns an ordered biome-destination route with per-leg travel information.",
        "Survey Mode": "Returns the generated serpentine survey points, spacing, point count, and planned route length.",
        "Spiral": "Returns a 2D X/Z spiral block path.",
        "Helix": "Returns a 3D X/Y/Z helix block path with radius, height, and turn count.",
        "Loot Table Simulator": "Returns normalized user-supplied weights, observed counts/rates, and a deterministic preview sequence.",
        "Tree Generation Simulator": "Returns modeled successful tree-attempt positions and observed success rate for the user-supplied chance.",
        "Geode Generator": "Returns modeled geode chunks, expected count, and observed modeled count across the deterministic sample grid.",
        "RNG Sequence Viewer": "Returns indexed raw Java RNG values.",
        "RNG Timeline": "Returns indexed normalized values, per-step deltas, minimum, maximum, and mean.",
    })
