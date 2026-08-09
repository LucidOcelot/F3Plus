from __future__ import annotations

"""Theme-aware visual previews for result families that are hard to read as text.

The preview never replaces exact result data. It adds a compact X/Z map or sequence
plot above the detailed cards/tables for structures, slime chunks, shapes, layouts,
world scans, generation samples, portal geometry, and RNG sequences.
"""

import math


SPATIAL_KEYS = (
    "candidate_chunks", "chunks", "points", "positions", "sample_positions",
    "nearest_samples", "corners", "vertices", "matches", "largest", "ranked",
    "strand_a", "strand_b", "boundary_segments", "portals", "waypoints",
)
PAIR_FIRST_KEYS = {"nearest_samples", "boundary_segments"}
SEQUENCE_KEYS = ("sequence", "rolls", "values", "samples")


def attach_visual_preview(result_view, spec, data, theme: str, custom_palette: dict | None = None) -> None:
    """Insert one useful visual preview before the ResultView's bottom stretch."""
    try:
        from .ui_theme import palette
        colors = palette(theme, custom_palette)
        series = _spatial_series(data)
        widget = None
        if series and sum(len(points) for _, points in series) >= 2:
            widget = _SpatialPreview(_preview_title(spec, "Spatial preview — X/Z"), series, colors)
        else:
            sequence = _numeric_sequence(data)
            if sequence and len(sequence) >= 2:
                widget = _SequencePreview(_preview_title(spec, "Sequence preview"), sequence, colors)
        if widget is None:
            return
        index = max(0, result_view.layout.count() - 1)
        result_view.layout.insertWidget(index, widget)
    except Exception:
        # Visuals are supplemental. A preview failure must never hide the exact result.
        return


def _preview_title(spec, fallback: str) -> str:
    name = getattr(spec, "name", "") if spec is not None else ""
    if name:
        return f"{name} — {fallback}"
    return fallback


def _number(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _point(value, *, pair_first: bool = False) -> tuple[float, float] | None:
    if isinstance(value, dict):
        for key in ("chunk", "position", "point", "nether", "overworld", "center"):
            if key in value:
                point = _point(value[key], pair_first=pair_first)
                if point is not None:
                    return point
        pairs = (("x", "z"), ("chunk_x", "chunk_z"), ("cx", "cz"), ("block_x", "block_z"))
        for x_key, z_key in pairs:
            x = _number(value.get(x_key))
            z = _number(value.get(z_key))
            if x is not None and z is not None:
                return x, z
        return None
    if isinstance(value, (list, tuple)):
        if pair_first and len(value) >= 2:
            x = _number(value[0])
            z = _number(value[1])
            if x is not None and z is not None:
                return x, z
        if len(value) >= 3:
            x = _number(value[0])
            z = _number(value[2])
            if x is not None and z is not None:
                return x, z
        if len(value) >= 2:
            x = _number(value[0])
            z = _number(value[1])
            if x is not None and z is not None:
                return x, z
    return None


def _collect_points(value, limit: int = 2400, *, pair_first: bool = False) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []

    def visit(node):
        if len(points) >= limit:
            return
        point = _point(node, pair_first=pair_first)
        if point is not None:
            points.append(point)
            return
        if isinstance(node, dict):
            for child in node.values():
                visit(child)
                if len(points) >= limit:
                    break
        elif isinstance(node, (list, tuple)):
            for child in node:
                visit(child)
                if len(points) >= limit:
                    break

    visit(value)
    return points


def _spatial_series(data) -> list[tuple[str, list[tuple[float, float]]]]:
    found: list[tuple[str, list[tuple[float, float]]]] = []

    def walk(node, depth: int = 0):
        if depth > 5 or len(found) >= 4:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                key_text = str(key).lower()
                if key_text in SPATIAL_KEYS:
                    points = _collect_points(value, pair_first=key_text in PAIR_FIRST_KEYS)
                    if len(points) >= 2:
                        found.append((str(key).replace("_", " ").title(), points))
                        if len(found) >= 4:
                            return
                if isinstance(value, (dict, list, tuple)):
                    walk(value, depth + 1)
        elif isinstance(node, (list, tuple)):
            for child in node[:32]:
                if isinstance(child, (dict, list, tuple)):
                    walk(child, depth + 1)
                    if len(found) >= 4:
                        return

    walk(data)
    if not found and isinstance(data, (list, tuple)):
        points = _collect_points(data)
        if len(points) >= 2:
            found.append(("Points", points))
    return found


def _numeric_sequence(data) -> list[float]:
    result: list[float] = []

    def walk(node, depth: int = 0):
        nonlocal result
        if result or depth > 5:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).lower() in SEQUENCE_KEYS and isinstance(value, (list, tuple)):
                    values = [_number(item) for item in value[:512]]
                    clean = [value for value in values if value is not None]
                    if len(clean) >= 2:
                        result = clean
                        return
                if isinstance(value, (dict, list, tuple)):
                    walk(value, depth + 1)
                    if result:
                        return
        elif isinstance(node, (list, tuple)):
            values = [_number(item) for item in node[:512]]
            clean = [value for value in values if value is not None]
            if len(clean) == len(node[:512]) and len(clean) >= 2:
                result = clean

    walk(data)
    return result


