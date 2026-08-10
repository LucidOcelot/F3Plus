from __future__ import annotations

"""Original recolorable SVG artwork for F3+ semantic UI roles.

These are first-party F3+ assets, not recovered Minecraft artwork.  They are rendered
from theme color tokens at runtime so Custom themes can recolor the complete icon set.
Installed Minecraft textures remain the preferred art source where the user enables or
selects them.
"""

from xml.sax.saxutils import escape

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QPainter, QPixmap


# Body fragments live in a 24x24 viewBox. P=primary, A=accent, T=text, M=muted.
_SVG_BODY = {
    "home": '<circle cx="12" cy="12" r="3" fill="{A}"/><path d="M12 2v7M12 15v7M2 12h7M15 12h7M5 5l5 5M14 14l5 5M19 5l-5 5M10 14l-5 5" stroke="{P}" stroke-width="3" stroke-linecap="square"/>',
    "app": '<path d="M12 2v6M12 16v6M2 12h6M16 12h6M5 5l4 4M15 15l4 4M19 5l-4 4M9 15l-4 4" stroke="{P}" stroke-width="3"/><rect x="9" y="9" width="6" height="6" rx="1" fill="{A}"/>',
    "seed": '<path d="M12 3c5 2 7 6 5 10-2 4-6 6-10 4-4-2-5-7-2-10 2-2 4-3 7-4Z" fill="none" stroke="{P}" stroke-width="2"/><path d="M8 16c1-5 4-8 9-10" stroke="{A}" stroke-width="2"/>',
    "automation": '<path d="M13 2 5 13h6l-1 9 9-13h-6Z" fill="{P}" stroke="{A}" stroke-width="1.5"/>',
    "navigation": '<circle cx="12" cy="12" r="9" fill="none" stroke="{P}" stroke-width="2"/><path d="m15.5 8.5-2.2 5-5 2.2 2.2-5Z" fill="{A}"/><circle cx="12" cy="12" r="1.2" fill="{T}"/>',
    "map": '<path d="m3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2Z" fill="none" stroke="{P}" stroke-width="2"/><path d="M9 3v16M15 5v16" stroke="{A}" stroke-width="1.5"/>',
    "route": '<circle cx="5" cy="18" r="2.5" fill="{A}"/><circle cx="19" cy="5" r="2.5" fill="{A}"/><path d="M7 17c5-1 1-7 6-7s3-4 4-4" fill="none" stroke="{P}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="2 2"/>',
    "portal": '<rect x="4" y="2" width="16" height="20" rx="1" fill="none" stroke="{P}" stroke-width="3"/><rect x="8" y="6" width="8" height="12" fill="{A}" opacity=".65"/><path d="m10 9 4 3-4 3M14 9l-4 3 4 3" stroke="{T}" stroke-width="1.3" fill="none"/>',
    "structure": '<path d="M3 20h18M5 20V10h14v10M3 10l9-7 9 7ZM9 20v-6h6v6" fill="none" stroke="{P}" stroke-width="2"/><circle cx="12" cy="8" r="1.5" fill="{A}"/>',
    "spawner": '<rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="{P}" stroke-width="2"/><path d="M7 3v18M12 3v18M17 3v18M3 7h18M3 12h18M3 17h18" stroke="{M}" stroke-width="1"/><circle cx="12" cy="12" r="3" fill="{A}"/>',
    "biome": '<path d="M2 19h20M3 18l5-7 3 4 4-8 6 11" fill="none" stroke="{P}" stroke-width="2"/><path d="M4 19c3-4 5-4 8 0M13 19c2-3 4-3 7 0" stroke="{A}" stroke-width="2" fill="none"/>',
    "ore": '<path d="M4 20 14 10M10 5l9 9M8 7l4-4 9 9-4 4Z" fill="none" stroke="{P}" stroke-width="2"/><path d="m4 4 3 1 1 3-3 1-2-2Z" fill="{A}"/><path d="m16 18 3-1 2 2-2 3-3-1Z" fill="{A}"/>',
    "calculator": '<rect x="4" y="2" width="16" height="20" rx="2" fill="none" stroke="{P}" stroke-width="2"/><rect x="7" y="5" width="10" height="4" fill="{A}"/><path d="M8 13h2M14 13h2M8 17h2M14 17h2" stroke="{T}" stroke-width="2.5"/>',
    "building": '<path d="M4 20V8l8-5 8 5v12ZM8 20v-6h8v6" fill="none" stroke="{P}" stroke-width="2"/><path d="M5 10h14M12 4v9" stroke="{A}" stroke-width="1.5"/>',
    "shape": '<circle cx="9" cy="10" r="6" fill="none" stroke="{P}" stroke-width="2"/><rect x="10" y="9" width="10" height="10" fill="none" stroke="{A}" stroke-width="2"/><path d="M3 21h18" stroke="{M}"/>',
    "farm": '<path d="M12 21V10M12 13c-5 0-7-3-7-7 5 0 7 3 7 7ZM12 16c5 0 7-3 7-7-5 0-7 3-7 7Z" fill="none" stroke="{P}" stroke-width="2"/><path d="M3 21h18" stroke="{A}" stroke-width="2"/>',
    "redstone": '<circle cx="5" cy="12" r="2" fill="{A}"/><circle cx="19" cy="6" r="2" fill="{A}"/><circle cx="19" cy="18" r="2" fill="{A}"/><path d="M7 12h5V6h5M12 12v6h5" fill="none" stroke="{P}" stroke-width="2"/>',
    "storage": '<path d="M3 8h18v12H3ZM5 4h14l2 4H3Z" fill="none" stroke="{P}" stroke-width="2"/><path d="M9 11h6v4H9Z" fill="{A}"/>',
    "rng": '<rect x="4" y="4" width="16" height="16" rx="3" fill="none" stroke="{P}" stroke-width="2"/><circle cx="9" cy="9" r="1.5" fill="{A}"/><circle cx="15" cy="15" r="1.5" fill="{A}"/><circle cx="15" cy="9" r="1.5" fill="{T}"/><circle cx="9" cy="15" r="1.5" fill="{T}"/>',
    "enchant": '<path d="M3 6c4-2 7-1 9 1 2-2 5-3 9-1v14c-4-2-7-1-9 1-2-2-5-3-9-1Z" fill="none" stroke="{P}" stroke-width="2"/><path d="M12 7v14M17 2v4M15 4h4" stroke="{A}" stroke-width="1.5"/>',
    "anvil": '<path d="M3 5h18l-3 5h-4v4l4 5H6l4-5v-4H6Z" fill="none" stroke="{P}" stroke-width="2"/><path d="M7 8h10M8 19h8" stroke="{A}" stroke-width="2"/>',
    "loot": '<path d="M3 8h18v12H3ZM5 4h14l2 4H3Z" fill="none" stroke="{P}" stroke-width="2"/><path d="m17 2 .7 2.3L20 5l-2.3.7L17 8l-.7-2.3L14 5l2.3-.7Z" fill="{A}"/><circle cx="12" cy="14" r="2" fill="{A}"/>',
    "brewing": '<path d="M9 2h6M10 2v7l-5 9c-1 2 1 4 3 4h8c2 0 4-2 3-4l-5-9V2" fill="none" stroke="{P}" stroke-width="2"/><path d="M7 17h10" stroke="{A}" stroke-width="3"/><circle cx="10" cy="14" r="1" fill="{A}"/>',
    "horse": '<path d="M5 21V9l4-6 3 4 5-2 2 5-3 4v7M8 12h8M9 17h6" fill="none" stroke="{P}" stroke-width="2"/><circle cx="15" cy="9" r="1" fill="{A}"/>',
    "villager": '<path d="M6 5h12v11l-3 5H9l-3-5Z" fill="none" stroke="{P}" stroke-width="2"/><path d="M9 10h2M15 10h-2M10 14h4" stroke="{T}" stroke-width="2"/><path d="m19 15 2 3-2 3-2-3Z" fill="{A}"/>',
    "trade": '<path d="M3 8h13l-3-3M16 8l-3 3M21 16H8l3-3M8 16l3 3" fill="none" stroke="{P}" stroke-width="2"/><path d="m4 15 2-3 2 3-2 3Z" fill="{A}"/>',
    "guided": '<path d="M4 4h13a3 3 0 0 1 3 3v13H7a3 3 0 0 1-3-3ZM7 8h9M7 12h9M7 16h6" fill="none" stroke="{P}" stroke-width="2"/><circle cx="19" cy="5" r="2" fill="{A}"/>',
    "utilities": '<path d="m14 4 2-2 4 4-2 2-3-1-7 7 1 3-4 4-3-3 4-4 3 1 7-7Z" fill="none" stroke="{P}" stroke-width="2"/><circle cx="6" cy="18" r="1.5" fill="{A}"/>',
    "safety": '<path d="M12 2 20 5v6c0 5-3 9-8 11-5-2-8-6-8-11V5Z" fill="none" stroke="{P}" stroke-width="2"/><path d="m8 12 3 3 5-6" fill="none" stroke="{A}" stroke-width="2.5"/>',
}

