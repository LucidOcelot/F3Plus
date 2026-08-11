from __future__ import annotations

"""Task-first navigation and concise workbench discovery text."""

from dataclasses import dataclass

from .tool_registry import BY_ID, LEGACY_TO_CANONICAL, TOOLS, ToolSpec, modes_for


NAV_SECTIONS = [
    ("Home", "home"),
    ("Play & Travel", "travel"),
    ("Explore Worlds", "world"),
    ("Plan & Build", "building"),
    ("Mechanics & Trading", "mechanics"),
    ("App & Safety", "utilities"),
]


_SECTION_BY_PREFIX = {
    "automation.": "Play & Travel",
    "navigation.": "Play & Travel",
    "world.": "Explore Worlds",
    "build.": "Plan & Build",
    "simulation.": "Mechanics & Trading",
    "villagers.": "Mechanics & Trading",
    "utilities.": "App & Safety",
}


_GROUP_BY_ID = {
    "automation.actions": "Repeat Actions",
    "automation.travel": "Travel Automation",
    "automation.mining": "Mining Automation",
    "automation.farming": "Farm Automation",
    "automation.construction": "Build Automation",
    "automation.sequences": "Macros",
    "automation.macro_studio": "Macros",
    "navigation.position": "Position & Coordinates",
    "navigation.coordinates": "Position & Coordinates",
    "navigation.routes": "Routes & Waypoints",
    "navigation.portals": "Portals",
    "world.seed_recovery": "Seed Tools",
    "world.slime": "Seed Tools",
    "world.structures": "Find Locations",
    "world.spawners": "Scan Generated Worlds",
    "world.biomes": "Find Locations",
    "world.area": "Scan Generated Worlds",
    "world.ores": "Scan Generated Worlds",
    "world.analysis": "Analyze Worlds",
    "world.nether": "Find Locations",
    "world.profiles": "Worlds & Saves",
    "build.planner": "Build Planning",
    "build.redstone": "Redstone & Timing",
    "build.storage": "Storage & Logistics",
    "build.farming": "Farms",
    "build.technical": "Technical Layouts",
    "build.resources": "Materials & Resources",
    "build.recipes": "Materials & Resources",
    "simulation.rng": "Enchanting & RNG",
    "simulation.loot": "Loot & Drops",
    "simulation.generation": "Generation Mechanics",
    "simulation.mechanics": "Game Mechanics",
    "villagers.explorer": "Villagers",
    "utilities.version": "Minecraft Data",
    "utilities.settings": "Settings & Controls",
    "utilities.safety": "Settings & Controls",
    "utilities.results": "History & Export",
    "utilities.diagnostics": "Diagnostics",
}


def display_name(spec: ToolSpec) -> str:
    return spec.name


def nav_section(spec: ToolSpec) -> str:
    for prefix, section in _SECTION_BY_PREFIX.items():
        if spec.id.startswith(prefix):
            return section
    return "App & Safety"


def workspace_group(spec: ToolSpec) -> str:
    return _GROUP_BY_ID.get(spec.id, spec.group)


def submenu_label(spec: ToolSpec) -> str:
    return workspace_group(spec)


def group_order(section: str, groups=()) -> list[str]:
    if section == "Home":
        return ["Favorites", "Recent", "Suggested"]
    ordered: list[str] = []
    for tool in TOOLS:
        if nav_section(tool) == section:
            group = workspace_group(tool)
            if group not in ordered:
                ordered.append(group)
    for group in groups:
        if group not in ordered:
            ordered.append(group)
    return ordered


def _canonical_id(value: str) -> str | None:
    if value in BY_ID:
        return value
    return LEGACY_TO_CANONICAL.get(value)


def specs_for_section(section: str, favorites=(), recent=()):
    if section != "Home":
        return [tool for tool in TOOLS if nav_section(tool) == section]

    out: list[ToolSpec] = []
    seen: set[str] = set()
    for raw in list(favorites) + list(recent):
        tool_id = _canonical_id(str(raw))
        if tool_id and tool_id not in seen:
            out.append(BY_ID[tool_id])
            seen.add(tool_id)

    if out:
        return out

    for wanted in (
        "navigation.coordinates",
        "navigation.portals",
        "world.structures",
        "world.ores",
        "build.planner",
        "build.recipes",
        "simulation.rng",
        "villagers.explorer",
    ):
        if wanted in BY_ID:
            out.append(BY_ID[wanted])
            seen.add(wanted)
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


def _operation_preview(spec: ToolSpec, limit: int = 8) -> str:
    names = [mode.name for mode in modes_for(spec)]
    if not names:
        return ""
    preview = ", ".join(names[:limit])
    if len(names) > limit:
        preview += f", +{len(names) - limit} more"
    return preview


def make_guide(spec: ToolSpec, description=None, input_labels=None, output_keys=None, status="tool") -> ToolGuide:
    """Return concise, workbench-specific discovery text.

    The shell still consumes the older ToolGuide shape, but the strings deliberately
    avoid generic product boilerplate. Detailed field meaning belongs on each input.
    """
    operations = _operation_preview(spec)
    summary = spec.summary.strip()
    inputs = f"Includes: {operations}." if operations else "Opens a dedicated interactive workspace."
    limitation = spec.limitations.strip()
    if "does not" in limitation.lower() or "never presented" in limitation.lower():
        limitation = ""
    return ToolGuide(
        title=spec.name,
        summary=summary,
        when=summary,
        how="",
        inputs=inputs,
        output="",
        limitations=limitation,
        tags=(nav_section(spec), workspace_group(spec)),
    )


def search_text(spec: ToolSpec, guide: ToolGuide) -> str:
    operations = " ".join(mode.name for mode in modes_for(spec))
    return " ".join((
        spec.id,
        spec.name,
        nav_section(spec),
        workspace_group(spec),
        spec.summary,
        operations,
    )).lower()


_ART_KEYS = {
    "automation.actions": "actions",
    "automation.travel": "travel",
    "automation.mining": "mining",
    "automation.farming": "farm",
    "automation.construction": "construction",
    "automation.sequences": "macro",
    "automation.macro_studio": "macro",
    "navigation.position": "position",
    "navigation.coordinates": "coordinates",
    "navigation.routes": "route",
    "navigation.portals": "portal",
    "world.seed_recovery": "seed_recovery",
    "world.slime": "slime",
    "world.structures": "structure",
    "world.spawners": "spawner",
    "world.biomes": "biome",
    "world.area": "local_area",
    "world.ores": "ore",
    "world.analysis": "world_analysis",
    "world.nether": "portal",
    "world.profiles": "profiles",
    "build.planner": "building",
    "build.redstone": "redstone",
    "build.storage": "storage",
    "build.farming": "farm",
    "build.technical": "technical",
    "build.resources": "resources",
    "build.recipes": "recipes",
    "simulation.rng": "enchant",
    "simulation.loot": "loot",
    "simulation.generation": "generation",
    "simulation.mechanics": "brewing",
    "villagers.explorer": "villager",
    "utilities.version": "version",
    "utilities.settings": "settings",
    "utilities.safety": "safety",
    "utilities.results": "history",
    "utilities.diagnostics": "diagnostics",
}


def tool_art_key(spec: ToolSpec) -> str:
    return _ART_KEYS.get(spec.id, "utilities")
