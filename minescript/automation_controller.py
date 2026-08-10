from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSplitter,
    QVBoxLayout, QWidget,
)

from .descriptions import PRECISE, SPECIAL
from .feature_executor import MACRO_NAMES
from .tool_registry import ToolMode, ToolSpec, modes_for
from .ui_dialogs import ParameterDialog


CONFIGURE_FIRST = {
    "Custom Hold", "Custom Periodic Action", "Livestock Breeder", "Auto Fishing",
    "Coordinate Travel", "Waypoint Travel", "Nether-Assisted Travel",
    "Rectangle", "Filled Rectangle", "Grid", "Rows", "Alternating Pattern", "Perimeter",
    "Branch Miner", "Stair Excavator", "Area Excavator",
    "Coordinate Row Farmer", "Multi-Row Farmer", "Bone Meal Farmer", "Mending Grinder",
}

MACRO_STUDIO_MODES = {"Macro Recorder", "Macro Template", "Action Sequencer", "Route Runner"}

_CATEGORY_ORDER = [
    "Hold & Continuous", "Repeat & Interaction", "Fishing", "Equipment & Safety",
    "Ground & Vehicle", "Advanced Movement", "Coordinate Travel",
    "Mining Routines", "Farm Routines", "Placement Patterns", "Macro Workflows",
    "Setup & Planning", "Other",
]


def automation_category(mode: ToolMode) -> str:
    legacy = mode.legacy
    if legacy is None:
        return "Other"
    submenu = legacy.submenu
    name = mode.name
    if submenu == "Continuous Action":
        return "Hold & Continuous"
    if submenu == "Periodic Interaction":
        return "Repeat & Interaction"
    if submenu == "Fishing":
        return "Fishing"
    if submenu == "Equipment":
        return "Equipment & Safety"
    if submenu == "Travel":
        low = name.lower()
        if any(token in low for token in ("coordinate", "waypoint", "nether-assisted")):
            return "Coordinate Travel"
        if any(token in low for token in ("elytra", "riptide", "spear")):
            return "Advanced Movement"
        return "Ground & Vehicle"
    if submenu == "Mining":
        return "Setup & Planning" if legacy.top == "Wizards" else "Mining Routines"
    if submenu == "Farming":
        return "Setup & Planning" if legacy.top == "Wizards" else "Farm Routines"
    if submenu == "Construction":
        return "Placement Patterns"
    if submenu == "Automation":
        return "Macro Workflows"
    if legacy.top == "Wizards":
        return "Setup & Planning"
    return "Other"


def automation_description(mode: ToolMode) -> str:
    if mode.name in PRECISE:
        return PRECISE[mode.name]
    if mode.name in SPECIAL:
        return SPECIAL[mode.name]
    legacy = mode.legacy
    if legacy is None:
        return mode.name
    category = automation_category(mode)
    if legacy.top == "Wizards":
        return f"Guided setup for {mode.name.lower()}. Configure the plan before applying it in Minecraft."
    if mode.name in MACRO_STUDIO_MODES:
        return "Opens Macro Studio for a reusable, reviewable multi-step automation sequence."
    return f"{mode.name} is a {category.lower()} routine. Review the run behavior and safety state, then start it when Minecraft is ready."