_ALIASES = {
    "chorus_flower": "home", "chorus_fruit": "seed", "shulker": "automation",
    "shulker_seed": "structure", "chorus_calc": "calculator",
}

SVG_KEYS = frozenset(_SVG_BODY)


def svg_text(kind: str, colors: dict) -> str | None:
    key = _ALIASES.get(str(kind or "home").lower(), str(kind or "home").lower())
    body = _SVG_BODY.get(key)
    if body is None: return None
    tokens = {
        "P": escape(str(colors.get("primary", "#7B3FF2"))),
        "A": escape(str(colors.get("accent", "#D9B64C"))),
        "T": escape(str(colors.get("text", "#F7F3FF"))),
        "M": escape(str(colors.get("muted", "#A99BBD"))),
    }
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">' + body.format(**tokens) + '</svg>'


def icon_pixmap(kind: str, colors: dict, size: int = 32) -> QPixmap:
    svg = svg_text(kind, colors)
    if not svg: return QPixmap()
    try:
        from PySide6.QtSvg import QSvgRenderer
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        if not renderer.isValid(): return QPixmap()
        pix = QPixmap(int(size), int(size)); pix.fill(Qt.transparent); painter = QPainter(pix); renderer.render(painter); painter.end(); return pix
    except Exception:
        return QPixmap()
