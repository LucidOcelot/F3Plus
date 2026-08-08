from __future__ import annotations
from dataclasses import dataclass
import math
import re
import time

@dataclass(frozen=True)
class Position:
    x: float
    y: float
    z: float
    yaw: float | None = None
    pitch: float | None = None

    @property
    def block(self):
        return (math.floor(self.x), math.floor(self.y), math.floor(self.z))

    @property
    def chunk(self):
        bx, _, bz = self.block
        return (math.floor(bx / 16), math.floor(bz / 16))

    @property
    def region(self):
        cx, cz = self.chunk
        return (math.floor(cx / 32), math.floor(cz / 32))

    def horizontal_distance(self, other: "Position") -> float:
        return math.hypot(other.x - self.x, other.z - self.z)

    def distance(self, other: "Position") -> float:
        return math.sqrt((other.x-self.x)**2 + (other.y-self.y)**2 + (other.z-self.z)**2)


    def sister(self, dimension: str = "Overworld") -> "Position":
        d=dimension.strip().lower()
        if d.startswith("over"):
            return Position(self.x/8, self.y, self.z/8, self.yaw, self.pitch)
        if d.startswith("nether"):
            return Position(self.x*8, self.y, self.z*8, self.yaw, self.pitch)
        raise ValueError("Sister portal conversion is only defined between Overworld and Nether.")
    def bearing_to(self, other: "Position") -> float:
        # Minecraft yaw: 0 south, 90 west, 180 north, -90 east.
        dx, dz = other.x-self.x, other.z-self.z
        return math.degrees(math.atan2(-dx, dz))

TP_RE = re.compile(r"(?:/execute\s+in\s+\S+\s+run\s+)?/tp\s+@s\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?))?", re.I)
NUM_RE = re.compile(r"(-?\d+(?:\.\d+)?)")

class CoordinateCapture:
    def __init__(self, input_engine, settings):
        self.input = input_engine
        self.settings = settings

    def parse(self, text: str) -> Position:
        m = TP_RE.search(text.strip())
        if m:
            nums = [float(v) if v is not None else None for v in m.groups()]
            return Position(nums[0], nums[1], nums[2], nums[3], nums[4])
        vals = [float(v) for v in NUM_RE.findall(text)]
        if len(vals) >= 3:
            return Position(vals[0], vals[1], vals[2], vals[3] if len(vals)>3 else None, vals[4] if len(vals)>4 else None)
        raise ValueError("Clipboard does not contain a valid Minecraft location.")

    def capture(self) -> Position:
        import pyperclip
        before = pyperclip.paste()
        # Send the configured copy-location chord as a short press.
        self.input.chord("f3", "c", hold=.03)
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            now = pyperclip.paste()
            if now != before and now.strip():
                return self.parse(now)
            time.sleep(.03)
        # Accept an unchanged clipboard when it already contains a valid location.
        return self.parse(pyperclip.paste())
