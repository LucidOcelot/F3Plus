from __future__ import annotations
from dataclasses import dataclass
import math
from ..coordinates import Position

@dataclass
class CoordinatePolicy:
    check_interval: float=.65
    tolerance: float=.75
    stuck_samples: int=4
    max_failures: int=4
    min_progress: float=.12
    overshoot_tolerance: float=1.5

@dataclass
class ProgressState:
    samples:int=0
    stalled:int=0
    failures:int=0
    last:Position|None=None

class CoordinateController:
    def __init__(self,engine,policy:CoordinatePolicy|None=None):
        self.engine=engine; self.policy=policy or CoordinatePolicy(); self.state=ProgressState()

    def capture(self):
        try:
            p=self.engine.get_position(); self.state.failures=0; return p
        except Exception:
            self.state.failures+=1
            if self.state.failures>=self.policy.max_failures: raise RuntimeError('Coordinate capture failed repeatedly. Macro paused for recovery.')
            return None

    def move_until(self,target:Position,keys=('w',),axes=('x','z'),max_seconds=120.0):
        start=self.capture()
        if start is None:return False
        for k in keys:self.engine.input.key_down(k)
        elapsed=0.0; previous=start; previous_distance=self._distance(previous,target,axes)
        try:
            while not self.engine.stop_event.is_set() and elapsed<max_seconds:
                if self.engine.wait(self.policy.check_interval):return False
                elapsed+=self.policy.check_interval
                current=self.capture()
                if current is None:continue
                d=self._distance(current,target,axes)
                if d<=self.policy.tolerance:return True
                progress=previous_distance-d
                if progress<self.policy.min_progress:self.state.stalled+=1
                else:self.state.stalled=0
                if self.state.stalled>=self.policy.stuck_samples:
                    raise RuntimeError('No coordinate progress detected. Check alignment or obstruction.')
                # Increasing distance by more than tolerance means the routine passed or moved away from target.
                if d>previous_distance+self.policy.overshoot_tolerance:
                    raise RuntimeError('Coordinate route moved away from the target. Check heading calibration.')
                previous=current; previous_distance=d; self.state.samples+=1
            raise RuntimeError('Coordinate target timed out before arrival.')
        finally:
            for k in keys:self.engine.input.key_up(k)

    def move_distance(self,distance:float,keys=('w',),max_seconds=120.0):
        start=self.capture()
        if start is None:return False
        for k in keys:self.engine.input.key_down(k)
        elapsed=0.0; previous=start; last_distance=0.0
        try:
            while not self.engine.stop_event.is_set() and elapsed<max_seconds:
                if self.engine.wait(self.policy.check_interval):return False
                elapsed+=self.policy.check_interval
                current=self.capture()
                if current is None:continue
                traveled=start.horizontal_distance(current)
                if traveled+ self.policy.tolerance >= float(distance):return True
                step=previous.horizontal_distance(current)
                if step<self.policy.min_progress:self.state.stalled+=1
                else:self.state.stalled=0
                if self.state.stalled>=self.policy.stuck_samples:
                    raise RuntimeError('No coordinate progress detected. Check alignment or obstruction.')
                if traveled + self.policy.overshoot_tolerance < last_distance:
                    raise RuntimeError('Coordinate progress reversed unexpectedly.')
                previous=current; last_distance=traveled; self.state.samples+=1
            raise RuntimeError('Coordinate distance timed out before completion.')
        finally:
            for k in keys:self.engine.input.key_up(k)

    @staticmethod
    def _distance(a,b,axes):
        total=0.0
        for axis in axes: total+=(getattr(b,axis)-getattr(a,axis))**2
        return math.sqrt(total)


def target_along_axis(start:Position,axis:str,distance:float,direction:int=1):
    vals={'x':start.x,'y':start.y,'z':start.z}; vals[axis]+=float(distance)*(1 if direction>=0 else -1)
    return Position(vals['x'],vals['y'],vals['z'],start.yaw,start.pitch)
