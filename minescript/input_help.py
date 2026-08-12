from __future__ import annotations

"""Qt-free labels, hints, and tooltip text for configurable inputs."""

from html import escape

from .field_semantics import field_help


_PARAMETER_LABELS: dict[tuple[str, str], str] = {
    ("Mending Grinder", "attack"): "Attack every",
    ("Mending Grinder", "rotate"): "Switch item every",
    ("Mending Grinder", "slots"): "Mending slots",
    ("Crossbow Volley", "slots"): "Crossbow slots",
    ("Crossbow Volley", "charge"): "Charge for",
    ("Crossbow Volley", "swap"): "After switching, wait",
    ("Tool Rotation", "slots"): "Tool slots",
    ("Tool Rotation", "interval"): "Switch tool every",
    ("Hotbar Workflow", "delay"): "Switch every",
    ("Food Manager", "interval"): "Eat every",
    ("Food Manager", "duration"): "Hold use for",
    ("Offhand Workflow", "interval"): "Swap every",
    ("Custom Periodic Action", "interval"): "Repeat every",
    ("Custom Periodic Action", "spacing"): "Click spacing",
    ("Livestock Breeder", "minutes"): "Repeat cycle every",
    ("Auto Fishing", "wait"): "Reel after",
    ("Auto Fishing", "recast"): "Recast after",
}


_PARAMETER_COPY: dict[tuple[str, str], tuple[str, str]] = {
    ("Mending Grinder", "attack"): (
        "Seconds between attack clicks.",
        "How often F3+ clicks attack while the grinder runs. Lower values attack faster. The routine clamps this to at least 0.05 seconds.",
    ),
    ("Mending Grinder", "rotate"): (
        "Seconds before switching hotbar slots.",
        "How long each selected hotbar slot stays active before F3+ switches to the next slot. Use this to distribute collected Mending XP among several tools.",
    ),
    ("Mending Grinder", "slots"): (
        "Hotbar slots that should receive Mending XP.",
        "Enter hotbar slot numbers 1 through 9 separated by commas, for example 1,2,3,5. Slots are cycled in the order entered; invalid entries are ignored.",
    ),
    ("Crossbow Volley", "slots"): (
        "Hotbar slots containing loaded crossbows.",
        "Enter crossbow hotbar slots 1 through 9 separated by commas. F3+ cycles through these slots in order.",
    ),
    ("Crossbow Volley", "charge"): (
        "Seconds allowed for each crossbow to charge.",
        "Time F3+ holds use before firing each crossbow. Increase this if a crossbow is released before it finishes charging.",
    ),
    ("Crossbow Volley", "swap"): (
        "Delay after changing to the next crossbow.",
        "Seconds F3+ waits after selecting the next configured hotbar slot before beginning the next charge.",
    ),
    ("Tool Rotation", "slots"): (
        "Hotbar slots included in the rotation.",
        "Enter slot numbers 1 through 9 separated by commas. F3+ rotates through them in the order entered.",
    ),
    ("Tool Rotation", "interval"): (
        "Seconds each tool remains selected.",
        "Time before F3+ switches from the current configured tool slot to the next one.",
    ),
    ("Hotbar Workflow", "slots"): (
        "Hotbar slots visited by the workflow.",
        "Enter slot numbers 1 through 9 separated by commas. The workflow visits them in the order entered.",
    ),
    ("Hotbar Workflow", "delay"): (
        "Seconds between hotbar changes.",
        "Pause after selecting one configured slot before moving to the next slot.",
    ),
    ("Food Manager", "slot"): (
        "Hotbar slot containing food.",
        "Choose the hotbar slot from 1 through 9 that contains the food F3+ should select before eating.",
    ),
    ("Food Manager", "interval"): (
        "Seconds between eating attempts.",
        "Time from one eating attempt to the next. This routine uses the timer; it does not read the hunger bar.",
    ),
    ("Food Manager", "duration"): (
        "Seconds to hold the use button while eating.",
        "How long F3+ holds use after selecting the food slot. Increase this if the item is released before eating completes.",
    ),
    ("Offhand Workflow", "interval"): (
        "Seconds between offhand swaps.",
        "Time F3+ waits between presses of the configured swap key.",
    ),
    ("Custom Periodic Action", "interval"): (
        "Seconds between action cycles.",
        "Time from the start of one configured interaction cycle to the start of the next cycle.",
    ),
    ("Custom Periodic Action", "actions"): (
        "Number of clicks in each cycle.",
        "How many mouse actions F3+ performs whenever one periodic cycle begins.",
    ),
    ("Custom Periodic Action", "spacing"): (
        "Seconds between clicks inside one cycle.",
        "Delay between individual mouse actions when a cycle contains more than one action.",
    ),
    ("Livestock Breeder", "minutes"): (
        "Minutes between breeding/growth interaction cycles.",
        "Time F3+ waits before repeating the configured livestock interaction cycle. The default matches the normal 20-minute adult breeding cooldown/growth interval.",
    ),
    ("Auto Fishing", "wait"): (
        "Seconds to wait before reeling in.",
        "Delay between casting and the reel action used by this timer-based fishing routine.",
    ),
    ("Auto Fishing", "recast"): (
        "Seconds to wait before casting again.",
        "Pause after the reel action before F3+ sends the next cast.",
    ),
}


