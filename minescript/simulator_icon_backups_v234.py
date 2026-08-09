from __future__ import annotations

"""Map Simulation Lab icon roles to existing original F3+ artwork.

Minecraft textures remain the preferred artwork. These aliases are deliberately kept
inside the first-party pixel-art library path so missing/renamed client textures never
leave a simulator with a blank or generic placeholder icon.
"""

BACKUP_ICON_KEYS = {
    "loot": "storage",
    "enchant": "rng",
    "anvil": "shape",
    "brewing": "redstone",
    "dye": "trade",
    "animal": "farm",
}


def install() -> None:
    from . import pixel_art

    if getattr(pixel_art, "_simulator_backups_v234_installed", False):
        return
    previous = pixel_art.icon_pixmap

    def icon_pixmap(kind: str, p: dict, size: int = 32):
        return previous(BACKUP_ICON_KEYS.get(str(kind).lower(), kind), p, size)

    pixel_art.icon_pixmap = icon_pixmap
    pixel_art._simulator_backups_v234_installed = True
