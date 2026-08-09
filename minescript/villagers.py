from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from functools import lru_cache
import json
import os
import re
import zipfile

LEVEL_NAMES = {1: "Novice", 2: "Apprentice", 3: "Journeyman", 4: "Expert", 5: "Master"}
PROFESSIONS = [
    "armorer", "butcher", "cartographer", "cleric", "farmer", "fisherman",
    "fletcher", "leatherworker", "librarian", "mason", "shepherd", "toolsmith", "weaponsmith",
]
BASELINE_SOURCE = "Bundled baseline reference"


@dataclass
class Trade:
    profession: str
    level: int
    name: str
    wants: str
    gives: str
    additional_wants: str | None = None
    max_uses: float | None = None
    xp: float | None = None
    source: str = "installed-version"
    raw_path: str = ""
    wants_id: str = ""
    wants_count: str = "1"
    additional_wants_id: str = ""
    additional_wants_count: str = "1"
    gives_id: str = ""
    gives_count: str = "1"
    details: str = ""

    def dict(self):
        data = asdict(self)
        data["level_name"] = LEVEL_NAMES.get(self.level, str(self.level))
        data["direction"] = trade_direction(self)
        data["key"] = trade_key(self)
        return data


def minecraft_roots() -> list[Path]:
    roots = []
    home = Path.home()
    appdata = os.getenv("APPDATA")
    if appdata:
        roots.append(Path(appdata) / ".minecraft")
    roots += [home / ".minecraft", home / "Library" / "Application Support" / "minecraft"]
    out = []
    for path in roots:
        try:
            if path.exists() and path not in out:
                out.append(path)
        except OSError:
            pass
    return out


def installed_versions() -> dict[str, Path]:
    out = {}
    for root in minecraft_roots():
        versions_dir = root / "versions"
        if not versions_dir.exists():
            continue
        try:
            folders = list(versions_dir.iterdir())
        except OSError:
            continue
        for folder in folders:
            if not folder.is_dir():
                continue
            jar = folder / (folder.name + ".jar")
            if jar.exists():
                out[folder.name] = jar
    return dict(sorted(out.items()))


def _count_text(obj) -> str:
    if obj is None:
        return "1"
    if isinstance(obj, (int, float)):
        return str(obj)
    if isinstance(obj, dict):
        if "value" in obj and isinstance(obj["value"], (int, float, str)):
            return str(obj["value"])
        if obj.get("type", "").endswith("constant"):
            return str(obj.get("value", obj.get("constant", 1)))
        lo = obj.get("min_inclusive", obj.get("min", obj.get("min_value")))
        hi = obj.get("max_inclusive", obj.get("max", obj.get("max_value")))
        if lo is not None or hi is not None:
            return f"{lo if lo is not None else '?'}-{hi if hi is not None else '?'}"
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def _clean_id(value) -> str:
    if isinstance(value, list):
        value = value[0] if value else ""
    if isinstance(value, dict):
        value = value.get("id", value.get("item", ""))
    return str(value or "").removeprefix("minecraft:")


def _detail_summary(obj) -> str:
    if not isinstance(obj, dict):
        return ""
    details = []
    components = obj.get("components")
    if isinstance(components, dict):
        for key, value in components.items():
            label = str(key).removeprefix("minecraft:").replace("_", " ")
            if any(token in label for token in ("enchant", "potion", "custom name", "instrument", "trim")):
                details.append(f"{label}: {json.dumps(value, separators=(',', ':'), ensure_ascii=False)}")
    for key in ("functions", "data", "tag"):
        if key in obj and not details:
            details.append(f"{key}: {json.dumps(obj[key], separators=(',', ':'), ensure_ascii=False)[:280]}")
    return "; ".join(details)


def _item_info(obj) -> tuple[str, str, str, str]:
    if not obj:
        return "", "", "1", ""
    if isinstance(obj, str):
        item_id = _clean_id(obj)
        return item_id, item_id, "1", ""
    if isinstance(obj, list):
        if not obj:
            return "", "", "1", ""
        return _item_info(obj[0])
    if isinstance(obj, dict):
        raw_id = obj.get("id", obj.get("item", obj.get("items", "?")))
        if isinstance(raw_id, list):
            ids = [_clean_id(value) for value in raw_id]
            item_id = ids[0] if ids else ""
            display_id = " | ".join(value for value in ids if value)
        else:
            item_id = _clean_id(raw_id)
            display_id = item_id
        count = _count_text(obj.get("count", 1))
        text = f"{count} {display_id}".strip()
        return text, item_id, count, _detail_summary(obj)
    text = str(obj)
    return text, _clean_id(text.split()[-1] if text else ""), "1", ""


