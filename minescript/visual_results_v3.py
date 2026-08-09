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
                seen.add(key)
                clean.append(point)
        if clean and len(series) < 7:
            series.append((str(label).replace("_", " ").title(), clean))

    def walk(node, parent="", depth=0):
        if depth > 6 or len(series) >= 7:
            return
        if isinstance(node, dict):
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


def visual_ui_capabilities() -> tuple[str, ...]:
    """Stable capability list used by docs/regression tests."""
    return (
        "wheel zoom",
        "drag pan",
        "fit to data",
        "series visibility",
        "grid toggle",
        "point labels",
        "cursor coordinates",
        "copy visible coordinates",
    )


def install() -> None:
    from PySide6.QtCore import QPointF, QRectF, QTimer, Qt
    from PySide6.QtGui import QColor, QBrush, QPainter, QPainterPath, QPen
    from PySide6.QtWidgets import (
        QApplication, QCheckBox, QFrame, QGraphicsEllipseItem, QGraphicsItem,
        QGraphicsItemGroup, QGraphicsLineItem, QGraphicsPathItem, QGraphicsScene,
        QGraphicsSimpleTextItem, QGraphicsView, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QSplitter, QVBoxLayout, QWidget,
    )

    from . import visual_results
    from .ui_theme import palette

    if getattr(visual_results, "_rich_v3_installed", False):
        return
    old_attach = visual_results.attach_visual_preview

    class PlotView(QGraphicsView):
        def __init__(self, scene, status_callback, parent=None):
            super().__init__(scene, parent)
            self._status_callback = status_callback
            self.setRenderHint(QPainter.Antialiasing, False)
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
            self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
            self.setMouseTracking(True)
            self.setMinimumSize(520, 330)

        def wheelEvent(self, event):
            factor = 1.18 if event.angleDelta().y() > 0 else 1 / 1.18
            self.scale(factor, factor)
            event.accept()

        def mouseMoveEvent(self, event):
            point = self.mapToScene(event.pos())
            self._status_callback(point.x(), point.y())
            super().mouseMoveEvent(event)

    class MapPreview(QFrame):
        def __init__(self, title, series, colors, center=None, parent=None):
            super().__init__(parent)
            self.title = str(title)
            self.series = [(str(label), list(points)) for label, points in series if points]
            self.colors = colors
            self.center = center
            self._series_groups: list[tuple[str, list[tuple[float, float]], QGraphicsItemGroup]] = []
            self._grid_group = None
            self.setObjectName("ResultSection")
            self.setMinimumHeight(470)

            outer = QVBoxLayout(self)
            outer.setContentsMargins(10, 9, 10, 10)
            outer.setSpacing(7)

            top = QHBoxLayout()
            heading = QLabel(self.title)
            heading.setObjectName("WorkspaceTitle")
            top.addWidget(heading, 1)
            badge = QLabel("INTERACTIVE X/Z VIEW")
            badge.setObjectName("VersionChip")
            badge.setToolTip("All plotted seed/world coordinates share block X/Z units. Construction plans use their local block-coordinate frame.")
            top.addWidget(badge)
            outer.addLayout(top)

            toolbar = QHBoxLayout()
            self.fit_button = QPushButton("Fit")
            self.zoom_in_button = QPushButton("+")
            self.zoom_out_button = QPushButton("−")
            self.grid_toggle = QCheckBox("Grid")
            self.grid_toggle.setChecked(True)
            self.labels_toggle = QCheckBox("Point labels")
            for button in (self.fit_button, self.zoom_in_button, self.zoom_out_button):
                button.setObjectName("SegmentButton")
            self.fit_button.setToolTip("Fit all visible plotted data in the viewport.")
            self.zoom_in_button.setToolTip("Zoom in. Mouse-wheel zoom is also supported.")
            self.zoom_out_button.setToolTip("Zoom out. Drag the map to pan.")
            self.grid_toggle.setToolTip("Show or hide the scale grid.")
            self.labels_toggle.setToolTip("Label a limited number of points with their X/Z coordinates.")
            toolbar.addWidget(self.fit_button)
            toolbar.addWidget(self.zoom_in_button)
            toolbar.addWidget(self.zoom_out_button)
            toolbar.addSpacing(8)
            toolbar.addWidget(self.grid_toggle)
            toolbar.addWidget(self.labels_toggle)
            toolbar.addStretch(1)
            help_text = QLabel("Wheel: zoom  •  Drag: pan  •  +X east  •  +Z south")
            help_text.setObjectName("Muted")
            toolbar.addWidget(help_text)
            outer.addLayout(toolbar)

            splitter = QSplitter(Qt.Horizontal)
            splitter.setChildrenCollapsible(False)
            outer.addWidget(splitter, 1)

            self.scene = QGraphicsScene(self)
            self.scene.setBackgroundBrush(QBrush(QColor(self.colors["surface2"])))
            self.cursor_label = QLabel("Move over the view to inspect block coordinates.")
            self.cursor_label.setObjectName("Muted")
            self.view = PlotView(self.scene, self._cursor_moved)
            splitter.addWidget(self.view)

            side_scroll = QScrollArea()
            side_scroll.setWidgetResizable(True)
            side_scroll.setFrameShape(QFrame.NoFrame)
            side = QWidget()
            side_layout = QVBoxLayout(side)
            side_layout.setContentsMargins(8, 5, 6, 5)
            side_layout.setSpacing(6)
            legend_title = QLabel("LAYERS")
            legend_title.setObjectName("DeckLabel")
            side_layout.addWidget(legend_title)
            self.legend_layout = side_layout
            self.layer_checks: list[QCheckBox] = []
            self.bounds_label = QLabel()
            self.bounds_label.setObjectName("Muted")
            self.bounds_label.setWordWrap(True)
            self.copy_button = QPushButton("Copy visible coordinates")
            self.copy_button.setToolTip("Copy all currently visible plotted points as tab-separated X/Z block coordinates.")
            side_layout.addStretch(1)
            side_layout.addWidget(self.bounds_label)
            side_layout.addWidget(self.copy_button)
            side_scroll.setWidget(side)
            splitter.addWidget(side_scroll)
            splitter.setSizes([760, 230])

            outer.addWidget(self.cursor_label)

            self.fit_button.clicked.connect(self.fit_to_data)
            self.zoom_in_button.clicked.connect(lambda: self.view.scale(1.25, 1.25))
            self.zoom_out_button.clicked.connect(lambda: self.view.scale(0.8, 0.8))
            self.grid_toggle.toggled.connect(self._set_grid_visible)
            self.labels_toggle.toggled.connect(self._rebuild_scene)
            self.copy_button.clicked.connect(self._copy_visible)

            self._rebuild_scene()
            QTimer.singleShot(0, self.fit_to_data)

        def _cursor_moved(self, x, z):
            self.cursor_label.setText(f"Cursor: X {x:,.1f}   Z {z:,.1f} blocks")

        def _ordered(self, label: str) -> bool:
            low = label.lower()
            return any(token in low for token in ("route", "outline", "footprint", "shape", "strand", "path", "span"))

        def _all_points(self):
            points = [point for _, rows in self.series for point in rows]
            if self.center is not None:
                points.append(self.center)
            return points

        def _bounds(self):
            points = self._all_points()
            if not points:
                return (-16.0, 16.0, -16.0, 16.0)
            xs = [p[0] for p in points]
            zs = [p[1] for p in points]
            return min(xs), max(xs), min(zs), max(zs)

        @staticmethod
        def _grid_step(span: float) -> float:
            span = max(1.0, float(span))
            raw = span / 8.0
            power = 10 ** math.floor(math.log10(raw))
            normalized = raw / power
            factor = 1 if normalized <= 1 else 2 if normalized <= 2 else 5 if normalized <= 5 else 10
            return max(1.0, factor * power)

        def _new_grid(self, minx, maxx, minz, maxz):
            group = QGraphicsItemGroup()
            span = max(maxx - minx, maxz - minz, 32.0)
            pad = span * 0.08
            minx -= pad; maxx += pad; minz -= pad; maxz += pad
            step = self._grid_step(span)
            pen = QPen(QColor(self.colors["border"]), 0)
            x = math.floor(minx / step) * step
            while x <= maxx:
                item = QGraphicsLineItem(x, minz, x, maxz)
                item.setPen(pen)
                group.addToGroup(item)
                x += step
            z = math.floor(minz / step) * step
            while z <= maxz:
                item = QGraphicsLineItem(minx, z, maxx, z)
                item.setPen(pen)
                group.addToGroup(item)
                z += step
            group.setZValue(-100)
            self.scene.addItem(group)
            return group, step

        def _rebuild_scene(self):
            visibility = [check.isChecked() for check in self.layer_checks]
            self.scene.clear()
            self._series_groups = []
            for check in self.layer_checks:
                check.deleteLater()
            self.layer_checks = []

            minx, maxx, minz, maxz = self._bounds()
            self._grid_group, step = self._new_grid(minx, maxx, minz, maxz)
            self._grid_group.setVisible(self.grid_toggle.isChecked())

            palette_keys = ["primary", "accent", "accent2", "success", "warning", "danger", "glow"]
            for index, (label, points) in enumerate(self.series):
                color = QColor(self.colors[palette_keys[index % len(palette_keys)]])
                group = QGraphicsItemGroup()
                group.setZValue(10 + index)
                ordered = self._ordered(label)
                if ordered and len(points) > 1 and len(points) <= 1000:
                    path = QPainterPath(QPointF(points[0][0], points[0][1]))
                    for x, z in points[1:]:
                        path.lineTo(QPointF(x, z))
                    path_item = QGraphicsPathItem(path)
                    path_item.setPen(QPen(color, 1.5))
                    group.addToGroup(path_item)

                point_size = 8.0 if len(points) < 80 else 5.0 if len(points) < 400 else 3.0
                for point_index, (x, z) in enumerate(points):
                    dot = QGraphicsEllipseItem(QRectF(x - point_size / 2, z - point_size / 2, point_size, point_size))
                    dot.setPen(QPen(color, 0))
                    dot.setBrush(QBrush(color))
                    dot.setToolTip(f"{label}\nX {x:,.1f}\nZ {z:,.1f}")
                    group.addToGroup(dot)
                    if self.labels_toggle.isChecked() and point_index < 20:
                        text = QGraphicsSimpleTextItem(f"{x:.0f}, {z:.0f}")
                        text.setBrush(QBrush(QColor(self.colors["text"])))
                        text.setPos(x + point_size, z + point_size)
                        text.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
                        group.addToGroup(text)
                self.scene.addItem(group)
                self._series_groups.append((label, points, group))

                check = QCheckBox(f"{label} ({len(points):,})")
                check.setChecked(visibility[index] if index < len(visibility) else True)
                check.setToolTip("Toggle this plotted layer without changing the underlying result.")
                check.toggled.connect(group.setVisible)
                group.setVisible(check.isChecked())
                self.legend_layout.insertWidget(len(self.layer_checks) + 1, check)
                self.layer_checks.append(check)

            if self.center is not None:
                x, z = self.center
                center_group = QGraphicsItemGroup()
                pen = QPen(QColor(self.colors["text"]), 2)
                center_group.addToGroup(QGraphicsLineItem(x - 10, z, x + 10, z))
                center_group.addToGroup(QGraphicsLineItem(x, z - 10, x, z + 10))
                for child in center_group.childItems():
                    if hasattr(child, "setPen"):
                        child.setPen(pen)
                center_group.setToolTip(f"Search/reference center\nX {x:,.1f}\nZ {z:,.1f}")
                center_group.setZValue(100)
                self.scene.addItem(center_group)

            span = max(maxx - minx, maxz - minz, 0.0)
            self.bounds_label.setText(
                f"Bounds\nX {minx:,.0f} … {maxx:,.0f}\nZ {minz:,.0f} … {maxz:,.0f}\nGrid ≈ {step:,.0f} blocks\nSpan ≈ {span:,.0f} blocks"
            )
            self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-16, -16, 16, 16))

        def _set_grid_visible(self, visible):
            if self._grid_group is not None:
                self._grid_group.setVisible(bool(visible))

        def fit_to_data(self):
            rect = self.scene.itemsBoundingRect()
            if rect.isValid() and rect.width() > 0 and rect.height() > 0:
                self.view.fitInView(rect.adjusted(-12, -12, 12, 12), Qt.KeepAspectRatio)

        def _copy_visible(self):
            lines = ["Layer\tBlock X\tBlock Z"]
            for label, points, group in self._series_groups:
                if not group.isVisible():
                    continue
                for x, z in points:
                    lines.append(f"{label}\t{x:g}\t{z:g}")
            QApplication.clipboard().setText("\n".join(lines))
            self.cursor_label.setText(f"Copied {max(0, len(lines) - 1):,} visible coordinate rows to the clipboard.")

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
    visual_results.MapPreview = MapPreview
    visual_results._rich_v3_installed = True
