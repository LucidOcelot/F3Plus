from __future__ import annotations

"""Structured result renderer for canonical F3+ workbenches.

Maps and charts are selected by ``visual_contracts`` from the operation identity and
named result fields. Arbitrary numeric arrays are never guessed to be coordinates or a
distribution, and map contracts explicitly distinguish ordered paths from unordered
candidate sets.
"""

import json
import math
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QGraphicsEllipseItem, QGraphicsItemGroup,
    QGraphicsPathItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QPlainTextEdit, QPushButton,
    QScrollArea, QSplitter, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget,
)

from .structured_results import _presentation_data
from .ui_theme import palette
from .visual_contracts import chart_series, map_series


_INTERNAL_KEYS = {"_contract", "_display", "_source_contract", "_exactness_contract"}


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
    for key in ("source", "data_source", "trade_source", "backend"):
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
    if "mojang server" in low or "observed generated" in low or "generated-world block states" in low:
        return "Exact / observed"
    if "installed" in low and "minecraft" in low:
        return "Installed-version data"
    if "baseline" in low or "reference" in low:
        return "Reference / model"
    return "Calculated / model"


def _make_table(rows: list[list[str]], headers: list[str]) -> QTableWidget:
    table = QTableWidget(len(rows), len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row[:len(headers)]):
            table.setItem(row_index, column_index, QTableWidgetItem(value))
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    if headers:
        table.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.Stretch)
    table.setMinimumHeight(min(430, max(90, 36 + 28 * min(len(rows), 12))))
    return table


class _MapView(QGraphicsView):
    def __init__(self, scene, cursor, parent=None):
        super().__init__(scene, parent)
        self.cursor = cursor
        self.setRenderHint(QPainter.Antialiasing, False)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setMouseTracking(True)
        self.setMinimumHeight(360)

    def wheelEvent(self, event):
        factor = 1.18 if event.angleDelta().y() > 0 else 1 / 1.18
        self.scale(factor, factor)
        event.accept()

    def mouseMoveEvent(self, event):
        point = self.mapToScene(event.pos())
        self.cursor.setText(f"Cursor: X {point.x():,.1f}   Z {point.y():,.1f} blocks")
        super().mouseMoveEvent(event)


