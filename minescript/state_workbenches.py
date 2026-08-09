from __future__ import annotations

from dataclasses import asdict, fields
import json
import math
from pathlib import Path
import shutil

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSpinBox,
    QDoubleSpinBox, QTabWidget, QTableWidget, QTableWidgetItem, QTextBrowser,
    QVBoxLayout, QWidget,
)

from .config import CONFIG_FILE, Keybinds, Settings
from .control_bindings import normalize_binding
from .ui_dialogs import ParameterDialog
from .user_state import clear_results, load_projects, load_results, save_projects
from .villagers import installed_versions
from .world_profiles import discover_saves, read_level_dat


def _group_for(settings, name: str) -> str:
    for group, members in (settings.waypoint_groups or {}).items():
        if name in (members or []): return str(group)
    return ""


def _assign_group(settings, name: str, group: str):
    groups = {str(k): list(v or []) for k, v in (settings.waypoint_groups or {}).items()}
    for members in groups.values():
        while name in members: members.remove(name)
    if group:
        groups.setdefault(group, []).append(name)
    settings.waypoint_groups = {k: v for k, v in groups.items() if v}


class WaypointManagerDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner); self.owner = owner; self.settings = owner.settings
        self.setWindowTitle("Waypoints, Routes & Coordinate History"); self.resize(980, 700)
        root = QVBoxLayout(self); tabs = QTabWidget(); root.addWidget(tabs, 1)

        waypoints = QWidget(); wv = QVBoxLayout(waypoints)
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["Name", "X", "Y", "Z", "Group"]); self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setSelectionMode(QAbstractItemView.SingleSelection); wv.addWidget(self.table, 1)
        buttons = QHBoxLayout();
        for text, fn in (("Add", self.add), ("Edit", self.edit), ("Delete", self.delete), ("New group", self.new_group), ("Delete group", self.delete_group), ("Import…", self.import_json), ("Export…", self.export_json)):
            b = QPushButton(text); b.clicked.connect(fn); buttons.addWidget(b)
        buttons.addStretch(); wv.addLayout(buttons); tabs.addTab(waypoints, "Waypoints")

        history = QWidget(); hv = QVBoxLayout(history); self.history = QTableWidget(0, 5); self.history.setHorizontalHeaderLabels(["Time", "Dimension", "X", "Y", "Z"]); self.history.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch); hv.addWidget(self.history, 1)
        hbuttons = QHBoxLayout(); clear = QPushButton("Clear history"); clear.clicked.connect(self.clear_history); copy = QPushButton("Copy selected coordinates"); copy.clicked.connect(self.copy_history); hbuttons.addWidget(copy); hbuttons.addWidget(clear); hbuttons.addStretch(); hv.addLayout(hbuttons); tabs.addTab(history, "Coordinate History")
        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close); self.refresh()

    def refresh(self):
        rows = sorted((self.settings.waypoints or {}).items())
        self.table.setRowCount(len(rows))
        for r, (name, value) in enumerate(rows):
            xyz = list(value or [0, 64, 0]) + [0, 0, 0]
            for c, value in enumerate((name, xyz[0], xyz[1], xyz[2], _group_for(self.settings, name))): self.table.setItem(r, c, QTableWidgetItem(str(value)))
        history = list(self.settings.coordinate_history or [])
        self.history.setRowCount(len(history))
        for r, row in enumerate(reversed(history[-500:])):
            if isinstance(row, dict): values = (row.get("time", ""), row.get("dimension", ""), row.get("x", ""), row.get("y", ""), row.get("z", ""))
            else:
                raw = list(row) if isinstance(row, (list, tuple)) else [row]; raw += ["", "", "", "", ""]; values = ("", "", raw[0], raw[1], raw[2])
            for c, value in enumerate(values): self.history.setItem(r, c, QTableWidgetItem(str(value)))

    def selected_name(self):
        rows = self.table.selectionModel().selectedRows(); return self.table.item(rows[0].row(), 0).text() if rows else ""

    def _editor(self, title, name="Waypoint", values=(0.0, 64.0, 0.0), group=""):
        groups = sorted(set((self.settings.waypoint_groups or {}).keys()) | ({group} if group else set()))
        dialog = ParameterDialog(title, [
            ("name", "Name", name, "text"), ("x", "X", values[0], "float"), ("y", "Y", values[1], "float"), ("z", "Z", values[2], "float"),
            ("group", "Group", ["", *groups], "choice"),
        ], self, "Waypoints are stored locally in F3+ settings and are available to route and travel workbenches.", "Save")
        if group and isinstance(dialog.inputs.get("group"), QComboBox): dialog.inputs["group"].setCurrentText(group)
        return dialog

    def add(self):
        p = getattr(self.owner, "current_position", None); xyz = (p.x, p.y, p.z) if p is not None else (0.0, 64.0, 0.0)
        dialog = self._editor("Add Waypoint", values=xyz)
        if dialog.exec() != QDialog.Accepted: return
        v = dialog.values(); name = str(v["name"]).strip()
        if not name: return QMessageBox.warning(self, "Waypoint", "Enter a waypoint name.")
        self.settings.waypoints[name] = [float(v["x"]), float(v["y"]), float(v["z"])]; _assign_group(self.settings, name, str(v["group"])); self.settings.save(); self.refresh()

    def edit(self):
        old = self.selected_name()
        if not old: return
        raw = self.settings.waypoints.get(old, [0, 64, 0]); dialog = self._editor("Edit Waypoint", old, raw, _group_for(self.settings, old))
        if dialog.exec() != QDialog.Accepted: return
        v = dialog.values(); name = str(v["name"]).strip()
        if not name: return
        if name != old: self.settings.waypoints.pop(old, None); _assign_group(self.settings, old, "")
        self.settings.waypoints[name] = [float(v["x"]), float(v["y"]), float(v["z"])]; _assign_group(self.settings, name, str(v["group"])); self.settings.save(); self.refresh()

    def delete(self):
        name = self.selected_name()
        if not name: return
        if QMessageBox.question(self, "Delete Waypoint", f"Delete {name}?") != QMessageBox.Yes: return
        self.settings.waypoints.pop(name, None); _assign_group(self.settings, name, ""); self.settings.save(); self.refresh()

    def new_group(self):
        dialog = ParameterDialog("New Waypoint Group", [("name", "Group name", "Project", "text")], self, run_label="Create")
        if dialog.exec() != QDialog.Accepted: return
        name = str(dialog.values()["name"]).strip()
        if name: self.settings.waypoint_groups.setdefault(name, []); self.settings.save(); self.refresh()

    def delete_group(self):
        groups = sorted((self.settings.waypoint_groups or {}).keys())
        if not groups: return
        dialog = ParameterDialog("Delete Waypoint Group", [("group", "Group", groups, "choice")], self, "Waypoints are kept; only their group assignment is removed.", "Delete")
        if dialog.exec() != QDialog.Accepted: return
        self.settings.waypoint_groups.pop(dialog.values()["group"], None); self.settings.save(); self.refresh()

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Waypoints", "F3Plus-waypoints.json", "JSON (*.json)")
        if not path: return
        Path(path).write_text(json.dumps({"waypoints": self.settings.waypoints, "groups": self.settings.waypoint_groups}, indent=2) + "\n", encoding="utf-8")

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Waypoints", "", "JSON (*.json)")
        if not path: return
        try: raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as exc: return QMessageBox.warning(self, "Import Waypoints", str(exc))
        points = raw.get("waypoints", raw) if isinstance(raw, dict) else {}
        if not isinstance(points, dict): return QMessageBox.warning(self, "Import Waypoints", "File does not contain a waypoint object.")
        for name, value in points.items():
            if isinstance(value, (list, tuple)) and len(value) >= 3:
                try: self.settings.waypoints[str(name)] = [float(value[0]), float(value[1]), float(value[2])]
                except (TypeError, ValueError): pass
        if isinstance(raw, dict) and isinstance(raw.get("groups"), dict): self.settings.waypoint_groups.update({str(k): list(v or []) for k, v in raw["groups"].items()})
        self.settings.save(); self.refresh()

    def clear_history(self):
        self.settings.coordinate_history = []; self.settings.save(); self.refresh()

    def copy_history(self):
        rows = self.history.selectionModel().selectedRows()
        if not rows: return
        r = rows[0].row(); text = " ".join(self.history.item(r, c).text() for c in (2, 3, 4)); from PySide6.QtWidgets import QApplication; QApplication.clipboard().setText(text)


class SafetySettingsDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner); self.owner = owner; s = owner.settings
        self.setWindowTitle("Automation Safety"); self.resize(650, 580); root = QVBoxLayout(self)
        title = QLabel("Automation Safety"); title.setObjectName("WorkspaceTitle"); root.addWidget(title)
        note = QLabel("These limits are enforced by MacroEngine during real automation runs. Zero disables a limit where indicated."); note.setWordWrap(True); note.setObjectName("Muted"); root.addWidget(note)
        form = QFormLayout(); root.addLayout(form); self.widgets = {}
        specs = [
            ("runtime_limit_seconds", "Runtime limit", 0, 86400, " s"), ("action_limit", "Action/cycle limit", 0, 10_000_000, ""),
            ("delayed_start_seconds", "Delayed start", 0, 3600, " s"), ("recovery_attempts", "Coordinate recovery attempts", 1, 100, ""),
            ("restore_hotbar_slot", "Restore hotbar slot (0 disables)", 0, 9, ""),
        ]
        for key, label, lo, hi, suffix in specs:
            w = QSpinBox(); w.setRange(lo, hi); w.setValue(int(getattr(s, key))); w.setSuffix(suffix); self.widgets[key] = w; form.addRow(label, w)
        self.focus_loss = QCheckBox("Stop when the linked Minecraft client loses focus"); self.focus_loss.setChecked(bool(s.focus_loss_stop)); form.addRow("", self.focus_loss)
        self.stuck_window = QDoubleSpinBox(); self.stuck_window.setRange(.1, 600); self.stuck_window.setValue(float(s.stuck_window_seconds)); self.stuck_window.setSuffix(" s"); form.addRow("Stuck detection window", self.stuck_window)
        self.stuck_distance = QDoubleSpinBox(); self.stuck_distance.setRange(0, 100); self.stuck_distance.setDecimals(3); self.stuck_distance.setValue(float(s.stuck_min_displacement)); self.stuck_distance.setSuffix(" blocks"); form.addRow("Minimum progress", self.stuck_distance)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def save(self):
        s = self.owner.settings
        for key, widget in self.widgets.items(): setattr(s, key, widget.value())
        s.focus_loss_stop = self.focus_loss.isChecked(); s.stuck_window_seconds = self.stuck_window.value(); s.stuck_min_displacement = self.stuck_distance.value(); s.save(); self.owner.engine.set_settings(s)

    def accept(self): self.save(); super().accept()


class ProfilesControlsDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner); self.owner = owner; self.settings = owner.settings
        self.setWindowTitle("Profiles, Controls & Calibration"); self.resize(800, 720)
        root = QVBoxLayout(self); tabs = QTabWidget(); root.addWidget(tabs, 1)

        controls = QWidget(); cf = QFormLayout(controls); self.binding_fields = {}
        for field in fields(Keybinds):
            edit = QLineEdit(str(getattr(self.settings.keybinds, field.name))); self.binding_fields[field.name] = edit; cf.addRow(field.name.replace("_", " ").title(), edit)
        self.capture_delay = QSpinBox(); self.capture_delay.setRange(0, 3000); self.capture_delay.setValue(int(self.settings.coordinate_capture_delay_ms)); self.capture_delay.setSuffix(" ms"); cf.addRow("F3+C capture delay", self.capture_delay); tabs.addTab(controls, "Controls")

        calibration = QWidget(); cal = QFormLayout(calibration); self.turn = QSpinBox(); self.turn.setRange(1, 100000); self.turn.setValue(int(self.settings.turn_units_per_90)); cal.addRow("Mouse units per 90°", self.turn); self.distance = QDoubleSpinBox(); self.distance.setRange(.01, 1000); self.distance.setValue(float(self.settings.movement_blocks_per_second)); self.distance.setDecimals(4); self.distance.setSuffix(" blocks/s"); cal.addRow("Planning movement speed", self.distance); tabs.addTab(calibration, "Calibration")

        profiles = QWidget(); pv = QVBoxLayout(profiles); explain = QLabel("Profiles are complete F3+ JSON settings. Import creates a local backup before applying the selected profile."); explain.setWordWrap(True); pv.addWidget(explain)
        for text, fn in (("Backup current settings…", self.backup), ("Export profile…", self.export), ("Import profile…", self.import_profile)):
            button = QPushButton(text); button.clicked.connect(fn); pv.addWidget(button)
        pv.addStretch(); tabs.addTab(profiles, "Profiles")
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def save_values(self):
        for key, edit in self.binding_fields.items(): setattr(self.settings.keybinds, key, normalize_binding(edit.text()))
        self.settings.coordinate_capture_delay_ms = self.capture_delay.value(); self.settings.turn_units_per_90 = self.turn.value(); self.settings.movement_blocks_per_second = self.distance.value(); self.settings.save(); self.owner.engine.set_settings(self.settings); self.owner.engine.set_input(self.owner.input); self.owner.capture.settings = self.settings

    def accept(self): self.save_values(); super().accept()

    def backup(self):
        self.settings.save(); path, _ = QFileDialog.getSaveFileName(self, "Backup Settings", "F3Plus-settings-backup.json", "JSON (*.json)")
        if path: shutil.copy2(CONFIG_FILE, Path(path))

    def export(self):
        self.save_values(); path, _ = QFileDialog.getSaveFileName(self, "Export Profile", "F3Plus-profile.json", "JSON (*.json)")
        if path: shutil.copy2(CONFIG_FILE, Path(path))

    def import_profile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Profile", "", "JSON (*.json)")
        if not path: return
        try: raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as exc: return QMessageBox.warning(self, "Import Profile", str(exc))
        if not isinstance(raw, dict): return QMessageBox.warning(self, "Import Profile", "Profile root must be a JSON object.")
        self.settings.save(); backup = CONFIG_FILE.with_name("config.before-import.json"); shutil.copy2(CONFIG_FILE, backup)
        allowed = {f.name for f in fields(Settings)}
        for key, value in raw.items():
            if key in allowed and key != "keybinds": setattr(self.settings, key, value)
        kb = raw.get("keybinds")
        if isinstance(kb, dict):
            allowed_kb = {f.name for f in fields(Keybinds)}
            for key, value in kb.items():
                if key in allowed_kb: setattr(self.settings.keybinds, key, normalize_binding(value))
        self.settings.save(); self.owner.engine.set_settings(self.settings); self.owner.executor.minecraft_version = self.settings.minecraft_version; QMessageBox.information(self, "Import Profile", f"Profile imported. Previous settings: {backup}"); self.close()


