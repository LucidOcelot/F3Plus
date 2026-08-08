from __future__ import annotations

"""Original F3+ pixel-art UI assets.

The shapes use a deliberately small 16×16 grid and blocky shading so they sit
comfortably beside Minecraft textures without copying Mojang artwork.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap


def _luma(hex_color: str) -> float:
    c = QColor(hex_color)
    return 0.2126 * c.redF() + 0.7152 * c.greenF() + 0.0722 * c.blueF()


def _color(p: dict, key: str, fallback: str) -> QColor:
    value = p.get(key, fallback)
    c = QColor(value)
    return c if c.isValid() else QColor(fallback)


def _draw_rect(q: QPainter, x: int, y: int, w: int, h: int, c: QColor) -> None:
    q.fillRect(x, y, w, h, c)


def _outline_palette(p: dict) -> tuple[QColor, QColor, QColor, QColor, QColor, QColor]:
    outline = QColor("#17121D") if _luma(p.get("bg", "#000000")) > 0.45 else QColor("#050409")
    primary = _color(p, "primary", "#7B3FF2")
    secondary = _color(p, "primary2", "#5A27B5")
    accent = _color(p, "accent", "#D9B64C")
    blue = _color(p, "accent2", "#4388FF")
    text = _color(p, "text", "#F7F3FF")
    return outline, primary, secondary, accent, blue, text


def _flower(q: QPainter, p: dict) -> None:
    o,a,b,g,blue,t = _outline_palette(p)
    # Four square petals around a gold core; the stepped silhouette is intentional.
    for x,y,w,h in ((6,1,4,5),(6,10,4,5),(1,6,5,4),(10,6,5,4)):
        _draw_rect(q,x-1,y-1,w+2,h+2,o)
        _draw_rect(q,x,y,w,h,a)
    _draw_rect(q,5,5,6,6,o); _draw_rect(q,6,6,4,4,b)
    _draw_rect(q,7,7,2,2,g)
    _draw_rect(q,7,2,2,1,t); _draw_rect(q,2,7,1,2,t)
    _draw_rect(q,9,12,1,1,blue)


def _fruit(q: QPainter, p: dict) -> None:
    o,a,b,g,blue,t = _outline_palette(p)
    # Irregular clustered fruit with a short chorus-like stem.
    for x,y,w,h in ((5,3,6,2),(3,5,10,6),(5,11,6,2)):
        _draw_rect(q,x-1,y-1,w+2,h+2,o); _draw_rect(q,x,y,w,h,a)
    _draw_rect(q,4,6,2,4,b); _draw_rect(q,10,5,2,5,b)
    _draw_rect(q,6,4,2,2,t); _draw_rect(q,9,9,2,2,blue)
    _draw_rect(q,8,1,2,3,o); _draw_rect(q,8,1,1,2,g)


def _shulker(q: QPainter, p: dict, *, seed: bool=False) -> None:
    o,a,b,g,blue,t = _outline_palette(p)
    # Boxy shell, separated lid, and a bright eye slot.
    _draw_rect(q,2,8,12,7,o); _draw_rect(q,3,9,10,5,a)
    _draw_rect(q,3,3,10,6,o); _draw_rect(q,4,4,8,4,b)
    _draw_rect(q,5,8,6,2,o); _draw_rect(q,6,8,4,1,t)
    _draw_rect(q,7,10,2,2,g)
    _draw_rect(q,4,10,1,2,blue); _draw_rect(q,11,10,1,2,blue)
    if seed:
        _draw_rect(q,12,1,2,2,g); _draw_rect(q,13,3,1,2,blue); _draw_rect(q,10,2,2,1,blue)


def _calculator(q: QPainter, p: dict) -> None:
    o,a,b,g,blue,t = _outline_palette(p)
    _draw_rect(q,1,3,9,11,o); _draw_rect(q,2,4,7,9,b)
    _draw_rect(q,3,5,5,3,a)
    for x,y in ((3,9),(6,9),(3,11),(6,11)):_draw_rect(q,x,y,2,1,t)
    _draw_rect(q,12,5,2,7,o); _draw_rect(q,10,7,6,2,o)
    _draw_rect(q,12,6,1,5,g); _draw_rect(q,11,7,4,1,g)


def _arrow(q: QPainter, p: dict) -> None:
    _,_,_,g,blue,_ = _outline_palette(p)
    _draw_rect(q,9,3,2,8,blue); _draw_rect(q,7,5,6,2,blue); _draw_rect(q,11,1,2,2,g)


def _shield(q: QPainter, p: dict) -> None:
    o,a,_,g,_,t = _outline_palette(p)
    _draw_rect(q,3,2,10,2,o); _draw_rect(q,2,4,12,6,o); _draw_rect(q,4,10,8,3,o); _draw_rect(q,6,13,4,2,o)
    _draw_rect(q,4,3,8,2,a); _draw_rect(q,3,5,10,4,a); _draw_rect(q,5,9,6,3,a); _draw_rect(q,7,12,2,2,g)
    _draw_rect(q,7,5,2,5,t)


def _plant_block(q: QPainter, p: dict) -> None:
    o,a,b,g,blue,t = _outline_palette(p)
    _draw_rect(q,2,9,12,6,o); _draw_rect(q,3,10,10,4,b)
    _draw_rect(q,7,4,2,6,o); _draw_rect(q,7,4,1,5,a)
    _draw_rect(q,4,3,4,3,o); _draw_rect(q,5,4,2,1,a)
    _draw_rect(q,8,1,4,4,o); _draw_rect(q,9,2,2,2,a)
    _draw_rect(q,11,11,1,1,g); _draw_rect(q,4,11,1,1,blue)


def _rng(q: QPainter, p: dict) -> None:
    _fruit(q,p)
    _,_,_,g,blue,t = _outline_palette(p)
    for x,y in ((4,7),(7,9),(10,6)):
        _draw_rect(q,x,y,1,1,g)
    _draw_rect(q,12,2,1,3,blue); _draw_rect(q,11,3,3,1,blue); _draw_rect(q,12,3,1,1,t)


def _trade(q: QPainter, p: dict) -> None:
    _shulker(q,p)
    success = _color(p,"success","#58D69A"); o,*_ = _outline_palette(p)
    _draw_rect(q,11,1,3,4,o); _draw_rect(q,12,2,1,2,success)


def _utility(q: QPainter, p: dict) -> None:
    _shulker(q,p)
    _,_,_,g,blue,t = _outline_palette(p)
    _draw_rect(q,1,2,5,2,blue); _draw_rect(q,3,0,2,6,blue); _draw_rect(q,3,2,1,2,g)


def _app(q: QPainter, p: dict) -> None:
    _shulker(q,p)
    # Compact flower crest above the shell.
    _,a,b,g,blue,t = _outline_palette(p)
    _draw_rect(q,6,0,4,3,a); _draw_rect(q,4,1,3,3,b); _draw_rect(q,9,1,3,3,b)
    _draw_rect(q,7,1,2,2,g); _draw_rect(q,12,3,1,1,blue)


def icon_pixmap(kind: str, p: dict, size: int = 32) -> QPixmap:
    image = QImage(16,16,QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    q = QPainter(image)
    q.setRenderHint(QPainter.Antialiasing,False)
    key = str(kind or "chorus_flower").lower()
    if key in {"chorus_flower","home"}: _flower(q,p)
    elif key in {"chorus_fruit","seed"}: _fruit(q,p)
    elif key in {"shulker","automation"}: _shulker(q,p)
    elif key in {"shulker_seed","structure"}: _shulker(q,p,seed=True)
    elif key in {"chorus_calc","calculator"}: _calculator(q,p)
    elif key == "navigation": _flower(q,p); _arrow(q,p)
    elif key == "building": _plant_block(q,p)
    elif key == "rng": _rng(q,p)
    elif key == "villager": _trade(q,p)
    elif key == "guided": _flower(q,p); _arrow(q,p)
    elif key == "utilities": _utility(q,p)
    elif key == "safety": _shield(q,p)
    elif key == "app": _app(q,p)
    else: _flower(q,p)
    q.end()
    return QPixmap.fromImage(image).scaled(int(size),int(size),Qt.KeepAspectRatio,Qt.FastTransformation)

