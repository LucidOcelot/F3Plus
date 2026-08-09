from __future__ import annotations

"""Conservative multiplayer-safe feature filtering.

Safe Mode is deliberately simple and auditable.  It disables automation and the
workbenches that expose hidden-world or predictive RNG information while leaving
ordinary calculators, brewing/dye references, villagers, and local settings usable.
"""

SAFE_MODE_SUMMARY = (
    "Safe Mode is a conservative filter for strict SMP servers. It disables "
    "automation/macros, world and seed analysis, structure/biome locators, "
    "world-seed recovery, slime/seed searches, and predictive RNG/loot/generation tools."
)

SAFE_MODE_DISCLAIMER = (
    "Safe Mode reduces the chance of accidentally using a disputed feature, but it "
    "cannot determine a server's rules. Check the rules for the SMP you are joining."
)


def restriction_reason(spec) -> str | None:
    """Return why a canonical or legacy feature is disabled, or None when allowed."""
    feature_id = str(getattr(spec, "id", ""))
    if feature_id == "simulation.mechanics":
        return None
    if feature_id.startswith("automation.") or getattr(spec, "top", "") == "Gameplay":
        return "Automation and macros are disabled because many strict SMPs prohibit scripted input."
    if feature_id.startswith("world.") or getattr(spec, "top", "") == "Seed Tools":
        return (
            "World/seed analysis is disabled because it can reveal information that is not normally "
            "available to a player in-game on a strict SMP."
        )
    if feature_id in {"simulation.rng", "simulation.loot", "simulation.generation"} or getattr(spec, "top", "") == "RNG Tools":
        return (
            "Predictive RNG, loot, and generation analysis are disabled because strict SMPs may "
            "treat external prediction as an unfair gameplay advantage."
        )
    return None


def allowed(spec, safe_mode: bool) -> bool:
    return not safe_mode or restriction_reason(spec) is None
