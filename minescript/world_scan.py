from __future__ import annotations
import io, struct, zlib, gzip
from pathlib import Path

class NBTReader:
    def __init__(self,data:bytes): self.f=io.BytesIO(data)
    def _read(self,n):
        b=self.f.read(n)
        if len(b)!=n: raise EOFError
        return b
    def b(self):return struct.unpack('>b',self._read(1))[0]
    def ub(self):return self._read(1)[0]
    def s(self):return struct.unpack('>h',self._read(2))[0]
    def i(self):return struct.unpack('>i',self._read(4))[0]
    def q(self):return struct.unpack('>q',self._read(8))[0]
    def f32(self):return struct.unpack('>f',self._read(4))[0]
    def f64(self):return struct.unpack('>d',self._read(8))[0]
    def text(self):
        n=struct.unpack('>H',self._read(2))[0]; return self._read(n).decode('utf-8','replace')
    def payload(self,t):
        if t==1:return self.b()
        if t==2:return self.s()
        if t==3:return self.i()
        if t==4:return self.q()
        if t==5:return self.f32()
        if t==6:return self.f64()
        if t==7:return list(self._read(max(0,self.i())))
        if t==8:return self.text()
        if t==9:
            et=self.ub(); n=max(0,self.i()); return [self.payload(et) for _ in range(n)]
        if t==10:
            d={}
            while True:
                et=self.ub()
                if et==0:return d
                name=self.text(); d[name]=self.payload(et)
        if t==11:return [self.i() for _ in range(max(0,self.i()))]
        if t==12:return [self.q() for _ in range(max(0,self.i()))]
        raise ValueError(f'unsupported NBT tag {t}')
    def root(self):
        t=self.ub()
        if t==0:return {}
        _=self.text(); return self.payload(t)

def parse_nbt(data:bytes): return NBTReader(data).root()

def _region_chunks(path:Path):
    data=path.read_bytes()
    if len(data)<8192:return
    for idx in range(1024):
        off=idx*4; loc=int.from_bytes(data[off:off+3],'big'); sectors=data[off+3]
        if not loc or not sectors:continue
        pos=loc*4096
        if pos+5>len(data):continue
        length=int.from_bytes(data[pos:pos+4],'big'); ctype=data[pos+4]
        payload=data[pos+5:pos+4+length]
        try:
            if ctype==1: raw=gzip.decompress(payload)
            elif ctype==2: raw=zlib.decompress(payload)
            elif ctype==3: raw=payload
            else: continue
            yield idx,parse_nbt(raw)
        except Exception:
            continue

def _walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():yield from _walk(v)
    elif isinstance(obj,list):
        for v in obj:yield from _walk(v)

def _region_dir(root:Path, dimension='overworld'):
    # Java 26.x stores vanilla dimensions under dimensions/minecraft/*; retain legacy paths.
    modern={'overworld':'overworld','nether':'the_nether','end':'the_end'}.get(dimension,dimension)
    p=root/'dimensions'/'minecraft'/modern/'region'
    if p.exists(): return p
    return root/'region' if dimension=='overworld' else (root/'DIM-1'/'region' if dimension=='nether' else root/'DIM1'/'region')

def scan_block_entities(world_path:str|Path, ids=None, dimension='overworld'):
    root=Path(world_path).expanduser()
    region = _region_dir(root, dimension)
    wanted={x.lower() for x in ids} if ids else None
    hits=[];chunks=0;files=0
    if not region.exists():return {'world_path':str(root),'dimension':dimension,'region_dir':str(region),'exists':False,'hits':[],'chunks_scanned':0}
    for rp in sorted(region.glob('r.*.*.mca')):
        files+=1
        for _,nbt in _region_chunks(rp):
            chunks+=1
            for d in _walk(nbt):
                ident=str(d.get('id','')).lower()
                if not ident:continue
                if wanted is None or ident in wanted:
                    if all(k in d for k in ('x','y','z')):
                        hits.append({'id':ident,'x':d['x'],'y':d['y'],'z':d['z'],'region_file':rp.name})
    return {'world_path':str(root),'dimension':dimension,'region_dir':str(region),'exists':True,'region_files':files,'chunks_scanned':chunks,'hits':hits,'count':len(hits)}

def scan_spawners(world_path,dimension='overworld'):
    ids={'minecraft:mob_spawner','mobspawner','minecraft:trial_spawner','minecraft:vault'}
    return scan_block_entities(world_path,ids,dimension)


