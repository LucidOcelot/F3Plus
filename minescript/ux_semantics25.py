from __future__ import annotations

"""Small player-facing semantics shared by the 2.5 UI.

This module deliberately keeps presentation rules out of simulator/world-generation
engines: readable seed defaults, enchantment rarity labels, and the narrow list of
animals whose offspring stats are materially affected by breeding.
"""

import hashlib
from typing import Any

DEFAULT_SEED_TEXT = "F3Plus"
STAT_BREEDING_SPECIES = ("Horse", "Donkey", "Llama")


def seed_value(value: Any) -> int:
    """Convert an optional numeric/text seed to a deterministic signed 64-bit value.

    Minecraft accepts arbitrary text seeds by hashing them. F3+ mirrors the useful
    player-facing behavior without requiring a number: blank input is treated as the
    literal text ``F3Plus``.
    """
    text = str(value or "").strip() or DEFAULT_SEED_TEXT
    try:
        return int(text)
    except ValueError:
        raw = hashlib.sha256(text.encode("utf-8")).digest()[:8]
        unsigned = int.from_bytes(raw, "big", signed=False)
        return unsigned - (1 << 64) if unsigned >= (1 << 63) else unsigned


def rarity_from_weight(weight: Any) -> str:
    """Translate Mojang enchantment selection weights into readable rarity bands."""
    try:
        value = int(weight)
    except Exception:
        value = 1
    if value >= 10:
        return "Common"
    if value >= 5:
        return "Uncommon"
    if value >= 2:
        return "Rare"
    return "Very rare"


def enchantment_possibilities(enchantments: dict[str, dict], *, treasure: bool = True) -> list[dict[str, Any]]:
    rows = []
    for enchant_id, definition in sorted((enchantments or {}).items()):
        if not isinstance(definition, dict):
            continue
        if not treasure and definition.get("treasure_only"):
            continue
        weight = definition.get("weight", 1)
        rows.append({
            "id": enchant_id,
            "name": str(enchant_id).removeprefix("minecraft:").replace("_", " ").title(),
            "weight": int(weight) if str(weight).lstrip("-").isdigit() else weight,
            "rarity": rarity_from_weight(weight),
            "max_level": definition.get("max_level", 1),
            "treasure_only": bool(definition.get("treasure_only", False)),
        })
    return rows


def compact_note(text: Any, limit: int = 220) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    cut = value.rfind(" ", 0, limit - 1)
    if cut < 80:
        cut = limit - 1
    return value[:cut].rstrip(" ,;:") + "…"
