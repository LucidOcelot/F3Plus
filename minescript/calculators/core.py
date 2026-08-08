from __future__ import annotations
import math
from itertools import permutations
from collections import Counter

STACK=64; SHULKER_SLOTS=27; DOUBLE_CHEST_SLOTS=54

def stacks(n): return divmod(max(0,int(n)),STACK)
def storage(n,stack_size=64):
    n=max(0,int(n)); s,r=divmod(n,stack_size)
    return {'items':n,'stacks':s,'remainder':r,'shulkers':math.ceil(n/(stack_size*27)) if n else 0,'double_chests':math.ceil(n/(stack_size*54)) if n else 0}
def dimensions(w,l,h=1):
    w,l,h=map(int,(w,l,h)); return {'area':w*l,'volume':w*l*h,'perimeter':2*(w+l),'surface_area':2*(w*l+w*h+l*h)}
def tick_convert(ticks):
    sec=float(ticks)/20; return {'ticks':float(ticks),'seconds':sec,'minutes':sec/60,'hours':sec/3600}
def seconds_to_ticks(seconds): return float(seconds)*20
def hopper_timer(items): return tick_convert(max(0,int(items))*8)
def repeater_delay(settings):
    rt=sum(max(1,min(4,int(v))) for v in settings); return {'redstone_ticks':rt,**tick_convert(rt*2)}
def comparator_strength(items,slots,max_stack=64):
    if items<=0:return 0
    fullness=max(0,min(1,float(items)/(slots*max_stack))); return 1+math.floor(14*fullness)
def nether_convert(x,z,to_nether=True):
    f=1/8 if to_nether else 8; return (x*f,z*f)
def distance3(a,b): return math.dist(tuple(map(float,a)),tuple(map(float,b)))
def distance2(a,b): return math.hypot(float(b[0])-float(a[0]),float(b[1])-float(a[1]))
def midpoint(a,b): return tuple((float(x)+float(y))/2 for x,y in zip(a,b))
def bearing(x1,z1,x2,z2): return math.degrees(math.atan2(-(x2-x1),(z2-z1)))
def travel_time(distance,speed): return float(distance)/max(.001,float(speed))
def stacks_text(n,stack=64):
    q,r=divmod(max(0,int(n)),stack); return f'{q} stacks + {r}' if r else f'{q} stacks'
def beacon_blocks(levels):
    levels=max(1,min(4,int(levels))); layers=[(2*i+1)**2 for i in range(1,levels+1)]; return {'levels':levels,'layers':layers,'blocks':sum(layers)}
def beacon_multi(count,levels=4): return {'beacons':int(count),'mineral_blocks':beacon_blocks(levels)['blocks']*int(count)}
def furnace_throughput(furnaces,seconds_per_item=10,hours=1): return int(furnaces)*3600/float(seconds_per_item)*float(hours)
def fuel_items(items,burns_per_fuel): return math.ceil(max(0,int(items))/max(.001,float(burns_per_fuel)))
def breeding_cycles(start_adults,cycles): return int(start_adults)*(2**max(0,int(cycles)))
def villager_food(breedings,food='bread'):
    costs={'bread':3,'carrot':12,'potato':12,'beetroot':12}; return max(0,int(breedings))*costs.get(food,3)
def xp_levels_to_points(level):
    l=max(0,int(level));
    if l<=16:return l*l+6*l
    if l<=31:return int(2.5*l*l-40.5*l+360)
    return int(4.5*l*l-162.5*l+2220)