class AutomationControllerDialog(QDialog):
    """Purpose-built controller for automation workbenches.

    Automation is action-oriented: select a routine, review what it does, configure it
    when needed, start it, monitor the live MacroEngine state, and stop it from the same
    surface. It deliberately does not use the calculator/explorer result UI.
    """

    def __init__(self, owner, tool: ToolSpec, executor, settings, preferred_mode: str = ""):
        super().__init__(owner)
        self.owner = owner
        self.tool = tool
        self.executor = executor
        self.settings = settings
        self._modes = [mode for mode in modes_for(tool) if mode.legacy is not None]
        self.mode: ToolMode | None = None
        self.setWindowTitle(tool.name)
        self.resize(1120, 740)
        self.setMinimumSize(940, 620)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        hero = QFrame()
        hero.setObjectName("ExplorerHero")
        hv = QVBoxLayout(hero)
        title = QLabel(tool.name)
        title.setObjectName("WorkspaceTitle")
        hv.addWidget(title)
        summary = QLabel(tool.summary)
        summary.setObjectName("Muted")
        summary.setWordWrap(True)
        hv.addWidget(summary)
        root.addWidget(hero)

        status_bar = QFrame()
        status_bar.setObjectName("ContextDeck")
        sv = QHBoxLayout(status_bar)
        sv.setContentsMargins(10, 7, 10, 7)
        self.link_status = QLabel()
        self.input_status = QLabel()
        self.safe_status = QLabel()
        self.run_status = QLabel()
        for widget in (self.link_status, self.input_status, self.safe_status, self.run_status):
            sv.addWidget(widget)
        sv.addStretch()
        safety = QPushButton("Safety settings")
        safety.clicked.connect(self._open_safety)
        sv.addWidget(safety)
        stop = QPushButton("Stop current")
        stop.setObjectName("DangerButton")
        stop.clicked.connect(self._stop)
        sv.addWidget(stop)
        root.addWidget(status_bar)

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        root.addWidget(split, 1)

        left = QFrame()
        left.setObjectName("ExplorerRail")
        lv = QVBoxLayout(left)
        lv.setContentsMargins(8, 8, 8, 8)
        kicker = QLabel("ROUTINES")
        kicker.setObjectName("DeckLabel")
        lv.addWidget(kicker)
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText("Search automation routines…")
        lv.addWidget(self.search)
        self.list = QListWidget()
        self.list.setObjectName("AutomationRoutineList")
        lv.addWidget(self.list, 1)
        self.count = QLabel()
        self.count.setObjectName("Muted")
        lv.addWidget(self.count)
        split.addWidget(left)

        right = QFrame()
        right.setObjectName("ExplorerTrades")
        rv = QVBoxLayout(right)
        rv.setContentsMargins(14, 10, 14, 10)

        self.path = QLabel()
        self.path.setObjectName("DeckLabel")
        rv.addWidget(self.path)
        self.title = QLabel("Choose a routine")
        self.title.setObjectName("WorkspaceTitle")
        rv.addWidget(self.title)
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setObjectName("Muted")
        rv.addWidget(self.description)

        run_card = QFrame()
        run_card.setObjectName("ExplorerHero")
        rc = QVBoxLayout(run_card)
        rc.setContentsMargins(12, 10, 12, 10)
        label = QLabel("RUN BEHAVIOR")
        label.setObjectName("DeckLabel")
        rc.addWidget(label)
        self.behavior = QLabel()
        self.behavior.setWordWrap(True)
        rc.addWidget(self.behavior)
        self.requirements = QLabel()
        self.requirements.setWordWrap(True)
        self.requirements.setObjectName("Muted")
        rc.addWidget(self.requirements)
        rv.addWidget(run_card)

        session = QFrame()
        session.setObjectName("ExplorerHero")
        se = QVBoxLayout(session)
        se.setContentsMargins(12, 10, 12, 10)
        sl = QLabel("CURRENT SESSION")
        sl.setObjectName("DeckLabel")
        se.addWidget(sl)
        self.session_text = QLabel()
        self.session_text.setWordWrap(True)
        se.addWidget(self.session_text)
        rv.addWidget(session)
        rv.addStretch(1)

        actions = QHBoxLayout()
        self.primary = QPushButton("Start")
        self.primary.setObjectName("PrimaryButton")
        self.primary.clicked.connect(self._activate)
        actions.addWidget(self.primary)
        self.macro_studio = QPushButton("Macro Studio")
        self.macro_studio.clicked.connect(self._open_macro_studio)
        actions.addWidget(self.macro_studio)
        actions.addStretch()
        rv.addLayout(actions)
        split.addWidget(right)
        split.setSizes([330, 760])

        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.rejected.connect(self.reject)
        root.addWidget(close)

        self.search.textChanged.connect(self._refresh_list)
        self.list.currentItemChanged.connect(self._selected)
        self.list.itemDoubleClicked.connect(lambda *_: self._activate())

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_status)
        self.timer.start(500)

        self._refresh_list()
        wanted = preferred_mode
        if wanted:
            for row in range(self.list.count()):
                item = self.list.item(row)
                mode = item.data(Qt.UserRole)
                if isinstance(mode, ToolMode) and wanted in {mode.key, mode.name}:
                    self.list.setCurrentRow(row)
                    break
        if self.list.currentRow() < 0:
            self._select_first_routine()
        self._refresh_status()

    def _refresh_list(self):
        query = self.search.text().strip().lower()
        current_key = self.mode.key if self.mode else ""
        groups: dict[str, list[ToolMode]] = {}
        for mode in self._modes:
            text = f"{mode.name} {automation_description(mode)} {automation_category(mode)}".lower()
            if query and query not in text:
                continue
            groups.setdefault(automation_category(mode), []).append(mode)

        self.list.blockSignals(True)
        self.list.clear()
        visible = 0
        selected_row = -1
        for category in _CATEGORY_ORDER:
            rows = groups.get(category, [])
            if not rows:
                continue
            header = QListWidgetItem(category.upper())
            header.setFlags(Qt.NoItemFlags)
            self.list.addItem(header)
            for mode in rows:
                item = QListWidgetItem(mode.name)
                item.setData(Qt.UserRole, mode)
                item.setToolTip(automation_description(mode))
                self.list.addItem(item)
                visible += 1
                if mode.key == current_key:
                    selected_row = self.list.count() - 1
        self.list.blockSignals(False)
        self.count.setText(f"{visible} routine{'s' if visible != 1 else ''}")
        if selected_row >= 0:
            self.list.setCurrentRow(selected_row)
        elif visible:
            self._select_first_routine()

    def _select_first_routine(self):
        for row in range(self.list.count()):
            if isinstance(self.list.item(row).data(Qt.UserRole), ToolMode):
                self.list.setCurrentRow(row)
                return

    def _selected(self, item, _previous=None):
        if item is None:
            return
        mode = item.data(Qt.UserRole)
        if not isinstance(mode, ToolMode):
            return
        self.mode = mode
        legacy = mode.legacy
        self.path.setText(f"{automation_category(mode).upper()}  •  {legacy.top} → {legacy.submenu}" if legacy else automation_category(mode).upper())
        self.title.setText(mode.name)
        self.description.setText(automation_description(mode))

        if mode.name in MACRO_STUDIO_MODES:
            self.primary.setText("Open Macro Studio")
            self.behavior.setText("Opens the macro editor instead of immediately sending input to Minecraft.")
        elif mode.name in MACRO_NAMES:
            if mode.name in CONFIGURE_FIRST:
                self.primary.setText("Configure & Start")
                self.behavior.setText("A focused configuration dialog opens first. Nothing is sent to Minecraft until you confirm the settings and start the routine.")
            else:
                self.primary.setText("Start")
                self.behavior.setText("Starts the built-in preset immediately after the normal F3+ link, focus, Safe Mode and safety checks pass.")
        else:
            fields = self.executor.input_fields(legacy) if legacy is not None else []
            self.primary.setText("Configure & Run" if fields else "Run")
            self.behavior.setText("This is a setup/planning operation. It does not begin background player input unless its workflow explicitly says so.")

        self.requirements.setText(
            "Automation uses the linked Minecraft client and the configured input backend. "
            "Emergency Stop always releases tracked held input. Safe Mode prevents automation from starting."
        )

    def _activate(self):
        if self.mode is None or self.mode.legacy is None:
            return
        name = self.mode.name
        if name in MACRO_STUDIO_MODES:
            self._open_macro_studio()
            return
        if name in MACRO_NAMES:
            self.owner.start_macro(name)
            self._refresh_status()
            return
        fields = self.executor.input_fields(self.mode.legacy)
        values = {}
        if fields:
            dialog = ParameterDialog(
                name,
                fields,
                self,
                automation_description(self.mode),
                "Run",
            )
            if dialog.exec() != QDialog.Accepted:
                return
            values = dialog.values()
        self.owner.run_mode(self.mode, values)

    def _open_macro_studio(self):
        from .automation_workbench import MacroStudioDialog
        MacroStudioDialog(self.owner).exec()

    def _open_safety(self):
        from .state_workbenches import SafetySettingsDialog
        SafetySettingsDialog(self.owner).exec()
        self._refresh_status()

    def _stop(self):
        self.owner.engine.stop("Stopped from Automation Studio.")
        self._refresh_status()

    def _refresh_status(self):
        target = getattr(self.owner, "target", None)
        cap = getattr(getattr(self.owner, "input", None), "capabilities", None)
        status = getattr(getattr(self.owner, "engine", None), "status", None)
        safe = bool(getattr(self.settings, "safe_mode", False))
        self.link_status.setText("Minecraft: linked" if target else "Minecraft: not linked")
        self.input_status.setText("Input: " + str(getattr(cap, "name", "foreground")))
        self.safe_status.setText("Safe Mode: ON" if safe else "Safe Mode: off")
        running = bool(getattr(status, "running", False))
        active_name = str(getattr(status, "name", "Automation") or "Automation")
        cycles = int(getattr(status, "cycles", 0) or 0)
        self.run_status.setText(f"Running: {active_name}" if running else "Running: none")
        message = str(getattr(status, "message", "") or "")
        state = "Paused" if getattr(status, "paused", False) else ("Running" if running else "Stopped")
        self.session_text.setText(f"State: {state}  •  Routine: {active_name}  •  Cycles: {cycles}" + (f"\n{message}" if message else ""))
        self.primary.setEnabled(not safe)
