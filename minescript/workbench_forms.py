from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QScrollArea, QSplitter, QStackedWidget, QVBoxLayout, QWidget,
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
    ("Navigation", "Coordinates"): "calculates coordinate geometry and travel measurements from the positions you enter",
    ("Navigation", "Routes"): "builds or analyzes a route/survey from entered or recorded Minecraft positions",
    ("Navigation", "Portal Helpers"): "plans portal coordinates and link geometry without modifying the world",
    ("Seed Tools", "Slime"): "analyzes slime-chunk positions for a known Java world seed",
    ("Seed Tools", "Structures"): "searches or compares structure placement candidates for a known Java world seed",
    ("Seed Tools", "Spawners"): "inspects generated Java world data for actual saved spawner blocks/entities",
    ("Seed Tools", "Biomes"): "queries biome or generated-terrain information around a selected location",
    ("Seed Tools", "Local Area"): "summarizes a bounded area for building, technical, or exploration planning",
    ("Seed Tools", "World Analysis"): "analyzes generated-world or known-seed information for a bounded region",
    ("Seed Tools", "Nether"): "analyzes Nether travel, biome, structure, or portal-network behavior",
    ("Calculators", "Coordinate"): "calculates coordinate, distance, direction, or travel values",
    ("Calculators", "Build"): "plans a Minecraft build from dimensions, spacing, or material constraints",
    ("Calculators", "Shapes"): "generates a block-layout plan for the selected geometric shape",
    ("Calculators", "Redstone"): "calculates timing or throughput for a redstone-related planning problem",
    ("Calculators", "Storage"): "converts item totals into Minecraft storage/logistics requirements",
    ("Calculators", "Farm"): "estimates farm dimensions, capacity, yield, or supporting infrastructure",
    ("Calculators", "Technical"): "calculates technical-Minecraft spacing, loading, spawning, or alignment geometry",
    ("Calculators", "Speedrunning"): "calculates route or triangulation values from speedrun observations",
    ("Calculators", "Resource Usage"): "estimates resource, XP, durability, or consumable requirements",
    ("Calculators", "End"): "calculates End-dimension travel or gateway planning values",
    ("RNG Tools", "Enchanting"): "models enchanting-related RNG, cost, or table planning",
    ("RNG Tools", "Probability"): "calculates or visualizes deterministic/probability sequences",
    ("RNG Tools", "Generation RNG"): "previews deterministic generation-stage RNG behavior without claiming a candidate roll guarantees placement",
}


