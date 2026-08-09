from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QSpinBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem,
    QTextBrowser, QVBoxLayout, QWidget,
)

from .coordinates import Position
from .control_bindings import normalize_binding
from .gameplay import macros
from .gameplay.presets import alternating_steps, grid_steps, parallel_row_steps, rectangle_steps, serpentine_steps
from .gameplay.recorder import MacroRecording, TEMPLATES
from .ui_dialogs import ParameterDialog
from .user_state import load_macros, save_macros

try:
    from pynput import keyboard as pynput_keyboard, mouse as pynput_mouse
except Exception:
    pynput_keyboard = pynput_mouse = None


def _aim_and_travel(engine, target: Position, sprint: bool = False):
    current = engine.get_position(); desired = current.bearing_to(target)
    if current.yaw is not None:
        delta = ((desired - current.yaw + 180.0) % 360.0) - 180.0
        engine.turn_degrees(delta)
        if engine.wait(0.12): return
    keys = ("w", "ctrl") if sprint else ("w",)
    from .gameplay.coordinate_control import CoordinateController
    return CoordinateController(engine, engine.coordinate_policy()).move_until(target, keys=keys)


def configure_and_start(owner, name: str) -> bool:
    """Return True when this macro owns a dedicated configuration workflow."""
    run = owner.start_macro_callable

    if name == "Custom Hold":
        d = ParameterDialog(name, [("binding", "Minecraft action/key", "w", "text")], owner, "Use a configured key/action such as w, space, f, mouse:left or mouse:right.")
        if d.exec() == QDialog.Accepted:
            binding = normalize_binding(d.values()["binding"])
            if binding.startswith("mouse:"): run(name, lambda e, b=binding.split(":", 1)[1]: macros.continuous_action(e, held_mouse=(b,)))
            else: run(name, lambda e, b=binding: macros.continuous_action(e, held_keys=(b,)))
        return True

    if name == "Custom Periodic Action":
        d = ParameterDialog(name, [("button", "Mouse button", ["left", "right"], "choice"), ("interval", "Interval", 1.0, "float"), ("actions", "Actions per cycle", 1, "int"), ("spacing", "Spacing between actions", 1.0, "float")], owner)
        if d.exec() == QDialog.Accepted:
            v = d.values(); run(name, lambda e: macros.periodic_interaction(e, False, int(max(.01, v["interval"]) * 1000), max(1, int(v["actions"])), int(max(.01, v["spacing"]) * 1000), button=v["button"]))
        return True

    if name == "Livestock Breeder":
        d = ParameterDialog(name, [("hold", "Hold feed/use", True, "bool"), ("minutes", "Growth cycle", 20.0, "float"), ("swings", "Swings per cycle", 2, "int"), ("spacing", "Swing spacing", 1.0, "float")], owner, "Holds feed/use and performs the configured interaction cycle. Default timing matches the normal livestock growth interval.")
        if d.exec() == QDialog.Accepted:
            v = d.values(); run(name, lambda e: macros.livestock_breeder(e, bool(v["hold"]), max(.1, float(v["minutes"])), max(1, int(v["swings"])), int(max(.05, float(v["spacing"])) * 1000)))
        return True

    if name == "Auto Fishing":
        d = ParameterDialog(name, [("wait", "Wait before reel", 1.2, "float"), ("recast", "Recast delay", .25, "float")], owner)
        if d.exec() == QDialog.Accepted:
            v = d.values(); run(name, lambda e: macros.auto_fishing(e, int(max(.05, v["wait"]) * 1000), int(max(.05, v["recast"]) * 1000)))
        return True

    if name in {"Coordinate Travel", "Waypoint Travel", "Nether-Assisted Travel"}:
        p = owner.current_position or Position(0, 64, 0)
        if name == "Waypoint Travel":
            names = sorted(owner.settings.waypoints)
            if not names: QMessageBox.information(owner, name, "Create a waypoint first."); return True
            d = ParameterDialog(name, [("waypoint", "Waypoint", names, "choice"), ("sprint", "Sprint", True, "bool")], owner)
            if d.exec() == QDialog.Accepted:
                v = d.values(); raw = owner.settings.waypoints[v["waypoint"]]; target = Position(float(raw[0]), float(raw[1]), float(raw[2])); run(name, lambda e: _aim_and_travel(e, target, bool(v["sprint"])))
            return True
        if name == "Nether-Assisted Travel":
            d = ParameterDialog(name, [("x", "Overworld destination X", 8000.0, "float"), ("z", "Overworld destination Z", 8000.0, "float"), ("current_dimension", "Current dimension", ["Nether", "Overworld"], "choice"), ("y", "Travel Y", p.y, "float"), ("sprint", "Sprint", True, "bool")], owner, "In the Nether, the Overworld destination is scaled 8:1 before coordinate-aware travel begins.")
            if d.exec() == QDialog.Accepted:
                v = d.values(); scale = 1 / 8 if v["current_dimension"] == "Nether" else 1.0; target = Position(float(v["x"]) * scale, float(v["y"]), float(v["z"]) * scale); run(name, lambda e: _aim_and_travel(e, target, bool(v["sprint"])))
            return True
        d = ParameterDialog(name, [("x", "Target X", p.x + 64, "float"), ("y", "Target Y", p.y, "float"), ("z", "Target Z", p.z, "float"), ("sprint", "Sprint", True, "bool")], owner, "F3+ captures F3+C coordinates, turns toward the target when yaw is available, and stops using coordinate feedback.")
        if d.exec() == QDialog.Accepted:
            v = d.values(); target = Position(float(v["x"]), float(v["y"]), float(v["z"])); run(name, lambda e: _aim_and_travel(e, target, bool(v["sprint"])))
        return True

    construction = {"Rectangle", "Filled Rectangle", "Grid", "Rows", "Alternating Pattern", "Perimeter"}
    if name in construction:
        d = ParameterDialog(name, [("rows", "Rows", 8, "int"), ("row_seconds", "Row/side travel time", 1.5, "float"), ("spacing", "Row spacing time", .35, "float")], owner, "Align the player before starting. The configured values generate the actual path instead of using a fixed preset.")
        if d.exec() == QDialog.Accepted:
            v = d.values(); rows = max(1, int(v["rows"])); row = max(.05, float(v["row_seconds"])); spacing = max(.05, float(v["spacing"]))
            if name in {"Rectangle", "Perimeter"}: steps = rectangle_steps(row)
            elif name == "Filled Rectangle": steps = serpentine_steps(rows, row, spacing, True)
            elif name == "Grid": steps = grid_steps(rows, row, spacing)
            elif name == "Rows": steps = parallel_row_steps(rows, row, spacing)
            else: steps = alternating_steps(rows, row, spacing)
            run(name, lambda e: macros.construction_pattern(e, steps, loop=False))
        return True

    if name == "Branch Miner":
        d = ParameterDialog(name, [("main", "Main tunnel spacing", 4.0, "float"), ("depth", "Branch depth", 24.0, "float"), ("branches", "Branches", 8, "int"), ("alternating", "Alternate sides", True, "bool")], owner, "Uses coordinate captures to measure travel rather than fixed timing.")
        if d.exec() == QDialog.Accepted:
            v = d.values(); run(name, lambda e: macros.coordinate_branch_miner(e, max(.1, v["main"]), max(.1, v["depth"]), 900, max(1, v["branches"]), bool(v["alternating"])))
        return True

    if name == "Stair Excavator":
        d = ParameterDialog(name, [("steps", "Steps", 32, "int"), ("distance", "Distance per step", 1.0, "float"), ("descending", "Descending", True, "bool")], owner)
        if d.exec() == QDialog.Accepted:
            v = d.values(); run(name, lambda e: macros.coordinate_stair_excavator(e, max(1, v["steps"]), max(.1, v["distance"]), bool(v["descending"])))
        return True

    if name == "Area Excavator":
        d = ParameterDialog(name, [("rows", "Rows", 8, "int"), ("distance", "Row distance", 16.0, "float"), ("shift", "Row shift", 1.0, "float")], owner)
        if d.exec() == QDialog.Accepted:
            v = d.values(); run(name, lambda e: macros.coordinate_area_excavator(e, max(1, v["rows"]), max(.1, v["distance"]), max(.1, v["shift"]), 900))
        return True

    if name in {"Coordinate Row Farmer", "Multi-Row Farmer"}:
        d = ParameterDialog(name, [("rows", "Rows", 16 if name == "Multi-Row Farmer" else 8, "int"), ("seconds", "Row travel time", 10.0, "float"), ("shift", "Row shift time", .45, "float"), ("harvest", "Hold attack/harvest", True, "bool"), ("plant", "Hold use/replant", True, "bool")], owner)
        if d.exec() == QDialog.Accepted:
            v = d.values(); run(name, lambda e: macros.row_farmer(e, max(1, v["rows"]), max(.1, v["seconds"]), max(.05, v["shift"]), 900, bool(v["harvest"]), bool(v["plant"])))
        return True

    if name == "Bone Meal Farmer":
        d = ParameterDialog(name, [("clicks", "Bone meal clicks", 4, "int"), ("delay", "Click delay", .15, "float"), ("plant_slot", "Plant slot", 1, "int"), ("bonemeal_slot", "Bone meal slot", 2, "int")], owner)
        if d.exec() == QDialog.Accepted:
            v = d.values(); run(name, lambda e: macros.bone_meal_farmer(e, max(1, v["clicks"]), int(max(.02, v["delay"]) * 1000), max(1, min(9, v["plant_slot"])), max(1, min(9, v["bonemeal_slot"]))))
        return True

    if name == "Mending Grinder":
        d = ParameterDialog(name, [("attack", "Attack interval", 1.25, "float"), ("rotate", "Slot rotation interval", 30.0, "float"), ("slots", "Slots (comma separated)", "1,2,3", "text")], owner)
        if d.exec() == QDialog.Accepted:
            v = d.values(); slots = tuple(int(x) for x in str(v["slots"]).split(",") if x.strip().isdigit() and 1 <= int(x) <= 9) or (1,); run(name, lambda e: macros.mending_grinder(e, int(max(.05, v["attack"]) * 1000), int(max(.1, v["rotate"]) * 1000), slots))
        return True

    return False


