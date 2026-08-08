from __future__ import annotations

import gzip
import math
import struct
import zlib
from collections import Counter, deque
from pathlib import Path
from typing import Any, Iterator

AIR = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}
WATER = {"minecraft:water", "minecraft:bubble_column"}
ORE_NAMES = {
    "minecraft:coal_ore", "minecraft:deepslate_coal_ore",
    "minecraft:iron_ore", "minecraft:deepslate_iron_ore",
    "minecraft:copper_ore", "minecraft:deepslate_copper_ore",
    "minecraft:gold_ore", "minecraft:deepslate_gold_ore", "minecraft:nether_gold_ore",
    "minecraft:redstone_ore", "minecraft:deepslate_redstone_ore",
    "minecraft:lapis_ore", "minecraft:deepslate_lapis_ore",
    "minecraft:diamond_ore", "minecraft:deepslate_diamond_ore",
    "minecraft:emerald_ore", "minecraft:deepslate_emerald_ore",
    "minecraft:nether_quartz_ore", "minecraft:ancient_debris",
}


class NBTError(ValueError):
    pass


class _NBT:
    def __init__(self, data: bytes):
        self.data = memoryview(data)
        self.pos = 0

    def _take(self, n: int) -> memoryview:
        if n < 0 or self.pos + n > len(self.data):
            raise NBTError("Truncated NBT payload")
        out = self.data[self.pos:self.pos + n]
        self.pos += n
        return out

    def _unpack(self, fmt: str):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self._take(size))[0]

    def u8(self) -> int:
        return self._unpack(">B")

    def i8(self) -> int:
        return self._unpack(">b")

    def i16(self) -> int:
        return self._unpack(">h")

    def i32(self) -> int:
        return self._unpack(">i")

    def i64(self) -> int:
        return self._unpack(">q")

    def f32(self) -> float:
        return self._unpack(">f")

    def f64(self) -> float:
        return self._unpack(">d")

    def string(self) -> str:
        n = self._unpack(">H")
        return bytes(self._take(n)).decode("utf-8", "replace")

    def payload(self, tag: int):
        if tag == 1:
            return self.i8()
        if tag == 2:
            return self.i16()
        if tag == 3:
            return self.i32()
        if tag == 4:
            return self.i64()
        if tag == 5:
            return self.f32()
        if tag == 6:
            return self.f64()
        if tag == 7:
            n = self.i32()
            return bytes(self._take(n))
        if tag == 8:
            return self.string()
        if tag == 9:
            child = self.u8()
            n = self.i32()
            if n < 0:
                raise NBTError("Negative NBT list length")
            return [self.payload(child) for _ in range(n)]
        if tag == 10:
            out: dict[str, Any] = {}
            while True:
                child = self.u8()
                if child == 0:
                    return out
                name = self.string()
                out[name] = self.payload(child)
        if tag == 11:
            n = self.i32()
            return [self.i32() for _ in range(max(0, n))]
        if tag == 12:
            n = self.i32()
            return [self.i64() for _ in range(max(0, n))]
        raise NBTError(f"Unsupported NBT tag {tag}")

    def root(self) -> dict[str, Any]:
        tag = self.u8()
        if tag != 10:
            raise NBTError("Chunk root is not an NBT compound")
        self.string()  # root name
        value = self.payload(10)
        if not isinstance(value, dict):
            raise NBTError("Invalid NBT root")
        return value


def parse_nbt(data: bytes) -> dict[str, Any]:
    return _NBT(data).root()


def _region_dir(world: Path, dimension: str) -> Path:
    d = str(dimension).lower()
    if d in {"nether", "-1", "dim-1"}:
        return world / "DIM-1" / "region"
    if d in {"end", "1", "dim1"}:
        return world / "DIM1" / "region"
    return world / "region"


def _region_coords(path: Path) -> tuple[int, int]:
    parts = path.stem.split(".")
    if len(parts) < 3:
        return 0, 0
    return int(parts[-2]), int(parts[-1])


