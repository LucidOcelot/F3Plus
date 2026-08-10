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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from minescript.app import OptionsDialog
from minescript.app25 import F3Plus25 as F3Plus
from minescript.automation_controller import AutomationControllerDialog
from minescript.catalog_ids import BY_NAME
from minescript.enchantment_catalog import loot_enchanted_book_enchantments
from minescript.result_view254 import ResultView
from minescript.tool_registry import BY_ID
from minescript.ui_theme import stylesheet
from minescript.workbenches import LootWorkbenchDialog, MechanicsLabDialog, OperationDialog, RngEnchantingDialog, VillagerExplorerDialog

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
ores = OperationDialog(BY_ID["world.ores"], window.executor, window.settings, window, preferred_mode="Ore Distribution"); select_mode(ores, "Ore Distribution"); capture(ores, "workbench-ore-cave-explorer-seed-source", 1280, 840)
if ores.world_source_mode is not None:
    ores.world_source_mode.setCurrentText("World save"); settle(3); capture(ores, "workbench-ore-cave-explorer-world-save-source", 1280, 840)
ores.close(); ores.deleteLater()
automation = AutomationControllerDialog(window, BY_ID["automation.actions"], window.executor, window.settings, preferred_mode="Resource Guard"); capture(automation, "workbench-automation-resource-guard", 1120, 740); automation.close(); automation.deleteLater()

villagers = VillagerExplorerDialog(window, profession="librarian", mode="Librarian Browser"); villagers.show(); wait_until(lambda: getattr(villagers, "_load_job", None) is None, 10.0)
for row, trade in enumerate(getattr(villagers, "rows", [])):
    if "enchanted_book" in str(getattr(trade, "gives", "")).lower():
        villagers.trade_view.setCurrentIndex(villagers.trade_model.index(row, 0)); villagers.show_selected(); break
settle(4); capture(villagers, "workbench-villager-librarian-enchanted-book", 1460, 900); villagers.close(); villagers.deleteLater()

rng = RngEnchantingDialog(window, window.executor, BY_ID["simulation.rng"]); rng.show(); wait_until(lambda: rng.tabs.count() >= 3, 10.0); capture(rng, "workbench-enchanting-table-dropdown", 1180, 820)
if rng.tabs.count() >= 2:
    rng.tabs.setCurrentIndex(1); settle(4); capture(rng, "workbench-anvil", 1180, 820)
if rng.tabs.count() >= 3:
    rng.tabs.setCurrentIndex(2); settle(4); capture(rng, "workbench-rng-explorer", 1180, 820)
rng.close(); rng.deleteLater()

mechanics = MechanicsLabDialog(window); capture(mechanics, "workbench-mechanics-brewing", 1120, 800)
mechanics_tabs = mechanics.findChild(__import__("PySide6.QtWidgets", fromlist=["QTabWidget"]).QTabWidget)
if mechanics_tabs is not None and mechanics_tabs.count() >= 3:
    mechanics_tabs.setCurrentIndex(1); settle(3); capture(mechanics, "workbench-mechanics-dye", 1120, 800)
    mechanics_tabs.setCurrentIndex(2); settle(3); capture(mechanics, "workbench-horse-breeding-stats", 1120, 800)
mechanics.close(); mechanics.deleteLater()

loot = LootWorkbenchDialog(window, "Loot Table Simulator"); loot.show(); capture(loot, "workbench-loot-loading-or-ready", 1460, 890)
if wait_until(lambda: getattr(loot, "engine", None) is not None and getattr(loot, "tables", None) is not None and loot.tables.count() > 0, 10.0):
    enchanted_row = None
    for row in range(loot.tables.count()):
        table_id = loot.tables.item(row).data(Qt.UserRole)
        try: book_rows = loot_enchanted_book_enchantments(loot.data, table_id)
        except Exception: continue
        if book_rows:
            enchanted_row = row; break
    if enchanted_row is not None:
        loot.tables.setCurrentRow(enchanted_row); loot.load_current(); settle(4); capture(loot, "workbench-loot-enchanted-book", 1460, 890)
    loot.run_sim(100); wait_until(lambda: loot.stats.rowCount() > 0 or "failed" in loot.summary.text().lower(), 10.0)
capture(loot, "workbench-loot-explorer", 1460, 890); loot.close(); loot.deleteLater()

village_spec = BY_NAME["Village"][0]
map_result = SimpleNamespace(status="ok", note="CI visualization fixture.", data={"purpose": "Unordered structure placement candidates", "source": "CI fixture", "candidate_chunks": [[1, 2], [4, -3], [7, 5]], "count": 3})
result_map = ResultView(); result_map.set_result(village_spec, map_result, "chorus", window.settings.custom_palette); capture(result_map, "result-structure-scatter-map-explained", 1120, 780); result_map.deleteLater()

biome_spec = BY_NAME["Biome Diversity Finder"][0]
biome_result = SimpleNamespace(status="ok", note="CI ranked-result fixture.", data={"ranked": [{"position": [-256, -128], "distinct": 6}, {"position": [64, -192], "distinct": 5}, {"position": [192, 96], "distinct": 4}], "samples": 128, "biome_counts": {"Plains": 42, "Forest": 31, "Desert": 20, "Taiga": 18, "Savanna": 17}})
result_biomes = ResultView(); result_biomes.set_result(biome_spec, biome_result, "chorus", window.settings.custom_palette); capture(result_biomes, "result-biome-diversity-ranked-explained", 1180, 800); result_biomes.deleteLater()

cluster_spec = BY_NAME["Structure Cluster Finder"][0]
cluster_result = SimpleNamespace(status="ok", note="CI ranked-result fixture.", data={"ranked": [{"center": [64, -96], "candidate_count": 3, "spread": 46.5}, {"center": [-160, 48], "candidate_count": 2, "spread": 31.0}], "total_candidates": 5, "radius": 256})
result_cluster = ResultView(); result_cluster.set_result(cluster_spec, cluster_result, "chorus", window.settings.custom_palette); capture(result_cluster, "result-structure-cluster-ranked-explained", 1180, 800); result_cluster.deleteLater()

ore_spec = BY_NAME["Ore Distribution"][0]
chart_result = SimpleNamespace(status="ok", note="Generated-world CI fixture.", data={"source": "generated-world block states", "chunks_scanned": 81, "ore_counts": {"diamond_ore": 48, "iron_ore": 730, "coal_ore": 910, "redstone_ore": 310}})
result_chart = ResultView(); result_chart.set_result(ore_spec, chart_result, "chorus", window.settings.custom_palette); capture(result_chart, "result-ore-chart-explained", 1120, 720); result_chart.deleteLater()

sphere_spec = BY_NAME["Sphere"][0]
points = []; r = 5
for y in range(-r, r + 1):
    for z in range(-r, r + 1):
        for x in range(-r, r + 1):
            d = x*x + y*y + z*z
            if (r - .75) ** 2 <= d <= (r + .25) ** 2: points.append([x, y, z])
shape_result = SimpleNamespace(status="ok", note="Layered build CI fixture.", data={"purpose": "Discrete block sphere blueprint", "points": points, "count": len(points)})
result_shape = ResultView(); result_shape.set_result(sphere_spec, shape_result, "chorus", window.settings.custom_palette); capture(result_shape, "result-shape-layer-blueprint", 1120, 780); result_shape.deleteLater()

window.close(); window.deleteLater(); settle(4)
files = sorted(OUT.glob("*.png"))
if len(files) < 29: raise RuntimeError(f"Expected at least 29 UI review screenshots, created {len(files)}")
print(f"Captured {len(files)} UI review screenshots in {OUT}")
