from __future__ import annotations

"""Read enchantment possibilities from installed Minecraft data.

The UI uses this for librarian enchanted-book offers and loot tables that can return an
 enchanted book. Rarity is derived from the vanilla enchantment weight: 10 common,
5 uncommon, 2 rare, 1 very rare. Installed tags narrow the set when a table or the
librarian trade tag provides one.
"""

from functools import lru_cache
from typing import Any

from .minecraft_simulators import MinecraftJarData


def pretty_enchantment(value: str) -> str:
    return str(value).removeprefix("minecraft:").replace("_", " ").title()


def rarity_from_weight(weight: Any) -> str:
    try:
        value = int(weight)
    except (TypeError, ValueError):
        return "Unknown"
    if value >= 10: return "Common"
    if value >= 5: return "Uncommon"
    if value >= 2: return "Rare"
    if value >= 1: return "Very Rare"
    return "Unknown"


def _tag_rows(data: MinecraftJarData) -> dict[str, list[Any]]:
    raw = data.json_namespace(("data/minecraft/tags/enchantment/", "data/minecraft/tags/enchantments/"))
    rows: dict[str, list[Any]] = {}
    for key, value in raw.items():
        if isinstance(value, dict) and isinstance(value.get("values"), list):
            rows[key] = list(value["values"])
    return rows


