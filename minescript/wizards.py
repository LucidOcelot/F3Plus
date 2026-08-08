from __future__ import annotations
import math
from .calculators import core,technical


def branch_mine(spacing=4,depth=32,branches=8,torch_spacing=12):
    return {'wizard':'branch_mine','macro':'Branch Miner','coordinate_validation':True,'spacing':int(spacing),'depth':int(depth),'branches':int(branches),'torch_spacing':int(torch_spacing),'estimated_side_distance':2*int(depth)*int(branches)}

def quarry(width=16,length=16,depth=16):
    d=core.dimensions(width,length,depth)
    return {'wizard':'quarry','macro':'Area Excavator','coordinate_validation':True,'width':int(width),'length':int(length),'depth':int(depth),'layers':int(depth),'row_distance':int(length),'rows_per_layer':int(width),**d}

def perimeter(width=256,length=256,depth=64):
    volume=int(width)*int(length)*int(depth)
    return {'wizard':'perimeter','macro':'Area Excavator','coordinate_validation':True,'width':width,'length':length,'depth':depth,'blocks':volume,**technical.material_storage(volume)}

def crop(rows=8,row_length=32): return {'wizard':'crop_farm','macro':'Coordinate Row Farmer','coordinate_validation':True,'rows':int(rows),'row_length':float(row_length)}
def tree(sapling_slot=1,bonemeal_slot=2,tool_slot=3): return {'wizard':'tree_farm','macro':'Tree Farm Cycle','sapling_slot':sapling_slot,'bonemeal_slot':bonemeal_slot,'tool_slot':tool_slot}
def villager_hall(villagers=20,spacing=1): return {'wizard':'villager_hall','villagers':villagers,'workstations':villagers,'minimum_length':villagers*spacing}
def nether_highway(start=(0,64,0),destination=(8000,64,0),speed=72.7):
    dx=destination[0]-start[0]; dz=destination[2]-start[2]; ow=math.hypot(dx,dz); n=ow/8
    return {'wizard':'nether_highway','coordinate_validation':True,'start':start,'destination':destination,'sister_start':(start[0]/8,start[1],start[2]/8),'sister_destination':(destination[0]/8,destination[1],destination[2]/8),'overworld_distance':ow,'nether_distance':n,'travel_seconds':n/max(.001,speed)}
def portal_network(portals=4): return {'wizard':'portal_network','portals':int(portals),'validation':['link_matrix','routing_margin','loop_detection']}
def asymmetric_portal(stages=6): return {'wizard':'asymmetric_portal','stages':int(stages),'validation':['candidate_ranking','vertical_isolation','routing_margin','loop_detection']}
def build_material(width=16,length=16,height=8): return {'wizard':'build_material',**core.dimensions(width,length,height),**technical.material_storage(width*length*height)}
def lighting(width=32,length=32,spacing=8): return {'wizard':'lighting_grid',**technical.lighting_grid(width,length,spacing)}
def beacon_network(beacons=4,levels=4): return {'wizard':'beacon_network',**technical.beacon_pyramid(levels,beacons)}
