from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from functools import lru_cache
import json, os, zipfile

LEVEL_NAMES = {1:'Novice',2:'Apprentice',3:'Journeyman',4:'Expert',5:'Master'}
PROFESSIONS = ['armorer','butcher','cartographer','cleric','farmer','fisherman','fletcher','leatherworker','librarian','mason','shepherd','toolsmith','weaponsmith']

@dataclass
class Trade:
    profession: str
    level: int
    name: str
    wants: str
    gives: str
    additional_wants: str | None = None
    max_uses: float | None = None
    xp: float | None = None
    source: str = 'installed-version'
    raw_path: str = ''
    def dict(self):
        d=asdict(self); d['level_name']=LEVEL_NAMES.get(self.level,str(self.level)); return d

def minecraft_roots() -> list[Path]:
    roots=[]
    home=Path.home()
    appdata=os.getenv('APPDATA')
    if appdata: roots.append(Path(appdata)/'.minecraft')
    roots += [home/'.minecraft', home/'Library'/'Application Support'/'minecraft']
    out=[]
    for p in roots:
        try:
            if p.exists() and p not in out: out.append(p)
        except OSError: pass
    return out

def installed_versions() -> dict[str, Path]:
    out={}
    for root in minecraft_roots():
        vd=root/'versions'
        if not vd.exists(): continue
        for folder in vd.iterdir():
            if not folder.is_dir(): continue
            jar=folder/(folder.name+'.jar')
            if jar.exists(): out[folder.name]=jar
    return dict(sorted(out.items()))

def _count_text(obj) -> str:
    if obj is None: return '1'
    if isinstance(obj,(int,float)): return str(obj)
    if isinstance(obj,dict):
        if 'value' in obj: return str(obj['value'])
        if obj.get('type','').endswith('constant'): return str(obj.get('value',obj.get('constant',1)))
        lo=obj.get('min_inclusive',obj.get('min',obj.get('min_value')))
        hi=obj.get('max_inclusive',obj.get('max',obj.get('max_value')))
        if lo is not None or hi is not None: return f'{lo if lo is not None else "?"}-{hi if hi is not None else "?"}'
    return json.dumps(obj,separators=(',',':'))

def _item_text(obj) -> str:
    if not obj: return ''
    if isinstance(obj,str): return obj.removeprefix('minecraft:')
    if isinstance(obj,dict):
        iid=obj.get('id',obj.get('item',obj.get('items','?')))
        if isinstance(iid,list): iid='|'.join(map(str,iid))
        count=_count_text(obj.get('count',1))
        return f'{count} {str(iid).removeprefix("minecraft:")}'
    return str(obj)

def _parse_path(path: str):
    parts=path.split('/')
    try:
        i=parts.index('villager_trade'); profession=parts[i+1]; level=int(parts[i+2]); name=Path(parts[-1]).stem
        return profession,level,name
    except Exception: return None

@lru_cache(maxsize=8)
def _load_trades_cached(path_text: str, mtime_ns: int, size: int) -> tuple[Trade, ...]:
    jar=Path(path_text)
    rows=[]
    with zipfile.ZipFile(jar) as z:
        names=[n for n in z.namelist() if '/villager_trade/' in n and n.endswith('.json') and '/datapacks/trade_rebalance/' not in n]
        # If only experimental/rebalance files exist, include those as a second pass.
        if not names: names=[n for n in z.namelist() if '/villager_trade/' in n and n.endswith('.json')]
        for path in names:
            info=_parse_path(path)
            if not info: continue
            profession,level,name=info
            if profession not in PROFESSIONS: continue
            try: data=json.loads(z.read(path))
            except Exception: continue
            rows.append(Trade(
                profession=profession, level=level, name=name.replace('_',' '),
                wants=_item_text(data.get('wants')), gives=_item_text(data.get('gives')),
                additional_wants=_item_text(data.get('additional_wants')) or None,
                max_uses=data.get('max_uses'), xp=data.get('xp'), raw_path=path
            ))
    return tuple(sorted(rows,key=lambda t:(t.profession,t.level,t.name)))

def load_trades_from_jar(jar: Path) -> list[Trade]:
    """Load one version JAR, caching by file revision rather than just its path."""
    st=jar.stat()
    return list(_load_trades_cached(str(jar.resolve()), int(st.st_mtime_ns), int(st.st_size)))

def load_for_version(version: str | None=None) -> tuple[list[Trade], str]:
    versions=installed_versions()
    if version and version in versions:
        return load_trades_from_jar(versions[version]), version
    # Prefer exact-looking 26.3 snapshot, then newest lexicographically as a local fallback.
    candidates=[v for v in versions if '26.3' in v.lower()]
    pick=(sorted(candidates)[-1] if candidates else (sorted(versions)[-1] if versions else None))
    if pick: return load_trades_from_jar(versions[pick]), pick
    return [], 'not-installed'

def search(trades:list[Trade], text='', profession=None, level=None) -> list[Trade]:
    q=text.strip().lower(); out=[]
    for t in trades:
        if profession and t.profession!=profession.lower(): continue
        if level and t.level!=int(level): continue
        hay=' '.join([t.name,t.wants,t.gives,t.additional_wants or '',t.profession]).lower()
        if q and q not in hay: continue
        out.append(t)
    return out

def grouped(trades:list[Trade]):
    out={}
    for p in PROFESSIONS:
        out[p]={LEVEL_NAMES[i]:[] for i in range(1,6)}
    for t in trades:
        out.setdefault(t.profession,{LEVEL_NAMES[i]:[] for i in range(1,6)})[LEVEL_NAMES.get(t.level,str(t.level))].append(t.dict())
    return out
