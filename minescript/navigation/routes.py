from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Iterable

@dataclass(frozen=True)
class Point:
    x: float
    y: float
    z: float
    name: str = ""

    @property
    def xz(self):
        return self.x, self.z


def horizontal_distance(a: Point, b: Point) -> float:
    return math.hypot(b.x-a.x, b.z-a.z)


def distance(a: Point, b: Point) -> float:
    return math.dist((a.x,a.y,a.z),(b.x,b.y,b.z))


def bearing(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(-(b.x-a.x), b.z-a.z))


def cardinal_from_bearing(yaw: float) -> str:
    y=((yaw+180)%360)-180
    if -45 <= y < 45:return 'South'
    if 45 <= y < 135:return 'West'
    if y >= 135 or y < -135:return 'North'
    return 'East'


def route_report(a: Point,b: Point) -> dict:
    dx,dy,dz=b.x-a.x,b.y-a.y,b.z-a.z
    yaw=bearing(a,b)
    return {
        'from':a,'to':b,'dx':dx,'dy':dy,'dz':dz,
        'horizontal':horizontal_distance(a,b),'distance':distance(a,b),
        'bearing':yaw,'cardinal':cardinal_from_bearing(yaw),
    }


def nether_equivalent(a: Point,b: Point) -> dict:
    direct=horizontal_distance(a,b)
    nether=direct/8.0
    return {'overworld_distance':direct,'nether_horizontal':nether,'saved_horizontal':max(0.0,direct-nether)}


def nearest(origin: Point,points: Iterable[Point]) -> Point|None:
    pts=list(points)
    return min(pts,key=lambda p:horizontal_distance(origin,p)) if pts else None


def greedy_route(origin: Point,points: Iterable[Point],return_to_start: bool=False):
    remaining=list(points); cur=origin; ordered=[]; total=0.0
    while remaining:
        nxt=min(remaining,key=lambda p:horizontal_distance(cur,p))
        total+=horizontal_distance(cur,nxt);ordered.append(nxt);remaining.remove(nxt);cur=nxt
    if return_to_start and ordered:total+=horizontal_distance(cur,origin)
    return {'distance':total,'route':ordered,'return_to_start':return_to_start}


def breadcrumb_simplify(points: Iterable[Point],minimum_spacing: float=8.0):
    pts=list(points)
    if not pts:return []
    out=[pts[0]]
    for p in pts[1:]:
        if horizontal_distance(out[-1],p)>=minimum_spacing:out.append(p)
    if out[-1]!=pts[-1]:out.append(pts[-1])
    return out
