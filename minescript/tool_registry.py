from __future__ import annotations

"""Canonical F3+ product registry.

The historical catalog is retained only as a compatibility namespace. The desktop
application exposes coherent workbenches; old feature IDs resolve to a workbench mode
so favorites, recents, scripts and saved settings keep working without presenting
hundreds of near-duplicate buttons.
"""

from dataclasses import dataclass

from .catalog_ids import FeatureSpec, SPECS as LEGACY_SPECS


@dataclass(frozen=True)
class ToolSpec:
    id: str
    workspace: str
    group: str
    name: str
    summary: str
    top: str
    submenu: str
    limitations: str = ""
    special_modes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ToolMode:
    key: str
    name: str
    tool_id: str
    legacy: FeatureSpec | None = None
    special: str = ""


TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec("automation.actions", "Automation", "Actions", "Automation Studio",
             "Hold, repeat, fish, manage equipment, and run common hands-free gameplay routines from one safety-aware controller.", "Gameplay", "Continuous Action"),
    ToolSpec("automation.travel", "Automation", "Movement", "Travel & Mobility",
             "Automated and planned travel modes for walking, sprinting, swimming, vehicles, elytra, riptide, coordinates, waypoints, and Nether-assisted routes.", "Gameplay", "Travel"),
    ToolSpec("automation.mining", "Automation", "Mining", "Mining & Excavation",
             "Tunnel, branch, stair, area, quarry, perimeter, and beacon-mining workflows with the related setup plans in one place.", "Gameplay", "Mining"),
    ToolSpec("automation.farming", "Automation", "Farming", "Farm Automation",
             "Crop, tree, breeding, growth, row, and station automation plus the guided setups needed to configure them.", "Gameplay", "Farming"),
    ToolSpec("automation.construction", "Automation", "Building", "Construction Automation",
             "Line, rectangle, grid, rows, perimeter, alternating, and repeating placement routines under one construction controller.", "Gameplay", "Construction"),
    ToolSpec("automation.sequences", "Automation", "Advanced", "Sequences & Macro Workflows",
             "Record, assemble, sequence, and configure multi-step automation without duplicating each template as a separate tool.", "Gameplay", "Automation"),
    ToolSpec("automation.macro_studio", "Automation", "Advanced", "Macro Studio",
             "Record, edit, save, import/export, dry-review and run custom input sequences under the same safety controls as built-in automation.", "Gameplay", "Automation",
             special_modes=(("studio", "Macro Studio"),)),

    ToolSpec("navigation.position", "Navigation", "Position", "Live Position",
             "Capture, continuously track, announce, convert, and save the player's current coordinates.", "Navigation", "Position"),
    ToolSpec("navigation.coordinates", "Navigation", "Coordinates", "Coordinate & Travel Calculator",
             "Distance, bearing, midpoint, XYZ delta, travel time, chunk/region geometry, snapping, offsets, and Overworld/Nether conversion in one calculator.", "Navigation", "Coordinates"),
    ToolSpec("navigation.routes", "Navigation", "Routes", "Waypoints, Routes & Surveys",
             "Create and organize waypoints, rank nearby destinations, simplify breadcrumbs, build multi-stop routes, and record survey/expedition paths.", "Navigation", "Routes"),
    ToolSpec("navigation.portals", "Navigation", "Portals", "Portal Network Planner",
             "Plan sister portals, link competition, asymmetric routes, highway layouts, reliability, loops, routing tables, and multi-destination portal networks.", "Navigation", "Portal Helpers"),

    ToolSpec("world.seed_recovery", "World Explorer", "Seed", "World Seed Recovery",
             "The single supported world/structure-seed recovery workflow: Nether bedrock observations and the pinned cracker backend.", "Seed Tools", "World Seed Recovery",
             "Gameplay/player RNG recovery is intentionally separate and never presented as world-seed recovery."),
    ToolSpec("world.slime", "World Explorer", "Seed", "Slime Chunk Explorer",
             "Find, cluster, measure, and rank slime chunks around a known world seed from one explorer.", "Seed Tools", "Slime"),
    ToolSpec("world.structures", "World Explorer", "Structures", "Structure Explorer",
             "Search individual or combined structures, compare density and relationships, and inspect route/cluster candidates without one button per structure type.", "Seed Tools", "Structures"),
    ToolSpec("world.spawners", "World Explorer", "Generated World", "Spawner Explorer",
             "Inspect generated world data for actual spawners, mob filters, multi-spawner groups, clusters, stronghold silverfish, and trial spawners.", "Seed Tools", "Spawners"),
    ToolSpec("world.biomes", "World Explorer", "Biomes & Terrain", "Biome & Terrain Explorer",
             "Biome lookup, nearest/intersection searches, region sizing, terrain forms, islands, peaks, valleys, cliffs, rivers, and diversity analysis.", "Seed Tools", "Biomes"),
    ToolSpec("world.area", "World Explorer", "Analysis", "Local Area Analyzer",
             "Biome composition, structure counts, slime distribution, highlights, and technical/build/exploration reports for one bounded area.", "Seed Tools", "Local Area"),
    ToolSpec("world.analysis", "World Explorer", "Analysis", "World Analysis",
             "Spawn, resource, ore, cave, loading, search-radius, comparison, and world-suitability analysis from one workbench.", "Seed Tools", "World Analysis"),
    ToolSpec("world.nether", "World Explorer", "Nether", "Nether Explorer",
             "Known-seed Nether biome and fortress/bastion searching plus generation-specific reports that are not merely portal coordinate math.", "Seed Tools", "Nether"),
    ToolSpec("world.profiles", "World Explorer", "Projects", "World Profiles & Local Saves",
             "Discover local Java saves, read level.dat context, and reuse world path, seed and version information across F3+ workflows.", "Seed Tools", "World Analysis",
             special_modes=(("profiles", "World Profiles"), ("discover", "Discover Local Saves"))),

    ToolSpec("build.planner", "Build & Technical", "Building", "Build & Shape Planner",
             "Dimensions, materials, stairs, bridges, roofs, grids, lighting, roads, gradients, and geometric block layouts in one visual planning surface.", "Calculators", "Build"),
    ToolSpec("build.redstone", "Build & Technical", "Redstone", "Redstone & Timing Lab",
             "Tick conversion, hopper/comparator/repeater timing, transport timing, crafter throughput, clocks, counters, and signal planning.", "Calculators", "Redstone"),
    ToolSpec("build.storage", "Build & Technical", "Logistics", "Storage & Logistics",
             "Capacity, stacks, shulkers, chests, compression, bulk materials, transport trips, and logistics planning without duplicate capacity calculators.", "Calculators", "Storage"),
    ToolSpec("build.farming", "Build & Technical", "Farms", "Farm & Breeding Planner",
             "Yield, breeding, furnace/fuel, crop layouts, apiaries, villager halls, pens, beacon coverage, slime/fortress/trial planning, and guided farm setups.", "Calculators", "Farm"),
    ToolSpec("build.technical", "Build & Technical", "Technical", "Technical Minecraft Calculator",
             "Mob/loading radii, chunk alignment, sorters, perimeters, branch density, spawnproofing, technical spacing, and related geometry.", "Calculators", "Technical"),
    ToolSpec("build.resources", "Build & Technical", "Resources", "Resource, Speedrun & End Toolkit",
             "XP, Mending, anvil prior work, durability/consumables, speedrun coordinate planning, and End travel utilities grouped by task instead of isolated forms.", "Calculators", "Resource Usage"),
    ToolSpec("build.recipes", "Build & Technical", "Resources", "Recipe & Material Explorer",
             "Browse installed vanilla recipes and expand a target item into a recursive raw-material bill of materials for planning and logistics.", "Calculators", "Resource Usage",
             special_modes=(("recipes", "Recipe Explorer"), ("bom", "Recursive Material List"))),

    ToolSpec("simulation.rng", "Simulation & RNG", "RNG", "RNG & Enchanting Workbench",
             "Enchanting simulation, sequence/timeline views, probability, bookshelf/lapis/reset planning, Java LCG recovery, and player-RNG recovery in one workbench.", "RNG Tools", "Enchanting"),
    ToolSpec("simulation.loot", "Simulation & RNG", "Loot", "Loot & Drop Workbench",
             "Installed loot-table exploration, structure/fishing/archaeology/piglin/trial rewards, mob drops, and repeatable statistical simulation.", "RNG Tools", "Loot"),
    ToolSpec("simulation.generation", "Simulation & RNG", "Generation", "Generation RNG Workbench",
             "Decoration, feature, ore, tree, geode, trial-chamber, and structure-placement RNG previews from one generation-oriented surface.", "RNG Tools", "Generation RNG"),
    ToolSpec("simulation.mechanics", "Simulation & RNG", "Mechanics", "Minecraft Mechanics Lab",
             "Brewing, leather dye/cauldron behavior, animal breeding, and horse breeding as dedicated mechanic simulators.", "RNG Tools", "Mechanics",
             special_modes=(("brewing", "Brewing Stand"), ("dye", "Leather Dye & Cauldron"), ("breeding", "Animal & Horse Breeding"))),

    ToolSpec("villagers.explorer", "Villagers", "Trades", "Villager Explorer",
             "Browse professions and levels, search/compare trades, plan emerald/use cycles, focus librarians, and calculate curing, breeding, workstations, and halls.", "Villager Explorer", "Trades"),

    ToolSpec("utilities.version", "Utilities & Safety", "Version & Data", "Version & Data",
             "Selected Minecraft version, installed versions, compatibility, trade-data status, and bundled component readiness.", "Utilities", "Version / Backend"),
    ToolSpec("utilities.settings", "Utilities & Safety", "Settings", "Profiles, Controls & Calibration",
             "Import/export profiles, back up settings, edit bindings, and calibrate movement, turning, and coordinate capture.", "Utilities", "Controls"),
    ToolSpec("utilities.safety", "Utilities & Safety", "Safety", "Automation Safety",
             "Emergency stop, pause/resume, input release, focus-loss behavior, runtime/action limits, delayed start, stuck detection, and recovery policy.", "Safety", "Controls"),
    ToolSpec("utilities.results", "Utilities & Safety", "History", "Result History",
             "Keep recent F3+ calculations locally, inspect their source/version context, and export individual results as JSON.", "Utilities", "Profiles",
             special_modes=(("history", "Result History"),)),
    ToolSpec("utilities.diagnostics", "Utilities & Safety", "Diagnostics", "Diagnostics",
             "Inspect input backend state, installed Minecraft versions, component readiness, configuration location and saved-state counts.", "Utilities", "Version / Backend",
             special_modes=(("diagnostics", "Diagnostics"),)),
)

