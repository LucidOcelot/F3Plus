from __future__ import annotations

"""Installed-data enchantment possibilities for trades and loot."""

from typing import Any

from .minecraft_simulators import MinecraftJarData


def pretty_enchantment(value: str) -> str:
    return str(value).removeprefix("minecraft:").replace("_", " ").title()


def rarity_from_weight(weight: Any) -> str:
    try: value = int(weight)
    except (TypeError, ValueError): return "Unknown"
    if value >= 10: return "Common"
    if value >= 5: return "Uncommon"
    if value >= 2: return "Rare"
    if value >= 1: return "Very Rare"
    return "Unknown"


def _tag_rows(data: MinecraftJarData) -> dict[str, list[Any]]:
    raw = data.json_namespace(("data/minecraft/tags/enchantment/", "data/minecraft/tags/enchantments/")); rows = {}
    for key, value in raw.items():
        if isinstance(value, dict) and isinstance(value.get("values"), list): rows[key] = list(value["values"])
    return rows


def _tag_entry_id(value: Any) -> str:
    if isinstance(value, dict): value = value.get("id", value.get("value", ""))
    return str(value or "")


def resolve_tag(data: MinecraftJarData, tag_id: str) -> set[str]:
    tags = _tag_rows(data); wanted = str(tag_id).removeprefix("#")
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
    visit(wanted); return out


def _definition_rows(data: MinecraftJarData, ids: set[str] | None = None) -> list[dict[str, Any]]:
    definitions = data.enchantments(); rows = []
    for enchant_id, definition in sorted(definitions.items()):
        if ids is not None and enchant_id not in ids: continue
        definition = definition if isinstance(definition, dict) else {}; weight = definition.get("weight", 1)
        rows.append({"id": enchant_id, "name": pretty_enchantment(enchant_id), "weight": weight, "rarity": rarity_from_weight(weight), "max_level": definition.get("max_level", 1), "treasure_only": bool(definition.get("treasure_only", False))})
    return rows


def librarian_enchantments(data: MinecraftJarData) -> list[dict[str, Any]]:
    ids = resolve_tag(data, "minecraft:tradeable")
    return _definition_rows(data, ids if ids else None)


def _function_name(function: Any) -> str:
    if not isinstance(function, dict): return ""
    return str(function.get("function", function.get("type", ""))).removeprefix("minecraft:")


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
            token = str(key); out.add(token if ":" in token else "minecraft:" + token)
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
    """Return enchantments reachable from every enchanted-book production path.

    Vanilla tables can contain an enchanted_book directly or contain a normal book and
    turn it into an enchanted book with enchant_randomly/enchant_with_levels. Table,
    pool, entry, and nested-table functions are all considered.
    """
    tables = data.loot_tables(); start = str(table_id); all_defs = set(data.enchantments())
    found: set[str] = set(); saw_book = False; saw_unrestricted_random = False; visited: set[tuple[str, tuple[str, ...]]] = set()

    def examine(functions: list[Any]) -> tuple[bool, set[str], set[str]]:
        nonlocal saw_unrestricted_random
        random_enchant = False; restricted: set[str] = set(); explicit: set[str] = set()
        for fn in functions:
            if not isinstance(fn, dict): continue
            name = _function_name(fn)
            if name in {"enchant_randomly", "enchant_with_levels"}:
                random_enchant = True; options = _function_options(fn, data)
                if options: restricted.update(options)
                else: saw_unrestricted_random = True
            if name in {"set_enchantments", "set_components"}: explicit.update(_explicit_enchantments(fn))
        return random_enchant, restricted, explicit

    def walk_table(key: str, inherited_functions: list[Any] | None = None):
        inherited_functions = list(inherited_functions or [])
        signature = (key, tuple(_function_name(fn) for fn in inherited_functions if isinstance(fn, dict)))
        if signature in visited: return
        visited.add(signature); table = tables.get(key)
        if not isinstance(table, dict): return
        table_functions = inherited_functions + (list(table.get("functions", [])) if isinstance(table.get("functions"), list) else [])
        for pool in table.get("pools", []) if isinstance(table.get("pools"), list) else []:
            if not isinstance(pool, dict): continue
            pool_functions = table_functions + (list(pool.get("functions", [])) if isinstance(pool.get("functions"), list) else [])
            for entry in pool.get("entries", []) if isinstance(pool.get("entries"), list) else []: walk_entry(entry, pool_functions)

    def walk_entry(entry: Any, inherited_functions: list[Any]):
        nonlocal saw_book
        if not isinstance(entry, dict): return
        functions = inherited_functions + (list(entry.get("functions", [])) if isinstance(entry.get("functions"), list) else [])
        kind = str(entry.get("type", "")).removeprefix("minecraft:")
        if kind == "loot_table":
            target = entry.get("value", entry.get("name"))
            if isinstance(target, dict): target = target.get("id", "")
            if isinstance(target, str) and target: walk_table(target if ":" in target else "minecraft:" + target, functions)
        for child_key in ("children", "entries"):
            children = entry.get(child_key)
            if isinstance(children, list):
                for child in children: walk_entry(child, functions)
        name = str(entry.get("name", entry.get("item", "")))
        random_enchant, restricted, explicit = examine(functions)
        direct_enchanted = name in {"minecraft:enchanted_book", "enchanted_book"}
        enchanted_plain_book = name in {"minecraft:book", "book"} and (random_enchant or bool(explicit))
        if not direct_enchanted and not enchanted_plain_book: return
        saw_book = True; found.update(restricted); found.update(explicit)

    walk_table(start)
    if not saw_book: return []
    ids = (found | all_defs) if saw_unrestricted_random else found
    if not ids: ids = all_defs
    return _definition_rows(data, ids)


def grouped_summary(rows: list[dict[str, Any]], limit_per_group: int = 18) -> str:
    if not rows: return "No enchanted-book enchantment set was found in the active data source."
    groups: dict[str, list[str]] = {"Common": [], "Uncommon": [], "Rare": [], "Very Rare": [], "Unknown": []}
    for row in rows:
        name = row["name"]; level = row.get("max_level", 1); label = f"{name} (max {level})" if int(level or 1) > 1 else name
        groups.setdefault(row["rarity"], []).append(label)
    lines = ["Rarity uses vanilla enchantment weight; exact table/trade odds can differ."]
    for rarity in ("Common", "Uncommon", "Rare", "Very Rare", "Unknown"):
        names = groups.get(rarity, [])
        if not names: continue
        shown = names[:limit_per_group]; suffix = f" +{len(names)-len(shown)} more" if len(names) > len(shown) else ""
        lines.append(f"{rarity}: {', '.join(shown)}{suffix}")
    return "\n".join(lines)
