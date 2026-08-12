from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from .descriptions import PRECISE, SPECIAL
from .feature_executor import MACRO_NAMES
from .tool_registry import ToolMode, ToolSpec, modes_for
from .ui_dialogs import ParameterDialog


EQUIPMENT_CONFIG = {
    "Crossbow Volley", "Hotbar Workflow", "Tool Rotation", "Durability Guard",
    "Resource Guard", "Food Manager", "Offhand Workflow",
}

CONFIGURE_FIRST = {
    "Custom Hold", "Custom Periodic Action", "Livestock Breeder", "Auto Fishing",
    "Coordinate Travel", "Waypoint Travel", "Nether-Assisted Travel",
    "Rectangle", "Filled Rectangle", "Grid", "Rows", "Alternating Pattern", "Perimeter",
    "Branch Miner", "Stair Excavator", "Area Excavator",
    "Coordinate Row Farmer", "Multi-Row Farmer", "Bone Meal Farmer", "Mending Grinder",
    *EQUIPMENT_CONFIG,
}

MACRO_STUDIO_MODES = {"Macro Recorder", "Macro Template", "Action Sequencer", "Route Runner"}

_CATEGORY_ORDER = [
    "Repeated Actions", "Travel", "Mining", "Farming", "Building",
    "Equipment", "Macros & Setup", "Other",
]

_AUTOMATION_DESCRIPTIONS = {
    "Custom Hold": "Holds one Minecraft key or mouse button continuously until you stop the routine.",
    "Custom Periodic Action": "Clicks the selected mouse button on a repeating timer, with configurable clicks per cycle and spacing.",
    "AFK Mob Grinder": "Repeatedly attacks while you remain positioned at a mob grinder collection point.",
    "Livestock Breeder": "Holds feed/use and repeats interaction swings on a configurable livestock growth or breeding cycle.",
    "Auto Fishing": "Alternates timed reel and recast actions for a stationary fishing setup.",
    "Mending Grinder": "Attacks on a timer and rotates through selected hotbar slots so collected XP can repair multiple Mending items.",
    "Crossbow Volley": "Cycles through selected hotbar crossbows, charges each one for the configured time, then fires it.",
    "Hotbar Workflow": "Cycles through selected hotbar slots in order, optionally repeating the sequence.",
    "Tool Rotation": "Keeps each selected tool active for a set time before moving to the next hotbar slot.",
    "Durability Guard": "Runs a held action for a fixed number of status cycles, then stops automatically.",
    "Resource Guard": "Runs a held action for a fixed number of status cycles, then stops automatically.",
    "Food Manager": "Selects a configured food slot and holds use at a repeating interval.",
    "Offhand Workflow": "Presses the configured offhand-swap key at a repeating interval.",
    "Coordinate Travel": "Turns toward a target coordinate when yaw is available, then moves until coordinate feedback reaches the destination.",
    "Waypoint Travel": "Travels toward one saved waypoint using coordinate feedback and optional sprinting.",
    "Nether-Assisted Travel": "Converts an Overworld destination to Nether scale when needed, then travels toward the resulting coordinate.",
    "Branch Miner": "Measures a main tunnel and repeated side branches with coordinate feedback instead of fixed travel timing.",
    "Stair Excavator": "Repeats forward excavation with a vertical step to create a measured ascending or descending staircase.",
    "Area Excavator": "Excavates parallel rows across a rectangular area using coordinate-measured row distance and shifts.",
    "Coordinate Row Farmer": "Traverses crop rows while holding harvest and/or replant input, then shifts to the next row.",
    "Multi-Row Farmer": "Repeats the row-farming pattern across a larger configured set of crop rows.",
    "Bone Meal Farmer": "Alternates plant and bone-meal hotbar slots and applies the configured number of growth clicks.",
    "Rectangle": "Follows the four sides of a timed rectangular placement path.",
    "Filled Rectangle": "Uses a serpentine row path to cover a rectangular build area.",
    "Grid": "Traverses repeated rows and cross-lines to create a timed placement grid.",
    "Rows": "Traverses parallel timed rows with a configured shift between them.",
    "Alternating Pattern": "Traverses repeated rows while alternating the placement pattern between passes.",
    "Perimeter": "Follows a four-sided timed perimeter path.",
    "Macro Recorder": "Opens Macro Studio to record player input as an editable sequence.",
    "Macro Template": "Opens Macro Studio with reusable sequence templates.",
    "Action Sequencer": "Opens Macro Studio to assemble ordered input steps.",
    "Route Runner": "Opens Macro Studio for a saved multi-step route or action sequence.",
}


