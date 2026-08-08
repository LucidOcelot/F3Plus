from __future__ import annotations
from dataclasses import dataclass
from .catalog_ids import FeatureSpec, SPECS, BY_ID


NAV_SECTIONS = [
    ("Home", "H"),
    ("Automation", "A"),
    ("Navigation", "N"),
    ("World & Seed", "W"),
    ("Structures & Biomes", "S"),
    ("Calculators", "C"),
    ("Building & Farming", "B"),
    ("RNG", "R"),
    ("Villagers", "V"),
    ("Guided Setups", "G"),
    ("Utilities", "U"),
    ("Safety", "!"),
]

# Display-only names. Internal catalog names and feature IDs remain stable.
DISPLAY_NAMES = {
    ("RNG Tools","RNG Recovery","Enchantment RNG Seed Cracker"): "Enchantment / Player RNG Seed Cracker",
    ("RNG Tools","RNG Recovery","Java LCG State Recovery - 2 nextInt"): "Java RNG State Recovery — 2 nextInt Outputs",
    ("RNG Tools","RNG Recovery","Java LCG State Recovery - nextLong"): "Java RNG State Recovery — nextLong Output",
    ("RNG Tools","RNG Recovery","Java LCG State Inspector"): "Recovered Java RNG State Inspector",
    ("Gameplay","Construction","Line"): "Straight-Line Builder",
    ("Gameplay","Construction","Rectangle"): "Rectangle Perimeter Builder",
    ("Gameplay","Construction","Filled Rectangle"): "Filled Rectangle Builder",
    ("Gameplay","Construction","Grid"): "Construction Grid Builder",
    ("Gameplay","Construction","Rows"): "Parallel Row Builder",
    ("Gameplay","Construction","Alternating Pattern"): "Alternating Row Builder",
    ("Gameplay","Construction","Perimeter"): "Perimeter Builder",
    ("Gameplay","Construction","Repeating Segment"): "Repeating Segment Builder",
    ("Navigation","Coordinates","Distance"): "3D Coordinate Distance",
    ("Navigation","Coordinates","Bearing"): "Coordinate Bearing",
    ("Navigation","Coordinates","Midpoint"): "Coordinate Midpoint",
    ("Navigation","Coordinates","Delta XYZ"): "Coordinate Delta XYZ",
    ("Navigation","Coordinates","Travel Time"): "Travel Time from Distance",
    ("Navigation","Coordinates","Chunk"): "Block-to-Chunk Converter",
    ("Navigation","Coordinates","Region"): "Block-to-Region Converter",
    ("Navigation","Coordinates","Grid"): "Coordinate Grid",
    ("Calculators","Build","Area"): "Build Area Calculator",
    ("Calculators","Build","Volume"): "Build Volume Calculator",
    ("Calculators","Build","Surface Area"): "Build Surface Area Calculator",
    ("Calculators","Build","Perimeter"): "Build Perimeter Calculator",
    ("Calculators","Build","Block Count"): "Build Block Count Calculator",
    ("Calculators","Build","Stacks"): "Stack Count Calculator",
    ("Calculators","Build","Shulkers"): "Shulker Box Requirement",
    ("Calculators","Build","Grid"): "Build Grid Coordinate Calculator",
    ("Calculators","Technical","Mob Cap"): "Mob Cap Reference Calculator",
    ("Calculators","Technical","Simulation Distance"): "Simulation Distance Area Calculator",
    ("Calculators","Technical","Render Distance"): "Render Distance Area Calculator",
    ("Utilities","Version / Backend","Minecraft Version"): "Minecraft Version Target",
    ("Safety","Controls","Pause/Resume"): "Pause / Resume Automation",
    ("Seed Tools","Slime","Slime Radius"): "Slime Chunks in Radius",
    ("Seed Tools","Slime","Adjacent Pair"): "Adjacent Slime Chunk Pair",
    ("Seed Tools","Slime","2x2 Cluster"): "2×2 Slime Chunk Cluster",
    ("Seed Tools","Slime","Triple Cluster"): "Triple Slime Chunk Cluster",
    ("Seed Tools","Slime","Quad Cluster"): "Quad Slime Chunk Cluster",
    ("Seed Tools","Slime","Slime Density"): "Slime Chunk Density",
    ("Navigation","Portal Helpers","Sister Portal"): "Ideal Sister Portal Coordinates",
    ("Navigation","Portal Helpers","Standard Link Calculator"): "Portal Exit Selection Calculator",
    ("Navigation","Portal Helpers","Portal Conflict Analysis"): "Competing Portal Link Analysis",
    ("Navigation","Portal Helpers","Optimal Portal Placement"): "Best Candidate Portal Placement",
    ("Navigation","Portal Helpers","Portal Network"): "Portal Link Network Summary",
    ("Navigation","Portal Helpers","Highway Planner"): "Nether Highway Distance Planner",
    ("Navigation","Portal Helpers","Portal Separation"): "Portal Exit Separation Check",
    ("Navigation","Portal Helpers","Portal Coverage"): "Portal Coverage Radius Calculator",
    ("Navigation","Portal Helpers","Multi-Portal Jump"): "Two-Portal Nether Shortcut",
    ("Seed Tools","Nether","Nether Biome Finder"): "Nether Biome Composition Scan",
    ("Seed Tools","Nether","Nether Structure Density"): "Nether Fortress + Bastion Candidate Density",
    ("Seed Tools","Nether","Asymmetric Portal Router"): "Asymmetric (One-Way) Portal Linking",
    ("Seed Tools","Nether","Vertical Isolation Analyzer"): "Portal Y-Level Isolation Check",
    ("Seed Tools","Nether","Bidirectional Link Matrix"): "Two-Way Portal Link Matrix",
    ("Seed Tools","Nether","Reliability Margin"): "Portal Link Reliability Margin",
    ("Seed Tools","Nether","Portal Graph"): "Nether Portal Link Graph",
    ("Seed Tools","Nether","Loop Detector"): "Portal Link Loop Detector",
    ("Seed Tools","Nether","Travel Compression"): "Nether Travel Compression",
    ("Seed Tools","Nether","Travel Compression"): "Nether Shortcut Compression Ratio",
    ("Seed Tools","Nether","Bedrock Pattern Helper"): "Nether Bedrock Recovery Helper",
    ("Seed Tools","Nether","Asymmetric Jump Designer"): "Asymmetric Portal Jump Layout",
    ("Seed Tools","Nether","Maximum Displacement"): "Maximum Portal Link Offset",
    ("Seed Tools","Nether","Repeating Network Generator"): "Repeated Asymmetric Portal Network",
    ("Seed Tools","Nether","Destination Gate Planner"): "Portal Destination Gate Plan",
    ("Seed Tools","Nether","Portal-State Simulator"): "Active/Inactive Portal Link Simulator",
    ("Seed Tools","Nether","Routing Table Generator"): "Portal Entry-to-Exit Routing Table",
    ("Seed Tools","Nether","Corridor Transport"): "Nether Corridor Travel Comparison",
    ("Seed Tools","Nether","Standard Route Comparison"): "Standard vs. Asymmetric Portal Route",
    ("Seed Tools","Nether","Multi-Destination Optimizer"): "Multi-Destination Portal Link Optimizer",
    ("Seed Tools","Nether","Portal Reliability Heatmap"): "Portal Link Reliability Heatmap",
    ("Seed Tools","Nether","Portal Radius Visualizer"): "Portal Search-Radius Visualizer",
    ("Seed Tools","Nether","Portal Cost Optimizer"): "Portal Network Travel-Cost Optimizer",
    ("Seed Tools","Structures","Structure Finder"): "Structure Candidate Search",
    ("Seed Tools","Structures","Compound Search"): "Multi-Structure Candidate Search",
    ("Seed Tools","Structures","Structure Density"): "Structure Candidate Density",
    ("Seed Tools","Structures","Structure Heatmap"): "Structure Candidate Heatmap",
    ("Seed Tools","Biomes","Current Biome"): "Biome at Coordinate",
    ("Seed Tools","Biomes","Nearest Biome"): "Nearest Biome Search",
    ("Seed Tools","Biomes","Largest Biome"): "Largest Biome Region Search",
    ("Seed Tools","Biomes","Lake Density"): "Local Lake Density",
    ("Seed Tools","Biomes","Biome Boundary"): "Biome Boundary Search",
    ("Seed Tools","Local Area","Structure Counts"): "Local Structure Counts",
    ("Seed Tools","Local Area","Slime Distribution"): "Local Slime Chunk Distribution",
    ("Seed Tools","Local Area","Technical Score"): "Local Technical Build Score",
    ("Calculators","Shapes","Circle"): "Circle Block Layout",
    ("Calculators","Shapes","Sphere"): "Sphere Block Layout",
    ("Calculators","Shapes","Cylinder"): "Cylinder Block Layout",
    ("Calculators","Shapes","Cone"): "Cone Block Layout",
    ("Calculators","Shapes","Torus"): "Torus Block Layout",
    ("Calculators","Shapes","Helix"): "Helix Block Layout",
    ("Calculators","Shapes","Double Helix"): "Double-Helix Block Layout",
    ("Calculators","Shapes","Hexagon"): "Hexagon Block Layout",
    ("Calculators","Shapes","Octagon"): "Octagon Block Layout",
    ("Calculators","Shapes","Ellipse"): "Ellipse Block Layout",
    ("Calculators","Shapes","Pyramid"): "Pyramid Block Layout",
    ("Calculators","Shapes","Diamond"): "Diamond Block Layout",
    ("Calculators","Shapes","Arch"): "Arch Block Layout",
    ("Calculators","Technical","Symmetry"): "Build Symmetry Calculator",
    ("Calculators","Speedrunning","Blind Travel"): "Blind Travel Coordinate Calculator",
    ("RNG Tools","Probability","RNG Timeline"): "Gameplay RNG Timeline",
    ("RNG Tools","Generation RNG","Decoration RNG"): "Decoration RNG Preview",
    ("RNG Tools","Generation RNG","Geode Generator"): "Geode Placement Simulator",
    ("Utilities","Controls","Control Bindings"): "Input & Hotkey Bindings",
    ("Utilities","Controls","Backup Settings"): "Back Up F3+ Settings",
    ("Safety","Controls","Runtime Limit"): "Automation Runtime Limit",
    ("Safety","Controls","Delayed Start"): "Automation Start Countdown",
    ("Safety","Controls","Action Counter"): "Automation Action Counter",
    ("Safety","Controls","Stuck Detection"): "Movement Stuck Detection",
    ("Safety","Controls","Recovery Attempts"): "Automatic Recovery Limit",
}

