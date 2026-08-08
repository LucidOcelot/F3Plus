from __future__ import annotations
from dataclasses import dataclass
import re
from .catalog import FEATURES
from .seed.policy import validate_feature

@dataclass(frozen=True)
class FeatureSpec:
    id: str
    top: str
    submenu: str
    name: str


def _slug(value: str) -> str:
    value = value.lower().replace('&','and').replace('/','-')
    value = re.sub(r'[^a-z0-9]+','-',value).strip('-')
    return value or 'feature'


def feature_specs():
    out=[]
    seen=set()
    for top, groups in FEATURES.items():
        for submenu, names in groups.items():
            for index, name in enumerate(names):
                validate_feature(name, submenu, top)
                base=f'{_slug(top)}.{_slug(submenu)}.{_slug(name)}'
                fid=base
                n=2
                while fid in seen:
                    fid=f'{base}.{n}'; n+=1
                seen.add(fid)
                out.append(FeatureSpec(fid,top,submenu,name))
    return out

SPECS=feature_specs()
BY_ID={s.id:s for s in SPECS}
BY_PATH={(s.top,s.submenu,s.name):s for s in SPECS}
BY_NAME={}
for s in SPECS: BY_NAME.setdefault(s.name,[]).append(s)
