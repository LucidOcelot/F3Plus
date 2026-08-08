from __future__ import annotations
import math


def chunk_of(x:float,z:float):return math.floor(x/16),math.floor(z/16)
def region_of_chunk(cx:int,cz:int):return math.floor(cx/32),math.floor(cz/32)
def local_in_chunk(x:float,z:float):
    bx,bz=math.floor(x),math.floor(z);return bx%16,bz%16

def nearest_chunk_border(x:float,z:float):
    bx,bz=math.floor(x),math.floor(z);lx,lz=bx%16,bz%16
    distances={'west':lx,'east':15-lx,'north':lz,'south':15-lz}
    side=min(distances,key=distances.get)
    return {'side':side,'blocks':distances[side],'all':distances}

def portal_pair(x:float,z:float,from_dimension:str='Overworld'):
    if from_dimension.lower().startswith('over'):
        return {'dimension':'Nether','x':x/8,'z':z/8}
    return {'dimension':'Overworld','x':x*8,'z':z*8}

def map_coverage(scale:int=0):
    s=max(0,min(4,int(scale)));side=128*(2**s)
    return {'scale':s,'side_blocks':side,'area_blocks':side*side}

def centered_map_bounds(x:float,z:float,scale:int=0):
    info=map_coverage(scale);side=info['side_blocks']
    # Map centers lie on scale-specific grids. This gives a practical planning cell, not a map-id lookup.
    cx=(math.floor(x/side)*side)+(side//2);cz=(math.floor(z/side)*side)+(side//2)
    return {**info,'center':(cx,cz),'bounds':(cx-side//2,cz-side//2,cx+side//2-1,cz+side//2-1)}

def project_materials(width:int,length:int,height:int=1,fill:bool=True):
    w,l,h=max(1,int(width)),max(1,int(length)),max(1,int(height))
    blocks=w*l*h if fill else (2*w+2*l-4)*h
    return {'blocks':blocks,'stacks':blocks//64,'remainder':blocks%64,'shulkers':math.ceil(blocks/(64*27))}