# Structure rows named only after the structure are much clearer as actions.
_STRUCTURE_NAMES = {
    "Village","Stronghold","Trial Chamber","Ancient City","Woodland Mansion","Ocean Monument",
    "Desert Pyramid","Jungle Temple","Swamp Hut","Igloo","Pillager Outpost","Ruined Portal",
    "Shipwreck","Ocean Ruin","Buried Treasure","Mineshaft","Nether Fortress","Bastion","End City",
}


def display_name(spec: FeatureSpec) -> str:
    mapped = DISPLAY_NAMES.get((spec.top,spec.submenu,spec.name))
    if mapped:return mapped
    if spec.top=="Seed Tools" and spec.submenu=="Structures" and spec.name in _STRUCTURE_NAMES:
        return f"{spec.name} Candidate Finder"
    return spec.name


def nav_section(spec: FeatureSpec) -> str:
    if spec.top=="Gameplay":return "Automation"
    if spec.top=="Navigation":return "Navigation"
    if spec.top=="Seed Tools":
        if spec.submenu in {"Structures","Spawners","Biomes"}:return "Structures & Biomes"
        return "World & Seed"
    if spec.top=="Calculators":
        if spec.submenu in {"Build","Shapes","Farm"}:return "Building & Farming"
        return "Calculators"
    if spec.top=="RNG Tools":return "RNG"
    if spec.top=="Villager Explorer":return "Villagers"
    if spec.top=="Wizards":return "Guided Setups"
    if spec.top=="Utilities":return "Utilities"
    if spec.top=="Safety":return "Safety"
    return spec.top