class InteractiveMap(QFrame):
    def __init__(self, title: str, series, colors, center=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ResultSection")
        self.series = []
        for row in series:
            if len(row) >= 3:
                label, points, ordered = row[0], row[1], bool(row[2])
            else:
                label, points, ordered = row[0], row[1], False
            if points:
                self.series.append((str(label), list(points), ordered))
        self.colors = colors
        self.center = center
        self.groups = []
        self.layer_checks = []

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 9, 10, 10)
        root.setSpacing(7)
        head = QHBoxLayout()
        heading = QLabel(title)
        heading.setObjectName("WorkspaceTitle")
        head.addWidget(heading, 1)
        badge = QLabel("INTERACTIVE X/Z MAP")
        badge.setObjectName("VersionChip")
        head.addWidget(badge)
        root.addLayout(head)

        tools = QHBoxLayout()
        fit = QPushButton("Fit")
        zoom_in = QPushButton("+")
        zoom_out = QPushButton("−")
        self.labels = QCheckBox("Point labels")
        for widget in (fit, zoom_in, zoom_out, self.labels):
            tools.addWidget(widget)
        tools.addStretch()
        hint = QLabel("Wheel: zoom  •  Drag: pan  •  +X east  •  +Z south")
        hint.setObjectName("Muted")
        tools.addWidget(hint)
        root.addLayout(tools)

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        root.addWidget(split, 1)
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor(colors["surface2"])))
        self.cursor = QLabel("Move over the map to inspect block coordinates.")
        self.cursor.setObjectName("Muted")
        self.view = _MapView(self.scene, self.cursor)
        split.addWidget(self.view)

        side = QWidget()
        self.side = QVBoxLayout(side)
        self.side.setContentsMargins(6, 4, 6, 4)
        label = QLabel("LAYERS")
        label.setObjectName("DeckLabel")
        self.side.addWidget(label)
        self.bounds = QLabel()
        self.bounds.setWordWrap(True)
        self.bounds.setObjectName("Muted")
        copy = QPushButton("Copy visible coordinates")
        self.side.addStretch()
        self.side.addWidget(self.bounds)
        self.side.addWidget(copy)
        split.addWidget(side)
        split.setSizes([760, 220])
        root.addWidget(self.cursor)

        fit.clicked.connect(self.fit_to_data)
        zoom_in.clicked.connect(lambda: self.view.scale(1.25, 1.25))
        zoom_out.clicked.connect(lambda: self.view.scale(.8, .8))
        self.labels.toggled.connect(self.rebuild)
        copy.clicked.connect(self.copy_visible)
        self.rebuild()
        self.fit_to_data()

    def _bounds(self):
        points = [point for _label, rows, _ordered in self.series for point in rows]
        if self.center is not None:
            points.append(self.center)
        if not points:
            return -16.0, 16.0, -16.0, 16.0
        xs = [point[0] for point in points]
        zs = [point[1] for point in points]
        return min(xs), max(xs), min(zs), max(zs)

    def rebuild(self):
        visible = [check.isChecked() for check in self.layer_checks]
        for check in self.layer_checks:
            check.deleteLater()
        self.layer_checks = []
        self.scene.clear()
        self.groups = []
        minx, maxx, minz, maxz = self._bounds()
        span = max(maxx - minx, maxz - minz, 24.0)
        pad = span * .08
        minx -= pad; maxx += pad; minz -= pad; maxz += pad
        step = max(1.0, 2 ** round(math.log2(max(1.0, span / 8.0))))
        grid_pen = QPen(QColor(self.colors["border"]), 0)
        x = math.floor(minx / step) * step
        while x <= maxx:
            self.scene.addLine(x, minz, x, maxz, grid_pen)
            x += step
        z = math.floor(minz / step) * step
        while z <= maxz:
            self.scene.addLine(minx, z, maxx, z, grid_pen)
            z += step

        color_keys = ["primary", "accent", "accent2", "success", "warning", "danger"]
        for index, (label, points, ordered) in enumerate(self.series):
            color = QColor(self.colors[color_keys[index % len(color_keys)]])
            group = QGraphicsItemGroup()
            if ordered and len(points) > 1:
                path = QPainterPath(QPointF(points[0][0], points[0][1]))
                for px, pz in points[1:]:
                    path.lineTo(px, pz)
                line = QGraphicsPathItem(path)
                line.setPen(QPen(color, 1.25))
                group.addToGroup(line)
            radius = max(2.4, min(6.0, span / 150.0))
            for point_index, (px, pz) in enumerate(points):
                dot = QGraphicsEllipseItem(QRectF(px - radius / 2, pz - radius / 2, radius, radius))
                dot.setPen(QPen(color, 0))
                dot.setBrush(QBrush(color))
                group.addToGroup(dot)
                if self.labels.isChecked() and point_index < 80:
                    text = QGraphicsSimpleTextItem(f"{px:g}, {pz:g}")
                    text.setBrush(QBrush(color))
                    text.setPos(px + radius, pz + radius)
                    text.setFlag(QGraphicsSimpleTextItem.ItemIgnoresTransformations, True)
                    group.addToGroup(text)
            self.scene.addItem(group)
            self.groups.append((label, points, group))
            check = QCheckBox(f"{label} ({len(points):,})")
            check.setChecked(visible[index] if index < len(visible) else True)
            check.toggled.connect(group.setVisible)
            self.side.insertWidget(1 + index, check)
            self.layer_checks.append(check)

        if self.center is not None:
            cx, cz = self.center
            marker = QGraphicsEllipseItem(QRectF(cx - 4, cz - 4, 8, 8))
            marker.setPen(QPen(QColor(self.colors["text"]), 1))
            self.scene.addItem(marker)
        self.scene.setSceneRect(QRectF(minx, minz, maxx - minx, maxz - minz))
        self.bounds.setText(f"X {minx:,.0f} … {maxx:,.0f}\nZ {minz:,.0f} … {maxz:,.0f}\nGrid {step:g} blocks")

    def fit_to_data(self):
        rect = self.scene.itemsBoundingRect()
        if rect.isValid() and rect.width() > 0 and rect.height() > 0:
            self.view.fitInView(rect.adjusted(-8, -8, 8, 8), Qt.KeepAspectRatio)

    def copy_visible(self):
        lines = ["layer\tx\tz"]
        for label, points, group in self.groups:
            if group.isVisible():
                lines.extend(f"{label}\t{x:g}\t{z:g}" for x, z in points)
        QApplication.clipboard().setText("\n".join(lines))


