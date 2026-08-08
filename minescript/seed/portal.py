from __future__ import annotations
from dataclasses import dataclass
import math
from collections import defaultdict

@dataclass(frozen=True)
class Portal:
    name:str
    dimension:str
    x:float
    y:float
    z:float
    active:bool=True

    @property
    def point(self):return self.x,self.y,self.z


def _dim_name(name:str):
    return 'Nether' if name.lower().startswith('nether') else 'Overworld'


def ideal_target(entry:Portal):
    if _dim_name(entry.dimension)=='Overworld':
        return 'Nether',entry.x/8.0,entry.y,entry.z/8.0
    return 'Overworld',entry.x*8.0,entry.y,entry.z*8.0


def score(entry:Portal,exit:Portal):
    dim,ix,iy,iz=ideal_target(entry)
    if _dim_name(exit.dimension)!=dim or not exit.active:return math.inf
    return math.dist((ix,iy,iz),(exit.x,exit.y,exit.z))


def rank(entry:Portal,exits:list[Portal],max_distance:float|None=None):
    rows=[]
    for p in exits:
        if p is entry or not p.active:continue
        d=score(entry,p)
        if math.isfinite(d) and (max_distance is None or d<=max_distance):rows.append((d,p))
    return sorted(rows,key=lambda x:(x[0],x[1].y,x[1].name))


def selected_exit(entry:Portal,exits:list[Portal],max_distance:float|None=None):
    rows=rank(entry,exits,max_distance)
    return rows[0] if rows else None


def routing_margin(entry:Portal,exits:list[Portal],max_distance:float|None=None):
    rows=rank(entry,exits,max_distance)
    if not rows:return {'selected':None,'margin':math.inf,'ranked':[]}
    margin=(rows[1][0]-rows[0][0]) if len(rows)>1 else math.inf
    return {'selected':rows[0][1],'selected_distance':rows[0][0],'margin':margin,'ranked':rows}


def link_matrix(portals:list[Portal],max_distance:float|None=None):
    out=[]
    for p in portals:
        r=routing_margin(p,portals,max_distance)
        out.append({'entry':p.name,'exit':r['selected'].name if r['selected'] else None,'distance':r.get('selected_distance'),'margin':r['margin']})
    return out


def directed_graph(portals:list[Portal],max_distance:float|None=None):
    return {row['entry']:row['exit'] for row in link_matrix(portals,max_distance) if row['exit'] is not None}


def cycles(portals:list[Portal],max_distance:float|None=None):
    graph=directed_graph(portals,max_distance);found=[];seen=set()
    for start in graph:
        order=[];pos={};cur=start
        while cur in graph and cur not in seen:
            if cur in pos:
                cyc=order[pos[cur]:]
                key=tuple(sorted(cyc))
                if key not in {tuple(sorted(c)) for c in found}:found.append(cyc)
                break
            pos[cur]=len(order);order.append(cur);cur=graph[cur]
        seen.update(order)
    return found


def validate_intended(portals:list[Portal],intended:dict[str,str],minimum_margin:float=0.0,max_distance:float|None=None):
    rows=[]
    by_name={p.name:p for p in portals}
    for entry_name,exit_name in intended.items():
        entry=by_name[entry_name];r=routing_margin(entry,portals,max_distance)
        actual=r['selected'].name if r['selected'] else None
        rows.append({'entry':entry_name,'intended':exit_name,'actual':actual,'margin':r['margin'],'correct':actual==exit_name,'safe':actual==exit_name and r['margin']>=minimum_margin})
    return rows


def convert(x,z,to_nether=True):
    f=1/8 if to_nether else 8
    return x*f,z*f


def compression(overworld_gain,nether_walk,overworld_walk):
    physical=max(0,float(nether_walk))+max(0,float(overworld_walk));gain=max(0,float(overworld_gain));conventional=gain/8.0
    return {'overworld_gain':gain,'physical':physical,'conventional':conventional,'gain_per_walk':gain/physical if physical else math.inf,'reduction_vs_nether':1-physical/conventional if conventional else 0.0}


def asymmetric_sequence(start_x:float=0.0,start_z:float=0.0,ow_y:float=64.0,low_y:float=5.0,high_y:float=122.0,nether_step:float=15.0,ow_step:float=5.0,stages:int=6):
    """Generate an alternating floor/roof candidate layout for simulation.
    Coordinates are candidates only; validate the resulting portal graph before building it.
    """
    portals=[];x=float(start_x);z=float(start_z)
    for i in range(max(1,int(stages))):
        floor=(i%2==0);ny=low_y if floor else high_y
        ow=Portal(f'OW{i+1}','Overworld',x,ow_y,z)
        nx=x/8.0
        arrival=Portal(f'N{i+1}A','Nether',nx,ny,z/8.0)
        departure=Portal(f'N{i+1}B','Nether',nx+nether_step,ny,z/8.0)
        portals.extend((ow,arrival,departure))
        x=(departure.x*8.0)+127.0+ow_step
    return portals


def optimize_candidate(entry:Portal,candidates:list[Portal],minimum_margin:float=8.0):
    r=routing_margin(entry,candidates)
    if not r['selected']:return None
    return {'selected':r['selected'],'distance':r['selected_distance'],'margin':r['margin'],'meets_margin':r['margin']>=minimum_margin}


def gate_table(destinations:dict[str,str],portal_names:list[str]):
    # destinations maps destination name -> portal that should remain active.
    rows={}
    for dest,open_name in destinations.items():rows[dest]={p:(p==open_name) for p in portal_names}
    return rows


def network_summary(portals:list[Portal]):
    matrix=link_matrix(portals);by_dim=defaultdict(int)
    for p in portals:by_dim[_dim_name(p.dimension)]+=1
    return {'portals':len(portals),'by_dimension':dict(by_dim),'links':matrix,'cycles':cycles(portals)}