def submenu_label(spec: FeatureSpec) -> str:
    return {"Version / Backend":"Version & Components"}.get(spec.submenu,spec.submenu)


_STRUCTURE_BASIC = {
    "Structure Finder","Village","Stronghold","Trial Chamber","Ancient City","Woodland Mansion",
    "Ocean Monument","Desert Pyramid","Jungle Temple","Swamp Hut","Igloo","Pillager Outpost",
    "Ruined Portal","Shipwreck","Ocean Ruin","Buried Treasure","Mineshaft","Nether Fortress","Bastion","End City",
}
_STRUCTURE_ANALYSIS = {
    "Compound Search","Structure Chains","Isolated Structure Finder","Structure Cluster Finder",
    "Structure Density","Structure Heatmap","Structure Corridor","Multi-Target Locator","Portal-Optimized Structure Search",
}
_BIOME_FIND = {"Current Biome","Nearest Biome","Rare Biome Search","Biome Boundary","Two-Way Biome Intersection","Three-Way Biome Intersection","Four-Way Biome Intersection"}
_TECH_ALIGN = {"Chunk Alignment","Region Alignment","Cardinal Alignment","Build Rotation","Symmetry","Blueprint Coordinates","Chunk Loader Planner","Loaded Chunk Area","Simulation Distance","Render Distance","Chunk Loader Radius"}
_TECH_MOB = {"Mob Cap Calculator","Despawn Radius Planner","Spawn Sphere","Mob Spawn Area","Random Tick Area","Spawnproof Calculator","Farm Separation","Iron Farm Spacing","Villager Gossip Radius","Raid Distance","Mob Cap","Guardian Area","Fortress Bounding Box","Mob Switch Radius"}
_TECH_PLAN = {"Item Sorter Planner","Perimeter Planner","Branch Density Calculator","Tunnel Progress","Torch Planner"}
_BUILD_MATERIAL = {"Area","Volume","Surface Area","Perimeter","Block Count","Stacks","Shulkers","Double Chests","Foundation Planner"}
_BUILD_INFRA = {"Stair Calculator","Spiral Staircase Planner","Catenary Calculator","Roof Pitch","Wall Segments","Bridge Span","Grid","Lighting Grid","Pillar Spacing","Road Planner","Crop Layout","Gradient Ratio","Chunk Grid Builder","Circle Layer Export","Beacon Offset"}
_FARM_YIELD = {"Crop Yield","Tree Yield","Animal Breeding","Villager Breeding"}
_FARM_SYSTEMS = {"Furnace Array","Fuel Optimizer","Sugar Cane Layout","Bamboo Layout","Kelp Tower","Bee Apiary","Villager Hall Layout","Animal Pen","Crop Row Calculator"}
_FARM_TECH = {"Beacon Pyramid","Beacon Coverage","Slime Farm Optimizer","Fortress Farm Planner","Trial Chamber Planner"}
_TRADE_BROWSE = {"Trade Browser","Trade Search","Trade Comparison","Librarian Browser","Refresh Trades From Installed Version"}
_TRADE_PLAN = {"Emerald Calculator","Trade Cycle Calculator"}

WORKSPACE_GROUP_ORDER = {
    "Home": ["Favorites","Recent","Suggested"],
    "Automation": ["Hands-Free Actions","Travel & Mobility","Mining & Excavation","Farming & Stations","Equipment & Inventory","Construction","Sequences & Setup"],
    "Navigation": ["Live Position","Coordinate Math & Chunking","Waypoints","Routes & Surveys","Nether Portals"],
    "World & Seed": ["Seed Recovery","Seed Components","Slime Chunks","Nether Generation & Portals","Local Area Reports","World Evaluation"],
    "Structures & Biomes": ["Find Structures","Structure Relationships & Scoring","Generated Spawners","Find Biomes","Terrain & Biome Regions"],
    "Calculators": ["Coordinate & Travel Math","Redstone & Timing","Storage & Logistics","Alignment & Chunk Geometry","Mob & Farm Mechanics","Technical Planning","Speedrun Planning","Resource & Durability","End Travel"],
    "Building & Farming": ["Materials & Dimensions","Build Infrastructure","Shape Layouts","Yield & Breeding","Farm Systems","Technical Farm Planning"],
    "RNG": ["RNG Recovery","Enchanting","Drop Probability","General Probability","Loot Simulation","Generation Simulation"],
    "Villagers": ["Browse Trades","Trade Planning","Professions","Curing, Breeding & Halls"],
    "Guided Setups": ["Mining Setups","Farm Setups","Portal Setups","Building Setups"],
    "Utilities": ["Version & Data","Components","Input & Calibration","Profiles & Backups"],
    "Safety": ["Emergency Controls","Run Limits","Failure Handling"],
}