def _parse_path(path: str):
    parts = path.split("/")
    try:
        index = parts.index("villager_trade")
        profession = parts[index + 1]
        level = int(parts[index + 2])
        name = Path(parts[-1]).stem
        return profession, level, name
    except Exception:
        return None


@lru_cache(maxsize=16)
def _load_trades_cached(path_text: str, mtime_ns: int, size: int) -> tuple[Trade, ...]:
    jar = Path(path_text)
    rows = []
    with zipfile.ZipFile(jar) as archive:
        names = [
            name for name in archive.namelist()
            if "/villager_trade/" in name and name.endswith(".json") and "/datapacks/trade_rebalance/" not in name
        ]
        if not names:
            names = [name for name in archive.namelist() if "/villager_trade/" in name and name.endswith(".json")]
        for path in names:
            info = _parse_path(path)
            if not info:
                continue
            profession, level, name = info
            if profession not in PROFESSIONS:
                continue
            try:
                data = json.loads(archive.read(path))
            except Exception:
                continue
            wants, wants_id, wants_count, wants_detail = _item_info(data.get("wants"))
            gives, gives_id, gives_count, gives_detail = _item_info(data.get("gives"))
            additional, additional_id, additional_count, additional_detail = _item_info(data.get("additional_wants"))
            details = "; ".join(value for value in (wants_detail, additional_detail, gives_detail) if value)
            rows.append(Trade(
                profession=profession,
                level=level,
                name=name.replace("_", " "),
                wants=wants,
                gives=gives,
                additional_wants=additional or None,
                max_uses=data.get("max_uses"),
                xp=data.get("xp"),
                raw_path=path,
                wants_id=wants_id,
                wants_count=wants_count,
                additional_wants_id=additional_id,
                additional_wants_count=additional_count,
                gives_id=gives_id,
                gives_count=gives_count,
                details=details,
            ))
    return tuple(sorted(rows, key=lambda trade: (trade.profession, trade.level, trade.name)))


def load_trades_from_jar(jar: Path) -> list[Trade]:
    stat = jar.stat()
    return list(_load_trades_cached(str(jar.resolve()), int(stat.st_mtime_ns), int(stat.st_size)))


def _normal(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "-")


def _is_unstable(value: str) -> bool:
    text = _normal(value)
    return bool(
        re.fullmatch(r"\d{2}w\d{2}[a-z]", text)
        or any(token in text for token in ("snapshot", "pre", "rc", "experimental"))
    )