class _PreviewBase:
    pass


def _qt_classes():
    from PySide6.QtCore import Qt, QPointF, QRectF
    from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
    from PySide6.QtWidgets import QFrame
    return Qt, QPointF, QRectF, QColor, QPainter, QPainterPath, QPen, QFrame


try:
    Qt, QPointF, QRectF, QColor, QPainter, QPainterPath, QPen, QFrame = _qt_classes()

    class _SpatialPreview(QFrame):
        def __init__(self, title: str, series, colors, parent=None):
            super().__init__(parent)
            self.title = title
            self.series = series
            self.colors = colors
            self.setObjectName("ResultSection")
            self.setMinimumHeight(300)

        def paintEvent(self, event):
            super().paintEvent(event)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, False)
            area = self.rect().adjusted(18, 42, -18, -22)
            all_points = [point for _, points in self.series for point in points]
            if not all_points or area.width() <= 10 or area.height() <= 10:
                return
            xs = [point[0] for point in all_points]
            zs = [point[1] for point in all_points]
            min_x, max_x = min(xs), max(xs)
            min_z, max_z = min(zs), max(zs)
            if min_x == max_x:
                min_x -= 1; max_x += 1
            if min_z == max_z:
                min_z -= 1; max_z += 1
            pad_x = (max_x - min_x) * 0.05
            pad_z = (max_z - min_z) * 0.05
            min_x -= pad_x; max_x += pad_x
            min_z -= pad_z; max_z += pad_z

            painter.setPen(QPen(QColor(self.colors["border"]), 1))
            for index in range(1, 5):
                x = area.left() + area.width() * index / 5
                y = area.top() + area.height() * index / 5
                painter.drawLine(int(x), area.top(), int(x), area.bottom())
                painter.drawLine(area.left(), int(y), area.right(), int(y))

            painter.setPen(QColor(self.colors["text"]))
            font = painter.font(); font.setBold(True); painter.setFont(font)
            painter.drawText(18, 25, self.title)
            font.setBold(False); painter.setFont(font)
            painter.setPen(QColor(self.colors["muted"]))
            painter.drawText(area.left(), self.height() - 6, f"X {min_x:g} … {max_x:g}    Z {min_z:g} … {max_z:g}")

            series_colors = [self.colors["primary"], self.colors["accent"], self.colors["accent2"], self.colors["success"]]
            for series_index, (label, points) in enumerate(self.series):
                color = QColor(series_colors[series_index % len(series_colors)])
                painter.setPen(QPen(color, 1))
                painter.setBrush(color)
                mapped = []
                for x_value, z_value in points:
                    px = area.left() + (x_value - min_x) / (max_x - min_x) * area.width()
                    py = area.bottom() - (z_value - min_z) / (max_z - min_z) * area.height()
                    mapped.append(QPointF(px, py))
                if _looks_ordered(label) and len(mapped) <= 800:
                    for a, b in zip(mapped, mapped[1:]):
                        painter.drawLine(a, b)
                size = 5 if len(mapped) < 150 else 3 if len(mapped) < 800 else 2
                half = size / 2
                for point in mapped:
                    painter.drawRect(QRectF(point.x() - half, point.y() - half, size, size))

    class _SequencePreview(QFrame):
        def __init__(self, title: str, values: list[float], colors, parent=None):
            super().__init__(parent)
            self.title = title
            self.values = values[:512]
            self.colors = colors
            self.setObjectName("ResultSection")
            self.setMinimumHeight(260)

        def paintEvent(self, event):
            super().paintEvent(event)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            area = self.rect().adjusted(18, 42, -18, -22)
            if len(self.values) < 2 or area.width() <= 10 or area.height() <= 10:
                return
            lo, hi = min(self.values), max(self.values)
            if lo == hi:
                lo -= 1; hi += 1
            painter.setPen(QColor(self.colors["text"]))
            font = painter.font(); font.setBold(True); painter.setFont(font)
            painter.drawText(18, 25, self.title)
            painter.setPen(QPen(QColor(self.colors["border"]), 1))
            for index in range(1, 5):
                y = area.top() + area.height() * index / 5
                painter.drawLine(area.left(), int(y), area.right(), int(y))
            path = QPainterPath()
            for index, value in enumerate(self.values):
                x = area.left() + index / max(1, len(self.values) - 1) * area.width()
                y = area.bottom() - (value - lo) / (hi - lo) * area.height()
                if index == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            painter.setPen(QPen(QColor(self.colors["primary"]), 2))
            painter.drawPath(path)
            painter.setPen(QColor(self.colors["muted"]))
            painter.drawText(area.left(), self.height() - 6, f"{len(self.values)} values    {lo:g} … {hi:g}")

except Exception:
    class _SpatialPreview(_PreviewBase):
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Qt is unavailable")

    class _SequencePreview(_PreviewBase):
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Qt is unavailable")


def _looks_ordered(label: str) -> bool:
    low = label.lower()
    return any(token in low for token in ("route", "path", "strand", "vertices", "corners", "boundary"))