def workspace_group(spec: FeatureSpec) -> str:
    section=nav_section(spec); sub=spec.submenu; name=spec.name
    if section=="Automation":
        if sub in {"Continuous Action","Periodic Interaction","Fishing"}: return "Hands-Free Actions"
        return {"Travel":"Travel & Mobility","Mining":"Mining & Excavation","Farming":"Farming & Stations","Equipment":"Equipment & Inventory","Construction":"Construction","Automation":"Sequences & Setup"}.get(sub,submenu_label(spec))
    if section=="Navigation":
        return {"Position":"Live Position","Coordinates":"Coordinate Math & Chunking","Waypoints":"Waypoints","Routes":"Routes & Surveys","Portal Helpers":"Nether Portals"}.get(sub,submenu_label(spec))
    if section=="World & Seed":
        return {"World Seed Recovery":"Seed Recovery","Cubiomes":"Seed Components","Slime":"Slime Chunks","Nether":"Nether Generation & Portals","Local Area":"Local Area Reports","World Analysis":"World Evaluation"}.get(sub,submenu_label(spec))
    if section=="Structures & Biomes":
        if sub=="Structures": return "Find Structures" if name in _STRUCTURE_BASIC else "Structure Relationships & Scoring"
        if sub=="Spawners": return "Generated Spawners"
        if sub=="Biomes": return "Find Biomes" if name in _BIOME_FIND else "Terrain & Biome Regions"
    if section=="Calculators":
        if sub=="Coordinate": return "Coordinate & Travel Math"
        if sub=="Redstone": return "Redstone & Timing"
        if sub=="Storage": return "Storage & Logistics"
        if sub=="Technical":
            if name in _TECH_ALIGN:return "Alignment & Chunk Geometry"
            if name in _TECH_MOB:return "Mob & Farm Mechanics"
            return "Technical Planning"
        return {"Speedrunning":"Speedrun Planning","Resource Usage":"Resource & Durability","End":"End Travel"}.get(sub,submenu_label(spec))
    if section=="Building & Farming":
        if sub=="Build": return "Materials & Dimensions" if name in _BUILD_MATERIAL else "Build Infrastructure"
        if sub=="Shapes": return "Shape Layouts"
        if sub=="Farm":
            if name in _FARM_YIELD:return "Yield & Breeding"
            if name in _FARM_TECH:return "Technical Farm Planning"
            return "Farm Systems"
    if section=="RNG":
        return {"RNG Recovery":"RNG Recovery","Enchanting":"Enchanting","Drops":"Drop Probability","Probability":"General Probability","Loot":"Loot Simulation","Generation RNG":"Generation Simulation"}.get(sub,submenu_label(spec))
    if section=="Villagers":
        if sub=="Trades": return "Browse Trades" if name in _TRADE_BROWSE else "Trade Planning"
        if sub=="Professions":return "Professions"
        return "Curing, Breeding & Halls"
    if section=="Guided Setups": return {"Mining":"Mining Setups","Farming":"Farm Setups","Portals":"Portal Setups","Building":"Building Setups"}.get(sub,submenu_label(spec))
    if section=="Utilities":
        if sub=="Version / Backend": return "Components" if name in {"Cubiomes Setup & Status","Nether Bedrock Cracker Status"} else "Version & Data"
        if sub=="Controls": return "Profiles & Backups" if name=="Backup Settings" else "Input & Calibration"
        return "Profiles & Backups"
    if section=="Safety":
        if name in {"Emergency Stop","Pause/Resume","Release Held Inputs","Restore Hotbar"}:return "Emergency Controls"
        if name in {"Runtime Limit","Delayed Start","Action Counter"}:return "Run Limits"
        return "Failure Handling"
    return submenu_label(spec)


def group_order(section: str, groups: set[str] | list[str]) -> list[str]:
    groups=set(groups); ordered=[g for g in WORKSPACE_GROUP_ORDER.get(section,[]) if g in groups]
    return ordered+sorted(groups-set(ordered))


def tool_art_key(spec: FeatureSpec) -> str:
    """Choose an original F3+ pixel-art motif by tool function."""
    group=workspace_group(spec)
    if group in {"Find Biomes","Terrain & Biome Regions","Live Position","Routes & Surveys","Shape Layouts","Farm Systems","Yield & Breeding","Building Setups","Farm Setups"}:
        return "chorus_flower"
    if group in {"Seed Recovery","Slime Chunks","World Evaluation","RNG Recovery","General Probability","Drop Probability","Generation Simulation","Speedrun Planning","Recent"}:
        return "chorus_fruit"
    if group in {"Storage & Logistics","Browse Trades","Professions","Emergency Controls","Failure Handling","Equipment & Inventory","Hands-Free Actions"}:
        return "shulker"
    if group in {"Find Structures","Structure Relationships & Scoring","Generated Spawners","Seed Components","Nether Generation & Portals"}:
        return "shulker_seed"
    if nav_section(spec) in {"Calculators","Utilities"}:return "chorus_calc"
    return "chorus_flower"


def specs_for_section(section: str, favorites=(), recent=()):
    if section=="Home":
        seen=set(); out=[]
        for fid in list(favorites)+list(recent):
            if fid in BY_ID and fid not in seen:
                out.append(BY_ID[fid]); seen.add(fid)
        if out:
            return out
        # A useful first-launch home view without inventing a separate catalog.
        for wanted in ("Navigation","Calculators","Building & Farming","Villagers","Utilities","Safety"):
            spec=next((s for s in SPECS if nav_section(s)==wanted),None)
            if spec and spec.id not in seen:
                out.append(spec); seen.add(spec.id)
        return out
    return [s for s in SPECS if nav_section(s)==section]