def compression(items,ratio=9): return {'input':int(items),'compressed':int(items)//int(ratio),'remainder':int(items)%int(ratio)}
def logistics(items,inventory_slots=36,stack_size=64,shulkers=0):
    per=inventory_slots*stack_size+shulkers*27*stack_size; return {'items':int(items),'capacity_per_trip':per,'trips':math.ceil(items/per) if items>0 else 0}
def spawn_sphere(radius=128): return {'radius':radius,'diameter':radius*2,'volume':4/3*math.pi*radius**3}
def chunk_bounds(cx,cz): return {'x_min':cx*16,'x_max':cx*16+15,'z_min':cz*16,'z_max':cz*16+15}
def region_bounds(rx,rz): return {'chunk_x_min':rx*32,'chunk_x_max':rx*32+31,'chunk_z_min':rz*32,'chunk_z_max':rz*32+31,'block_x_min':rx*512,'block_x_max':rx*512+511,'block_z_min':rz*512,'block_z_max':rz*512+511}
def grid_count(width,length,spacing): return (math.floor((width-1)/spacing)+1)*(math.floor((length-1)/spacing)+1)
def perimeter_spacing(width,length,spacing): return max(0,2*(math.ceil(width/spacing)+math.ceil(length/spacing))-4)
def farm_separation(a,b): return distance2((a[0],a[2]),(b[0],b[2]))
def random_tick_square(sim_distance):
    r=max(0,int(sim_distance)); side=2*r+1; return {'chunks':side*side,'side_chunks':side,'side_blocks':side*16}
def loaded_chunk_square(view_distance):
    r=max(0,int(view_distance)); side=2*r+1; return {'chunks':side*side,'side_chunks':side,'side_blocks':side*16}
def tool_wear(actions,unbreaking=0,conservative=False):
    a=max(0,int(actions)); u=max(0,int(unbreaking)); expected=a/(u+1); return {'actions':a,'expected_durability_used':a if conservative else expected,'conservative_durability_used':a}
def consumption(rate_per_hour,hours): return float(rate_per_hour)*float(hours)
def crafter_throughput(cycle_ticks,items_per_cycle=1): return 20/max(.001,float(cycle_ticks))*float(items_per_cycle)*3600
def copper_oxidation_estimate(stages=1,base_minutes=50): return {'stages':int(stages),'rough_minutes':float(stages)*float(base_minutes),'note':'Random ticks make real time variable.'}
def firework_duration(flight_duration): return {'flight_duration':int(flight_duration),'rough_burn_seconds':0.5+0.5*int(flight_duration)}
def respawn_anchor(glowstone): return {'charges':min(4,max(0,int(glowstone))),'explosive_outside_nether':True}
def stronghold_ring(index):
    # Stronghold ring values are planning estimates for versions using the modern ring layout.
    rings=[(3,1408,2688),(6,4480,5760),(10,7552,8832),(15,10624,11904),(21,13696,14976),(28,16768,18048),(36,19840,21120),(9,22912,24192)]
    return rings[max(0,min(len(rings)-1,int(index)))]
def triangulate_ray(p1,angle1,p2,angle2):
    # Minecraft yaw: 0 south, -90 east.
    a1=math.radians(angle1); a2=math.radians(angle2); v1=(-math.sin(a1),math.cos(a1)); v2=(-math.sin(a2),math.cos(a2))
    dx=p2[0]-p1[0]; dz=p2[1]-p1[1]; det=v1[0]*(-v2[1])-v1[1]*(-v2[0])
    if abs(det)<1e-9: raise ValueError('The two throws are too parallel.')
    t=(dx*(-v2[1])-dz*(-v2[0]))/det; return (p1[0]+t*v1[0],p1[1]+t*v1[1])
def optimal_visit_order(origin,points):
    if not points:return (0,())
    if len(points)<=9:
        best=None
        for perm in permutations(points):
            total=distance2(origin,perm[0])+sum(distance2(perm[i],perm[i+1]) for i in range(len(perm)-1))
            if best is None or total<best[0]:best=(total,perm)
        return best
    remaining=list(points); cur=origin; route=[]; total=0
    while remaining:
        nxt=min(remaining,key=lambda p:distance2(cur,p)); total+=distance2(cur,nxt); route.append(nxt); remaining.remove(nxt); cur=nxt
    return total,tuple(route)

def circle(radius,filled=False):
    r=max(1,int(radius)); pts=set()
    if filled:
        for z in range(-r,r+1):
            for x in range(-r,r+1):
                if x*x+z*z<=r*r:pts.add((x,z))
    else:
        for i in range(3600):
            a=math.radians(i/10); pts.add((round(r*math.cos(a)),round(r*math.sin(a))))
    return sorted(pts,key=lambda p:math.atan2(p[1],p[0]))
def ellipse(rx,rz,filled=False):
    rx,rz=max(1,int(rx)),max(1,int(rz)); pts=set()
    if filled:
        for z in range(-rz,rz+1):
            for x in range(-rx,rx+1):
                if x*x/(rx*rx)+z*z/(rz*rz)<=1:pts.add((x,z))
    else:
        for i in range(3600):
            a=math.radians(i/10); pts.add((round(rx*math.cos(a)),round(rz*math.sin(a))))
    return list(pts)
def polygon(radius,sides):
    sides=max(3,int(sides)); return [(round(radius*math.cos(2*math.pi*i/sides)),round(radius*math.sin(2*math.pi*i/sides))) for i in range(sides)]
def sphere(radius,hollow=True):
    r=max(1,int(radius)); out=[]
    for y in range(-r,r+1):
      for z in range(-r,r+1):
       for x in range(-r,r+1):
        d=x*x+y*y+z*z
        if (hollow and (r-.75)**2<=d<=(r+.25)**2) or (not hollow and d<=r*r):out.append((x,y,z))
    return out
def dome(radius,hollow=True): return [p for p in sphere(radius,hollow) if p[1]>=0]
def cylinder(radius,height,hollow=True): return [(x,y,z) for y in range(max(1,int(height))) for x,z in circle(radius,not hollow)]
def cone(radius,height):
    out=[]; h=max(1,int(height))
    for y in range(h):
        r=max(0,round(radius*(1-y/max(1,h-1)))); out.extend([(x,y,z) for x,z in circle(r,False)] if r else [(0,y,0)])
    return out
def spiral(radius,height,turns=2):
    out=[]; steps=max(8,int(height)*8)
    for i in range(steps+1):
        t=i/steps;a=2*math.pi*float(turns)*t;out.append((round(radius*math.cos(a)),round(height*t),round(radius*math.sin(a))))
    return list(dict.fromkeys(out))
def rotate_point(x,z,degrees):
    a=math.radians(degrees); return (round(x*math.cos(a)-z*math.sin(a)),round(x*math.sin(a)+z*math.cos(a)))
def mirror_point(x,y,z,cx,cy,cz,axis='x'):
    return {'x':(2*cx-x,y,z),'y':(x,2*cy-y,z),'z':(x,y,2*cz-z)}[axis]
def roof_layers(width,height,pitch=1): return [{'y':y,'inset':math.floor(y/max(.001,float(pitch))),'width':max(1,int(width)-2*math.floor(y/max(.001,float(pitch))))} for y in range(max(1,int(height)))]
def stair_run(rise,run_per_step=1): return {'rise':int(rise),'run':abs(int(rise))*int(run_per_step),'blocks':abs(int(rise))}
def bridge_supports(span,spacing): return math.floor(max(0,float(span))/max(.001,float(spacing)))+1
def banner_patterns(layers): return {'layers':int(layers),'max_vanilla_layers':6,'within_standard_limit':int(layers)<=6}
def potion_batches(bottles,per_batch=3): return math.ceil(max(0,int(bottles))/max(1,int(per_batch)))
def smithing_materials(items): return {'templates':int(items),'upgrade_materials':int(items),'base_items':int(items)}
def note_block_clicks(target_pitch): return max(0,min(24,int(target_pitch)))
