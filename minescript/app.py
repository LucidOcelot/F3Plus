from __future__ import annotations

import html
import json
import math
import sys
from typing import Any

from PySide6.QtCore import QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QColorDialog, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QPlainTextEdit, QScrollArea, QSpinBox, QSplitter, QStackedWidget,
    QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

try:
    from pynput import keyboard
except Exception:
    keyboard = None

from . import TARGET_MINECRAFT, __version__
from .config import Settings
from .coordinates import CoordinateCapture
from .feature_executor import FeatureExecutor, MACRO_NAMES
from .gameplay.presets import runner as macro_runner
from .macro_engine import MacroEngine
from .minecraft_art import clear_texture_cache, texture_bytes
from .pixel_art import icon_pixmap
from .platform_input import create_focus_controller, create_input_backend, discover_minecraft_targets
from .platform_input.requirements import focus_issue
from .safe_mode import SAFE_MODE_DISCLAIMER, SAFE_MODE_SUMMARY, restriction_reason as safe_mode_restriction
from .tool_guides import (
    NAV_SECTIONS, group_order, make_guide, nav_section, search_text,
    specs_for_section, tool_art_key, workspace_group,
)
from .tool_registry import BY_ID, LEGACY_TO_CANONICAL, ToolMode, ToolSpec, modes_for
from .ui_theme import COLOR_KEYS, DEFAULT_CUSTOM_PALETTE, palette, stylesheet
from .workbenches import (
    LootWorkbenchDialog, MechanicsLabDialog, OperationDialog, ResultMapDialog,
    RngEnchantingDialog, VillagerExplorerDialog, extract_coordinate_layers,
)


NAV_ART = {
    "Home": "home",
    "Automation": "automation",
    "Navigation": "map",
    "World Explorer": "seed",
    "Build & Technical": "building",
    "Simulation & RNG": "rng",
    "Villagers": "villager",
    "Utilities & Safety": "utilities",
}


class Bridge(QObject):
    status = Signal(object)


