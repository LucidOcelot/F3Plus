from __future__ import annotations

"""Small player-facing semantics shared by the 2.5 UI."""

from typing import Any

DEFAULT_SEED_TEXT = "F3Plus"
STAT_BREEDING_SPECIES = ("Horse", "Donkey")


def seed_value(value: Any) -> int:
    """Convert numeric/text seed input to the value used by Java-style seed tools.

    Blank input means ``F3Plus``. Numeric strings remain numeric; other text uses the
    signed Java ``String.hashCode`` value, matching the familiar Minecraft text-seed
    convention instead of exposing an arbitrary internal number in the UI.
    """
    text = str(value or "").strip() or DEFAULT_SEED_TEXT
    try:
        return int(text)
    except ValueError:
        result = 0
        for char in text:
            result = (31 * result + ord(char)) & 0xFFFFFFFF
        return result - 0x100000000 if result & 0x80000000 else result


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


def grouped_enchantment_text(rows: list[dict[str, Any]], *, include_levels: bool = True) -> str:
    groups = {"Common": [], "Uncommon": [], "Rare": [], "Very rare": []}
    for row in rows:
        name = str(row.get("name", row.get("id", "Unknown")))
        if include_levels:
            name += f" I–{row.get('max_level', 1)}" if int(row.get("max_level", 1) or 1) > 1 else " I"
        if row.get("treasure_only"):
            name += " (treasure)"
        groups.setdefault(str(row.get("rarity", "Very rare")), []).append(name)
    parts = []
    for rarity in ("Common", "Uncommon", "Rare", "Very rare"):
        values = groups.get(rarity) or []
        if values:
            parts.append(f"{rarity}: {', '.join(values)}")
    return "\n".join(parts)


def compact_note(text: Any, limit: int = 220) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    cut = value.rfind(" ", 0, limit - 1)
    if cut < 80:
        cut = limit - 1
    return value[:cut].rstrip(" ,;:") + "…"
