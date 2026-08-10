from __future__ import annotations

"""Coverage-aware coordinator for Mojang reference-world generation.

The underlying generator intentionally remains the small, independently integration-
tested implementation in ``seed_worldgen``. This layer reuses an already generated
world when Search Until Found expands the radius instead of materializing a separate
full world for every radius.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .seed_worldgen import (
    CACHE_ROOT,
    TARGET_MINECRAFT,
    WorldgenError,
    canonical_version_id,
    generate_reference_world,
)

_MARKER = ".f3plus-worldgen.json"


def _radius_key(version_id: str, seed: int, cx: int, cz: int, radius: int) -> str:
    return hashlib.sha256(f"{version_id}|{int(seed)}|{int(cx)}|{int(cz)}|{int(radius)}".encode()).hexdigest()[:20]


def _world_root(cache_root: Path, version_id: str, seed: int) -> Path:
    return Path(cache_root) / "worlds" / version_id / str(int(seed))


def _read_marker(target: Path) -> dict[str, Any] | None:
    marker = target / _MARKER
    if not marker.is_file():
        return None
    try:
        value = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _cached_world(target: Path, meta: dict[str, Any]) -> Path | None:
    raw = str(meta.get("world_relative", "world"))
    candidate = target / raw
    roots = [candidate, target]
    try:
        roots.extend(path.parent for path in target.rglob("region") if path.is_dir())
    except OSError:
        pass
    seen = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            resolved = root
        if resolved in seen:
            continue
        seen.add(resolved)
        region = root / "region"
        try:
            if region.is_dir() and any(region.glob("r.*.*.mca")):
                return root
        except OSError:
            continue
    return None


def _compatible(meta: dict[str, Any], *, version_id: str, seed: int, cx: int, cz: int) -> bool:
    try:
        center = list(meta.get("center_chunk", []))
        return (
            str(meta.get("version", "")) == version_id
            and int(meta.get("seed")) == int(seed)
            and len(center) >= 2
            and int(center[0]) == int(cx)
            and int(center[1]) == int(cz)
        )
    except (TypeError, ValueError):
        return False


def cached_coverage(
    cache_root: Path,
    version: str,
    seed: int,
    center_chunk: tuple[int, int],
) -> list[tuple[int, Path, Path, dict[str, Any]]]:
    """Return valid cached coverage rows as ``radius, target, world, marker``."""
    version_id = canonical_version_id(version); cx, cz = map(int, center_chunk); root = _world_root(cache_root, version_id, seed); rows = []
    if not root.is_dir():
        return rows
    try:
        targets = list(root.iterdir())
    except OSError:
        return rows
    for target in targets:
        if not target.is_dir():
            continue
        meta = _read_marker(target)
        if meta is None or not _compatible(meta, version_id=version_id, seed=seed, cx=cx, cz=cz):
            continue
        try:
            radius = max(0, int(meta.get("radius_chunks", -1)))
        except (TypeError, ValueError):
            continue
        world = _cached_world(target, meta)
        if world is not None:
            rows.append((radius, target, world, meta))
    rows.sort(key=lambda row: row[0], reverse=True)
    return rows


def prepare_expansion_cache(
    cache_root: Path,
    version: str,
    seed: int,
    center_chunk: tuple[int, int],
    requested_radius: int,
) -> dict[str, Any]:
    """Promote the largest smaller cached world into the requested radius cache key.

    The old completion marker is removed after the directory rename. The existing
    generator therefore starts Mojang's server in the same world directory, keeps the
    already-generated chunks, and generates only missing coverage as the world is
    forceloaded. If promotion cannot be performed, callers simply use normal generation.
    """
    version_id = canonical_version_id(version); cx, cz = map(int, center_chunk); radius = max(0, int(requested_radius)); root = _world_root(cache_root, version_id, seed); target = root / _radius_key(version_id, seed, cx, cz, radius)
    rows = cached_coverage(cache_root, version, seed, center_chunk)

    for cached_radius, cached_target, world, meta in rows:
        if cached_radius >= radius:
            return {"ready": True, "world": world, "coverage_radius": cached_radius, "target": cached_target, "meta": meta, "reused": True}

    if target.exists():
        return {"ready": False, "target": target, "reused": False, "reason": "requested cache target already exists without complete coverage"}

    smaller = next((row for row in rows if row[0] < radius), None)
    if smaller is None:
        return {"ready": False, "target": target, "reused": False}

    cached_radius, cached_target, _world, _meta = smaller
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(cached_target, target)
        (target / _MARKER).unlink(missing_ok=True)
    except OSError as exc:
        return {"ready": False, "target": target, "reused": False, "reason": f"cache promotion unavailable: {exc}"}
    return {"ready": False, "target": target, "reused": True, "promoted_from_radius": cached_radius, "requested_radius": radius}


def generate_reusable_reference_world(
    seed: int,
    version: str,
    *,
    center_chunk: tuple[int, int] = (0, 0),
    radius_chunks: int = 4,
    dimension: str = "Overworld",
    java: str | None = None,
    accept_eula: bool = False,
    cache_root: Path = CACHE_ROOT,
    max_chunks: int = 4096,
    startup_timeout: float = 180.0,
) -> tuple[Path, dict[str, Any]]:
    if not accept_eula:
        # Preserve the underlying generator's EULA contract before touching cache data.
        raise WorldgenError("Exact seed regeneration needs explicit Minecraft EULA acceptance for the temporary local server run.")
    state = prepare_expansion_cache(cache_root, version, int(seed), center_chunk, int(radius_chunks))
    if state.get("ready") and isinstance(state.get("world"), Path):
        return state["world"], {"cache_reused": True, "cached_radius_chunks": int(state.get("coverage_radius", radius_chunks)), "reference_world_extended": False}
    world = generate_reference_world(
        int(seed),
        version,
        center_chunk=center_chunk,
        radius_chunks=radius_chunks,
        dimension=dimension,
        java=java,
        accept_eula=accept_eula,
        cache_root=cache_root,
        max_chunks=max_chunks,
        startup_timeout=startup_timeout,
    )
    return world, {
        "cache_reused": bool(state.get("reused")),
        "cached_radius_chunks": int(radius_chunks),
        "reference_world_extended": "promoted_from_radius" in state,
        "previous_radius_chunks": state.get("promoted_from_radius"),
    }


def resolve_world_source(params: dict[str, Any], executor=None, *, default_radius: int = 8) -> tuple[str | None, dict[str, Any]]:
    supplied = str(params.get("world_path", "")).strip()
    if supplied:
        return supplied, {"source": "generated-world save", "exactness": "observed generated chunks"}
    if not bool(params.get("regenerate_from_seed", True)):
        return None, {"requires_generated_world": True, "reason": "No world save selected and exact seed regeneration is disabled."}
    version = str(params.get("minecraft_version") or getattr(executor, "minecraft_version", TARGET_MINECRAFT)); seed = int(str(params.get("seed", 0)).strip()); radius = max(0, int(params.get("radius", default_radius))); max_chunks = max(1, int(params.get("worldgen_max_chunks", 4096))); center = (int(params.get("cx", 0)), int(params.get("cz", 0)))
    try:
        world, reuse = generate_reusable_reference_world(
            seed,
            version,
            center_chunk=center,
            radius_chunks=radius,
            dimension=str(params.get("dimension", "Overworld")),
            java=str(params.get("java", "")).strip() or None,
            accept_eula=bool(params.get("accept_minecraft_eula", False)),
            max_chunks=max_chunks,
        )
    except (WorldgenError, OSError, ValueError) as exc:
        return None, {"requires_seed_worldgen": True, "available": False, "reason": str(exc), "version": version, "seed": seed, "requested_radius_chunks": radius, "next_step": "Select an existing generated save, or let F3+ use a compatible Minecraft Launcher Java runtime for exact seed regeneration."}
    return str(world), {"source": "seed-regenerated vanilla chunks", "exactness": "official Mojang server reference generation", "version": canonical_version_id(version), "seed": seed, "world_path": str(world), **reuse}


__all__ = [
    "cached_coverage", "prepare_expansion_cache", "generate_reusable_reference_world",
    "resolve_world_source",
]
