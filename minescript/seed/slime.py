from .java_rng import JavaRandom


def _i32(value: int) -> int:
    value = int(value) & 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def is_slime_chunk(seed:int,cx:int,cz:int)->bool:
    """Match Java Edition's legacy slime-chunk predicate exactly.

    Minecraft's expression performs several multiplications as Java ``int``
    before widening to ``long``. Those 32-bit intermediate overflows are
    intentional compatibility behavior and must be reproduced in Python.
    """
    cx=int(cx); cz=int(cz)
    x2_term = _i32(_i32(_i32(cx * cx) * 0x4C1906))
    x_term  = _i32(cx * 0x5AC0DB)
    z2 = _i32(cz * cz)
    z_term  = _i32(cz * 0x5F24F)
    # z^2 is widened before multiplying by 0x4307a7L in the Java expression.
    s = (int(seed) + x2_term + x_term + z2 * 0x4307A7 + z_term) ^ 0x3AD8025F
    return JavaRandom(s).next_int(10)==0


def nearby(seed:int,cx:int,cz:int,radius:int=32):
    return [(x,z) for z in range(cz-radius,cz+radius+1) for x in range(cx-radius,cx+radius+1) if is_slime_chunk(seed,x,z)]


def nearest(seed:int,cx:int,cz:int,max_radius:int=256):
    if is_slime_chunk(seed,cx,cz): return cx,cz,0
    for r in range(1,max_radius+1):
        for x in range(cx-r,cx+r+1):
            for z in (cz-r,cz+r):
                if is_slime_chunk(seed,x,z): return x,z,max(abs(x-cx),abs(z-cz))
        for z in range(cz-r+1,cz+r):
            for x in (cx-r,cx+r):
                if is_slime_chunk(seed,x,z): return x,z,max(abs(x-cx),abs(z-cz))
    return None


def clusters(chunks:set[tuple[int,int]]):
    seen=set(); out=[]
    for p in chunks:
        if p in seen: continue
        stack=[p]; group=[]; seen.add(p)
        while stack:
            q=stack.pop(); group.append(q)
            x,z=q
            for n in ((x+1,z),(x-1,z),(x,z+1),(x,z-1)):
                if n in chunks and n not in seen: seen.add(n); stack.append(n)
        out.append(group)
    return sorted(out,key=len,reverse=True)
