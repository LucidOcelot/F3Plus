from __future__ import annotations

"""Read a small set of UI textures from the player's installed Minecraft client.

F3+ never redistributes these Mojang assets.  When a compatible local Java
version JAR is available, the UI reads selected PNGs directly from that JAR at
runtime.  Original F3+ theme-aware pixel art remains the fallback.
"""

from functools import lru_cache
from pathlib import Path
import zipfile

from .villagers import installed_versions

# Semantic F3+ art keys -> possible texture paths in an installed Java client.
# Multiple candidates keep this useful across Mojang resource-layout changes.
_TEXTURES = {
    "home": (
        "assets/minecraft/textures/block/chorus_flower.png",
        "assets/minecraft/textures/block/chorus_flower_dead.png",
    ),
    "chorus_flower": (
        "assets/minecraft/textures/block/chorus_flower.png",
        "assets/minecraft/textures/block/chorus_flower_dead.png",
    ),
    "seed": ("assets/minecraft/textures/item/chorus_fruit.png",),
    "chorus_fruit": ("assets/minecraft/textures/item/chorus_fruit.png",),
    "automation": (
        "assets/minecraft/textures/item/redstone.png",
        "assets/minecraft/textures/block/redstone_torch.png",
    ),
    "shulker": (
        "assets/minecraft/textures/item/shulker_shell.png",
        "assets/minecraft/textures/item/purple_dye.png",
    ),
    "navigation": (
        "assets/minecraft/textures/item/compass_00.png",
        "assets/minecraft/textures/item/compass.png",
        "assets/minecraft/textures/item/recovery_compass_00.png",
    ),
    "structure": (
        "assets/minecraft/textures/item/ender_eye.png",
        "assets/minecraft/textures/item/map.png",
    ),
    "shulker_seed": (
        "assets/minecraft/textures/item/ender_eye.png",
        "assets/minecraft/textures/item/shulker_shell.png",
    ),
    "calculator": (
        "assets/minecraft/textures/item/redstone.png",
        "assets/minecraft/textures/item/clock_00.png",
        "assets/minecraft/textures/item/clock.png",
    ),
    "chorus_calc": (
        "assets/minecraft/textures/item/redstone.png",
        "assets/minecraft/textures/item/clock_00.png",
    ),
    "building": (
        "assets/minecraft/textures/item/iron_pickaxe.png",
        "assets/minecraft/textures/item/brick.png",
    ),
    "rng": (
        "assets/minecraft/textures/item/ender_pearl.png",
        "assets/minecraft/textures/item/ender_eye.png",
    ),
    "villager": (
        "assets/minecraft/textures/item/emerald.png",
        "assets/minecraft/textures/item/emerald_block.png",
    ),
    "guided": (
        "assets/minecraft/textures/item/book.png",
        "assets/minecraft/textures/item/writable_book.png",
    ),
    "utilities": (
        "assets/minecraft/textures/item/recovery_compass_00.png",
        "assets/minecraft/textures/item/compass_00.png",
        "assets/minecraft/textures/item/redstone.png",
    ),
    "safety": (
        "assets/minecraft/textures/item/totem_of_undying.png",
        "assets/minecraft/textures/item/golden_apple.png",
    ),
    "app": (
        "assets/minecraft/textures/block/chorus_flower.png",
        "assets/minecraft/textures/item/chorus_fruit.png",
    ),
}


def _normalized(value: str | None) -> str:
    return (value or "").strip().lower().replace(" ", "-")


def _version_order(version_hint: str | None) -> list[tuple[str, Path]]:
    versions = installed_versions()
    if not versions:
        return []
    hint = _normalized(version_hint)
    # Prefer the selected version, then related snapshot/version names, then
    # locally installed versions ordered by JAR modification time and name.
    items = list(versions.items())
    def modified(item):
        try:
            return int(item[1].stat().st_mtime_ns)
        except OSError:
            return 0
    items.sort(key=lambda item: (modified(item), item[0].lower()), reverse=True)
    exact, related, rest = [], [], []
    for item in items:
        name = _normalized(item[0])
        if hint and name == hint:
            exact.append(item)
        elif hint and (hint in name or name in hint):
            related.append(item)
        else:
            rest.append(item)
    return exact + related + rest


@lru_cache(maxsize=96)
def _read_from_jar(jar_text: str, mtime_ns: int, size: int, kind: str) -> tuple[bytes | None, str | None]:
    paths = _TEXTURES.get(kind, ())
    if not paths:
        return None, None
    try:
        with zipfile.ZipFile(jar_text) as jar:
            names = set(jar.namelist())
            for member in paths:
                if member in names:
                    return jar.read(member), member
    except (OSError, zipfile.BadZipFile, KeyError):
        pass
    return None, None


def texture_bytes(kind: str, version_hint: str = "") -> tuple[bytes | None, str | None, str | None]:
    """Return ``(PNG bytes, path in JAR, version)`` for an installed texture."""
    key = str(kind or "").lower()
    if key not in _TEXTURES:
        return None, None, None
    for version, jar in _version_order(version_hint):
        try:
            st = jar.stat()
        except OSError:
            continue
        data, member = _read_from_jar(str(jar.resolve()), int(st.st_mtime_ns), int(st.st_size), key)
        if data:
            return data, member, version
    return None, None, None


def clear_texture_cache() -> None:
    _read_from_jar.cache_clear()
