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


@lru_cache(maxsize=8)
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
    """Load one version JAR, caching by file revision rather than only its path."""
    stat = jar.stat()
    return list(_load_trades_cached(str(jar.resolve()), int(stat.st_mtime_ns), int(stat.st_size)))


def _normal(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "-")


def _version_key(value: str):
    text = _normal(value)
    numbers = [int(x) for x in re.findall(r"\d+", text)[:4]]
    while len(numbers) < 4:
        numbers.append(0)
    unstable = 1 if any(token in text for token in ("snapshot", "pre", "rc", "experimental")) else 0
    return (*numbers, -unstable, text)


def load_for_version(version: str | None = None) -> tuple[list[Trade], str]:
    versions = installed_versions()
    if not versions:
        return [], "not-installed"
    wanted = _normal(version or "")
    for name, jar in versions.items():
        if _normal(name) == wanted:
            return load_trades_from_jar(jar), name
    stable = [
        name for name in versions
        if not any(token in name.lower() for token in ("snapshot", "pre", "rc", "experimental"))
    ]
    pool = stable or list(versions)
    pick = max(pool, key=_version_key)
    return load_trades_from_jar(versions[pick]), pick


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
            trade.profession, trade.details,
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