@dataclass(frozen=True)
class ToolGuide:
    title: str
    summary: str
    when: str
    how: str
    inputs: str
    output: str
    limitations: str
    tags: tuple[str,...]


_USE_BY_GROUP = {
    "Hands-Free Actions":"Use this when one simple input or interaction needs to repeat while you watch another window or leave Minecraft unfocused. It is intended for tasks you would otherwise hold or click by hand.",
    "Travel & Mobility":"Use this for repeatable movement or vehicle travel. Link the correct client first and check the Camera indicator because turns and elytra/riptide actions may require focus.",
    "Mining & Excavation":"Use this to plan or automate repetitive excavation. Check tool durability, inventory capacity, and the stop hotkey before starting a long unattended run.",
    "Farming & Stations":"Use this for repetitive harvest, replant, growth, or station cycles where the same movement/interaction pattern is repeated.",
    "Equipment & Inventory":"Use this when an automation needs predictable hotbar/offhand/tool handling or a guard against resource/durability overrun.",
    "Construction":"Use this for repetitive placement paths. It controls movement/placement patterns; verify orientation and required blocks before starting.",
    "Sequences & Setup":"Use this to assemble, record, or calculate a more complex automation instead of relying on a single held action.",
    "Live Position":"Use this while Minecraft is open when you need F3+ to capture, announce, or transform the player's current coordinates.",
    "Coordinate Math & Chunking":"Use this when comparing coordinates, locating chunk/region boundaries, or translating a position into a travel direction without changing the world.",
    "Waypoints":"Use this to save, organize, rank, or route through locations you intend to revisit.",
    "Routes & Surveys":"Use this for multi-stop exploration, recorded trails, or route cleanup rather than a single destination calculation.",
    "Nether Portals":"Use this before building or relinking portals. These tools compare 8:1 coordinate scaling, candidate exits, portal separation, and routing conflicts.",
    "Seed Recovery":"Use this only when you deliberately want to recover a Java world seed from observed Nether bedrock. It is the sole F3+ world-seed recovery workflow.",
    "Seed Components":"Use this to verify the generation component or query supported known-seed generation directly.",
    "Slime Chunks":"Use this after entering a known world seed to locate or rank slime chunks for farms and chunk clusters.",
    "Nether Generation & Portals":"Use this for known-seed Nether structure searches or advanced portal-network geometry beyond the basic Navigation portal helpers.",
    "Local Area Reports":"Use this to summarize a bounded area around a seed/chunk center instead of inspecting one structure or biome at a time.",
    "World Evaluation":"Use this when comparing larger-scale technical suitability: spawn, resources, loading, build potential, or exploration value.",
    "Find Structures":"Use this when you know the world seed and want candidate coordinates for one structure type. Treat candidates as locations to verify, not guarantees of final terrain-valid generation.",
    "Structure Relationships & Scoring":"Use this after basic structure search when proximity, density, clustering, routing, or multi-target combinations matter more than one nearest location.",
    "Generated Spawners":"Use this with a generated Java world save when you need actual spawner/trial-spawner data that seed math alone cannot guarantee.",
    "Find Biomes":"Use this for direct biome lookup or nearby/intersection searches on versions supported by the active generation backend.",
    "Terrain & Biome Regions":"Use this to search for large or shaped terrain/biome regions such as islands, peaks, valleys, cliffs, oceans, or continuous areas.",
    "Coordinate & Travel Math":"Use this when you need exact coordinate geometry or travel time: distance, Minecraft yaw, midpoint, Nether scaling, snapping, or XYZ deltas.",
    "Redstone & Timing":"Use this while designing a circuit or transport line to convert ticks, estimate delays, or size throughput before building it.",
    "Storage & Logistics":"Use this before gathering or moving bulk items to determine stacks, shulkers, chests, compression, capacity, and trip counts.",
    "Alignment & Chunk Geometry":"Use this to align builds with chunks, regions, cardinal axes, loaders, or blueprint coordinates.",
    "Mob & Farm Mechanics":"Use this to reason about spawning/despawning/loading/separation radii and other geometry that affects technical farms.",
    "Technical Planning":"Use this for supporting technical layouts such as sorters, perimeters, branch mines, tunnels, and lighting plans.",
    "Speedrun Planning":"Use this for route/triangulation calculations where fast coordinate decisions matter. It does not automate a run.",
    "Resource & Durability":"Use this to estimate XP, Mending repair, anvil penalties, durability, fuel, food, rockets, torches, or other consumables before a session.",
    "End Travel":"Use this for End gateway/outer-island/end-city route planning.",
    "Materials & Dimensions":"Use this before a build to convert dimensions into area, volume, surface/perimeter, block counts, stacks, shulkers, and foundations.",
    "Build Infrastructure":"Use this for roads, stairs, bridges, roofs, grids, pillars, lighting, slopes, and other repeatable structural layout measurements.",
    "Shape Layouts":"Use this to generate block-coordinate outlines/layers for geometric Minecraft builds rather than drawing the shape by eye.",
    "Yield & Breeding":"Use this for rough production/population planning before scaling a crop, tree, animal, or villager system.",
    "Farm Systems":"Use this to size physical farm/support systems such as furnaces, rows, towers, apiaries, halls, pens, or fuel supply.",
    "Technical Farm Planning":"Use this for farm-specific technical placement/coverage calculations involving beacons, slime, fortresses, or trial chambers.",
    "Enchanting":"Use this to estimate or simulate enchanting costs/probabilities and XP requirements. Gameplay RNG here is separate from the world seed.",
    "Drop Probability":"Use this to model repeated independent drop rolls and expected/at-least-one outcomes.",
    "RNG Recovery":"Use this when you need to derive gameplay RNG state from observations instead of starting from a seed you already know. Keep it separate from world-seed recovery.",
    "General Probability":"Use this when you want odds across repeated attempts or a deterministic RNG-sequence preview without treating the RNG seed as a world seed.",
    "Loot Simulation":"Use this for planning/experimentation with loot and reward rolls. Treat results as simulations unless the selected mechanic/version is explicitly implemented exactly.",
    "Generation Simulation":"Use this for placement/RNG previews. These are not presented as a complete modern terrain generator.",
    "Browse Trades":"Use this to inspect the trade data loaded from an installed Minecraft version, search offers, compare trades, or focus on librarians.",
    "Trade Planning":"Use this before a trading session to estimate emerald cost or repeatable trade cycles.",
    "Professions":"Use this as a profession-specific trade reference for the locally loaded Minecraft version.",
    "Curing, Breeding & Halls":"Use this to plan villager curing, breeding food, workstations, and trading-hall capacity/layout.",
    "Mining Setups":"Use this when you want F3+ to turn mining measurements into a guided setup instead of entering every related calculator separately.",
    "Farm Setups":"Use this for a guided farm setup that combines the main measurements and prerequisites in one place.",
    "Portal Setups":"Use this to prepare a portal/highway/network plan before placing portals in the world.",
    "Building Setups":"Use this to assemble common build-material, lighting, or beacon measurements into one guided plan.",
    "Version & Data":"Use this to check the selected Minecraft version, installed versions, or locally available trade/version data.",
    "Components":"Use this when a seed/generation feature says a required component is unavailable or you want to verify its status.",
    "Input & Calibration":"Use this when automation input, camera turning, movement timing, or coordinate capture needs to be checked or calibrated.",
    "Profiles & Backups":"Use this before moving settings to another installation or before making larger configuration changes.",
    "Emergency Controls":"Use these controls immediately when automation needs to pause, stop, release input, or restore a known state.",
    "Run Limits":"Use these before unattended automation to bound start time, duration, or action count.",
    "Failure Handling":"Use these to decide how F3+ should react when focus is lost, movement stalls, or recovery fails.",
}