BY_ID: dict[str, ToolSpec] = {tool.id: tool for tool in TOOLS}

_ROUTE: dict[tuple[str, str], str] = {
    ("Gameplay", "Continuous Action"): "automation.actions",
    ("Gameplay", "Periodic Interaction"): "automation.actions",
    ("Gameplay", "Fishing"): "automation.actions",
    ("Gameplay", "Travel"): "automation.travel",
    ("Gameplay", "Mining"): "automation.mining",
    ("Gameplay", "Farming"): "automation.farming",
    ("Gameplay", "Equipment"): "automation.actions",
    ("Gameplay", "Construction"): "automation.construction",
    ("Gameplay", "Automation"): "automation.sequences",
    ("Navigation", "Position"): "navigation.position",
    ("Navigation", "Coordinates"): "navigation.coordinates",
    ("Navigation", "Waypoints"): "navigation.routes",
    ("Navigation", "Routes"): "navigation.routes",
    ("Navigation", "Portal Helpers"): "navigation.portals",
    ("Seed Tools", "World Seed Recovery"): "world.seed_recovery",
    ("Seed Tools", "Slime"): "world.slime",
    ("Seed Tools", "Cubiomes"): "utilities.version",
    ("Seed Tools", "Nether"): "world.nether",
    ("Seed Tools", "Structures"): "world.structures",
    ("Seed Tools", "Spawners"): "world.spawners",
    ("Seed Tools", "Biomes"): "world.biomes",
    ("Seed Tools", "Local Area"): "world.area",
    ("Seed Tools", "World Analysis"): "world.analysis",
    ("Calculators", "Coordinate"): "navigation.coordinates",
    ("Calculators", "Build"): "build.planner",
    ("Calculators", "Shapes"): "build.planner",
    ("Calculators", "Redstone"): "build.redstone",
    ("Calculators", "Storage"): "build.storage",
    ("Calculators", "Farm"): "build.farming",
    ("Calculators", "Technical"): "build.technical",
    ("Calculators", "Speedrunning"): "build.resources",
    ("Calculators", "Resource Usage"): "build.resources",
    ("Calculators", "End"): "build.resources",
    ("RNG Tools", "RNG Recovery"): "simulation.rng",
    ("RNG Tools", "Enchanting"): "simulation.rng",
    ("RNG Tools", "Drops"): "simulation.loot",
    ("RNG Tools", "Probability"): "simulation.rng",
    ("RNG Tools", "Loot"): "simulation.loot",
    ("RNG Tools", "Generation RNG"): "simulation.generation",
    ("Villager Explorer", "Trades"): "villagers.explorer",
    ("Villager Explorer", "Professions"): "villagers.explorer",
    ("Villager Explorer", "Helpers"): "villagers.explorer",
    ("Wizards", "Mining"): "automation.mining",
    ("Wizards", "Farming"): "build.farming",
    ("Wizards", "Portals"): "navigation.portals",
    ("Wizards", "Building"): "build.planner",
    ("Utilities", "Version / Backend"): "utilities.version",
    ("Utilities", "Profiles"): "utilities.settings",
    ("Utilities", "Controls"): "utilities.settings",
    ("Safety", "Controls"): "utilities.safety",
}

