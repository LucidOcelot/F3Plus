from __future__ import annotations

from dataclasses import dataclass

from .tool_registry import BY_ID, LEGACY_TO_CANONICAL, TOOLS, ToolSpec, modes_for


NAV_SECTIONS = [
    ("Home", "home"),
    ("Automation", "automation"),
    ("Navigation", "navigation"),
    ("World Explorer", "seed"),
    ("Build & Technical", "building"),
    ("Simulation & RNG", "rng"),
    ("Villagers", "villager"),
    ("Utilities & Safety", "utilities"),
]


def display_name(spec: ToolSpec) -> str: return spec.name

def nav_section(spec: ToolSpec) -> str: return spec.workspace

def submenu_label(spec: ToolSpec) -> str: return spec.group

def workspace_group(spec: ToolSpec) -> str: return spec.group


def group_order(section: str, groups=()) -> list[str]:
    ordered = []
    for tool in TOOLS:
        if tool.workspace == section and tool.group not in ordered: ordered.append(tool.group)
    for group in groups:
        if group not in ordered: ordered.append(group)
    if section == "Home": return ["Favorites", "Recent", "Suggested"]
    return ordered


def _canonical_id(value: str) -> str | None:
    if value in BY_ID: return value
    return LEGACY_TO_CANONICAL.get(value)


def specs_for_section(section: str, favorites=(), recent=()):
    if section != "Home": return [tool for tool in TOOLS if tool.workspace == section]
    out: list[ToolSpec] = []; seen: set[str] = set()
    for raw in list(favorites) + list(recent):
        tool_id = _canonical_id(str(raw))
        if tool_id and tool_id not in seen:
            out.append(BY_ID[tool_id]); seen.add(tool_id)
    if out: return out
    # First-run Home stays compact but includes visually distinctive, high-value entry points.
    for wanted in (
        "navigation.coordinates", "world.structures", "world.ores", "build.planner",
        "simulation.rng", "villagers.explorer", "utilities.version",
    ):
        if wanted in BY_ID:
            out.append(BY_ID[wanted]); seen.add(wanted)
    return out


@dataclass(frozen=True)
class ToolGuide:
    title: str
    summary: str
    when: str
    how: str
    inputs: str
    output: str
    limitations: str
    tags: tuple[str, ...]


_WHEN = {
    "Automation": "Use this when the job involves repeated player input, guided automation, or a repeatable gameplay workflow. Link the intended Minecraft client first and keep Emergency Stop available.",
    "Navigation": "Use this for coordinates, routes, waypoints, and portals when you want related geometry and routing operations in one place instead of hopping between calculators.",
    "World Explorer": "Use this with a known seed or generated Java save when you want to inspect world-generation candidates, actual generated data, or larger area reports.",
    "Build & Technical": "Use this while planning a build, redstone system, storage/logistics job, farm, or technical Minecraft layout before committing resources in-game.",
    "Simulation & RNG": "Use this to model Minecraft mechanics or gameplay RNG. Player/gameplay RNG is kept separate from world-seed recovery.",
    "Villagers": "Use this for one end-to-end villager workflow: browse local-version trades, compare offers, inspect professions, and plan curing, breeding, workstations, or halls.",
    "Utilities & Safety": "Use this to manage F3+ itself: versions/data, profiles, controls, calibration, and automation safety policy.",
}

_OUTPUT = {
    "Automation": "The selected mode either starts a safety-bounded automation routine or returns the setup/plan needed to run it.",
    "Navigation": "Returns readable coordinates, distances, routes, waypoint operations, or portal-network results for the selected operation.",
    "World Explorer": "Returns structured world/seed results with source/exactness notes; generated-save tools distinguish observed data from placement candidates.",
    "Build & Technical": "Returns dimensions, counts, coordinates, timing, layout points, material requirements, or mechanic-specific planning values.",
    "Simulation & RNG": "Returns simulator results, sequences/recovery candidates, observed statistics, or data-driven mechanic output with its source clearly identified.",
    "Villagers": "Opens or returns the relevant trade/profession/planning view using installed-version data when available and a labeled fallback otherwise.",
    "Utilities & Safety": "Returns configuration/status information or performs the selected local control action.",
}

