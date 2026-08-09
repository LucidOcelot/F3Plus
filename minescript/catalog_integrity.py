from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

ORIGINAL_FEATURE_COUNT = 457


@dataclass(frozen=True)
class ImplementationContract:
    kind: str
    engine: str
    exactness: str
    prerequisite: str = "none"
    limitation: str = ""


_EXTERNAL = {"Nether Bedrock Cracker", "Enchantment RNG Seed Cracker"}
_GENERATED_WORLD = {
    "Dungeon/Pig Spawner Locator", "Double Spawner Locator", "Triple Spawner Locator",
    "Quad Spawner Locator", "Spawner Cluster Ranking", "Stronghold Silverfish",
    "Trial Chamber Spawners", "Largest Ocean", "Largest Mountain Chain",
    "Largest Cave Region", "Flat Terrain Finder", "Valley Finder", "Mountain Peak Finder",
    "Terrain Base Finder", "Island Finder", "Peninsula Detector", "River Crossing Finder",
    "Lake Density", "Cliff Locator", "Ore Distribution", "Ore Exposure Estimate",
    "Cave Exposure Estimate", "Technical World Score", "Resource Score",
}
_CONTROL_NAMES = {
    "Capture Position", "Copy Sister Coordinates", "Save Sister Waypoint", "Current Position",
    "Continuous Capture", "Coordinate History", "Create Waypoint", "Rename Waypoint",
    "Delete Waypoint", "Waypoint Groups", "Minecraft Version", "Export Profiles",
    "Import Profiles", "Control Bindings", "Turn Calibration", "Movement Calibration",
    "Coordinate Capture Settings", "Backup Settings", "Emergency Stop", "Pause/Resume",
    "Release Held Inputs", "Focus Loss Stop", "Restore Hotbar", "Runtime Limit",
    "Delayed Start", "Action Counter", "Stuck Detection", "Recovery Attempts",
}


def contract_for(spec) -> ImplementationContract:
    name = spec.name
    if name in _EXTERNAL:
        return ImplementationContract(
            "external-tool", "pinned community integration", "upstream",
            "component available/cached",
            "F3+ reports the upstream support boundary and does not claim unsupported versions.",
        )
    if name in _GENERATED_WORLD:
        return ImplementationContract(
            "generated-world-analysis", "Anvil/NBT + generated block-state scanner", "observed-world",
            "generated Java world save",
            "The result describes generated chunks only; ungenerated terrain is not invented from biome/structure proxies.",
        )
    if spec.top == "Gameplay":
        return ImplementationContract(
            "automation", "MacroEngine + configurable BoundInput", "input-automation",
            "linked/focused Minecraft as required by platform backend",
            "Macros emit ordinary player inputs and cannot read hidden game state.",
        )
    if name in _CONTROL_NAMES or spec.top in {"Utilities", "Safety"}:
        return ImplementationContract(
            "control", "persistent F3+ settings/UI workflow", "stateful-control",
            "none", "A control is only considered implemented when its UI path changes or reports real application state.",
        )
    if spec.top == "RNG Tools":
        return ImplementationContract(
            "simulation", "Java LCG/probability model or version data", "modelled",
            "mechanic-specific observations/parameters where applicable",
            "Category simulations identify their model; they are not represented as exact modern loot-table emulation unless version data is actually parsed.",
        )
    if spec.top == "Seed Tools":
        return ImplementationContract(
            "seed-analysis", "Cubiomes/local deterministic math/generated-world scanner", "version-bounded",
            "known world seed or generated save, depending on tool",
            "Unsupported Cubiomes versions fail closed rather than silently substituting another generation version.",
        )
    if spec.top == "Villager Explorer":
        return ImplementationContract(
            "version-data", "installed Minecraft JAR villager_trade JSON", "installed-version",
            "compatible installed Minecraft version",
            "No synthetic trade table is substituted when the selected version data is unavailable.",
        )
    if spec.top == "Wizards" or name.endswith("Wizard") or name.endswith("Setup"):
        return ImplementationContract(
            "planner", "F3+ planning engine", "planning",
            "user dimensions/targets where applicable",
            "Planner output is a construction/workflow plan, not a claim that the game state was inspected.",
        )
    return ImplementationContract("calculator", "F3+ deterministic calculator", "deterministic")


def annotate(spec, data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data or {})
    out.setdefault("implementation", asdict(contract_for(spec)))
    return out


_GENERIC_SIGNATURES = (
    {"operation", "value", "secondary"},
    {"operation", "seed"},
    {"operation", "distance", "bearing"},
    {"operation", "origin", "radius", "nether_scale", "seed"},
    {"operation", "seed", "center_chunk", "radius", "structure_candidate_counts", "sampled_chunks"},
)


def generic_placeholder_reason(spec, data: dict[str, Any]) -> str | None:
    """Return why a result still looks like a renamed generic placeholder.

    Prerequisite/status/control results are legitimate; this check targets old fallbacks
    that returned the feature name with unrelated generic numbers.
    """
    if not isinstance(data, dict) or not data:
        return "empty/non-dictionary result"
    if data.get("requires_generated_world") or data.get("available") is False:
        return None
    contract = contract_for(spec)
    if contract.kind in {"control", "external-tool", "automation"}:
        return None
    keys = set(data) - {"implementation", "note", "limitations", "source", "backend"}
    for signature in _GENERIC_SIGNATURES:
        if keys <= signature and "operation" in keys:
            return f"generic placeholder signature: {sorted(keys)}"
    if keys == {"action"}:
        return "action-only descriptor has no observable implementation"
    return None
