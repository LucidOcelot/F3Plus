from __future__ import annotations

import random
from collections import Counter

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTableWidgetItem

from .async_jobs import raise_if_cancelled, start_job
from .loot_workbench import LootWorkbenchDialog as _LootWorkbenchDialog


class LootWorkbenchDialog(_LootWorkbenchDialog):
    """Loot explorer with background, cooperatively cancellable simulation."""

    def __init__(self, *args, **kwargs):
        self._sim_job = None
        super().__init__(*args, **kwargs)
        row = QHBoxLayout(); row.addStretch()
        self.cancel_sim = QPushButton("Cancel simulation"); self.cancel_sim.setEnabled(False); self.cancel_sim.clicked.connect(self._cancel_simulation); row.addWidget(self.cancel_sim)
        layout = self.layout(); layout.insertLayout(max(0, layout.count() - 1), row)

    def _simulate_cancellable(self, table_id: str, pulls: int, seed: int, context: dict):
        pulls = max(1, min(1_000_000, int(pulls))); rng = random.Random(int(seed)); hits = Counter(); totals = Counter(); examples = []
        for index in range(pulls):
            if index % 128 == 0: raise_if_cancelled()
            stacks = self.engine.roll(table_id, rng=rng, context=context); seen = set()
            for stack in stacks:
                totals[stack.item] += stack.count; seen.add(stack.item)
            hits.update(seen)
            if index < 30: examples.append([{"item": stack.item, "count": stack.count, "detail": stack.detail} for stack in stacks])
        raise_if_cancelled(); possible = {row["item"] for row in self.engine.possible_items(table_id)}; possible.update(totals)
        stats = [{"item": item_id, "pulls_with_item": hits[item_id], "observed_hit_rate": hits[item_id] / pulls, "total_items": totals[item_id], "mean_items_per_pull": totals[item_id] / pulls} for item_id in sorted(possible, key=lambda item: (-hits[item], item))]
        return {"table": table_id, "source": self.engine.source, "pulls": pulls, "seed": int(seed), "stats": stats, "examples": examples}

    def run_sim(self, pulls: int):
        if self.engine is None or self._sim_job is not None: return
        item = self.tables.currentItem()
        if item is None: return
        table_id = item.data(Qt.UserRole); seed = self.seed.value(); context = {"killed_by_player": self.killed.isChecked(), "include_contextual_entries": self.contextual.isChecked()}
        self.summary.setText(f"Simulating {pulls:,} pulls in the background…"); self.cancel_sim.setEnabled(True)
        self._sim_job = start_job(lambda: self._simulate_cancellable(table_id, pulls, seed, context), finished=self._simulation_finished, failed=self._simulation_failed, cancelled=self._simulation_cancelled)

    def _simulation_finished(self, result):
        self._sim_job = None; self.cancel_sim.setEnabled(False); rows = result.get("stats", []); self.stats.setRowCount(len(rows))
        for r, row in enumerate(rows):
            first = QTableWidgetItem(self.icons.icon(row["item"], 24) if self.icons else QIcon(), str(row["item"]).removeprefix("minecraft:")); self.stats.setItem(r, 0, first)
            self.stats.setItem(r, 1, QTableWidgetItem(f"{row['observed_hit_rate'] * 100:.3f}%")); self.stats.setItem(r, 2, QTableWidgetItem(f"{row['mean_items_per_pull']:.4f}")); self.stats.setItem(r, 3, QTableWidgetItem(str(row["total_items"])))
        self.summary.setText(f"{result['pulls']:,} pulls • seed {result['seed']} • {len(rows):,} item types observed • {result['source']}")

    def _simulation_failed(self, message: str, _detail: str):
        self._sim_job = None; self.cancel_sim.setEnabled(False); self.summary.setText(f"Simulation failed: {message}")

    def _simulation_cancelled(self):
        self._sim_job = None; self.cancel_sim.setEnabled(False); self.summary.setText("Simulation cancelled. Table and inputs were preserved.")

    def _cancel_simulation(self):
        if self._sim_job is not None: self._sim_job.cancel(); self.cancel_sim.setEnabled(False); self.summary.setText("Cancelling simulation…")

    def closeEvent(self, event):
        if self._sim_job is not None: self._sim_job.cancel()
        super().closeEvent(event)
