from __future__ import annotations

"""Capture reviewable UI screenshots for the Windows CI artifact.

This is deliberately a human-review artifact in addition to automated widget tests. It
covers the surfaces that repeatedly regressed during the 2.4 rewrite and all five
supported themes for the main window and Options dialog.
"""

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")
os.environ.setdefault("F3PLUS_SKIP_UPDATE", "1")

from PySide6.QtWidgets import QApplication

from minescript.app import F3Plus, OptionsDialog
from minescript.automation_controller import AutomationControllerDialog
from minescript.result_view import ResultView
from minescript.tool_registry import BY_ID
from minescript.ui_theme import stylesheet
from minescript.villager_workbench import VillagerExplorerDialog
from minescript.workbenches import LootWorkbenchDialog, OperationDialog
from minescript.catalog_ids import BY_NAME


OUT = Path(os.environ.get("F3PLUS_UI_ARTIFACT_DIR", "ui-artifacts"))
OUT.mkdir(parents=True, exist_ok=True)
app = QApplication.instance() or QApplication([])


def settle(rounds: int = 4):
    for _ in range(rounds):
        app.processEvents()


def capture(widget, name: str, width: int, height: int):
    widget.resize(width, height)
    widget.show()
    settle(6)
    pixmap = widget.grab()
    if pixmap.isNull() or pixmap.width() < 400 or pixmap.height() < 300:
        raise RuntimeError(f"UI capture failed for {name}: {pixmap.width()}x{pixmap.height()}")
    path = OUT / f"{name}.png"
    if not pixmap.save(str(path)):
        raise RuntimeError(f"Could not save UI capture {path}")
    widget.hide()
    settle(2)
    return path


def select_mode(dialog: OperationDialog, name: str):
    for index, mode in enumerate(dialog._modes):
        if mode.name == name:
            dialog._select_mode_index(index)
            return
    raise AssertionError(f"Missing operation {name}")


window = F3Plus()
window.stop_hotkeys()
window.link_timer.stop()
window.settings.auto_link_minecraft = False

THEMES = (
    ("chorus", "chorus"),
    ("light", "light"),
    ("cyberpunk", "cyber"),
    ("minecraft", "vanilla"),
    ("custom", "custom"),
)

for theme, label in THEMES:
    window.settings.theme = theme
    app.setStyleSheet(stylesheet(theme, window.settings.custom_palette))
    window.apply_theme()
    capture(window, f"main-{label}", 1480, 900)
    options = OptionsDialog(window.settings, window)
    capture(options, f"options-{label}", 900, 760)
    options.deleteLater()

window.settings.theme = "chorus"
app.setStyleSheet(stylesheet("chorus", window.settings.custom_palette))
window.apply_theme()

build = OperationDialog(BY_ID["build.planner"], window.executor, window.settings, window, preferred_mode="Arch")
select_mode(build, "Arch")
capture(build, "workbench-build-shapes-arch", 1220, 820)
build.close(); build.deleteLater()

automation = AutomationControllerDialog(window, BY_ID["automation.actions"], window.executor, window.settings, preferred_mode="Resource Guard")
capture(automation, "workbench-automation-resource-guard", 1120, 740)
automation.close(); automation.deleteLater()

villagers = VillagerExplorerDialog(window, profession="armorer")
capture(villagers, "workbench-villager-explorer", 1440, 880)
villagers.close(); villagers.deleteLater()

loot = LootWorkbenchDialog(window, "Loot Table Simulator")
settle(10)
capture(loot, "workbench-loot-explorer", 1460, 890)
loot.close(); loot.deleteLater()

village_spec = BY_NAME["Village"][0]
map_result = SimpleNamespace(
    status="ok",
    note="Example CI visualization fixture.",
    data={
        "purpose": "Structure candidate map screenshot fixture",
        "source": "CI fixture",
        "candidate_chunks": [[1, 2], [4, -3], [7, 5]],
        "count": 3,
    },
)
result_map = ResultView()
result_map.set_result(village_spec, map_result, "chorus", window.settings.custom_palette)
capture(result_map, "result-structure-map", 1120, 780)
result_map.deleteLater()

ore_spec = BY_NAME["Ore Distribution"][0]
chart_result = SimpleNamespace(
    status="ok",
    note="Example CI visualization fixture.",
    data={
        "purpose": "Ore distribution chart screenshot fixture",
        "source": "generated-world block states",
        "ore_counts": {"diamond_ore": 48, "iron_ore": 730, "coal_ore": 910, "redstone_ore": 310},
    },
)
result_chart = ResultView()
result_chart.set_result(ore_spec, chart_result, "chorus", window.settings.custom_palette)
capture(result_chart, "result-ore-chart", 1120, 720)
result_chart.deleteLater()

window.close(); window.deleteLater(); settle(4)

files = sorted(OUT.glob("*.png"))
if len(files) < 16:
    raise RuntimeError(f"Expected at least 16 UI review screenshots, created {len(files)}")
print(f"Captured {len(files)} UI review screenshots in {OUT}")