def automation_category(mode: ToolMode) -> str:
    legacy = mode.legacy
    if legacy is None:
        return "Other"
    submenu = legacy.submenu
    if submenu in {"Continuous Action", "Periodic Interaction", "Fishing"}:
        return "Repeated Actions"
    if submenu == "Equipment":
        return "Equipment"
    if submenu == "Travel":
        return "Travel"
    if submenu == "Mining":
        return "Macros & Setup" if legacy.top == "Wizards" else "Mining"
    if submenu == "Farming":
        return "Macros & Setup" if legacy.top == "Wizards" else "Farming"
    if submenu == "Construction":
        return "Building"
    if submenu == "Automation" or legacy.top == "Wizards":
        return "Macros & Setup"
    return "Other"


def automation_description(mode: ToolMode) -> str:
    if mode.name in _AUTOMATION_DESCRIPTIONS:
        return _AUTOMATION_DESCRIPTIONS[mode.name]
    if mode.name in MACRO_STUDIO_MODES:
        return "Opens Macro Studio to edit and run a multi-step input sequence."
    if mode.name in PRECISE:
        return PRECISE[mode.name].split(". ", 1)[0].rstrip(".") + "."
    if mode.name in SPECIAL:
        return SPECIAL[mode.name].split(". ", 1)[0].rstrip(".") + "."
    category = automation_category(mode)
    return f"Runs the {mode.name.lower()} routine from the {category.lower()} group."


def _slots(text: str, fallback=(1, 2, 3)) -> tuple[int, ...]:
    values = []
    for token in str(text).replace(";", ",").split(","):
        token = token.strip()
        if token.isdigit() and 1 <= int(token) <= 9:
            values.append(int(token))
    return tuple(values) or tuple(fallback)