LEGACY_TO_CANONICAL: dict[str, str] = {}
_MODES: dict[str, list[ToolMode]] = {tool.id: [] for tool in TOOLS}
_unmapped: list[str] = []
for spec in LEGACY_SPECS:
    tool_id = _ROUTE.get((spec.top, spec.submenu))
    if tool_id is None:
        _unmapped.append(f"{spec.top} / {spec.submenu} / {spec.name}")
        continue
    LEGACY_TO_CANONICAL[spec.id] = tool_id
    _MODES[tool_id].append(ToolMode(spec.id, spec.name, tool_id, legacy=spec))

if _unmapped:
    raise RuntimeError("Legacy catalog entries without a canonical route:\n" + "\n".join(_unmapped))

for tool in TOOLS:
    for key, name in tool.special_modes:
        _MODES[tool.id].append(ToolMode(key, name, tool.id, special=key))

MODES_BY_TOOL: dict[str, tuple[ToolMode, ...]] = {key: tuple(value) for key, value in _MODES.items()}


def modes_for(tool: ToolSpec | str) -> tuple[ToolMode, ...]:
    tool_id = tool if isinstance(tool, str) else tool.id
    return MODES_BY_TOOL.get(tool_id, ())


def resolve_tool(value: ToolSpec | FeatureSpec | str) -> ToolSpec:
    if isinstance(value, ToolSpec): return value
    if isinstance(value, FeatureSpec): return BY_ID[LEGACY_TO_CANONICAL[value.id]]
    text = str(value)
    if text in BY_ID: return BY_ID[text]
    if text in LEGACY_TO_CANONICAL: return BY_ID[LEGACY_TO_CANONICAL[text]]
    matches = [tool for tool in TOOLS if tool.name.lower() == text.lower()]
    if len(matches) == 1: return matches[0]
    raise KeyError(f"Unknown canonical tool: {value}")


