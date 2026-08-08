from __future__ import annotations

"""Conservative multiplayer-safe feature filtering.

Safe Mode is deliberately simple and auditable. It does not claim that every
remaining feature is permitted by every server; it disables the broad classes
most likely to violate strict SMP rules: automation, hidden-world/seed analysis,
and predictive RNG tooling.
"""

from .catalog_ids import FeatureSpec

SAFE_MODE_SUMMARY = (
    "Safe Mode is a conservative filter for strict SMP servers. It disables "
    "automation/macros, world and seed analysis, structure/biome locators, "
    "world-seed recovery, slime/seed searches, and predictive RNG/simulation tools."
)

SAFE_MODE_DISCLAIMER = (
    "Safe Mode reduces the chance of accidentally using a disputed feature, but it "
    "cannot determine a server's rules. Check the rules for the SMP you are joining."
)


def restriction_reason(spec: FeatureSpec) -> str | None:
    """Return why a feature is disabled in Safe Mode, or None when allowed."""
    if spec.top == "Gameplay":
        return "Automation and macros are disabled because many strict SMPs prohibit scripted input."
    if spec.top == "Seed Tools":
        return (
            "World/seed analysis is disabled because it can reveal information that is not normally "
            "available to a player in-game on a strict SMP."
        )
    if spec.top == "RNG Tools":
        return (
            "Predictive RNG, loot simulation, and sequence analysis are disabled because strict SMPs "
            "may treat external prediction as an unfair gameplay advantage."
        )
    return None


def allowed(spec: FeatureSpec, safe_mode: bool) -> bool:
    return not safe_mode or restriction_reason(spec) is None
