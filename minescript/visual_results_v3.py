from __future__ import annotations

"""Purpose-built visual output for seed/world and construction tool families."""

import math
from typing import Any


def _num(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _point_from(value, *, pair_is_xz=False):
    if isinstance(value, dict):
        for key in ("position", "block_center", "candidate_block_center", "nearest_border_point", "target_block", "midpoint"):
            if key in value:
                point = _point_from(value[key])
                if point is not None:
                    return point
        for key in ("chunk", "candidate_chunk", "reference_chunk", "center_chunk"):
            if key in value:
                raw = value[key]
                if isinstance(raw, (list, tuple)) and len(raw) >= 2:
                    x, z = _num(raw[0]), _num(raw[1])
                    if x is not None and z is not None:
                        return x * 16 + 8, z * 16 + 8
        x = _num(value.get("x")); z = _num(value.get("z"))
        if x is not None and z is not None:
            return x, z
        return None
    if isinstance(value, (list, tuple)):
        if pair_is_xz and len(value) >= 2:
            x, z = _num(value[0]), _num(value[1])
            return (x, z) if x is not None and z is not None else None
        if len(value) >= 3:
            x, z = _num(value[0]), _num(value[2])
            return (x, z) if x is not None and z is not None else None
        if len(value) >= 2:
            x, z = _num(value[0]), _num(value[1])
            return (x, z) if x is not None and z is not None else None
    return None


def _list_points(value, *, chunk_pairs=False, pair_is_xz=False, limit=1800):
    points = []
    if not isinstance(value, (list, tuple)):
        return points
    for row in value[:limit]:
        if chunk_pairs and isinstance(row, (list, tuple)) and len(row) >= 2:
            x, z = _num(row[0]), _num(row[1])
            if x is not None and z is not None:
                points.append((x * 16 + 8, z * 16 + 8))
                continue
        point = _point_from(row, pair_is_xz=pair_is_xz)
        if point is not None:
            points.append(point)
    return points


def seed_series(data: Any) -> tuple[list[tuple[str, list[tuple[float, float]]]], tuple[float, float] | None]:
    series: list[tuple[str, list[tuple[float, float]]]] = []
    center = None

    if isinstance(data, dict):
        for key in ("center_chunk", "reference_chunk"):
            raw = data.get(key)
            if isinstance(raw, (list, tuple)) and len(raw) >= 2:
                x, z = _num(raw[0]), _num(raw[1])
                if x is not None and z is not None:
                    center = (x * 16 + 8, z * 16 + 8)
                    break

    seen = set()
    def add(label, points):
        clean = []
        for point in points:
            key = (round(point[0], 5), round(point[1], 5))
            if key not in seen:
                seen.add(key); clean.append(point)
        if clean and len(series) < 7:
            series.append((str(label).replace("_", " ").title(), clean))

    def walk(node, parent="", depth=0):
        if depth > 6 or len(series) >= 7:
            return
        if isinstance(node, dict):
            # Common containers preserve the child key as the legend label.
            for key, value in node.items():
                low = str(key).lower()
                if low in {"candidate_sets", "structure_candidates", "structures"} and isinstance(value, dict):
                    for label, rows in value.items():
                        add(label, _list_points(rows, chunk_pairs=True))
                    continue
                if low in {"candidate_chunks", "slime_chunks", "chunks"}:
                    add(key, _list_points(value, chunk_pairs=True))
                    continue
                if low in {"nearest_samples", "biome_samples"}:
                    add(key, _list_points(value, pair_is_xz=True))
                    continue
                if low in {"hits", "targets", "ranked_sites", "suggested_first_stops", "compound_candidates"} and isinstance(value, list):
                    grouped: dict[str, list[tuple[float, float]]] = {}
                    for row in value:
                        if not isinstance(row, dict):
                            continue
                        point = _point_from(row)
                        if point is None:
                            continue
                        label = row.get("structure") or row.get("type") or row.get("spawner_kind") or row.get("anchor_type") or key
                        if row.get("mobs"):
                            label = "/".join(row.get("mobs") or [])
                        grouped.setdefault(str(label), []).append(point)
                    for label, points in grouped.items():
                        add(label, points)
                    if grouped:
                        continue
                if low in {"positions", "points", "vertices", "corners", "strand_a", "strand_b", "route_order"}:
                    add(key, _list_points(value))
                    continue
                if isinstance(value, (dict, list, tuple)):
                    walk(value, str(key), depth + 1)
        elif isinstance(node, (list, tuple)):
            points = _list_points(node)
            if points:
                add(parent or "Locations", points)

    walk(data)
    return series, center


def construction_series(spec, data: Any):
    series, _ = seed_series(data)
    if series:
        return series
    if not isinstance(data, dict):
        return []
    width = _num(data.get("width_blocks", data.get("width")))
    length = _num(data.get("length_blocks", data.get("length")))
    if width is not None and length is not None and width > 0 and length > 0:
        outline = [(0, 0), (width, 0), (width, length), (0, length), (0, 0)]
        return [("Footprint", outline)]
    radius = _num(data.get("radius_blocks", data.get("radius")))
    if radius is not None and radius > 0 and getattr(spec, "submenu", "") == "Shapes":
        points = [(radius * math.cos(i * math.tau / 96), radius * math.sin(i * math.tau / 96)) for i in range(97)]
        return [("Shape footprint", points)]
    return []


def install() -> None:
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import QFrame

    from . import visual_results
    from .ui_theme import palette

    if getattr(visual_results, "_rich_v3_installed", False):
        return
    old_attach = visual_results.attach_visual_preview

    class MapPreview(QFrame):
        def __init__(self, title, series, colors, center=None, parent=None):
            super().__init__(parent)
            self.title = title; self.series = series; self.colors = colors; self.center = center
            self.setObjectName("ResultSection")
            self.setMinimumHeight(360)

        def paintEvent(self, event):
            super().paintEvent(event)
            painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing, False)
            plot = self.rect().adjusted(18, 58, -18, -36)
            all_points = [point for _, points in self.series for point in points]
            if self.center is not None:
                all_points.append(self.center)
            if not all_points or plot.width() < 20 or plot.height() < 20:
                return
            xs = [p[0] for p in all_points]; zs = [p[1] for p in all_points]
            minx, maxx, minz, maxz = min(xs), max(xs), min(zs), max(zs)
            span = max(maxx - minx, maxz - minz, 32.0)
            midx, midz = (minx + maxx) / 2, (minz + maxz) / 2
            half = span * 0.56
            minx, maxx, minz, maxz = midx - half, midx + half, midz - half, midz + half
            painter.setPen(QColor(self.colors["text"]))
            font = painter.font(); font.setBold(True); font.setPointSizeF(max(font.pointSizeF(), 10.0)); painter.setFont(font)
            painter.drawText(18, 25, self.title)
            font.setBold(False); font.setPointSizeF(max(8.0, font.pointSizeF() - 1)); painter.setFont(font)
            painter.setPen(QPen(QColor(self.colors["border"]), 1))
            for i in range(6):
                x = plot.left() + plot.width() * i / 5
                y = plot.top() + plot.height() * i / 5
                painter.drawLine(int(x), plot.top(), int(x), plot.bottom())
                painter.drawLine(plot.left(), int(y), plot.right(), int(y))
            def map_point(point):
                x, z = point
                return QPointF(
                    plot.left() + (x - minx) / (maxx - minx) * plot.width(),
                    plot.bottom() - (z - minz) / (maxz - minz) * plot.height(),
                )
            colors = [self.colors["primary"], self.colors["accent"], self.colors["accent2"], self.colors["success"], self.colors["warning"], self.colors["danger"], self.colors["glow"]]
            legend_x = 20
            for index, (label, points) in enumerate(self.series):
                color = QColor(colors[index % len(colors)])
                painter.setPen(QPen(color, 1)); painter.setBrush(color)
                mapped = [map_point(point) for point in points]
                ordered = any(token in label.lower() for token in ("route", "outline", "footprint", "shape", "strand", "path"))
                if ordered and len(mapped) <= 900:
                    for a, b in zip(mapped, mapped[1:]): painter.drawLine(a, b)
                size = 7 if len(mapped) < 80 else 5 if len(mapped) < 400 else 3
                for point in mapped:
                    painter.drawRect(QRectF(point.x() - size/2, point.y() - size/2, size, size))
                painter.drawRect(QRectF(legend_x, 38, 8, 8))
                painter.setPen(QColor(self.colors["muted"])); painter.drawText(legend_x + 12, 47, f"{label} ({len(points)})")
                legend_x += min(180, 30 + len(label) * 7)
            if self.center is not None:
                point = map_point(self.center)
                painter.setPen(QPen(QColor(self.colors["text"]), 2))
                painter.drawLine(QPointF(point.x()-7, point.y()), QPointF(point.x()+7, point.y()))
                painter.drawLine(QPointF(point.x(), point.y()-7), QPointF(point.x(), point.y()+7))
            painter.setPen(QColor(self.colors["muted"]))
            painter.drawText(plot.left(), self.height() - 10, f"Block X {minx:.0f} … {maxx:.0f}   •   Block Z {minz:.0f} … {maxz:.0f}")

    def attach(result_view, spec, data, theme, custom_palette=None):
        colors = palette(theme, custom_palette)
        widget = None
        if getattr(spec, "top", "") == "Seed Tools":
            series, center = seed_series(data)
            if series:
                widget = MapPreview(f"{getattr(spec, 'name', 'Seed result')} — map", series, colors, center)
        elif getattr(spec, "top", "") in {"Calculators", "Wizards"} and getattr(spec, "submenu", "") in {"Build", "Shapes", "Farm", "Technical"}:
            series = construction_series(spec, data)
            if series:
                widget = MapPreview(f"{getattr(spec, 'name', 'Plan')} — visual plan", series, colors)
        if widget is not None:
            index = max(0, result_view.layout.count() - 1)
            result_view.layout.insertWidget(index, widget)
            return
        old_attach(result_view, spec, data, theme, custom_palette)

    visual_results.attach_visual_preview = attach
    visual_results._rich_v3_installed = True
