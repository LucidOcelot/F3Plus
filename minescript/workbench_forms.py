from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
    QSplitter, QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .descriptions import PRECISE, SPECIAL
from .feature_executor import FeatureExecutor, MACRO_NAMES
from .guide_metadata import OUTPUT_KEYS
from .result_view import ResultView
from .tool_registry import ToolMode, ToolSpec, modes_for
from .ui_dialogs import field_help, make_widget, widget_value


_CONTROL_DELEGATES = {
    "Current Position", "Capture Position", "Copy Sister Coordinates", "Save Sister Waypoint",
    "Minecraft Version", "Emergency Stop", "Pause/Resume", "Release Held Inputs",
    "Refresh Trades From Installed Version",
}


_DOMAIN_PURPOSE = {
    ("Navigation", "Coordinates"): "Calculates coordinate geometry, distance, direction, chunk/region positions, or travel measurements from the coordinates you enter.",
    ("Navigation", "Routes"): "Builds or analyzes routes and surveys from entered, saved, or recorded Minecraft positions.",
    ("Navigation", "Portal Helpers"): "Calculates portal coordinates, link competition, routing, and network geometry.",
    ("Seed Tools", "Slime"): "Finds and compares slime chunks for the selected Java world seed and search area.",
    ("Seed Tools", "Structures"): "Finds or compares structure placement locations around the selected center.",
    ("Seed Tools", "Spawners"): "Reads generated Java world data to find saved spawners and spawner groups.",
    ("Seed Tools", "Biomes"): "Finds or measures biome and terrain information around the selected location.",
    ("Seed Tools", "Local Area"): "Summarizes a bounded area for building, technical planning, or exploration.",
    ("Seed Tools", "World Analysis"): "Measures spawn, loading, resource, or suitability information for a world area.",
    ("Seed Tools", "Nether"): "Finds Nether locations or calculates Nether travel and portal-network behavior.",
    ("Calculators", "Coordinate"): "Calculates distance, direction, coordinate conversion, or travel values.",
    ("Calculators", "Build"): "Calculates build dimensions, spacing, materials, or layout measurements.",
    ("Calculators", "Shapes"): "Generates a Minecraft block layout for the selected geometric shape.",
    ("Calculators", "Redstone"): "Calculates redstone timing, signal delays, or component throughput.",
    ("Calculators", "Storage"): "Converts item totals into stack, container, shulker, or transport requirements.",
    ("Calculators", "Farm"): "Calculates farm dimensions, capacity, yield, breeding, or supporting infrastructure.",
    ("Calculators", "Technical"): "Calculates technical spacing, loading, spawning, alignment, or perimeter geometry.",
    ("Calculators", "Speedrunning"): "Calculates route, triangulation, or coordinate values from speedrun observations.",
    ("Calculators", "Resource Usage"): "Calculates resource, XP, durability, fuel, or consumable requirements.",
    ("Calculators", "End"): "Calculates End travel, gateway, or coordinate-planning values.",
    ("RNG Tools", "Enchanting"): "Models enchanting offers, costs, or repeatable enchanting sequences.",
    ("RNG Tools", "Probability"): "Calculates probability or displays deterministic RNG sequences.",
    ("RNG Tools", "Generation RNG"): "Displays generation-stage RNG values and modeled feature attempts.",
}


_EXPLANATION_OVERRIDES = {
    "Arch": "Builds the upper half of a hollow block circle. Width is about 2×radius + 1 blocks and height is about the radius.",
    "Rounded Rectangle": "Builds a rounded rectangular footprint from its size and corner radius.",
    "Diamond": "Builds a diamond-shaped block outline from the selected radius.",
    "Pyramid": "Builds stacked square layers for a pyramid from base radius and height.",
    "Ellipse": "Builds an elliptical block outline from horizontal and vertical radii.",
    "Hexagon": "Builds a hexagonal block outline from the selected radius.",
    "Octagon": "Builds an octagonal block outline from the selected radius.",
    "Circle": "Builds a hollow block circle from the selected radius.",
    "Filled Circle": "Builds a filled block circle from the selected radius.",
    "Sphere": "Builds a solid block sphere from the selected radius.",
    "Hollow Sphere": "Builds only the outer shell of a block sphere.",
    "Dome": "Builds the upper portion of a block sphere as a dome.",
    "Cylinder": "Builds a cylindrical block layout from radius and height.",
    "Cone": "Builds a tapered cone from radius and height.",
    "Spiral": "Builds a flat X/Z spiral path from radius and turn count.",
    "Helix": "Builds a three-dimensional helix from radius, height, and turn count.",
    "Double Helix": "Builds two phase-offset helices around the same axis.",
}