def _tag_entry_id(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("id", value.get("value", ""))
    return str(value or "")


def resolve_tag(data: MinecraftJarData, tag_id: str) -> set[str]:
    tags = _tag_rows(data); wanted = str(tag_id)
    if wanted.startswith("#"): wanted = wanted[1:]
    if ":" not in wanted: wanted = "minecraft:" + wanted
    seen: set[str] = set(); out: set[str] = set()

    def visit(key: str):
        if key in seen: return
        seen.add(key)
        for raw in tags.get(key, []):
            token = _tag_entry_id(raw)
            if not token: continue
            if token.startswith("#"):
                nested = token[1:]
                if ":" not in nested: nested = "minecraft:" + nested
                visit(nested)
            else:
                if ":" not in token: token = "minecraft:" + token
                out.add(token)
    visit(wanted)
    return out


def _definition_rows(data: MinecraftJarData, ids: set[str] | None = None) -> list[dict[str, Any]]:
    definitions = data.enchantments(); rows = []
    for enchant_id, definition in sorted(definitions.items()):
        if ids is not None and enchant_id not in ids: continue
        definition = definition if isinstance(definition, dict) else {}
        weight = definition.get("weight", 1)
        rows.append({
            "id": enchant_id,
            "name": pretty_enchantment(enchant_id),
            "weight": weight,
            "rarity": rarity_from_weight(weight),
            "max_level": definition.get("max_level", 1),
            "treasure_only": bool(definition.get("treasure_only", False)),
        })
    return rows


def librarian_enchantments(data: MinecraftJarData) -> list[dict[str, Any]]:
    """Return enchantments permitted by the installed librarian trade tag when present."""
    ids = resolve_tag(data, "minecraft:tradeable")
    return _definition_rows(data, ids if ids else None)


def _function_options(function: dict[str, Any], data: MinecraftJarData) -> set[str]:
    for key in ("options", "enchantments"):
        raw = function.get(key)
        if isinstance(raw, str):
            if raw.startswith("#"): return resolve_tag(data, raw)
            return {raw if ":" in raw else "minecraft:" + raw}
        if isinstance(raw, list):
            out = set()
            for entry in raw:
                token = _tag_entry_id(entry)
                if token.startswith("#"): out.update(resolve_tag(data, token))
                elif token: out.add(token if ":" in token else "minecraft:" + token)
            if out: return out
    return set()


def _explicit_enchantments(function: dict[str, Any]) -> set[str]:
    out = set(); raw = function.get("enchantments")
    if isinstance(raw, dict):
        for key in raw:
            token = str(key)
            out.add(token if ":" in token else "minecraft:" + token)
    components = function.get("components")
    if isinstance(components, dict):
        stored = components.get("minecraft:stored_enchantments", components.get("stored_enchantments"))
        if isinstance(stored, dict):
            levels = stored.get("levels", stored)
            if isinstance(levels, dict):
                for key in levels:
                    token = str(key); out.add(token if ":" in token else "minecraft:" + token)
    return out


def loot_enchanted_book_enchantments(data: MinecraftJarData, table_id: str) -> list[dict[str, Any]]:
    """Find enchantments reachable by enchanted-book entries in a loot table tree."""
    tables = data.loot_tables(); start = str(table_id)
    all_defs = set(data.enchantments())
    found: set[str] = set(); saw_book = False; saw_unrestricted_random = False; visited: set[str] = set()

    def walk_table(key: str):
        nonlocal saw_book, saw_unrestricted_random
        if key in visited: return
        visited.add(key); table = tables.get(key)
        if not isinstance(table, dict): return
        inherited = list(table.get("functions", [])) if isinstance(table.get("functions"), list) else []
        for pool in table.get("pools", []) if isinstance(table.get("pools"), list) else []:
            if not isinstance(pool, dict): continue
            pool_functions = inherited + (list(pool.get("functions", [])) if isinstance(pool.get("functions"), list) else [])
            for entry in pool.get("entries", []) if isinstance(pool.get("entries"), list) else []:
                walk_entry(entry, pool_functions)

    def walk_entry(entry: Any, inherited_functions: list[Any]):
        nonlocal saw_book, saw_unrestricted_random
        if not isinstance(entry, dict): return
        kind = str(entry.get("type", "")); functions = inherited_functions + (list(entry.get("functions", [])) if isinstance(entry.get("functions"), list) else [])
        if kind.endswith("loot_table"):
            target = entry.get("value", entry.get("name"))
            if isinstance(target, str): walk_table(target if ":" in target else "minecraft:" + target)
        for child_key in ("children", "entries"):
            children = entry.get(child_key)
            if isinstance(children, list):
                for child in children: walk_entry(child, functions)
        name = str(entry.get("name", ""))
        if name not in {"minecraft:enchanted_book", "enchanted_book"}: return
        saw_book = True
        restricted = set(); explicit = set()
        for fn in functions:
            if not isinstance(fn, dict): continue
            fn_name = str(fn.get("function", fn.get("type", ""))).removeprefix("minecraft:")
            if fn_name in {"enchant_randomly", "enchant_with_levels"}:
                opts = _function_options(fn, data)
                if opts: restricted.update(opts)
                else: saw_unrestricted_random = True
            if fn_name in {"set_enchantments", "set_components"}: explicit.update(_explicit_enchantments(fn))
        found.update(restricted); found.update(explicit)

    walk_table(start)
    if not saw_book: return []
    ids = (found | all_defs) if saw_unrestricted_random else found
    if not ids:
        # An enchanted-book entry without a visible restriction is safest presented as
        # the installed enchantment set rather than silently showing no possibilities.
        ids = all_defs
    return _definition_rows(data, ids)


def grouped_summary(rows: list[dict[str, Any]], limit_per_group: int = 18) -> str:
    if not rows: return "No enchanted-book enchantment set was found in the active data source."
    groups: dict[str, list[str]] = {"Common": [], "Uncommon": [], "Rare": [], "Very Rare": [], "Unknown": []}
    for row in rows:
        name = row["name"]; level = row.get("max_level", 1)
        label = f"{name} (max {level})" if int(level or 1) > 1 else name
        groups.setdefault(row["rarity"], []).append(label)
    lines = []
    for rarity in ("Common", "Uncommon", "Rare", "Very Rare", "Unknown"):
        names = groups.get(rarity, [])
        if not names: continue
        shown = names[:limit_per_group]; suffix = f" +{len(names)-len(shown)} more" if len(names) > len(shown) else ""
        lines.append(f"{rarity}: {', '.join(shown)}{suffix}")
    return "\n".join(lines)
