from __future__ import annotations

"""Task-first F3+ desktop shell."""

import html
import sys

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QFontMetrics, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QComboBox, QDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListView, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSplitter, QStackedWidget, QStyle, QStyledItemDelegate, QTextBrowser, QVBoxLayout,
    QWidget,
)

from .app import F3Plus as _BaseF3Plus
from .automation_workbench import MacroStudioDialog
from .launch_contract import launch_kind
from .minecraft_art25 import semantic_texture_bytes
from .pixel_art import icon_pixmap
from .recipe_workbench import RecipeExplorerDialog
from .safe_mode import restriction_reason as safe_mode_restriction
from .state_workbenches import (
    DiagnosticsDialog, ProfilesControlsDialog, ResultHistoryDialog, SafetySettingsDialog,
    WorldProfilesDialog,
)
from .tool_guides import (
    NAV_SECTIONS, group_order, make_guide, nav_section, search_text, specs_for_section,
    tool_art_key, workspace_group,
)
from .tool_registry import BY_ID, ToolMode, ToolSpec, modes_for
from .ui_dialogs import wrapped_tooltip
from .ui_theme import palette, stylesheet
from .ux25_theme import desktop_stylesheet
from .workbenches import (
    LootWorkbenchDialog, MechanicsLabDialog, OperationDialog, RngEnchantingDialog,
    VillagerExplorerDialog,
)


NAV_ART = {
    "Home": "home",
    "Play & Travel": "travel",
    "Explore Worlds": "map",
    "Plan & Build": "technical",
    "Mechanics & Trading": "enchant",
    "App & Safety": "utilities",
}


class WorkbenchCardDelegate(QStyledItemDelegate):
    """Paint responsive task cards without allocating a widget per workbench."""

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner

    def sizeHint(self, option, index):
        return QSize(286, 158)

    def paint(self, painter: QPainter, option, index):
        p = palette(self.owner.settings.theme, self.owner.settings.custom_palette)
        rect = option.rect.adjusted(5, 5, -5, -5)
        selected = bool(option.state & QStyle.State_Selected)
        hovered = bool(option.state & QStyle.State_MouseOver)
        bg = QColor(p["surface3"] if selected else p["surface2"])
        border = QColor(p["glow"] if selected or hovered else p["border"])

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(border, 1.4 if selected else 1.0))
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(QRectF(rect), 10, 10)

        icon = index.data(Qt.DecorationRole)
        if isinstance(icon, QIcon):
            painter.drawPixmap(rect.left() + 14, rect.top() + 14, icon.pixmap(QSize(42, 42)))

        title = str(index.data(Qt.DisplayRole) or "")
        summary = str(index.data(Qt.UserRole + 1) or "")
        meta = str(index.data(Qt.UserRole + 2) or "")
        locked = str(index.data(Qt.UserRole + 3) or "")
        count = str(index.data(Qt.UserRole + 4) or "")

        title_font = QFont(painter.font()); title_font.setPointSizeF(11.0); title_font.setBold(True)
        painter.setFont(title_font); painter.setPen(QColor(p["text"]))
        painter.drawText(QRectF(rect.left() + 66, rect.top() + 12, rect.width() - 80, 25), Qt.AlignLeft | Qt.AlignVCenter, title)

        meta_font = QFont(painter.font()); meta_font.setPointSizeF(8.0); meta_font.setBold(False)
        painter.setFont(meta_font); painter.setPen(QColor(p["muted"]))
        painter.drawText(QRectF(rect.left() + 66, rect.top() + 36, rect.width() - 80, 18), Qt.AlignLeft | Qt.AlignVCenter, meta)

        body_font = QFont(painter.font()); body_font.setPointSizeF(9.0)
        painter.setFont(body_font); painter.setPen(QColor(p["text"]))
        fm = QFontMetrics(body_font)
        words = summary.split(); lines, current = [], ""; max_width = rect.width() - 28
        for word in words:
            proposed = (current + " " + word).strip()
            if fm.horizontalAdvance(proposed) <= max_width:
                current = proposed
            else:
                if current: lines.append(current)
                current = word
            if len(lines) >= 2: break
        if current and len(lines) < 3: lines.append(current)
        text = "\n".join(lines[:3])
        if fm.horizontalAdvance(summary) > max_width * 3 and text:
            text = text.rstrip(".") + "…"
        painter.drawText(QRectF(rect.left() + 14, rect.top() + 63, max_width, 57), Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, text)

        painter.setPen(QColor(p["danger"] if locked else p["muted"]))
        painter.drawText(QRectF(rect.left() + 14, rect.bottom() - 27, rect.width() - 28, 18), Qt.AlignLeft | Qt.AlignVCenter, "SAFE MODE" if locked else count)
        painter.restore()