_GROUP_LABELS = {
    "Coordinates": "Coordinate Calculators",
    "Routes": "Routes & Surveys",
    "Portal Helpers": "Portal Planning",
    "Build": "Build Calculators",
    "Shapes": "Shape Layouts",
    "Redstone": "Redstone & Timing",
    "Storage": "Storage & Logistics",
    "Farm": "Farm Planning",
    "Technical": "Technical Minecraft",
    "Resource Usage": "Resource Planning",
    "Speedrunning": "Speedrun Planning",
    "World Analysis": "World Analysis",
    "Local Area": "Local Area Analysis",
    "Structures": "Structure Search",
    "Spawners": "Generated Spawners",
    "Biomes": "Biomes & Terrain",
    "Nether": "Nether Analysis",
    "Enchanting": "Enchanting",
    "Probability": "Probability & Sequences",
    "Generation RNG": "Generation RNG",
}


_OUTPUT_LABELS = {
    "x": "X", "y": "Y", "z": "Z", "distance": "Distance", "bearing": "Bearing",
    "count": "Count", "candidate_count": "Locations found", "chunks_scanned": "Chunks scanned",
    "materials": "Materials", "points": "Block positions", "probability": "Probability",
    "mean": "Average", "minimum": "Minimum", "maximum": "Maximum", "route": "Route",
    "segments": "Route segments", "item_capacity": "Item capacity", "shulkers_required": "Shulker boxes",
}


def _operation_group(mode: ToolMode) -> str:
    legacy = mode.legacy
    if legacy is None:
        return "Operations"
    return _GROUP_LABELS.get(legacy.submenu, legacy.submenu or "Operations")


def _human_key(value: str) -> str:
    value = str(value)
    return _OUTPUT_LABELS.get(value, value.replace("_", " ").strip().title())


def _output_summary(mode: ToolMode) -> str:
    keys = [
        key for key in OUTPUT_KEYS.get(mode.key, [])
        if key not in {"implementation", "implementation_detail", "operation", "source", "backend", "exactness", "accuracy"}
    ]
    if not keys:
        return ""
    visible = ", ".join(_human_key(key) for key in keys[:6])
    if len(keys) > 6:
        visible += f", +{len(keys) - 6} more"
    return f"Returns: {visible}."


def _short_description(text: str) -> str:
    text = str(text).strip()
    if not text:
        return ""
    first = text.split(". ", 1)[0].strip()
    return first if first.endswith(".") else first + "."


def _operation_description(mode: ToolMode) -> str:
    name = mode.name
    if name in _EXPLANATION_OVERRIDES:
        return _EXPLANATION_OVERRIDES[name]
    if name in PRECISE:
        return _short_description(PRECISE[name])
    if name in SPECIAL:
        return _short_description(SPECIAL[name])
    legacy = mode.legacy
    if legacy is not None:
        purpose = _DOMAIN_PURPOSE.get((legacy.top, legacy.submenu))
        if purpose:
            return purpose
        return f"Runs {name.lower()} using the fields shown below."
    return f"Open {name}."


