from __future__ import annotations

"""Public operation explorer UX for F3+."""

from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit, QVBoxLayout, QWidget

from .async_workbench import OperationDialog as _AsyncOperationDialog
from .field_semantics import field_help
from .guide_metadata import OUTPUT_KEYS
from .result_view254 import ResultView
from .seed_text import DEFAULT_SEED_TEXT
from .ui_dialogs import make_widget, widget_value
from .workbench_forms import _operation_description


_CONCISE_HELP = {
    "Island Finder": "Finds island candidates around the selected center.",
    "Biome Diversity Finder": "Ranks sample locations by how many different biomes occur nearby.",
    "Structure Cluster Finder": "Ranks locations where multiple structure candidates occur close together.",
    "Dungeon/Pig Spawner Locator": "Finds saved dungeon/pig spawner blocks in a save, or generates the search area from a seed.",
    "Double Spawner Locator": "Finds pairs of saved spawners that can be active from one player position.",
    "Triple Spawner Locator": "Finds three-spawner groups that can be active from one player position.",
    "Quad Spawner Locator": "Finds four-spawner groups that can be active from one player position.",
    "Ore Distribution": "Counts generated ore blocks by ore type and Y level in the selected area.",
    "Ore Exposure Estimate": "Counts generated ore blocks exposed to modeled cave/air surfaces in the selected area.",
    "Cave Exposure Estimate": "Measures generated cave air and cave-surface coverage in the selected area.",
    "Terrain Base Finder": "Ranks generated terrain areas suitable for a broad, relatively level base.",
    "Largest Cave Region": "Finds the largest connected cave region in the generated area.",
}

_OUTPUT_EXPLANATIONS = {
    "Island Finder": "Island X/Z coordinates and terrain size/shape measurements.",
    "Biome Diversity Finder": "Ranked X/Z sample locations and distinct-biome count.",
    "Structure Cluster Finder": "Cluster X/Z locations, candidate count, represented structures, and spread.",
    "Dungeon/Pig Spawner Locator": "Spawner X/Y/Z, mob type, searched radius, and stop reason when nothing can be searched.",
    "Double Spawner Locator": "Spawner-pair coordinates and shared activation geometry.",
    "Triple Spawner Locator": "Three-spawner coordinates and shared activation geometry.",
    "Quad Spawner Locator": "Four-spawner coordinates and shared activation geometry.",
    "Ore Distribution": "Ore totals by type/Y level, measured chunk coverage, and a labeled chart.",
    "Ore Exposure Estimate": "Exposed ore totals by type plus measured chunk coverage.",
    "Cave Exposure Estimate": "Cave-air/surface measurements plus measured chunk coverage.",
    "Ancient City Area Analysis": "Ancient City candidate X/Z locations and area measurements.",
    "Structure Finder": "Candidate X/Z locations, structure type, and source/exactness; points are not connected as a route.",
}

_INTERNAL_OUTPUT_KEYS = {
    "implementation", "safety", "policy", "source_available", "executable", "source_dir",
    "automatic_acquisition", "backend", "backend_error", "note", "source", "operation",
    "parser", "method", "ready", "allowed", "persistent", "storage",
}
_OUTPUT_NAMES = {
    "dx": "X delta", "dy": "Y delta", "dz": "Z delta", "x": "X", "y": "Y", "z": "Z",
    "horizontal": "horizontal distance", "distance_3d": "3D distance", "seconds": "travel time",
    "candidate_chunks": "candidate chunk coordinates", "candidate_sets": "candidate locations",
    "nearest": "nearest match", "ranked": "ranked matches", "matches": "matching locations",
    "count": "match count", "density": "density", "radius": "radius", "route": "ordered route",
    "points": "block coordinates", "volume": "block volume", "area": "area", "perimeter": "perimeter",
    "materials": "material totals", "total": "total", "probability": "probability", "odds": "odds",
    "mean": "average", "minimum": "minimum", "maximum": "maximum", "spread": "spread",
    "biome_counts": "biome counts", "samples": "sample locations", "nearest_samples": "nearest samples",
    "ore_counts": "ore totals", "chunks_scanned": "chunks scanned", "links": "portal links",
    "cycles": "loops/cycles", "converted": "converted coordinates", "midpoint": "midpoint",
    "bearing": "bearing", "cardinal": "cardinal direction", "result": "calculated result",
}

_INLINE_KEYS = {
    "seed", "world_path", "search_mode", "radius", "radius_step", "max_search_radius",
    "worldgen_max_chunks", "target_biome", "probability", "attempts",
}


def _concise_description(mode) -> str:
    if mode is None: return ""
    if mode.name in _CONCISE_HELP: return _CONCISE_HELP[mode.name]
    text = " ".join(_operation_description(mode).split()); prefix = mode.name + " "
    if text.startswith(prefix): text = text[len(prefix):]
    text = text[:1].upper() + text[1:] if text else mode.name
    if len(text) > 190:
        text = text[:190].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return text


def _friendly_output_key(key: str) -> str:
    key = str(key); return _OUTPUT_NAMES.get(key, key.replace("_", " "))


