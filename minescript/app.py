from __future__ import annotations
import html
import sys

from PySide6.QtCore import QObject, Signal, Qt, QTimer, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap, QColor, QFont
from PySide6.QtWidgets import *
try:
    from pynput import keyboard
except Exception:
    keyboard = None

from . import TARGET_MINECRAFT, __version__
from .config import Settings
from .platform_input import (
    create_input_backend, create_focus_controller, discover_minecraft_targets,
)
from .platform_input.requirements import focus_issue
from .macro_engine import MacroEngine
from .coordinates import CoordinateCapture, Position
from .gameplay.presets import runner as macro_runner
from .catalog_ids import BY_ID
from .feature_executor import FeatureExecutor, MACRO_NAMES
from .descriptions import describe
from .tool_guides import (
    NAV_SECTIONS, nav_section, submenu_label, specs_for_section,
    workspace_group, group_order, tool_art_key, make_guide, search_text,
)
from .ui_theme import stylesheet, palette, COLOR_KEYS, DEFAULT_CUSTOM_PALETTE
from .safe_mode import restriction_reason as safe_mode_restriction, SAFE_MODE_SUMMARY, SAFE_MODE_DISCLAIMER
from .rng_recovery import launch_enchantment_cracker, enchantment_cracker_status
from .villagers import load_for_version, search as trade_search, PROFESSIONS, LEVEL_NAMES
from .guide_metadata import OUTPUT_KEYS
from .pixel_art import icon_pixmap
from .minecraft_art import texture_bytes, clear_texture_cache

NAV_ART = {
    "Home": "home",
    "Automation": "automation",
    "Navigation": "navigation",
    "World & Seed": "seed",
    "Structures & Biomes": "structure",
    "Calculators": "calculator",
    "Building & Farming": "building",
    "RNG": "rng",
    "Villagers": "villager",
    "Guided Setups": "guided",
    "Utilities": "utilities",
    "Safety": "safety",
}



class Bridge(QObject):
    status = Signal(object)


class ValuesDialog(QDialog):
    def __init__(self, title, fields, parent=None, subtitle=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        self.setMinimumWidth(500)
        self.inputs = {}
        layout = QVBoxLayout(self)
        if subtitle:
            note = QLabel(subtitle)
            note.setObjectName("Muted")
            note.setWordWrap(True)
            layout.addWidget(note)
        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)
        layout.addLayout(form)
        for key, label, default, kind in fields:
            if kind == "int":
                w = QSpinBox(); w.setRange(-2147483647, 2147483647); w.setValue(int(default))
            elif kind == "float":
                w = QDoubleSpinBox(); w.setDecimals(4); w.setRange(-1e12, 1e12); w.setValue(float(default))
            elif kind == "bool":
                w = QCheckBox(); w.setChecked(bool(default))
            elif kind == "choice":
                w = QComboBox(); w.addItems(list(default))
            else:
                w = QLineEdit(str(default))
            self.inputs[key] = w
            form.addRow(label, w)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Run")
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        out = {}
        for key, w in self.inputs.items():
            if isinstance(w, (QSpinBox, QDoubleSpinBox)): out[key] = w.value()
            elif isinstance(w, QCheckBox): out[key] = w.isChecked()
            elif isinstance(w, QComboBox): out[key] = w.currentText()
            else: out[key] = w.text()
        return out


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
        "Custom": "custom",
    }
    CUSTOM_LABELS = {
        "primary": "Primary",
        "primary2": "Primary pressed",
        "accent": "Accent",
        "accent2": "Secondary accent",
        "glow": "Focus / glow",
        "bg": "Window background",
        "surface": "Panel surface",
        "surface2": "Control surface",
        "surface3": "Selected surface",
        "text": "Primary text",
        "muted": "Secondary text",
        "border": "Borders",
        "success": "Success",
        "warning": "Warning",
        "danger": "Danger",
    }

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("F3+ Options")
        self.setObjectName("OptionsDialog")
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        self.resize(800, 660)
        outer = QVBoxLayout(self)
        intro = QLabel("Change behavior here; everyday controls stay in the command deck.")
        intro.setObjectName("Muted"); intro.setWordWrap(True); outer.addWidget(intro)
        tabs = QTabWidget(); tabs.setObjectName("OptionsTabs"); tabs.setDocumentMode(True); outer.addWidget(tabs, 1)

        general = QWidget(); general.setObjectName("OptionsPage"); g = QFormLayout(general)
        self.version = QLineEdit(settings.minecraft_version)
        self.dimension = QComboBox(); self.dimension.addItems(["Overworld", "Nether", "End"]); self.dimension.setCurrentText(settings.dimension)
        self.auto_link = QCheckBox("Link automatically when one Minecraft Java client is detected"); self.auto_link.setChecked(settings.auto_link_minecraft)
        self.title_hint = QLineEdit(settings.minecraft_window_title)
        g.addRow("Minecraft version", self.version); g.addRow("Default dimension", self.dimension); g.addRow("", self.auto_link); g.addRow("Window/title hint", self.title_hint)
        tabs.addTab(general, "General")

        inp = QWidget(); inp.setObjectName("OptionsPage"); f = QFormLayout(inp)
        self.mode = QComboBox(); self.mode.addItems(self.MODES.keys())
        wanted = settings.input_mode if settings.input_mode in {"auto", "targeted", "standard"} else "auto"
        self.mode.setCurrentText(next(k for k,v in self.MODES.items() if v == wanted))
        self.allow_focus = QCheckBox("Allow F3+ to focus Minecraft when a macro needs it"); self.allow_focus.setChecked(settings.allow_focus_switch)
        self.confirm_focus = QCheckBox("Ask before switching focus"); self.confirm_focus.setChecked(settings.confirm_focus_switch)
        self.restore_focus = QCheckBox("Return focus to the previous app when automation stops"); self.restore_focus.setChecked(settings.restore_previous_focus)
        self.focus_delay = QSpinBox(); self.focus_delay.setRange(100, 3000); self.focus_delay.setValue(settings.focus_switch_delay_ms); self.focus_delay.setSuffix(" ms")
        self.manual_delay = QSpinBox(); self.manual_delay.setRange(1, 10); self.manual_delay.setValue(settings.manual_focus_delay_seconds); self.manual_delay.setSuffix(" s")
        f.addRow("Input strategy", self.mode); f.addRow("", self.allow_focus); f.addRow("", self.confirm_focus); f.addRow("", self.restore_focus); f.addRow("Focus settle time", self.focus_delay); f.addRow("Manual focus countdown", self.manual_delay)
        tabs.addTab(inp, "Input")

        appearance = QWidget(); appearance.setObjectName("OptionsPage"); av = QVBoxLayout(appearance)
        af = QFormLayout(); av.addLayout(af)
        self.theme = QComboBox(); self.theme.addItems(self.THEMES.keys())
        selected = next((k for k,v in self.THEMES.items() if v == settings.theme), "Chorus")
        self.theme.setCurrentText(selected); af.addRow("Theme", self.theme)
        self.theme_note = QLabel(
            "Choose a preset here. Chorus is the default. Vanilla uses local Minecraft textures when available. Custom exposes the full F3+ palette and can optionally use recovered Minecraft artwork."
        )
        self.theme_note.setObjectName("Muted"); self.theme_note.setWordWrap(True); af.addRow("", self.theme_note)

        custom_box = QGroupBox("Custom palette")
        grid = QGridLayout(custom_box); grid.setColumnStretch(1,1)
        self.custom_fields = {}
        self.custom_minecraft_assets = QCheckBox("Use recovered Minecraft textures when available")
        self.custom_minecraft_assets.setChecked(bool(getattr(settings, "custom_theme_use_minecraft_assets", False)))
        grid.addWidget(self.custom_minecraft_assets,0,0,1,3)
        current = dict(DEFAULT_CUSTOM_PALETTE); current.update(settings.custom_palette or {})
        for row,key in enumerate(COLOR_KEYS, start=1):
            label = QLabel(self.CUSTOM_LABELS.get(key,key.replace('_',' ').title()))
            edit = QLineEdit(current.get(key,DEFAULT_CUSTOM_PALETTE[key])); edit.setMaxLength(9)
            pick = QPushButton("Choose…")
            pick.clicked.connect(lambda _=False, e=edit: self._choose_color(e))
            self.custom_fields[key] = edit
            grid.addWidget(label,row,0); grid.addWidget(edit,row,1); grid.addWidget(pick,row,2)
        reset = QPushButton("Reset custom palette")
        reset.clicked.connect(self._reset_custom)
        grid.addWidget(reset,len(COLOR_KEYS)+1,1,1,2)
        custom_scroll=QScrollArea(); custom_scroll.setObjectName("OptionsScroll"); custom_scroll.setWidgetResizable(True); custom_scroll.setFrameShape(QFrame.NoFrame); custom_scroll.setWidget(custom_box); av.addWidget(custom_scroll,1)
        self.custom_box = custom_box
        self.theme.currentTextChanged.connect(self._sync_custom_enabled)
        self._sync_custom_enabled()
        tabs.addTab(appearance, "Appearance")

        automation = QWidget(); automation.setObjectName("OptionsPage"); m = QFormLayout(automation)
        self.stop_hotkey = QLineEdit(settings.stop_hotkey); self.toggle_hotkey = QLineEdit(settings.toggle_hotkey); self.coord_copy_hotkey = QLineEdit(settings.coord_copy_hotkey)
        m.addRow("Emergency stop hotkey", self.stop_hotkey); m.addRow("Pause / resume hotkey", self.toggle_hotkey); m.addRow("Copy sister coordinates hotkey", self.coord_copy_hotkey)
        note = QLabel("Hotkeys use forms such as ctrl+alt+s. Emergency Stop always releases held inputs. The copy hotkey copies the current Overworld/Nether sister coordinates.")
        note.setWordWrap(True); note.setObjectName("Muted"); m.addRow("",note)
        tabs.addTab(automation, "Automation")

        components = QWidget(); components.setObjectName("OptionsPage"); c = QVBoxLayout(components)
        c.addWidget(QLabel("Components are prepared automatically when needed."))
        try:
            from .seed.bundled import cubiomes_status, bedrock_status
            cs,bs=cubiomes_status(),bedrock_status()
            component_state=(f"Cubiomes: {'ready' if cs.available else 'source missing'}\n"
                             f"Nether Bedrock Cracker: {'executable ready' if bs.executable else ('source ready; executable prepared on first use' if bs.source_dir.exists() else 'source missing')}")
            state=QLabel(component_state);state.setObjectName("Muted");state.setWordWrap(True);c.addWidget(state)
        except Exception:
            pass
        comp_text = QLabel(
            "Cubiomes is bundled for supported known-seed calculations. Nether Bedrock Cracker is prepared only for its seed-recovery workflow. "
            "Linux background input uses native Wayland/uinput paths. Other Linux display sessions use foreground-only input. macOS background input depends on Accessibility/Input Monitoring permission."
        )
        comp_text.setObjectName("Muted"); comp_text.setWordWrap(True); c.addWidget(comp_text); c.addStretch()
        tabs.addTab(components, "Components")

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); outer.addWidget(buttons)

    def _choose_color(self, edit: QLineEdit):
        initial = QColor(edit.text()) if QColor(edit.text()).isValid() else QColor("#FFFFFF")
        chosen = QColorDialog.getColor(initial,self,"Choose color")
        if chosen.isValid(): edit.setText(chosen.name(QColor.HexRgb).upper())

    def _reset_custom(self):
        for key,edit in self.custom_fields.items(): edit.setText(DEFAULT_CUSTOM_PALETTE[key])

    def _sync_custom_enabled(self):
        self.custom_box.setEnabled(self.THEMES.get(self.theme.currentText()) == "custom")

    def apply(self):
        s = self.settings
        s.minecraft_version = self.version.text().strip() or s.minecraft_version
        s.dimension = self.dimension.currentText()
        s.auto_link_minecraft = self.auto_link.isChecked()
        s.minecraft_window_title = self.title_hint.text().strip() or "Minecraft"
        s.input_mode = self.MODES[self.mode.currentText()]
        s.allow_focus_switch = self.allow_focus.isChecked()
        s.confirm_focus_switch = self.confirm_focus.isChecked()
        s.restore_previous_focus = self.restore_focus.isChecked()
        s.focus_switch_delay_ms = self.focus_delay.value()
        s.manual_focus_delay_seconds = self.manual_delay.value()
        s.theme = self.THEMES[self.theme.currentText()]
        custom = dict(DEFAULT_CUSTOM_PALETTE)
        for key,edit in self.custom_fields.items():
            value = edit.text().strip()
            custom[key] = value if QColor(value).isValid() else DEFAULT_CUSTOM_PALETTE[key]
        s.custom_palette = custom
        s.custom_theme_use_minecraft_assets = self.custom_minecraft_assets.isChecked()
        s.stop_hotkey = self.stop_hotkey.text().strip() or "ctrl+alt+s"
        s.toggle_hotkey = self.toggle_hotkey.text().strip() or "ctrl+alt+space"
        s.coord_copy_hotkey = self.coord_copy_hotkey.text().strip() or "ctrl+alt+c"
        s.save()