_OUTPUT_EXACT = {
    "Distance Calculator":"Returns both full 3D Euclidean distance and horizontal X/Z distance between the two points.",
    "Bearing Calculator":"Returns Minecraft yaw from the start X/Z point to the target X/Z point. In Minecraft convention, 0° faces south, -90° east, 90° west, and ±180° north.",
    "Midpoint Calculator":"Returns the X/Y/Z midpoint exactly halfway between the two entered positions.",
    "Travel Time Calculator":"Returns travel time in seconds from distance ÷ blocks-per-second speed.",
    "Nether Conversion Calculator":"Returns the converted X/Z position using the Overworld↔Nether 8:1 coordinate scale.",
    "Coordinate Snap":"Returns the nearest whole block coordinate and the center of the containing chunk.",
    "Delta XYZ Calculator":"Returns signed ΔX, ΔY, and ΔZ from the first point to the second.",
    "Tick Converter":"Returns game ticks converted to seconds, minutes, and hours using 20 game ticks per second.",
    "Hopper Timer":"Returns the estimated transfer/timer duration for the entered item count using one hopper transfer every 8 game ticks while unobstructed.",
    "Comparator Strength":"Returns comparator signal strength from container fullness using the entered item/slot values.",
    "Crafter Throughput":"Returns estimated items per hour from the entered cycle time and items per cycle.",
    "Storage Capacity":"Returns item count, full stacks, remainder, shulkers, and double chests required.",
    "Shulker Requirement":"Returns the number of shulker boxes needed for the item count and stack size.",
    "Chest Requirement":"Returns the number of double chests needed for the item count and stack size.",
    "Item Compression":"Returns compressed-item count and remainder using the supported compression ratio.",
    "Transport Trips":"Returns per-trip capacity and the number of inventory/shulker trips needed.",
    "Area":"Returns width × length and supporting build dimensions.",
    "Volume":"Returns width × length × height and supporting build dimensions.",
    "Surface Area":"Returns the total surface area of the rectangular dimensions.",
    "Perimeter":"Returns the rectangular perimeter for the entered width and length.",
    "Block Count":"Returns the rectangular volume as a raw block count plus supporting dimensions.",
    "Stacks":"Returns how the build block count fits into stacks/shulkers/chests.",
    "Shulkers":"Returns shulker-box storage required for the calculated build volume.",
    "Double Chests":"Returns double-chest storage required for the calculated build volume.",
    "Current Biome":"Returns the biome at the requested coordinate when the selected version/backend supports that lookup.",
    "Nearest Biome":"Returns the closest matching biome candidate within the requested search area/backend support.",
    "Nether Bedrock Cracker":"Opens/prepares the permitted Nether-bedrock world-seed recovery workflow; recovered output comes from the cracker itself.",
    "Trade Browser":"Opens the searchable trade table loaded from the selected/installed Minecraft version.",
    "Trade Search":"Returns trade definitions matching the entered search/profession filters.",
    "Emerald Calculator":"Returns the emerald cost estimate produced by the configured trade quantities.",
    "Macro Template":"Returns the reusable automation templates/actions that can be assembled into a custom sequence.",
    "Midpoint":"Returns the exact X/Y/Z midpoint between the two entered positions.",
    "Delta XYZ":"Returns signed ΔX, ΔY, and ΔZ from the start position to the target position.",
    "Travel Time":"Returns estimated travel time in seconds from distance and blocks-per-second speed.",
    "Axis Distance":"Returns absolute X, Y, and Z separation between the two positions.",
    "OW/Nether Conversion":"Returns the X/Z coordinate converted through the standard 8:1 Overworld↔Nether scale.",
    "Coordinate Offset":"Returns the starting position plus the entered X/Y/Z offset.",
    "Sister Portal":"Returns the ideal sister X/Z coordinate in the opposite Overworld/Nether dimension plus the entered Y reference.",
    "Nearest Slime Chunk":"Returns the nearest slime-chunk coordinate found around the entered center chunk for the known world seed.",
    "Farm Location Ranking":"Returns slime-farm candidate chunks ranked by the local slime-chunk criteria used by the tool.",
    "Reliability Margin":"Returns portal-link distance margins for the generated portal-network candidates.",
    "Bidirectional Link Matrix":"Returns the calculated portal-to-portal link matrix for the candidate network.",
    "Loop Detector":"Returns portal-routing cycles detected in the generated portal graph.",
    "Farm Separation":"Returns horizontal separation between the entered technical-farm reference positions.",
    "Iron Farm Spacing":"Returns the spacing measurement used to compare the entered iron-farm reference positions.",
    "Villager Gossip Radius":"Returns the distance measurement used to plan the entered villager-gossip reference positions.",
    "Raid Distance":"Returns the distance measurement used to plan the entered raid/farm reference positions.",
    "Eye Throw Triangulation":"Returns the estimated X/Z intersection target of the two entered eye-throw rays.",
    "Stronghold Ring":"Returns the modern-ring planning count and inner/outer radius range for the selected ring index.",
}


