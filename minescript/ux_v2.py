from __future__ import annotations

"""F3+ 2.x shared interaction layer.

This module keeps the catalog/algorithms independent from Qt while giving every tool
one visual language for configuration, warnings, version context, and results.
"""

import html
from typing import Any


def install() -> None:
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
        QFileDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QScrollArea, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
        QWidget,
    )

    from .app import F3Plus, OptionsDialog, ValuesDialog
    from .safe_mode import restriction_reason as safe_mode_restriction
    from .tool_guides import nav_section, workspace_group
    from .version_context import resolve as resolve_version_context
    from .villager_explorer import VillagerExplorer

    if getattr(F3Plus, "_v2_ux_installed", False):
        return

    OptionsDialog.THEMES = {
        "Chorus": "chorus",
        "Light": "light",
        "Cyber": "cyberpunk",
        "Vanilla": "minecraft",
        "Aether": "aether",
        "Foundry": "foundry",
        "Custom": "custom",
    }

    original_options_init = OptionsDialog.__init__

    def options_init(self, settings, parent=None):
        original_options_init(self, settings, parent)
        try:
            self.theme_note.setText(
                "Chorus is the default. Light is a conventional bright interface. Cyber keeps the existing high-contrast neon layout. "
                "Vanilla uses local Minecraft textures where available. Aether is an airy cartographic theme; Foundry is a dense industrial theme. "
                "Custom exposes the full palette and can optionally use recovered Minecraft artwork."
            )
        except Exception:
            pass

    OptionsDialog.__init__ = options_init

    def values_init(self, title, fields, parent=None, subtitle=""):
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        self.setObjectName("ToolConfigDialog")
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        self.resize(660, min(760, max(360, 190 + len(fields) * 58)))
        self.setMinimumWidth(580)
        self.inputs = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 14)
        outer.setSpacing(11)
        kicker = QLabel("CONFIGURE TOOL")
        kicker.setObjectName("DeckLabel")
        outer.addWidget(kicker)
        heading = QLabel(title)
        heading.setObjectName("DetailTitle")
        heading.setWordWrap(True)
        outer.addWidget(heading)
        if subtitle:
            note = QLabel(subtitle)
            note.setObjectName("Muted")
            note.setWordWrap(True)
            outer.addWidget(note)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        card = QFrame()
        card.setObjectName("ToolConfigCard")
        form = QFormLayout(card)
        form.setContentsMargins(14, 14, 14, 14)
        form.setHorizontalSpacing(22)
        form.setVerticalSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        for key, label, default, kind in fields:
            if kind == "int":
                widget = QSpinBox()
                widget.setRange(-2147483647, 2147483647)
                widget.setValue(int(default))
            elif kind == "float":
                widget = QDoubleSpinBox()
                widget.setDecimals(5)
                widget.setRange(-1e12, 1e12)
                widget.setValue(float(default))
            elif kind == "bool":
                widget = QCheckBox("Enabled")
                widget.setChecked(bool(default))
            elif kind == "choice":
                widget = QComboBox()
                widget.addItems([str(value) for value in default])
            else:
                widget = QLineEdit(str(default))
                helper = _placeholder_for(str(key))
                if helper:
                    widget.setPlaceholderText(helper)
                if str(key).endswith("path"):
                    holder = QWidget()
                    row = QHBoxLayout(holder)
                    row.setContentsMargins(0, 0, 0, 0)
                    row.setSpacing(6)
                    row.addWidget(widget, 1)
                    browse = QPushButton("Browse…")
                    browse.clicked.connect(lambda _=False, edit=widget: _browse_path(self, edit))
                    row.addWidget(browse)
                    self.inputs[key] = widget
                    form.addRow(_field_label(label), holder)
                    continue
            self.inputs[key] = widget
            form.addRow(_field_label(label), widget)
        scroll.setWidget(card)
        outer.addWidget(scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        run = buttons.button(QDialogButtonBox.Ok)
        run.setText("Run Tool")
        run.setObjectName("PrimaryButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    ValuesDialog.__init__ = values_init

    class ResultView(QScrollArea):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("ResultView")
            self.setWidgetResizable(True)
            self.setFrameShape(QFrame.NoFrame)
            self.body = QWidget()
            self.layout = QVBoxLayout(self.body)
            self.layout.setContentsMargins(6, 6, 6, 12)
            self.layout.setSpacing(10)
            self.layout.addStretch(1)
            self.setWidget(self.body)
            self.placeholder = "Run a tool to see its result."
            self._show_placeholder()

        def setPlaceholderText(self, value):
            self.placeholder = str(value)

        def clear(self):
            self._clear()
            self._show_placeholder()

        def appendPlainText(self, text):
            self.show_text(str(text))

        def _clear(self):
            while self.layout.count():
                item = self.layout.takeAt(0)
                widget = item.widget()
                child = item.layout()
                if widget is not None:
                    widget.deleteLater()
                if child is not None:
                    _clear_layout(child)

        def _show_placeholder(self):
            self._clear()
            card = QFrame()
            card.setObjectName("ResultCard")
            layout = QVBoxLayout(card)
            title = QLabel("RESULTS")
            title.setObjectName("DeckLabel")
            layout.addWidget(title)
            note = QLabel(self.placeholder)
            note.setObjectName("Muted")
            note.setWordWrap(True)
            layout.addWidget(note)
            self.layout.addWidget(card)
            self.layout.addStretch(1)

        def show_text(self, text: str, warning: str = ""):
            lines = [line.rstrip() for line in text.strip().splitlines()]
            title = lines[0].strip() if lines else "Result"
            body = lines[1:] if len(lines) > 1 else []
            self._clear()
            self._add_title(title)
            if warning:
                self._add_warning(warning)
            scalar_rows = []
            free = []
            for line in body:
                stripped = line.strip()
                if not stripped:
                    continue
                if ": " in stripped and not stripped.startswith(("Note:", "Reason:")):
                    label, value = stripped.split(": ", 1)
                    if len(label) <= 42 and value:
                        scalar_rows.append((label, value))
                        continue
                free.append(stripped)
            if scalar_rows:
                self._add_metrics(scalar_rows)
            if free:
                section = QFrame()
                section.setObjectName("ResultSection")
                layout = QVBoxLayout(section)
                for line in free:
                    label = QLabel(line)
                    label.setWordWrap(True)
                    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                    layout.addWidget(label)
                self.layout.addWidget(section)
            self.layout.addStretch(1)

        def show_structured(self, title: str, data: Any, note: str = "", warning: str = ""):
            self._clear()
            self._add_title(title)
            if warning:
                self._add_warning(warning)
            self._render_value("Result", data)
            if note:
                self._add_warning(note, label="NOTE")
            self.layout.addStretch(1)

        def _add_title(self, title: str):
            card = QFrame()
            card.setObjectName("ResultCard")
            layout = QVBoxLayout(card)
            kicker = QLabel("RESULT")
            kicker.setObjectName("DeckLabel")
            layout.addWidget(kicker)
            heading = QLabel(str(title))
            heading.setObjectName("WorkspaceTitle")
            heading.setWordWrap(True)
            layout.addWidget(heading)
            self.layout.addWidget(card)

        def _add_warning(self, message: str, label: str = "VERSION NOTICE"):
            card = QFrame()
            card.setObjectName("WarningBanner")
            layout = QVBoxLayout(card)
            kicker = QLabel(label)
            kicker.setObjectName("DeckLabel")
            layout.addWidget(kicker)
            text = QLabel(str(message))
            text.setWordWrap(True)
            text.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(text)
            self.layout.addWidget(card)

        def _add_metrics(self, rows):
            card = QFrame()
            card.setObjectName("ResultSection")
            grid = QGridLayout(card)
            grid.setSpacing(8)
            columns = 3
            for index, (label, value) in enumerate(rows[:18]):
                metric = QFrame()
                metric.setObjectName("ResultMetric")
                box = QVBoxLayout(metric)
                box.setContentsMargins(10, 8, 10, 8)
                value_label = QLabel(str(value))
                value_label.setObjectName("MetricValue")
                value_label.setWordWrap(True)
                value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                box.addWidget(value_label)
                name = QLabel(str(label))
                name.setObjectName("MetricLabel")
                name.setWordWrap(True)
                box.addWidget(name)
                grid.addWidget(metric, index // columns, index % columns)
            self.layout.addWidget(card)

        def _render_value(self, name: str, value: Any):
            if isinstance(value, dict):
                scalars = [(str(k), _scalar(v)) for k, v in value.items() if not isinstance(v, (dict, list, tuple))]
                if scalars:
                    self._add_metrics([(human_key(k), v) for k, v in scalars])
                for key, child in value.items():
                    if isinstance(child, (dict, list, tuple)):
                        self._render_value(human_key(key), child)
                if not value:
                    self._add_text_section(name, "No additional details.")
                return
            if isinstance(value, (list, tuple)):
                if not value:
                    self._add_text_section(name, "None")
                    return
                if all(isinstance(row, dict) for row in value):
                    self._add_table(name, list(value))
                    return
                if all(isinstance(row, (list, tuple)) for row in value):
                    rows = [{f"Value {i + 1}": cell for i, cell in enumerate(row)} for row in value[:250]]
                    self._add_table(name, rows)
                    return
                self._add_text_section(name, "\n".join(f"{i + 1}. {_scalar(row)}" for i, row in enumerate(value[:250])))
                return
            self._add_text_section(name, _scalar(value))

        def _add_text_section(self, name: str, text: str):
            card = QFrame()
            card.setObjectName("ResultSection")
            layout = QVBoxLayout(card)
            title = QLabel(str(name).upper())
            title.setObjectName("DeckLabel")
            layout.addWidget(title)
            label = QLabel(str(text))
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(label)
            self.layout.addWidget(card)

        def _add_table(self, name: str, rows: list[dict]):
            preview = rows[:200]
            columns = []
            for row in preview:
                for key in row:
                    if key not in columns:
                        columns.append(key)
                if len(columns) >= 10:
                    break
            columns = columns[:10]
            card = QFrame()
            card.setObjectName("ResultSection")
            layout = QVBoxLayout(card)
            title = QLabel(str(name).upper())
            title.setObjectName("DeckLabel")
            layout.addWidget(title)
            if len(rows) > len(preview):
                note = QLabel(f"Showing the first {len(preview)} of {len(rows)} rows.")
                note.setObjectName("Muted")
                layout.addWidget(note)
            table = QTableWidget(len(preview), len(columns))
            table.setHorizontalHeaderLabels([human_key(column) for column in columns])
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setAlternatingRowColors(True)
            for r, row in enumerate(preview):
                for c, key in enumerate(columns):
                    table.setItem(r, c, QTableWidgetItem(_scalar(row.get(key))))
            table.resizeColumnsToContents()
            table.horizontalHeader().setStretchLastSection(True)
            table.setMinimumHeight(min(420, 70 + len(preview) * 24))
            layout.addWidget(table)
            self.layout.addWidget(card)

    original_f3_init = F3Plus.__init__
    original_run_selected = F3Plus.run_selected
    original_open_trades = F3Plus.open_trade_browser
    original_update_badges = F3Plus.update_link_badges
    original_version_dialog = F3Plus.version_dialog
    original_options_dialog = F3Plus.options_dialog
    original_selection_changed = F3Plus.selection_changed
    original_guide_html = F3Plus._guide_html

    def extended_init(self, *args, **kwargs):
        original_f3_init(self, *args, **kwargs)
        self._version_context = resolve_version_context(self.settings.minecraft_version)

        old_output = self.output
        self.detail_stack.removeWidget(old_output)
        old_output.deleteLater()
        self.output = ResultView(self)
        self.output.setPlaceholderText("Run a tool to see its current result, source, warnings, and technical details.")
        self.detail_stack.insertWidget(1, self.output)

        self.fallback_badge = QLabel()
        self.fallback_badge.setObjectName("WarningChip")
        self.fallback_badge.setVisible(False)
        context_layout = self.version_badge.parentWidget().layout()
        try:
            index = context_layout.indexOf(self.version_badge)
            context_layout.insertWidget(index + 1, self.fallback_badge)
        except Exception:
            context_layout.addWidget(self.fallback_badge)
        _sync_version_context(self)
        self.update_link_badges()

    def open_trade_browser(self, profession=None, mode="Trade Browser"):
        explorer = VillagerExplorer(
            self.settings.minecraft_version,
            self,
            profession=profession,
            mode=mode,
            settings=self.settings,
        )
        explorer.exec()

    def run_selected(self):
        spec = self.selected_spec()
        if spec is not None and spec.top == "Villager Explorer" and spec.submenu in {"Trades", "Professions"}:
            reason = safe_mode_restriction(spec) if self.settings.safe_mode else None
            if reason:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Safe Mode", reason)
                return
            self.settings.remember_tool(spec.id)
            profession = spec.name if spec.submenu == "Professions" else None
            return open_trade_browser(self, profession, spec.name)
        return original_run_selected(self)

    def write(self, text):
        warning = _result_warning(self)
        self.output.show_text(str(text).rstrip(), warning=warning)

    def show_result(self, title, data, note=""):
        self.output.show_structured(title, data, note=note, warning=_result_warning(self))
        self._set_detail_view(1)

    def update_link_badges(self):
        original_update_badges(self)
        _sync_version_context(self)

    def version_dialog(self):
        original_version_dialog(self)
        self._version_context = resolve_version_context(self.settings.minecraft_version)
        _sync_version_context(self)

    def options_dialog(self):
        original_options_dialog(self)
        self._version_context = resolve_version_context(self.settings.minecraft_version)
        _sync_version_context(self)

    def selection_changed(self):
        original_selection_changed(self)
        spec = self.selected_spec()
        if spec is not None and spec.top == "Villager Explorer" and spec.submenu in {"Trades", "Professions"} and self.run_btn.isEnabled():
            self.run_btn.setText("Open Explorer")
        _sync_version_context(self)

    def guide_html(self, spec, guide, restriction=None):
        base = original_guide_html(self, spec, guide, restriction)
        context = getattr(self, "_version_context", resolve_version_context(self.settings.minecraft_version))
        if not context.uses_worldgen_fallback or not _worldgen_relevant(spec):
            return base
        p = __import__("minescript.ui_theme", fromlist=["palette"]).palette(self.settings.theme, self.settings.custom_palette)
        warning = (
            f"<div style='padding:10px;border:1px solid {p['warning']};background:{p['surface3']};border-radius:6px'>"
            f"<b>World-generation fallback</b><br>{html.escape(context.calculation_reason)}</div>"
        )
        return warning + base

    F3Plus.__init__ = extended_init
    F3Plus.open_trade_browser = open_trade_browser
    F3Plus.run_selected = run_selected
    F3Plus.write = write
    F3Plus.show_result = show_result
    F3Plus.update_link_badges = update_link_badges
    F3Plus.version_dialog = version_dialog
    F3Plus.options_dialog = options_dialog
    F3Plus.selection_changed = selection_changed
    F3Plus._guide_html = guide_html
    F3Plus._v2_ux_installed = True


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child = item.layout()
        if widget is not None:
            widget.deleteLater()
        if child is not None:
            _clear_layout(child)


def _placeholder_for(key: str) -> str:
    key = key.lower()
    if key == "seed":
        return "Java Edition world seed"
    if key.endswith("path"):
        return "Select or paste a local path"
    if key in {"query", "filter"}:
        return "Search text"
    if key in {"x", "x1", "x2", "cx"}:
        return "X coordinate"
    if key in {"z", "z1", "z2", "cz"}:
        return "Z coordinate"
    return ""


def _field_label(label: str) -> str:
    text = str(label).strip()
    replacements = {
        "Radius (chunks)": "Search radius (chunks)",
        "Radius/chunks/count": "Primary radius / count",
        "Secondary": "Secondary value",
        "Units": "Units / entities",
    }
    return replacements.get(text, text)


def _browse_path(dialog, edit):
    path = QFileDialog.getExistingDirectory(dialog, "Select folder", edit.text().strip())
    if path:
        edit.setText(path)


def _scalar(value: Any) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def human_key(value: str) -> str:
    words = str(value).replace("_", " ").split()
    acronyms = {"xp": "XP", "rng": "RNG", "id": "ID", "x": "X", "y": "Y", "z": "Z", "mc": "Minecraft"}
    return " ".join(acronyms.get(word.lower(), word.capitalize()) for word in words)


def _worldgen_relevant(spec) -> bool:
    if spec is None or spec.top != "Seed Tools":
        return False
    return spec.submenu in {"Biomes", "Structures", "Cubiomes", "World Analysis", "Local Area", "Nether"}


def _result_warning(window) -> str:
    spec = window.selected_spec() if hasattr(window, "selected_spec") else None
    context = getattr(window, "_version_context", None)
    if context is None:
        return ""
    if context.uses_worldgen_fallback and _worldgen_relevant(spec):
        return context.calculation_reason
    return ""


def _sync_version_context(window) -> None:
    from .version_context import resolve as resolve_version_context

    context = resolve_version_context(window.settings.minecraft_version)
    window._version_context = context
    window.version_badge.setText("Java • " + context.selected)
    if not hasattr(window, "fallback_badge"):
        return
    if context.uses_worldgen_fallback:
        window.fallback_badge.setText("Worldgen → " + context.calculation_version)
        window.fallback_badge.setToolTip(context.calculation_reason)
        window.fallback_badge.setVisible(True)
    else:
        window.fallback_badge.setVisible(False)
