from __future__ import annotations

"""Player-facing result presentation for calculations, searches, and scans."""

from collections import Counter
import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel, QFrame, QGroupBox, QPlainTextEdit, QScrollArea, QToolButton,
    QVBoxLayout, QWidget,
)

from .block_layout_view import BlockLayoutPreview, layout_layers
from .result_view import InteractiveMap, NumericChart, _make_table, _scalar, _source_label, _text
from .structured_results import _presentation_data
from .ui_theme import palette
from .ux_semantics25 import compact_note
from .visual_contracts import chart_series, map_series


_METADATA = {
    "_contract", "_display", "_source_contract", "_exactness_contract",
    "purpose", "source", "data_source", "trade_source", "backend", "worldgen_source",
    "exactness", "accuracy", "confidence", "confidence_level", "model_exactness",
    "available", "requires_generated_world", "requires_seed_worldgen", "reason", "note",
    "model_limit", "limitation",
}

_LABELS = {
    "candidate_count": "Locations found",
    "candidate_counts": "Locations by type",
    "total_candidates": "Total locations found",
    "distinct": "Distinct biomes found",
    "biome_counts": "Biome sample counts",
    "nearest_samples": "Nearest matching samples",
    "samples": "Sample coordinates",
    "radius": "Radius",
    "configured_maximum_radius": "Configured radius limit",
    "effective_maximum_radius": "Radius limit used",
    "last_radius_searched": "Farthest radius checked",
    "found_radius": "Radius where match was found",
    "attempts": "Search passes completed",
    "found": "Match found",
    "mode": "Search mode",
    "unit": "Radius unit",
    "seed": "World seed",
    "world_path": "World save folder",
    "chunks_scanned": "Chunks scanned",
    "chunks_generated": "Chunks generated",
    "count": "Results",
    "mean": "Average",
    "average": "Average",
    "minimum": "Minimum",
    "maximum": "Maximum",
    "x": "X",
    "y": "Y",
    "z": "Z",
    "chunk_x": "Chunk X",
    "chunk_z": "Chunk Z",
    "distance": "Distance (blocks)",
    "travel_time": "Travel time",
    "items": "Items",
    "stacks": "Stacks",
    "slots": "Inventory slots",
    "shulkers": "Shulker boxes",
    "ticks": "Game ticks",
    "seconds": "Seconds",
    "probability": "Probability",
    "chance": "Chance",
    "emeralds": "Emeralds",
    "max_uses": "Maximum uses before restock",
    "health": "Health",
    "speed": "Movement speed",
    "jump_strength": "Jump strength",
}


def _label(key: str) -> str:
    text = str(key)
    return _LABELS.get(text, text.replace("_", " ").strip().title())


def _warnings(result, visible) -> list[str]:
    rows: list[str] = []
    note = getattr(result, "note", "")
    if note:
        rows.append(compact_note(note))
    if isinstance(visible, dict):
        for key in ("reason", "limitation", "model_limit"):
            value = visible.get(key)
            if value:
                short = compact_note(value)
                if short and short not in rows:
                    rows.append(short)
        worldgen = visible.get("worldgen_source")
        if isinstance(worldgen, dict) and worldgen.get("limitation"):
            short = compact_note(worldgen["limitation"])
            if short and short not in rows:
                rows.append(short)
    return rows


def _map_explanation(spec, series) -> str:
    ordered = any(bool(row[2]) for row in series if len(row) >= 3)
    submenu = str(getattr(spec, "submenu", ""))
    if ordered:
        return "Connected markers follow route order. Coordinates are Minecraft X/Z blocks; +X is east and +Z is south."
    if submenu == "Structures":
        return "Each marker is one returned structure location. Coordinates are Minecraft X/Z blocks; +X is east and +Z is south."
    if submenu in {"Biomes", "World Analysis", "Spawners", "Local Area"}:
        return "Each marker is one sampled or matching location. Coordinates are Minecraft X/Z blocks; +X is east and +Z is south."
    return "Each marker is one returned location unless the result is an ordered route. Coordinates are Minecraft X/Z blocks."


def _summary_rows(visible) -> list[list[str]]:
    if not isinstance(visible, dict):
        return []
    preferred = (
        "found", "count", "candidate_count", "total_candidates", "chunks_scanned",
        "found_radius", "last_radius_searched", "distance", "travel_time", "probability",
        "mean", "minimum", "maximum",
    )
    rows: list[list[str]] = []
    seen: set[str] = set()
    for key in preferred:
        value = visible.get(key)
        if key in visible and _scalar(value):
            rows.append([_label(key), _text(value)])
            seen.add(key)
    return rows[:6]