class NumericChart(QFrame):
    def __init__(self, title: str, rows: list[tuple[str, float]], kind: str, colors, parent=None):
        super().__init__(parent)
        self.title = title
        self.rows = rows[:512]
        self.kind = kind
        self.colors = colors
        self.setObjectName("ResultSection")
        self.setMinimumHeight(330)

    @staticmethod
    def _short_label(label: str, limit: int = 14) -> str:
        text = str(label).replace("minecraft:", "").replace("_", " ")
        return text if len(text) <= limit else text[: limit - 1] + "…"

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.rows:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        area = self.rect().adjusted(52, 46, -22, -74)
        values = [value for _label, value in self.rows]
        lo, hi = min(values), max(values)
        if self.kind == "bars":
            lo = min(0.0, lo)
        if lo == hi:
            lo -= 1
            hi += 1

        painter.setPen(QColor(self.colors["text"]))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(16, 27, self.title)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QPen(QColor(self.colors["border"]), 1))
        for index in range(5):
            y = area.top() + area.height() * index / 4
            painter.drawLine(area.left(), int(y), area.right(), int(y))

        color = QColor(self.colors["primary"])
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        count = len(self.rows)

        def py(value):
            return area.bottom() - (value - lo) / (hi - lo) * area.height()

        if self.kind == "line":
            path = QPainterPath()
            for index, (_label, value) in enumerate(self.rows):
                x = area.left() + area.width() * index / max(1, count - 1)
                y = py(value)
                path.moveTo(x, y) if index == 0 else path.lineTo(x, y)
            painter.drawPath(path)
        else:
            width = area.width() / max(1, count)
            zero = py(0)
            for index, (_label, value) in enumerate(self.rows):
                x = area.left() + index * width + width * .12
                y = py(value)
                painter.drawRect(QRectF(x, min(y, zero), max(1, width * .76), abs(zero - y)))

        painter.setPen(QColor(self.colors["muted"]))
        painter.drawText(8, area.top() + 5, f"{hi:.4g}")
        painter.drawText(8, area.bottom(), f"{lo:.4g}")

        if count <= 12:
            label_indices = range(count)
        else:
            step = max(1, math.ceil(count / 8))
            label_indices = sorted(set([0, count - 1, *range(0, count, step)]))
        painter.setPen(QColor(self.colors["text"]))
        if self.kind == "bars":
            width = area.width() / max(1, count)
            for index in label_indices:
                label = self._short_label(self.rows[index][0])
                x = area.left() + index * width
                painter.drawText(QRectF(x, area.bottom() + 6, width, 42), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, label)
        else:
            for index in label_indices:
                label = self._short_label(self.rows[index][0])
                x = area.left() + area.width() * index / max(1, count - 1)
                painter.drawText(QRectF(x - 42, area.bottom() + 6, 84, 42), Qt.AlignHCenter | Qt.AlignTop, label)


