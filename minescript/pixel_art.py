from __future__ import annotations

"""Compatibility icon API for original F3+ artwork.

The early 2.x UI used a small hard-coded pixel-art switch. F3+ now uses recolorable
semantic SVG libraries while keeping ``icon_pixmap`` stable for existing callers.
Installed Minecraft textures are still attempted by callers first.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap

from .semantic_icons_extra import icon_pixmap as _canonical_pixmap
from .vector_icons import icon_pixmap as _vector_pixmap


def icon_pixmap(kind: str, p: dict, size: int = 32) -> QPixmap:
    pix = _canonical_pixmap(kind, p, size)
    if not pix.isNull(): return pix
    pix = _vector_pixmap(kind, p, size)
    if not pix.isNull(): return pix

    # Deliberately simple original fallback for an unknown semantic key. Unknown tools
    # should remain visibly generic rather than silently borrowing an unrelated icon.
    image = QImage(24, 24, QImage.Format_ARGB32_Premultiplied); image.fill(Qt.transparent)
    painter = QPainter(image); painter.setRenderHint(QPainter.Antialiasing, True)
    primary = QColor(str(p.get("primary", "#7B3FF2"))); accent = QColor(str(p.get("accent", "#D9B64C")))
    painter.setPen(primary); painter.setBrush(Qt.NoBrush); painter.drawRoundedRect(3, 3, 18, 18, 3, 3)
    painter.setBrush(accent); painter.setPen(Qt.NoPen); painter.drawEllipse(9, 9, 6, 6); painter.end()
    return QPixmap.fromImage(image).scaled(int(size), int(size), Qt.KeepAspectRatio, Qt.SmoothTransformation)
