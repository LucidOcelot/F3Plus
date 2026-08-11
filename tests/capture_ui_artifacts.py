from __future__ import annotations

"""Capture reviewable UI screenshots for the Windows CI artifact."""

import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")
os.environ.setdefault("F3PLUS_SKIP_UPDATE", "1")

from PySide6.QtWidgets import QApplication

from minescript.app import OptionsDialog
from minescript.app25 import F3Plus25 as F3Plus
from minescript.automation_controller import AutomationControllerDialog
from minescript.result_view25 import ResultView
from minescript.tool_registry import BY_ID
from minescript.ui_theme import stylesheet
from minescript.workbenches import LootWorkbenchDialog, MechanicsLabDialog, OperationDialog, RngEnchantingDialog, VillagerExplorerDialog
from minescript.catalog_ids import BY_NAME


OUT = Path(os.environ.get("F3PLUS_UI_ARTIFACT_DIR", "ui-artifacts"))
OUT.mkdir(parents=True, exist_ok=True)
app = QApplication.instance() or QApplication([])


def settle(rounds: int = 4, delay: float = 0.0):
    for _ in range(rounds):
        app.processEvents()
        if delay: time.sleep(delay)


def wait_until(predicate, timeout: float = 8.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        settle(2, .02)
        if predicate(): return True
    return False


def capture(widget, name: str, width: int, height: int):
    widget.show(); settle(4, .01); widget.resize(width, height); settle(8, .01)
    if widget.width() < width - 8 or widget.height() < height - 8:
        widget.resize(width, height); settle(4, .01)
    pixmap = widget.grab()
    if pixmap.isNull() or pixmap.width() < 400 or pixmap.height() < 300:
        raise RuntimeError(f"UI capture failed for {name}: {pixmap.width()}x{pixmap.height()}")
    path = OUT / f"{name}.png"
    if not pixmap.save(str(path)): raise RuntimeError(f"Could not save UI capture {path}")
    widget.hide(); settle(2); return path


def select_mode(dialog: OperationDialog, name: str):
    for index, mode in enumerate(dialog._modes):
        if mode.name == name:
            dialog._select_mode_index(index); return
    raise AssertionError(f"Missing operation {name}")


window = F3Plus(); window.stop_hotkeys(); window.link_timer.stop(); window.settings.auto_link_minecraft = False

THEMES = (("chorus", "chorus"), ("light", "light"), ("cyberpunk", "cyber"), ("minecraft", "vanilla"), ("custom", "custom"))
for theme, label in THEMES:
    window.settings.theme = theme; app.setStyleSheet(stylesheet(theme, window.settings.custom_palette)); window.apply_theme(); capture(window, f"main-{label}", 1480, 900)
    options = OptionsDialog(window.settings, window); capture(options, f"options-{label}", 900, 760); options.deleteLater()

window.settings.theme = "chorus"; app.setStyleSheet(stylesheet("chorus", window.settings.custom_palette)); window.apply_theme()

build = OperationDialog(BY_ID["build.planner"], window.executor, window.settings, window, preferred_mode="Arch"); select_mode(build, "Arch"); capture(build, "workbench-build-shapes-arch", 1220, 820); build.close(); build.deleteLater()
structures = OperationDialog(BY_ID["world.structures"], window.executor, window.settings, window, preferred_mode="Structure Finder"); select_mode(structures, "Structure Finder"); capture(structures, "workbench-structure-search-center", 1280, 840); structures.close(); structures.deleteLater()
ores = OperationDialog(BY_ID["world.ores"], window.executor, window.settings, window, preferred_mode="Ore Distribution"); select_mode(ores, "Ore Distribution"); capture(ores, "workbench-ore-cave-explorer", 1280, 840); ores.close(); ores.deleteLater()
automation = AutomationControllerDialog(window, BY_ID["automation.actions"], window.executor, window.settings, preferred_mode="Resource Guard"); capture(automation, "workbench-automation-resource-guard", 1120, 740); automation.close(); automation.deleteLater()

villagers = VillagerExplorerDialog(window, profession="librarian"); capture(villagers, "workbench-villager-librarian-books", 1460, 900); villagers.close(); villagers.deleteLater()

rng = RngEnchantingDialog(window, window.executor, BY_ID["simulation.rng"]); rng.show(); wait_until(lambda: rng.tabs.count() >= 3, 10.0); capture(rng, "workbench-enchanting-table", 1180, 820)
if rng.tabs.count() >= 2:
    rng.tabs.setCurrentIndex(1); settle(4); capture(rng, "workbench-anvil", 1180, 820)
if rng.tabs.count() >= 3:
    rng.tabs.setCurrentIndex(2); settle(4); capture(rng, "workbench-rng-explorer", 1180, 820)
rng.close(); rng.deleteLater()

mechanics = MechanicsLabDialog(window); capture(mechanics, "workbench-mechanics-brewing", 1120, 800)
mechanics_tabs = mechanics.findChild(__import__("PySide6.QtWidgets", fromlist=["QTabWidget"]).QTabWidget)
if mechanics_tabs is not None and mechanics_tabs.count() >= 3:
    mechanics_tabs.setCurrentIndex(1); settle(3); capture(mechanics, "workbench-mechanics-dye", 1120, 800)
    mechanics_tabs.setCurrentIndex(2); settle(3); capture(mechanics, "workbench-mechanics-stat-breeding", 1120, 800)
mechanics.close(); mechanics.deleteLater()

loot = LootWorkbenchDialog(window, "Loot Table Simulator"); loot.show(); capture(loot, "workbench-loot-loading-or-ready", 1460, 890)
if wait_until(lambda: getattr(loot, "engine", None) is not None and getattr(loot, "tables", None) is not None and loot.tables.count() > 0, 10.0):
    enchanted_row = -1
    for row in range(loot.tables.count()):
        table_id = loot.tables.item(row).data(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.UserRole)
        if any(str(item.get("item", "")).endswith("enchanted_book") for item in loot.engine.possible_items(table_id)):
            enchanted_row = row; break
    if enchanted_row >= 0:
        loot.tables.setCurrentRow(enchanted_row); settle(4); capture(loot, "workbench-loot-enchanted-book-rarity", 1460, 890)
    loot.run_sim(100); wait_until(lambda: loot.stats.rowCount() > 0 or "failed" in loot.summary.text().lower(), 10.0)
capture(loot, "workbench-loot-explorer", 1460, 890); loot.close(); loot.deleteLater()

village_spec = BY_NAME["Village"][0]
map_result = SimpleNamespace(status="ok", note="", data={"purpose": "Structure placement candidates", "source": "CI fixture", "candidate_chunks": [[1, 2], [4, -3], [7, 5]], "count": 3})
result_map = ResultView(); result_map.set_result(village_spec, map_result, "chorus", window.settings.custom_palette); capture(result_map, "result-structure-scatter-map", 1120, 780); result_map.deleteLater()

cluster_spec = BY_NAME["Structure Cluster Finder"][0]
cluster_result = SimpleNamespace(status="ok", note="", data={"candidate_count": 23, "candidates": [{"x": x * 16, "z": z * 16, "candidate_count": 3 if x < 7 else 2} for x, z in [(0,0),(1,2),(2,1),(3,5),(4,3),(5,8),(6,5),(7,9),(8,6),(9,10),(10,7)]]})
result_cluster = ResultView(); result_cluster.set_result(cluster_spec, cluster_result, "chorus", window.settings.custom_palette); capture(result_cluster, "result-structure-cluster-summary", 1120, 780); result_cluster.deleteLater()

biome_spec = BY_NAME["Biome Diversity Finder"][0]
biome_result = SimpleNamespace(status="ok", note="", data={"biome_counts": {"plains": 42, "forest": 31, "river": 18, "meadow": 12, "birch_forest": 9, "savanna": 6}, "samples": [{"x": x * 32, "z": z * 32, "distinct": 6} for x in range(8) for z in range(8)]})
result_biome = ResultView(); result_biome.set_result(biome_spec, biome_result, "chorus", window.settings.custom_palette); capture(result_biome, "result-biome-diversity-summary", 1120, 780); result_biome.deleteLater()

ore_spec = BY_NAME["Ore Distribution"][0]
chart_result = SimpleNamespace(status="ok", note="", data={"purpose": "Ore distribution by observed block type", "source": "generated-world block states", "ore_counts": {"diamond_ore": 48, "iron_ore": 730, "coal_ore": 910, "redstone_ore": 310}})
result_chart = ResultView(); result_chart.set_result(ore_spec, chart_result, "chorus", window.settings.custom_palette); capture(result_chart, "result-ore-chart", 1120, 720); result_chart.deleteLater()

sphere_spec = BY_NAME["Sphere"][0]; points = []; r = 5
for y in range(-r, r + 1):
    for z in range(-r, r + 1):
        for x in range(-r, r + 1):
            d = x*x + y*y + z*z
            if (r - .75) ** 2 <= d <= (r + .25) ** 2: points.append([x, y, z])
shape_result = SimpleNamespace(status="ok", note="", data={"purpose": "Discrete block sphere blueprint", "points": points, "count": len(points)})
result_shape = ResultView(); result_shape.set_result(sphere_spec, shape_result, "chorus", window.settings.custom_palette); capture(result_shape, "result-shape-layer-blueprint", 1120, 780); result_shape.deleteLater()

window.close(); window.deleteLater(); settle(4)
files = sorted(OUT.glob("*.png"))
if len(files) < 28: raise RuntimeError(f"Expected at least 28 UI review screenshots, created {len(files)}")
print(f"Captured {len(files)} UI review screenshots in {OUT}")
