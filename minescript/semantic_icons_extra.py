from __future__ import annotations

"""Additional first-party recolorable SVGs for canonical F3+ workbenches.

These identities are intentionally more specific than the broad family icons in
``vector_icons`` so the main workbench list can be scanned visually without repeated
flowers, pickaxes, or generic utility glyphs.
"""

from xml.sax.saxutils import escape

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QPainter, QPixmap


_BODY = {
    "actions": '<path d="M4 12h5M15 12h5M12 4v5M12 15v5" stroke="{P}" stroke-width="2.4"/><circle cx="12" cy="12" r="4" fill="none" stroke="{A}" stroke-width="2"/><path d="m10 12 2 2 4-5" fill="none" stroke="{T}" stroke-width="1.8"/>',
    "travel": '<path d="M4 19c4-8 7-3 10-9 1-2 3-4 6-5" fill="none" stroke="{P}" stroke-width="2.3" stroke-linecap="round"/><path d="m16 4 4 1-1 4" fill="none" stroke="{A}" stroke-width="2"/><circle cx="5" cy="18" r="2" fill="{A}"/>',
    "mining": '<path d="M4 20 14 10M9 5l10 10M7 7l4-4 10 10-4 4Z" fill="none" stroke="{P}" stroke-width="2.2"/><path d="M3 4h3M4.5 2.5v3M17 20h4" stroke="{A}" stroke-width="1.8"/>',
    "construction": '<path d="M3 20h18M5 20V9h14v11M8 9V5h8v4M9 13h6M9 16h6" fill="none" stroke="{P}" stroke-width="2"/><path d="M4 9h16" stroke="{A}" stroke-width="2"/>',
    "macro": '<path d="M5 4h14v16H5Z" fill="none" stroke="{P}" stroke-width="2"/><path d="M8 8h5M8 12h8M8 16h4" stroke="{A}" stroke-width="1.8"/><path d="m16 15 4 2-4 2Z" fill="{T}"/>',
    "position": '<circle cx="12" cy="10" r="4" fill="none" stroke="{P}" stroke-width="2"/><path d="M12 2v4M12 14v8M4 10h4M16 10h4" stroke="{A}" stroke-width="2"/><circle cx="12" cy="10" r="1.5" fill="{T}"/>',
    "coordinates": '<path d="M3 20h18M4 4v17" stroke="{P}" stroke-width="2"/><path d="M8 16 12 9l4 3 4-8" fill="none" stroke="{A}" stroke-width="2.2"/><circle cx="12" cy="9" r="1.6" fill="{T}"/>',
    "slime": '<path d="M5 8c0-3 3-5 7-5s7 2 7 5v9c0 3-3 4-7 4s-7-1-7-4Z" fill="none" stroke="{P}" stroke-width="2"/><circle cx="9" cy="12" r="1.3" fill="{A}"/><circle cx="15" cy="12" r="1.3" fill="{A}"/><path d="M9 16h6" stroke="{T}" stroke-width="1.5"/>',
    "local_area": '<rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="{P}" stroke-width="2"/><path d="M9 3v18M15 3v18M3 9h18M3 15h18" stroke="{M}"/><rect x="9" y="9" width="6" height="6" fill="{A}" opacity=".75"/>',
    "world_analysis": '<circle cx="10" cy="10" r="6" fill="none" stroke="{P}" stroke-width="2"/><path d="m14.5 14.5 6 6" stroke="{P}" stroke-width="2.5"/><path d="M6 11h3l1-5 2 8 1-4h3" fill="none" stroke="{A}" stroke-width="1.7"/>',
    "profiles": '<path d="M4 5h6l2 2h8v13H4Z" fill="none" stroke="{P}" stroke-width="2"/><circle cx="10" cy="12" r="2" fill="{A}"/><path d="M7 17c1-2 5-2 6 0M15 10h3M15 14h3" stroke="{T}" stroke-width="1.4"/>',
    "recipes": '<path d="M5 3h14v18H5Z" fill="none" stroke="{P}" stroke-width="2"/><path d="M8 7h8M8 11h5M8 15h8" stroke="{A}" stroke-width="1.8"/><circle cx="16" cy="11" r="1.5" fill="{T}"/>',
    "technical": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4" stroke="{P}" stroke-width="2"/><circle cx="12" cy="12" r="5" fill="none" stroke="{P}" stroke-width="2"/><path d="M12 9v6M9 12h6" stroke="{A}" stroke-width="2"/>',
    "resources": '<path d="M7 3h10l3 5-8 13L4 8Z" fill="none" stroke="{P}" stroke-width="2"/><path d="M4 8h16M8 3l4 5 4-5M8 8l4 13 4-13" stroke="{A}" stroke-width="1.5"/>',
    "generation": '<path d="M12 2 4 7v10l8 5 8-5V7Z" fill="none" stroke="{P}" stroke-width="2"/><path d="m4 7 8 5 8-5M12 12v10" stroke="{A}" stroke-width="1.7"/><circle cx="12" cy="7" r="2" fill="{T}"/>',
    "version": '<path d="M5 4h14v16H5Z" fill="none" stroke="{P}" stroke-width="2"/><path d="M8 8h8M8 12h5M8 16h8" stroke="{A}" stroke-width="1.8"/><circle cx="17" cy="12" r="2" fill="{T}"/>',
    "settings": '<circle cx="12" cy="12" r="3" fill="none" stroke="{A}" stroke-width="2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2" stroke="{P}" stroke-width="2.4"/>',
    "history": '<path d="M4 6h11a6 6 0 1 1-5 9" fill="none" stroke="{P}" stroke-width="2.2"/><path d="m4 3-2 3 2 3M15 9v4l3 2" fill="none" stroke="{A}" stroke-width="2"/>',
    "diagnostics": '<path d="M4 18h16M6 18V8h3v10M11 18V4h3v14M16 18v-6h3v6" fill="none" stroke="{P}" stroke-width="2"/><path d="M4 5h3M18 5h2" stroke="{A}" stroke-width="2"/>',
    "seed_recovery": '<path d="M5 17c4-2 3-8 8-11 2-1 4-1 6 0-1 6-4 10-10 11" fill="none" stroke="{P}" stroke-width="2"/><path d="M4 21c4-5 8-8 14-11" stroke="{A}" stroke-width="2"/><circle cx="6" cy="5" r="2" fill="{T}"/>',
}


SVG_KEYS = frozenset(_BODY)


def icon_pixmap(kind: str, colors: dict, size: int = 32) -> QPixmap:
    body = _BODY.get(str(kind or "").lower())
    if body is None: return QPixmap()
    tokens = {
        "P": escape(str(colors.get("primary", "#7B3FF2"))),
        "A": escape(str(colors.get("accent", "#D9B64C"))),
        "T": escape(str(colors.get("text", "#F7F3FF"))),
        "M": escape(str(colors.get("muted", "#A99BBD"))),
    }
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">' + body.format(**tokens) + '</svg>'
    try:
        from PySide6.QtSvg import QSvgRenderer
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        if not renderer.isValid(): return QPixmap()
        pix = QPixmap(int(size), int(size)); pix.fill(Qt.transparent); painter = QPainter(pix); renderer.render(painter); painter.end(); return pix
    except Exception:
        return QPixmap()
