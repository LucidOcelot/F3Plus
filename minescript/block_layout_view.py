from __future__ import annotations

"""Discrete block-layout visualizer for build/shape results.

World-coordinate maps and build blueprints are different user jobs. This renderer shows
Minecraft block cells directly and, for 3D geometry, lets the user inspect one Y layer
at a time instead of flattening the entire model into a misleading X/Z projection.
"""

from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)


def _number(value): return isinstance(value, (int, float)) and not isinstance(value, bool)


def _normalize_points(rows) -> list[tuple[int, int, int]]:
    if not isinstance(rows, (list, tuple)): return []
    out = []; seen = set()
    for row in rows[:100_000]:
        if not isinstance(row, (list, tuple)): continue
        if len(row) >= 3 and all(_number(v) for v in row[:3]): x, y, z = int(round(row[0])), int(round(row[1])), int(round(row[2]))
        elif len(row) >= 2 and all(_number(v) for v in row[:2]): x, y, z = int(round(row[0])), 0, int(round(row[1]))
        else: continue
        point = (x, y, z)
        if point not in seen: seen.add(point); out.append(point)
    return out


def layout_layers(spec, data: Any):
    if not isinstance(data, dict) or str(getattr(spec, "top", "")) != "Calculators" or str(getattr(spec, "submenu", "")) != "Shapes": return None
    sets = []
    for key in ("points", "vertices", "strand_a", "strand_b"):
        points = _normalize_points(data.get(key))
        if points: sets.append((key.replace("_", " ").title(), points))
    if not sets: return None
    ys = sorted({point[1] for _label, points in sets for point in points})
    return sets, ys


class _BlockView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent); self.setRenderHint(QPainter.Antialiasing, False); self.setDragMode(QGraphicsView.ScrollHandDrag); self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse); self.setMinimumHeight(390)
    def wheelEvent(self, event):
        factor = 1.18 if event.angleDelta().y() > 0 else 1 / 1.18; self.scale(factor, factor); event.accept()


class BlockLayoutPreview(QFrame):
    def __init__(self, title: str, sets, layers, colors, parent=None):
        super().__init__(parent); self.setObjectName("ResultSection"); self.sets = sets; self.layers = layers or [0]; self.colors = colors
        root = QVBoxLayout(self); root.setContentsMargins(10, 9, 10, 10); root.setSpacing(7)
        head = QHBoxLayout(); heading = QLabel(title); heading.setObjectName("WorkspaceTitle"); head.addWidget(heading, 1); badge = QLabel("BLOCK BLUEPRINT"); badge.setObjectName("VersionChip"); head.addWidget(badge); root.addLayout(head)
        tools = QHBoxLayout(); fit = QPushButton("Fit"); zin = QPushButton("+"); zout = QPushButton("−"); tools.addWidget(fit); tools.addWidget(zin); tools.addWidget(zout); tools.addSpacing(12); self.layer_label = QLabel("Y layer"); tools.addWidget(self.layer_label); self.layer = QComboBox(); self.layer.addItems([str(y) for y in self.layers]); tools.addWidget(self.layer); tools.addStretch(); self.summary = QLabel(); self.summary.setObjectName("Muted"); tools.addWidget(self.summary); root.addLayout(tools)
        self.scene = QGraphicsScene(self); self.scene.setBackgroundBrush(QBrush(QColor(colors["surface2"]))); self.view = _BlockView(self.scene); root.addWidget(self.view, 1)
        note = QLabel("Each square is one Minecraft block in X/Z. For 3D shapes, change Y layer to inspect construction slices instead of flattening all layers together."); note.setWordWrap(True); note.setObjectName("Muted"); root.addWidget(note)
        self.layer.setVisible(len(self.layers) > 1); self.layer_label.setVisible(len(self.layers) > 1); self.layer.currentTextChanged.connect(self.rebuild); fit.clicked.connect(self.fit); zin.clicked.connect(lambda: self.view.scale(1.25, 1.25)); zout.clicked.connect(lambda: self.view.scale(.8, .8)); self.rebuild(); self.fit()

    def rebuild(self):
        self.scene.clear(); current_y = int(self.layer.currentText()) if self.layer.count() else 0; color_keys = ["primary", "accent", "accent2", "success", "warning", "danger"]; shown = 0; all_points = []
        for set_index, (_label, points) in enumerate(self.sets):
            color = QColor(self.colors[color_keys[set_index % len(color_keys)]])
            for x, y, z in points:
                if y != current_y: continue
                shown += 1; all_points.append((x, z)); cell = QGraphicsRectItem(QRectF(x - .48, z - .48, .96, .96)); cell.setPen(QPen(QColor(self.colors["border"]), 0)); cell.setBrush(QBrush(color)); self.scene.addItem(cell)
        if all_points:
            xs = [p[0] for p in all_points]; zs = [p[1] for p in all_points]; minx, maxx, minz, maxz = min(xs), max(xs), min(zs), max(zs); pad = 1.5; self.scene.setSceneRect(QRectF(minx - pad, minz - pad, max(1, maxx - minx + 2 * pad), max(1, maxz - minz + 2 * pad))); self.summary.setText(f"Y {current_y} • {shown:,} blocks • X {minx}…{maxx} • Z {minz}…{maxz}")
        else:
            self.scene.setSceneRect(QRectF(-8, -8, 16, 16)); self.summary.setText(f"Y {current_y} • no blocks on this layer")
        grid = QPen(QColor(self.colors["border"]), 0)
        rect = self.scene.sceneRect(); x = int(rect.left())
        while x <= int(rect.right()): self.scene.addLine(x + .5, rect.top(), x + .5, rect.bottom(), grid); x += 1
        z = int(rect.top())
        while z <= int(rect.bottom()): self.scene.addLine(rect.left(), z + .5, rect.right(), z + .5, grid); z += 1

    def fit(self):
        rect = self.scene.itemsBoundingRect()
        if rect.isValid() and rect.width() > 0 and rect.height() > 0: self.view.fitInView(rect.adjusted(-1, -1, 1, 1), Qt.KeepAspectRatio)