def resolve_mode(tool: ToolSpec | str, value: ToolMode | FeatureSpec | str | None = None) -> ToolMode:
    target = resolve_tool(tool); modes = modes_for(target)
    if not modes: raise KeyError(f"{target.name} has no operations")
    if isinstance(value, ToolMode):
        if value.tool_id != target.id: raise KeyError(f"{value.name} does not belong to {target.name}")
        return value
    if isinstance(value, FeatureSpec): value = value.id
    if value is None or str(value).strip() == "": return modes[0]
    text = str(value).strip(); exact = [mode for mode in modes if mode.key == text]
    if exact: return exact[0]
    named = [mode for mode in modes if mode.name.lower() == text.lower()]
    if len(named) == 1: return named[0]
    raise KeyError(f"Unknown operation {value!r} for {target.name}")


def canonical_for_legacy(feature_id: str) -> ToolSpec:
    return BY_ID[LEGACY_TO_CANONICAL[feature_id]]


def legacy_aliases(tool: ToolSpec | str) -> tuple[FeatureSpec, ...]:
    return tuple(mode.legacy for mode in modes_for(tool) if mode.legacy is not None)


def all_legacy_ids() -> tuple[str, ...]: return tuple(LEGACY_TO_CANONICAL)


def registry_health() -> dict[str, int]:
    return {
        "canonical_tools": len(TOOLS),
        "legacy_feature_ids": len(LEGACY_SPECS),
        "legacy_aliases_mapped": len(LEGACY_TO_CANONICAL),
        "unmapped_legacy_ids": len(LEGACY_SPECS) - len(LEGACY_TO_CANONICAL),
    }
