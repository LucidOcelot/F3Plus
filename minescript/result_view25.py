from __future__ import annotations

"""Concise 2.5 result presentation.

The legacy result renderer remains available for compatibility. This surface removes
boilerplate status/exactness badges, collapses repetitive tables, explains map meaning,
and keeps source/limitations available without repeating them as normal result fields.
"""

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
    "exactness", "accuracy", "model_exactness", "available", "requires_generated_world",
    "requires_seed_worldgen", "reason", "note", "model_limit", "limitation",
}

_LABELS = {
    "candidate_count": "Candidate locations",
    "candidate_counts": "Candidates by type",
    "total_candidates": "Total candidates",
    "distinct": "Distinct biomes",
    "biome_counts": "Biome counts",
    "nearest_samples": "Nearest samples",
    "samples": "Sample locations",
    "radius": "Search radius",
    "configured_maximum_radius": "Configured radius limit",
    "effective_maximum_radius": "Effective radius limit",
    "last_radius_searched": "Last radius searched",
    "found_radius": "Found at radius",
    "attempts": "Search passes",
    "found": "Match found",
    "mode": "Search mode",
    "unit": "Radius unit",
    "seed": "Seed",
    "world_path": "World save",
    "chunks_scanned": "Chunks scanned",
    "count": "Count",
    "mean": "Average",
    "minimum": "Minimum",
    "maximum": "Maximum",
}


def _label(key: str) -> str:
    text = str(key)
    return _LABELS.get(text, text.replace("_", " ").strip().title())


def _warnings(result, visible) -> list[str]:
    rows = []
    note = getattr(result, "note", "")
    if note:
        rows.append(compact_note(note))
    if isinstance(visible, dict):
        for key in ("reason", "limitation", "model_limit"):
            value = visible.get(key)
            if value:
                short = compact_note(value)
                if short not in rows:
                    rows.append(short)
        worldgen = visible.get("worldgen_source")
        if isinstance(worldgen, dict) and worldgen.get("limitation"):
            short = compact_note(worldgen["limitation"])
            if short not in rows:
                rows.append(short)
    return [row for row in rows if row]


def _map_explanation(spec, series) -> str:
    ordered = any(bool(row[2]) for row in series if len(row) >= 3)
    submenu = str(getattr(spec, "submenu", ""))
    if ordered:
        return "X/Z block coordinates. Connected points are shown in route order; +X is east and +Z is south."
    if submenu == "Structures":
        return "Each point is a structure candidate, not a route. Coordinates are X/Z blocks; +X is east and +Z is south."
    if submenu in {"Biomes", "World Analysis", "Spawners", "Local Area"}:
        return "Each point is a sampled or matched world location. Coordinates are X/Z blocks; +X is east and +Z is south."
    return "X/Z block coordinates. Points are independent unless the operation explicitly returns an ordered route."


class ExplainedMap(QFrame):
    def __init__(self, spec, title: str, series, colors, center=None, parent=None):
        super().__init__(parent); self.setObjectName("ResultSection")
        box = QVBoxLayout(self); box.setContentsMargins(8, 8, 8, 8); box.setSpacing(5)
        help_text = QLabel(_map_explanation(spec, series)); help_text.setWordWrap(True); help_text.setObjectName("Muted"); box.addWidget(help_text)
        box.addWidget(InteractiveMap(title, series, colors, center), 1)


