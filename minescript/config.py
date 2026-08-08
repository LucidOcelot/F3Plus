from __future__ import annotations
from dataclasses import dataclass, asdict, field, fields
from pathlib import Path
from datetime import datetime
import json
import platform
import shutil

from .ui_theme import DEFAULT_CUSTOM_PALETTE, COLOR_KEYS

APP_DIR = Path.home() / ".f3plus"
CONFIG_FILE = APP_DIR / "config.json"
LEGACY_APP_DIR = Path.home() / ".minescript"
LEGACY_CONFIG_FILE = LEGACY_APP_DIR / "config.json"


@dataclass
class Keybinds:
    forward: str = "w"
    back: str = "s"
    left: str = "a"
    right: str = "d"
    jump: str = "space"
    sneak: str = "shift"
    sprint: str = "ctrl"
    swap_hands: str = "f"
    inventory: str = "e"


def _default_custom_palette() -> dict[str, str]:
    return dict(DEFAULT_CUSTOM_PALETTE)


@dataclass
class Settings:
    minecraft_version: str = "26.3-snapshot-5"
    edition: str = "Java"
    dimension: str = "Overworld"
    seed: str = ""
    keybinds: Keybinds = field(default_factory=Keybinds)
    coord_copy_hotkey: str = "ctrl+alt+c"
    stop_hotkey: str = "ctrl+alt+s"
    toggle_hotkey: str = "ctrl+alt+space"
    coordinate_capture_delay_ms: int = 120
    movement_check_ms: int = 750
    input_mode: str = "auto"
    minecraft_window_title: str = "Minecraft"
    platform: str = field(default_factory=platform.system)
    waypoints: dict = field(default_factory=dict)
    portals: list = field(default_factory=list)

    auto_link_minecraft: bool = True
    allow_focus_switch: bool = True
    confirm_focus_switch: bool = True
    restore_previous_focus: bool = True
    focus_switch_delay_ms: int = 350
    manual_focus_delay_seconds: int = 3
    theme: str = "chorus"
    appearance_schema: int = 2
    custom_palette: dict[str, str] = field(default_factory=_default_custom_palette)
    custom_theme_use_minecraft_assets: bool = False
    safe_mode: bool = False
    favorites: list[str] = field(default_factory=list)
    recent_tools: list[str] = field(default_factory=list)
    recent_limit: int = 12

    @classmethod
    def load(cls) -> "Settings":
        APP_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE.exists() and LEGACY_CONFIG_FILE.exists():
            try:
                shutil.copy2(LEGACY_CONFIG_FILE, CONFIG_FILE)
            except OSError:
                pass
        if not CONFIG_FILE.exists():
            obj = cls(); obj.save(); return obj
        try:
            raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("Configuration root must be an object")
            allowed = {f.name for f in fields(cls)}
            raw = {k: v for k, v in raw.items() if k in allowed}

            kb = raw.get("keybinds", {})
            if isinstance(kb, dict):
                kb_allowed = {f.name for f in fields(Keybinds)}
                raw["keybinds"] = Keybinds(**{k: v for k, v in kb.items() if k in kb_allowed})
            else:
                raw["keybinds"] = Keybinds()

            # One-time appearance migration for configurations written before the
            # current palette schema. The former accidental default moves to Chorus.
            schema = int(raw.get("appearance_schema", 0) or 0)
            theme = str(raw.get("theme", "chorus"))
            if schema < 2:
                if theme in {"minecraft", "royal", "blurple"}:
                    theme = "chorus"
                elif theme == "light":
                    theme = "light"
            if theme not in {"chorus", "light", "cyberpunk", "minecraft", "custom"}:
                theme = "chorus"
            raw["theme"] = theme
            raw["appearance_schema"] = 2

            custom = raw.get("custom_palette", {})
            merged = _default_custom_palette()
            if isinstance(custom, dict):
                for key in COLOR_KEYS:
                    value = custom.get(key)
                    if isinstance(value, str) and value.strip():
                        merged[key] = value.strip()
            raw["custom_palette"] = merged

            obj = cls(**raw)
            obj.favorites = list(dict.fromkeys(str(x) for x in obj.favorites))
            obj.recent_tools = list(dict.fromkeys(str(x) for x in obj.recent_tools))[: max(1, int(obj.recent_limit))]
            if obj.input_mode not in {"auto", "targeted", "background", "standard", "foreground"}:
                obj.input_mode = "auto"
            return obj
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            try:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                shutil.copy2(CONFIG_FILE, CONFIG_FILE.with_name(f"config.invalid-{stamp}.json"))
            except Exception:
                pass
            obj = cls(); obj.save(); return obj

    def save(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
        tmp.replace(CONFIG_FILE)

    def remember_tool(self, feature_id: str) -> None:
        fid = str(feature_id)
        self.recent_tools = [x for x in self.recent_tools if x != fid]
        self.recent_tools.insert(0, fid)
        del self.recent_tools[max(1, int(self.recent_limit)):]
        self.save()

    def toggle_favorite(self, feature_id: str) -> bool:
        fid = str(feature_id)
        if fid in self.favorites:
            self.favorites = [x for x in self.favorites if x != fid]
            active = False
        else:
            self.favorites.append(fid)
            active = True
        self.save()
        return active