class ResultView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(self.scroll)
        self.host = QWidget()
        self.layout = QVBoxLayout(self.host)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(10)
        self.scroll.setWidget(self.host)
        self.show_empty("Run an operation to see its result here.")

    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def show_empty(self, text: str):
        self.clear()
        label = QLabel(text)
        label.setWordWrap(True)
        label.setObjectName("Muted")
        self.layout.addWidget(label)
        self.layout.addStretch()

    def set_result(self, spec, result, theme: str = "chorus", custom_palette: dict | None = None):
        self.clear()
        colors = palette(theme, custom_palette)
        data = getattr(result, "data", result)
        visible = _presentation_data(data)
        source = _source_label(data)
        exactness = _exactness_label(data, source)
        status = str(getattr(result, "status", "ok"))
        note = str(getattr(result, "note", "") or "")

        hero = QFrame()
        hero.setObjectName("ResultCard")
        hero_layout = QVBoxLayout(hero)
        title = QLabel(getattr(spec, "name", "Result"))
        title.setObjectName("WorkspaceTitle")
        hero_layout.addWidget(title)
        badges = QHBoxLayout()
        for text in (f"Status: {status}", f"Exactness: {exactness}", f"Source: {source}"):
            label = QLabel(text)
            label.setObjectName("VersionChip")
            label.setWordWrap(True)
            badges.addWidget(label)
        badges.addStretch()
        hero_layout.addLayout(badges)
        if isinstance(visible, dict) and visible.get("purpose"):
            purpose = QLabel(str(visible["purpose"]))
            purpose.setWordWrap(True)
            purpose.setObjectName("Muted")
            hero_layout.addWidget(purpose)
        self.layout.addWidget(hero)

        warning_texts = []
        if note:
            warning_texts.append(note)
        if isinstance(visible, dict):
            for key in ("reason", "note", "model_limit", "limitation"):
                value = visible.get(key)
                if value and str(value) not in warning_texts:
                    warning_texts.append(str(value))
        if warning_texts:
            banner = QFrame()
            banner.setObjectName("WarningBanner")
            box = QVBoxLayout(banner)
            for text in warning_texts:
                label = QLabel(text)
                label.setWordWrap(True)
                box.addWidget(label)
            self.layout.addWidget(banner)

        series, center = map_series(spec, visible)
        if series:
            self.layout.addWidget(InteractiveMap(f"{getattr(spec, 'name', 'Result')} — map", series, colors, center))
        chart = chart_series(spec, visible)
        if chart:
            chart_title, rows, kind = chart
            self.layout.addWidget(NumericChart(chart_title, rows, kind, colors))
        self._render_value("Result", visible, 0)

        raw_toggle = QToolButton()
        raw_toggle.setText("Raw structured data")
        raw_toggle.setCheckable(True)
        raw_toggle.setArrowType(Qt.RightArrow)
        self.layout.addWidget(raw_toggle)
        raw = QPlainTextEdit()
        raw.setReadOnly(True)
        raw.setPlainText(json.dumps(visible, indent=2, ensure_ascii=False, default=str))
        raw.setMaximumHeight(360)
        raw.hide()
        self.layout.addWidget(raw)

        def show_raw(checked: bool):
            raw.setVisible(checked)
            raw_toggle.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

        raw_toggle.toggled.connect(show_raw)
        self.layout.addStretch()

    def _render_value(self, title: str, value: Any, depth: int):
        if depth > 4:
            return
        if isinstance(value, dict):
            clean = {key: child for key, child in value.items() if str(key) not in _INTERNAL_KEYS and key not in {"purpose"}}
            scalar_rows = [[_friendly_key(key), _text(child)] for key, child in clean.items() if _scalar(child)]
            complex_rows = [(key, child) for key, child in clean.items() if not _scalar(child)]
            if scalar_rows:
                group = QGroupBox(_friendly_key(title))
                box = QVBoxLayout(group)
                box.addWidget(_make_table(scalar_rows, ["Field", "Value"]))
                self.layout.addWidget(group)
            for key, child in complex_rows:
                self._render_value(str(key), child, depth + 1)
            if not clean:
                label = QLabel(f"{_friendly_key(title)}: no data returned")
                label.setObjectName("Muted")
                self.layout.addWidget(label)
            return

        if isinstance(value, (list, tuple)):
            rows = list(value)
            group = QGroupBox(f"{_friendly_key(title)} ({len(rows):,})")
            box = QVBoxLayout(group)
            if not rows:
                empty = QLabel("No matching rows.")
                empty.setObjectName("Muted")
                box.addWidget(empty)
                self.layout.addWidget(group)
                return
            if all(isinstance(row, dict) for row in rows[:200]):
                keys = []
                for row in rows[:100]:
                    for key in row:
                        if key not in keys and _scalar(row.get(key)):
                            keys.append(key)
                        if len(keys) >= 10:
                            break
                if keys:
                    box.addWidget(_make_table([[_text(row.get(key)) for key in keys] for row in rows[:500]], [_friendly_key(key) for key in keys]))
                else:
                    label = QLabel(json.dumps(rows[:20], indent=2, default=str))
                    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                    box.addWidget(label)
            elif all(isinstance(row, (list, tuple)) for row in rows[:200]) and rows and len(rows[0]) <= 8:
                width = max(len(row) for row in rows[:500])
                box.addWidget(_make_table([[_text(child) for child in row] + [""] * (width - len(row)) for row in rows[:500]], [f"Value {index + 1}" for index in range(width)]))
            else:
                box.addWidget(_make_table([[_text(index + 1), _text(row)] for index, row in enumerate(rows[:500])], ["#", "Value"]))
            if len(rows) > 500:
                note = QLabel(f"Showing the first 500 of {len(rows):,} rows. Raw structured data retains the complete result.")
                note.setObjectName("Muted")
                box.addWidget(note)
            self.layout.addWidget(group)
            return

        group = QGroupBox(_friendly_key(title))
        box = QVBoxLayout(group)
        label = QLabel(_text(value))
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        box.addWidget(label)
        self.layout.addWidget(group)