_EXPLANATION_OVERRIDES = {
    "Arch": "Generates a symmetric block arch plan from the entered shape dimensions. Use it to choose the span/height before building; the result is a geometric planning layout rather than an in-world scan.",
    "Rounded Rectangle": "Generates a rounded rectangular footprint from a primary radius/size and secondary width value for build planning.",
    "Diamond": "Generates a diamond-shaped block outline from the selected radius/size.",
    "Pyramid": "Generates stacked square layers for a pyramid-style build from the selected radius and height.",
    "Ellipse": "Generates an elliptical block outline using the primary and secondary radii.",
    "Hexagon": "Generates a hexagonal block outline sized by the selected radius.",
    "Octagon": "Generates an octagonal block outline sized by the selected radius.",
    "Circle": "Generates a hollow block circle from the selected radius.",
    "Filled Circle": "Generates a filled block circle from the selected radius.",
    "Sphere": "Generates a block sphere from the selected radius.",
    "Hollow Sphere": "Generates only the outer shell of a block sphere.",
    "Dome": "Generates the upper portion of a block sphere as a dome plan.",
    "Cylinder": "Generates a cylindrical block layout from radius and height.",
    "Cone": "Generates a tapered cone layout from radius and height.",
    "Spiral": "Generates a flat spiral path on the X/Z plane from radius and turn count.",
    "Helix": "Generates a three-dimensional helical path rising along Y from radius, height, and turn count.",
    "Double Helix": "Generates two phase-offset helical paths for a paired spiral build.",
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


def _operation_group(mode: ToolMode) -> str:
    legacy = mode.legacy
    if legacy is None:
        return "Operations"
    return _GROUP_LABELS.get(legacy.submenu, legacy.submenu or "Operations")


def _human_key(value: str) -> str:
    return str(value).replace("_", " ").strip().capitalize()


def _output_summary(mode: ToolMode) -> str:
    keys = [
        key for key in OUTPUT_KEYS.get(mode.key, [])
        if key not in {"implementation", "implementation_detail", "operation", "source", "backend"}
    ]
    if not keys:
        return "A structured result with the calculation status, values, limitations, and source/exactness context when applicable."
    visible = ", ".join(_human_key(key) for key in keys[:6])
    if len(keys) > 6:
        visible += f", and {len(keys) - 6} more result fields"
    return visible + "."


def _operation_description(mode: ToolMode) -> str:
    name = mode.name
    if name in PRECISE:
        return PRECISE[name]
    if name in SPECIAL:
        return SPECIAL[name]
    if name in _EXPLANATION_OVERRIDES:
        return _EXPLANATION_OVERRIDES[name]
    legacy = mode.legacy
    if legacy is not None:
        purpose = _DOMAIN_PURPOSE.get((legacy.top, legacy.submenu))
        if purpose:
            return f"{name} {purpose}."
        return f"{name} performs the {legacy.submenu} workflow in {legacy.top}."
    return f"Configure and run {name}."


class OperationDialog(QDialog):
    """Searchable full-workspace UI for calculator/explorer-style operations.

    Automation workbenches are deliberately routed to AutomationControllerDialog;
    action-oriented macro control does not belong in this result-oriented surface.
    """

    def __init__(self, tool: ToolSpec, executor: FeatureExecutor, settings, parent=None, preferred_mode: str = ""):
        super().__init__(parent)
        self.tool = tool; self.executor = executor; self.settings = settings
        self.mode: ToolMode | None = None; self.inputs: dict[str, QWidget] = {}
        self._modes = [mode for mode in modes_for(tool) if mode.legacy is not None]
        self.setWindowTitle(tool.name); self.resize(1220, 820); self.setMinimumSize(980, 660)

        root = QVBoxLayout(self); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(8)
        hero = QFrame(); hero.setObjectName("ExplorerHero"); hv = QVBoxLayout(hero)
        title = QLabel(tool.name); title.setObjectName("WorkspaceTitle"); hv.addWidget(title)
        summary = QLabel(tool.summary); summary.setWordWrap(True); summary.setObjectName("Muted"); hv.addWidget(summary); root.addWidget(hero)

        split = QSplitter(Qt.Horizontal); split.setChildrenCollapsible(False); root.addWidget(split, 1)
        left = QFrame(); left.setObjectName("ExplorerRail"); lv = QVBoxLayout(left); lv.setContentsMargins(8, 8, 8, 8)
        kicker = QLabel("OPERATIONS"); kicker.setObjectName("DeckLabel"); lv.addWidget(kicker)
        self.operation_search = QLineEdit(); self.operation_search.setClearButtonEnabled(True); self.operation_search.setPlaceholderText(f"Search {tool.name.lower()} operations…"); lv.addWidget(self.operation_search)
        self.mode_list = QListWidget(); self.mode_list.setObjectName("ProfessionList"); lv.addWidget(self.mode_list, 1)
        self.count = QLabel(); self.count.setObjectName("Muted"); lv.addWidget(self.count); split.addWidget(left)

        right = QFrame(); right.setObjectName("ExplorerTrades"); rv = QVBoxLayout(right); rv.setContentsMargins(12, 10, 12, 10); rv.setSpacing(8)
        top = QHBoxLayout(); names = QVBoxLayout(); self.path = QLabel(); self.path.setObjectName("DeckLabel"); names.addWidget(self.path)
        self.mode_title = QLabel("Choose an operation"); self.mode_title.setObjectName("WorkspaceTitle"); names.addWidget(self.mode_title)
        self.mode_help = QLabel(); self.mode_help.setWordWrap(True); self.mode_help.setObjectName("Muted"); names.addWidget(self.mode_help); top.addLayout(names, 1)
        self.configure_btn = QPushButton("Inputs"); self.configure_btn.setCheckable(True); self.configure_btn.setChecked(True)
        self.results_btn = QPushButton("Results"); self.results_btn.setCheckable(True); top.addWidget(self.configure_btn); top.addWidget(self.results_btn); rv.addLayout(top)

        self.context_card = QFrame(); self.context_card.setObjectName("ExplorerHero"); context = QVBoxLayout(self.context_card); context.setContentsMargins(10, 8, 10, 8)
        out_kicker = QLabel("EXPECTED OUTPUT"); out_kicker.setObjectName("DeckLabel"); context.addWidget(out_kicker)
        self.output_help = QLabel(); self.output_help.setWordWrap(True); self.output_help.setObjectName("Muted"); context.addWidget(self.output_help); rv.addWidget(self.context_card)

        self.mode_combo = QComboBox(); self.mode_combo.addItems([mode.name for mode in self._modes]); self.mode_combo.hide(); rv.addWidget(self.mode_combo)

        self.pages = QStackedWidget(); rv.addWidget(self.pages, 1)
        config = QWidget(); cv = QVBoxLayout(config); cv.setContentsMargins(0, 0, 0, 0); cv.setSpacing(8)
        self.search_card = QFrame(); self.search_card.setObjectName("WarningBanner"); sc = QVBoxLayout(self.search_card); sc.setContentsMargins(10, 8, 10, 8)
        sk = QLabel("SEARCH BEHAVIOR"); sk.setObjectName("DeckLabel"); sc.addWidget(sk); self.search_help = QLabel(); self.search_help.setWordWrap(True); self.search_help.setObjectName("Muted"); sc.addWidget(self.search_help); cv.addWidget(self.search_card); self.search_card.hide()
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame); host = QWidget(); self.form = QFormLayout(host); self.form.setHorizontalSpacing(18); self.form.setVerticalSpacing(14); self.form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow); scroll.setWidget(host); cv.addWidget(scroll, 1)
        self.note = QLabel(); self.note.setWordWrap(True); self.note.setObjectName("Muted"); cv.addWidget(self.note)
        actions = QHBoxLayout(); self.run_btn = QPushButton("Run"); self.run_btn.setObjectName("PrimaryButton"); actions.addWidget(self.run_btn); actions.addStretch(); cv.addLayout(actions); self.pages.addWidget(config)
        self.result_view = ResultView(); self.pages.addWidget(self.result_view); split.addWidget(right); split.setSizes([320, 880])

        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close)
        self.operation_search.textChanged.connect(self._refresh_mode_list); self.mode_list.currentItemChanged.connect(self._list_selected)
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
        query = self.operation_search.text().strip().lower(); current = self.mode.key if self.mode else ""; groups: dict[str, list[tuple[int, ToolMode]]] = {}
        for index, mode in enumerate(self._modes):
            haystack = f"{mode.name} {_operation_description(mode)} {_operation_group(mode)}".lower()
            if query and query not in haystack: continue
            groups.setdefault(_operation_group(mode), []).append((index, mode))
        selected_row = -1; visible = 0
        self.mode_list.blockSignals(True); self.mode_list.clear()
        for group, rows in groups.items():
            header = QListWidgetItem(group.upper()); header.setFlags(Qt.NoItemFlags); self.mode_list.addItem(header)
            for index, mode in rows:
                item = QListWidgetItem(mode.name); item.setData(Qt.UserRole, index); item.setToolTip(_operation_description(mode)); self.mode_list.addItem(item); visible += 1
                if mode.key == current: selected_row = self.mode_list.count() - 1
        self.mode_list.blockSignals(False); self.count.setText(f"{visible} operation{'s' if visible != 1 else ''}")
        if selected_row >= 0: self.mode_list.setCurrentRow(selected_row)
        elif self.mode_list.count():
            for row in range(self.mode_list.count()):
                if self.mode_list.item(row).data(Qt.UserRole) is not None:
                    self.mode_list.setCurrentRow(row); break

    def _list_selected(self, current, _previous=None):
        if current is None: return
        index = current.data(Qt.UserRole)
        if index is None: return
        self._select_mode_index(int(index))

    def _combo_selected(self, index: int):
        if 0 <= index < len(self._modes) and (self.mode is None or self.mode.key != self._modes[index].key): self._select_mode_index(index)

    def _select_mode_index(self, index: int):
        if not (0 <= index < len(self._modes)): return
        changed = self.mode is None or self.mode.key != self._modes[index].key; self.mode = self._modes[index]
        self.mode_combo.blockSignals(True); self.mode_combo.setCurrentIndex(index); self.mode_combo.blockSignals(False)
        for row in range(self.mode_list.count()):
            item = self.mode_list.item(row)
            if item.data(Qt.UserRole) == index:
                self.mode_list.blockSignals(True); self.mode_list.setCurrentRow(row); self.mode_list.blockSignals(False); break
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
        column = QWidget(); layout = QVBoxLayout(column); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(3); layout.addWidget(widget)
        if tip:
            hint = QLabel(tip); hint.setWordWrap(True); hint.setObjectName("Muted"); layout.addWidget(hint)
        return widget, column

    def _rebuild(self):
        self._clear_form()
        if self.mode is None or self.mode.legacy is None:
            self.path.clear(); self.mode_title.setText("Choose an operation"); self.mode_help.clear(); self.output_help.clear(); self.note.setText("No operation selected."); self.search_card.hide(); return
        self.path.setText(f"{self.mode.legacy.top.upper()}  •  {_operation_group(self.mode).upper()}")
        self.mode_title.setText(self.mode.name); self.mode_help.setText(_operation_description(self.mode)); self.output_help.setText(_output_summary(self.mode))
        fields = self.executor.input_fields(self.mode.legacy)
        for key, label, default, kind in fields:
            if key == "seed" and getattr(self.settings, "seed", None): default = self.settings.seed
            default = self._live_default(str(key), default); widget, editor = self._field_editor(str(key), str(label), default, kind)
            self.inputs[str(key)] = widget; self.form.addRow(str(label), editor)
        self.note.setText("Only the inputs shown here are sent to this operation." if fields else "This operation uses saved/live application state and does not require manual input.")
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
            text = "Runs one bounded search inside the selected radius. Expansion controls are disabled because they do not affect this mode."
        elif unlimited:
            text = "Expands after each empty result until a real match is found. The configured maximum is ignored; backend/prerequisite errors and an internal runaway guard can still stop the run. Exact world generation may become expensive."
        else:
            text = "Expands outward after each empty result by the selected step and stops at the configured maximum. The result records attempts and the first radius that produced a match."
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
            box = QMessageBox(QMessageBox.Warning, name, str(exc), parent=self); box.setDetailedText(repr(exc)); box.exec()
        finally:
            self.run_btn.setEnabled(True); self.run_btn.setText("Run")