class OperationDialog(QDialog):
    """Searchable calculator/explorer workbench with grouped operation navigation."""

    def __init__(self, tool: ToolSpec, executor: FeatureExecutor, settings, parent=None, preferred_mode: str = ""):
        super().__init__(parent)
        self.tool = tool; self.executor = executor; self.settings = settings
        self.mode: ToolMode | None = None; self.inputs: dict[str, QWidget] = {}
        self._modes = [mode for mode in modes_for(tool) if mode.legacy is not None]
        self.setWindowTitle(tool.name); self.resize(1180, 800); self.setMinimumSize(920, 620)

        root = QVBoxLayout(self); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(8)
        hero = QFrame(); hero.setObjectName("ExplorerHero"); hv = QVBoxLayout(hero)
        title = QLabel(tool.name); title.setObjectName("WorkspaceTitle"); hv.addWidget(title)
        summary = QLabel(tool.summary); summary.setWordWrap(True); summary.setObjectName("Muted"); hv.addWidget(summary); root.addWidget(hero)

        split = QSplitter(Qt.Horizontal); split.setChildrenCollapsible(False); root.addWidget(split, 1)
        left = QFrame(); left.setObjectName("ExplorerRail"); lv = QVBoxLayout(left); lv.setContentsMargins(8, 8, 8, 8); lv.setSpacing(7)
        kicker = QLabel("OPERATIONS"); kicker.setObjectName("DeckLabel"); lv.addWidget(kicker)
        self.operation_search = QLineEdit(); self.operation_search.setClearButtonEnabled(True); self.operation_search.setPlaceholderText(f"Search {tool.name.lower()}…"); lv.addWidget(self.operation_search)
        self.mode_list = QTreeWidget(); self.mode_list.setHeaderHidden(True); self.mode_list.setRootIsDecorated(True); self.mode_list.setIndentation(14); self.mode_list.setAnimated(True); self.mode_list.setUniformRowHeights(True); self.mode_list.setObjectName("OperationTree"); lv.addWidget(self.mode_list, 1)
        self.count = QLabel(); self.count.setObjectName("Muted"); lv.addWidget(self.count); split.addWidget(left)

        right = QFrame(); right.setObjectName("ExplorerTrades"); rv = QVBoxLayout(right); rv.setContentsMargins(12, 10, 12, 10); rv.setSpacing(8)
        top = QHBoxLayout(); names = QVBoxLayout(); self.path = QLabel(); self.path.setObjectName("DeckLabel"); names.addWidget(self.path)
        self.mode_title = QLabel("Choose an operation"); self.mode_title.setObjectName("WorkspaceTitle"); names.addWidget(self.mode_title)
        self.mode_help = QLabel(); self.mode_help.setWordWrap(True); self.mode_help.setObjectName("Muted"); names.addWidget(self.mode_help); top.addLayout(names, 1)
        self.configure_btn = QPushButton("Inputs"); self.configure_btn.setCheckable(True); self.configure_btn.setChecked(True)
        self.results_btn = QPushButton("Results"); self.results_btn.setCheckable(True); top.addWidget(self.configure_btn); top.addWidget(self.results_btn); rv.addLayout(top)

        self.context_card = QFrame(); self.context_card.setObjectName("ExplorerHero"); context = QVBoxLayout(self.context_card); context.setContentsMargins(10, 8, 10, 8)
        out_kicker = QLabel("OUTPUT"); out_kicker.setObjectName("DeckLabel"); context.addWidget(out_kicker)
        self.output_help = QLabel(); self.output_help.setWordWrap(True); self.output_help.setObjectName("Muted"); context.addWidget(self.output_help); rv.addWidget(self.context_card)

        self.mode_combo = QComboBox(); self.mode_combo.addItems([mode.name for mode in self._modes]); self.mode_combo.hide(); rv.addWidget(self.mode_combo)

        self.pages = QStackedWidget(); rv.addWidget(self.pages, 1)
        config = QWidget(); cv = QVBoxLayout(config); cv.setContentsMargins(0, 0, 0, 0); cv.setSpacing(8)
        self.search_card = QFrame(); self.search_card.setObjectName("WarningBanner"); sc = QVBoxLayout(self.search_card); sc.setContentsMargins(10, 8, 10, 8)
        sk = QLabel("SEARCH"); sk.setObjectName("DeckLabel"); sc.addWidget(sk); self.search_help = QLabel(); self.search_help.setWordWrap(True); self.search_help.setObjectName("Muted"); sc.addWidget(self.search_help); cv.addWidget(self.search_card); self.search_card.hide()
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame); host = QWidget(); self.form = QFormLayout(host); self.form.setHorizontalSpacing(18); self.form.setVerticalSpacing(14); self.form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow); scroll.setWidget(host); cv.addWidget(scroll, 1)
        self.note = QLabel(); self.note.setWordWrap(True); self.note.setObjectName("Muted"); cv.addWidget(self.note)
        actions = QHBoxLayout(); self.run_btn = QPushButton("Run"); self.run_btn.setObjectName("PrimaryButton"); actions.addWidget(self.run_btn); actions.addStretch(); cv.addLayout(actions); self.pages.addWidget(config)
        self.result_view = ResultView(); self.pages.addWidget(self.result_view); split.addWidget(right); split.setSizes([300, 860])

        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close)
        self.operation_search.textChanged.connect(self._refresh_mode_list); self.operation_search.returnPressed.connect(self._select_first_visible)
        self.mode_list.currentItemChanged.connect(self._list_selected); self.mode_list.itemActivated.connect(self._tree_activated)
        self.mode_combo.currentIndexChanged.connect(self._combo_selected); self.configure_btn.clicked.connect(lambda: self._show_page(0)); self.results_btn.clicked.connect(lambda: self._show_page(1)); self.run_btn.clicked.connect(self._run)

        wanted_index = 0
        if preferred_mode:
            for index, mode in enumerate(self._modes):
                if preferred_mode in {mode.key, mode.name}: wanted_index = index; break
        if self._modes: self.mode_combo.setCurrentIndex(wanted_index)
        self._refresh_mode_list(); self._select_mode_index(wanted_index); self._rebuild()

    def exec(self):
        owner = self.parent()
        if self.tool.id == "automation.macro_studio":
            if owner is None: return QDialog.Rejected
            from .automation_workbench import MacroStudioDialog
            MacroStudioDialog(owner).exec(); return QDialog.Rejected
        if self.tool.workspace == "Automation":
            if owner is None: return QDialog.Rejected
            from .automation_controller import AutomationControllerDialog
            preferred = self.mode.key if self.mode is not None else ""
            AutomationControllerDialog(owner, self.tool, self.executor, self.settings, preferred).exec()
            return QDialog.Rejected
        if self._modes:
            return super().exec()
        if owner is None: return QDialog.Rejected
        if self.tool.id == "world.profiles":
            from .state_workbenches import WorldProfilesDialog; WorldProfilesDialog(owner).exec()
        elif self.tool.id == "build.recipes":
            from .recipe_workbench import RecipeExplorerDialog; RecipeExplorerDialog(owner).exec()
        elif self.tool.id == "utilities.results":
            from .state_workbenches import ResultHistoryDialog; ResultHistoryDialog(owner).exec()
        elif self.tool.id == "utilities.diagnostics":
            from .state_workbenches import DiagnosticsDialog; DiagnosticsDialog(owner).exec()
        return QDialog.Rejected

    def _show_page(self, index: int):
        self.pages.setCurrentIndex(index); self.configure_btn.setChecked(index == 0); self.results_btn.setChecked(index == 1)

    def _refresh_mode_list(self):
        query = self.operation_search.text().strip().lower(); current = self.mode.key if self.mode else ""
        expanded = {self.mode_list.topLevelItem(i).text(0) for i in range(self.mode_list.topLevelItemCount()) if self.mode_list.topLevelItem(i).isExpanded()}
        groups: dict[str, list[tuple[int, ToolMode]]] = {}
        for index, mode in enumerate(self._modes):
            haystack = f"{mode.name} {_operation_description(mode)} {_operation_group(mode)}".lower()
            if query and query not in haystack: continue
            groups.setdefault(_operation_group(mode), []).append((index, mode))

        self.mode_list.blockSignals(True); self.mode_list.clear(); visible = 0; selected = None; first = None
        for group_name, rows in groups.items():
            parent = QTreeWidgetItem([group_name]); parent.setFlags(Qt.ItemIsEnabled); self.mode_list.addTopLevelItem(parent)
            parent.setExpanded(bool(query) or not expanded or group_name in expanded)
            for index, mode in rows:
                item = QTreeWidgetItem([mode.name]); item.setData(0, Qt.UserRole, index); parent.addChild(item); visible += 1
                if first is None: first = item
                if mode.key == current: selected = item
        self.mode_list.blockSignals(False); self.count.setText(f"{visible} operation{'s' if visible != 1 else ''}")
        if selected is not None:
            self.mode_list.setCurrentItem(selected)
        elif first is not None:
            self.mode_list.setCurrentItem(first)

    def _select_first_visible(self):
        for row in range(self.mode_list.topLevelItemCount()):
            group = self.mode_list.topLevelItem(row)
            if group.childCount():
                group.setExpanded(True); self.mode_list.setCurrentItem(group.child(0)); self.mode_list.setFocus(); return

    def _tree_activated(self, item, _column=0):
        self._list_selected(item)
        if self.inputs:
            next(iter(self.inputs.values())).setFocus()
        else:
            self.run_btn.setFocus()

    def _list_selected(self, current, _previous=None):
        if current is None: return
        index = current.data(0, Qt.UserRole)
        if index is None: return
        self._select_mode_index(int(index))

    def _combo_selected(self, index: int):
        if 0 <= index < len(self._modes) and (self.mode is None or self.mode.key != self._modes[index].key): self._select_mode_index(index)

    def _select_mode_index(self, index: int):
        if not (0 <= index < len(self._modes)): return
        changed = self.mode is None or self.mode.key != self._modes[index].key; self.mode = self._modes[index]
        self.mode_combo.blockSignals(True); self.mode_combo.setCurrentIndex(index); self.mode_combo.blockSignals(False)
        for group_row in range(self.mode_list.topLevelItemCount()):
            group = self.mode_list.topLevelItem(group_row)
            for child_row in range(group.childCount()):
                item = group.child(child_row)
                if item.data(0, Qt.UserRole) == index:
                    self.mode_list.blockSignals(True); group.setExpanded(True); self.mode_list.setCurrentItem(item); self.mode_list.blockSignals(False); break
        if changed: self._rebuild()

    def _clear_form(self):
        while self.form.rowCount(): self.form.removeRow(0)
        self.inputs.clear()

    def _live_default(self, key: str, default):
        owner = self.parent(); position = getattr(owner, "current_position", None) if owner is not None else None
        if position is None: return default
        return {"x": position.x, "y": position.y, "z": position.z, "x1": position.x, "y1": position.y, "z1": position.z}.get(str(key), default)

    def _field_editor(self, key: str, label: str, default, kind: str):
        widget = make_widget(kind, default); tip = field_help(key, label)
        if tip:
            widget.setToolTip(tip); widget.setAccessibleDescription(tip)
        return widget, widget

    def _rebuild(self):
        self._clear_form()
        if self.mode is None or self.mode.legacy is None:
            self.path.clear(); self.mode_title.setText("Choose an operation"); self.mode_help.clear(); self.output_help.clear(); self.context_card.hide(); self.note.setText("No operation selected."); self.search_card.hide(); return
        self.path.setText(_operation_group(self.mode).upper())
        self.mode_title.setText(self.mode.name); self.mode_help.setText(_operation_description(self.mode))
        output = _output_summary(self.mode); self.output_help.setText(output); self.context_card.setVisible(bool(output))
        fields = self.executor.input_fields(self.mode.legacy)
        for key, label, default, kind in fields:
            if key == "seed" and getattr(self.settings, "seed", None): default = self.settings.seed
            default = self._live_default(str(key), default); widget, editor = self._field_editor(str(key), str(label), default, kind)
            self.inputs[str(key)] = widget; self.form.addRow(str(label), editor)
        self.note.setText("Ready." if fields else "No manual input required.")
        mode = self.inputs.get("search_mode"); ignore = self.inputs.get("ignore_max_generation_limit")
        if isinstance(mode, QComboBox): mode.currentTextChanged.connect(lambda *_: self._sync_search())
        if isinstance(ignore, QCheckBox): ignore.setText("Continue beyond the configured maximum"); ignore.toggled.connect(lambda *_: self._sync_search())
        self.search_card.setVisible(isinstance(mode, QComboBox)); self._sync_search(); self._show_page(0)

    def _sync_search(self):
        mode = self.inputs.get("search_mode")
        if not isinstance(mode, QComboBox): return
        until = mode.currentText() == "Search until found"; ignore = self.inputs.get("ignore_max_generation_limit"); unlimited = bool(ignore.isChecked()) if isinstance(ignore, QCheckBox) else False
        for key in ("radius_step", "max_search_radius", "ignore_max_generation_limit"):
            widget = self.inputs.get(key)
            if widget is not None: widget.setEnabled(until)
        maximum = self.inputs.get("max_search_radius")
        if maximum is not None and until: maximum.setEnabled(not unlimited)
        budget = self.inputs.get("worldgen_max_chunks")
        if budget is not None: budget.setEnabled(not (until and unlimited))
        if not until:
            text = "Searches once inside the selected radius."
        elif unlimited:
            text = "Keeps expanding after empty passes until a match is found or the job is stopped."
        else:
            text = "Expands by the selected step after each empty pass and stops at the maximum radius."
        self.search_help.setText(text)

    def values(self) -> dict[str, Any]:
        return {key: widget_value(widget) for key, widget in self.inputs.items()}

    def _run(self):
        if self.mode is None or self.mode.legacy is None: return
        legacy = self.mode.legacy; owner = self.parent(); values = self.values(); name = legacy.name
        if owner is not None:
            try:
                from .state_workbenches import stateful_operation
                if stateful_operation(owner, name): return
            except Exception:
                pass
            if name in MACRO_NAMES or name in _CONTROL_DELEGATES:
                if hasattr(owner, "run_mode"): owner.run_mode(self.mode, values)
                return
        self.run_btn.setEnabled(False); self.run_btn.setText("Running…")
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            result = self.executor.execute(legacy, values)
            self.result_view.set_result(legacy, result, self.settings.theme, self.settings.custom_palette)
            self._show_page(1)
        except Exception as exc:
            QMessageBox.warning(self, legacy.name, str(exc))
        finally:
            self.run_btn.setEnabled(True); self.run_btn.setText("Run")
