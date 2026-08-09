from __future__ import annotations

"""Final desktop readability pass: compact results, semantic tables and focused forms."""

import math
import re
from typing import Any


def _pretty_label(key: str) -> str:
    overrides = {
        "available": "Status",
        "requires_seed_worldgen": "Generated terrain",
        "requires_generated_world": "Generated world",
        "requested_radius_chunks": "Scan radius (chunks)",
        "radius_chunks": "Radius (chunks)",
        "seed": "World seed",
        "version": "Minecraft version",
        "selected_version": "Selected Minecraft version",
        "source_version": "Data source version",
        "matches_found": "Matches found",
        "chunks_scanned": "Chunks scanned",
        "region_files_scanned": "Region files scanned",
    }
    if key in overrides:
        return overrides[key]
    return str(key).replace("_", " ").strip().title()


def _friendly_value(key: str, value: Any) -> str:
    low = str(key).lower()
    if isinstance(value, bool):
        if low == "available":
            return "Ready" if value else "Unavailable"
        if low.startswith("requires_"):
            return "Required" if value else "Not required"
        if "enabled" in low:
            return "Enabled" if value else "Disabled"
        return "Yes" if value else "No"
    if isinstance(value, float):
        if any(token in low for token in ("density", "share", "ratio", "rate")) and 0 <= value <= 1:
            return f"{value * 100:.2f}%"
        if low.endswith("seconds") or low == "seconds":
            if value >= 3600:
                return f"{value / 3600:.2f} hr"
            if value >= 60:
                return f"{value / 60:.1f} min"
            return f"{value:.2f} sec"
        return f"{value:,.3f}".rstrip("0").rstrip(".")
    if isinstance(value, int):
        return f"{value:,}"
    text = str(value)
    if text.startswith("minecraft:"):
        return text.removeprefix("minecraft:").replace("_", " ").title()
    return text


def _coordinate_rows(name: str, value: list | tuple) -> list[dict[str, Any]] | None:
    if not value or not all(isinstance(row, (list, tuple)) for row in value):
        return None
    widths = {len(row) for row in value if isinstance(row, (list, tuple))}
    if len(widths) != 1:
        return None
    width = next(iter(widths))
    low = name.lower()
    chunkish = any(token in low for token in (
        "candidate", "chunk", "village", "trial chamber", "ocean monument", "outpost",
        "ancient city", "ruined portal", "slime", "fortress", "bastion", "end city",
    ))
    rows = []
    if width == 2:
        for row in value[:250]:
            x, z = row
            if chunkish and isinstance(x, (int, float)) and isinstance(z, (int, float)):
                rows.append({
                    "Chunk X": x, "Chunk Z": z,
                    "Block center X": int(x) * 16 + 8,
                    "Block center Z": int(z) * 16 + 8,
                })
            else:
                rows.append({"X": x, "Z": z})
        return rows
    if width == 3:
        biome_like = "biome" in low or "sample" in low
        for row in value[:250]:
            a, b, c = row
            if biome_like and all(isinstance(q, (int, float)) for q in row):
                try:
                    from .analysis_reports_v2 import biome_name
                    label = biome_name(c)
                except Exception:
                    label = str(c)
                rows.append({"Block X": a, "Block Z": b, "Biome": label})
            else:
                rows.append({"X": a, "Y": b, "Z": c})
        return rows
    if width == 4 and all(isinstance(row[0], str) for row in value):
        return [{"Name": row[0], "X": row[1], "Y": row[2], "Z": row[3]} for row in value[:250]]
    return None


