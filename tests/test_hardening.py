import time
import unittest

from minescript.config import Keybinds, Settings
from minescript.control_bindings import BoundInput
from minescript.macro_engine import MacroEngine
from minescript.world.versioning import UnsupportedMinecraftVersion, cubiomes_enum_for_version


class FakeInput:
    def __init__(self):
        self.events = []

    def key_down(self, key): self.events.append(("down", key))
    def key_up(self, key): self.events.append(("up", key))
    def mouse_down(self, button): self.events.append(("mdown", button))
    def mouse_up(self, button): self.events.append(("mup", button))
    def tap(self, key, hold=0.05): self.events.append(("tap", key))
    def click(self, button, hold=0.05): self.events.append(("click", button))
    def chord(self, *keys, hold=0.04): self.events.append(("chord", keys))
    def move_relative(self, dx, dy=0): self.events.append(("move", dx, dy))
    def release_all(self): self.events.append(("release",))


class HardeningTests(unittest.TestCase):
    def test_custom_movement_binding(self):
        backend = FakeInput()
        bound = BoundInput(backend, Keybinds(forward="up"))
        bound.key_down("w")
        self.assertIn(("down", "up"), backend.events)

    def test_attack_can_be_keyboard_bound(self):
        backend = FakeInput()
        bound = BoundInput(backend, Keybinds(attack="g"))
        bound.mouse_down("left")
        self.assertIn(("down", "g"), backend.events)

    def test_runtime_limit_releases_input(self):
        backend = FakeInput()
        settings = Settings(runtime_limit_seconds=1)
        engine = MacroEngine(backend, settings=settings)
        engine.start("guard", lambda e: e.wait(5))
        engine.thread.join(timeout=2)
        self.assertFalse(engine.status.running)
        self.assertIn(("release",), backend.events)
        self.assertIn("Runtime limit", engine.status.message)

    def test_snapshot_is_not_silently_mapped_to_old_cubiomes(self):
        with self.assertRaises(UnsupportedMinecraftVersion):
            cubiomes_enum_for_version("26.3 Snapshot 7")

    def test_known_cubiomes_mapping(self):
        self.assertEqual(cubiomes_enum_for_version("1.21.3"), 27)


if __name__ == "__main__":
    unittest.main()
