from __future__ import annotations

"""Minecraft-oriented location input shared by world/search workbenches.

The UI exposes three user concepts instead of leaking historical coordinate keys:
current player position, block coordinates, or a center chunk. Returned values include
compatibility aliases so old handlers keep working behind one coherent player-facing
control.
"""

import math

from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

from .location_contract import LOCATION_KEYS, applies_to


class LocationInput(QFrame):
    """Compact three-source location selector for world/search operations."""

    def __init__(self, owner=None, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.setObjectName("ToolConfigCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        root = QVBoxLayout(self); root.setContentsMargins(10, 8, 10, 8); root.setSpacing(5)

        head = QHBoxLayout(); title = QLabel("SEARCH CENTER"); title.setObjectName("DeckLabel"); head.addWidget(title)
        head.addStretch(); self.source = QComboBox(); self.source.addItems(["Current position", "Block coordinates", "Center chunk"]); self.source.setMinimumWidth(170)
        self.source.setToolTip("Choose how to provide the center of this search: the last captured player position, exact block coordinates, or a chunk coordinate.")
        head.addWidget(self.source); root.addLayout(head)
        help_label = QLabel("Choose one center source. F3+ converts it to both block and chunk coordinates for the selected operation.")
        help_label.setWordWrap(True); help_label.setObjectName("Muted"); root.addWidget(help_label)

        self.pages = QStackedWidget(); self.pages.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum); root.addWidget(self.pages)

        live = QWidget(); live.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum); ll = QHBoxLayout(live); ll.setContentsMargins(0, 0, 0, 0); ll.setSpacing(8)
        self.live_text = QLabel("No position captured yet."); self.live_text.setWordWrap(True); ll.addWidget(self.live_text, 1)
        self.capture = QPushButton("Capture F3+C"); self.capture.setToolTip("Ask Minecraft for the current debug-copy position and use it as this search center."); self.capture.clicked.connect(self._capture); ll.addWidget(self.capture); self.pages.addWidget(live)

        block = QWidget(); block.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum); bf = QHBoxLayout(block); bf.setContentsMargins(0, 0, 0, 0); bf.setSpacing(8)
        self.x = QDoubleSpinBox(); self.x.setRange(-30_000_000, 30_000_000); self.x.setDecimals(3); self.x.setPrefix("X ")
        self.y = QDoubleSpinBox(); self.y.setRange(-2048, 4096); self.y.setDecimals(3); self.y.setValue(64); self.y.setPrefix("Y ")
        self.z = QDoubleSpinBox(); self.z.setRange(-30_000_000, 30_000_000); self.z.setDecimals(3); self.z.setPrefix("Z ")
        self.x.setToolTip("Block X coordinate of the search center. Positive is east; negative is west.")
        self.y.setToolTip("Block Y coordinate of the search center when the selected operation uses height.")
        self.z.setToolTip("Block Z coordinate of the search center. Positive is south; negative is north.")
        bf.addWidget(self.x, 1); bf.addWidget(self.y, 1); bf.addWidget(self.z, 1); self.pages.addWidget(block)

        chunk = QWidget(); chunk.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum); cf = QHBoxLayout(chunk); cf.setContentsMargins(0, 0, 0, 0); cf.setSpacing(8)
        self.chunk_x = QSpinBox(); self.chunk_x.setRange(-1_875_000, 1_875_000); self.chunk_x.setPrefix("Chunk X ")
        self.chunk_z = QSpinBox(); self.chunk_z.setRange(-1_875_000, 1_875_000); self.chunk_z.setPrefix("Chunk Z ")
        note = QLabel("Block center = chunk×16 + 8"); note.setObjectName("Muted")
        self.chunk_x.setToolTip("Chunk X used as the center. F3+ converts it to the middle block of that 16×16 chunk.")
        self.chunk_z.setToolTip("Chunk Z used as the center. F3+ converts it to the middle block of that 16×16 chunk.")
        cf.addWidget(self.chunk_x, 1); cf.addWidget(self.chunk_z, 1); cf.addWidget(note); self.pages.addWidget(chunk)

        self.source.currentIndexChanged.connect(self.pages.setCurrentIndex)
        self._sync_live()

    def _current(self):
        return getattr(self.owner, "current_position", None) if self.owner is not None else None

    def _sync_live(self):
        pos = self._current()
        if pos is None:
            self.live_text.setText("No cached player position. Capture F3+C or choose coordinates/chunk entry.")
            return
        self.live_text.setText(f"X {pos.x:g}   Y {pos.y:g}   Z {pos.z:g}")
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