class PositionMonitorDialog(QDialog):
    def __init__(self, owner, mode="Continuous Capture"):
        super().__init__(owner); self.owner = owner; self.mode = mode; self.setWindowTitle(mode); self.resize(560, 360)
        root = QVBoxLayout(self); self.status = QLabel("Capture has not started."); self.status.setWordWrap(True); self.status.setObjectName("WorkspaceTitle"); root.addWidget(self.status)
        form = QFormLayout(); root.addLayout(form); self.interval = QDoubleSpinBox(); self.interval.setRange(.2, 60); self.interval.setValue(1.0); self.interval.setSuffix(" s"); form.addRow("Capture interval", self.interval)
        self.x = QDoubleSpinBox(); self.x.setRange(-30_000_000, 30_000_000); self.z = QDoubleSpinBox(); self.z.setRange(-30_000_000, 30_000_000)
        if mode in {"Distance Announcer", "Bearing Lock"}: form.addRow("Target X", self.x); form.addRow("Target Z", self.z)
        buttons = QHBoxLayout(); self.start = QPushButton("Start"); self.stop = QPushButton("Stop"); self.stop.setEnabled(False); self.start.clicked.connect(self.begin); self.stop.clicked.connect(self.timer_stop); buttons.addWidget(self.start); buttons.addWidget(self.stop); buttons.addStretch(); root.addLayout(buttons)
        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close); self.timer = QTimer(self); self.timer.timeout.connect(self.sample)

    def begin(self): self.timer.start(max(200, int(self.interval.value() * 1000))); self.start.setEnabled(False); self.stop.setEnabled(True); self.sample()
    def timer_stop(self): self.timer.stop(); self.start.setEnabled(True); self.stop.setEnabled(False)
    def sample(self):
        try: self.owner.capture_position(); p = self.owner.current_position
        except Exception: return
        if p is None: return
        if self.mode == "Continuous Capture": self.status.setText(f"X {p.x:.3f}  Y {p.y:.3f}  Z {p.z:.3f}\nChunk {p.chunk} • Region {p.region}")
        else:
            dx, dz = self.x.value() - p.x, self.z.value() - p.z; distance = math.hypot(dx, dz); bearing = (math.degrees(math.atan2(-dx, dz)) + 360) % 360
            self.status.setText(f"Remaining: {distance:.2f} blocks\nBearing: {bearing:.2f}°\nCurrent: {p.x:.2f}, {p.z:.2f}")
    def closeEvent(self, event): self.timer.stop(); super().closeEvent(event)


class WorldProfilesDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner); self.owner = owner; self.setWindowTitle("World Profiles"); self.resize(940, 660)
        root = QVBoxLayout(self); title = QLabel("World Profiles & Local Saves"); title.setObjectName("WorkspaceTitle"); root.addWidget(title)
        self.list = QListWidget(); root.addWidget(self.list, 1); buttons = QHBoxLayout();
        for text, fn in (("Discover Minecraft saves", self.discover), ("Add folder…", self.add_folder), ("Use selected profile", self.apply), ("Remove saved profile", self.remove)):
            b = QPushButton(text); b.clicked.connect(fn); buttons.addWidget(b)
        buttons.addStretch(); root.addLayout(buttons); self.detail = QTextBrowser(); self.detail.setMaximumHeight(190); root.addWidget(self.detail); self.list.itemSelectionChanged.connect(self.show_detail); close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close); self.refresh()

    def refresh(self):
        self.list.clear(); saved = load_projects(); discovered = discover_saves(); rows = []
        known = set()
        for row in saved + discovered:
            path = str(row.get("path", ""))
            if not path or path in known: continue
            known.add(path); rows.append(row)
        self.rows = rows
        for i, row in enumerate(rows):
            label = row.get("name") or Path(str(row.get("path", ""))).name; version = row.get("version_name") or row.get("minecraft_version") or "unknown version"; item = QListWidgetItem(f"{label}\n{version} • {row.get('path', '')}"); item.setData(Qt.UserRole, i); self.list.addItem(item)
        if self.list.count(): self.list.setCurrentRow(0)

    def row(self):
        item = self.list.currentItem(); return self.rows[int(item.data(Qt.UserRole))] if item else None

    def show_detail(self):
        row = self.row(); self.detail.setPlainText(json.dumps(row or {}, indent=2, default=str))

    def discover(self):
        saved = load_projects(); paths = {str(row.get("path", "")) for row in saved}
        for row in discover_saves():
            if row.get("path") not in paths: saved.append(row)
        save_projects(saved); self.refresh()

    def add_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Choose Java world folder")
        if not path: return
        row = read_level_dat(path); saved = [r for r in load_projects() if r.get("path") != path]; saved.append(row); save_projects(saved); self.refresh()

    def apply(self):
        row = self.row()
        if not row: return
        if row.get("seed") is not None: self.owner.settings.seed = str(row["seed"])
        if row.get("version_name"): self.owner.settings.minecraft_version = str(row["version_name"])
        self.owner.settings.save(); self.owner.executor.minecraft_version = self.owner.settings.minecraft_version; self.owner.seed_label.setText("Seed set" if self.owner.settings.seed else "Seed not set"); self.owner.version_badge.setText(self.owner.settings.minecraft_version); QMessageBox.information(self, "World Profile", "Selected world seed/version applied to F3+.")

    def remove(self):
        row = self.row()
        if not row: return
        save_projects([r for r in load_projects() if r.get("path") != row.get("path")]); self.refresh()


class ResultHistoryDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner); self.setWindowTitle("Result History"); self.resize(980, 650); root = QVBoxLayout(self); self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["Time", "Workbench", "Operation", "Minecraft version"]); self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); root.addWidget(self.table, 1); self.detail = QTextBrowser(); root.addWidget(self.detail, 1); buttons = QHBoxLayout(); export = QPushButton("Export selected…"); export.clicked.connect(self.export); clear = QPushButton("Clear history"); clear.clicked.connect(self.clear); buttons.addWidget(export); buttons.addWidget(clear); buttons.addStretch(); root.addLayout(buttons); close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close); self.table.itemSelectionChanged.connect(self.show); self.refresh()
    def refresh(self):
        self.rows = load_results(); self.table.setRowCount(len(self.rows))
        for r, row in enumerate(self.rows):
            for c, value in enumerate((row.get("timestamp", ""), row.get("workbench", ""), row.get("operation", ""), row.get("minecraft_version", ""))): self.table.setItem(r, c, QTableWidgetItem(str(value)))
        if self.table.rowCount(): self.table.selectRow(0)
    def selected(self):
        rows = self.table.selectionModel().selectedRows(); return self.rows[rows[0].row()] if rows else None
    def show(self): self.detail.setPlainText(json.dumps(self.selected() or {}, indent=2, ensure_ascii=False, default=str))
    def export(self):
        row = self.selected()
        if not row: return
        path, _ = QFileDialog.getSaveFileName(self, "Export Result", "F3Plus-result.json", "JSON (*.json)")
        if path: Path(path).write_text(json.dumps(row, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    def clear(self): clear_results(); self.refresh()


class DiagnosticsDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner); self.owner = owner; self.setWindowTitle("F3+ Diagnostics"); self.resize(760, 620); root = QVBoxLayout(self); self.report = QTextBrowser(); root.addWidget(self.report, 1); buttons = QHBoxLayout(); refresh = QPushButton("Refresh"); refresh.clicked.connect(self.build); copy = QPushButton("Copy report"); copy.clicked.connect(lambda: __import__('PySide6.QtWidgets', fromlist=['QApplication']).QApplication.clipboard().setText(self.report.toPlainText())); buttons.addWidget(refresh); buttons.addWidget(copy); buttons.addStretch(); root.addLayout(buttons); close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close); self.build()
    def build(self):
        lines = [f"F3+ Minecraft target: {self.owner.settings.minecraft_version}", f"Linked client: {self.owner.target.display if self.owner.target else 'none'}"]
        cap = getattr(self.owner.input, "capabilities", None); lines += [f"Input backend: {getattr(cap, 'name', 'unknown')}", f"Desktop session: {getattr(cap, 'session', '')}", f"Background input: {getattr(cap, 'background_label', 'unknown')}", f"Minimized input: {getattr(cap, 'minimized_label', 'unknown')}", "", "Installed Minecraft versions:"]
        lines += [f"  {name}: {path}" for name, path in installed_versions().items()] or ["  none detected"]
        try:
            from .seed.bundled import cubiomes_status, bedrock_status
            cs, bs = cubiomes_status(), bedrock_status(); lines += ["", f"Cubiomes: {'ready' if cs.available else 'not ready'}", f"Nether Bedrock Cracker: {'ready' if bs.executable else 'source/preparation required'}"]
        except Exception as exc: lines += ["", f"Component status error: {exc}"]
        lines += ["", f"Settings file: {CONFIG_FILE}", f"Saved waypoints: {len(self.owner.settings.waypoints)}", f"Coordinate history entries: {len(self.owner.settings.coordinate_history)}"]
        self.report.setPlainText("\n".join(lines))


def stateful_operation(owner, name: str) -> bool:
    if name in {"Coordinate History", "Waypoint Groups"}:
        WaypointManagerDialog(owner).exec(); return True
    if name in {"Continuous Capture", "Distance Announcer", "Bearing Lock"}:
        PositionMonitorDialog(owner, name).exec(); return True
    if name in {"Control Bindings", "Turn Calibration", "Movement Calibration", "Coordinate Capture Settings", "Backup Settings", "Export Profiles", "Import Profiles"}:
        ProfilesControlsDialog(owner).exec(); return True
    if name in {"Focus Loss Stop", "Restore Hotbar", "Runtime Limit", "Delayed Start", "Action Counter", "Stuck Detection", "Recovery Attempts"}:
        SafetySettingsDialog(owner).exec(); return True
    return False