def _output_explanation(mode) -> str:
    if mode is None or mode.legacy is None: return "Result for the selected operation."
    if mode.name in _OUTPUT_EXPLANATIONS: return _OUTPUT_EXPLANATIONS[mode.name]
    keys = OUTPUT_KEYS.get(mode.legacy.id, [])
    useful = []
    for key in keys:
        if key in _INTERNAL_OUTPUT_KEYS or str(key).startswith("_"): continue
        label = _friendly_output_key(key)
        if label not in useful: useful.append(label)
        if len(useful) >= 6: break
    if useful:
        return "Returns " + ", ".join(useful) + "."
    name = mode.name.lower()
    if any(token in name for token in ("finder", "locator", "nearest", "search")): return "Matching locations with coordinates, distance/search coverage, and match details."
    if any(token in name for token in ("route", "tour", "path")): return "Ordered stops/coordinates with route distance and direction where applicable."
    if any(token in name for token in ("probability", "odds", "chance")): return "Calculated probability plus attempt/confidence values used by this operation."
    if any(token in name for token in ("planner", "calculator", "estimate", "optimizer")): return f"{mode.name} calculation with labeled quantities and units."
    return f"{mode.name} result with labeled values relevant to this operation."


def _short_hint(key: str, label: str, default, kind: str) -> str:
    if key not in _INLINE_KEYS: return ""
    if key == "seed": return f"Number or text seed. Blank = {DEFAULT_SEED_TEXT}."
    if key == "world_path": return "Existing Java world folder. Leave blank when using Seed as the data source."
    base = field_help(key, label).split(". ", 1)[0].rstrip(".") + "."
    if kind in {"int", "float"}: base += f" Default: {default}."
    return base


class OperationDialog(_AsyncOperationDialog):
    def __init__(self, *args, **kwargs):
        self.world_source_mode = None
        super().__init__(*args, **kwargs)
        old = self.result_view; replacement = ResultView(self); index = self.pages.indexOf(old)
        if index >= 0:
            self.pages.removeWidget(old); old.deleteLater(); self.pages.insertWidget(index, replacement)
        self.result_view = replacement
        for label in self.context_card.findChildren(QLabel):
            if label.text() == "EXPECTED OUTPUT": label.setText("RESULT")

    def _field_editor(self, key: str, label: str, default, kind: str):
        widget = make_widget(kind, default); tip = field_help(key, label).strip(); widget.setToolTip(tip); widget.setAccessibleDescription(tip)
        column = QWidget(); layout = QVBoxLayout(column); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(3); layout.addWidget(widget)
        hint_text = _short_hint(key, label, default, kind)
        if hint_text:
            hint = QLabel(hint_text); hint.setWordWrap(True); hint.setObjectName("Muted"); layout.addWidget(hint)
        return widget, column

    def _rebuild(self):
        super()._rebuild(); self.world_source_mode = None
        if self.mode is None or self.mode.legacy is None: return
        self.mode_help.setText(_concise_description(self.mode)); self.output_help.setText(_output_explanation(self.mode))

        seed = self.inputs.get("seed")
        if isinstance(seed, QLineEdit):
            configured = getattr(self.settings, "seed", None); seed.setText(str(configured) if configured not in (None, "") else DEFAULT_SEED_TEXT)

        if "world_path" in self.inputs and "regenerate_from_seed" in self.inputs:
            source = QComboBox(); source.addItems(["Seed", "World save"]); source.setToolTip("Seed generates the required reference area. World save reads an existing Java save.")
            self.world_source_mode = source; self.form.insertRow(0, "Data source", source)
            regen = self.inputs.get("regenerate_from_seed")
            if regen is not None:
                editor = regen.parentWidget(); label = self.form.labelForField(editor) if editor is not None else None
                if label is not None: label.hide()
                if editor is not None: editor.hide()
            world = self.inputs.get("world_path")
            if isinstance(world, QLineEdit) and world.text().strip(): source.setCurrentText("World save")
            source.currentTextChanged.connect(self._sync_world_source); self._sync_world_source()

    def _sync_world_source(self):
        if self.world_source_mode is None: return
        use_seed = self.world_source_mode.currentText() == "Seed"
        for key in ("seed", "accept_minecraft_eula", "worldgen_max_chunks"):
            widget = self.inputs.get(key)
            if widget is not None: widget.setEnabled(use_seed)
        world = self.inputs.get("world_path")
        if world is not None: world.setEnabled(not use_seed)
        self.note.setText("Seed: generate the bounded reference area locally, then scan it." if use_seed else "World save: read the selected Java save locally.")
        self._sync_search()

    def _sync_search(self):
        mode = self.inputs.get("search_mode")
        if not isinstance(mode, QComboBox): return
        until = mode.currentText() == "Search until found"; ignore = self.inputs.get("ignore_max_generation_limit"); unlimited = bool(ignore.isChecked()) if isinstance(ignore, QCheckBox) else False
        for key in ("radius_step", "max_search_radius", "ignore_max_generation_limit"):
            widget = self.inputs.get(key)
            if widget is not None: widget.setEnabled(until)
        maximum = self.inputs.get("max_search_radius")
        if maximum is not None and until: maximum.setEnabled(not unlimited)
        budget = self.inputs.get("worldgen_max_chunks"); use_seed = self.world_source_mode is None or self.world_source_mode.currentText() == "Seed"
        if budget is not None: budget.setEnabled(use_seed and not (until and unlimited))
        if not until: text = "Searches once inside the selected radius."
        elif unlimited: text = "Expands until a match or a real backend/prerequisite failure stops the search."
        else: text = "Expands by the selected step until a match or the maximum radius is reached."
        self.search_help.setText(text)

    def values(self):
        values = {key: widget_value(widget) for key, widget in self.inputs.items()}
        if self.world_source_mode is not None:
            use_seed = self.world_source_mode.currentText() == "Seed"; values["regenerate_from_seed"] = use_seed
            if use_seed: values["world_path"] = ""
        return values