def _construction_fields(name: str):
    schemas = {
        "Area": [("width", "Width (blocks)", 16, "int"), ("length", "Length (blocks)", 20, "int")],
        "Perimeter": [("width", "Width (blocks)", 16, "int"), ("length", "Length (blocks)", 20, "int")],
        "Foundation Planner": [("width", "Foundation width", 16, "int"), ("length", "Foundation length", 20, "int")],
        "Volume": [("width", "Width", 16, "int"), ("length", "Length", 20, "int"), ("height", "Height", 8, "int")],
        "Surface Area": [("width", "Width", 16, "int"), ("length", "Length", 20, "int"), ("height", "Height", 8, "int")],
        "Block Count": [("width", "Width", 16, "int"), ("length", "Length", 20, "int"), ("height", "Height", 8, "int")],
        "Stacks": [("width", "Build width", 16, "int"), ("length", "Build length", 20, "int"), ("height", "Build height", 8, "int")],
        "Shulkers": [("width", "Build width", 16, "int"), ("length", "Build length", 20, "int"), ("height", "Build height", 8, "int")],
        "Double Chests": [("width", "Build width", 16, "int"), ("length", "Build length", 20, "int"), ("height", "Build height", 8, "int")],
        "Stair Calculator": [("height", "Vertical rise (blocks)", 8, "int"), ("spacing", "Horizontal run per step", 1, "int")],
        "Spiral Staircase Planner": [("width", "Diameter (blocks)", 9, "int"), ("height", "Total height", 16, "int"), ("spacing", "Steps per turn", 12, "int")],
        "Catenary Calculator": [("length", "Span (blocks)", 32, "int"), ("sag", "Center sag (blocks)", 6.0, "float"), ("height", "End height difference", 0, "int")],
        "Roof Pitch": [("width", "Horizontal run", 12, "int"), ("height", "Vertical rise", 6, "int")],
        "Wall Segments": [("width", "Width", 16, "int"), ("length", "Length", 20, "int"), ("spacing", "Target segment length", 4, "int")],
        "Bridge Span": [("length", "Bridge span", 64, "int"), ("spacing", "Support spacing", 8, "int")],
        "Grid": [("width", "Grid width", 32, "int"), ("length", "Grid length", 32, "int"), ("spacing", "Grid spacing", 4, "int")],
        "Lighting Grid": [("width", "Area width", 32, "int"), ("length", "Area length", 32, "int"), ("spacing", "Light spacing", 8, "int")],
        "Pillar Spacing": [("width", "Structure width", 32, "int"), ("length", "Structure length", 32, "int"), ("spacing", "Maximum pillar spacing", 8, "int")],
        "Road Planner": [("length", "Road length", 128, "int"), ("width", "Road width", 5, "int"), ("spacing", "Marker spacing", 16, "int")],
        "Crop Layout": [("width", "Farm width", 32, "int"), ("length", "Farm length", 32, "int"), ("spacing", "Crop spacing", 1, "int")],
        "Gradient Ratio": [("length", "Horizontal run", 32, "int"), ("height", "Vertical rise", 8, "int")],
        "Chunk Grid Builder": [("width", "Width (blocks)", 64, "int"), ("length", "Length (blocks)", 64, "int")],
        "Beacon Offset": [("width", "Build width", 32, "int"), ("length", "Build length", 32, "int"), ("height", "Beacon pyramid level", 4, "int")],
    }
    return schemas.get(name)


def _shape_fields(name: str):
    if name in {"Circle", "Filled Circle", "Sphere", "Hollow Sphere", "Dome", "Hexagon", "Octagon", "Diamond", "Arch"}:
        return [("radius", "Radius (blocks)", 8, "int")]
    if name in {"Cylinder", "Cone"}:
        return [("radius", "Radius (blocks)", 8, "int"), ("height", "Height (blocks)", 12, "int")]
    if name in {"Spiral", "Helix", "Double Helix"}:
        return [("radius", "Radius", 8, "int"), ("height", "Height / turns", 12, "int")]
    if name == "Ellipse":
        return [("radius", "X radius", 8, "int"), ("secondary", "Z radius", 5, "int")]
    if name == "Pyramid":
        return [("radius", "Base half-width", 8, "int"), ("height", "Height", 8, "int")]
    if name == "Rounded Rectangle":
        return [("radius", "Corner radius", 4, "int"), ("secondary", "Straight section", 12, "int")]
    return None


def _farm_fields(name: str):
    schemas = {
        "Crop Yield": [("units", "Plants", 64, "int"), ("hours", "Harvest cycles", 1.0, "float")],
        "Tree Yield": [("units", "Trees", 64, "int"), ("hours", "Harvest cycles", 1.0, "float")],
        "Animal Breeding": [("units", "Starting adult animals", 16, "int"), ("hours", "Breeding cycles", 3.0, "float")],
        "Villager Breeding": [("units", "Planned breedings", 10, "int")],
        "Furnace Array": [("units", "Furnaces", 16, "int"), ("hours", "Run time (hours)", 1.0, "float")],
        "Fuel Optimizer": [("units", "Items to smelt", 128, "int")],
        "Sugar Cane Layout": [("units", "Cane positions", 64, "int"), ("spacing", "Position spacing", 1, "int")],
        "Bamboo Layout": [("units", "Bamboo positions", 64, "int"), ("spacing", "Position spacing", 1, "int")],
        "Crop Row Calculator": [("units", "Crop positions", 64, "int"), ("spacing", "Row spacing", 1, "int")],
        "Kelp Tower": [("units", "Columns", 8, "int"), ("spacing", "Tower height", 32, "int")],
        "Bee Apiary": [("units", "Beehives", 8, "int"), ("spacing", "Hive spacing", 3, "int")],
        "Villager Hall Layout": [("units", "Villagers / stations", 20, "int"), ("spacing", "Station spacing", 1, "int")],
        "Animal Pen": [("units", "Animals", 20, "int")],
        "Beacon Pyramid": [("units", "Beacons", 1, "int"), ("spacing", "Pyramid level", 4, "int")],
        "Beacon Coverage": [("spacing", "Beacon level", 4, "int")],
    }
    return schemas.get(name)