_LIMITS = {
    "Automation": "Automation is constrained by the active platform input backend, Minecraft focus state, configured safety limits, and server rules. Safe Mode remains a conservative filter rather than a permission guarantee.",
    "Navigation": "Coordinate math is exact for the entered values; portal outcomes still depend on the actual portal/world state where the selected operation models link competition.",
    "World Explorer": "The selected Minecraft version, active generation backend, and local-data version are reported separately. Placement candidates are not mislabeled as confirmed final generation.",
    "Build & Technical": "Planning tools calculate from the supplied dimensions and mechanic assumptions; they do not inspect a world unless the selected mode explicitly requests generated-world data.",
    "Simulation & RNG": "Each simulator reports whether it is using installed data, a supported exact model, or a labeled baseline/partial model. Gameplay RNG output is never presented as world-seed recovery.",
    "Villagers": "Trade definitions and artwork are loaded independently. Installed trade data is preferred; fallback planning data is visibly non-exact for the selected Minecraft version.",
    "Utilities & Safety": "Component availability and platform permissions can limit specific features without disabling unrelated local calculators and explorers.",
}


def make_guide(spec: ToolSpec, description=None, input_labels=None, output_keys=None, status="tool") -> ToolGuide:
    modes = modes_for(spec); mode_names = [mode.name for mode in modes]; preview = ", ".join(mode_names[:6])
    if len(mode_names) > 6: preview += f", and {len(mode_names) - 6} more"
    inputs = "Choose an operation first. F3+ then shows only the fields required by that operation. " + (f"Available operations include {preview}." if preview else "This workbench opens its dedicated interactive surface.")
    how = "1. Open the workbench. 2. Choose the operation you actually need. 3. Enter only the operation-specific values. 4. Run it and inspect the result/source notice. Historical favorites open the matching operation automatically."
    tags = (spec.workspace, spec.group, f"{len(modes)} modes" if modes else "interactive")
    return ToolGuide(title=spec.name, summary=spec.summary, when=_WHEN.get(spec.workspace, spec.summary), how=how, inputs=inputs, output=_OUTPUT.get(spec.workspace, "Returns the selected operation result."), limitations=spec.limitations or _LIMITS.get(spec.workspace, "Version and backend limits are shown with the result."), tags=tags)


def search_text(spec: ToolSpec, guide: ToolGuide) -> str:
    operations = " ".join(mode.name for mode in modes_for(spec))
    return " ".join((spec.id, spec.name, spec.workspace, spec.group, spec.summary, guide.when, guide.inputs, guide.output, operations)).lower()


def tool_art_key(spec: ToolSpec) -> str:
    if spec.id.startswith("automation."): return "automation"
    if spec.id.startswith("navigation."): return "route" if spec.id == "navigation.routes" else "map"
    if spec.id.startswith("world."):
        if spec.id == "world.spawners": return "spawner"
        if spec.id == "world.biomes": return "biome"
        if spec.id == "world.ores": return "ore"
        if spec.id == "world.structures": return "structure"
        if spec.id == "world.nether": return "portal"
        return "seed"
    if spec.id.startswith("build."):
        if spec.id == "build.redstone": return "redstone"
        if spec.id == "build.storage": return "storage"
        if spec.id == "build.farming": return "farm"
        return "building"
    if spec.id.startswith("simulation."):
        if spec.id == "simulation.loot": return "loot"
        if spec.id == "simulation.rng": return "enchant"
        if spec.id == "simulation.mechanics": return "brewing"
        return "rng"
    if spec.id.startswith("villagers."): return "villager"
    if spec.id == "utilities.safety": return "safety"
    return "utilities"
