from __future__ import annotations
from . import macros


def line_steps(): return [{'type':'move','key':'w','seconds':.25,'place':True}]
def rectangle_steps(): return [{'type':'move','key':'w','seconds':2,'place':True},{'type':'turn','dx':900}]*4
def grid_steps(): return [{'type':'move','key':'w','seconds':1,'place':True},{'type':'turn','dx':900},{'type':'move','key':'w','seconds':.4,'place':True},{'type':'turn','dx':900}]

PRESETS={
 'Generator Miner':lambda e:macros.continuous_action(e,held_mouse=('left',)),
 'Hold Attack':lambda e:macros.continuous_action(e,held_mouse=('left',)),
 'Hold Use':lambda e:macros.continuous_action(e,held_mouse=('right',)),
 'Concrete Converter':lambda e:macros.continuous_action(e,held_mouse=('left','right')),
 'Auto Walk':lambda e:macros.continuous_action(e,held_keys=('w',)),
 'Custom Hold':lambda e:macros.continuous_action(e,held_keys=('w',)),
 'Auto Attack':lambda e:macros.periodic_interaction(e,False,1000),
 'AFK Mob Grinder':lambda e:macros.periodic_interaction(e,True,1000),
 'Livestock Breeder':lambda e:macros.livestock_breeder(e,True,20,2,1000),
 'Custom Periodic Action':lambda e:macros.periodic_interaction(e,False,1000),
 'Auto Fishing':lambda e:macros.auto_fishing(e,1200,250),
 'Basic Travel':lambda e:macros.travel(e,('w',)),
 'Sprint Travel':lambda e:macros.travel(e,('w','ctrl')),
 'Sprint-Jump Travel':lambda e:macros.travel(e,('w','ctrl'),800),
 'Swim Travel':lambda e:macros.continuous_action(e,held_keys=('w','ctrl','space')),
 'Boat Travel':lambda e:macros.travel(e,('w',)),
 'Horse/Camel Travel':lambda e:macros.travel(e,('w',)),
 'Elytra Launch':macros.elytra_launch,
 'Elytra Cruise':lambda e:macros.elytra_cruise(e,10000),
 'Riptide Travel':lambda e:macros.riptide_travel(e,850,1600),
 'Spear Dash Travel':lambda e:macros.spear_dash_travel(e,1,2,3,120,300,1650),
 'Coordinate Travel':lambda e:macros.coordinate_travel(e,64.0),
 'Waypoint Travel':lambda e:macros.coordinate_travel(e,64.0),
 'Nether-Assisted Travel':lambda e:macros.coordinate_travel(e,64.0),
 'Tunnel Miner':lambda e:macros.tunnel_miner(e,12000),
 'Branch Miner':lambda e:macros.coordinate_branch_miner(e,4,24,900,8,True),
 'Stair Excavator':lambda e:macros.coordinate_stair_excavator(e,32,1.0,True),
 'Area Excavator':lambda e:macros.coordinate_area_excavator(e,8,16,1,900),
 'Crop Farmer':lambda e:macros.crop_farmer(e,12000),
 'Coordinate Row Farmer':lambda e:macros.row_farmer(e,8,10,.45,900,True,True),
 'Multi-Row Farmer':lambda e:macros.row_farmer(e,16,10,.45,900,True,True),
 'Bone Meal Farmer':lambda e:macros.bone_meal_farmer(e,4,150),
 'Stationary Grow/Harvest':lambda e:macros.bone_meal_farmer(e,4,150),
 'Tree Farm Cycle':macros.tree_farm_cycle,
 'Farm Station Controller':macros.tree_farm_cycle,
 'Mending Grinder':lambda e:macros.mending_grinder(e,1250,30000,(1,2,3)),
 'Crossbow Volley':lambda e:macros.crossbow_volley(e,1300,250,(1,2,3)),
 'Hotbar Workflow':lambda e:macros.hotbar_workflow(e,(1,2,3),250,True),
 'Tool Rotation':lambda e:macros.tool_rotation(e,(1,2,3),30,False),
 'Durability Guard':lambda e:macros.guarded_continuous(e,held_mouse=('left',),max_cycles=100),
 'Resource Guard':lambda e:macros.guarded_continuous(e,held_mouse=('right',),max_cycles=100),
 'Food Manager':lambda e:macros.food_manager(e,2,120,1.65),
 'Offhand Workflow':lambda e:macros.offhand_workflow(e,'f',30),
 'Line':lambda e:macros.construction_pattern(e,line_steps(),loop=True),
 'Rectangle':lambda e:macros.construction_pattern(e,rectangle_steps(),loop=False),
 'Filled Rectangle':lambda e:macros.construction_pattern(e,grid_steps(),loop=True),
 'Grid':lambda e:macros.construction_pattern(e,grid_steps(),loop=True),
 'Rows':lambda e:macros.construction_pattern(e,grid_steps(),loop=True),
 'Alternating Pattern':lambda e:macros.construction_pattern(e,grid_steps(),loop=True),
 'Perimeter':lambda e:macros.construction_pattern(e,rectangle_steps(),loop=False),
 'Repeating Segment':lambda e:macros.construction_pattern(e,line_steps(),loop=True),
 'Action Sequencer':lambda e:macros.route_runner(e,[{'type':'tap','key':'space'},{'type':'wait','seconds':.1}],loop=True),
 'Route Runner':lambda e:macros.route_runner(e,[{'type':'hold','key':'w','seconds':1},{'type':'turn','dx':900}],loop=True),
}

MACRO_PRESETS=set(PRESETS)

def runner(name):return PRESETS.get(name)
