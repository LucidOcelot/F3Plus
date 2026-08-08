from __future__ import annotations

# Gameplay routines only emit ordinary player inputs. They do not inspect pixels, game memory,
# packets, or server APIs. Complex routines assume the player aligns the character before start.

def _cycle(engine):
    engine.status.cycles+=1;engine._emit()


def continuous_action(engine,held_keys=(),held_mouse=(),status_interval=.5):
    for k in held_keys:engine.input.key_down(k)
    for b in held_mouse:engine.input.mouse_down(b)
    while not engine.stop_event.is_set():
        _cycle(engine)
        if engine.wait(status_interval):break


def periodic_interaction(engine,hold_use=False,attack_interval_ms=1000,attacks_per_cycle=1,spacing_ms=1000,cycle_interval_ms=None,button='left'):
    if hold_use:engine.input.mouse_down('right')
    interval=(cycle_interval_ms or attack_interval_ms)/1000
    while not engine.stop_event.is_set():
        start_count=0
        for _ in range(max(1,int(attacks_per_cycle))):
            engine.input.click(button,.06);start_count+=1
            if start_count<attacks_per_cycle and engine.wait(spacing_ms/1000):return
        _cycle(engine)
        used=(spacing_ms/1000)*max(0,attacks_per_cycle-1)
        if engine.wait(max(0,interval-used)):return


def livestock_breeder(engine,hold_feed=True,cycle_minutes=20,actions=2,spacing_ms=1000):
    return periodic_interaction(engine,hold_use=hold_feed,attacks_per_cycle=actions,spacing_ms=spacing_ms,cycle_interval_ms=int(cycle_minutes*60_000),button='left')


def auto_fishing(engine,wait_ms=1200,recast_ms=250):
    while not engine.stop_event.is_set():
        engine.input.click('right',.06)
        if engine.wait(wait_ms/1000):return
        engine.input.click('right',.06);_cycle(engine)
        if engine.wait(recast_ms/1000):return


def travel(engine,keys=('w',),jump_interval_ms=None):
    for key in keys:engine.input.key_down(key)
    while not engine.stop_event.is_set():
        if jump_interval_ms:
            engine.input.tap('space',.06);_cycle(engine)
            if engine.wait(jump_interval_ms/1000):return
        else:
            _cycle(engine)
            if engine.wait(.5):return


def elytra_launch(engine,rocket_slot=None):
    if rocket_slot:engine.input.tap(str(rocket_slot))
    engine.input.tap('space',.075)
    if engine.wait(.20):return
    engine.input.tap('space',.075)
    if engine.wait(.075):return
    engine.input.click('right',.1);_cycle(engine)


def elytra_cruise(engine,boost_ms=10000,rocket_slot=None):
    elytra_launch(engine,rocket_slot);engine.input.key_down('w')
    while not engine.stop_event.is_set():
        if engine.wait(boost_ms/1000):return
        engine.input.click('right',.1);_cycle(engine)


def riptide_travel(engine,charge_ms=850,cycle_ms=1600):
    engine.input.key_down('w')
    while not engine.stop_event.is_set():
        engine.input.mouse_down('right')
        if engine.wait(charge_ms/1000):return
        engine.input.mouse_up('right');_cycle(engine)
        if engine.wait(max(0,(cycle_ms-charge_ms)/1000)):return


def spear_dash_travel(engine,spear_slot=1,food_slot=2,lunges=3,charge_ms=120,recovery_ms=300,eat_ms=1650,eat_before=False,lunge_button='left'):
    engine.input.key_down('w')
    def eat():
        engine.input.tap(str(food_slot));engine.input.mouse_down('right')
        stopped=engine.wait(eat_ms/1000);engine.input.mouse_up('right');return stopped
    if eat_before and eat():return
    while not engine.stop_event.is_set():
        engine.input.tap(str(spear_slot))
        for _ in range(max(1,int(lunges))):
            engine.input.mouse_down(lunge_button)
            if engine.wait(charge_ms/1000):return
            engine.input.mouse_up(lunge_button);_cycle(engine)
            if engine.wait(recovery_ms/1000):return
        if eat():return


def tunnel_miner(engine,torch_interval_ms=12000,torch_slot=9,tool_slot=None,torch_button='right'):
    if tool_slot:engine.input.tap(str(tool_slot))
    engine.input.key_down('w');engine.input.mouse_down('left')
    while not engine.stop_event.is_set():
        if engine.wait(torch_interval_ms/1000):return
        engine.input.mouse_up('left');engine.input.key_up('w');engine.input.tap(str(torch_slot));engine.input.click(torch_button,.08)
        if tool_slot:engine.input.tap(str(tool_slot))
        engine.input.key_down('w');engine.input.mouse_down('left');_cycle(engine)