def _version_key(value: str):
    text = _normal(value)
    # Release-style versions sort semantically; old weekly snapshots are deliberately
    # not allowed to masquerade as a giant release such as "23.18".
    release = re.fullmatch(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    if release:
        return (3, int(release.group(1)), int(release.group(2)), int(release.group(3) or 0), text)
    modern_snapshot = re.fullmatch(r"(\d+)\.(\d+)-snapshot-(\d+)", text)
    if modern_snapshot:
        return (2, int(modern_snapshot.group(1)), int(modern_snapshot.group(2)), int(modern_snapshot.group(3)), text)
    weekly = re.fullmatch(r"(\d{2})w(\d{2})([a-z])", text)
    if weekly:
        return (1, int(weekly.group(1)), int(weekly.group(2)), ord(weekly.group(3)) - 96, text)
    numbers = [int(x) for x in re.findall(r"\d+", text)[:3]]
    while len(numbers) < 3:
        numbers.append(0)
    return (0, *numbers, text)


def _stack(count: str | int, item: str) -> str:
    return f"{count} {item}"


def _baseline_trade(profession, level, name, wants_count, wants_id, gives_count, gives_id, *, additional=None, max_uses=12, xp=1, details=""):
    additional_text = None
    additional_id = ""
    additional_count = "1"
    if additional:
        additional_count, additional_id = additional
        additional_text = _stack(additional_count, additional_id)
    return Trade(
        profession=profession, level=level, name=name,
        wants=_stack(wants_count, wants_id), gives=_stack(gives_count, gives_id),
        additional_wants=additional_text, max_uses=max_uses, xp=xp,
        source="bundled-baseline", raw_path=f"baseline/{profession}/{level}/{name}",
        wants_id=wants_id, wants_count=str(wants_count),
        additional_wants_id=additional_id, additional_wants_count=str(additional_count),
        gives_id=gives_id, gives_count=str(gives_count), details=details,
    )


@lru_cache(maxsize=1)
def baseline_trades() -> tuple[Trade, ...]:
    """Useful vanilla planning reference when an installed JAR exposes no trade JSON.

    It is intentionally labeled baseline instead of pretending to be exact for the
    selected version. Exact data-driven trade JSON always wins when available.
    """
    b = _baseline_trade
    rows = [
        b("armorer",1,"coal for emerald",15,"coal",1,"emerald",max_uses=16), b("armorer",1,"iron boots",4,"emerald",1,"iron_boots"),
        b("armorer",2,"iron for emerald",4,"iron_ingot",1,"emerald",max_uses=12), b("armorer",3,"lava bucket for emerald",1,"lava_bucket",1,"emerald",max_uses=12), b("armorer",5,"diamond chestplate",19,"emerald",1,"diamond_chestplate",max_uses=3),
        b("butcher",1,"raw chicken for emerald",14,"chicken",1,"emerald",max_uses=16), b("butcher",2,"raw porkchop for emerald",7,"porkchop",1,"emerald",max_uses=16), b("butcher",3,"cooked porkchop",1,"emerald",5,"cooked_porkchop",max_uses=16),
        b("cartographer",1,"paper for emerald",24,"paper",1,"emerald",max_uses=16), b("cartographer",2,"glass panes for emerald",11,"glass_pane",1,"emerald",max_uses=12), b("cartographer",3,"explorer map",13,"emerald",1,"filled_map",additional=(1,"compass"),max_uses=12,details="Explorer map destination depends on the offer/version."),
        b("cleric",1,"rotten flesh for emerald",32,"rotten_flesh",1,"emerald",max_uses=16), b("cleric",2,"gold for emerald",3,"gold_ingot",1,"emerald",max_uses=12), b("cleric",4,"ender pearl",5,"emerald",1,"ender_pearl",max_uses=12), b("cleric",5,"bottle o enchanting",3,"emerald",1,"experience_bottle",max_uses=12),
        b("farmer",1,"wheat for emerald",20,"wheat",1,"emerald",max_uses=16), b("farmer",1,"bread",1,"emerald",6,"bread",max_uses=16), b("farmer",2,"pumpkin for emerald",6,"pumpkin",1,"emerald",max_uses=12), b("farmer",4,"cake",1,"emerald",1,"cake",max_uses=12), b("farmer",5,"golden carrots",3,"emerald",3,"golden_carrot",max_uses=12),
        b("fisherman",1,"string for emerald",20,"string",1,"emerald",max_uses=16), b("fisherman",1,"coal for emerald",15,"coal",1,"emerald",max_uses=16), b("fisherman",2,"cod for emerald",15,"cod",1,"emerald",max_uses=16), b("fisherman",3,"fishing rod",7,"emerald",1,"fishing_rod",max_uses=3,details="May carry enchantments depending on version/offer."),
        b("fletcher",1,"sticks for emerald",32,"stick",1,"emerald",max_uses=16), b("fletcher",1,"arrows",1,"emerald",16,"arrow",max_uses=12), b("fletcher",2,"flint for emerald",26,"flint",1,"emerald",max_uses=12), b("fletcher",4,"bow",2,"emerald",1,"bow",max_uses=3,details="May carry enchantments."), b("fletcher",5,"tipped arrows",2,"emerald",5,"tipped_arrow",max_uses=12,details="Potion effect varies by offer/version."),
        b("leatherworker",1,"leather for emerald",6,"leather",1,"emerald",max_uses=16), b("leatherworker",2,"leather leggings",3,"emerald",1,"leather_leggings",max_uses=12), b("leatherworker",5,"saddle",6,"emerald",1,"saddle",max_uses=12),
        b("librarian",1,"paper for emerald",24,"paper",1,"emerald",max_uses=16), b("librarian",1,"enchanted book",5,"emerald",1,"enchanted_book",additional=(1,"book"),max_uses=12,details="Random enchanted-book offer; emerald price and enchantment vary. Use exact installed trade data when available."), b("librarian",2,"books for emerald",4,"book",1,"emerald",max_uses=12), b("librarian",3,"ink sac for emerald",5,"ink_sac",1,"emerald",max_uses=12), b("librarian",4,"compass",4,"emerald",1,"compass",max_uses=12), b("librarian",5,"name tag",20,"emerald",1,"name_tag",max_uses=12),
        b("mason",1,"clay for emerald",10,"clay_ball",1,"emerald",max_uses=16), b("mason",2,"stone for emerald",20,"stone",1,"emerald",max_uses=16), b("mason",3,"granite",1,"emerald",4,"granite",max_uses=16), b("mason",5,"quartz block",1,"emerald",1,"quartz_block",max_uses=12),
        b("shepherd",1,"white wool for emerald",18,"white_wool",1,"emerald",max_uses=16), b("shepherd",1,"shears",2,"emerald",1,"shears",max_uses=12), b("shepherd",2,"colored wool",1,"emerald",1,"blue_wool",max_uses=16,details="Color varies by offer."), b("shepherd",5,"painting",2,"emerald",3,"painting",max_uses=12),
        b("toolsmith",1,"coal for emerald",15,"coal",1,"emerald",max_uses=16), b("toolsmith",1,"stone axe",1,"emerald",1,"stone_axe",max_uses=12), b("toolsmith",2,"iron for emerald",4,"iron_ingot",1,"emerald",max_uses=12), b("toolsmith",4,"diamond shovel",7,"emerald",1,"diamond_shovel",max_uses=3,details="May carry enchantments."), b("toolsmith",5,"diamond pickaxe",18,"emerald",1,"diamond_pickaxe",max_uses=3,details="May carry enchantments."),
        b("weaponsmith",1,"coal for emerald",15,"coal",1,"emerald",max_uses=16), b("weaponsmith",1,"iron axe",3,"emerald",1,"iron_axe",max_uses=12), b("weaponsmith",2,"iron for emerald",4,"iron_ingot",1,"emerald",max_uses=12), b("weaponsmith",4,"diamond axe",12,"emerald",1,"diamond_axe",max_uses=3,details="May carry enchantments."), b("weaponsmith",5,"diamond sword",17,"emerald",1,"diamond_sword",max_uses=3,details="May carry enchantments."),
    ]
    return tuple(sorted(rows, key=lambda trade: (trade.profession, trade.level, trade.name)))


def preferred_texture_version(selected_version: str | None = None) -> str | None:
    versions = installed_versions()
    if not versions:
        return None
    wanted = _normal(selected_version or "")
    exact = next((name for name in versions if _normal(name) == wanted), None)
    if exact:
        return exact
    stable = [name for name in versions if not _is_unstable(name)]
    pool = stable or list(versions)
    return max(pool, key=_version_key)


def load_for_version(version: str | None = None) -> tuple[list[Trade], str]:
    versions = installed_versions()
    if not versions:
        return list(baseline_trades()), BASELINE_SOURCE
    wanted = _normal(version or "")
    exact = next((name for name in versions if _normal(name) == wanted), None)
    if exact:
        try:
            rows = load_trades_from_jar(versions[exact])
        except (OSError, zipfile.BadZipFile):
            rows = []
        if rows:
            return rows, exact

    stable = [name for name in versions if not _is_unstable(name)]
    ordered = sorted(stable or list(versions), key=_version_key, reverse=True)
    for name in ordered:
        try:
            rows = load_trades_from_jar(versions[name])
        except (OSError, zipfile.BadZipFile):
            continue
        if rows:
            return rows, name

    # Older versions hard-code villager offers in Java instead of exposing the newer
    # data-driven JSON. A non-empty, explicitly labeled reference is more useful than
    # presenting a broken zero-row explorer or pretending an unrelated weekly snapshot
    # contains exact data.
    return list(baseline_trades()), BASELINE_SOURCE


def search(trades: list[Trade], text: str = "", profession=None, level=None) -> list[Trade]:
    query = text.strip().lower()
    out = []
    for trade in trades:
        if profession and trade.profession != profession.lower():
            continue
        if level and trade.level != int(level):
            continue
        haystack = " ".join([
            trade.name, trade.wants, trade.gives, trade.additional_wants or "",
            trade.profession, trade.details, LEVEL_NAMES.get(trade.level, ""),
        ]).lower()
        if query and query not in haystack:
            continue
        out.append(trade)
    return out


def trade_direction(trade: Trade) -> str:
    if trade.gives_id == "emerald":
        return "Villager buys from you"
    if trade.wants_id == "emerald" or trade.additional_wants_id == "emerald":
        return "Villager sells to you"
    return "Exchange"


def trade_key(trade: Trade) -> str:
    return "|".join([
        trade.profession, str(trade.level), trade.raw_path or trade.name,
        trade.wants, trade.additional_wants or "", trade.gives,
    ])


def grouped(trades: list[Trade]):
    out = {profession: {LEVEL_NAMES[level]: [] for level in range(1, 6)} for profession in PROFESSIONS}
    for trade in trades:
        out.setdefault(trade.profession, {LEVEL_NAMES[level]: [] for level in range(1, 6)})[
            LEVEL_NAMES.get(trade.level, str(trade.level))
        ].append(trade.dict())
    return out