def _chunk_at(world_path:str|Path, chunk_x:int, chunk_z:int, dimension='overworld'):
    root=Path(world_path).expanduser()
    region_dir = _region_dir(root, dimension)
    rx=chunk_x//32; rz=chunk_z//32
    path=region_dir/f'r.{rx}.{rz}.mca'
    if not path.exists():return None
    local_x=chunk_x-rx*32; local_z=chunk_z-rz*32; wanted=local_x+local_z*32
    for idx,nbt in _region_chunks(path):
        # Prefer explicit xPos/zPos because the region index alone can survive relocation tools.
        if int(nbt.get('xPos', chunk_x))==chunk_x and int(nbt.get('zPos',chunk_z))==chunk_z:
            return nbt
        if idx==wanted:return nbt
    return None


def _palette_name(entry):
    if isinstance(entry,str):return entry
    if isinstance(entry,dict):
        name=entry.get('Name') or entry.get('name') or ''
        props=entry.get('Properties') or entry.get('properties')
        return {'name':name,'properties':props or {}}
    return entry


def _palette_index(data, index:int, palette_len:int, minimum_bits:int):
    if palette_len<=1 or not data:return 0
    bits=max(minimum_bits,(palette_len-1).bit_length())
    per_long=max(1,64//bits)
    li=index//per_long
    if li>=len(data):return 0
    shift=(index%per_long)*bits
    value=int(data[li]) & ((1<<64)-1)
    return (value>>shift)&((1<<bits)-1)


def block_state_at(world_path:str|Path,x:int,y:int,z:int,dimension='overworld'):
    """Read an actual generated Java block state from modern Anvil chunk NBT."""
    cx=x//16; cz=z//16; chunk=_chunk_at(world_path,cx,cz,dimension)
    if chunk is None:return None
    sections=chunk.get('sections') or chunk.get('Sections') or []
    sy=y//16
    sec=next((s for s in sections if int(s.get('Y',10**9))==sy),None)
    if not sec:return {'name':'minecraft:air','properties':{}}
    bs=sec.get('block_states') or sec.get('BlockStates')
    if not isinstance(bs,dict):return {'name':'minecraft:air','properties':{}}
    palette=bs.get('palette') or bs.get('Palette') or []
    if not palette:return {'name':'minecraft:air','properties':{}}
    idx=(y&15)*256+(z&15)*16+(x&15)
    pi=_palette_index(bs.get('data') or bs.get('Data') or [],idx,len(palette),4)
    if pi>=len(palette):return None
    v=_palette_name(palette[pi])
    return v if isinstance(v,dict) else {'name':str(v),'properties':{}}


def biome_at_block(world_path:str|Path,x:int,y:int,z:int,dimension='overworld'):
    """Read the biome palette value stored for a generated block coordinate."""
    cx=x//16; cz=z//16; chunk=_chunk_at(world_path,cx,cz,dimension)
    if chunk is None:return None
    sections=chunk.get('sections') or chunk.get('Sections') or []
    sy=y//16
    sec=next((s for s in sections if int(s.get('Y',10**9))==sy),None)
    if not sec:return None
    bio=sec.get('biomes') or sec.get('Biomes')
    if not isinstance(bio,dict):return None
    palette=bio.get('palette') or bio.get('Palette') or []
    if not palette:return None
    # Modern biomes are stored in 4x4x4 cells per 16^3 section.
    idx=((y&15)//4)*16+((z&15)//4)*4+((x&15)//4)
    pi=_palette_index(bio.get('data') or bio.get('Data') or [],idx,len(palette),1)
    if pi>=len(palette):return None
    v=palette[pi]
    return str(v.get('Name') or v.get('name') or '') if isinstance(v,dict) else str(v)


def structure_starts(world_path:str|Path,dimension='overworld'):
    root=Path(world_path).expanduser()
    region = _region_dir(root, dimension)
    out=[]
    if not region.exists():return out
    for rp in sorted(region.glob('r.*.*.mca')):
        for _,nbt in _region_chunks(rp):
            cx=int(nbt.get('xPos',0));cz=int(nbt.get('zPos',0))
            structures=nbt.get('structures') or nbt.get('Structures') or {}
            starts=structures.get('starts') or structures.get('Starts') or {}
            if not isinstance(starts,dict):continue
            for key,val in starts.items():
                if not isinstance(val,dict):continue
                ident=str(val.get('id',key))
                if ident and ident.lower() not in ('invalid','minecraft:empty'):
                    out.append({'key':str(key),'id':ident,'chunk_x':cx,'chunk_z':cz,'region_file':rp.name})
    return out
