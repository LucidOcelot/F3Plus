from __future__ import annotations

import gzip
import io
from pathlib import Path
import struct
from typing import Any

from .villagers import minecraft_roots


class _NBT:
    def __init__(self, raw: bytes):
        self.f = io.BytesIO(raw)

    def read(self, n: int) -> bytes:
        data = self.f.read(n)
        if len(data) != n: raise EOFError("Unexpected end of NBT data")
        return data

    def u8(self): return self.read(1)[0]
    def i8(self): return struct.unpack(">b", self.read(1))[0]
    def i16(self): return struct.unpack(">h", self.read(2))[0]
    def i32(self): return struct.unpack(">i", self.read(4))[0]
    def i64(self): return struct.unpack(">q", self.read(8))[0]
    def f32(self): return struct.unpack(">f", self.read(4))[0]
    def f64(self): return struct.unpack(">d", self.read(8))[0]
    def text(self):
        size = struct.unpack(">H", self.read(2))[0]
        return self.read(size).decode("utf-8", "replace")

    def payload(self, tag: int):
        if tag == 1: return self.i8()
        if tag == 2: return self.i16()
        if tag == 3: return self.i32()
        if tag == 4: return self.i64()
        if tag == 5: return self.f32()
        if tag == 6: return self.f64()
        if tag == 7:
            n = max(0, self.i32()); return self.read(n)
        if tag == 8: return self.text()
        if tag == 9:
            inner = self.u8(); n = max(0, self.i32()); return [self.payload(inner) for _ in range(n)]
        if tag == 10:
            out = {}
            while True:
                inner = self.u8()
                if inner == 0: return out
                name = self.text(); out[name] = self.payload(inner)
        if tag == 11:
            n = max(0, self.i32()); return [self.i32() for _ in range(n)]
        if tag == 12:
            n = max(0, self.i32()); return [self.i64() for _ in range(n)]
        raise ValueError(f"Unsupported NBT tag {tag}")

    def root(self):
        tag = self.u8()
        if tag == 0: return {}
        _name = self.text()
        return self.payload(tag)


def read_level_dat(world: str | Path) -> dict[str, Any]:
    path = Path(world) / "level.dat"
    try:
        raw = gzip.decompress(path.read_bytes())
        root = _NBT(raw).root()
    except (OSError, EOFError, ValueError, struct.error):
        return {"path": str(Path(world)), "readable": False}
    data = root.get("Data", root) if isinstance(root, dict) else {}
    settings = data.get("WorldGenSettings", {}) if isinstance(data, dict) else {}
    seed = settings.get("seed") if isinstance(settings, dict) else None
    return {
        "path": str(Path(world)),
        "readable": True,
        "name": str(data.get("LevelName", Path(world).name)),
        "data_version": data.get("DataVersion"),
        "version_name": (data.get("Version", {}) or {}).get("Name") if isinstance(data.get("Version", {}), dict) else None,
        "seed": seed,
        "spawn": [data.get("SpawnX"), data.get("SpawnY"), data.get("SpawnZ")],
        "hardcore": bool(data.get("hardcore", 0)),
        "game_type": data.get("GameType"),
        "last_played": data.get("LastPlayed"),
    }


def discover_saves() -> list[dict[str, Any]]:
    rows = []
    seen = set()
    for root in minecraft_roots():
        saves = root / "saves"
        if not saves.exists(): continue
        try: folders = list(saves.iterdir())
        except OSError: continue
        for folder in folders:
            if not folder.is_dir() or not (folder / "level.dat").exists(): continue
            key = str(folder.resolve())
            if key in seen: continue
            seen.add(key); rows.append(read_level_dat(folder))
    rows.sort(key=lambda row: (int(row.get("last_played") or 0), str(row.get("name", ""))), reverse=True)
    return rows
