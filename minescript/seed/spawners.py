from __future__ import annotations
import math
from itertools import combinations


def _center(group):
    n=len(group);return tuple(sum(p[i] for p in group)/n for i in range(3))


def activation_overlap(points,radius=16.0,max_group=4):
    """Find supplied spawner groups that share a valid activation point.
    The center test is followed by a small coordinate search so groups near the radius edge
    are not rejected only because their arithmetic center is poor.
    """
    pts=[tuple(map(float,p)) for p in points];results=[]
    for n in range(2,min(max_group,len(pts))+1):
        for group in combinations(pts,n):
            c=_center(group);best=(max(math.dist(c,p) for p in group),c)
            # Search integer points around the average. A player can stand at fractional positions,
            # but this gives useful build coordinates and improves the simple-center result.
            bx,by,bz=(round(v) for v in c)
            for x in range(bx-2,bx+3):
                for y in range(by-2,by+3):
                    for z in range(bz-2,bz+3):
                        d=max(math.dist((x+.5,y,z+.5),p) for p in group)
                        if d<best[0]:best=(d,(x+.5,y,z+.5))
            if best[0]<=radius:results.append({'count':n,'max_distance':best[0],'stand':best[1],'spawners':group})
    return sorted(results,key=lambda r:(-r['count'],r['max_distance']))


def clusters_by_size(points,radius=16.0):
    rows=activation_overlap(points,radius)
    return {
        'double':[r for r in rows if r['count']>=2],
        'triple':[r for r in rows if r['count']>=3],
        'quad':[r for r in rows if r['count']>=4],
    }


def nearest_group(origin,groups):
    ox,oy,oz=map(float,origin)
    return min(groups,key=lambda g:math.dist((ox,oy,oz),g['stand'])) if groups else None


def classify_spawner(name:str):
    n=name.lower().strip()
    if 'pig' in n:return 'Pig'
    if 'silverfish' in n:return 'Silverfish'
    if 'blaze' in n:return 'Blaze'
    if 'trial' in n:return 'Trial'
    return 'Dungeon / Other'