class ResultView25(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.NoFrame); outer.addWidget(self.scroll)
        self.host = QWidget(); self.layout = QVBoxLayout(self.host); self.layout.setContentsMargins(8, 8, 8, 8); self.layout.setSpacing(10); self.scroll.setWidget(self.host)
        self.show_empty("Run an operation to see its result.")

    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0); widget = item.widget()
            if widget is not None: widget.deleteLater()

    def show_empty(self, text: str):
        self.clear(); label = QLabel(text); label.setWordWrap(True); label.setObjectName("Muted"); self.layout.addWidget(label); self.layout.addStretch()

    def set_result(self, spec, result, theme: str = "chorus", custom_palette: dict | None = None):
        self.clear(); colors = palette(theme, custom_palette)
        data = getattr(result, "data", result); visible = _presentation_data(data); status = str(getattr(result, "status", "ok"))

        hero = QFrame(); hero.setObjectName("ResultCard"); hv = QVBoxLayout(hero)
        title = QLabel(getattr(spec, "name", "Result")); title.setObjectName("WorkspaceTitle"); hv.addWidget(title)
        if isinstance(visible, dict) and visible.get("purpose"):
            purpose = QLabel(compact_note(visible["purpose"], 180)); purpose.setWordWrap(True); purpose.setObjectName("Muted"); hv.addWidget(purpose)
        if status.lower() not in {"ok", "success"}:
            state = QLabel(status.replace("_", " ").title()); state.setObjectName("VersionChip"); hv.addWidget(state)
        self.layout.addWidget(hero)

        warnings = _warnings(result, visible)
        if warnings:
            banner = QFrame(); banner.setObjectName("WarningBanner"); box = QVBoxLayout(banner); box.setContentsMargins(10, 7, 10, 7)
            for text in warnings:
                label = QLabel(text); label.setWordWrap(True); box.addWidget(label)
            self.layout.addWidget(banner)

        block_layout = layout_layers(spec, visible)
        if block_layout:
            sets, layers = block_layout
            self.layout.addWidget(BlockLayoutPreview(f"{getattr(spec, 'name', 'Shape')} — block layers", sets, layers, colors))
        else:
            series, center = map_series(spec, visible)
            if series:
                self.layout.addWidget(ExplainedMap(spec, f"{getattr(spec, 'name', 'Result')} — locations", series, colors, center))

        chart = chart_series(spec, visible)
        if chart:
            chart_title, rows, kind = chart
            self.layout.addWidget(NumericChart(chart_title, rows, kind, colors))

        self._render_value("Details", visible, 0)

        source = _source_label(data)
        if source and source not in {"F3+ calculation", "F3+ calculation/model"}:
            footer = QLabel(f"Source: {source}"); footer.setWordWrap(True); footer.setObjectName("Muted"); self.layout.addWidget(footer)

        raw_toggle = QToolButton(); raw_toggle.setText("Raw data"); raw_toggle.setCheckable(True); raw_toggle.setArrowType(Qt.RightArrow); self.layout.addWidget(raw_toggle)
        raw = QPlainTextEdit(); raw.setReadOnly(True); raw.setPlainText(json.dumps(visible, indent=2, ensure_ascii=False, default=str)); raw.setMaximumHeight(360); raw.hide(); self.layout.addWidget(raw)
        def show_raw(checked: bool): raw.setVisible(checked); raw_toggle.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        raw_toggle.toggled.connect(show_raw); self.layout.addStretch()

    def _render_value(self, title: str, value: Any, depth: int):
        if depth > 4:
            return
        if isinstance(value, dict):
            clean = {key: child for key, child in value.items() if str(key) not in _METADATA}
            scalar_rows = [[_label(key), _text(child)] for key, child in clean.items() if _scalar(child)]
            complex_rows = [(key, child) for key, child in clean.items() if not _scalar(child)]
            if scalar_rows:
                group = QGroupBox(_label(title)); box = QVBoxLayout(group); box.addWidget(_make_table(scalar_rows, ["Metric", "Value"])); self.layout.addWidget(group)
            for key, child in complex_rows:
                self._render_value(str(key), child, depth + 1)
            return

        if isinstance(value, (list, tuple)):
            rows = list(value)
            if not rows:
                return
            group = QGroupBox(f"{_label(title)} ({len(rows):,})"); box = QVBoxLayout(group)
            if all(isinstance(row, dict) for row in rows[:200]):
                keys = []
                for row in rows[:100]:
                    for key in row:
                        if key not in _METADATA and key not in keys and _scalar(row.get(key)):
                            keys.append(key)
                        if len(keys) >= 10: break
                if len(keys) == 1 and len(rows) > 12:
                    key = keys[0]; counts = Counter(_text(row.get(key)) for row in rows)
                    box.addWidget(_make_table([[value, f"{count:,}"] for value, count in counts.most_common()], [_label(key), "Occurrences"]))
                elif keys:
                    box.addWidget(_make_table([[_text(row.get(key)) for key in keys] for row in rows[:500]], [_label(key) for key in keys]))
            elif all(isinstance(row, (list, tuple)) for row in rows[:200]) and rows and len(rows[0]) <= 8:
                width = max(len(row) for row in rows[:500])
                headers = ["X", "Z"] if width == 2 and "sample" in str(title).lower() else [f"Column {index + 1}" for index in range(width)]
                box.addWidget(_make_table([[_text(child) for child in row] + [""] * (width - len(row)) for row in rows[:500]], headers))
            else:
                box.addWidget(_make_table([[_text(index + 1), _text(row)] for index, row in enumerate(rows[:500])], ["#", "Value"]))
            if len(rows) > 500:
                note = QLabel(f"Showing 500 of {len(rows):,} rows. Raw data keeps the complete result."); note.setObjectName("Muted"); box.addWidget(note)
            self.layout.addWidget(group)
            return

        if value is not None:
            group = QGroupBox(_label(title)); box = QVBoxLayout(group); label = QLabel(_text(value)); label.setWordWrap(True); label.setTextInteractionFlags(Qt.TextSelectableByMouse); box.addWidget(label); self.layout.addWidget(group)


# Keep the old public name for a one-line import swap in workbench wrappers.
ResultView = ResultView25