def parameter_label(title: str, key: str, label: str) -> str:
    """Return the player-facing label for a configurable field."""
    return _PARAMETER_LABELS.get((str(title), str(key)), str(label))


def _generic_hint(key: str, label: str) -> str:
    low = f"{key} {label}".lower()
    if "slots" in low: return "Hotbar slots 1–9, separated by commas."
    if "interval" in low: return "Time between repetitions."
    if "delay" in low or "wait" in low: return "Time to wait before the next action."
    if "duration" in low: return "How long the action remains active."
    if "spacing" in low: return "Distance or time between repeated elements."
    if "rows" in low: return "Number of rows to process."
    if "steps" in low: return "Number of steps to process."
    if "branches" in low: return "Number of branches to process."
    if "click" in low or "swings" in low or "actions" in low: return "Number of actions in each cycle."
    if "radius" in low: return "Distance from the selected center."
    if label.strip().lower().endswith(" x"): return "Minecraft X coordinate."
    if label.strip().lower().endswith(" y"): return "Minecraft Y coordinate."
    if label.strip().lower().endswith(" z"): return "Minecraft Z coordinate."
    return ""


def _requirement(default, kind: str) -> str:
    if kind == "choice" and isinstance(default, (list, tuple)):
        return "Choices: " + ", ".join(str(value) for value in default[:8]) + "."
    if kind == "bool": return f"Default: {'enabled' if bool(default) else 'disabled'}."
    if kind == "int": return f"Enter a whole number. Default: {default}."
    if kind == "float": return f"Enter a number. Default: {default}."
    if str(default).strip(): return f"Default: {default}."
    return ""


def parameter_copy(title: str, key: str, label: str, default, kind: str) -> tuple[str, str]:
    """Return a short visible hint and a more detailed tooltip for one field."""
    specific = _PARAMETER_COPY.get((str(title), str(key)))
    if specific:
        hint, tooltip = specific
    else:
        display = parameter_label(title, key, label)
        hint = _generic_hint(str(key), display)
        tooltip = field_help(str(key), display).strip()
    requirement = _requirement(default, kind)
    if requirement and requirement.lower() not in tooltip.lower():
        tooltip = f"{tooltip} {requirement}".strip()
    if hint.strip() == tooltip.strip():
        hint = ""
    return hint, tooltip


def wrapped_tooltip(text: str, width: int = 360) -> str:
    """Return wrapped Qt-compatible rich text without importing Qt."""
    plain = str(text).strip()
    if not plain:
        return ""
    return f"<qt><table width='{int(width)}'><tr><td>{escape(plain)}</td></tr></table></qt>"