class OptionsDialog(QDialog):
    MODES = {
        "Automatic — prefer background input": "auto",
        "Background / targeted": "targeted",
        "Foreground only": "standard",
    }
    THEMES = {
        "Chorus": "chorus",
        "Light": "light",
        "Cyber": "cyberpunk",
        "Vanilla": "minecraft",
        "Aether": "aether",
        "Foundry": "foundry",
        "Custom": "custom",
    }

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent); self.settings = settings
        self.setWindowTitle("F3+ Options"); self.resize(820, 700)
        root = QVBoxLayout(self); tabs = QTabWidget(); root.addWidget(tabs, 1)

        general = QWidget(); gf = QFormLayout(general)
        self.version = QLineEdit(settings.minecraft_version)
        self.dimension = QComboBox(); self.dimension.addItems(["Overworld", "Nether", "End"]); self.dimension.setCurrentText(settings.dimension)
        self.auto_link = QCheckBox("Automatically link when exactly one Minecraft Java client is detected"); self.auto_link.setChecked(settings.auto_link_minecraft)
        self.title_hint = QLineEdit(settings.minecraft_window_title)
        gf.addRow("Minecraft version", self.version); gf.addRow("Default dimension", self.dimension); gf.addRow("", self.auto_link); gf.addRow("Window/title hint", self.title_hint)
        tabs.addTab(general, "General")

        inp = QWidget(); inf = QFormLayout(inp)
        self.mode = QComboBox(); self.mode.addItems(self.MODES)
        wanted = settings.input_mode if settings.input_mode in self.MODES.values() else "auto"
        self.mode.setCurrentText(next(label for label, value in self.MODES.items() if value == wanted))
        self.allow_focus = QCheckBox("Allow F3+ to focus Minecraft when required"); self.allow_focus.setChecked(settings.allow_focus_switch)
        self.confirm_focus = QCheckBox("Ask before switching focus"); self.confirm_focus.setChecked(settings.confirm_focus_switch)
        self.restore_focus = QCheckBox("Restore the previous application after automation stops"); self.restore_focus.setChecked(settings.restore_previous_focus)
        self.focus_delay = QSpinBox(); self.focus_delay.setRange(100, 3000); self.focus_delay.setValue(settings.focus_switch_delay_ms); self.focus_delay.setSuffix(" ms")
        self.manual_delay = QSpinBox(); self.manual_delay.setRange(1, 10); self.manual_delay.setValue(settings.manual_focus_delay_seconds); self.manual_delay.setSuffix(" s")
        inf.addRow("Input strategy", self.mode); inf.addRow("", self.allow_focus); inf.addRow("", self.confirm_focus); inf.addRow("", self.restore_focus); inf.addRow("Focus settle time", self.focus_delay); inf.addRow("Manual countdown", self.manual_delay)
        tabs.addTab(inp, "Input")

        appearance = QWidget(); av = QVBoxLayout(appearance); af = QFormLayout(); av.addLayout(af)
        self.theme = QComboBox(); self.theme.addItems(self.THEMES)
        self.theme.setCurrentText(next((label for label, value in self.THEMES.items() if value == settings.theme), "Chorus")); af.addRow("Theme", self.theme)
        self.custom_minecraft_assets = QCheckBox("Use recovered Minecraft artwork in Custom when available"); self.custom_minecraft_assets.setChecked(bool(getattr(settings, "custom_theme_use_minecraft_assets", False))); af.addRow("", self.custom_minecraft_assets)
        custom = QFrame(); cf = QFormLayout(custom); self.custom_fields = {}
        current = dict(DEFAULT_CUSTOM_PALETTE); current.update(settings.custom_palette or {})
        for key in COLOR_KEYS:
            row = QWidget(); hl = QHBoxLayout(row); hl.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(current.get(key, DEFAULT_CUSTOM_PALETTE[key])); choose = QPushButton("Choose…"); choose.clicked.connect(lambda _=False, e=edit: self._choose_color(e)); hl.addWidget(edit, 1); hl.addWidget(choose); self.custom_fields[key] = edit; cf.addRow(key.replace("_", " ").title(), row)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame); scroll.setWidget(custom); av.addWidget(scroll, 1); tabs.addTab(appearance, "Appearance")

        automation = QWidget(); hf = QFormLayout(automation)
        self.stop_hotkey = QLineEdit(settings.stop_hotkey); self.toggle_hotkey = QLineEdit(settings.toggle_hotkey); self.coord_hotkey = QLineEdit(settings.coord_copy_hotkey)
        hf.addRow("Emergency stop", self.stop_hotkey); hf.addRow("Pause / resume", self.toggle_hotkey); hf.addRow("Copy sister coordinates", self.coord_hotkey)
        tabs.addTab(automation, "Automation")

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def _choose_color(self, edit):
        color = QColorDialog.getColor(QColor(edit.text()) if QColor(edit.text()).isValid() else QColor("#FFFFFF"), self)
        if color.isValid(): edit.setText(color.name().upper())

    def apply(self):
        s = self.settings
        s.minecraft_version = self.version.text().strip() or s.minecraft_version
        s.dimension = self.dimension.currentText(); s.auto_link_minecraft = self.auto_link.isChecked(); s.minecraft_window_title = self.title_hint.text().strip() or "Minecraft"
        s.input_mode = self.MODES[self.mode.currentText()]; s.allow_focus_switch = self.allow_focus.isChecked(); s.confirm_focus_switch = self.confirm_focus.isChecked(); s.restore_previous_focus = self.restore_focus.isChecked(); s.focus_switch_delay_ms = self.focus_delay.value(); s.manual_focus_delay_seconds = self.manual_delay.value()
        s.theme = self.THEMES[self.theme.currentText()]; s.custom_theme_use_minecraft_assets = self.custom_minecraft_assets.isChecked()
        custom = dict(DEFAULT_CUSTOM_PALETTE)
        for key, edit in self.custom_fields.items(): custom[key] = edit.text().strip() if QColor(edit.text().strip()).isValid() else DEFAULT_CUSTOM_PALETTE[key]
        s.custom_palette = custom; s.stop_hotkey = self.stop_hotkey.text().strip() or "ctrl+alt+s"; s.toggle_hotkey = self.toggle_hotkey.text().strip() or "ctrl+alt+space"; s.coord_copy_hotkey = self.coord_hotkey.text().strip() or "ctrl+alt+c"; s.save()


