from __future__ import annotations
import math
from dataclasses import dataclass

STACK=64
SHULKER_SLOTS=27
CHEST_SLOTS=27
DOUBLE_CHEST_SLOTS=54


def material_storage(items:int,stack_size:int=64):
    items=max(0,int(items)); per_shulker=stack_size*SHULKER_SLOTS; per_double=stack_size*DOUBLE_CHEST_SLOTS
    return {
        'items':items,
        'stacks':items//stack_size,
        'stack_remainder':items%stack_size,
        'shulkers':math.ceil(items/per_shulker) if items else 0,
        'double_chests':math.ceil(items/per_double) if items else 0,
    }


def excavation(width:int,length:int,height:int,blocks_per_second:float=4.0):
    volume=max(0,int(width))*max(0,int(length))*max(0,int(height))
    seconds=volume/max(.001,float(blocks_per_second))
    return {'blocks':volume,'seconds':seconds,'minutes':seconds/60,'hours':seconds/3600,**material_storage(volume)}


def perimeter(width:int,length:int,height:int=1):
    w=max(1,int(width));l=max(1,int(length));h=max(1,int(height))
    layer=2*w+2*l-4
    return {'blocks':layer*h,'per_layer':layer,'layers':h,**material_storage(layer*h)}


def hollow_box(width:int,length:int,height:int):
    w,l,h=max(1,int(width)),max(1,int(length)),max(1,int(height))
    outer=w*l*h
    inner=max(0,w-2)*max(0,l-2)*max(0,h-2)
    blocks=outer-inner
    return {'blocks':blocks,**material_storage(blocks)}


def lighting_grid(width:int,length:int,spacing:int=8):
    w,l,s=max(1,int(width)),max(1,int(length)),max(1,int(spacing))
    xs=list(range(0,w,s));zs=list(range(0,l,s))
    if xs[-1]!=w-1:xs.append(w-1)
    if zs[-1]!=l-1:zs.append(l-1)
    pts=[(x,z) for x in xs for z in zs]
    return {'count':len(pts),'positions':pts}


def beacon_pyramid(levels:int=4,beacons:int=1):
    levels=max(1,min(4,int(levels)));beacons=max(1,int(beacons))
    layers=[(2*i+1)**2 for i in range(1,levels+1)]
    single=sum(layers)
    return {'levels':levels,'layers':layers,'single_beacon_blocks':single,'blocks':single*beacons,'beacons':beacons}


def simulation_square(distance_chunks:int):
    r=max(0,int(distance_chunks));side=2*r+1
    return {'radius_chunks':r,'side_chunks':side,'chunks':side*side,'side_blocks':side*16,'area_blocks':(side*16)**2}


def sphere_volume(radius:float):
    r=max(0.0,float(radius))
    return {'radius':r,'diameter':2*r,'volume':4*math.pi*r**3/3,'surface_area':4*math.pi*r*r}


def mob_spawn_shell(min_radius:float=24,max_radius:float=128):
    a=sphere_volume(min_radius);b=sphere_volume(max_radius)
    return {'inner_radius':min_radius,'outer_radius':max_radius,'shell_volume':b['volume']-a['volume']}


def hopper_rate(items:int=1,hoppers:int=1):
    # Standard hopper transfer is one item every 8 game ticks while able to transfer.
    h=max(1,int(hoppers));i=max(0,int(items)); per_second=2.5*h
    return {'items':i,'hoppers':h,'items_per_second':per_second,'seconds':i/per_second if i else 0,'items_per_hour':per_second*3600}


def furnace_array(furnaces:int,seconds_per_item:float=10.0,hours:float=1.0):
    f=max(0,int(furnaces));sec=max(.001,float(seconds_per_item));hrs=max(0,float(hours))
    return {'furnaces':f,'items_per_hour':f*3600/sec,'items':f*3600/sec*hrs}


def comparator_signal(items:int,slots:int,max_stack:int=64):
    items=max(0,int(items));slots=max(1,int(slots));max_stack=max(1,int(max_stack))
    if items==0:return 0
    fullness=min(1.0,items/(slots*max_stack))
    return 1+math.floor(14*fullness)


def repeater_chain(settings):
    vals=[max(1,min(4,int(v))) for v in settings]
    redstone_ticks=sum(vals);game_ticks=redstone_ticks*2
    return {'repeaters':len(vals),'redstone_ticks':redstone_ticks,'game_ticks':game_ticks,'seconds':game_ticks/20}


def chunk_loader_grid(width_chunks:int,length_chunks:int,coverage_radius:int=1):
    w,l=max(1,int(width_chunks)),max(1,int(length_chunks));r=max(0,int(coverage_radius))
    step=max(1,2*r+1)
    nx=math.ceil(w/step);nz=math.ceil(l/step)
    return {'loaders':nx*nz,'x_count':nx,'z_count':nz,'spacing_chunks':step}


def portal_highway(overworld_distance:float,speed_nether:float=72.7,portal_overhead_seconds:float=8.0):
    ow=max(0.0,float(overworld_distance));nether=ow/8.0
    travel=nether/max(.001,float(speed_nether))
    return {'overworld_distance':ow,'nether_distance':nether,'travel_seconds':travel+max(0,float(portal_overhead_seconds))}


