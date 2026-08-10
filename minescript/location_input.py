from __future__ import annotations

"""Minecraft-oriented location input shared by world/search workbenches.

The UI exposes three user concepts instead of leaking every historical coordinate key:
current player position, block coordinates, or a center chunk.  The returned dictionary
contains compatibility aliases so older handlers can keep consuming their existing
parameter names while the user interacts with one coherent location control.
"""

import math

from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)


LOCATION_KEYS = {
    "x", "y", "z", "cx", "cz", "chunk_x", "chunk_z", "center_chunk_x",
    "center_chunk_z", "center_x", "center_z", "origin_x", "origin_z",
}


def applies_to(spec) -> bool:
    if getattr(spec, "top", "") != "Seed Tools":
        return False
    if getattr(spec, "submenu", "") in {"World Seed Recovery", "Cubiomes"}:
        return False
    name = str(getattr(spec, "name", ""))
    if name.endswith("Status") or name in {"Compatibility Report"}:
        return False
    return getattr(spec, "submenu", "") in {
        "Slime", "Structures", "Spawners", "Biomes", "Local Area",
        "World Analysis", "Nether",
    }


class LocationInput(QFrame):
    """One location panel that can feed legacy block/chunk center parameters."""

    def __init__(self, owner=None, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.setObjectName("ToolConfigCard")
        root = QVBoxLayout(self); root.setContentsMargins(10, 9, 10, 9); root.setSpacing(7)

        head = QHBoxLayout(); title = QLabel("SEARCH CENTER"); title.setObjectName("DeckLabel"); head.addWidget(title)
        head.addStretch(); self.source = QComboBox(); self.source.addItems(["Current position", "Block coordinates", "Center chunk"]); head.addWidget(self.source); root.addLayout(head)
        help_label = QLabel("Choose where the search/analysis is centered. F3+ converts the value to the block/chunk form required by the selected operation.")
        help_label.setWordWrap(True); help_label.setObjectName("Muted"); root.addWidget(help_label)

        self.pages = QStackedWidget(); root.addWidget(self.pages)

        live = QWidget(); ll = QVBoxLayout(live); ll.setContentsMargins(0, 0, 0, 0)
        self.live_text = QLabel("No position captured yet."); self.live_text.setWordWrap(True); ll.addWidget(self.live_text)
        self.capture = QPushButton("Capture F3+C now"); self.capture.clicked.connect(self._capture); ll.addWidget(self.capture); ll.addStretch(); self.pages.addWidget(live)

        block = QWidget(); bf = QFormLayout(block); bf.setContentsMargins(0, 0, 0, 0)
        self.x = QDoubleSpinBox(); self.x.setRange(-30_000_000, 30_000_000); self.x.setDecimals(3)
        self.y = QDoubleSpinBox(); self.y.setRange(-2048, 4096); self.y.setDecimals(3); self.y.setValue(64)
        self.z = QDoubleSpinBox(); self.z.setRange(-30_000_000, 30_000_000); self.z.setDecimals(3)
        bf.addRow("X", self.x); bf.addRow("Y", self.y); bf.addRow("Z", self.z); self.pages.addWidget(block)

        chunk = QWidget(); cf = QFormLayout(chunk); cf.setContentsMargins(0, 0, 0, 0)
        self.chunk_x = QSpinBox(); self.chunk_x.setRange(-1_875_000, 1_875_000)
        self.chunk_z = QSpinBox(); self.chunk_z.setRange(-1_875_000, 1_875_000)
        cf.addRow("Chunk X", self.chunk_x); cf.addRow("Chunk Z", self.chunk_z)
        note = QLabel("The block center is the middle of this 16×16 chunk (chunk×16 + 8)."); note.setWordWrap(True); note.setObjectName("Muted"); cf.addRow("", note); self.pages.addWidget(chunk)

        self.source.currentIndexChanged.connect(self.pages.setCurrentIndex)
        self._sync_live()

    def _current(self):
        return getattr(self.owner, "current_position", None) if self.owner is not None else None

    def _sync_live(self):
        pos = self._current()
        if pos is None:
            self.live_text.setText("No player position is cached. Capture F3+C or switch to block/chunk entry.")
            return
        self.live_text.setText(f"Current player position: X {pos.x:g}  Y {pos.y:g}  Z {pos.z:g}")
        self.x.setValue(float(pos.x)); self.y.setValue(float(pos.y)); self.z.setValue(float(pos.z))
        self.chunk_x.setValue(math.floor(float(pos.x) / 16)); self.chunk_z.setValue(math.floor(float(pos.z) / 16))

    def _capture(self):
        if self.owner is not None and hasattr(self.owner, "capture_position"):
            self.owner.capture_position(); self._sync_live()

    def values(self) -> dict[str, float | int]:
        mode = self.source.currentIndex()
        if mode == 0:
            pos = self._current()
            if pos is None:
                raise ValueError("Current position is not available. Capture F3+C or choose block/chunk coordinates.")
            x, y, z = float(pos.x), float(pos.y), float(pos.z)
            cx, cz = math.floor(x / 16), math.floor(z / 16)
        elif mode == 1:
            x, y, z = float(self.x.value()), float(self.y.value()), float(self.z.value())
            cx, cz = math.floor(x / 16), math.floor(z / 16)
        else:
            cx, cz = int(self.chunk_x.value()), int(self.chunk_z.value())
            x, z, y = cx * 16 + 8, cz * 16 + 8, 64.0
        return {
            "x": x, "y": y, "z": z,
            "cx": cx, "cz": cz,
            "chunk_x": cx, "chunk_z": cz,
            "center_chunk_x": cx, "center_chunk_z": cz,
            "center_x": x, "center_z": z,
            "origin_x": x, "origin_z": z,
        }