class F3Plus(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings.load(); self.target = None
        self.focus_controller = create_focus_controller(None)
        self.input = create_input_backend("standard", self.settings.minecraft_window_title)
        self.engine = MacroEngine(self.input); self.capture = CoordinateCapture(self.input, self.settings); self.executor = FeatureExecutor(self.settings.minecraft_version)
        self.engine.set_position_provider(self.capture.capture)
        self.current_position = None; self.listener = None; self._selected_id = None; self._guide_cache = {}; self._art_cache = {}; self._last_result = None; self._focus_token = None
        self.bridge = Bridge(); self.bridge.status.connect(self.update_status); self.engine.on_status = self.bridge.status.emit
        self.setWindowTitle(f"F3+ {__version__}"); self.resize(1480, 900); self.setMinimumSize(1180, 700)
        self.build_ui(); self.build_menu(); self.apply_theme(); self.start_hotkeys()
        self.link_timer = QTimer(self); self.link_timer.timeout.connect(self.refresh_link_state); self.link_timer.start(5000)
        if self.settings.auto_link_minecraft: QTimer.singleShot(200, self.auto_link_minecraft)

    # ----- presentation -------------------------------------------------
    def build_ui(self):
        root = QWidget(); self.setCentralWidget(root); outer = QVBoxLayout(root); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        command = QFrame(); command.setObjectName("CommandDeck"); top = QHBoxLayout(command); top.setContentsMargins(16, 8, 16, 8)
        self.brand = QLabel(); self.brand.setFixedSize(42, 42); top.addWidget(self.brand); title = QLabel("F3+"); title.setObjectName("AppTitle"); top.addWidget(title); top.addStretch()
        self.link_badge = QLabel("● Minecraft not linked"); self.backend_badge = QLabel("Foreground"); self.background_badge = QLabel("BG —"); self.camera_badge = QLabel("CAM —")
        for widget in (self.link_badge, self.backend_badge, self.background_badge, self.camera_badge): top.addWidget(widget)
        relink = QPushButton("Relink"); relink.clicked.connect(self.relink_minecraft); top.addWidget(relink)
        self.safe_btn = QPushButton("Safe Mode"); self.safe_btn.setCheckable(True); self.safe_btn.setChecked(self.settings.safe_mode); self.safe_btn.clicked.connect(self.toggle_safe_mode); top.addWidget(self.safe_btn)
        options = QPushButton("Options"); options.clicked.connect(self.options_dialog); top.addWidget(options)
        pause = QPushButton("Pause / Resume"); pause.clicked.connect(self.engine.toggle_pause); top.addWidget(pause)
        stop = QPushButton("EMERGENCY STOP"); stop.setObjectName("DangerButton"); stop.clicked.connect(self.engine.stop); top.addWidget(stop); outer.addWidget(command)

        context = QFrame(); context.setObjectName("ContextDeck"); row = QHBoxLayout(context); row.setContentsMargins(16, 7, 16, 7)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search workbenches or any historical operation…"); self.search.setClearButtonEnabled(True); row.addWidget(self.search, 2)
        self.dimension = QComboBox(); self.dimension.addItems(["Overworld", "Nether", "End"]); self.dimension.setCurrentText(self.settings.dimension); self.dimension.currentTextChanged.connect(self.set_dimension); row.addWidget(self.dimension)
        self.version_badge = QLabel(self.settings.minecraft_version); row.addWidget(self.version_badge); self.seed_label = QLabel("Seed set" if self.settings.seed else "Seed not set"); row.addWidget(self.seed_label)
        seed = QPushButton("World Seed"); seed.clicked.connect(self.set_seed); row.addWidget(seed); self.pos_label = QLabel("Position not captured"); row.addWidget(self.pos_label); capture = QPushButton("Capture F3+C"); capture.clicked.connect(self.capture_position); row.addWidget(capture); outer.addWidget(context)

        work = QSplitter(Qt.Horizontal); work.setChildrenCollapsible(False); outer.addWidget(work, 1)
        rail = QFrame(); rl = QVBoxLayout(rail); rl.addWidget(QLabel("WORKSPACES")); self.nav = QListWidget(); self.nav.setIconSize(QSize(22, 22)); rl.addWidget(self.nav, 1)
        for label, _ in NAV_SECTIONS:
            item = QListWidgetItem(label); item.setData(Qt.UserRole, label); self.nav.addItem(item)
        work.addWidget(rail)

        library = QFrame(); ll = QVBoxLayout(library); self.browser_title = QLabel("Home"); self.browser_title.setObjectName("WorkspaceTitle"); ll.addWidget(self.browser_title)
        self.group_filter = QComboBox(); self.group_filter.addItem("All groups"); ll.addWidget(self.group_filter); self.tool_list = QListWidget(); self.tool_list.setIconSize(QSize(30, 30)); self.tool_list.setSpacing(3); ll.addWidget(self.tool_list, 1); self.result_count = QLabel(); ll.addWidget(self.result_count); work.addWidget(library)

        detail = QFrame(); dl = QVBoxLayout(detail); hero = QHBoxLayout(); self.feature_icon = QLabel(); self.feature_icon.setFixedSize(46, 46); hero.addWidget(self.feature_icon); titles = QVBoxLayout(); self.feature_kicker = QLabel("SELECT A WORKBENCH"); self.feature_title = QLabel("Choose a workbench"); self.feature_title.setObjectName("DetailTitle"); self.feature_path = QLabel(); titles.addWidget(self.feature_kicker); titles.addWidget(self.feature_title); titles.addWidget(self.feature_path); hero.addLayout(titles, 1); self.favorite_btn = QPushButton("☆ Favorite"); self.favorite_btn.clicked.connect(self.toggle_favorite); hero.addWidget(self.favorite_btn); dl.addLayout(hero)
        actions = QHBoxLayout(); self.run_btn = QPushButton("Open Workbench"); self.run_btn.setObjectName("PrimaryButton"); self.run_btn.clicked.connect(self.run_selected); self.run_btn.setEnabled(False); actions.addWidget(self.run_btn); self.map_btn = QPushButton("Open Map"); self.map_btn.clicked.connect(self.open_result_map); self.map_btn.setEnabled(False); actions.addWidget(self.map_btn); actions.addStretch(); self.guide_btn = QPushButton("Guide"); self.results_btn = QPushButton("Results"); self.guide_btn.setCheckable(True); self.results_btn.setCheckable(True); self.guide_btn.setChecked(True); group = QButtonGroup(self); group.setExclusive(True); group.addButton(self.guide_btn); group.addButton(self.results_btn); actions.addWidget(self.guide_btn); actions.addWidget(self.results_btn); dl.addLayout(actions)
        self.stack = QStackedWidget(); self.guide = QTextBrowser(); self.output = QPlainTextEdit(); self.output.setReadOnly(True); self.stack.addWidget(self.guide); self.stack.addWidget(self.output); dl.addWidget(self.stack, 1); self.guide_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0)); self.results_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1)); work.addWidget(detail); work.setSizes([210, 440, 830])

        self.nav.currentItemChanged.connect(lambda *_: self.refresh_tools()); self.search.textChanged.connect(lambda *_: self.refresh_tools()); self.group_filter.currentTextChanged.connect(lambda *_: self.refresh_tools(True)); self.tool_list.itemSelectionChanged.connect(self.selection_changed); self.tool_list.itemDoubleClicked.connect(lambda *_: self.run_selected()); self.nav.setCurrentRow(0); self._sync_safe(); self._refresh_art()

    def build_menu(self):
        appm = self.menuBar().addMenu("F3+"); self.add_action(appm, "Set World Seed", self.set_seed); self.add_action(appm, "Capture Position", self.capture_position); appm.addSeparator(); self.add_action(appm, "Exit", self.close)
        conn = self.menuBar().addMenu("Connection"); self.add_action(conn, "Relink Minecraft", self.relink_minecraft); self.add_action(conn, "Connection Status", self.show_connection_status)
        tools = self.menuBar().addMenu("Workbenches"); self.add_action(tools, "Villager Explorer", lambda: VillagerExplorerDialog(self).exec()); self.add_action(tools, "RNG & Enchanting", lambda: RngEnchantingDialog(self, self.executor, BY_ID["simulation.rng"]).exec()); self.add_action(tools, "Loot & Drops", lambda: LootWorkbenchDialog(self).exec()); self.add_action(tools, "Mechanics Lab", lambda: MechanicsLabDialog(self).exec())
        safety = self.menuBar().addMenu("Safety"); self.add_action(safety, "Emergency Stop", self.engine.stop); self.add_action(safety, "Pause / Resume", self.engine.toggle_pause); self.add_action(safety, "Release Held Inputs", self.release_inputs)
        helpm = self.menuBar().addMenu("Help"); self.add_action(helpm, "Getting Started", self.show_getting_started); self.add_action(helpm, "About F3+", self.show_about)

    def add_action(self, menu, text, fn):
        action = QAction(text, self); action.triggered.connect(fn); menu.addAction(action)

    def apply_theme(self):
        QApplication.instance().setStyleSheet(stylesheet(self.settings.theme, self.settings.custom_palette)); self._art_cache.clear(); self._refresh_art(); self.refresh_tools(True)

    def _art(self, key, size=30):
        p = palette(self.settings.theme, self.settings.custom_palette); cache = (key, size, self.settings.theme, self.settings.minecraft_version, tuple(sorted(p.items())))
        if cache in self._art_cache: return self._art_cache[cache]
        pix = QPixmap(); local = self.settings.theme in {"chorus", "light", "minecraft", "aether", "foundry"} or (self.settings.theme == "custom" and getattr(self.settings, "custom_theme_use_minecraft_assets", False))
        if local:
            raw, _member, _version = texture_bytes(str(key), self.settings.minecraft_version)
            if raw and pix.loadFromData(raw): pix = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation)
        if pix.isNull(): pix = icon_pixmap(key, p, size)
        self._art_cache[cache] = pix; return pix

    def _refresh_art(self):
        if not hasattr(self, "brand"): return
        logo = self._art("app", 38); self.brand.setPixmap(logo); self.setWindowIcon(QIcon(logo))
        for i in range(self.nav.count()):
            item = self.nav.item(i); item.setIcon(QIcon(self._art(NAV_ART.get(item.data(Qt.UserRole), "home"), 22)))

    # ----- catalog ------------------------------------------------------
    def current_section(self):
        item = self.nav.currentItem(); return item.data(Qt.UserRole) if item else "Home"

    def _guide_for(self, spec: ToolSpec):
        guide = self._guide_cache.get(spec.id)
        if guide is None: guide = make_guide(spec); self._guide_cache[spec.id] = guide
        return guide

    def _display_group(self, spec, section):
        if section == "Home":
            if spec.id in self.settings.favorites: return "Favorites"
            if spec.id in self.settings.recent_tools: return "Recent"
            return "Suggested"
        return workspace_group(spec)

    def refresh_tools(self, preserve=False):
        if not hasattr(self, "tool_list"): return
        section = self.current_section(); query = self.search.text().strip().lower()
        candidates = list(BY_ID.values()) if query else specs_for_section(section, self.settings.favorites, self.settings.recent_tools)
        self.browser_title.setText("Search" if query else section)
        groups = {self._display_group(spec, section) for spec in candidates}
        old = self.group_filter.currentText(); self.group_filter.blockSignals(True); self.group_filter.clear(); self.group_filter.addItem("All groups")
        if query:
            for label, _ in NAV_SECTIONS:
                if label != "Home" and any(spec.workspace == label for spec in candidates): self.group_filter.addItem(label)
        else:
            for group in group_order(section, groups): self.group_filter.addItem(group)
        if preserve:
            index = self.group_filter.findText(old)
            if index >= 0: self.group_filter.setCurrentIndex(index)
        self.group_filter.blockSignals(False); selected_filter = self.group_filter.currentText(); rows = []
        for spec in candidates:
            guide = self._guide_for(spec)
            if query and query not in search_text(spec, guide): continue
            if selected_filter != "All groups":
                if query and spec.workspace != selected_filter: continue
                if not query and self._display_group(spec, section) != selected_filter: continue
            rows.append((spec, guide))
        rows.sort(key=lambda pair: (pair[0].workspace, pair[0].group, pair[0].name) if query else (group_order(section, groups).index(self._display_group(pair[0], section)) if self._display_group(pair[0], section) in group_order(section, groups) else 999, pair[0].name))
        self.tool_list.clear()
        for spec, guide in rows:
            item = QListWidgetItem(QIcon(self._art(tool_art_key(spec), 30)), f"{guide.title}\n{guide.summary}"); item.setData(Qt.UserRole, spec.id); item.setSizeHint(QSize(360, 74)); reason = safe_mode_restriction(spec) if self.settings.safe_mode else None
            if reason: item.setText("SAFE MODE • " + item.text()); item.setToolTip(reason)
            self.tool_list.addItem(item)
        self.result_count.setText(f"{len(rows)} workbench{'es' if len(rows) != 1 else ''}")
        if self._selected_id:
            for i in range(self.tool_list.count()):
                if self.tool_list.item(i).data(Qt.UserRole) == self._selected_id: self.tool_list.setCurrentRow(i); break
        if self.tool_list.currentRow() < 0 and self.tool_list.count(): self.tool_list.setCurrentRow(0)

    def selected_spec(self):
        items = self.tool_list.selectedItems(); return BY_ID.get(items[0].data(Qt.UserRole)) if items else None

    def selection_changed(self):
        spec = self.selected_spec()
        if not spec: self.run_btn.setEnabled(False); return
        self._selected_id = spec.id; guide = self._guide_for(spec); reason = safe_mode_restriction(spec) if self.settings.safe_mode else None
        self.feature_icon.setPixmap(self._art(tool_art_key(spec), 40)); self.feature_kicker.setText(spec.workspace.upper()); self.feature_title.setText(spec.name); self.feature_path.setText(f"{spec.workspace} / {spec.group} / {len(modes_for(spec))} operations"); self.favorite_btn.setText("★ Favorited" if spec.id in self.settings.favorites else "☆ Favorite"); self.run_btn.setEnabled(reason is None); self.run_btn.setText("Safe Mode Locked" if reason else "Open Workbench")
        p = palette(self.settings.theme, self.settings.custom_palette); esc = html.escape; locked = f"<p><b>Safe Mode:</b> {esc(reason)}</p>" if reason else ""
        operations = ", ".join(mode.name for mode in modes_for(spec))
        self.guide.setHtml(f"<div style='color:{p['text']}'>{locked}<h2>{esc(guide.title)}</h2><p>{esc(guide.summary)}</p><h3>When to use it</h3><p>{esc(guide.when)}</p><h3>How it works</h3><p>{esc(guide.how)}</p><h3>Operations</h3><p>{esc(operations)}</p><h3>Output</h3><p>{esc(guide.output)}</p><h3>Limits</h3><p>{esc(guide.limitations)}</p></div>"); self.stack.setCurrentIndex(0); self.guide_btn.setChecked(True)

    def _preferred_mode(self, tool: ToolSpec) -> str:
        for raw in list(self.settings.favorites) + list(self.settings.recent_tools):
            if LEGACY_TO_CANONICAL.get(str(raw)) == tool.id: return str(raw)
        return ""

    # ----- execution ----------------------------------------------------
    def run_selected(self):
        spec = self.selected_spec()
        if not spec: return
        reason = safe_mode_restriction(spec) if self.settings.safe_mode else None
        if reason: QMessageBox.warning(self, "Safe Mode", reason); return
        self.settings.remember_tool(spec.id)
        if spec.id == "villagers.explorer": VillagerExplorerDialog(self).exec(); return
        if spec.id == "simulation.rng": RngEnchantingDialog(self, self.executor, spec).exec(); return
        if spec.id == "simulation.loot": LootWorkbenchDialog(self).exec(); return
        if spec.id == "simulation.mechanics": MechanicsLabDialog(self).exec(); return
        dialog = OperationDialog(spec, self.executor, self.settings, self, self._preferred_mode(spec))
        if dialog.exec() != QDialog.Accepted or dialog.mode is None: return
        self.run_mode(dialog.mode, dialog.values())

    def run_mode(self, mode: ToolMode, params: dict[str, Any]):
        legacy = mode.legacy
        if legacy is None: return
        name = legacy.name
        if legacy.top == "Gameplay" and name in MACRO_NAMES: self.start_macro(name); return
        if name == "Capture Position": self.capture_position(); return
        if name == "Copy Sister Coordinates": self.copy_sister(); return
        if name == "Save Sister Waypoint": self.save_sister_waypoint(); return
        if name in {"Create Waypoint", "Rename Waypoint", "Delete Waypoint", "Nearest Waypoint", "Sort Waypoints by Distance", "Waypoint Route"}: self.waypoint_action(name); return
        if name == "Minecraft Version": self.version_dialog(); return
        if name == "Emergency Stop": self.engine.stop(); return
        if name == "Pause/Resume": self.engine.toggle_pause(); return
        if name == "Release Held Inputs": self.release_inputs(); return
        try:
            result = self.executor.execute(legacy, params); self._last_result = result.data; self.output.setPlainText(f"{name}\n\n{self._format(result.data)}" + (f"\n\nNote: {result.note}" if result.note else "")); self.stack.setCurrentIndex(1); self.results_btn.setChecked(True); self.map_btn.setEnabled(bool(extract_coordinate_layers(result.data)))
        except Exception as exc:
            QMessageBox.warning(self, name, str(exc))

    def open_result_map(self):
        if self._last_result is not None and extract_coordinate_layers(self._last_result): ResultMapDialog(self._last_result, self).exec()

    def _format(self, value, indent=0):
        pad = "  " * indent
        if isinstance(value, dict): return "\n".join(f"{pad}{str(k).replace('_', ' ').title()}:\n{self._format(v, indent+1)}" if isinstance(v, (dict, list, tuple)) else f"{pad}{str(k).replace('_', ' ').title()}: {self._scalar(v)}" for k, v in value.items())
        if isinstance(value, (list, tuple)): return "\n".join(self._format(v, indent) if isinstance(v, (dict, list, tuple)) else f"{pad}- {self._scalar(v)}" for v in value)
        return pad + self._scalar(value)

    def _scalar(self, value):
        if value is None: return "Not available"
        if isinstance(value, bool): return "Yes" if value else "No"
        if isinstance(value, float): return f"{value:.6f}".rstrip("0").rstrip(".")
        return str(value)

    # ----- automation / connection -------------------------------------
    def auto_link_minecraft(self):
        targets = discover_minecraft_targets(self.settings.minecraft_window_title)
        if len(targets) == 1: self.link_target(targets[0], True)
        elif len(targets) > 1: self.link_target(targets[0], True)
        else: self.update_link_badges()

    def relink_minecraft(self):
        targets = discover_minecraft_targets(self.settings.minecraft_window_title)
        if not targets: self.target = None; self._configure_input(None); QMessageBox.information(self, "Minecraft Link", "No Minecraft Java client was detected."); return
        if len(targets) == 1: self.link_target(targets[0]); return
        labels = [target.display for target in targets]
        from PySide6.QtWidgets import QInputDialog
        choice, ok = QInputDialog.getItem(self, "Select Minecraft", "Choose the client F3+ should control:", labels, 0, False)
        if ok: self.link_target(targets[labels.index(choice)])

    def link_target(self, target, quiet=False):
        self.engine.stop(); self.target = target
        try: self.input = create_input_backend(self.settings.input_mode, self.settings.minecraft_window_title, target)
        except Exception: self.input = create_input_backend("standard", self.settings.minecraft_window_title, target)
        self.focus_controller = create_focus_controller(target); self.engine.set_input(self.input); self.capture.input = self.input; clear_texture_cache(); self._art_cache.clear(); self.update_link_badges()
        if not quiet: self.statusBar().showMessage("Linked " + target.display)

    def _configure_input(self, target):
        self.input = create_input_backend(self.settings.input_mode, self.settings.minecraft_window_title, target); self.focus_controller = create_focus_controller(target); self.engine.set_input(self.input); self.capture.input = self.input; self.update_link_badges()

    def refresh_link_state(self):
        targets = discover_minecraft_targets(self.settings.minecraft_window_title)
        if self.target:
            match = next((target for target in targets if target.key == self.target.key or (target.pid and self.target.pid and target.pid == self.target.pid)), None)
            if match: self.target = match
            else: self.target = None
        if not self.target and self.settings.auto_link_minecraft and len(targets) == 1: self.link_target(targets[0], True); return
        self.update_link_badges()

    def update_link_badges(self):
        cap = getattr(self.input, "capabilities", None); self.link_badge.setText("● Linked: " + self.target.title[:28] if self.target else "● Minecraft not linked"); self.version_badge.setText(self.settings.minecraft_version); self.backend_badge.setText(getattr(cap, "session", "") or getattr(cap, "name", "Input")); self.background_badge.setText("BG: " + ("Targeted" if getattr(cap, "unfocused", False) else "Focus" if getattr(cap, "focus_switch", False) else "Foreground")); self.camera_badge.setText("Camera: " + ("Targeted" if getattr(cap, "targeted_relative_mouse", False) else "Focus" if getattr(cap, "focus_switch", False) else "Foreground"))

    def show_connection_status(self):
        cap = getattr(self.input, "capabilities", None); QMessageBox.information(self, "Connection Status", f"Client: {self.target.display if self.target else 'Not linked'}\nBackend: {getattr(cap, 'name', 'Unavailable')}\nBackground: {getattr(cap, 'background_label', 'Foreground only')}\nMinimized: {getattr(cap, 'minimized_label', 'Unavailable')}\n{getattr(cap, 'notes', '')}")

    def start_macro(self, name):
        if self.settings.safe_mode: QMessageBox.warning(self, "Safe Mode", "Automation is disabled in Safe Mode."); return
        fn = macro_runner(name)
        if not fn: QMessageBox.information(self, name, "This mode is a planning workflow rather than a direct macro."); return
        if not self.target and self.settings.auto_link_minecraft: self.auto_link_minecraft()
        cap = getattr(self.input, "capabilities", None); issue = focus_issue(name, cap, getattr(self.target, "minimized", False) if self.target else False)
        if issue and self.settings.allow_focus_switch and self.target and getattr(self.focus_controller, "available", False):
            if self.settings.confirm_focus_switch:
                answer = QMessageBox.question(self, "Minecraft focus required", issue + "\n\nAllow F3+ to focus Minecraft?")
                if answer != QMessageBox.Yes: return
            self._focus_token = self.focus_controller.capture_current(); self.focus_controller.focus(self.target); QTimer.singleShot(max(100, self.settings.focus_switch_delay_ms), lambda: self.engine.start(name, fn)); return
        if issue:
            seconds = max(1, self.settings.manual_focus_delay_seconds); answer = QMessageBox.question(self, "Minecraft focus required", issue + f"\n\nStart after a {seconds}-second countdown so you can focus Minecraft?")
            if answer != QMessageBox.Yes: return
            QTimer.singleShot(seconds * 1000, lambda: self.engine.start(name, fn)); return
        self.engine.start(name, fn)

    def release_inputs(self):
        try: self.input.release_all()
        except Exception: pass

    # ----- coordinates / user state ------------------------------------
    def set_seed(self):
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "World Seed", "Known Java world seed:", text=str(self.settings.seed or ""))
        if ok: self.settings.seed = text.strip(); self.settings.save(); self.seed_label.setText("Seed set" if self.settings.seed else "Seed not set")

    def set_dimension(self, value): self.settings.dimension = value; self.settings.save()

    def capture_position(self):
        try:
            pos = self.capture.capture(); self.current_position = pos; self.pos_label.setText(f"X {pos.x:g}  Y {pos.y:g}  Z {pos.z:g}")
        except Exception as exc: QMessageBox.warning(self, "Capture Position", str(exc))

    def copy_sister(self):
        if self.current_position is None: self.capture_position()
        if self.current_position is None: return
        p = self.current_position; to_nether = self.settings.dimension == "Overworld"; x = p.x / 8 if to_nether else p.x * 8; z = p.z / 8 if to_nether else p.z * 8; QApplication.clipboard().setText(f"{x:.3f} {p.y:.3f} {z:.3f}"); self.statusBar().showMessage("Copied sister coordinates")

    def save_sister_waypoint(self):
        self.copy_sister(); self.statusBar().showMessage("Sister coordinates copied. Use Waypoints, Routes & Surveys to save/organize locations.")

    def waypoint_action(self, name):
        # Preserve existing settings-backed waypoint behavior when that API is present;
        # otherwise surface the operation through the canonical route planner without
        # fabricating persistence.
        method = getattr(self.settings, name.lower().replace(" ", "_"), None)
        if callable(method): method(); self.settings.save(); return
        QMessageBox.information(self, name, "Open Waypoints, Routes & Surveys and choose this operation. Saved waypoint data remains in your F3+ settings.")

    def version_dialog(self):
        from PySide6.QtWidgets import QInputDialog
        value, ok = QInputDialog.getText(self, "Minecraft Version", "Target Minecraft Java version:", text=self.settings.minecraft_version)
        if ok and value.strip(): self.settings.minecraft_version = value.strip(); self.settings.save(); self.executor.minecraft_version = self.settings.minecraft_version; self.version_badge.setText(self.settings.minecraft_version); clear_texture_cache(); self._art_cache.clear()

    # ----- preferences / safety / hotkeys -------------------------------
    def options_dialog(self):
        dialog = OptionsDialog(self.settings, self)
        if dialog.exec() == QDialog.Accepted: dialog.apply(); self.executor.minecraft_version = self.settings.minecraft_version; self.dimension.setCurrentText(self.settings.dimension); self.stop_hotkeys(); self.start_hotkeys(); self._configure_input(self.target); self.apply_theme()

    def toggle_favorite(self):
        spec = self.selected_spec()
        if spec: self.settings.toggle_favorite(spec.id); self.selection_changed(); self.refresh_tools(True)

    def _sync_safe(self): self.safe_btn.setText("Safe Mode: ON" if self.settings.safe_mode else "Safe Mode"); self.safe_btn.setChecked(self.settings.safe_mode)

    def toggle_safe_mode(self, checked):
        checked = bool(checked)
        if checked and not self.settings.safe_mode:
            if QMessageBox.question(self, "Enable Safe Mode?", SAFE_MODE_SUMMARY + "\n\n" + SAFE_MODE_DISCLAIMER) != QMessageBox.Yes: self._sync_safe(); return
            self.engine.stop()
        self.settings.safe_mode = checked; self.settings.save(); self._sync_safe(); self.refresh_tools(True); self.selection_changed()

    def _pynput_hotkey(self, text):
        aliases = {"ctrl": "<ctrl>", "control": "<ctrl>", "alt": "<alt>", "shift": "<shift>", "cmd": "<cmd>", "win": "<cmd>", "space": "<space>"}
        return "+".join(aliases.get(part.strip().lower(), part.strip().lower()) for part in str(text).split("+") if part.strip())

    def start_hotkeys(self):
        if keyboard is None: return
        mapping = {
            self._pynput_hotkey(self.settings.stop_hotkey): self.engine.stop,
            self._pynput_hotkey(self.settings.toggle_hotkey): self.engine.toggle_pause,
            self._pynput_hotkey(self.settings.coord_copy_hotkey): self.copy_sister,
        }
        try: self.listener = keyboard.GlobalHotKeys(mapping); self.listener.start()
        except Exception: self.listener = None

    def stop_hotkeys(self):
        if self.listener:
            try: self.listener.stop()
            except Exception: pass
            self.listener = None

    # ----- misc ---------------------------------------------------------
    def update_status(self, status): self.statusBar().showMessage(str(status))

    def show_getting_started(self): QMessageBox.information(self, "Getting Started", "Pick a workbench, then choose the operation inside it. Old F3+ feature IDs and favorites are compatibility aliases and open the matching operation instead of appearing as separate tools.")

    def show_about(self): QMessageBox.information(self, "About F3+", f"F3+ {__version__}\n\nAll-in-one offline companion app for Minecraft. Built around community tools and based on Minescript/M.A.R.T by Lucid. F3+ brings common and niche technical Minecraft tools into one multi-platform desktop workflow.")

    def closeEvent(self, event):
        self.stop_hotkeys(); self.engine.stop(); self.release_inputs(); super().closeEvent(event)


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    window = F3Plus(); window.show()
    return app.exec()