def branch_mine_plan(width:int,branch_spacing:int=3,branch_depth:int=32):
    width=max(1,int(width));spacing=max(1,int(branch_spacing));depth=max(1,int(branch_depth))
    branches=max(1,math.ceil(width/spacing))
    return {'branches':branches,'branch_depth':depth,'side_tunnel_blocks':branches*depth,'spacing':spacing}


def portal_materials(portals:int,corner_blocks:bool=True):
    p=max(0,int(portals));obs=14 if corner_blocks else 10
    return {'portals':p,'obsidian':p*obs,'flint_and_steel_uses':p}


def shulker_trips(items:int,inventory_shulkers:int=27,stack_size:int=64):
    capacity=max(1,int(inventory_shulkers))*SHULKER_SLOTS*max(1,int(stack_size))
    return {'capacity_per_trip':capacity,'trips':math.ceil(max(0,int(items))/capacity) if items else 0}


def spear_dash_consumption(lunges:int,hunger_per_lunge:float,food_points:int):
    n=max(0,int(lunges));cost=n*max(0,float(hunger_per_lunge));food=max(1,int(food_points))
    return {'lunges':n,'hunger_cost':cost,'food_items':math.ceil(cost/food)}

# Community-inspired technical planning utilities. Implemented locally so they remain offline.
def catenary_curve(span:int, sag:float, height_delta:float=0.0):
    """Block-sampled hanging cable approximation using a parabola through endpoints.
    For Minecraft building the rounded lattice path is more useful than a continuous catenary."""
    n=max(1,int(span)); sag=max(0.0,float(sag)); dy=float(height_delta)
    pts=[]
    for x in range(n+1):
        t=x/n
        y=dy*t - 4.0*sag*t*(1.0-t)
        p=(x,round(y))
        if not pts or p!=pts[-1]: pts.append(p)
    return {'span':n,'sag':sag,'height_delta':dy,'points':pts,'blocks':len(pts)}

def spiral_staircase(diameter:int,height:int,steps_per_turn:int=12,clockwise:bool=True):
    d=max(3,int(diameter)); h=max(1,int(height)); steps=max(4,int(steps_per_turn)); r=(d-1)/2
    pts=[]
    for y in range(h):
        a=(2*math.pi*y/steps)*(1 if clockwise else -1)
        p=(round(r*math.cos(a)),y,round(r*math.sin(a)))
        if not pts or p!=pts[-1]:pts.append(p)
    return {'diameter':d,'height':h,'steps_per_turn':steps,'clockwise':clockwise,'points':pts,'blocks':len(pts)}

def xp_for_level(level:int):
    l=max(0,int(level))
    if l<=16:return l*l+6*l
    if l<=31:return int(2.5*l*l-40.5*l+360)
    return int(4.5*l*l-162.5*l+2220)

def xp_between_levels(start:int,end:int):
    a,b=max(0,int(start)),max(0,int(end));
    if b<a:a,b=b,a
    return {'start':a,'end':b,'xp':xp_for_level(b)-xp_for_level(a),'start_total':xp_for_level(a),'end_total':xp_for_level(b)}

def mending_repair(xp:int,items:int=1):
    # Mending converts each absorbed XP point into 2 durability on one eligible equipped item.
    x=max(0,int(xp)); n=max(1,int(items))
    return {'xp':x,'eligible_items':n,'maximum_total_durability_repaired':2*x,'average_if_evenly_distributed':2*x/n}

def mob_cap(players:int=1,eligible_chunks:int=289,category_cap:int=70):
    # Vanilla natural-spawn cap scales with eligible chunks: cap * chunks / 289.
    p=max(1,int(players)); chunks=max(0,int(eligible_chunks)); base=max(0,int(category_cap))
    cap=math.floor(base*chunks/289)
    return {'players':p,'eligible_chunks':chunks,'category_base_cap':base,'local_scaled_cap':cap,'simple_independent_player_upper_bound':cap*p}

def despawn_shell(player_x:float,player_z:float,soft:float=32.0,hard:float=128.0):
    return {'player':(float(player_x),float(player_z)),'soft_despawn_radius':float(soft),'hard_despawn_radius':float(hard),'hard_despawn_diameter':2*float(hard),'hard_square_bounds':(player_x-hard,player_z-hard,player_x+hard,player_z+hard)}

def item_sorter_capacity(modules:int,filter_items_per_module:int=41,hopper_slots:int=5):
    m=max(0,int(modules));f=max(1,int(filter_items_per_module));s=max(1,int(hopper_slots))
    return {'modules':m,'filter_items_reserved':m*f,'hopper_slots':m*s,'distinct_sorted_items':m}

def anvil_prior_work_plan(operations:int):
    """Prior-work penalty schedule for sequential anvil operations: 0,1,3,7,..."""
    n=max(0,int(operations)); penalties=[(1<<i)-1 for i in range(n)]
    return {'operations':n,'prior_work_penalties':penalties,'total_prior_work_penalty':sum(penalties),'recommendation':'Balance combination trees to minimize accumulated prior-work penalties.'}