class ExplainedMap(QFrame):
    def __init__(self, spec, title: str, series, colors, center=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ResultSection")
        box = QVBoxLayout(self)
        box.setContentsMargins(8, 8, 8, 8)
        box.setSpacing(5)
        help_text = QLabel(_map_explanation(spec, series))
        help_text.setWordWrap(True)
        help_text.setObjectName("Muted")
        box.addWidget(help_text)
        box.addWidget(InteractiveMap(title, series, colors, center), 1)


class ResultView25(QWidget):
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
        self.show_empty("Run an operation to see its result.")

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
        status = str(getattr(result, "status", "ok"))

        hero = QFrame()
        hero.setObjectName("ResultCard")
        hv = QVBoxLayout(hero)
        title = QLabel(getattr(spec, "name", "Result"))
        title.setObjectName("WorkspaceTitle")
        hv.addWidget(title)
        if status.lower() not in {"ok", "success"}:
            state = QLabel(status.replace("_", " ").title())
            state.setObjectName("VersionChip")
            hv.addWidget(state)
        summary = _summary_rows(visible)
        if summary:
            hv.addWidget(_make_table(summary, ["Result", "Value"]))
        self.layout.addWidget(hero)

        warnings = _warnings(result, visible)
        if warnings:
            banner = QFrame()
            banner.setObjectName("WarningBanner")
            box = QVBoxLayout(banner)
            box.setContentsMargins(10, 7, 10, 7)
            for text in warnings:
                label = QLabel(text)
                label.setWordWrap(True)
                box.addWidget(label)
            self.layout.addWidget(banner)

        block_layout = layout_layers(spec, visible)
        if block_layout:
            sets, layers = block_layout
            self.layout.addWidget(BlockLayoutPreview(
                f"{getattr(spec, 'name', 'Shape')} — block layers", sets, layers, colors
            ))
        else:
            series, center = map_series(spec, visible)
            if series:
                self.layout.addWidget(ExplainedMap(
                    spec,
                    f"{getattr(spec, 'name', 'Result')} — locations",
                    series,
                    colors,
                    center,
                ))

        chart = chart_series(spec, visible)
        if chart:
            chart_title, rows, kind = chart
            self.layout.addWidget(NumericChart(chart_title, rows, kind, colors))

        self._render_value("Details", visible, 0)

        source = _source_label(data)
        if source and source not in {"F3+ calculation", "F3+ calculation/model"}:
            footer = QLabel(f"Data source: {source}")
            footer.setWordWrap(True)
            footer.setObjectName("Muted")
            self.layout.addWidget(footer)

        raw_toggle = QToolButton()
        raw_toggle.setText("Raw data")
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
            clean = {key: child for key, child in value.items() if str(key) not in _METADATA}
            scalar_rows = [[_label(key), _text(child)] for key, child in clean.items() if _scalar(child)]
            complex_rows = [(key, child) for key, child in clean.items() if not _scalar(child)]
            if scalar_rows:
                group = QGroupBox(_label(title))
                box = QVBoxLayout(group)
                box.addWidget(_make_table(scalar_rows, ["Result", "Value"]))
                self.layout.addWidget(group)
            for key, child in complex_rows:
                self._render_value(str(key), child, depth + 1)
            return

        if isinstance(value, (list, tuple)):
            rows = list(value)
            if not rows:
                return
            group = QGroupBox(f"{_label(title)} ({len(rows):,})")
            box = QVBoxLayout(group)
            if all(isinstance(row, dict) for row in rows[:200]):
                keys = []
                for row in rows[:100]:
                    for key in row:
                        if key not in _METADATA and key not in keys and _scalar(row.get(key)):
                            keys.append(key)
                        if len(keys) >= 10:
                            break
                if len(keys) == 1 and len(rows) > 12:
                    key = keys[0]
                    counts = Counter(_text(row.get(key)) for row in rows)
                    box.addWidget(_make_table(
                        [[item, f"{count:,}"] for item, count in counts.most_common()],
                        [_label(key), "Occurrences"],
                    ))
                elif keys:
                    box.addWidget(_make_table(
                        [[_text(row.get(key)) for key in keys] for row in rows[:500]],
                        [_label(key) for key in keys],
                    ))
            elif all(isinstance(row, (list, tuple)) for row in rows[:200]) and rows and len(rows[0]) <= 8:
                width = max(len(row) for row in rows[:500])
                headers = ["X", "Z"] if width == 2 and "sample" in str(title).lower() else [f"Value {index + 1}" for index in range(width)]
                box.addWidget(_make_table(
                    [[_text(child) for child in row] + [""] * (width - len(row)) for row in rows[:500]],
                    headers,
                ))
            else:
                box.addWidget(_make_table(
                    [[_text(index + 1), _text(row)] for index, row in enumerate(rows[:500])],
                    ["#", _label(title)],
                ))
            if len(rows) > 500:
                note = QLabel(f"Showing the first 500 of {len(rows):,} rows. Raw data contains the complete result.")
                note.setObjectName("Muted")
                box.addWidget(note)
            self.layout.addWidget(group)
            return

        if value is not None:
            group = QGroupBox(_label(title))
            box = QVBoxLayout(group)
            label = QLabel(_text(value))
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            box.addWidget(label)
            self.layout.addWidget(group)


ResultView = ResultView25