def install() -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractItemView, QFrame, QGridLayout, QHeaderView, QLabel, QTableWidget, QTableWidgetItem,
        QVBoxLayout,
    )

    from . import app as app_module, ui_theme
    from .app import F3Plus
    from .feature_executor import FeatureExecutor
    from .villager_explorer import MinecraftTextureProvider, VillagerExplorer
    from .villagers import BASELINE_SOURCE, installed_versions, preferred_texture_version

    if getattr(F3Plus, "_ui_polish_v3_installed", False):
        return

    # Keep the dramatic theme identity, but stop result values from becoming billboard text.
    old_stylesheet = ui_theme.stylesheet
    def stylesheet(theme="chorus", custom=None):
        base = old_stylesheet(theme, custom)
        return base + """
        QLabel#WorkspaceTitle { font-size: 15pt; font-weight: 750; }
        QLabel#DetailTitle { font-size: 17pt; font-weight: 800; }
        QLabel#MetricValue { font-size: 12.5pt; font-weight: 700; }
        QLabel#MetricLabel { font-size: 8.25pt; }
        QFrame#ResultMetric { min-height: 44px; }
        QFrame#ResultSection { margin: 0px; }
        QTableWidget { font-size: 9pt; gridline-color: palette(mid); }
        QHeaderView::section { padding: 5px 7px; font-size: 8.5pt; font-weight: 700; }
        QListWidget#TradeCardList::item { margin: 1px 0px; }
        """
    ui_theme.stylesheet = stylesheet
    if hasattr(app_module, "stylesheet"):
        app_module.stylesheet = stylesheet

    # Baseline trade rows can still use textures from the newest useful installed JAR.
    old_texture_init = MinecraftTextureProvider.__init__
    def texture_init(self, source_version, theme, custom_palette=None):
        old_texture_init(self, source_version, theme, custom_palette)
        if self.jar is None:
            texture_version = preferred_texture_version(source_version)
            if texture_version:
                self.source_version = texture_version
                self.jar = installed_versions().get(texture_version)
    MinecraftTextureProvider.__init__ = texture_init

    old_explorer_init = VillagerExplorer.__init__
    def explorer_init(self, *args, **kwargs):
        old_explorer_init(self, *args, **kwargs)
        for index in range(1, self.level.count()):
            level = int(self.level.itemData(index) or index)
            self.level.setItemText(index, f"{self.level.itemText(index).split('—')[-1].strip()} (level {level})")
        if self.source_version == BASELINE_SOURCE:
            for label in self.findChildren(QLabel):
                if label.text().startswith("Trade data:"):
                    label.setText("Trade data: baseline reference")
                    label.setToolTip(
                        "No installed JAR exposed data-driven villager trade JSON. F3+ is showing an explicitly labeled baseline planning reference; verify exact offers in-game."
                    )
                elif label.text().startswith("Browse trades visually"):
                    label.setText("Browse real installed trade JSON when available; otherwise use the clearly labeled baseline planning reference.")
    VillagerExplorer.__init__ = explorer_init

    previous_fields = FeatureExecutor.input_fields
    def input_fields(self, feature):
        spec = self.spec(feature)
        if spec.top == "Calculators" and spec.submenu == "Build":
            schema = _construction_fields(spec.name)
            if schema:
                return schema
        if spec.top == "Calculators" and spec.submenu == "Shapes":
            schema = _shape_fields(spec.name)
            if schema:
                return schema
        if spec.top == "Calculators" and spec.submenu == "Farm":
            schema = _farm_fields(spec.name)
            if schema:
                return schema
        return previous_fields(self, feature)
    FeatureExecutor.input_fields = input_fields

    result_class_patched = {"done": False}

    def patch_result_class(cls):
        if result_class_patched["done"]:
            return

        def add_metrics(self, rows):
            compact = []
            long_rows = []
            for label, value in rows:
                key = str(label)
                rendered = _friendly_value(key, value)
                if len(rendered) > 90 or key.lower() in {"reason", "purpose", "note", "next step", "interpretation", "ranking basis"}:
                    long_rows.append((_pretty_label(key), rendered))
                else:
                    compact.append((_pretty_label(key), rendered))
            if compact:
                card = QFrame(); card.setObjectName("ResultSection")
                grid = QGridLayout(card); grid.setContentsMargins(10, 8, 10, 8); grid.setHorizontalSpacing(14); grid.setVerticalSpacing(4)
                columns = 2
                for index, (label, value) in enumerate(compact[:24]):
                    name = QLabel(label); name.setObjectName("MetricLabel"); name.setWordWrap(True)
                    val = QLabel(value); val.setTextInteractionFlags(Qt.TextSelectableByMouse); val.setWordWrap(True)
                    grid.addWidget(name, index // columns, (index % columns) * 2)
                    grid.addWidget(val, index // columns, (index % columns) * 2 + 1)
                self.layout.addWidget(card)
            for label, value in long_rows:
                self._add_text_section(label, value)

        def add_table(self, name, rows):
            preview = rows[:200]
            columns = []
            for row in preview:
                for key in row:
                    if key not in columns:
                        columns.append(key)
            columns = columns[:12]
            card = QFrame(); card.setObjectName("ResultSection")
            layout = QVBoxLayout(card); layout.setContentsMargins(10, 8, 10, 10); layout.setSpacing(6)
            title = QLabel(str(name).upper()); title.setObjectName("DeckLabel"); layout.addWidget(title)
            if len(rows) > len(preview):
                note = QLabel(f"Showing {len(preview):,} of {len(rows):,} rows."); note.setObjectName("Muted"); layout.addWidget(note)
            table = QTableWidget(len(preview), len(columns))
            table.setHorizontalHeaderLabels([_pretty_label(column) for column in columns])
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setAlternatingRowColors(True)
            table.verticalHeader().setVisible(False)
            for r, row in enumerate(preview):
                for c, key in enumerate(columns):
                    table.setItem(r, c, QTableWidgetItem(_friendly_value(str(key), row.get(key, ""))))
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            table.horizontalHeader().setStretchLastSection(True)
            table.setMinimumHeight(min(360, 56 + max(1, len(preview)) * 23))
            layout.addWidget(table)
            self.layout.addWidget(card)

        def render_value(self, name, value):
            if isinstance(value, dict):
                prose_keys = {"purpose", "reason", "next_step", "interpretation", "note", "ranking_basis", "classification_basis", "cluster_rule", "metric_warning"}
                for key in prose_keys:
                    if key in value and not isinstance(value[key], (dict, list, tuple)):
                        self._add_text_section(_pretty_label(key), _friendly_value(key, value[key]))
                scalars = [
                    (str(key), child) for key, child in value.items()
                    if key not in prose_keys and not isinstance(child, (dict, list, tuple))
                ]
                if scalars:
                    add_metrics(self, scalars)
                for key, child in value.items():
                    if isinstance(child, (dict, list, tuple)):
                        render_value(self, _pretty_label(str(key)), child)
                if not value:
                    self._add_text_section(name, "No additional details.")
                return
            if isinstance(value, (list, tuple)):
                if not value:
                    self._add_text_section(name, "No matches in the scanned area.")
                    return
                if all(isinstance(row, dict) for row in value):
                    add_table(self, name, list(value))
                    return
                semantic = _coordinate_rows(name, list(value))
                if semantic is not None:
                    add_table(self, name, semantic)
                    return
                self._add_text_section(name, "\n".join(f"{i + 1}. {_friendly_value(name, row)}" for i, row in enumerate(value[:250])))
                return
            self._add_text_section(name, _friendly_value(name, value))

        cls._add_metrics = add_metrics
        cls._add_table = add_table
        cls._render_value = render_value
        result_class_patched["done"] = True

    previous_init = F3Plus.__init__
    previous_write = F3Plus.write
    def f3_init(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        patch_result_class(type(self.output))
    def write(self, text):
        try:
            self.output._f3plus_spec = self.selected_spec()
        except Exception:
            pass
        return previous_write(self, text)
    F3Plus.__init__ = f3_init
    F3Plus.write = write
    F3Plus._ui_polish_v3_installed = True