class TradeBrowser(QDialog):
    def __init__(self, version, parent=None):
        super().__init__(parent); self.setWindowTitle("Villager Trade Explorer");
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        self.resize(1040, 680)
        self.trades, self.source = load_for_version(version)
        v = QVBoxLayout(self); top = QHBoxLayout(); v.addLayout(top)
        self.prof = QComboBox(); self.prof.addItem("All professions"); self.prof.addItems([p.title() for p in PROFESSIONS]); top.addWidget(self.prof)
        self.level = QComboBox(); self.level.addItem("All levels"); self.level.addItems([f"{i} — {LEVEL_NAMES[i]}" for i in range(1,6)]); top.addWidget(self.level)
        self.query = QLineEdit(); self.query.setPlaceholderText("Search item or trade…"); top.addWidget(self.query,1)
        self.source_label = QLabel(f"{len(self.trades)} definitions • {self.source}"); self.source_label.setObjectName("Muted"); top.addWidget(self.source_label)
        self.table = QTableWidget(0,8); self.table.setHorizontalHeaderLabels(["Profession","Level","Trade","Wants","Additional","Gives","Max uses","XP"]); self.table.horizontalHeader().setStretchLastSection(True); v.addWidget(self.table)
        self._first_refresh = True
        self.prof.currentTextChanged.connect(self.refresh); self.level.currentTextChanged.connect(self.refresh); self.query.textChanged.connect(self.refresh); self.refresh()

    def refresh(self):
        p = None if self.prof.currentText().startswith("All") else self.prof.currentText().lower()
        l = None if self.level.currentText().startswith("All") else int(self.level.currentText()[0])
        rows = trade_search(self.trades,self.query.text(),p,l)
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(rows))
            for r,t in enumerate(rows):
                vals=[t.profession.title(),f"{t.level} — {LEVEL_NAMES.get(t.level,t.level)}",t.name,t.wants,t.additional_wants or "",t.gives,"" if t.max_uses is None else str(t.max_uses),"" if t.xp is None else str(t.xp)]
                for c,val in enumerate(vals): self.table.setItem(r,c,QTableWidgetItem(val))
            if self._first_refresh:
                self.table.resizeColumnsToContents(); self._first_refresh=False
        finally:
            self.table.setUpdatesEnabled(True)