class AutomationControllerDialog(QDialog):
    """Task-oriented controller for automation routines."""

    def __init__(self, owner, tool: ToolSpec, executor, settings, preferred_mode: str = ""):
        super().__init__(owner)
        self.owner = owner; self.tool = tool; self.executor = executor; self.settings = settings
        self._modes = [mode for mode in modes_for(tool) if mode.legacy is not None]
        self.mode: ToolMode | None = None
        self.setWindowTitle(tool.name); self.resize(1080, 720); self.setMinimumSize(900, 600)

        root = QVBoxLayout(self); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(8)
        hero = QFrame(); hero.setObjectName("ExplorerHero"); hv = QVBoxLayout(hero)
        title = QLabel(tool.name); title.setObjectName("WorkspaceTitle"); hv.addWidget(title)
        summary = QLabel(tool.summary); summary.setObjectName("Muted"); summary.setWordWrap(True); hv.addWidget(summary); root.addWidget(hero)

        status_bar = QFrame(); status_bar.setObjectName("ContextDeck"); sv = QHBoxLayout(status_bar); sv.setContentsMargins(10, 7, 10, 7)
        self.link_status = QLabel(); self.input_status = QLabel(); self.safe_status = QLabel(); self.run_status = QLabel()
        for widget in (self.link_status, self.input_status, self.safe_status, self.run_status): sv.addWidget(widget)
        sv.addStretch(); safety = QPushButton("Safety"); safety.clicked.connect(self._open_safety); sv.addWidget(safety)
        stop = QPushButton("Stop current"); stop.setObjectName("DangerButton"); stop.clicked.connect(self._stop); sv.addWidget(stop); root.addWidget(status_bar)

        split = QSplitter(Qt.Horizontal); split.setChildrenCollapsible(False); root.addWidget(split, 1)
        left = QFrame(); left.setObjectName("ExplorerRail"); lv = QVBoxLayout(left); lv.setContentsMargins(8, 8, 8, 8); lv.setSpacing(7)
        kicker = QLabel("ROUTINES"); kicker.setObjectName("DeckLabel"); lv.addWidget(kicker)
        self.search = QLineEdit(); self.search.setClearButtonEnabled(True); self.search.setPlaceholderText("Search routines…"); lv.addWidget(self.search)
        self.list = QTreeWidget(); self.list.setHeaderHidden(True); self.list.setRootIsDecorated(True); self.list.setIndentation(14); self.list.setAnimated(True); self.list.setUniformRowHeights(True); self.list.setObjectName("AutomationRoutineList"); lv.addWidget(self.list, 1)
        self.count = QLabel(); self.count.setObjectName("Muted"); lv.addWidget(self.count); split.addWidget(left)

        right = QFrame(); right.setObjectName("ExplorerTrades"); rv = QVBoxLayout(right); rv.setContentsMargins(14, 10, 14, 10); rv.setSpacing(8)
        self.path = QLabel(); self.path.setObjectName("DeckLabel"); rv.addWidget(self.path)
        self.title = QLabel("Choose a routine"); self.title.setObjectName("WorkspaceTitle"); rv.addWidget(self.title)
        self.description = QLabel(); self.description.setWordWrap(True); self.description.setObjectName("Muted"); rv.addWidget(self.description)

        run_card = QFrame(); run_card.setObjectName("ExplorerHero"); rc = QVBoxLayout(run_card); rc.setContentsMargins(12, 10, 12, 10)
        label = QLabel("ACTION"); label.setObjectName("DeckLabel"); rc.addWidget(label)
        self.behavior = QLabel(); self.behavior.setWordWrap(True); rc.addWidget(self.behavior); rv.addWidget(run_card)

        self.session_card = QFrame(); self.session_card.setObjectName("ExplorerHero"); se = QVBoxLayout(self.session_card); se.setContentsMargins(12, 10, 12, 10)
        sl = QLabel("CURRENT SESSION"); sl.setObjectName("DeckLabel"); se.addWidget(sl)
        self.session_text = QLabel(); self.session_text.setWordWrap(True); se.addWidget(self.session_text); rv.addWidget(self.session_card); self.session_card.hide(); rv.addStretch(1)

        actions = QHBoxLayout(); self.primary = QPushButton("Start"); self.primary.setObjectName("PrimaryButton"); self.primary.clicked.connect(self._activate); actions.addWidget(self.primary)
        self.macro_studio = QPushButton("Macro Studio"); self.macro_studio.clicked.connect(self._open_macro_studio); actions.addWidget(self.macro_studio); actions.addStretch(); rv.addLayout(actions)
        split.addWidget(right); split.setSizes([300, 760])

        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close)
        self.search.textChanged.connect(self._refresh_list); self.search.returnPressed.connect(self._select_first_routine)
        self.list.currentItemChanged.connect(self._selected); self.list.itemActivated.connect(lambda *_: self._activate())
        self.timer = QTimer(self); self.timer.timeout.connect(self._refresh_status); self.timer.start(500)

        self._refresh_list()
        if preferred_mode:
            self._select_mode(preferred_mode)
        if self.list.currentItem() is None:
            self._select_first_routine()
        self._refresh_status()

    def _select_mode(self, wanted: str):
        for group_row in range(self.list.topLevelItemCount()):
            group = self.list.topLevelItem(group_row)
            for child_row in range(group.childCount()):
                item = group.child(child_row); mode = item.data(0, Qt.UserRole)
                if isinstance(mode, ToolMode) and wanted in {mode.key, mode.name}:
                    group.setExpanded(True); self.list.setCurrentItem(item); return

    def _refresh_list(self):
        query = self.search.text().strip().lower(); current_key = self.mode.key if self.mode else ""
        expanded = {self.list.topLevelItem(i).text(0) for i in range(self.list.topLevelItemCount()) if self.list.topLevelItem(i).isExpanded()}
        groups: dict[str, list[ToolMode]] = {}
        for mode in self._modes:
            text = f"{mode.name} {automation_description(mode)} {automation_category(mode)}".lower()
            if query and query not in text: continue
            groups.setdefault(automation_category(mode), []).append(mode)

        self.list.blockSignals(True); self.list.clear(); visible = 0; selected = None; first = None
        for category in _CATEGORY_ORDER:
            rows = groups.get(category, [])
            if not rows: continue
            parent = QTreeWidgetItem([category]); parent.setFlags(Qt.ItemIsEnabled); self.list.addTopLevelItem(parent)
            parent.setExpanded(bool(query) or not expanded or category in expanded)
            for mode in rows:
                item = QTreeWidgetItem([mode.name]); item.setData(0, Qt.UserRole, mode); parent.addChild(item); visible += 1
                if first is None: first = item
                if mode.key == current_key: selected = item
        self.list.blockSignals(False); self.count.setText(f"{visible} routine{'s' if visible != 1 else ''}")
        if selected is not None:
            self.list.setCurrentItem(selected)
        elif first is not None:
            self.list.setCurrentItem(first)

    def _select_first_routine(self):
        for group_row in range(self.list.topLevelItemCount()):
            group = self.list.topLevelItem(group_row)
            if group.childCount():
                group.setExpanded(True); self.list.setCurrentItem(group.child(0)); return

    def _selected(self, item, _previous=None):
        if item is None: return
        mode = item.data(0, Qt.UserRole)
        if not isinstance(mode, ToolMode): return
        self.mode = mode
        self.path.setText(automation_category(mode).upper())
        self.title.setText(mode.name); self.description.setText(automation_description(mode))
        if mode.name in MACRO_STUDIO_MODES:
            self.primary.setText("Open Macro Studio"); self.behavior.setText("Edit the sequence before running it.")
        elif mode.name in MACRO_NAMES:
            if mode.name in CONFIGURE_FIRST:
                self.primary.setText("Configure & Start"); self.behavior.setText("Review the routine settings, then start it.")
            else:
                self.primary.setText("Start"); self.behavior.setText("Starts immediately with the built-in routine settings.")
        else:
            fields = self.executor.input_fields(mode.legacy) if mode.legacy is not None else []
            self.primary.setText("Configure & Run" if fields else "Run"); self.behavior.setText("Enter the required values, then run this setup or planning operation.")

    def _activate(self):
        if self.mode is None or self.mode.legacy is None: return
        name = self.mode.name
        if name in MACRO_STUDIO_MODES: self._open_macro_studio(); return
        if name in EQUIPMENT_CONFIG: self._configure_equipment(name); self._refresh_status(); return
        if name in MACRO_NAMES: self.owner.start_macro(name); self._refresh_status(); return
        fields = self.executor.input_fields(self.mode.legacy); values = {}
        if fields:
            dialog = ParameterDialog(name, fields, self, automation_description(self.mode), "Run")
            if dialog.exec() != QDialog.Accepted: return
            values = dialog.values()
        self.owner.run_mode(self.mode, values)

    def _configure_equipment(self, name: str):
        from .gameplay import macros
        run = self.owner.start_macro_callable
        if name == "Crossbow Volley":
            d = ParameterDialog(name, [("slots", "Crossbow slots", "1,2,3", "text"), ("charge", "Charge time", 1.3, "float"), ("swap", "Swap delay", 0.25, "float")], self, "Charge and fire each crossbow in the selected hotbar slots.", "Start")
            if d.exec() == QDialog.Accepted:
                v = d.values(); run(name, lambda e: macros.crossbow_volley(e, int(max(.05, float(v["charge"])) * 1000), int(max(.02, float(v["swap"])) * 1000), _slots(v["slots"])))
            return
        if name == "Hotbar Workflow":
            d = ParameterDialog(name, [("slots", "Slots", "1,2,3", "text"), ("delay", "Delay between slots", 0.25, "float"), ("loop", "Loop", True, "bool")], self, run_label="Start")
            if d.exec() == QDialog.Accepted:
                v = d.values(); run(name, lambda e: macros.hotbar_workflow(e, _slots(v["slots"]), int(max(.02, float(v["delay"])) * 1000), bool(v["loop"])))
            return
        if name == "Tool Rotation":
            d = ParameterDialog(name, [("slots", "Tool slots", "1,2,3", "text"), ("interval", "Seconds per tool", 30.0, "float"), ("attack", "Hold attack", False, "bool")], self, run_label="Start")
            if d.exec() == QDialog.Accepted:
                v = d.values(); run(name, lambda e: macros.tool_rotation(e, _slots(v["slots"]), max(.1, float(v["interval"])), bool(v["attack"])))
            return
        if name in {"Durability Guard", "Resource Guard"}:
            default_action = "Hold attack" if name == "Durability Guard" else "Hold use"
            d = ParameterDialog(name, [("action", "Action", [default_action, "Hold use" if default_action == "Hold attack" else "Hold attack"], "choice"), ("cycles", "Maximum status cycles", 100, "int")], self, automation_description(self.mode) if self.mode else "", "Start")
            if d.exec() == QDialog.Accepted:
                v = d.values(); button = "left" if v["action"] == "Hold attack" else "right"; cycles = max(1, int(v["cycles"])); run(name, lambda e: macros.guarded_continuous(e, held_mouse=(button,), max_cycles=cycles))
            return
        if name == "Food Manager":
            d = ParameterDialog(name, [("slot", "Food slot", 2, "int"), ("interval", "Eat every", 120.0, "float"), ("duration", "Use duration", 1.65, "float")], self, "Select the food slot and hold use on a repeating timer.", "Start")
            if d.exec() == QDialog.Accepted:
                v = d.values(); run(name, lambda e: macros.food_manager(e, max(1, min(9, int(v["slot"]))), max(.1, float(v["interval"])), max(.1, float(v["duration"]))))
            return
        if name == "Offhand Workflow":
            d = ParameterDialog(name, [("key", "Swap key", "f", "text"), ("interval", "Swap interval", 30.0, "float")], self, run_label="Start")
            if d.exec() == QDialog.Accepted:
                v = d.values(); run(name, lambda e: macros.offhand_workflow(e, str(v["key"]).strip() or "f", max(.1, float(v["interval"]))))

    def _open_macro_studio(self):
        from .automation_workbench import MacroStudioDialog
        MacroStudioDialog(self.owner).exec()

    def _open_safety(self):
        from .state_workbenches import SafetySettingsDialog
        SafetySettingsDialog(self.owner).exec(); self._refresh_status()

    def _stop(self):
        self.owner.engine.stop("Stopped from Automation Studio."); self._refresh_status()

    def _refresh_status(self):
        target = getattr(self.owner, "target", None); cap = getattr(getattr(self.owner, "input", None), "capabilities", None); status = getattr(getattr(self.owner, "engine", None), "status", None)
        safe = bool(getattr(self.settings, "safe_mode", False)); self.link_status.setText("Minecraft linked" if target else "Minecraft not linked"); self.input_status.setText("Input: " + str(getattr(cap, "name", "foreground"))); self.safe_status.setText("Safe Mode on" if safe else "Safe Mode off")
        running = bool(getattr(status, "running", False)); active_name = str(getattr(status, "name", "Automation") or "Automation"); cycles = int(getattr(status, "cycles", 0) or 0)
        self.run_status.setText(active_name if running else "Idle"); message = str(getattr(status, "message", "") or ""); state = "Paused" if getattr(status, "paused", False) else ("Running" if running else "Stopped")
        self.session_card.setVisible(running or bool(message)); self.session_text.setText(f"{state} • {active_name} • {cycles} cycles" + (f"\n{message}" if message else "")); self.primary.setEnabled(not safe)