def branch_miner(engine,main_seconds=3.0,branch_seconds=4.0,turn_dx=900,branches=8,alternating=True):
    """Timed branch pattern. Coordinate-aware stopping can be supplied by Route Runner instead."""
    side=1
    engine.input.mouse_down('left')
    for _ in range(max(1,int(branches))):
        engine.input.key_down('w')
        if engine.wait(main_seconds):return
        engine.input.key_up('w');engine.input.move_relative(turn_dx*side,0)
        engine.input.key_down('w')
        if engine.wait(branch_seconds):return
        engine.input.key_up('w');engine.input.move_relative(turn_dx*2*side,0);engine.input.key_down('w')
        if engine.wait(branch_seconds):return
        engine.input.key_up('w');engine.input.move_relative(turn_dx*side,0);_cycle(engine)
        if alternating:side*=-1


def area_excavator(engine,rows=8,row_seconds=8.0,shift_seconds=.45,turn_dx=900):
    engine.input.mouse_down('left');direction=1
    for _ in range(max(1,int(rows))):
        engine.input.key_down('w')
        if engine.wait(row_seconds):return
        engine.input.key_up('w');_cycle(engine)
        engine.input.move_relative(turn_dx*direction,0);engine.input.key_down('w')
        if engine.wait(shift_seconds):return
        engine.input.key_up('w');engine.input.move_relative(turn_dx*direction,0);direction*=-1


def stair_excavator(engine,steps=32,step_seconds=.55,descending=True):
    engine.input.mouse_down('left')
    for _ in range(max(1,int(steps))):
        engine.input.key_down('w')
        if descending:engine.input.key_down('shift')
        else:engine.input.tap('space',.08)
        if engine.wait(step_seconds):return
        engine.input.key_up('w');engine.input.key_up('shift');_cycle(engine)


def crop_farmer(engine,row_ms=12000):
    engine.input.key_down('w');engine.input.mouse_down('left');engine.input.mouse_down('right')
    while not engine.stop_event.is_set():
        if engine.wait(row_ms/1000):return
        _cycle(engine)


def row_farmer(engine,rows=8,row_seconds=10.0,shift_seconds=.45,turn_dx=900,attack=True,use=True):
    if attack:engine.input.mouse_down('left')
    if use:engine.input.mouse_down('right')
    direction=1
    for _ in range(max(1,int(rows))):
        engine.input.key_down('w')
        if engine.wait(row_seconds):return
        engine.input.key_up('w');_cycle(engine)
        engine.input.move_relative(turn_dx*direction,0);engine.input.key_down('w')
        if engine.wait(shift_seconds):return
        engine.input.key_up('w');engine.input.move_relative(turn_dx*direction,0);direction*=-1


def mending_grinder(engine,attack_ms=1250,slot_ms=30000,slots=(1,2,3)):
    idx=0;engine.input.tap(str(slots[idx]));elapsed=0.0
    while not engine.stop_event.is_set():
        engine.input.click('left',.06);_cycle(engine);elapsed+=attack_ms/1000
        if elapsed>=slot_ms/1000:
            idx=(idx+1)%len(slots);engine.input.tap(str(slots[idx]));elapsed=0
        if engine.wait(attack_ms/1000):return


def bone_meal_farmer(engine,clicks=4,click_delay_ms=150,plant_slot=1,bonemeal_slot=2):
    while not engine.stop_event.is_set():
        engine.input.click('left');engine.input.tap(str(plant_slot));engine.input.click('right');engine.input.tap(str(bonemeal_slot))
        for _ in range(max(1,int(clicks))):
            engine.input.click('right')
            if engine.wait(click_delay_ms/1000):return
        _cycle(engine)


def crossbow_volley(engine,charge_ms=1300,swap_ms=250,slots=(1,2,3)):
    while not engine.stop_event.is_set():
        for slot in slots:
            engine.input.tap(str(slot))
            if engine.wait(swap_ms/1000):return
            engine.input.click('right');engine.input.mouse_down('right')
            if engine.wait(charge_ms/1000):return
            engine.input.mouse_up('right');_cycle(engine)


def tree_farm_cycle(engine,sapling_slot=1,bonemeal_slot=2,tool_slot=3,bonemeal_clicks=4,chop_seconds=4,collection_seconds=.75):
    while not engine.stop_event.is_set():
        engine.input.tap(str(sapling_slot));engine.input.click('right');engine.input.tap(str(bonemeal_slot))
        for _ in range(max(1,int(bonemeal_clicks))):
            engine.input.click('right')
            if engine.wait(.15):return
        engine.input.tap(str(tool_slot));engine.input.mouse_down('left')
        if engine.wait(chop_seconds):return
        engine.input.mouse_up('left')
        if engine.wait(collection_seconds):return
        _cycle(engine)


def construction_pattern(engine,steps,place_button='right',loop=False):
    while True:
        for step in steps:
            if engine.stop_event.is_set():return
            kind=step.get('type')
            if kind=='move':
                key=step.get('key','w');engine.input.key_down(key)
                if step.get('place',True):engine.input.click(place_button)
                if engine.wait(float(step.get('seconds',.25))):return
                engine.input.key_up(key)
            elif kind=='place':engine.input.click(step.get('button',place_button),float(step.get('hold',.05)))
            elif kind=='turn':engine.input.move_relative(int(step.get('dx',0)),int(step.get('dy',0)))
            elif kind=='tap':engine.input.tap(step.get('key','space'),float(step.get('hold',.05)))
            elif kind=='slot':engine.input.tap(str(step.get('slot',1)))
            elif kind=='wait' and engine.wait(float(step.get('seconds',1))):return
            _cycle(engine)
        if not loop:return