class F3Plus(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings.load()
        self.target = None
        self.focus_controller = create_focus_controller(None)
        self.input = create_input_backend("standard", self.settings.minecraft_window_title)
        self.engine = MacroEngine(self.input)
        self.capture = CoordinateCapture(self.input,self.settings)
        self.executor = FeatureExecutor(self.settings.minecraft_version)
        self.current_position = None
        self.engine.set_position_provider(self.capture.capture)
        self._focus_token = None
        self._restore_focus_pending = False
        self._selected_id = None
        self._guide_cache = {}
        self._art_cache = {}
        self.listener = None

        self.bridge = Bridge(); self.bridge.status.connect(self.update_status); self.engine.on_status = self.bridge.status.emit
        self.setWindowTitle(f"F3+ {__version__}")
        self.resize(1480, 900); self.setMinimumSize(1240, 720)
        self.build_ui(); self.build_menu(); self.apply_theme(); self.start_hotkeys()

        self.link_timer = QTimer(self); self.link_timer.timeout.connect(self.refresh_link_state); self.link_timer.start(5000)
        if self.settings.auto_link_minecraft: QTimer.singleShot(250, self.auto_link_minecraft)

    # ---------- UI ----------
    def apply_theme(self):
        QApplication.instance().setStyleSheet(stylesheet(self.settings.theme,self.settings.custom_palette))
        self._art_cache.clear()
        self._refresh_theme_assets()
        if hasattr(self,"tool_list") and self.selected_spec():
            self.selection_changed()

    def build_ui(self):
        root = QWidget(); root.setObjectName("AppRoot"); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)

        # Command deck: product identity, connection state, and actions that matter while automation is running.
        top = QFrame(); top.setObjectName("CommandDeck")
        top_layout = QHBoxLayout(top); top_layout.setContentsMargins(18,9,18,9); top_layout.setSpacing(10)
        self.brand_logo = QLabel(); self.brand_logo.setFixedSize(44,44); self.brand_logo.setAlignment(Qt.AlignCenter); self.brand_logo.setToolTip("Uses artwork from your installed Minecraft client when available; otherwise uses F3+ fallback art."); top_layout.addWidget(self.brand_logo)
        brand = QVBoxLayout(); brand.setSpacing(0)
        title = QLabel("F3+"); title.setObjectName("AppTitle"); brand.addWidget(title)
        sub = QLabel("Minecraft technical companion"); sub.setObjectName("AppSubtitle"); brand.addWidget(sub)
        top_layout.addLayout(brand)
        top_layout.addStretch(1)

        status = QFrame(); status.setObjectName("StatusCard")
        sl = QHBoxLayout(status); sl.setContentsMargins(10,5,10,5); sl.setSpacing(10)
        self.link_badge = QLabel("● Minecraft not linked"); self.link_badge.setObjectName("StatusBad"); sl.addWidget(self.link_badge)
        self.backend_badge = QLabel("Foreground"); self.backend_badge.setObjectName("Muted"); sl.addWidget(self.backend_badge)
        self.background_badge = QLabel("BG —"); self.background_badge.setObjectName("Muted"); sl.addWidget(self.background_badge)
        self.minimized_badge = QLabel("MIN —"); self.minimized_badge.setObjectName("Muted"); sl.addWidget(self.minimized_badge)
        self.camera_badge = QLabel("CAM —"); self.camera_badge.setObjectName("Muted"); sl.addWidget(self.camera_badge)
        top_layout.addWidget(status)

        self.relink_btn = QPushButton("Relink"); self.relink_btn.setObjectName("AccentButton"); self.relink_btn.clicked.connect(self.relink_minecraft); top_layout.addWidget(self.relink_btn)
        self.safe_mode_btn = QPushButton("Safe Mode"); self.safe_mode_btn.setObjectName("SafeModeButton"); self.safe_mode_btn.setCheckable(True); self.safe_mode_btn.setChecked(self.settings.safe_mode); self.safe_mode_btn.clicked.connect(self.toggle_safe_mode); top_layout.addWidget(self.safe_mode_btn)
        options = QPushButton("Options"); options.clicked.connect(self.options_dialog); top_layout.addWidget(options)
        pause = QPushButton("Pause / Resume"); pause.clicked.connect(self.engine.toggle_pause); top_layout.addWidget(pause)
        stop = QPushButton("EMERGENCY STOP"); stop.setObjectName("DangerButton"); stop.clicked.connect(self.engine.stop); top_layout.addWidget(stop)
        outer.addWidget(top)
        self._sync_safe_mode_button()

        # Context deck: global search and world state. This replaces the old cluttered sidebar controls.
        context = QFrame(); context.setObjectName("ContextDeck")
        cl = QHBoxLayout(context); cl.setContentsMargins(16,7,16,7); cl.setSpacing(9)
        search_label = QLabel("FIND"); search_label.setObjectName("DeckLabel"); cl.addWidget(search_label)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search tools by name, task, input, or result…"); self.search.setClearButtonEnabled(True); cl.addWidget(self.search,2)
        cl.addSpacing(6)
        dim_label = QLabel("DIMENSION"); dim_label.setObjectName("DeckLabel"); cl.addWidget(dim_label)
        self.dimension = QComboBox(); self.dimension.addItems(["Overworld","Nether","End"]); self.dimension.setCurrentText(self.settings.dimension); self.dimension.currentTextChanged.connect(self.set_dimension); cl.addWidget(self.dimension)
        self.version_badge = QLabel("Java • "+self.settings.minecraft_version); self.version_badge.setObjectName("Muted"); cl.addWidget(self.version_badge)
        self.seed_label = QLabel("Seed set" if self.settings.seed else "Seed not set"); self.seed_label.setObjectName("Muted"); cl.addWidget(self.seed_label)
        seed_btn = QPushButton("World Seed"); seed_btn.clicked.connect(self.set_seed); cl.addWidget(seed_btn)
        self.pos_label = QLabel("Position not captured"); self.pos_label.setObjectName("Muted"); cl.addWidget(self.pos_label)
        capture = QPushButton("Capture F3+C"); capture.clicked.connect(self.capture_position); cl.addWidget(capture)
        outer.addWidget(context)

        work = QSplitter(Qt.Horizontal); work.setChildrenCollapsible(False); outer.addWidget(work,1)

        # Navigation rail: top-level destinations only.
        rail = QFrame(); rail.setObjectName("NavRail")
        rail_l = QVBoxLayout(rail); rail_l.setContentsMargins(8,12,8,10); rail_l.setSpacing(8)
        kicker = QLabel("WORKSPACES"); kicker.setObjectName("DeckLabel"); rail_l.addWidget(kicker)
        self.nav = QListWidget(); self.nav.setObjectName("NavList"); self.nav.setIconSize(QSize(23,23)); rail_l.addWidget(self.nav,1)
        for label, glyph in NAV_SECTIONS:
            item=QListWidgetItem(label); item.setIcon(self._nav_icon(label,23)); item.setData(Qt.UserRole,label); self.nav.addItem(item)
        nav_tip = QLabel("Favorites and recent tools live on Home."); nav_tip.setObjectName("Muted"); nav_tip.setWordWrap(True); rail_l.addWidget(nav_tip)
        work.addWidget(rail)

        # Library pane: workspace title, task grouping, and lightweight tool cards.
        browser = QFrame(); browser.setObjectName("LibraryPane")
        b = QVBoxLayout(browser); b.setContentsMargins(14,13,14,13); b.setSpacing(8)
        header = QHBoxLayout()
        hbox = QVBoxLayout(); hbox.setSpacing(0)
        wk = QLabel("TOOL LIBRARY"); wk.setObjectName("DeckLabel"); hbox.addWidget(wk)
        self.browser_title = QLabel("Home"); self.browser_title.setObjectName("WorkspaceTitle"); hbox.addWidget(self.browser_title)
        header.addLayout(hbox); header.addStretch()
        self.result_count = QLabel(""); self.result_count.setObjectName("Muted"); header.addWidget(self.result_count)
        b.addLayout(header)
        filter_row = QHBoxLayout(); filter_row.addWidget(QLabel("Task group"))
        self.group_filter = QComboBox(); self.group_filter.addItem("All groups"); filter_row.addWidget(self.group_filter,1); b.addLayout(filter_row)
        self.tool_list = QListWidget(); self.tool_list.setObjectName("ToolList"); self.tool_list.setSpacing(2); self.tool_list.setUniformItemSizes(False); self.tool_list.setIconSize(QSize(30,30)); b.addWidget(self.tool_list,1)
        work.addWidget(browser)

        # Inspector pane: one selected tool, one primary action, then Guide/Results as a segmented view.
        detail = QFrame(); detail.setObjectName("InspectorPane")
        d = QVBoxLayout(detail); d.setContentsMargins(14,13,14,13); d.setSpacing(9)
        hero = QFrame(); hero.setObjectName("InspectorHero"); meta = QHBoxLayout(hero); meta.setContentsMargins(12,10,12,10)
        self.feature_icon=QLabel(); self.feature_icon.setFixedSize(48,48); self.feature_icon.setAlignment(Qt.AlignCenter); meta.addWidget(self.feature_icon)
        titlebox = QVBoxLayout(); titlebox.setSpacing(1)
        self.feature_kicker = QLabel("SELECT A TOOL"); self.feature_kicker.setObjectName("DeckLabel"); titlebox.addWidget(self.feature_kicker)
        self.feature_title = QLabel("Choose a tool to inspect"); self.feature_title.setObjectName("DetailTitle"); self.feature_title.setWordWrap(True); titlebox.addWidget(self.feature_title)
        self.feature_path = QLabel("Search globally or pick a workspace."); self.feature_path.setObjectName("Muted"); self.feature_path.setWordWrap(True); titlebox.addWidget(self.feature_path)
        meta.addLayout(titlebox,1)
        self.favorite_btn = QPushButton("☆ Favorite"); self.favorite_btn.clicked.connect(self.toggle_favorite); meta.addWidget(self.favorite_btn)
        d.addWidget(hero)

        actions = QHBoxLayout()
        self.run_btn = QPushButton("Run / Configure"); self.run_btn.setObjectName("PrimaryButton"); self.run_btn.clicked.connect(self.run_selected); self.run_btn.setEnabled(False); actions.addWidget(self.run_btn)
        actions.addStretch()
        self.guide_btn = QPushButton("Guide"); self.guide_btn.setObjectName("SegmentButton"); self.guide_btn.setCheckable(True); self.guide_btn.setChecked(True); actions.addWidget(self.guide_btn)
        self.results_btn = QPushButton("Results"); self.results_btn.setObjectName("SegmentButton"); self.results_btn.setCheckable(True); actions.addWidget(self.results_btn)
        self.view_group = QButtonGroup(self); self.view_group.setExclusive(True); self.view_group.addButton(self.guide_btn,0); self.view_group.addButton(self.results_btn,1)
        d.addLayout(actions)

        self.detail_stack = QStackedWidget()
        self.guide = QTextBrowser(); self.guide.setOpenExternalLinks(False); self.detail_stack.addWidget(self.guide)
        self.output = QPlainTextEdit(); self.output.setReadOnly(True); self.output.setPlaceholderText("Run a tool to place its result here."); self.detail_stack.addWidget(self.output)
        d.addWidget(self.detail_stack,1)
        self.guide_btn.clicked.connect(lambda: self._set_detail_view(0)); self.results_btn.clicked.connect(lambda: self._set_detail_view(1))
        work.addWidget(detail)
        work.setSizes([205,460,815])

        self.nav.currentItemChanged.connect(lambda *_: self.refresh_tools())
        self.search.textChanged.connect(lambda *_: self.refresh_tools())
        self.group_filter.currentTextChanged.connect(lambda *_: self.refresh_tools(preserve_groups=True))
        self.tool_list.itemSelectionChanged.connect(self.selection_changed)
        self.tool_list.itemDoubleClicked.connect(lambda *_: self.run_selected())
        self.nav.setCurrentRow(0)
        self._refresh_theme_assets()
        self.statusBar().showMessage("Ready. Choose a tool or link Minecraft for automation.")

    def _set_detail_view(self,index:int):
        index=0 if int(index)==0 else 1
        self.detail_stack.setCurrentIndex(index)
        self.guide_btn.setChecked(index==0); self.results_btn.setChecked(index==1)

    def build_menu(self):
        mb = self.menuBar()
        appm = mb.addMenu("F3+")
        self.add_action(appm,"Set World Seed",self.set_seed); self.add_action(appm,"Capture Position",self.capture_position); self.add_action(appm,"Villager Trade Explorer",self.open_trade_browser); appm.addSeparator(); self.add_action(appm,"Exit",self.close)
        conn = mb.addMenu("Connection")
        self.add_action(conn,"Relink Minecraft",self.relink_minecraft)
        self.add_action(conn,"Connection Status…",self.show_connection_status)
        optionsm = mb.addMenu("Options")
        self.add_action(optionsm,"Open Options…",self.options_dialog); self.add_action(optionsm,"Minecraft Version",self.version_dialog); self.add_action(optionsm,"Set World Seed",self.set_seed)
        safety = mb.addMenu("Safety")
        self.add_action(safety,"Safe Mode Information…",self.show_safe_mode_info); safety.addSeparator()
        self.add_action(safety,"Emergency Stop",self.engine.stop); self.add_action(safety,"Pause / Resume",self.engine.toggle_pause); self.add_action(safety,"Release Held Inputs",self.release_inputs)
        helpm = mb.addMenu("Help")
        self.add_action(helpm,"Getting Started",self.show_getting_started); self.add_action(helpm,"About F3+",self.show_about)

    def add_action(self, menu, text, fn):
        a=QAction(text,self); a.triggered.connect(fn); menu.addAction(a)

    def _current_section(self):
        item=self.nav.currentItem(); return item.data(Qt.UserRole) if item else "Home"

    def _display_group(self,spec,section=None):
        section=section or self._current_section()
        if section=="Home":
            if spec.id in self.settings.favorites:return "Favorites"
            if spec.id in self.settings.recent_tools:return "Recent"
            return "Suggested"
        return workspace_group(spec)

    def _art_pixmap(self,key,size=32):
        p=palette(self.settings.theme,self.settings.custom_palette)
        # Preset themes can use recognizable textures read from the player's own
        # Minecraft JAR. Cyberpunk and Custom keep recolorable F3+ art so their
        # palette remains intentional. No Mojang texture is bundled or cached to disk.
        local_allowed=self.settings.theme in {"chorus","light","minecraft"} or (self.settings.theme == "custom" and bool(getattr(self.settings, "custom_theme_use_minecraft_assets", False)))
        cache_key=(str(key),int(size),self.settings.theme,self.settings.minecraft_version,tuple(sorted(p.items())))
        cached=self._art_cache.get(cache_key)
        if cached is not None:return cached
        pix=QPixmap()
        if local_allowed:
            data,member,version=texture_bytes(str(key),self.settings.minecraft_version)
            if data and pix.loadFromData(data):
                pix=pix.scaled(int(size),int(size),Qt.KeepAspectRatio,Qt.FastTransformation)
                pix.setDevicePixelRatio(1.0)
        if pix.isNull():
            pix=icon_pixmap(key,p,size)
        self._art_cache[cache_key]=pix
        return pix

    def _art_icon(self,key,size=32):
        return QIcon(self._art_pixmap(key,size))

    def _nav_icon(self,label,size=24):
        return self._art_icon(NAV_ART.get(label,"home"),size)

    def _brand_pixmap(self,size=40):
        return self._art_pixmap("app",size)

    def _refresh_theme_assets(self):
        if hasattr(self,"brand_logo"):
            pix=self._brand_pixmap(40)
            self.brand_logo.setPixmap(pix)
            self.setWindowIcon(QIcon(pix))
        if hasattr(self,"nav"):
            for i in range(self.nav.count()):
                item=self.nav.item(i); label=item.data(Qt.UserRole)
                if label:item.setIcon(self._nav_icon(label,23))
        spec=self.selected_spec() if hasattr(self,"tool_list") else None
        if spec and hasattr(self,"feature_icon"):
            self.feature_icon.setPixmap(self._icon_for_spec(spec).pixmap(40,40))
        if hasattr(self,"tool_list"):
            self.refresh_tools(preserve_groups=True)

    def _guide_for(self,spec):
        cached=self._guide_cache.get(spec.id)
        if cached is not None:return cached
        fields=self.executor.input_fields(spec); labels=[x[1] for x in fields]
        status="macro" if spec.name in MACRO_NAMES else "tool"
        guide=make_guide(spec,describe(spec),labels,OUTPUT_KEYS.get(spec.id,[]),status)
        self._guide_cache[spec.id]=guide
        return guide

    def _icon_for_spec(self,spec):
        return self._art_icon(tool_art_key(spec),30)

    def refresh_tools(self, preserve_groups=False):
        section=self._current_section(); query=self.search.text().strip().lower()
        if query:
            candidates=list(BY_ID.values()); self.browser_title.setText("Search")
        else:
            candidates=specs_for_section(section,self.settings.favorites,self.settings.recent_tools); self.browser_title.setText(section)
        groups={self._display_group(s,section) for s in candidates}
        if not preserve_groups:
            old_value=self.group_filter.currentText()
            self.group_filter.blockSignals(True); self.group_filter.clear(); self.group_filter.addItem("All groups")
            if query:
                # Search is global: filter by workspace instead of presenting a long
                # mixed list of inherited catalog submenu names.
                for label,_ in NAV_SECTIONS:
                    if label!="Home" and any(nav_section(s)==label for s in candidates):self.group_filter.addItem(label)
            else:
                for group in group_order(section,groups):self.group_filter.addItem(group)
            if preserve_groups and old_value:
                i=self.group_filter.findText(old_value)
                if i>=0:self.group_filter.setCurrentIndex(i)
            self.group_filter.blockSignals(False)
        selected_filter=self.group_filter.currentText()
        filtered=[]
        for spec in candidates:
            guide=self._guide_for(spec)
            if query and query not in search_text(spec,guide):continue
            if selected_filter!="All groups":
                if query and nav_section(spec)!=selected_filter:continue
                if not query and self._display_group(spec,section)!=selected_filter:continue
            filtered.append((spec,guide))
        if query:
            def qscore(pair):
                spec,guide=pair; title=guide.title.lower(); raw=spec.name.lower()
                return (0 if title.startswith(query) else 1 if query in title else 2 if raw.startswith(query) else 3, nav_section(spec), workspace_group(spec), title)
            filtered.sort(key=qscore)
        else:
            order={g:i for i,g in enumerate(group_order(section,{self._display_group(s,section) for s,_ in filtered}))}
            original={s.id:i for i,s in enumerate(BY_ID.values())}
            filtered.sort(key=lambda pair:(order.get(self._display_group(pair[0],section),999),original.get(pair[0].id,9999)))

        p=palette(self.settings.theme,self.settings.custom_palette)
        self.tool_list.setUpdatesEnabled(False)
        try:
            self.tool_list.clear()
            current_group=None
            show_headers=(not query and selected_filter=="All groups")
            for spec,guide in filtered:
                group=self._display_group(spec,section)
                if show_headers and group!=current_group:
                    current_group=group
                    header=QListWidgetItem(group.upper())
                    header.setFlags(Qt.NoItemFlags); header.setData(Qt.UserRole,None); header.setData(Qt.UserRole+1,"group-header")
                    header.setForeground(QColor(p["accent"])); header.setBackground(QColor(p["surface"])); header.setFont(QFont("",9,QFont.Bold)); header.setSizeHint(QSize(360,36))
                    self.tool_list.addItem(header)
                item=QListWidgetItem(self._icon_for_spec(spec),""); item.setData(Qt.UserRole,spec.id); item.setSizeHint(QSize(360,76))
                reason=safe_mode_restriction(spec) if self.settings.safe_mode else None
                fav="★ " if spec.id in self.settings.favorites else ""
                locked="SAFE MODE • " if reason else ""
                item.setText(f"{locked}{fav}{guide.title}\n{guide.summary[:112]}{'…' if len(guide.summary)>112 else ''}")
                item.setToolTip((f"Safe Mode: {reason}\n\n" if reason else "")+f"{guide.title}\n{guide.summary}\n\n{guide.when}")
                self.tool_list.addItem(item)
        finally:
            self.tool_list.setUpdatesEnabled(True)
        self.result_count.setText(f"{len(filtered)} tool{'s' if len(filtered)!=1 else ''}")
        if self._selected_id:
            for i in range(self.tool_list.count()):
                if self.tool_list.item(i).data(Qt.UserRole)==self._selected_id:self.tool_list.setCurrentRow(i);break
        if self.tool_list.currentRow()<0:
            for i in range(self.tool_list.count()):
                if self.tool_list.item(i).data(Qt.UserRole):self.tool_list.setCurrentRow(i);break

    def selected_spec(self):
        items=self.tool_list.selectedItems(); fid=items[0].data(Qt.UserRole) if items else None; return BY_ID.get(fid) if fid else None

    def selection_changed(self):
        spec=self.selected_spec()
        if not spec:
            self.run_btn.setEnabled(False);return
        self._selected_id=spec.id; guide=self._guide_for(spec)
        reason=safe_mode_restriction(spec) if self.settings.safe_mode else None
        self.run_btn.setEnabled(reason is None); self.run_btn.setText("Safe Mode Locked" if reason else "Run / Configure")
        self.feature_icon.setPixmap(self._icon_for_spec(spec).pixmap(40,40))
        self.feature_kicker.setText("AUTOMATION" if spec.name in MACRO_NAMES else nav_section(spec).upper())
        self.feature_title.setText(guide.title)
        self.feature_path.setText(f"{nav_section(spec)}  /  {workspace_group(spec)}")
        self.favorite_btn.setText("★ Favorited" if spec.id in self.settings.favorites else "☆ Favorite")
        self.guide.setHtml(self._guide_html(spec,guide,reason)); self._set_detail_view(0)

    def _guide_html(self,spec,guide,restriction=None):
        esc=html.escape; p=palette(self.settings.theme,self.settings.custom_palette)
        tag_html=(f" <span style='color:{p['muted']}'>/</span> ").join(f"<span style='color:{p['accent']}'>{esc(t)}</span>" for t in guide.tags)
        locked=(f"<div style='padding:10px;border:1px solid {p['accent']};background:{p['surface3']};border-radius:6px'><b>Safe Mode locked this tool.</b><br>{esc(restriction)}</div>" if restriction else "")
        return f"""
        <div style='line-height:1.45;color:{p['text']}'>
        {locked}<p>{tag_html}</p>
        <h3 style='color:{p['accent']}'>What it does</h3><p>{esc(guide.summary)}</p>
        <h3 style='color:{p['accent']}'>When to use it</h3><p>{esc(guide.when)}</p>
        <h3 style='color:{p['accent']}'>How to use it</h3><p>{esc(guide.how)}</p>
        <h3 style='color:{p['accent']}'>Inputs</h3><p>{esc(guide.inputs)}</p>
        <h3 style='color:{p['accent']}'>Output</h3><p>{esc(guide.output)}</p>
        <h3 style='color:{p['accent']}'>Version & limitations</h3><p>{esc(guide.limitations)}</p>
        </div>"""

    # ---------- Minecraft link & background input ----------
    def auto_link_minecraft(self):
        targets=discover_minecraft_targets(self.settings.minecraft_window_title)
        if len(targets)==1:self.link_target(targets[0],quiet=True)
        elif len(targets)>1:self.choose_target(targets)
        else:self.update_link_badges()

    def relink_minecraft(self):
        targets=discover_minecraft_targets(self.settings.minecraft_window_title)
        if not targets:
            self.target=None; self._configure_input(None)
            QMessageBox.information(self,"Minecraft Link","No Minecraft Java window was detected. Start Minecraft, reach the game window, then select Relink again.\n\nCalculators and non-input tools still work without a link.")
            return
        if len(targets)==1:self.link_target(targets[0]);return
        self.choose_target(targets)

    def choose_target(self,targets):
        labels=[t.display for t in targets]
        choice,ok=QInputDialog.getItem(self,"Select Minecraft Client","More than one Minecraft Java client was detected. Choose the one F3+ should control:",labels,0,False)
        if ok:self.link_target(targets[labels.index(choice)])

    def link_target(self,target,quiet=False):
        self.engine.stop(); self.target=target
        try:
            self.input=create_input_backend(self.settings.input_mode,self.settings.minecraft_window_title,target)
        except Exception as exc:
            self.input=create_input_backend("standard",self.settings.minecraft_window_title,target)
            if not quiet:self.write(f"Background backend could not start. Foreground fallback is active.\n{exc}")
        self.focus_controller=create_focus_controller(target)
        self.engine.set_input(self.input); self.capture.input=self.input; self.engine.set_position_provider(self.capture.capture)
        clear_texture_cache(); self._art_cache.clear(); self._refresh_theme_assets()
        self.update_link_badges()
        if not quiet:self.write(f"Linked Minecraft: {target.display}\nInput: {self.input.capabilities.name}")

    def _configure_input(self,target):
        self.input=create_input_backend(self.settings.input_mode,self.settings.minecraft_window_title,target)
        self.focus_controller=create_focus_controller(target)
        self.engine.set_input(self.input); self.capture.input=self.input; self.update_link_badges()

    def refresh_link_state(self):
        found=discover_minecraft_targets(self.settings.minecraft_window_title)
        if self.target:
            match=next((x for x in found if x.key==self.target.key or (x.pid and self.target.pid and x.pid==self.target.pid)),None)
            if match:self.target=match
            else:
                self.target=None
                if self.settings.auto_link_minecraft and len(found)==1:self.link_target(found[0],quiet=True);return
        elif self.settings.auto_link_minecraft and len(found)==1:
            self.link_target(found[0],quiet=True);return
        self.update_link_badges()

    def update_link_badges(self):
        cap=getattr(self.input,"capabilities",None)
        if self.target:
            self.link_badge.setText("● Linked: "+self.target.title[:28]); self.link_badge.setObjectName("StatusGood")
        else:
            self.link_badge.setText("● Minecraft not linked"); self.link_badge.setObjectName("StatusBad")
        self.link_badge.style().unpolish(self.link_badge);self.link_badge.style().polish(self.link_badge)
        self.version_badge.setText("Java • "+self.settings.minecraft_version)
        session=getattr(cap,"session","") or "Input"
        self.backend_badge.setText(session)
        if getattr(cap,"unfocused",False): bg="Targeted"
        elif getattr(cap,"focus_switch",False): bg="Focus switch"
        else: bg="Foreground"
        self.background_badge.setText("BG: "+bg)
        minimized="Best effort" if getattr(cap,"minimized",False) else ("Restore first" if getattr(cap,"focus_switch",False) else "No")
        if self.target and self.target.minimized is True:minimized="MINIMIZED • "+minimized
        self.minimized_badge.setText("Min: "+minimized)
        camera="Targeted" if getattr(cap,"targeted_relative_mouse",False) else ("Focus" if getattr(cap,"focus_switch",False) else "Foreground")
        self.camera_badge.setText("Camera: "+camera)
        tip=(getattr(cap,"notes","") or "")
        if self.target:tip=f"{self.target.display}\n{tip}"
        for w in (self.link_badge,self.version_badge,self.backend_badge,self.background_badge,self.minimized_badge,self.camera_badge):w.setToolTip(tip)

    def show_connection_status(self):
        cap=getattr(self.input,"capabilities",None)
        target=self.target.display if self.target else "No Minecraft Java client is linked."
        lines=[
            f"Client: {target}",
            f"Input backend: {getattr(cap,'name','Unavailable')}",
            f"Desktop session: {getattr(cap,'session','') or 'Not reported'}",
            f"Background input: {getattr(cap,'background_label','Foreground only')}",
            f"Minimized input: {getattr(cap,'minimized_label','Not available')}",
            "Camera input: "+("Targeted" if getattr(cap,'targeted_relative_mouse',False) else ("Focus switching when required" if getattr(cap,'focus_switch',False) else "Foreground only")),
            f"Automatic focus helper: {getattr(self.focus_controller,'name','Manual focus') if getattr(self.focus_controller,'available',False) else 'Manual focus only'}",
        ]
        if getattr(cap,"notes",""):lines += ["",str(cap.notes)]
        QMessageBox.information(self,"Minecraft Connection Status","\n".join(lines))

    # ---------- execution ----------
    def run_selected(self):
        spec=self.selected_spec()
        if not spec:return
        reason=safe_mode_restriction(spec) if self.settings.safe_mode else None
        if reason:
            QMessageBox.warning(self,"Safe Mode",reason+"\n\nDisable Safe Mode only if the server rules permit this feature.")
            return
        self.settings.remember_tool(spec.id)
        if spec.top=="Gameplay" and spec.name in MACRO_NAMES:return self.start_macro(spec.name)
        if spec.top=="Villager Explorer" and (spec.submenu in ("Trades","Professions") or spec.name in [p.title() for p in PROFESSIONS]):return self.open_trade_browser(spec.name if spec.submenu=="Professions" else None)
        name=spec.name
        if name=="Capture Position":return self.capture_position()
        if name=="Copy Sister Coordinates":return self.copy_sister()
        if name=="Save Sister Waypoint":return self.save_sister_waypoint()
        if name in ("Create Waypoint","Rename Waypoint","Delete Waypoint","Nearest Waypoint","Sort Waypoints by Distance","Waypoint Route"):return self.waypoint_action(name)
        if name=="Minecraft Version":return self.version_dialog()
        if name=="Emergency Stop":return self.engine.stop()
        if name=="Pause/Resume":return self.engine.toggle_pause()
        if name=="Release Held Inputs":return self.release_inputs()
        if name=="Focus Loss Stop":return self.write("Focus-loss handling follows the active input backend. Emergency Stop remains available regardless of focus.")
        if name=="Enchantment RNG Seed Cracker":return self.launch_enchantment_rng_cracker()
        if spec.top=="Seed Tools" and spec.submenu=="Slime" and not self.settings.seed:self.set_seed()
        fields=self.executor.input_fields(spec);params={}; guide=self._guide_for(spec)
        if fields:
            adjusted=[]
            for key,label,default,kind in fields:
                if key=="seed" and self.settings.seed:default=self.settings.seed
                adjusted.append((key,label,default,kind))
            dialog=ValuesDialog(guide.title,adjusted,self,guide.summary)
            if dialog.exec()!=QDialog.Accepted:return
            params=dialog.values()
        try:
            result=self.executor.execute(spec,params); body=self._format_result(result.data)
            self.write(guide.title+"\n"+body+(f"\n\nNote: {result.note}" if result.note else "")); self._set_detail_view(1)
        except Exception as exc:
            friendly=self._friendly_error(exc); box=QMessageBox(QMessageBox.Warning,guide.title,friendly,parent=self);box.setDetailedText(str(exc));box.exec();self.write(f"{guide.title} could not finish. {friendly}")

    def launch_enchantment_rng_cracker(self):
        status=enchantment_cracker_status()
        first_use=not bool(status.get("cached"))
        box=QMessageBox(self); box.setIcon(QMessageBox.Warning); box.setWindowTitle("Enchantment RNG Seed Cracker")
        box.setText("This recovers Minecraft gameplay/player RNG state, not the world seed.")
        details=("F3+ integrates Earthcomputer EnchantmentCracker v1.9. Its upstream release supports Minecraft Java 1.8 through 1.21.11. "
                 "F3+ does not claim this workflow is validated for 26.x. Use the native Java LCG recovery tools for compatible raw java.util.Random observations on other versions.\n\n")
        if first_use:
            details += "First use downloads the 149 KB upstream release from GitHub and verifies its pinned SHA-256 before extraction. Internet access is required once."
        else:
            details += "The verified community tool is already cached locally."
        box.setInformativeText(details)
        proceed=box.addButton("Open RNG Cracker",QMessageBox.AcceptRole); box.addButton("Cancel",QMessageBox.RejectRole); box.exec()
        if box.clickedButton()!=proceed:return
        try:
            launch_enchantment_cracker()
            self.write("Opened Enchantment RNG Seed Cracker. This workflow is separate from world-seed recovery.")
        except Exception as exc:
            friendly=self._friendly_error(exc)
            err=QMessageBox(QMessageBox.Warning,"Enchantment RNG Seed Cracker",friendly,parent=self);err.setDetailedText(str(exc));err.exec()

    def start_macro(self,name):
        if self.settings.safe_mode:
            QMessageBox.warning(self,"Safe Mode","Automation and macros are disabled while Safe Mode is active. Check your SMP rules before turning it off.")
            return
        fn=macro_runner(name)
        if not fn:self.write(f"{name} is a planning helper, not a direct automation preset.");return
        if not self.target and self.settings.auto_link_minecraft:self.auto_link_minecraft()
        cap=getattr(self.input,"capabilities",None); issue=focus_issue(name,cap,getattr(self.target,"minimized",False) if self.target else False)
        if not self.target and getattr(cap,"all_input_requires_focus",True):
            issue="Minecraft is not linked, so F3+ cannot verify which client will receive foreground input"
        if issue:
            return self._start_macro_with_focus_decision(name,fn,issue)
        if self.target and self.target.minimized is True and getattr(cap,"minimized",False):
            return self._minimized_warning(name,fn)
        self._run_macro_now(name,fn)

    def _start_macro_with_focus_decision(self,name,fn,issue):
        if self.settings.allow_focus_switch and self.target and getattr(self.focus_controller,"available",False):
            if self.settings.confirm_focus_switch:
                box=QMessageBox(self);box.setIcon(QMessageBox.Warning);box.setWindowTitle("Minecraft focus required")
                box.setText("This macro needs Minecraft in the foreground for part or all of the run.")
                box.setInformativeText(issue+".\n\nProceed and let F3+ switch focus, or cancel without sending input.")
                proceed=box.addButton("Proceed with focus switching",QMessageBox.AcceptRole);box.addButton("Cancel",QMessageBox.RejectRole);box.exec()
                if box.clickedButton()!=proceed:return
            self._focus_token=self.focus_controller.capture_current()
            if not self.focus_controller.focus(self.target):
                return self._manual_focus_start(name,fn,"F3+ could not switch focus automatically.")
            self._restore_focus_pending=self.settings.restore_previous_focus
            QTimer.singleShot(max(100,self.settings.focus_switch_delay_ms),lambda:self._run_macro_now(name,fn))
            return
        self._manual_focus_start(name,fn,issue)

    def _manual_focus_start(self,name,fn,issue):
        seconds=max(1,self.settings.manual_focus_delay_seconds)
        box=QMessageBox(self);box.setIcon(QMessageBox.Warning);box.setWindowTitle("Minecraft focus needed")
        box.setText("This desktop cannot guarantee targeted input for this macro.")
        box.setInformativeText(issue+f".\n\nProceed to start a {seconds}-second countdown, then focus Minecraft yourself. Or cancel now.")
        proceed=box.addButton("Proceed",QMessageBox.AcceptRole);box.addButton("Cancel",QMessageBox.RejectRole);box.exec()
        if box.clickedButton()!=proceed:return
        self.write(f"{name} starts in {seconds} seconds. Focus the Minecraft client now.")
        QTimer.singleShot(seconds*1000,lambda:self._run_macro_now(name,fn))

    def _minimized_warning(self,name,fn):
        box=QMessageBox(self);box.setIcon(QMessageBox.Warning);box.setWindowTitle("Minecraft is minimized")
        box.setText("The linked Minecraft window is minimized.")
        box.setInformativeText("This backend can send targeted input while minimized, but Minecraft/GLFW may ignore some events. You can try it as-is, restore/focus the client for a reliable run, or cancel.")
        run_min=box.addButton("Run minimized",QMessageBox.AcceptRole); focus=box.addButton("Restore & focus",QMessageBox.ActionRole);box.addButton("Cancel",QMessageBox.RejectRole);box.exec()
        if box.clickedButton()==run_min:self._run_macro_now(name,fn)
        elif box.clickedButton()==focus:self._start_macro_with_focus_decision(name,fn,"Minecraft is minimized")

    def _run_macro_now(self,name,fn):
        self.engine.start(name,fn);self.write(f"Started: {name}. Emergency Stop: {self.settings.stop_hotkey}")

    def toggle_favorite(self):
        spec=self.selected_spec()
        if not spec:return
        active=self.settings.toggle_favorite(spec.id);self.favorite_btn.setText("★ Favorited" if active else "☆ Favorite");self.refresh_tools(preserve_groups=True)

    # ---------- multiplayer Safe Mode ----------
    def _sync_safe_mode_button(self):
        if not hasattr(self,"safe_mode_btn"):return
        self.safe_mode_btn.blockSignals(True)
        self.safe_mode_btn.setChecked(bool(self.settings.safe_mode))
        self.safe_mode_btn.setText("Safe Mode: ON" if self.settings.safe_mode else "Safe Mode")
        self.safe_mode_btn.setToolTip((SAFE_MODE_SUMMARY+"\n\n"+SAFE_MODE_DISCLAIMER) if self.settings.safe_mode else "Enable a conservative strict-SMP feature filter.")
        self.safe_mode_btn.blockSignals(False)

    def toggle_safe_mode(self,checked):
        checked=bool(checked)
        if checked and not self.settings.safe_mode:
            box=QMessageBox(self); box.setIcon(QMessageBox.Warning); box.setWindowTitle("Enable Safe Mode?")
            box.setText("Safe Mode disables features commonly disputed on strict SMP servers.")
            box.setInformativeText(SAFE_MODE_SUMMARY+"\n\n"+SAFE_MODE_DISCLAIMER)
            enable=box.addButton("Enable Safe Mode",QMessageBox.AcceptRole); box.addButton("Cancel",QMessageBox.RejectRole); box.exec()
            if box.clickedButton()!=enable:
                self._sync_safe_mode_button(); return
            self.engine.stop(); self.settings.safe_mode=True; self.settings.save()
            self.statusBar().showMessage("Safe Mode enabled. Restricted tools remain visible but cannot run.")
        elif not checked and self.settings.safe_mode:
            self.settings.safe_mode=False; self.settings.save()
            self.statusBar().showMessage("Safe Mode disabled. Check your server rules before using automation or hidden-information tools.")
        self._sync_safe_mode_button(); self.refresh_tools(preserve_groups=True); self.selection_changed()

    def show_safe_mode_info(self):
        state="ON" if self.settings.safe_mode else "OFF"
        QMessageBox.information(self,"Safe Mode",f"Safe Mode is {state}.\n\n{SAFE_MODE_SUMMARY}\n\n{SAFE_MODE_DISCLAIMER}")

    # ---------- utility controls ----------
    def _human_key(self,key):
        text=str(key).replace("_"," ").strip(); replacements={"xp":"XP","x":"X","y":"Y","z":"Z","rng":"RNG","id":"ID","url":"URL","sha256":"SHA-256","backend":"Calculation source","backend error":"Fallback details","mc enum":"Cubiomes version code","source dir":"Source folder","build ok":"Setup successful","source available":"Bundled source available","automatic acquisition":"Automatic setup"}
        return " ".join(replacements.get(word.lower(),word.capitalize()) for word in text.split())

    def _format_scalar(self,value):
        if isinstance(value,bool):return "Yes" if value else "No"
        if value is None:return "Not available"
        if isinstance(value,float):return f"{value:.6f}".rstrip("0").rstrip(".")
        aliases={"bundled_cubiomes":"Bundled Cubiomes","cubiomes":"Cubiomes","local_uniform_fallback":"Built-in placement fallback","nether_bedrock_only":"Nether bedrock observations only","release-fallback":"Stable-release fallback"}
        return aliases.get(str(value),str(value))

    def _format_result(self,data,indent=0):
        prefix="  "*indent
        if isinstance(data,dict):
            if not data:return prefix+"No additional details."
            lines=[]
            for key,value in data.items():
                label=self._human_key(key)
                if isinstance(value,(dict,list,tuple)):lines += [prefix+label+":",self._format_result(value,indent+1)]
                else:lines.append(prefix+label+": "+self._format_scalar(value))
            return "\n".join(lines)
        if isinstance(data,(list,tuple)):
            if not data:return prefix+"None"
            lines=[]
            for i,value in enumerate(data,1):
                if isinstance(value,(dict,list,tuple)):lines += [prefix+f"{i}.",self._format_result(value,indent+1)]
                else:lines.append(prefix+f"{i}. {self._format_scalar(value)}")
            return "\n".join(lines)
        return prefix+self._format_scalar(data)

    def _friendly_error(self,exc):
        text=str(exc);low=text.lower()
        if isinstance(exc,PermissionError) or "permission" in low or "accessibility" in low:return "F3+ needs an operating-system permission for this action. Grant the requested input/accessibility permission, then try again."
        if isinstance(exc,FileNotFoundError) or "not found" in low or "does not exist" in low:return "F3+ cannot find a required file or Minecraft folder. Check the path and try again."
        if "cubiomes" in low:return "Cubiomes is not ready. Check Options > Components, then retry while online if F3+ needs its verified compiler fallback."
        if "bedrock" in low or "cracker" in low:return "Nether Bedrock Cracker is not ready. Open it again while online so F3+ can prepare the verified platform component, or install Rust/Cargo to build the bundled source."
        if "seed" in low and any(x in low for x in ("invalid","integer","literal")):return "That world seed is not valid. Enter a numeric Java Edition world seed and try again."
        return "Could not finish. Check the values below and try again. Technical details are available if you need them."

    def capture_position(self):
        try:
            p=self.capture.capture();self.current_position=p;self.update_position_labels();self.write(f"Captured {p.x:.3f}, {p.y:.3f}, {p.z:.3f} • chunk {p.chunk} • region {p.region}")
        except Exception as e:QMessageBox.warning(self,"Coordinate Capture",self._friendly_error(e)+"\n\n"+str(e))

    def update_position_labels(self):
        if not self.current_position:return
        p=self.current_position;self.pos_label.setText(f"Position: {p.x:.1f}, {p.y:.1f}, {p.z:.1f} • {self.dimension.currentText()}")

    def copy_sister(self):
        if not self.current_position:self.capture_position()
        if not self.current_position or self.dimension.currentText()=="End":return
        import pyperclip
        q=self.current_position.sister(self.dimension.currentText());text=f"{q.x:.3f} {q.y:.3f} {q.z:.3f}";pyperclip.copy(text);self.write("Copied sister coordinates: "+text)

    def save_sister_waypoint(self):
        if not self.current_position:self.capture_position()
        if not self.current_position or self.dimension.currentText()=="End":return
        q=self.current_position.sister(self.dimension.currentText());dest="Nether" if self.dimension.currentText()=="Overworld" else "Overworld";name=f"Sister {dest}";self.settings.waypoints[name]=[q.x,q.y,q.z];self.settings.save();self.write(f"Saved {name}: {q.x:.2f}, {q.y:.2f}, {q.z:.2f}")

    def waypoint_action(self,action):
        if action=="Create Waypoint":
            if not self.current_position:self.capture_position()
            p=self.current_position or Position(0,64,0);d=ValuesDialog("Create Waypoint",[("name","Name","Waypoint","text"),("x","X",p.x,"float"),("y","Y",p.y,"float"),("z","Z",p.z,"float")],self,"Save a named coordinate for routing and nearest-waypoint tools.")
            if d.exec()!=QDialog.Accepted:return
            v=d.values();name=v["name"].strip()
            if not name:return QMessageBox.warning(self,"Waypoint","Enter a name first.")
            self.settings.waypoints[name]=[v["x"],v["y"],v["z"]];self.settings.save();return self.write(f"Saved waypoint {name}.")
        names=sorted(self.settings.waypoints)
        if not names:return QMessageBox.information(self,"Waypoints","No waypoints are saved yet.")
        if action in ("Rename Waypoint","Delete Waypoint"):
            d=ValuesDialog(action,[("name","Waypoint",names,"choice")]+([("new","New name",names[0],"text")] if action=="Rename Waypoint" else []),self)
            if d.exec()!=QDialog.Accepted:return
            v=d.values();old=v["name"]
            if action=="Delete Waypoint":self.settings.waypoints.pop(old,None);self.settings.save();return self.write(f"Deleted waypoint {old}.")
            new=v["new"].strip()
            if not new:return QMessageBox.warning(self,"Waypoint","Enter a name first.")
            self.settings.waypoints[new]=self.settings.waypoints.pop(old);self.settings.save();return self.write(f"Renamed {old} to {new}.")
        if not self.current_position:self.capture_position()
        p=self.current_position or Position(0,64,0)
        from .navigation.routes import Point,greedy_route
        origin=Point(p.x,p.y,p.z,"Current");pts=[Point(float(v[0]),float(v[1]),float(v[2]),k) for k,v in self.settings.waypoints.items()];route=greedy_route(origin,pts);rows=[{"name":q.name,"x":q.x,"y":q.y,"z":q.z} for q in route["route"][1:]]
        if action=="Nearest Waypoint":rows=rows[:1]
        self.write(action+"\n"+self._format_result({"distance":route["distance"],"waypoints":rows}));self._set_detail_view(1)

    def set_dimension(self,value):self.settings.dimension=value;self.settings.save();self.update_position_labels()

    def set_seed(self):
        d=ValuesDialog("World Seed",[("seed","Java Edition world seed",self.settings.seed,"text")],self,"Save a known world seed for seed-aware tools. This does not perform seed recovery.")
        if d.exec()==QDialog.Accepted:
            self.settings.seed=d.values()["seed"].strip();self.settings.save();self.seed_label.setText("Seed set" if self.settings.seed else "Seed not set");self.write("World seed saved." if self.settings.seed else "World seed cleared.")

    def version_dialog(self):
        d=ValuesDialog("Minecraft Version",[("version","Version",self.settings.minecraft_version,"text")],self,"Set the version F3+ should use for version-aware calculations.")
        if d.exec()==QDialog.Accepted:
            self.settings.minecraft_version=d.values()["version"].strip();self.settings.save();self.executor.minecraft_version=self.settings.minecraft_version;clear_texture_cache();self._art_cache.clear();self.apply_theme();self.update_link_badges();self.write("Minecraft version: "+self.settings.minecraft_version)

    def options_dialog(self):
        before=(self.settings.input_mode,self.settings.minecraft_window_title,self.settings.theme)
        d=OptionsDialog(self.settings,self)
        if d.exec()!=QDialog.Accepted:return
        d.apply();self.executor.minecraft_version=self.settings.minecraft_version;self.dimension.setCurrentText(self.settings.dimension);self._guide_cache.clear();clear_texture_cache();self._art_cache.clear();self.apply_theme();self.refresh_tools();self.start_hotkeys();self._sync_safe_mode_button()
        after=(self.settings.input_mode,self.settings.minecraft_window_title,self.settings.theme)
        if before[:2]!=after[:2]:self.relink_minecraft()
        self.refresh_tools();self.write("Options saved.")

    def open_trade_browser(self,profession=None):
        d=TradeBrowser(self.settings.minecraft_version,self)
        if profession and profession.lower() in PROFESSIONS:d.prof.setCurrentText(profession.title())
        d.exec()

    def release_inputs(self):
        self.input.release_all();self.write("Released all held keyboard and mouse inputs.")

    def write(self,text):
        self.output.appendPlainText(str(text).rstrip()+"\n\n")

    def update_status(self,s):
        state="paused" if s.paused else ("running" if s.running else "stopped");self.statusBar().showMessage(f"{s.name}: {state} • {s.cycles} cycles")
        if not s.running and self._restore_focus_pending:
            token=self._focus_token;self._focus_token=None;self._restore_focus_pending=False
            if token is not None:QTimer.singleShot(120,lambda:self.focus_controller.restore(token))

    @staticmethod
    def _pynput_hotkey(value):
        special={"ctrl":"<ctrl>","alt":"<alt>","shift":"<shift>","space":"<space>","enter":"<enter>","tab":"<tab>","esc":"<esc>"}
        return "+".join(special.get(x.strip().lower(),x.strip().lower()) for x in value.split("+") if x.strip())

    def start_hotkeys(self):
        if keyboard is None:
            self.listener=None; return
        try:
            if self.listener:self.listener.stop()
        except Exception:pass
        try:
            mapping={}
            if self.settings.stop_hotkey.strip():
                mapping[self._pynput_hotkey(self.settings.stop_hotkey)] = self.engine.stop
            if self.settings.toggle_hotkey.strip():
                mapping[self._pynput_hotkey(self.settings.toggle_hotkey)] = self.engine.toggle_pause
            if getattr(self.settings, "coord_copy_hotkey", "").strip():
                mapping[self._pynput_hotkey(self.settings.coord_copy_hotkey)] = self.copy_sister
            self.listener=keyboard.GlobalHotKeys(mapping);self.listener.daemon=True;self.listener.start()
        except Exception:self.listener=None

    def show_getting_started(self):
        QMessageBox.information(self,"Getting Started",
            "1. Start Minecraft Java. F3+ links automatically when one client is open.\n"
            "2. Use the context deck for global search, dimension, world seed, and F3+C position capture.\n"
            "3. Home collects Favorites and Recent tools; the workspace rail opens the full task groups.\n"
            "4. Select a tool and read the Inspector guide before running it.\n"
            "5. Automation uses background delivery where the platform allows it. If focus is required, F3+ explains why before switching.\n"
            f"6. Emergency Stop is {self.settings.stop_hotkey} and releases held input immediately.\n"
            f"7. Copy Sister Coordinates is {self.settings.coord_copy_hotkey}.\n\n"
            "Appearance presets, icon source options, and custom colors are available under Options > Appearance.")

    def show_about(self):
        QMessageBox.about(self,"About F3+",f"F3+ {__version__} by LucidOcelot\n\n{TARGET_MINECRAFT}\n\nAll in one offline companion app for Minecraft. Built around community tools and based on Minescript/M.A.R.T by Lucid. F3+ aims to bring common and niche technical Minecraft tools to the greater community in a convenient multi-platform solution.\n\nSee LICENSE.md, THIRD_PARTY.md, COMMUNITY_CREDITS.md, and FEATURES.md for licensing, attribution, and the full tool manual.")

    def closeEvent(self,event):
        self.engine.stop()
        try:
            if self.listener:self.listener.stop()
        except Exception:pass
        event.accept()


def run():
    app=QApplication(sys.argv);app.setApplicationName("F3+");app.setOrganizationName("LucidOcelot")
    w=F3Plus();w.show();sys.exit(app.exec())
