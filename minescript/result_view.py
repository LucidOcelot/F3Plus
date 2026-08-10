from __future__ import annotations

"""Reusable structured result surface for canonical F3+ workbenches.

The canonical rewrite briefly routed most operations into a QTextBrowser dump even
though the project still produced structured data.  This widget keeps the structured
result authoritative while presenting it as cards/tables and restoring interactive
spatial/graph previews where the result contains meaningful visual data.
"""

import json
import math
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QGraphicsEllipseItem, QGraphicsItemGroup,
    QGraphicsLineItem, QGraphicsPathItem, QGraphicsScene, QGraphicsSimpleTextItem,
    QGraphicsView, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QPlainTextEdit,
    QPushButton, QScrollArea, QSplitter, QTableWidget, QTableWidgetItem,
    QToolButton, QVBoxLayout, QWidget,
)

from .structured_results import _presentation_data
from .ui_theme import palette
from .visual_data import construction_series, seed_series


_INTERNAL_KEYS = {
    "_contract", "_display", "_source_contract", "_exactness_contract",
}


def _scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _friendly_key(value: str) -> str:
    return str(value).replace("_", " ").strip().title()


def _text(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        return f"{value:,.6g}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _source_label(data: Any) -> str:
    if not isinstance(data, dict):
        return "F3+ calculation"
    worldgen = data.get("worldgen_source")
    if isinstance(worldgen, dict) and worldgen.get("source"):
        return str(worldgen["source"])
    for key in ("source", "data_source", "trade_source", "backend", "implementation"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if data.get("requires_generated_world"):
        return "Generated Java world required"
    return "F3+ calculation/model"


def _exactness_label(data: Any, source: str) -> str:
    if not isinstance(data, dict):
        return "Calculated"
    for key in ("exactness", "accuracy", "model_exactness"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    low = source.lower()
    if data.get("available") is False:
        return "Unavailable"
    if "mojang server" in low or "observed generated" in low:
        return "Exact / observed"
    if "installed minecraft" in low:
        return "Installed-version data"
    if "baseline" in low or "reference" in low:
        return "Reference / model"
    return "Calculated"


def _spatial_series(spec, data: Any):
    series, center = seed_series(data)
    if not series and getattr(spec, "top", "") in {"Calculators", "Wizards"}:
        series = construction_series(spec, data)
    return series, center


def _numeric_series(data: Any, depth: int = 0):
    """Find one useful numeric sequence/category set without inventing data."""
    if depth > 5:
        return None
    if isinstance(data, dict):
        # Prefer named numeric arrays: RNG sequences, histograms, distributions, rates.
        preferred = (
            "sequence", "rolls", "values", "samples", "distribution", "counts",
            "frequencies", "histogram", "rates", "percentages", "levels",
        )
        lowered = {str(k).lower(): k for k in data}
        for wanted in preferred:
            key = lowered.get(wanted)
            if key is None:
                continue
            value = data[key]
            if isinstance(value, (list, tuple)):
                nums = [float(v) for v in value if isinstance(v, (int, float)) and not isinstance(v, bool)]
                if len(nums) >= 2 and len(nums) == len(value):
                    return str(key), [(str(i + 1), number) for i, number in enumerate(nums[:512])], "line"
            if isinstance(value, dict):
                rows = [(str(k), float(v)) for k, v in value.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
                if len(rows) >= 2:
                    return str(key), rows[:96], "bars"
        # A dictionary whose values are numeric is usually a category distribution.
        rows = [(str(k), float(v)) for k, v in data.items() if k not in _INTERNAL_KEYS and isinstance(v, (int, float)) and not isinstance(v, bool)]
        if 2 <= len(rows) <= 96:
            return "Distribution", rows, "bars"
        for key, value in data.items():
            if isinstance(value, (dict, list, tuple)):
                found = _numeric_series(value, depth + 1)
                if found:
                    return found
    elif isinstance(data, (list, tuple)):
        nums = [float(v) for v in data if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if len(nums) >= 2 and len(nums) == len(data):
            return "Values", [(str(i + 1), number) for i, number in enumerate(nums[:512])], "line"
        for value in data[:24]:
            if isinstance(value, (dict, list, tuple)):
                found = _numeric_series(value, depth + 1)
                if found:
                    return found
    return None


class _MapView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, cursor_label: QLabel, parent=None):
        super().__init__(scene, parent)
        self.cursor_label = cursor_label
        self.setRenderHint(QPainter.Antialiasing, False)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setMouseTracking(True)
        self.setMinimumHeight(330)

    def wheelEvent(self, event):
        factor = 1.18 if event.angleDelta().y() > 0 else 1 / 1.18
        self.scale(factor, factor)
        event.accept()

    def mouseMoveEvent(self, event):
        point = self.mapToScene(event.pos())
        self.cursor_label.setText(f"Cursor: X {point.x():,.1f}   Z {point.y():,.1f} blocks")
        super().mouseMoveEvent(event)


class InteractiveMap(QFrame):
    def __init__(self, title: str, series, colors, center=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ResultSection")
        self.series = [(str(label), list(points)) for label, points in series if points]
        self.colors = colors
        self.center = center
        self.groups: list[tuple[str, list[tuple[float, float]], QGraphicsItemGroup]] = []
        self.layer_checks: list[QCheckBox] = []
        self.grid_group = None

        root = QVBoxLayout(self); root.setContentsMargins(10, 9, 10, 10); root.setSpacing(7)
        head = QHBoxLayout(); heading = QLabel(title); heading.setObjectName("WorkspaceTitle"); head.addWidget(heading, 1)
        badge = QLabel("INTERACTIVE X/Z VIEW"); badge.setObjectName("VersionChip"); head.addWidget(badge); root.addLayout(head)

        tools = QHBoxLayout()
        self.fit_btn = QPushButton("Fit"); self.zoom_in = QPushButton("+"); self.zoom_out = QPushButton("−")
        self.grid = QCheckBox("Grid"); self.grid.setChecked(True); self.labels = QCheckBox("Point labels")
        for button in (self.fit_btn, self.zoom_in, self.zoom_out): button.setObjectName("SegmentButton")
        tools.addWidget(self.fit_btn); tools.addWidget(self.zoom_in); tools.addWidget(self.zoom_out); tools.addSpacing(8); tools.addWidget(self.grid); tools.addWidget(self.labels); tools.addStretch()
        hint = QLabel("Wheel: zoom  •  Drag: pan  •  +X east  •  +Z south"); hint.setObjectName("Muted"); tools.addWidget(hint); root.addLayout(tools)

        split = QSplitter(Qt.Horizontal); split.setChildrenCollapsible(False); root.addWidget(split, 1)
        self.scene = QGraphicsScene(self); self.scene.setBackgroundBrush(QBrush(QColor(colors["surface2"])))
        self.cursor = QLabel("Move over the map to inspect block coordinates."); self.cursor.setObjectName("Muted")
        self.view = _MapView(self.scene, self.cursor); split.addWidget(self.view)
        side_scroll = QScrollArea(); side_scroll.setWidgetResizable(True); side_scroll.setFrameShape(QFrame.NoFrame)
        side = QWidget(); self.side = QVBoxLayout(side); self.side.setContentsMargins(7, 4, 7, 4); self.side.addWidget(QLabel("LAYERS"))
        self.bounds = QLabel(); self.bounds.setWordWrap(True); self.bounds.setObjectName("Muted")
        self.copy_btn = QPushButton("Copy visible coordinates")
        self.side.addStretch(); self.side.addWidget(self.bounds); self.side.addWidget(self.copy_btn); side_scroll.setWidget(side); split.addWidget(side_scroll); split.setSizes([760, 240])
        root.addWidget(self.cursor)

        self.fit_btn.clicked.connect(self.fit_to_data); self.zoom_in.clicked.connect(lambda: self.view.scale(1.25, 1.25)); self.zoom_out.clicked.connect(lambda: self.view.scale(.8, .8))
        self.grid.toggled.connect(self._toggle_grid); self.labels.toggled.connect(self.rebuild); self.copy_btn.clicked.connect(self.copy_visible)
        self.rebuild(); self.fit_to_data()

    def _bounds(self):
        points = [p for _, rows in self.series for p in rows]
        if self.center is not None: points.append(self.center)
        if not points: return -16.0, 16.0, -16.0, 16.0
        xs = [p[0] for p in points]; zs = [p[1] for p in points]
        return min(xs), max(xs), min(zs), max(zs)

    @staticmethod
    def _grid_step(span: float):
        span = max(1.0, span); raw = span / 8.0; power = 10 ** math.floor(math.log10(raw)); n = raw / power
        factor = 1 if n <= 1 else 2 if n <= 2 else 5 if n <= 5 else 10
        return max(1.0, factor * power)

    def rebuild(self):
        visibility = [check.isChecked() for check in self.layer_checks]
        for check in self.layer_checks: check.deleteLater()
        self.layer_checks = []; self.scene.clear(); self.groups = []
        minx, maxx, minz, maxz = self._bounds(); span = max(maxx - minx, maxz - minz, 32.0); pad = span * .08
        minx -= pad; maxx += pad; minz -= pad; maxz += pad
        step = self._grid_step(span); grid = QGraphicsItemGroup(); grid_pen = QPen(QColor(self.colors["border"]), 0)
        x = math.floor(minx / step) * step
        while x <= maxx:
            line = QGraphicsLineItem(x, minz, x, maxz); line.setPen(grid_pen); grid.addToGroup(line); x += step
        z = math.floor(minz / step) * step
        while z <= maxz:
            line = QGraphicsLineItem(minx, z, maxx, z); line.setPen(grid_pen); grid.addToGroup(line); z += step
        grid.setZValue(-100); self.scene.addItem(grid); self.grid_group = grid; grid.setVisible(self.grid.isChecked())

        color_keys = ["primary", "accent", "accent2", "success", "warning", "danger", "glow"]
        for index, (label, points) in enumerate(self.series):
            color = QColor(self.colors[color_keys[index % len(color_keys)]])
            group = QGraphicsItemGroup(); pen = QPen(color, 0); brush = QBrush(color)
            ordered = any(token in label.lower() for token in ("route", "path", "outline", "footprint", "shape", "strand", "boundary", "corner"))
            if ordered and len(points) >= 2:
                path = QPainterPath(QPointF(points[0][0], points[0][1]))
                for px, pz in points[1:]: path.lineTo(px, pz)
                item = QGraphicsPathItem(path); item.setPen(QPen(color, 1.4)); group.addToGroup(item)
            radius = max(1.8, min(5.0, span / 170.0))
            for point_index, (px, pz) in enumerate(points):
                dot = QGraphicsEllipseItem(QRectF(px - radius / 2, pz - radius / 2, radius, radius)); dot.setPen(pen); dot.setBrush(brush); group.addToGroup(dot)
                if self.labels.isChecked() and point_index < 80:
                    text = QGraphicsSimpleTextItem(f"{px:g}, {pz:g}"); text.setBrush(brush); text.setPos(px + radius, pz + radius); text.setFlag(QGraphicsSimpleTextItem.ItemIgnoresTransformations, True); group.addToGroup(text)
            self.scene.addItem(group); self.groups.append((label, points, group))
            check = QCheckBox(f"{label} ({len(points):,})"); check.setChecked(visibility[index] if index < len(visibility) else True)
            check.toggled.connect(group.setVisible); self.side.insertWidget(1 + index, check); self.layer_checks.append(check)

        if self.center is not None:
            cx, cz = self.center; color = QColor(self.colors["text"]); marker = QGraphicsEllipseItem(QRectF(cx - 4, cz - 4, 8, 8)); marker.setPen(QPen(color, 1)); self.scene.addItem(marker)
        self.scene.setSceneRect(QRectF(minx, minz, maxx - minx, maxz - minz)); self.bounds.setText(f"X {minx:,.0f} … {maxx:,.0f}\nZ {minz:,.0f} … {maxz:,.0f}\nGrid {step:g} blocks")

    def _toggle_grid(self, visible: bool):
        if self.grid_group is not None: self.grid_group.setVisible(visible)

    def fit_to_data(self):
        rect = self.scene.itemsBoundingRect()
        if rect.isValid() and rect.width() > 0 and rect.height() > 0:
            self.view.fitInView(rect.adjusted(-8, -8, 8, 8), Qt.KeepAspectRatio)

    def copy_visible(self):
        lines = ["layer\tx\tz"]
        for label, points, group in self.groups:
            if not group.isVisible(): continue
            lines.extend(f"{label}\t{x:g}\t{z:g}" for x, z in points)
        QApplication.clipboard().setText("\n".join(lines))


class NumericChart(QFrame):
    def __init__(self, title: str, rows: list[tuple[str, float]], kind: str, colors, parent=None):
        super().__init__(parent); self.title = title; self.rows = rows; self.kind = kind; self.colors = colors
        self.setObjectName("ResultSection"); self.setMinimumHeight(290)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.rows: return
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing, True)
        area = self.rect().adjusted(48, 42, -20, -46); values = [row[1] for row in self.rows]
        lo = min(values); hi = max(values)
        if self.kind == "bars": lo = min(0.0, lo)
        if lo == hi: lo -= 1; hi += 1
        painter.setPen(QColor(self.colors["text"])); font = painter.font(); font.setBold(True); painter.setFont(font); painter.drawText(16, 25, _friendly_key(self.title))
        font.setBold(False); painter.setFont(font); painter.setPen(QPen(QColor(self.colors["border"]), 1))
        for i in range(5):
            y = area.top() + area.height() * i / 4; painter.drawLine(area.left(), int(y), area.right(), int(y))
        color = QColor(self.colors["primary"]); painter.setPen(QPen(color, 2)); painter.setBrush(QBrush(color))
        if self.kind == "line":
            path = QPainterPath()
            for index, (_, value) in enumerate(self.rows):
                x = area.left() + index / max(1, len(self.rows) - 1) * area.width(); y = area.bottom() - (value - lo) / (hi - lo) * area.height()
                if index == 0: path.moveTo(x, y)
                else: path.lineTo(x, y)
            painter.drawPath(path)
        else:
            width = area.width() / max(1, len(self.rows)); baseline = area.bottom() - (0 - lo) / (hi - lo) * area.height()
            for index, (label, value) in enumerate(self.rows):
                x = area.left() + index * width + width * .12; y = area.bottom() - (value - lo) / (hi - lo) * area.height(); rect = QRectF(x, min(y, baseline), max(1.0, width * .76), abs(baseline - y)); painter.drawRect(rect)
                if len(self.rows) <= 18:
                    painter.save(); painter.translate(x + width * .35, area.bottom() + 8); painter.rotate(-45); painter.setPen(QColor(self.colors["muted"])); painter.drawText(0, 0, str(label)[:18]); painter.restore()
        painter.setPen(QColor(self.colors["muted"])); painter.drawText(area.left(), self.height() - 8, f"{len(self.rows)} values   {lo:g} … {hi:g}")


def _make_table(rows: list[list[str]], headers: list[str]) -> QTableWidget:
    table = QTableWidget(len(rows), len(headers)); table.setHorizontalHeaderLabels(headers); table.verticalHeader().setVisible(False); table.setAlternatingRowColors(True); table.setEditTriggers(QTableWidget.NoEditTriggers)
    for r, row in enumerate(rows):
        for c, value in enumerate(row[:len(headers)]): table.setItem(r, c, QTableWidgetItem(value))
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    if headers: table.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.Stretch)
    table.setMinimumHeight(min(420, max(90, 34 + 28 * min(len(rows), 12))))
    return table


class ResultView(QWidget):
    """Structured, visual result renderer used inside canonical workbench dialogs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.NoFrame); outer.addWidget(self.scroll)
        self.host = QWidget(); self.layout = QVBoxLayout(self.host); self.layout.setContentsMargins(8, 8, 8, 8); self.layout.setSpacing(10); self.scroll.setWidget(self.host)
        self._raw: QPlainTextEdit | None = None
        self.show_empty("Run an operation to see its result here.")

    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0); widget = item.widget()
            if widget is not None: widget.deleteLater()
        self._raw = None

    def show_empty(self, text: str):
        self.clear(); label = QLabel(text); label.setWordWrap(True); label.setObjectName("Muted"); self.layout.addWidget(label); self.layout.addStretch()

    def set_result(self, spec, result, theme: str = "chorus", custom_palette: dict | None = None):
        self.clear(); colors = palette(theme, custom_palette); data = getattr(result, "data", result); visible = _presentation_data(data); source = _source_label(data); exactness = _exactness_label(data, source); status = str(getattr(result, "status", "ok")); note = str(getattr(result, "note", "") or "")

        hero = QFrame(); hero.setObjectName("ResultCard"); hv = QVBoxLayout(hero); title = QLabel(getattr(spec, "name", "Result")); title.setObjectName("WorkspaceTitle"); hv.addWidget(title)
        badges = QHBoxLayout()
        for text in (f"Status: {status}", f"Exactness: {exactness}", f"Source: {source}"):
            label = QLabel(text); label.setObjectName("VersionChip"); label.setWordWrap(True); badges.addWidget(label)
        badges.addStretch(); hv.addLayout(badges); self.layout.addWidget(hero)
        if note:
            banner = QFrame(); banner.setObjectName("WarningBanner"); box = QVBoxLayout(banner); n = QLabel(note); n.setWordWrap(True); box.addWidget(n); self.layout.addWidget(banner)

        series, center = _spatial_series(spec, visible)
        if series:
            self.layout.addWidget(InteractiveMap(f"{getattr(spec, 'name', 'Result')} — map", series, colors, center))
        numeric = _numeric_series(visible)
        if numeric and not series:
            name, rows, kind = numeric; self.layout.addWidget(NumericChart(name, rows, kind, colors))

        self._render_value("Result", visible, depth=0)
        raw_toggle = QToolButton(); raw_toggle.setText("Raw structured data"); raw_toggle.setCheckable(True); raw_toggle.setArrowType(Qt.RightArrow); self.layout.addWidget(raw_toggle)
        raw = QPlainTextEdit(); raw.setReadOnly(True); raw.setPlainText(json.dumps(visible, indent=2, ensure_ascii=False, default=str)); raw.setMaximumHeight(360); raw.hide(); self.layout.addWidget(raw); self._raw = raw
        raw_toggle.toggled.connect(lambda checked: (raw.setVisible(checked), raw_toggle.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)))
        self.layout.addStretch()

    def _render_value(self, title: str, value: Any, depth: int):
        if depth > 4:
            return
        if isinstance(value, dict):
            clean = {k: v for k, v in value.items() if str(k) not in _INTERNAL_KEYS}
            scalar_rows = [[_friendly_key(k), _text(v)] for k, v in clean.items() if _scalar(v)]
            complex_rows = [(k, v) for k, v in clean.items() if not _scalar(v)]
            if scalar_rows:
                group = QGroupBox(_friendly_key(title)); box = QVBoxLayout(group); box.addWidget(_make_table(scalar_rows, ["Field", "Value"])); self.layout.addWidget(group)
            for key, child in complex_rows:
                self._render_value(str(key), child, depth + 1)
            if not clean:
                label = QLabel(f"{_friendly_key(title)}: no data returned"); label.setObjectName("Muted"); self.layout.addWidget(label)
            return
        if isinstance(value, (list, tuple)):
            rows = list(value)
            group = QGroupBox(f"{_friendly_key(title)} ({len(rows):,})"); box = QVBoxLayout(group)
            if not rows:
                empty = QLabel("No matching rows."); empty.setObjectName("Muted"); box.addWidget(empty); self.layout.addWidget(group); return
            if all(isinstance(row, dict) for row in rows[:200]):
                keys = []
                for row in rows[:100]:
                    for key in row:
                        if key not in keys and _scalar(row.get(key)): keys.append(key)
                        if len(keys) >= 10: break
                if keys:
                    table_rows = [[_text(row.get(key)) for key in keys] for row in rows[:500]]; box.addWidget(_make_table(table_rows, [_friendly_key(k) for k in keys]))
                else:
                    label = QLabel(json.dumps(rows[:20], indent=2, default=str)); label.setTextInteractionFlags(Qt.TextSelectableByMouse); box.addWidget(label)
            elif all(isinstance(row, (list, tuple)) for row in rows[:200]) and rows and len(rows[0]) <= 8:
                width = max(len(row) for row in rows[:500]); table_rows = [[_text(v) for v in row] + [""] * (width - len(row)) for row in rows[:500]]; box.addWidget(_make_table(table_rows, [f"Value {i + 1}" for i in range(width)]))
            else:
                table_rows = [[str(index + 1), _text(row)] for index, row in enumerate(rows[:500])]; box.addWidget(_make_table(table_rows, ["#", "Value"]))
            if len(rows) > 500:
                note = QLabel(f"Showing the first 500 of {len(rows):,} rows. Raw structured data retains the complete result."); note.setObjectName("Muted"); box.addWidget(note)
            self.layout.addWidget(group); return
        group = QGroupBox(_friendly_key(title)); box = QVBoxLayout(group); label = QLabel(_text(value)); label.setWordWrap(True); label.setTextInteractionFlags(Qt.TextSelectableByMouse); box.addWidget(label); self.layout.addWidget(group)
