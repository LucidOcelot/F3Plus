from __future__ import annotations

import json
import math
import shutil
from dataclasses import asdict, fields
from pathlib import Path


def install() -> None:
    """Attach parameterized workflows without duplicating the main Qt window.

    F3+'s main window predates several restored feature families. Keeping these
    extensions isolated lets the individual algorithms remain testable without Qt
    while still giving every QA-flagged control a real user-facing configuration path.
    """
    from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

    from .app import F3Plus, ValuesDialog
    from .config import CONFIG_FILE, Keybinds, Settings
    from .control_bindings import normalize_binding
    from .coordinates import Position
    from .gameplay import macros
    from .gameplay.presets import alternating_steps, grid_steps, parallel_row_steps, rectangle_steps, serpentine_steps
    from .qa_features import navigation, portal_tool, rng_tool, villager_tool

    if getattr(F3Plus, "_qa_extensions_installed", False):
        return

    original_init = F3Plus.__init__
    original_run_selected = F3Plus.run_selected
    original_start_macro = F3Plus.start_macro

    def extended_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # MacroEngine's configurable/safety layer must use the same Settings object
        # as the UI and the executor. Re-wrap the backend so all canonical actions
        # pass through BoundInput immediately, including custom Minecraft bindings.
        self.engine.set_settings(self.settings)
        self.engine.set_input(self.input)
        self.engine.set_position_provider(self.capture.capture)
        self.executor.settings = self.settings

    def _values(self, title, schema, summary=""):
        dialog = ValuesDialog(title, schema, self, summary)
        if dialog.exec() != QDialog.Accepted:
            return None
        return dialog.values()

    def _configure_safety(self, name):
        schemas = {
            "Runtime Limit": [("seconds", "Maximum runtime (0 disables)", int(self.settings.runtime_limit_seconds), "int")],
            "Action Counter": [("limit", "Maximum actions/cycles (0 disables)", int(self.settings.action_limit), "int")],
            "Delayed Start": [("delay", "Delay before automation starts", int(self.settings.delayed_start_seconds), "int")],
            "Recovery Attempts": [("attempts", "Coordinate capture recovery attempts", int(self.settings.recovery_attempts), "int")],
            "Restore Hotbar": [("slot", "Restore hotbar slot after natural completion (0 disables)", int(self.settings.restore_hotbar_slot), "int")],
            "Stuck Detection": [
                ("seconds", "No-progress window", float(self.settings.stuck_window_seconds), "float"),
                ("distance", "Minimum displacement per sample", float(self.settings.stuck_min_displacement), "float"),
            ],
            "Focus Loss Stop": [("enabled", "Stop when Minecraft loses focus", bool(self.settings.focus_loss_stop), "bool")],
        }
        schema = schemas.get(name)
        if not schema:
            return False
        values = _values(self, name, schema, "These values are enforced by MacroEngine during automation; they are not informational presets.")
        if values is None:
            return True
        if name == "Runtime Limit":
            self.settings.runtime_limit_seconds = max(0, int(values["seconds"]))
        elif name == "Action Counter":
            self.settings.action_limit = max(0, int(values["limit"]))
        elif name == "Delayed Start":
            self.settings.delayed_start_seconds = max(0, int(values["delay"]))
        elif name == "Recovery Attempts":
            self.settings.recovery_attempts = max(1, int(values["attempts"]))
        elif name == "Restore Hotbar":
            self.settings.restore_hotbar_slot = max(0, min(9, int(values["slot"])))
        elif name == "Stuck Detection":
            self.settings.stuck_window_seconds = max(0.1, float(values["seconds"]))
            self.settings.stuck_min_displacement = max(0.0, float(values["distance"]))
        elif name == "Focus Loss Stop":
            self.settings.focus_loss_stop = bool(values["enabled"])
        self.settings.save()
        self.engine.set_settings(self.settings)
        self.write(f"{name} saved and active for subsequent automation runs.")
        return True

    def _control_bindings(self):
        schema = []
        for field in fields(Keybinds):
            schema.append((field.name, field.name.replace("_", " ").title(), getattr(self.settings.keybinds, field.name), "text"))
        values = _values(self, "Control Bindings", schema, "Map F3+'s canonical Minecraft actions to your in-game controls. Mouse bindings use mouse:left / mouse:right.")
        if values is None:
            return
        for key, value in values.items():
            setattr(self.settings.keybinds, key, normalize_binding(value))
        self.settings.save()
        self.engine.set_settings(self.settings)
        self.engine.set_input(self.input)
        self.engine.set_position_provider(self.capture.capture)
        self.write("Minecraft control bindings saved. All automation now uses the updated mapping.")

    def _settings_file(self, name):
        if name in {"Backup Settings", "Export Profiles"}:
            self.settings.save()
            suggested = "F3Plus-settings-backup.json" if name == "Backup Settings" else "F3Plus-profile.json"
            path, _ = QFileDialog.getSaveFileName(self, name, suggested, "JSON (*.json)")
            if not path:
                return
            shutil.copy2(CONFIG_FILE, Path(path))
            self.write(f"{name} completed: {path}")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import Profiles", "", "JSON (*.json)")
        if not path:
            return
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Imported profile must contain a JSON object")
        backup = CONFIG_FILE.with_name("config.before-import.json")
        self.settings.save()
        shutil.copy2(CONFIG_FILE, backup)
        # Validate by using the same dataclass boundaries as Settings.load().
        allowed = {f.name for f in fields(Settings)}
        for key, value in raw.items():
            if key not in allowed or key == "keybinds":
                continue
            setattr(self.settings, key, value)
        kb = raw.get("keybinds")
        if isinstance(kb, dict):
            allowed_kb = {f.name for f in fields(Keybinds)}
            for key, value in kb.items():
                if key in allowed_kb:
                    setattr(self.settings.keybinds, key, normalize_binding(value))
        self.settings.save()
        self.engine.set_settings(self.settings)
        self.engine.set_input(self.input)
        self.engine.set_position_provider(self.capture.capture)
        self.executor.minecraft_version = self.settings.minecraft_version
        self.executor.settings = self.settings
        self.apply_theme()
        self.write(f"Imported profile from {path}. Previous settings were backed up to {backup}.")

    def _calibration(self, name):
        if name == "Turn Calibration":
            values = _values(self, name, [
                ("degrees", "Observed camera rotation (degrees)", 360.0, "float"),
                ("mouse_units", "Mouse units sent", float(self.settings.turn_units_per_90) * 4.0, "float"),
            ], "Run a known rotation, enter the observed rotation and sent mouse units, and F3+ will persist units-per-90°.")
            if values is None:
                return
            degrees = abs(float(values["degrees"]))
            if degrees < 0.001:
                raise ValueError("Observed rotation must be non-zero")
            self.settings.turn_units_per_90 = max(1, round(abs(float(values["mouse_units"])) * 90.0 / degrees))
            self.settings.save()
            self.engine.set_settings(self.settings)
            self.write(f"Turn calibration saved: {self.settings.turn_units_per_90} mouse units per 90°.")
            return
        values = _values(self, name, [
            ("distance", "Measured blocks travelled", 100.0, "float"),
            ("seconds", "Measured seconds", 20.0, "float"),
        ], "Calibrate the planning speed used by travel-time helpers. Coordinate-aware travel still uses live F3+C position feedback.")
        if values is None:
            return
        seconds = float(values["seconds"])
        if seconds <= 0:
            raise ValueError("Seconds must be positive")
        self.settings.movement_blocks_per_second = max(0.01, float(values["distance"]) / seconds)
        self.settings.save()
        self.write(f"Movement calibration saved: {self.settings.movement_blocks_per_second:.3f} blocks/second.")

    def _trade_operation(self, name):
        schemas = {
            "Trade Search": [("query", "Search text", "", "text"), ("profession", "Profession (blank = all)", "", "text"), ("level", "Level 0-5 (0 = all)", 0, "int")],
            "Trade Comparison": [("query", "Item/trade text", "mending", "text")],
            "Emerald Calculator": [("query", "Trade filter", "", "text"), ("cycles", "Planned uses", 12, "int")],
            "Trade Cycle Calculator": [("query", "Trade filter", "", "text"), ("cycles", "Desired uses", 64, "int")],
            "Librarian Browser": [("query", "Librarian filter", "", "text")],
        }
        values = _values(self, name, schemas[name], "Uses trade definitions extracted from the selected/installed Minecraft version JAR.")
        if values is None:
            return
        result = villager_tool(name, self.settings.minecraft_version, values)
        self.write(name + "\n" + self._format_result(result or {}))
        self._set_detail_view(1)

    def _qa_navigation(self, name):
        if name == "Breadcrumb Simplifier":
            schema = [("points", "Points x,y,z separated by ;", "0,64,0;8,64,0;16,64,0;16,64,8", "text"), ("tolerance", "Simplification tolerance", 2.0, "float")]
        else:
            schema = [
                ("x1", "Start X", self.current_position.x if self.current_position else 0.0, "float"),
                ("y1", "Start Y", self.current_position.y if self.current_position else 64.0, "float"),
                ("z1", "Start Z", self.current_position.z if self.current_position else 0.0, "float"),
                ("stops", "Stops x,y,z,name separated by ;", "80,64,0,A;80,64,80,B;0,64,80,C", "text"),
                ("return_to_start", "Return to start", False, "bool"),
            ]
        values = _values(self, name, schema)
        if values is None:
            return
        result = navigation(name, values)
        self.write(name + "\n" + self._format_result(result or {}))
        self._set_detail_view(1)

    def _qa_portal(self, name):
        schema = [
            ("x", "Overworld target X", 800.0, "float"),
            ("z", "Overworld target Z", -800.0, "float"),
            ("other_x", "Reference/other Nether X", 0.0, "float"),
            ("other_z", "Reference/other Nether Z", 0.0, "float"),
            ("radius", "Candidate radius", 16, "int"),
        ]
        if name == "Multi-Destination Optimizer":
            schema.append(("destinations", "Overworld destinations x,z separated by ;", "800,-800;1600,0;0,1600", "text"))
        values = _values(self, name, schema)
        if values is None:
            return
        result = portal_tool(name, values)
        self.write(name + "\n" + self._format_result(result or {}))
        self._set_detail_view(1)

    def _qa_rng(self, name):
        schema = [("seed", "World/RNG seed", 12345, "text"), ("attempts", "Attempts", 100, "int")]
        if name in {"Decoration RNG", "Decoration RNG Preview", "Feature Placement RNG", "Feature Placement RNG Preview", "Ore Placement Simulator", "Tree Generation Simulator", "Geode Generator", "Geode Placement Simulator", "Trial Chamber Generation", "Structure Placement Preview"}:
            schema += [("cx", "Chunk X", 0, "int"), ("cz", "Chunk Z", 0, "int")]
        if name == "Ore Placement Simulator":
            schema += [("min_y", "Minimum Y", -64, "int"), ("max_y", "Maximum Y", 64, "int")]
        if name in {"Tree Generation Simulator", "Geode Generator", "Geode Placement Simulator"}:
            schema += [("probability", "Configured placement chance", 0.05, "float")]
        values = _values(self, name, schema)
        if values is None:
            return
        result = rng_tool(name, values, self.executor)
        if result is None:
            return original_run_selected(self)
        self.write(name + "\n" + self._format_result(result))
        self._set_detail_view(1)

    def extended_run_selected(self):
        spec = self.selected_spec()
        if spec is None:
            return
        name = spec.name
        try:
            if spec.top == "Safety" and _configure_safety(self, name):
                return
            if name == "Control Bindings":
                return _control_bindings(self)
            if name in {"Backup Settings", "Export Profiles", "Import Profiles"}:
                return _settings_file(self, name)
            if name in {"Turn Calibration", "Movement Calibration"}:
                return _calibration(self, name)
            if name in {"Trade Search", "Trade Comparison", "Emerald Calculator", "Trade Cycle Calculator", "Librarian Browser"}:
                return _trade_operation(self, name)
            if name in {"Multi-stop Route", "Breadcrumb Simplifier"}:
                return _qa_navigation(self, name)
            if name in {"Portal Cost Optimizer", "Portal Reliability Heatmap", "Destination Gate Planner", "Multi-Destination Optimizer"}:
                return _qa_portal(self, name)
            if name in {
                "Loot Table Simulator", "Structure Loot Simulator", "Trial Chamber Loot Simulator", "Trial Spawner Reward Simulator",
                "Archaeology Loot Simulator", "Fishing Loot Simulator", "Piglin Barter Simulator", "Mob Drop Simulator",
                "Decoration RNG", "Decoration RNG Preview", "Feature Placement RNG", "Feature Placement RNG Preview", "Ore Placement Simulator",
                "Tree Generation Simulator", "Geode Generator", "Geode Placement Simulator", "Trial Chamber Generation", "Structure Placement Preview",
            }:
                return _qa_rng(self, name)
            return original_run_selected(self)
        except Exception as exc:
            box = QMessageBox(QMessageBox.Warning, name, str(exc), parent=self)
            box.exec()

    def _aim_and_travel(engine, target: Position, sprint: bool = False):
        current = engine.get_position()
        desired = current.bearing_to(target)
        if current.yaw is not None:
            delta = ((desired - current.yaw + 180.0) % 360.0) - 180.0
            engine.turn_degrees(delta)
            if engine.wait(0.12):
                return
        keys = ("w", "ctrl") if sprint else ("w",)
        policy = engine.coordinate_policy()
        from .gameplay.coordinate_control import CoordinateController
        return CoordinateController(engine, policy).move_until(target, keys=keys)

    def _start_parameterized_macro(self, name):
        if name == "Custom Hold":
            values = _values(self, name, [("binding", "Minecraft action/key", "w", "text")], "Use a canonical key such as w, space, f, mouse:left, or a raw configured key.")
            if values is None:
                return True
            binding = normalize_binding(values["binding"])
            return original_start_macro(self, name) if not binding else self._run_macro_now(name, lambda e: macros.continuous_action(e, held_keys=(binding,))) or True

        if name == "Coordinate Travel":
            p = self.current_position or Position(0, 64, 0)
            values = _values(self, name, [("x", "Target X", p.x + 64, "float"), ("y", "Target Y", p.y, "float"), ("z", "Target Z", p.z, "float"), ("sprint", "Sprint", True, "bool")], "F3+ captures F3+C coordinates, turns toward the target when yaw is available, and stops at the target tolerance.")
            if values is None:
                return True
            target = Position(float(values["x"]), float(values["y"]), float(values["z"]))
            self._run_macro_now(name, lambda e: _aim_and_travel(e, target, bool(values["sprint"])))
            return True

        if name == "Waypoint Travel":
            names = sorted(self.settings.waypoints)
            if not names:
                QMessageBox.information(self, name, "Create a waypoint first.")
                return True
            values = _values(self, name, [("waypoint", "Waypoint", names, "choice"), ("sprint", "Sprint", True, "bool")])
            if values is None:
                return True
            raw = self.settings.waypoints[values["waypoint"]]
            target = Position(float(raw[0]), float(raw[1]), float(raw[2]))
            self._run_macro_now(name, lambda e: _aim_and_travel(e, target, bool(values["sprint"])))
            return True

        if name == "Nether-Assisted Travel":
            values = _values(self, name, [
                ("overworld_x", "Overworld destination X", 8000.0, "float"),
                ("overworld_z", "Overworld destination Z", 8000.0, "float"),
                ("current_dimension", "Current dimension", ["Nether", "Overworld"], "choice"),
                ("y", "Travel Y", 64.0, "float"),
                ("sprint", "Sprint", True, "bool"),
            ], "When travelling in the Nether, the destination is automatically scaled 8:1 from the Overworld target.")
            if values is None:
                return True
            scale = 1.0 / 8.0 if values["current_dimension"] == "Nether" else 1.0
            target = Position(float(values["overworld_x"]) * scale, float(values["y"]), float(values["overworld_z"]) * scale)
            self._run_macro_now(name, lambda e: _aim_and_travel(e, target, bool(values["sprint"])))
            return True

        construction = {"Rectangle", "Filled Rectangle", "Grid", "Rows", "Alternating Pattern", "Perimeter"}
        if name in construction:
            values = _values(self, name, [
                ("rows", "Rows", 8, "int"),
                ("row_seconds", "Row travel seconds", 1.5, "float"),
                ("spacing_seconds", "Row spacing seconds", 0.35, "float"),
            ], "Construction presets now generate distinct paths. Align the player before starting and use Emergency Stop if the build diverges.")
            if values is None:
                return True
            rows = max(1, int(values["rows"]))
            row_seconds = max(0.05, float(values["row_seconds"]))
            spacing = max(0.05, float(values["spacing_seconds"]))
            if name in {"Rectangle", "Perimeter"}:
                steps = rectangle_steps(row_seconds)
            elif name == "Filled Rectangle":
                steps = serpentine_steps(rows, row_seconds, spacing, True)
            elif name == "Grid":
                steps = grid_steps(rows, row_seconds, spacing)
            elif name == "Rows":
                steps = parallel_row_steps(rows, row_seconds, spacing)
            else:
                steps = alternating_steps(rows, row_seconds, spacing)
            self._run_macro_now(name, lambda e: macros.construction_pattern(e, steps, loop=False))
            return True
        return False

    def extended_start_macro(self, name):
        try:
            if _start_parameterized_macro(self, name):
                return
        except Exception as exc:
            QMessageBox.warning(self, name, str(exc))
            return
        return original_start_macro(self, name)

    F3Plus.__init__ = extended_init
    F3Plus.run_selected = extended_run_selected
    F3Plus.start_macro = extended_start_macro
    F3Plus._qa_extensions_installed = True
