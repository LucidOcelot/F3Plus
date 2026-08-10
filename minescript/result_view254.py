from __future__ import annotations

"""2.5.4 result presentation: less boilerplate, more meaning."""

from typing import Any

from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout

from .minecraft_widgets import ExplanationCard
from .result_view import ResultView as _ResultView, _friendly_key, _make_table, _scalar, _text
from .structured_results import _presentation_data
from .visual_contracts import map_series


_METRIC_HELP = {
    "distinct": "Different biomes found in this sample area.",
    "biome_count": "Different biomes found in this sample area.",
    "candidate_count": "Placement candidates represented by this row.",
    "total_candidates": "All placement candidates returned by this search.",
    "attempts": "Search radii actually checked.",
    "last_radius_searched": "Farthest radius reached before the search stopped.",
    "found_radius": "First radius that contained a match.",
    "radius": "Distance from the selected search center.",
    "chunks_scanned": "Generated chunks actually read from the save/reference world.",
    "samples": "Locations or measurements evaluated.",
    "mean": "Arithmetic average across the returned sample.",
    "minimum": "Smallest observed value in the returned sample.",
    "maximum": "Largest observed value in the returned sample.",
    "observed_hit_rate": "Simulated pulls containing this item ÷ total pulls.",
    "mean_items_per_pull": "Total copies observed ÷ total simulated pulls.",
    "total_items": "All copies observed in the simulation.",
    "restocks": "Minimum completed villager restocks needed for the planned uses.",
    "max_uses": "Trades available before the villager must restock.",
}

_OPERATION_READ = {
    "Biome Diversity Finder": "Rows are ranked sample locations. Distinct = number of different biomes found around that location; use X/Z to identify the sample on the map.",
    "Island Finder": "Each result is an island candidate. Coordinates identify the candidate; size/shape fields describe the generated terrain that was inspected.",
    "Structure Cluster Finder": "Each row is a cluster candidate. Candidate Count is how many structure placements contribute to that cluster; the map shows their X/Z locations, not a travel route.",
    "Dungeon/Pig Spawner Locator": "Spawner results are observed saved spawner blocks. If no save is selected, F3+ can generate the bounded area from the seed and scan that reference world.",
    "Ore Distribution": "Counts come from generated block states. The chart compares ore totals; scanned chunks and Y ranges describe the measured coverage.",
    "Ore Exposure Estimate": "Counts are generated ore blocks touching modeled exposed space in the scanned area. This is a measured/generated-world result, not an ore probability chart.",
    "Cave Exposure Estimate": "Measurements describe generated cave air/surface coverage inside the scanned chunks. Use the coverage fields to judge how representative the sample is.",
}

_NOISE_KEYS = {
    "purpose", "source", "data_source", "backend", "exactness", "accuracy",
    "model_exactness", "available", "operation", "worldgen_source",
}


def _compact(text: str, limit: int = 240) -> str:
    full = " ".join(str(text or "").split())
    replacements = (
        ("F3+ will not pretend ", "Does not treat "),
        ("This operation needs generated Java world data. ", "Needs generated world data. "),
        ("Select a save or run it with exact Mojang reference-world generation after accepting the EULA.", "Choose a save, or choose Seed and allow local reference-world generation."),
        ("Configured maximum radius/generation limits are ignored for this run. ", "Maximum radius is ignored. "),
    )
    for old, new in replacements: full = full.replace(old, new)
    if len(full) <= limit: return full
    cut = full[:limit].rsplit(" ", 1)[0].rstrip(" ,;:")
    return cut + "…"


