from __future__ import annotations

import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QPen
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QGraphicsItem, QGraphicsScene, QGraphicsView,
    QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QSplitter, QVBoxLayout,
)

from .visual_data import extract_coordinate_layers


class ZoomView(QGraphicsView):
    def wheelEvent(self, event):
        self.scale(1.2 if event.angleDelta().y() > 0 else 1 / 1.2, 1.2 if event.angleDelta().y() > 0 else 1 / 1.2)


class ResultMapDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.layers = extract_coordinate_layers(data)
        self.setWindowTitle("Interactive X/Z Result View"); self.resize(1000, 760)
        root = QVBoxLayout(self); toolbar = QHBoxLayout(); fit = QPushButton("Fit"); self.labels = QCheckBox("Point labels"); copy = QPushButton("Copy visible coordinates"); toolbar.addWidget(fit); toolbar.addWidget(self.labels); toolbar.addStretch(); toolbar.addWidget(copy); root.addLayout(toolbar)
        split = QSplitter(Qt.Horizontal); root.addWidget(split, 1); self.layer_list = QListWidget(); split.addWidget(self.layer_list); self.scene = QGraphicsScene(self); self.view = ZoomView(self.scene); self.view.setDragMode(QGraphicsView.ScrollHandDrag); self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse); split.addWidget(self.view); split.setSizes([220, 780])
        for layer in self.layers:
            item = QListWidgetItem(layer); item.setFlags(item.flags() | Qt.ItemIsUserCheckable); item.setCheckState(Qt.Checked); self.layer_list.addItem(item)
        self.layer_list.itemChanged.connect(self.redraw); self.labels.toggled.connect(self.redraw); fit.clicked.connect(self.fit); copy.clicked.connect(self.copy_visible); self.redraw(); self.fit()

    def visible_layers(self):
        return {self.layer_list.item(i).text() for i in range(self.layer_list.count()) if self.layer_list.item(i).checkState() == Qt.Checked}

    def redraw(self):
        self.scene.clear(); active = self.visible_layers(); points = [point for layer, values in self.layers.items() if layer in active for point in values]
        if not points: return
        xs = [point[0] for point in points]; zs = [point[1] for point in points]; step = max(16.0, max(max(xs) - min(xs), max(zs) - min(zs), 64.0) / 12.0); left = math.floor(min(xs) / step) * step; right = math.ceil(max(xs) / step) * step; top = math.floor(min(zs) / step) * step; bottom = math.ceil(max(zs) / step) * step; pen = QPen(); pen.setCosmetic(True)
        x = left
        while x <= right: self.scene.addLine(x, top, x, bottom, pen); x += step
        z = top
        while z <= bottom: self.scene.addLine(left, z, right, z, pen); z += step
        for layer, values in self.layers.items():
            if layer not in active: continue
            for x, z, _ in values:
                dot = self.scene.addEllipse(x - 2, z - 2, 4, 4); dot.setToolTip(f"{layer}: X {x:g}, Z {z:g}")
                if self.labels.isChecked():
                    text = self.scene.addText(f"{x:g}, {z:g}"); text.setPos(x + 3, z + 3); text.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)

    def fit(self):
        rect = self.scene.itemsBoundingRect()
        if not rect.isNull(): self.view.fitInView(rect.adjusted(-20, -20, 20, 20), Qt.KeepAspectRatio)

    def copy_visible(self):
        active = self.visible_layers(); lines = []
        for layer, values in self.layers.items():
            if layer in active: lines.extend(f"{layer}: {x:g}, {z:g}" for x, z, _ in values)
        QApplication.clipboard().setText("\n".join(lines))


__all__ = ["ResultMapDialog", "extract_coordinate_layers"]