def iter_region_chunks(path: Path) -> Iterator[dict[str, Any]]:
    raw = path.read_bytes()
    if len(raw) < 8192:
        return
    rx, rz = _region_coords(path)
    for index in range(1024):
        entry = int.from_bytes(raw[index * 4:index * 4 + 4], "big")
        offset = entry >> 8
        sectors = entry & 0xFF
        if not offset or not sectors:
            continue
        pos = offset * 4096
        if pos + 5 > len(raw):
            continue
        length = int.from_bytes(raw[pos:pos + 4], "big")
        if length <= 1 or pos + 4 + length > len(raw):
            continue
        compression = raw[pos + 4]
        payload = raw[pos + 5:pos + 4 + length]
        try:
            if compression == 1:
                data = gzip.decompress(payload)
            elif compression == 2:
                data = zlib.decompress(payload)
            elif compression == 3:
                data = payload
            else:
                continue
            chunk = parse_nbt(data)
        except (OSError, zlib.error, NBTError, ValueError, struct.error):
            continue
        local_x = index & 31
        local_z = index >> 5
        chunk.setdefault("xPos", rx * 32 + local_x)
        chunk.setdefault("zPos", rz * 32 + local_z)
        yield chunk


def _packed_indices(data: list[int], palette_size: int, count: int = 4096) -> list[int]:
    if palette_size <= 1 or not data:
        return [0] * count
    bits = max(4, math.ceil(math.log2(palette_size)))
    per_long = max(1, 64 // bits)
    mask = (1 << bits) - 1
    out = [0] * count
    for i in range(count):
        li = i // per_long
        if li >= len(data):
            break
        shift = (i % per_long) * bits
        out[i] = ((int(data[li]) & 0xFFFFFFFFFFFFFFFF) >> shift) & mask
    return out


def _section_blocks(section: dict[str, Any]) -> tuple[int, list[str], list[int]] | None:
    states = section.get("block_states") or section.get("BlockStates")
    if isinstance(states, dict):
        palette = states.get("palette", [])
        data = states.get("data", [])
    else:
        palette = section.get("Palette", [])
        data = section.get("BlockStates", [])
    if not isinstance(palette, list) or not palette:
        return None
    names = []
    for item in palette:
        if isinstance(item, dict):
            names.append(str(item.get("Name", item.get("name", "minecraft:air"))))
        else:
            names.append(str(item))
    sy = int(section.get("Y", section.get("y", 0)))
    return sy, names, _packed_indices(list(data) if isinstance(data, list) else [], len(names))


def _chunk_sections(chunk: dict[str, Any]) -> list[dict[str, Any]]:
    level = chunk.get("Level") if isinstance(chunk.get("Level"), dict) else chunk
    sections = level.get("sections", level.get("Sections", []))
    return sections if isinstance(sections, list) else []


def _block_name(names: list[str], values: list[int], index: int) -> str:
    pi = values[index] if 0 <= index < len(values) else 0
    return names[pi] if 0 <= pi < len(names) else "minecraft:air"


def analyze_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    cx = int(chunk.get("xPos", chunk.get("Level", {}).get("xPos", 0) if isinstance(chunk.get("Level"), dict) else 0))
    cz = int(chunk.get("zPos", chunk.get("Level", {}).get("zPos", 0) if isinstance(chunk.get("Level"), dict) else 0))
    ore_counts: Counter[str] = Counter()
    ore_by_y: dict[str, Counter[int]] = {}
    exposed: Counter[str] = Counter()
    cave_air = 0
    cave_faces = 0
    columns: dict[tuple[int, int], tuple[int, str]] = {}

    for raw_section in _chunk_sections(chunk):
        if not isinstance(raw_section, dict):
            continue
        parsed = _section_blocks(raw_section)
        if parsed is None:
            continue
        sy, names, values = parsed
        if len(names) == 1:
            values = [0] * 4096
        for idx in range(4096):
            name = _block_name(names, values, idx)
            ly = idx // 256
            rem = idx % 256
            lz = rem // 16
            lx = rem % 16
            y = sy * 16 + ly
            if name in ORE_NAMES:
                ore_counts[name] += 1
                ore_by_y.setdefault(name, Counter())[y] += 1
                for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                    nx, ny, nz = lx + dx, ly + dy, lz + dz
                    if 0 <= nx < 16 and 0 <= ny < 16 and 0 <= nz < 16:
                        ni = nx + nz * 16 + ny * 256
                        if _block_name(names, values, ni) in AIR | WATER:
                            exposed[name] += 1
                            break
            if name in {"minecraft:cave_air", "minecraft:air"} and y < 64:
                cave_air += 1
                for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                    nx, ny, nz = lx + dx, ly + dy, lz + dz
                    if 0 <= nx < 16 and 0 <= ny < 16 and 0 <= nz < 16:
                        ni = nx + nz * 16 + ny * 256
                        neighbor = _block_name(names, values, ni)
                        if neighbor not in AIR | WATER:
                            cave_faces += 1
            if name not in AIR:
                key = (lx, lz)
                current = columns.get(key)
                if current is None or y > current[0]:
                    columns[key] = (y, name)

    heights = [value[0] for value in columns.values()]
    water_tops = sum(1 for _, name in columns.values() if name in WATER)
    return {
        "chunk": (cx, cz),
        "ore_counts": dict(ore_counts),
        "ore_by_y": {name: dict(counter) for name, counter in ore_by_y.items()},
        "exposed_ore_counts": dict(exposed),
        "cave_air_blocks": cave_air,
        "cave_surface_faces": cave_faces,
        "min_surface_y": min(heights) if heights else None,
        "max_surface_y": max(heights) if heights else None,
        "mean_surface_y": (sum(heights) / len(heights)) if heights else None,
        "water_top_ratio": water_tops / max(1, len(columns)),
        "columns": {f"{x},{z}": [y, name] for (x, z), (y, name) in columns.items()},
    }


def _components(points: set[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    out: list[list[tuple[int, int]]] = []
    unseen = set(points)
    while unseen:
        start = unseen.pop()
        group = [start]
        queue = deque([start])
        while queue:
            x, z = queue.popleft()
            for neighbor in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
                    group.append(neighbor)
        out.append(group)
    out.sort(key=len, reverse=True)
    return out


def analyze_world(world_path: str | Path, *, dimension: str = "Overworld", center_chunk: tuple[int, int] = (0, 0), radius_chunks: int = 64, max_chunks: int = 4096) -> dict[str, Any]:
    world = Path(world_path).expanduser()
    region = _region_dir(world, dimension)
    if not region.is_dir():
        raise FileNotFoundError(f"No region directory found at {region}")
    cx0, cz0 = map(int, center_chunk)
    radius = max(0, int(radius_chunks))
    chunks: list[dict[str, Any]] = []
    for file in sorted(region.glob("r.*.*.mca")):
        for chunk in iter_region_chunks(file):
            cx = int(chunk.get("xPos", 0))
            cz = int(chunk.get("zPos", 0))
            if abs(cx - cx0) > radius or abs(cz - cz0) > radius:
                continue
            chunks.append(analyze_chunk(chunk))
            if len(chunks) >= max_chunks:
                break
        if len(chunks) >= max_chunks:
            break
    if not chunks:
        raise ValueError("No generated chunks were found in the selected scan area")

    ores: Counter[str] = Counter()
    exposed: Counter[str] = Counter()
    ore_by_y: dict[str, Counter[int]] = {}
    cave_air = 0
    cave_faces = 0
    peak = None
    valley = None
    water_chunks: set[tuple[int, int]] = set()
    land_chunks: set[tuple[int, int]] = set()
    surface_mean: dict[tuple[int, int], float] = {}
    for item in chunks:
        ores.update(item["ore_counts"])
        exposed.update(item["exposed_ore_counts"])
        for ore, rows in item["ore_by_y"].items():
            ore_by_y.setdefault(ore, Counter()).update({int(y): int(n) for y, n in rows.items()})
        cave_air += int(item["cave_air_blocks"])
        cave_faces += int(item["cave_surface_faces"])
        pos = tuple(item["chunk"])
        if item["water_top_ratio"] >= 0.5:
            water_chunks.add(pos)
        else:
            land_chunks.add(pos)
        if item["mean_surface_y"] is not None:
            surface_mean[pos] = float(item["mean_surface_y"])
        if item["max_surface_y"] is not None and (peak is None or item["max_surface_y"] > peak[0]):
            peak = (item["max_surface_y"], pos)
        if item["min_surface_y"] is not None and (valley is None or item["min_surface_y"] < valley[0]):
            valley = (item["min_surface_y"], pos)

    cliff = None
    for (cx, cz), h in surface_mean.items():
        for neighbor in ((cx + 1, cz), (cx, cz + 1)):
            if neighbor in surface_mean:
                delta = abs(h - surface_mean[neighbor])
                if cliff is None or delta > cliff[0]:
                    cliff = (delta, (cx, cz), neighbor)

    ocean_components = _components(water_chunks)
    land_components = _components(land_chunks)
    islands = []
    for comp in land_components:
        border_water = 0
        border_total = 0
        comp_set = set(comp)
        for x, z in comp:
            for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
                if n in comp_set:
                    continue
                border_total += 1
                if n in water_chunks:
                    border_water += 1
        if border_total and border_water / border_total >= 0.75:
            islands.append({"chunks": comp, "size_chunks": len(comp), "water_border_ratio": border_water / border_total})
    islands.sort(key=lambda x: x["size_chunks"], reverse=True)

    total_ore = sum(ores.values())
    diamond = ores["minecraft:diamond_ore"] + ores["minecraft:deepslate_diamond_ore"]
    iron = ores["minecraft:iron_ore"] + ores["minecraft:deepslate_iron_ore"]
    resource_score = min(100.0, 20.0 * math.log10(1 + total_ore) + 15.0 * math.log10(1 + diamond) + 8.0 * math.log10(1 + iron))
    relief = (peak[0] - valley[0]) if peak and valley else 0
    technical_score = min(100.0, resource_score * 0.55 + min(30.0, relief / 4.0) + min(15.0, cave_faces / max(1, len(chunks) * 300.0)))

    return {
        "world_path": str(world.resolve()),
        "dimension": dimension,
        "center_chunk": [cx0, cz0],
        "radius_chunks": radius,
        "chunks_scanned": len(chunks),
        "ore_counts": dict(ores),
        "ore_by_y": {ore: dict(sorted(rows.items())) for ore, rows in ore_by_y.items()},
        "exposed_ore_counts": dict(exposed),
        "cave_air_blocks": cave_air,
        "cave_surface_faces": cave_faces,
        "peak": {"y": peak[0], "chunk": list(peak[1])} if peak else None,
        "valley": {"y": valley[0], "chunk": list(valley[1])} if valley else None,
        "largest_cliff": {"mean_height_delta": cliff[0], "chunk_a": list(cliff[1]), "chunk_b": list(cliff[2])} if cliff else None,
        "largest_ocean": {"size_chunks": len(ocean_components[0]), "chunks": ocean_components[0][:256]} if ocean_components else None,
        "largest_islands": islands[:16],
        "resource_score": round(resource_score, 2),
        "technical_world_score": round(technical_score, 2),
        "limitations": [
            "Exposure counts inspect neighbors inside each 16x16x16 section; section/chunk boundary faces are intentionally not guessed.",
            "Only already-generated chunks in the selected save are analyzed.",
        ],
    }