def _category_when(spec: FeatureSpec) -> str:
    return _USE_BY_GROUP.get(workspace_group(spec), "Use this when the selected Minecraft task matches the calculation or control described above.")


def _how(spec: FeatureSpec, input_labels: list[str]) -> str:
    group=workspace_group(spec)
    if spec.top=="Gameplay":
        return "1. Link the intended Minecraft client. 2. Check Background, Minimized, and Camera status in the command deck. 3. Select Run. 4. If focus is required, read the warning and choose Proceed or Cancel. 5. Use Emergency Stop to release all held input immediately."
    if spec.name=="Bearing Calculator":
        return "Enter the start X/Z and target X/Z coordinates, then select Run. The result uses Minecraft yaw convention; vertical Y position does not affect bearing."
    if spec.name in {"Distance Calculator","Midpoint Calculator","Delta XYZ Calculator"}:
        return "Enter the start and target coordinates, then select Run. F3+ treats the first point as the origin and the second as the destination."
    if spec.name=="Enchantment RNG Seed Cracker":
        return "Select Run, read the version/support warning, then open the verified community cracker. Follow its enchantment-observation workflow to narrow the XP/player RNG seed. F3+ downloads the upstream v1.9 ZIP only on first use and verifies its pinned SHA-256 before launching it."
    if spec.name=="Java LCG State Recovery - 2 nextInt":
        return "Enter two consecutive unbounded java.util.Random.nextInt() outputs from the same RNG instance. Decimal and 0x-prefixed values are accepted. F3+ enumerates the missing 16 state bits and returns every 48-bit state consistent with both observations."
    if spec.name=="Java LCG State Recovery - nextLong":
        return "Enter one observed java.util.Random.nextLong() value. F3+ splits the Java long back into the two signed next(32) results, recovers the 48-bit state, and predicts the next nextInt() output."
    if spec.name=="Java LCG State Inspector":
        return "Paste a recovered 48-bit internal state. Use a positive step count to advance or a negative count to rewind, choose how many nextInt() values to preview, then run the tool."
    if group in {"Find Structures","Structure Relationships & Scoring","Find Biomes","Terrain & Biome Regions","Slime Chunks","World Evaluation","Local Area Reports"}:
        return "Set the correct Minecraft version and world seed first. Select Run / Configure, enter the search center/radius or world path requested, then verify any candidate location in-game before committing a build."
    if group=="Generated Spawners":
        return "Select Run / Configure and point F3+ at an already-generated Java world save. The tool reads chunk NBT/Anvil data and reports the matching spawner locations/results."
    if group in {"Browse Trades","Professions"}:
        return "Make sure the relevant Minecraft client version is installed locally, then run the tool. F3+ reads trade definitions from that installed version and opens or returns the matching offers."
    if not input_labels:
        return "Select Run. F3+ uses the current saved state or opens the dedicated control. Read the returned status/result before changing anything in Minecraft."
    short=", ".join(input_labels[:6])+("…" if len(input_labels)>6 else "")
    return f"Select Run / Configure, enter {short}, then run the tool. The labels describe the exact values used by this calculation; the Results view shows the computed output."