class CommandPalette(QDialog):
    """Searchable launcher for workbenches and individual operations."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setObjectName("CommandPalette25")
        self.setWindowTitle("F3+ Command Palette")
        self.resize(720, 560)
        root = QVBoxLayout(self); root.setContentsMargins(14, 14, 14, 14); root.setSpacing(8)
        title = QLabel("Open a workbench or operation"); title.setObjectName("SectionTitle25"); root.addWidget(title)
        note = QLabel("Search by task, mechanic, workbench, or operation name. Enter opens the selected result.")
        note.setWordWrap(True); note.setObjectName("Muted"); root.addWidget(note)
        self.query = QLineEdit(); self.query.setObjectName("GlobalSearch25"); self.query.setPlaceholderText("Try: ore distribution, anvil, portal, villager, slime…"); self.query.setClearButtonEnabled(True); root.addWidget(self.query)
        self.results = QListWidget(); self.results.setObjectName("PaletteList25"); root.addWidget(self.results, 1)
        hint = QLabel("Enter — open   •   Esc — close"); hint.setObjectName("Muted"); root.addWidget(hint)
        self.query.textChanged.connect(self.refresh); self.results.itemDoubleClicked.connect(lambda *_: self.open_current()); self.query.returnPressed.connect(self.open_current)
        self.refresh(); self.query.setFocus()

    def refresh(self):
        q = self.query.text().strip().lower(); self.results.clear()
        for tool in BY_ID.values():
            guide = self.owner._guide_for(tool)
            if not q or q in search_text(tool, guide):
                item = QListWidgetItem(QIcon(self.owner._art(tool_art_key(tool), 24)), tool.name)
                item.setData(Qt.UserRole, (tool.id, ""))
                item.setToolTip(f"{nav_section(tool)} • {workspace_group(tool)}")
                self.results.addItem(item)
            for mode in modes_for(tool):
                hay = f"{tool.name} {mode.name} {nav_section(tool)} {workspace_group(tool)}".lower()
                if q and q not in hay:
                    continue
                item = QListWidgetItem(QIcon(self.owner._art(tool_art_key(tool), 22)), f"{tool.name}  →  {mode.name}")
                item.setData(Qt.UserRole, (tool.id, mode.key))
                item.setToolTip(f"Open {mode.name} in {tool.name}")
                self.results.addItem(item)
        if self.results.count(): self.results.setCurrentRow(0)

    def open_current(self):
        item = self.results.currentItem()
        if item is None: return
        tool_id, mode_key = item.data(Qt.UserRole); tool = BY_ID[tool_id]
        mode = next((row for row in modes_for(tool) if row.key == mode_key), None) if mode_key else None
        self.accept(); self.owner._select_tool(tool_id); self.owner.launch_tool(tool, mode)


class F3PlusDesktop(_BaseF3Plus):
    """Task-first desktop shell over the calculation and automation services."""

    def build_ui(self):
        root = QWidget(); root.setObjectName("AppRoot"); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        topbar = QFrame(); topbar.setObjectName("TopBar"); top = QHBoxLayout(topbar); top.setContentsMargins(14, 9, 14, 9); top.setSpacing(8)
        self.brand = QLabel(); self.brand.setFixedSize(42, 42); top.addWidget(self.brand)
        names = QVBoxLayout(); app_name = QLabel("F3+"); app_name.setObjectName("AppTitle"); names.addWidget(app_name); subtitle = QLabel("Technical Minecraft workstation"); subtitle.setObjectName("AppSubtitle"); names.addWidget(subtitle); top.addLayout(names)
        top.addSpacing(10)
        self.link_badge = QLabel("Minecraft not linked"); self.link_badge.setObjectName("StatusPillWarn"); self.link_badge.setToolTip("Minecraft Java client used by live capture and automation."); top.addWidget(self.link_badge)
        self.backend_badge = QLabel("Foreground"); self.backend_badge.hide(); top.addWidget(self.backend_badge)
        self.background_badge = QLabel("BG —"); self.background_badge.hide(); top.addWidget(self.background_badge)
        self.camera_badge = QLabel("Camera —"); self.camera_badge.hide(); top.addWidget(self.camera_badge)
        top.addStretch()
        relink = QPushButton("Link Minecraft"); relink.setObjectName("QuietAction25"); relink.clicked.connect(self.relink_minecraft); top.addWidget(relink)
        self.safe_btn = QPushButton("Safe Mode"); self.safe_btn.setCheckable(True); self.safe_btn.setChecked(self.settings.safe_mode); self.safe_btn.setObjectName("SafeModeButton"); self.safe_btn.clicked.connect(self.toggle_safe_mode); top.addWidget(self.safe_btn)
        options = QPushButton("Options"); options.setObjectName("QuietAction25"); options.clicked.connect(self.options_dialog); top.addWidget(options)
        self.pause_btn = QPushButton("Pause"); self.pause_btn.setObjectName("QuietAction25"); self.pause_btn.clicked.connect(self.engine.toggle_pause); top.addWidget(self.pause_btn)
        self.stop_btn = QPushButton("STOP AUTOMATION"); self.stop_btn.setObjectName("DangerButton"); self.stop_btn.clicked.connect(self.engine.stop); top.addWidget(self.stop_btn)
        self._sync_automation_chrome(False)
        outer.addWidget(topbar)

        status = QFrame(); status.setObjectName("StatusBar25"); sr = QHBoxLayout(status); sr.setContentsMargins(14, 7, 14, 7); sr.setSpacing(8)
        self.search = QLineEdit(); self.search.setObjectName("GlobalSearch25"); self.search.setPlaceholderText("Search tasks, workbenches, or operations…"); self.search.setClearButtonEnabled(True); sr.addWidget(self.search, 1)
        palette_btn = QPushButton("Ctrl+K  Search"); palette_btn.setObjectName("Command25"); palette_btn.clicked.connect(self.command_palette); sr.addWidget(palette_btn)
        self.dimension = QComboBox(); self.dimension.addItems(["Overworld", "Nether", "End"]); self.dimension.setCurrentText(self.settings.dimension); self.dimension.currentTextChanged.connect(self.set_dimension); self.dimension.setToolTip("Dimension used by coordinate-aware tools unless a workbench explicitly overrides it."); sr.addWidget(self.dimension)
        self.version_badge = QLabel(self.settings.minecraft_version); self.version_badge.setObjectName("StatusPill"); self.version_badge.setToolTip("Minecraft Java version selected for calculations and local data lookup."); sr.addWidget(self.version_badge)
        self.seed_label = QLabel("Seed set" if self.settings.seed else "Seed not set"); self.seed_label.setObjectName("StatusPillGood" if self.settings.seed else "StatusPillWarn"); sr.addWidget(self.seed_label)
        seed = QPushButton("World Seed"); seed.setObjectName("QuietAction25"); seed.clicked.connect(self.set_seed); sr.addWidget(seed)
        self.pos_label = QLabel("Position not captured"); self.pos_label.setObjectName("StatusPill"); sr.addWidget(self.pos_label)
        capture = QPushButton("Capture F3+C"); capture.setObjectName("QuietAction25"); capture.clicked.connect(self.capture_position); sr.addWidget(capture)
        outer.addWidget(status)

        work = QSplitter(Qt.Horizontal); work.setChildrenCollapsible(False); outer.addWidget(work, 1); self.work_splitter = work

        rail = QFrame(); rail.setObjectName("NavRail25"); rl = QVBoxLayout(rail); rl.setContentsMargins(10, 12, 10, 12); rl.setSpacing(7)
        rk = QLabel("TASKS"); rk.setObjectName("Eyebrow25"); rl.addWidget(rk)
        self.nav = QListWidget(); self.nav.setObjectName("NavList25"); self.nav.setIconSize(QSize(22, 22)); self.nav.setSpacing(1); rl.addWidget(self.nav, 1)
        for label, _ in NAV_SECTIONS:
            item = QListWidgetItem(label); item.setData(Qt.UserRole, label); self.nav.addItem(item)
        rail_hint = QLabel("Ctrl+K opens any workbench or operation by name."); rail_hint.setWordWrap(True); rail_hint.setObjectName("Muted"); rl.addWidget(rail_hint); work.addWidget(rail)

        canvas = QFrame(); canvas.setObjectName("WorkbenchCanvas"); cv = QVBoxLayout(canvas); cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(10)
        head = QHBoxLayout(); titles = QVBoxLayout(); self.browser_title = QLabel("Home"); self.browser_title.setObjectName("HeroTitle25"); titles.addWidget(self.browser_title); self.browser_subtitle = QLabel("Choose what you want to do. Related operations are grouped into one workbench."); self.browser_subtitle.setWordWrap(True); self.browser_subtitle.setObjectName("Muted"); titles.addWidget(self.browser_subtitle); head.addLayout(titles, 1)
        filters = QVBoxLayout(); fk = QLabel("FILTER"); fk.setObjectName("Eyebrow25"); filters.addWidget(fk); self.group_filter = QComboBox(); self.group_filter.setObjectName("GroupFilter25"); self.group_filter.addItem("All groups"); filters.addWidget(self.group_filter); head.addLayout(filters); cv.addLayout(head)
        self.tool_list = QListWidget(); self.tool_list.setObjectName("WorkbenchGrid"); self.tool_list.setViewMode(QListView.IconMode); self.tool_list.setResizeMode(QListView.Adjust); self.tool_list.setMovement(QListView.Static); self.tool_list.setWrapping(True); self.tool_list.setUniformItemSizes(True); self.tool_list.setSpacing(8); self.tool_list.setSelectionMode(QListView.SingleSelection); self.tool_list.setMouseTracking(True); self.tool_list.setItemDelegate(WorkbenchCardDelegate(self, self.tool_list)); cv.addWidget(self.tool_list, 1)
        footer = QHBoxLayout(); self.result_count = QLabel(); self.result_count.setObjectName("Muted"); footer.addWidget(self.result_count); footer.addStretch()
        self.details_btn = QPushButton("Details"); self.details_btn.setObjectName("QuietAction25"); self.details_btn.setCheckable(True); self.details_btn.clicked.connect(self._set_details_visible); footer.addWidget(self.details_btn)
        self.quick_open_btn = QPushButton("Open Selected"); self.quick_open_btn.setObjectName("PrimaryAction25"); self.quick_open_btn.setEnabled(False); self.quick_open_btn.clicked.connect(self.run_selected); footer.addWidget(self.quick_open_btn)
        cv.addLayout(footer); work.addWidget(canvas)

        inspector = QFrame(); inspector.setObjectName("Inspector25"); self.inspector = inspector
        iv = QVBoxLayout(inspector); iv.setContentsMargins(14, 14, 14, 14); iv.setSpacing(10)
        ik = QLabel("SELECTED"); ik.setObjectName("Eyebrow25"); iv.addWidget(ik)
        hero = QHBoxLayout(); self.feature_icon = QLabel(); self.feature_icon.setFixedSize(48, 48); self.feature_icon.setAlignment(Qt.AlignCenter); hero.addWidget(self.feature_icon)
        hero_names = QVBoxLayout(); self.feature_kicker = QLabel("SELECT A WORKBENCH"); self.feature_kicker.setObjectName("Eyebrow25"); hero_names.addWidget(self.feature_kicker); self.feature_title = QLabel("Choose a workbench"); self.feature_title.setObjectName("SectionTitle25"); self.feature_title.setWordWrap(True); hero_names.addWidget(self.feature_title); self.feature_path = QLabel(); self.feature_path.setWordWrap(True); self.feature_path.setObjectName("Muted"); hero_names.addWidget(self.feature_path); hero.addLayout(hero_names, 1); iv.addLayout(hero)
        self.inspector_summary = QLabel("Select a card to see its operations."); self.inspector_summary.setWordWrap(True); self.inspector_summary.setObjectName("Muted"); iv.addWidget(self.inspector_summary)
        action_row = QHBoxLayout(); self.run_btn = QPushButton("Open Workbench"); self.run_btn.setObjectName("PrimaryAction25"); self.run_btn.clicked.connect(self.run_selected); self.run_btn.setEnabled(False); action_row.addWidget(self.run_btn, 1); self.favorite_btn = QPushButton("☆"); self.favorite_btn.setObjectName("QuietAction25"); self.favorite_btn.setToolTip("Favorite this workbench"); self.favorite_btn.clicked.connect(self.toggle_favorite); action_row.addWidget(self.favorite_btn); iv.addLayout(action_row)
        secondary = QHBoxLayout(); self.map_btn = QPushButton("Open Map"); self.map_btn.setObjectName("QuietAction25"); self.map_btn.clicked.connect(self.open_result_map); self.map_btn.setEnabled(False); secondary.addWidget(self.map_btn); self.guide_btn = QPushButton("Operations"); self.guide_btn.setObjectName("QuietAction25"); self.guide_btn.setCheckable(True); self.guide_btn.setChecked(True); secondary.addWidget(self.guide_btn); self.results_btn = QPushButton("Results"); self.results_btn.setObjectName("QuietAction25"); self.results_btn.setCheckable(True); secondary.addWidget(self.results_btn); secondary.addStretch(); iv.addLayout(secondary)
        group = QButtonGroup(self); group.setExclusive(True); group.addButton(self.guide_btn); group.addButton(self.results_btn)
        self.stack = QStackedWidget(); self.guide = QTextBrowser(); self.guide.setObjectName("InspectorGuide25"); self.output = QTextBrowser(); self.output.setObjectName("InspectorResult25"); self.stack.addWidget(self.guide); self.stack.addWidget(self.output); iv.addWidget(self.stack, 1)
        self.guide_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0)); self.results_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1)); work.addWidget(inspector)
        work.setStretchFactor(1, 1); self._set_details_visible(False)

        self.nav.currentItemChanged.connect(lambda *_: self.refresh_tools())
        self.search.textChanged.connect(lambda *_: self.refresh_tools())
        self.group_filter.currentTextChanged.connect(lambda *_: self.refresh_tools(True))
        self.tool_list.itemSelectionChanged.connect(self.selection_changed)
        self.tool_list.itemDoubleClicked.connect(lambda *_: self.run_selected())
        self.nav.setCurrentRow(0); self._sync_safe(); self._refresh_art()

    def build_menu(self):
        self.menuBar().clear()
        f3 = self.menuBar().addMenu("F3+")
        self._menu_action(f3, "Search / Command Palette", self.command_palette, "Ctrl+K")
        self._menu_action(f3, "Result History", lambda: ResultHistoryDialog(self).exec())
        f3.addSeparator(); self._menu_action(f3, "Exit", self.close)

        minecraft = self.menuBar().addMenu("Minecraft")
        self._menu_action(minecraft, "Link / Relink Client", self.relink_minecraft)
        self._menu_action(minecraft, "Connection Status", self.show_connection_status)
        minecraft.addSeparator()
        self._menu_action(minecraft, "World Profiles", lambda: WorldProfilesDialog(self).exec())
        self._menu_action(minecraft, "Set World Seed", self.set_seed)
        self._menu_action(minecraft, "Capture F3+C Position", self.capture_position)

        for section, _ in NAV_SECTIONS:
            if section == "Home":
                continue
            menu = self.menuBar().addMenu(section)
            submenus = {}
            for tool in specs_for_section(section):
                group_name = workspace_group(tool)
                submenu = submenus.get(group_name)
                if submenu is None:
                    submenu = menu.addMenu(group_name); submenus[group_name] = submenu
                self._menu_action(submenu, tool.name, lambda _checked=False, tool_id=tool.id: self._open_menu_tool(tool_id))
            if section == "App & Safety":
                menu.addSeparator(); self._menu_action(menu, "Options", self.options_dialog)

        help_menu = self.menuBar().addMenu("Help")
        self._menu_action(help_menu, "Getting Started", self.show_getting_started)
        self._menu_action(help_menu, "About F3+", self.show_about)

    def _menu_action(self, menu, label: str, callback, shortcut: str = ""):
        action = QAction(label, self); action.triggered.connect(callback)
        if shortcut: action.setShortcut(shortcut)
        menu.addAction(action); return action

    def _open_menu_tool(self, tool_id: str):
        tool = BY_ID[tool_id]; self._select_tool(tool_id); self.launch_tool(tool, None)

    def show_getting_started(self):
        QMessageBox.information(
            self,
            "Getting Started",
            "Choose a task from the left, or press Ctrl+K and type what you want to do.\n\n"
            "World tools can use a seed or a local Java save. Capture F3+C when a calculation should start from your current position.\n\n"
            "Automation tools require a linked Minecraft client. Configure the routine, start it, and use Stop Automation whenever you need to release managed input.",
        )

    def _set_details_visible(self, visible: bool):
        visible = bool(visible)
        if not hasattr(self, "inspector"): return
        self.inspector.setVisible(visible)
        if hasattr(self, "details_btn"):
            self.details_btn.blockSignals(True); self.details_btn.setChecked(visible); self.details_btn.setText("Hide Details" if visible else "Details"); self.details_btn.blockSignals(False)
        if hasattr(self, "work_splitter"):
            self.work_splitter.setSizes([185, 885, 390] if visible else [185, 1275, 0])

    def _show_result(self, spec, result):
        self._set_details_visible(True)
        super()._show_result(spec, result)

    def _sync_automation_chrome(self, active: bool):
        if hasattr(self, "pause_btn"): self.pause_btn.setVisible(bool(active))
        if hasattr(self, "stop_btn"): self.stop_btn.setVisible(bool(active))

    def update_status(self, status):
        super().update_status(status)
        active = bool(getattr(status, "running", False) or getattr(status, "paused", False))
        self._sync_automation_chrome(active)
        if hasattr(self, "pause_btn"):
            self.pause_btn.setText("Resume" if getattr(status, "paused", False) else "Pause")

    def apply_theme(self):
        app = QApplication.instance()
        app.setStyleSheet(stylesheet(self.settings.theme, self.settings.custom_palette) + desktop_stylesheet(self.settings.theme, self.settings.custom_palette))
        self._art_cache.clear(); self._refresh_art(); self.refresh_tools(True)

    def _art(self, key, size=30):
        p = palette(self.settings.theme, self.settings.custom_palette)
        cache = (key, size, self.settings.theme, self.settings.minecraft_version, tuple(sorted(p.items())))
        if cache in self._art_cache: return self._art_cache[cache]
        pix = QPixmap()
        use_minecraft = self.settings.theme in {"chorus", "light", "minecraft"} or (self.settings.theme == "custom" and getattr(self.settings, "custom_theme_use_minecraft_assets", False))
        if use_minecraft:
            raw, _member, _version = semantic_texture_bytes(str(key), self.settings.minecraft_version)
            if raw and pix.loadFromData(raw): pix = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation)
        if pix.isNull(): pix = icon_pixmap(key, p, size)
        self._art_cache[cache] = pix; return pix

    def _refresh_art(self):
        if not hasattr(self, "brand"): return
        logo = self._art("app", 38); self.brand.setPixmap(logo); self.setWindowIcon(QIcon(logo))
        for i in range(self.nav.count()):
            item = self.nav.item(i); item.setIcon(QIcon(self._art(NAV_ART.get(item.data(Qt.UserRole), "home"), 22)))

    def refresh_tools(self, preserve=False):
        if not hasattr(self, "tool_list"): return
        section = self.current_section(); query = self.search.text().strip().lower()
        candidates = list(BY_ID.values()) if query else specs_for_section(section, self.settings.favorites, self.settings.recent_tools)
        self.browser_title.setText("Search results" if query else ("Home" if section == "Home" else section))
        self.browser_subtitle.setText(
            f"Matches for “{self.search.text().strip()}”. Open a workbench or use Ctrl+K to jump directly to an operation." if query
            else "Choose what you want to do. Related operations are grouped into one workbench."
        )
        groups = {workspace_group(spec) for spec in candidates}
        old = self.group_filter.currentText(); self.group_filter.blockSignals(True); self.group_filter.clear(); self.group_filter.addItem("All groups")
        if query:
            for label, _ in NAV_SECTIONS:
                if label != "Home" and any(nav_section(spec) == label for spec in candidates): self.group_filter.addItem(label)
        else:
            for name in group_order(section, groups): self.group_filter.addItem(name)
        if preserve:
            idx = self.group_filter.findText(old)
            if idx >= 0: self.group_filter.setCurrentIndex(idx)
        self.group_filter.blockSignals(False); chosen = self.group_filter.currentText(); rows = []
        for spec in candidates:
            guide = self._guide_for(spec)
            if query and query not in search_text(spec, guide): continue
            if chosen != "All groups":
                if query and nav_section(spec) != chosen: continue
                if not query and workspace_group(spec) != chosen: continue
            rows.append((spec, guide))
        rows.sort(key=lambda pair: (nav_section(pair[0]), workspace_group(pair[0]), pair[0].name) if query else (workspace_group(pair[0]), pair[0].name))
        self.tool_list.clear()
        for spec, guide in rows:
            reason = safe_mode_restriction(spec) if self.settings.safe_mode else None
            operations = [mode.name for mode in modes_for(spec)]
            item = QListWidgetItem(QIcon(self._art(tool_art_key(spec), 42)), spec.name)
            item.setData(Qt.UserRole, spec.id); item.setData(Qt.UserRole + 1, guide.summary); item.setData(Qt.UserRole + 2, f"{nav_section(spec)} • {workspace_group(spec)}"); item.setData(Qt.UserRole + 3, reason or ""); item.setData(Qt.UserRole + 4, f"{len(operations)} operation{'s' if len(operations) != 1 else ''}")
            tooltip = f"Contains: {', '.join(operations[:6])}" + (f", +{len(operations) - 6} more" if len(operations) > 6 else "")
            if reason: tooltip = reason + "\n\n" + tooltip
            item.setSizeHint(QSize(286, 158)); item.setToolTip(wrapped_tooltip(tooltip)); self.tool_list.addItem(item)
        self.result_count.setText(f"{len(rows)} workbench{'es' if len(rows) != 1 else ''}")
        if self._selected_id:
            for i in range(self.tool_list.count()):
                if self.tool_list.item(i).data(Qt.UserRole) == self._selected_id: self.tool_list.setCurrentRow(i); break
        if self.tool_list.currentRow() < 0 and self.tool_list.count(): self.tool_list.setCurrentRow(0)
        if not self.tool_list.count():
            self.run_btn.setEnabled(False); self.quick_open_btn.setEnabled(False); self.feature_title.setText("No matching workbench"); self.inspector_summary.setText("Try a broader task or mechanic name.")

    def selection_changed(self):
        spec = self.selected_spec()
        if not spec:
            self.run_btn.setEnabled(False); self.quick_open_btn.setEnabled(False); return
        self._selected_id = spec.id; guide = self._guide_for(spec); reason = safe_mode_restriction(spec) if self.settings.safe_mode else None
        self.feature_icon.setPixmap(self._art(tool_art_key(spec), 44)); self.feature_kicker.setText(nav_section(spec).upper()); self.feature_title.setText(spec.name); self.feature_path.setText(f"{workspace_group(spec)} • {len(modes_for(spec))} operations"); self.inspector_summary.setText(guide.summary)
        self.favorite_btn.setText("★" if spec.id in self.settings.favorites else "☆"); self.favorite_btn.setToolTip("Remove from favorites" if spec.id in self.settings.favorites else "Add to favorites")
        enabled = reason is None
        self.run_btn.setEnabled(enabled); self.run_btn.setText("Safe Mode Locked" if reason else "Open Workbench")
        self.quick_open_btn.setEnabled(enabled); self.quick_open_btn.setText("Safe Mode Locked" if reason else "Open Selected")
        operations = [mode.name for mode in modes_for(spec)]; preview = operations[:12]; more = len(operations) - len(preview)
        p = palette(self.settings.theme, self.settings.custom_palette); esc = html.escape
        locked = f"<div style='border-left:3px solid {p['warning']};padding:7px 9px;background:{p['surface2']};'><b>Safe Mode</b><br>{esc(reason)}</div>" if reason else ""
        op_html = "<br>".join("• " + esc(name) for name in preview) + (f"<br><span style='color:{p['muted']}'>+ {more} more</span>" if more > 0 else "")
        self.guide.setHtml(f"<div style='color:{p['text']};line-height:1.35'>{locked}<h3>Operations</h3><p>{op_html}</p></div>")
        self.stack.setCurrentIndex(0); self.guide_btn.setChecked(True)

    def command_palette(self):
        CommandPalette(self).exec()

    def run_selected(self):
        spec = self.selected_spec()
        if spec is not None: self.launch_tool(spec, None)

    def launch_tool(self, spec: ToolSpec, mode: ToolMode | None = None):
        reason = safe_mode_restriction(spec) if self.settings.safe_mode else None
        if reason:
            QMessageBox.warning(self, "Safe Mode", reason); return
        self.settings.remember_tool(mode.key if mode is not None and mode.legacy is not None else spec.id)
        kind = launch_kind(spec.id)
        if kind == "macro_studio": MacroStudioDialog(self).exec(); return
        if kind == "world_profiles": WorldProfilesDialog(self).exec(); return
        if kind == "recipes": RecipeExplorerDialog(self).exec(); return
        if kind == "rng_enchanting": RngEnchantingDialog(self, self.executor, spec).exec(); return
        if kind == "loot": LootWorkbenchDialog(self, mode.name if mode is not None else "Loot Table Simulator").exec(); return
        if kind == "mechanics": MechanicsLabDialog(self).exec(); return
        if kind == "villagers":
            profession = None
            if mode is not None and mode.legacy is not None and mode.legacy.submenu == "Professions": profession = mode.name.lower()
            VillagerExplorerDialog(self, profession=profession, mode=mode.name if mode is not None else "Trade Browser").exec(); return
        if kind == "profiles_controls": ProfilesControlsDialog(self).exec(); return
        if kind == "safety": SafetySettingsDialog(self).exec(); return
        if kind == "result_history": ResultHistoryDialog(self).exec(); return
        if kind == "diagnostics": DiagnosticsDialog(self).exec(); return

        preferred = mode.key if mode is not None else self._preferred_mode(spec)
        dialog = OperationDialog(spec, self.executor, self.settings, self, preferred)
        if dialog.exec() == QDialog.Accepted and dialog.mode is not None:
            self.run_mode(dialog.mode, dialog.values())


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("F3+"); app.setOrganizationName("LucidOcelot")
    window = F3PlusDesktop(); window.show(); return app.exec()


F3Plus = F3PlusDesktop