def _coords(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for key, x_name, z_name in (
        ("center", "x", "z"), ("position", "x", "z"), ("point", "x", "z"),
        ("chunk", "chunk_x", "chunk_z"), ("center_chunk", "chunk_x", "chunk_z"),
    ):
        value = out.get(key)
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            out.setdefault(x_name, value[0]); out.setdefault(z_name, value[-1])
    return out


class ResultView(_ResultView):
    def set_result(self, spec, result, theme: str = "chorus", custom_palette: dict | None = None):
        super().set_result(spec, result, theme, custom_palette)
        data = getattr(result, "data", result); visible = _presentation_data(data)

        # Successful status is implicit. Keep unusual statuses and meaningful source
        # badges, but remove generic model boilerplate from the top of every result.
        for label in self.findChildren(QLabel):
            text = label.text().strip()
            if text.lower() == "status: ok": label.hide()
            elif text.lower() in {"exactness: calculated / model", "source: f3+ calculation/model"}: label.hide()

        for banner in self.findChildren(QLabel):
            parent = banner.parentWidget()
            if parent is not None and parent.objectName() == "WarningBanner":
                original = banner.text(); banner.setToolTip(original); banner.setText(_compact(original))

        read = _OPERATION_READ.get(getattr(spec, "name", ""))
        series, center = map_series(spec, visible)
        if series:
            layer_names = ", ".join(str(row[0]) for row in series[:4])
            map_note = f"Map: X increases east, Z increases south; grid values are blocks. Points are independent locations unless the layer is explicitly a route. Layers: {layer_names}."
            if center is not None: map_note += f" Ring marker = search center ({center[0]:g}, {center[1]:g})."
            read = (read + " " if read else "") + map_note
        if read:
            card = ExplanationCard("Read this result", read)
            self.layout.insertWidget(1, card)

    def _render_value(self, title: str, value: Any, depth: int):
        if depth > 4: return
        if isinstance(value, dict):
            clean = {key: child for key, child in value.items() if str(key) not in _NOISE_KEYS and not str(key).startswith("_")}
            scalar = []
            for key, child in clean.items():
                if not _scalar(child): continue
                meaning = _METRIC_HELP.get(str(key), "")
                scalar.append([_friendly_key(key), _text(child), meaning])
            complex_rows = [(key, child) for key, child in clean.items() if not _scalar(child)]
            if scalar:
                group = QGroupBox(_friendly_key(title)); box = QVBoxLayout(group)
                headers = ["Metric", "Value", "Meaning"] if any(row[2] for row in scalar) else ["Metric", "Value"]
                rows = scalar if len(headers) == 3 else [row[:2] for row in scalar]
                box.addWidget(_make_table(rows, headers)); self.layout.addWidget(group)
            for key, child in complex_rows: self._render_value(str(key), child, depth + 1)
            if not clean:
                return
            return
        if isinstance(value, (list, tuple)) and value and all(isinstance(row, dict) for row in value[:200]):
            rows = [_coords(dict(row)) for row in value]
            keys = []
            preferred = ("x", "z", "chunk_x", "chunk_z", "distinct", "biome_count", "candidate_count", "distance", "score", "count", "type", "name")
            for key in preferred:
                if any(_scalar(row.get(key)) and key in row for row in rows): keys.append(key)
            for row in rows[:100]:
                for key, child in row.items():
                    if key in keys or key in _NOISE_KEYS or not _scalar(child): continue
                    keys.append(key)
                    if len(keys) >= 10: break
                if len(keys) >= 10: break
            group = QGroupBox(f"{_friendly_key(title)} ({len(rows):,})"); box = QVBoxLayout(group)
            if keys:
                box.addWidget(_make_table([[_text(row.get(key)) for key in keys] for row in rows[:500]], [_friendly_key(key) for key in keys]))
            else:
                empty = QLabel("No displayable fields returned for these rows."); empty.setObjectName("Muted"); box.addWidget(empty)
            if len(rows) > 500:
                note = QLabel(f"Showing 500 of {len(rows):,} rows. Raw data retains all rows."); note.setObjectName("Muted"); box.addWidget(note)
            self.layout.addWidget(group); return
        super()._render_value(title, value, depth)