def route_runner(engine,steps,loop=False):
    while not engine.stop_event.is_set():
        for step in steps:
            if engine.stop_event.is_set():return
            typ=step.get('type')
            if typ=='wait':
                if engine.wait(float(step.get('seconds',1))):return
            elif typ=='tap':engine.input.tap(step['key'],float(step.get('hold',.05)))
            elif typ=='click':engine.input.click(step.get('button','right'),float(step.get('hold',.05)))
            elif typ=='slot':engine.input.tap(str(step.get('slot',1)))
            elif typ=='turn':engine.input.move_relative(int(step.get('dx',0)),int(step.get('dy',0)))
            elif typ=='hold':
                key=step.get('key');button=step.get('button')
                if key:engine.input.key_down(key)
                if button:engine.input.mouse_down(button)
                if engine.wait(float(step.get('seconds',1))):return
                if key:engine.input.key_up(key)
                if button:engine.input.mouse_up(button)
            _cycle(engine)
        if not loop:return


def hotbar_workflow(engine,slots=(1,2,3),delay_ms=250,loop=True):
    while not engine.stop_event.is_set():
        for slot in slots:
            engine.input.tap(str(slot)); _cycle(engine)
            if engine.wait(delay_ms/1000):return
        if not loop:return


def tool_rotation(engine,slots=(1,2,3),slot_seconds=30,hold_attack=False):
    if hold_attack:engine.input.mouse_down('left')
    while not engine.stop_event.is_set():
        for slot in slots:
            engine.input.tap(str(slot)); _cycle(engine)
            if engine.wait(float(slot_seconds)):return


def food_manager(engine,food_slot=2,interval_seconds=120,eat_seconds=1.65):
    while not engine.stop_event.is_set():
        if engine.wait(float(interval_seconds)):return
        engine.input.tap(str(food_slot)); engine.input.mouse_down('right')
        if engine.wait(float(eat_seconds)):return
        engine.input.mouse_up('right'); _cycle(engine)


def offhand_workflow(engine,swap_key='f',interval_seconds=30):
    while not engine.stop_event.is_set():
        engine.input.tap(swap_key); _cycle(engine)
        if engine.wait(float(interval_seconds)):return


def guarded_continuous(engine,held_keys=(),held_mouse=(),max_cycles=100):
    for k in held_keys:engine.input.key_down(k)
    for b in held_mouse:engine.input.mouse_down(b)
    for _ in range(max(1,int(max_cycles))):
        if engine.stop_event.is_set():return
        _cycle(engine)
        if engine.wait(.5):return

# Coordinate-aware routines use periodic clipboard position captures. They stop instead of
# silently falling back to timing when coordinates cannot be validated.
def coordinate_travel(engine,distance=64.0,target=None,keys=('w',),check_interval=.65):
    from .coordinate_control import CoordinateController,CoordinatePolicy
    ctl=CoordinateController(engine,CoordinatePolicy(check_interval=check_interval))
    if target is not None:return ctl.move_until(target,keys=keys)
    return ctl.move_distance(float(distance),keys=keys)


def coordinate_branch_miner(engine,main_distance=4.0,branch_depth=24.0,turn_dx=900,branches=8,alternating=True):
    from .coordinate_control import CoordinateController
    ctl=CoordinateController(engine); side=1
    engine.input.mouse_down('left')
    try:
        for _ in range(max(1,int(branches))):
            if not ctl.move_distance(main_distance):return
            engine.input.move_relative(turn_dx*side,0)
            if not ctl.move_distance(branch_depth):return
            engine.input.move_relative(turn_dx*2*side,0)
            if not ctl.move_distance(branch_depth):return
            engine.input.move_relative(turn_dx*side,0); _cycle(engine)
            if alternating:side*=-1
    finally:
        engine.input.mouse_up('left')


def coordinate_area_excavator(engine,rows=8,row_distance=16.0,shift_distance=1.0,turn_dx=900):
    from .coordinate_control import CoordinateController
    ctl=CoordinateController(engine); direction=1
    engine.input.mouse_down('left')
    try:
        for _ in range(max(1,int(rows))):
            if not ctl.move_distance(row_distance):return
            _cycle(engine); engine.input.move_relative(turn_dx*direction,0)
            if not ctl.move_distance(shift_distance):return
            engine.input.move_relative(turn_dx*direction,0); direction*=-1
    finally:
        engine.input.mouse_up('left')


def coordinate_stair_excavator(engine,steps=32,step_distance=1.0,descending=True):
    from .coordinate_control import CoordinateController
    ctl=CoordinateController(engine); engine.input.mouse_down('left')
    try:
        for _ in range(max(1,int(steps))):
            if descending:engine.input.key_down('shift')
            else:engine.input.tap('space',.08)
            if not ctl.move_distance(step_distance):return
            engine.input.key_up('shift'); _cycle(engine)
    finally:
        engine.input.key_up('shift'); engine.input.mouse_up('left')
