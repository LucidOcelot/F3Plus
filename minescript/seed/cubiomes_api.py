from __future__ import annotations

import ctypes
from dataclasses import dataclass
from .bundled import load_cubiomes, cubiomes_status

# Cubiomes enum StructureType values from bundled finders.h.
STRUCTURE_TYPES = {
    'Desert Pyramid': 1,
    'Jungle Temple': 2,
    'Swamp Hut': 3,
    'Igloo': 4,
    'Village': 5,
    'Ocean Ruin': 6,
    'Shipwreck': 7,
    'Ocean Monument': 8,
    'Woodland Mansion': 9,
    'Pillager Outpost': 10,
    'Ruined Portal': 11,
    'Ancient City': 13,
    'Buried Treasure': 14,
    'Nether Fortress': 18,
    'Bastion': 19,
    'End City': 20,
    'Trial Chamber': 24,
}


def _canonical_structure_name(name: str) -> str:
    key = ''.join(ch for ch in str(name).strip().lower() if ch.isalnum())
    aliases = {''.join(ch for ch in canonical.lower() if ch.isalnum()): canonical for canonical in STRUCTURE_TYPES}
    aliases.update({
        'deserttemple': 'Desert Pyramid',
        'junglepyramid': 'Jungle Temple',
        'witchhut': 'Swamp Hut',
        'monument': 'Ocean Monument',
        'mansion': 'Woodland Mansion',
        'outpost': 'Pillager Outpost',
        'fortress': 'Nether Fortress',
        'netherfortress': 'Nether Fortress',
        'bastionremnant': 'Bastion',
        'trialchambers': 'Trial Chamber',
        'ancientcities': 'Ancient City',
    })
    try:
        return aliases[key]
    except KeyError as exc:
        raise KeyError(name) from exc


@dataclass(frozen=True)
class CubiomesBiomeResult:
    biome_id: int
    seed: int
    x: int
    y: int
    z: int
    dimension: int
    mc_enum: int
    bundled_newest_enum: int

@dataclass(frozen=True)
class CubiomesStructureConfig:
    name: str
    structure_type: int
    salt: int
    region_size: int
    chunk_range: int
    dimension: int
    mc_enum: int

@dataclass(frozen=True)
class CubiomesStructureResult:
    name: str
    structure_type: int
    seed: int
    region_x: int
    region_z: int
    chunk_x: int
    chunk_z: int
    mc_enum: int


def _lib():
    lib = load_cubiomes()
    lib.minescript_cubiomes_newest.argtypes = []
    lib.minescript_cubiomes_newest.restype = ctypes.c_int
    lib.minescript_cubiomes_biome_at.argtypes = [
        ctypes.c_int64, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ]
    lib.minescript_cubiomes_biome_at.restype = ctypes.c_int
    lib.minescript_cubiomes_structure_config.argtypes = [
        ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ]
    lib.minescript_cubiomes_structure_config.restype = ctypes.c_int
    lib.minescript_cubiomes_structure_pos.argtypes = [
        ctypes.c_int64, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ]
    lib.minescript_cubiomes_structure_pos.restype = ctypes.c_int
    return lib


def newest_enum() -> int:
    return int(_lib().minescript_cubiomes_newest())


def biome_at(seed: int, x: int, y: int = 64, z: int = 0, *, dimension: int = 0, mc: int = 0) -> CubiomesBiomeResult:
    """Query bundled Cubiomes directly.

    ``mc=0`` selects the newest version supported by the bundled Cubiomes revision.
    Cubiomes' own supported-version range is independent of F3+'s active
    snapshot/release targets; callers must not imply 26.x support merely because
    F3+ itself supports those versions elsewhere.
    """
    status = cubiomes_status()
    if not status.available:
        raise RuntimeError(status.note)
    lib = _lib()
    newest = int(lib.minescript_cubiomes_newest())
    selected = newest if int(mc) <= 0 else int(mc)
    bid = int(lib.minescript_cubiomes_biome_at(int(seed), selected, int(dimension), int(x), int(y), int(z)))
    return CubiomesBiomeResult(bid, int(seed), int(x), int(y), int(z), int(dimension), selected, newest)


def structure_config(name: str, *, mc: int = 0) -> CubiomesStructureConfig:
    name = _canonical_structure_name(name)
    lib = _lib(); selected = newest_enum() if int(mc) <= 0 else int(mc)
    salt=ctypes.c_int(); region=ctypes.c_int(); chunk_range=ctypes.c_int(); dim=ctypes.c_int()
    ok=lib.minescript_cubiomes_structure_config(STRUCTURE_TYPES[name],selected,ctypes.byref(salt),ctypes.byref(region),ctypes.byref(chunk_range),ctypes.byref(dim))
    if not ok: raise ValueError(f'{name} is unsupported by bundled Cubiomes version enum {selected}')
    return CubiomesStructureConfig(name,STRUCTURE_TYPES[name],salt.value,region.value,chunk_range.value,dim.value,selected)


def structure_pos(name: str, seed: int, region_x: int, region_z: int, *, mc: int = 0) -> CubiomesStructureResult | None:
    name = _canonical_structure_name(name)
    lib = _lib(); selected = newest_enum() if int(mc) <= 0 else int(mc)
    cx=ctypes.c_int(); cz=ctypes.c_int()
    ok=lib.minescript_cubiomes_structure_pos(int(seed),selected,STRUCTURE_TYPES[name],int(region_x),int(region_z),ctypes.byref(cx),ctypes.byref(cz))
    if not ok:return None
    return CubiomesStructureResult(name,STRUCTURE_TYPES[name],int(seed),int(region_x),int(region_z),cx.value,cz.value,selected)