class MacroStudioDialog(QDialog):
    STEP_TYPES = ["tap", "click", "wait", "hold", "turn", "slot"]

    def __init__(self, owner):
        super().__init__(owner); self.owner = owner; self.recording = MacroRecording(); self.k_listener = None; self.m_listener = None; self._pressed = set()
        self.setWindowTitle("Macro Studio"); self.resize(980, 720)
        root = QVBoxLayout(self); title = QLabel("Macro Studio"); title.setObjectName("WorkspaceTitle"); root.addWidget(title)
        note = QLabel("Build, record, save, dry-review and run input sequences. Custom macros remain local under ~/.f3plus and use the same MacroEngine safety limits as built-in automation."); note.setWordWrap(True); note.setObjectName("Muted"); root.addWidget(note)
        top = QHBoxLayout(); self.name = QLineEdit("Custom Macro"); top.addWidget(QLabel("Name")); top.addWidget(self.name, 1); self.loop = QCheckBox("Loop"); top.addWidget(self.loop); root.addLayout(top)
        library = QHBoxLayout(); self.saved = QComboBox(); library.addWidget(QLabel("Saved/template")); library.addWidget(self.saved, 1); load = QPushButton("Load"); load.clicked.connect(self.load_selected); library.addWidget(load); save = QPushButton("Save"); save.clicked.connect(self.save_current); library.addWidget(save); delete = QPushButton("Delete"); delete.clicked.connect(self.delete_current); library.addWidget(delete); root.addLayout(library)

        self.table = QTableWidget(0, 3); self.table.setHorizontalHeaderLabels(["Step type", "Value", "Seconds / amount"]); self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch); root.addWidget(self.table, 1)
        edit = QHBoxLayout();
        for text, fn in (("Add step", self.add_step), ("Remove", self.remove_step), ("Up", lambda: self.move(-1)), ("Down", lambda: self.move(1))): b = QPushButton(text); b.clicked.connect(fn); edit.addWidget(b)
        edit.addStretch(); self.record_btn = QPushButton("Start recording"); self.record_btn.clicked.connect(self.toggle_recording); edit.addWidget(self.record_btn); root.addLayout(edit)
        self.timeline = QTextBrowser(); self.timeline.setMaximumHeight(130); root.addWidget(self.timeline)
        actions = QHBoxLayout(); preview = QPushButton("Refresh dry timeline"); preview.clicked.connect(self.update_timeline); run = QPushButton("Run macro"); run.setObjectName("PrimaryButton"); run.clicked.connect(self.run_macro); export = QPushButton("Export…"); export.clicked.connect(self.export_macro); imp = QPushButton("Import…"); imp.clicked.connect(self.import_macro); actions.addWidget(preview); actions.addWidget(run); actions.addWidget(export); actions.addWidget(imp); actions.addStretch(); root.addLayout(actions)
        close = QDialogButtonBox(QDialogButtonBox.Close); close.rejected.connect(self.reject); root.addWidget(close); self.refresh_library(); self.load_template("Stationary Use")

    def refresh_library(self):
        selected = self.saved.currentText(); self.saved.clear(); self.saved.addItems([f"Template: {name}" for name in sorted(TEMPLATES)] + [f"Saved: {name}" for name in sorted(load_macros())]); index = self.saved.findText(selected)
        if index >= 0: self.saved.setCurrentIndex(index)

    def add_step(self, typ="tap", value="space", seconds="0.05"):
        row = self.table.rowCount(); self.table.insertRow(row); combo = QComboBox(); combo.addItems(self.STEP_TYPES); combo.setCurrentText(str(typ)); self.table.setCellWidget(row, 0, combo); self.table.setItem(row, 1, QTableWidgetItem(str(value))); self.table.setItem(row, 2, QTableWidgetItem(str(seconds)))

    def remove_step(self):
        row = self.table.currentRow()
        if row >= 0: self.table.removeRow(row); self.update_timeline()

    def move(self, delta):
        row = self.table.currentRow(); target = row + delta
        if row < 0 or target < 0 or target >= self.table.rowCount(): return
        steps = self.steps(); steps[row], steps[target] = steps[target], steps[row]; self.set_steps(steps); self.table.setCurrentCell(target, 1)

    def steps(self):
        out = []
        for row in range(self.table.rowCount()):
            typ = self.table.cellWidget(row, 0).currentText(); value = self.table.item(row, 1).text() if self.table.item(row, 1) else ""; raw = self.table.item(row, 2).text() if self.table.item(row, 2) else "0"
            try: amount = float(raw)
            except ValueError: amount = 0.0
            if typ == "tap": out.append({"type": "tap", "key": value or "space", "hold": max(.01, amount or .05)})
            elif typ == "click": out.append({"type": "click", "button": value or "right", "hold": max(.01, amount or .05)})
            elif typ == "wait": out.append({"type": "wait", "seconds": max(0, amount)})
            elif typ == "hold":
                if (value or "").startswith("mouse:"): out.append({"type": "hold", "button": value.split(":", 1)[1], "seconds": max(.01, amount or 1)})
                else: out.append({"type": "hold", "key": value or "w", "seconds": max(.01, amount or 1)})
            elif typ == "turn": out.append({"type": "turn", "dx": int(amount), "dy": 0})
            elif typ == "slot": out.append({"type": "slot", "slot": max(1, min(9, int(amount or value or 1)))})
        return out

    def set_steps(self, steps):
        self.table.setRowCount(0)
        for step in steps:
            typ = step.get("type", "tap")
            if typ == "tap": self.add_step(typ, step.get("key", "space"), step.get("hold", .05))
            elif typ == "click": self.add_step(typ, step.get("button", "right"), step.get("hold", .05))
            elif typ == "wait": self.add_step(typ, "", step.get("seconds", 1))
            elif typ == "hold": self.add_step(typ, step.get("key") or ("mouse:" + str(step.get("button", "right"))), step.get("seconds", 1))
            elif typ == "turn": self.add_step(typ, "horizontal mouse units", step.get("dx", 0))
            elif typ == "slot": self.add_step(typ, "slot", step.get("slot", 1))
        self.update_timeline()

    def load_template(self, name): self.name.setText(name); self.loop.setChecked(False); self.set_steps(TEMPLATES.get(name, []))
    def load_selected(self):
        text = self.saved.currentText()
        if text.startswith("Template: "): self.load_template(text.split(": ", 1)[1]); return
        name = text.split(": ", 1)[1] if ": " in text else text; row = load_macros().get(name)
        if row: self.name.setText(name); self.loop.setChecked(bool(row.get("loop", False))); self.set_steps(list(row.get("steps", [])))
    def save_current(self):
        name = self.name.text().strip() or "Custom Macro"; rows = load_macros(); rows[name] = {"steps": self.steps(), "loop": self.loop.isChecked()}; save_macros(rows); self.refresh_library(); self.saved.setCurrentText("Saved: " + name)
    def delete_current(self):
        name = self.name.text().strip(); rows = load_macros()
        if name in rows: rows.pop(name); save_macros(rows); self.refresh_library()
    def update_timeline(self):
        total = 0.0; lines = []
        for i, step in enumerate(self.steps(), 1):
            duration = float(step.get("seconds", step.get("hold", 0)) or 0); total += max(0, duration); lines.append(f"{i}. {step}")
        self.timeline.setPlainText(f"Known minimum duration: {total:.3f} s per pass\nLoop: {'yes' if self.loop.isChecked() else 'no'}\n\n" + "\n".join(lines))
    def run_macro(self):
        steps = self.steps()
        if not steps: return QMessageBox.information(self, "Macro Studio", "Add at least one step first.")
        self.owner.start_macro_callable(self.name.text().strip() or "Custom Macro", lambda e: macros.route_runner(e, steps, self.loop.isChecked()))
    def export_macro(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Macro", (self.name.text().strip() or "F3Plus-macro") + ".json", "JSON (*.json)")
        if path: Path(path).write_text(json.dumps({"name": self.name.text(), "loop": self.loop.isChecked(), "steps": self.steps()}, indent=2) + "\n", encoding="utf-8")
    def import_macro(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Macro", "", "JSON (*.json)")
        if not path: return
        try: raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as exc: return QMessageBox.warning(self, "Import Macro", str(exc))
        if not isinstance(raw, dict) or not isinstance(raw.get("steps"), list): return QMessageBox.warning(self, "Import Macro", "Not an F3+ macro file.")
        self.name.setText(str(raw.get("name", Path(path).stem))); self.loop.setChecked(bool(raw.get("loop", False))); self.set_steps(raw["steps"])

    def toggle_recording(self):
        if self.recording.active: self.stop_recording(); return
        if pynput_keyboard is None or pynput_mouse is None: return QMessageBox.warning(self, "Macro Recorder", "pynput recording is unavailable on this system. Manual step editing remains available.")
        self.recording.start(); self._pressed.clear(); self.record_btn.setText("Stop recording")
        def key_press(key):
            token = getattr(key, "char", None) or str(key).removeprefix("Key.")
            if token in self._pressed: return
            self._pressed.add(token); self.recording.add("tap", token)
        def key_release(key): self._pressed.discard(getattr(key, "char", None) or str(key).removeprefix("Key."))
        def click(_x, _y, button, pressed):
            if pressed: self.recording.add("click", str(button).split(".")[-1])
        try:
            self.k_listener = pynput_keyboard.Listener(on_press=key_press, on_release=key_release); self.m_listener = pynput_mouse.Listener(on_click=click); self.k_listener.start(); self.m_listener.start()
        except Exception as exc:
            self.recording.stop(); self.record_btn.setText("Start recording"); QMessageBox.warning(self, "Macro Recorder", str(exc))
    def stop_recording(self):
        events = self.recording.stop(); self.record_btn.setText("Start recording")
        for listener in (self.k_listener, self.m_listener):
            try:
                if listener: listener.stop()
            except Exception: pass
        self.k_listener = self.m_listener = None; self.set_steps(self.recording.as_steps()); self.name.setText("Recorded Macro")
    def closeEvent(self, event):
        if self.recording.active: self.stop_recording()
        super().closeEvent(event)
