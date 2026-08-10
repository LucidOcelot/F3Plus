from __future__ import annotations

"""Qt-free launch ownership for canonical F3+ workbenches.

Every visible workbench must have exactly one launch owner.  Historical operations may
still select a mode inside that owner, but they never choose an unrelated generic form
because of how the user happened to reach the tool (Home, search, favorite, palette,
or menu).
"""

DEDICATED_LAUNCHERS: dict[str, str] = {
    "automation.macro_studio": "macro_studio",
    "world.profiles": "world_profiles",
    "build.recipes": "recipes",
    "simulation.rng": "rng_enchanting",
    "simulation.loot": "loot",
    "simulation.mechanics": "mechanics",
    "villagers.explorer": "villagers",
    "utilities.settings": "profiles_controls",
    "utilities.safety": "safety",
    "utilities.results": "result_history",
    "utilities.diagnostics": "diagnostics",
}


def launch_kind(tool_id: str) -> str:
    """Return the canonical owner used to launch a workbench."""
    return DEDICATED_LAUNCHERS.get(str(tool_id), "operation_explorer")


def has_launch_owner(tool) -> bool:
    """A workbench is launchable if it has a dedicated owner or at least one mode."""
    from .tool_registry import modes_for
    return launch_kind(tool.id) != "operation_explorer" or bool(modes_for(tool))
