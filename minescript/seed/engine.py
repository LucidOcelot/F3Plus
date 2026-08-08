from __future__ import annotations
from dataclasses import dataclass
from .slime import nearest as nearest_slime, nearby as nearby_slime, clusters as slime_clusters

TARGET="26.3-snapshot-5"

@dataclass
class SeedResult:
    title:str
    text:str

class SeedEngine:
    """Local seed calculations with per-feature version support."""
    def __init__(self, seed:int, version:str=TARGET):
        self.seed=int(seed); self.version=version

    def nearest_slime(self,cx,cz):
        return nearest_slime(self.seed,cx,cz)

    def local_slime_report(self,cx,cz,radius=32):
        pts=nearby_slime(self.seed,cx,cz,radius); groups=slime_clusters(set(pts))
        total=(radius*2+1)**2
        return {"chunks":total,"slime":len(pts),"percent":100*len(pts)/total,"largest_cluster":len(groups[0]) if groups else 0,"clusters":groups}

    def unavailable(self, feature:str):
        raise NotImplementedError(
            f"{feature} does not have a verified {self.version} implementation in this build. "
            "No coordinate result was returned."
        )