def _limitations(spec: FeatureSpec) -> str:
    if spec.top=="Gameplay":return "Background keyboard/mouse delivery depends on the operating system and Minecraft window state. Relative camera movement may require focus switching. Fully minimized Minecraft can ignore some events; F3+ warns before proceeding."
    if spec.top=="Seed Tools" and spec.submenu=="World Seed Recovery":return "This is F3+'s only world/structure-seed recovery workflow. It uses Nether bedrock observations; gameplay RNG tools remain separate."
    if spec.top=="Seed Tools" and spec.submenu in {"Biomes","Structures","Cubiomes","World Analysis","Local Area"}:return "Generation math is version-bounded. Cubiomes is used only where the bundled rules are valid; unsupported modern terrain is not presented as authoritative. Structure placement candidates may still fail final biome/terrain checks."
    if spec.top=="Seed Tools" and spec.submenu=="Spawners":return "Spawner results depend on generated world data. F3+ does not claim arbitrary spawners are recoverable from the world seed alone."
    if spec.top=="RNG Tools" and spec.submenu=="RNG Recovery":
        if spec.name=="Enchantment RNG Seed Cracker":return "This is gameplay/player RNG recovery, never world-seed recovery. The integrated upstream v1.9 release declares Minecraft Java support through 1.21.11; F3+ does not claim it is validated for 26.x. Server software or changed mechanics can break the observation method."
        return "These native recovery tools apply only when the observed RNG is compatible with the 48-bit java.util.Random LCG and the outputs are consecutive in the stated form. Modern Minecraft uses multiple RNG sources, so verify the mechanic before treating a recovered state as authoritative. This does not recover the world seed."
    if spec.top=="RNG Tools":return "These tools model gameplay/generation RNG or probability and do not recover the world seed. Simulations are only exact where the selected mechanic/version is explicitly implemented."
    if spec.top=="Villager Explorer":return "Trade definitions can change by version or experimental datapack. F3+ reports the installed data source it loaded; verify the active world/server rules if they differ."
    if spec.top=="Utilities":return "Availability can depend on the operating system, local Minecraft data, permissions, or one-time verified component setup."
    return "Results assume Java Edition mechanics and the Minecraft version selected in F3+. Recheck the version whenever the underlying mechanic changed between releases."


def _human_output_label(value: str) -> str:
    text=str(value).replace("_"," ").strip()
    acronyms={"xp":"XP","xyz":"XYZ","x":"X","y":"Y","z":"Z","rng":"RNG","id":"ID","url":"URL","3d":"3D","2d":"2D","ow":"Overworld"}
    return " ".join(acronyms.get(part.lower(),part.capitalize()) for part in text.split())


def _output_text(spec: FeatureSpec, output_labels: list[str], status: str) -> str:
    if status=="macro":return "Starts a managed automation routine. The status bar shows running/paused state and cycle count; stopping releases tracked keyboard and mouse input."
    exact=_OUTPUT_EXACT.get(spec.name)
    if exact:return exact
    if output_labels:
        labels=[_human_output_label(x) for x in output_labels[:10]]
        return "Returns "+", ".join(labels)+(" and additional details." if len(output_labels)>10 else ".")
    group=workspace_group(spec)
    if group=="Coordinate Math & Chunking":return "Returns the requested coordinate, chunk/region boundary, direction, or distance values in the Results view."
    if group=="Nether Portals":return "Returns converted portal coordinates, candidate exits, separation/routing information, or network geometry for the selected helper."
    if group in {"Find Structures","Structure Relationships & Scoring"}:return "Returns structure candidate coordinates and, where applicable, distance/density/cluster/routing scores for those candidates."
    if group in {"Find Biomes","Terrain & Biome Regions"}:return "Returns matching biome/terrain coordinates or region measurements from the supported generation backend."
    if group=="Generated Spawners":return "Returns actual generated-world spawner/trial-spawner locations or cluster rankings read from the save."
    if group in {"Mob & Farm Mechanics","Technical Planning","Alignment & Chunk Geometry"}:return "Returns the relevant radii, bounds, counts, spacing, capacity, or layout measurements for the selected technical mechanic."
    if group in {"Materials & Dimensions","Build Infrastructure","Shape Layouts"}:return "Returns block counts, coordinates/layers, dimensions, spacing, or support positions needed to lay out the selected build."
    if group in {"Yield & Breeding","Farm Systems","Technical Farm Planning"}:return "Returns the selected farm's planning estimate: yield/population, required resources, dimensions, spacing, throughput, or coverage."
    if group=="RNG Recovery":return "Returns the recovered 48-bit gameplay RNG state/candidates and prediction data, or opens the verified enchantment/player RNG cracker. World-seed state is not returned."
    if spec.top=="RNG Tools":return "Returns the requested probability, simulated outcome, RNG sequence, or planning estimate without altering Minecraft state."
    if spec.top=="Villager Explorer":return "Returns or opens the requested trade, profession, cost, curing/breeding, workstation, or hall-planning information."
    if spec.top=="Wizards":return "Returns a guided set of measurements/settings for the selected setup so you can verify the plan before building or automating it."
    if spec.top=="Safety":return "Applies or configures the selected automation safety control and reports its active state where applicable."
    return "Runs the selected control and reports its concrete result/status in F3+."


def make_guide(spec: FeatureSpec, description: str, input_labels: list[str], output_labels: list[str], status: str="ok") -> ToolGuide:
    title=display_name(spec)
    summary=description.strip().replace("F3+'s","F3+’s")
    inputs="No manual fields. This tool uses saved/current F3+ state or opens its own control." if not input_labels else "; ".join(input_labels)+"."
    raw_tags=(nav_section(spec),workspace_group(spec),"Automation" if status=="macro" else "Tool")
    tags=tuple(dict.fromkeys(raw_tags))
    return ToolGuide(title,summary,_category_when(spec),_how(spec,input_labels),inputs,_output_text(spec,output_labels,status),_limitations(spec),tags)


def search_text(spec: FeatureSpec, guide: ToolGuide) -> str:
    return " ".join([display_name(spec),spec.name,spec.top,spec.submenu,workspace_group(spec),guide.summary,guide.when,guide.inputs,guide.output]).lower()
