from __future__ import annotations
import math, random, hashlib, json, os, struct, zlib, gzip
from pathlib import Path

# Java Random compatible subset used by structure-region placement.
MASK=(1<<48)-1
MULT=0x5DEECE66D
ADD=0xB
class JavaRandom:
    def __init__(self,seed:int): self.seed=(int(seed)^MULT)&MASK
    def next(self,bits:int):
        self.seed=(self.seed*MULT+ADD)&MASK
        return self.seed>>(48-bits)
    def next_int(self,bound:int|None=None):
        if bound is None:return self.next(32)
        if bound<=0: raise ValueError('bound must be positive')
        if bound&(bound-1)==0:return (bound*self.next(31))>>31
        while True:
            bits=self.next(31); val=bits%bound
            if bits-val+(bound-1)>=0:return val

# Long-lived structure-set constants. These produce placement candidates; biome/terrain
# viability is a separate stage and is intentionally reported separately.
STRUCTURE_RULES={
 # (region size, chunk range, salt). chunk range is the direct nextInt bound,
 # not the Minecraft JSON "separation" value. Values mirror bundled Cubiomes.
 'Village':(34,26,10387312),'Desert Pyramid':(32,24,14357617),'Jungle Temple':(32,24,14357619),
 'Swamp Hut':(32,24,14357620),'Igloo':(32,24,14357618),'Pillager Outpost':(32,24,165745296),
 'Ocean Monument':(32,27,10387313),'Woodland Mansion':(80,60,10387319),'Shipwreck':(24,20,165745295),
 'Ocean Ruin':(20,12,14357621),'Buried Treasure':(1,1,10387320),'Ruined Portal':(40,25,34222645),
 'Nether Fortress':(27,23,30084232),'Bastion':(27,23,30084232),'End City':(20,9,10387313),
 'Trial Chamber':(34,22,94251327),'Ancient City':(24,16,20083232),
}

def _seed(v):
    try:return int(str(v).strip())
    except:return 0

def _region_candidate(seed,rx,rz,spacing,chunk_range,salt):
    r=JavaRandom(seed + rx*341873128712 + rz*132897987541 + salt)
    ox=r.next_int(max(1,chunk_range)); oz=r.next_int(max(1,chunk_range))
    return rx*spacing+ox,rz*spacing+oz

def structure_candidates(name,seed,cx=0,cz=0,radius=64,mc=0):
    from .seed.cubiomes_api import _canonical_structure_name
    try: name = _canonical_structure_name(name)
    except KeyError: pass
    # Prefer the bundled upstream implementation. It handles triangular-distribution
    # structures and special validity gates (outposts, bastions, End cities, etc.)
    # that cannot be represented by one generic region formula.
    try:
        from .seed.cubiomes_api import structure_config, structure_pos
        cfg=structure_config(name,mc=int(mc))
        spacing=cfg.region_size; chunk_range=cfg.chunk_range
        r=max(1,int(radius)); minx=(cx-r)//spacing-1; maxx=(cx+r)//spacing+1; minz=(cz-r)//spacing-1; maxz=(cz+r)//spacing+1
        pts=[]
        for rx in range(minx,maxx+1):
            for rz in range(minz,maxz+1):
                q=structure_pos(name,int(seed),rx,rz,mc=int(mc))
                if q is not None and abs(q.chunk_x-cx)<=r and abs(q.chunk_z-cz)<=r:
                    pts.append((q.chunk_x,q.chunk_z))
        pts=sorted(set(pts),key=lambda q:(q[0]-cx)**2+(q[1]-cz)**2)
        return {'structure':name,'candidate_chunks':pts,'count':len(pts),'region_size':spacing,'chunk_range':chunk_range,'salt':cfg.salt,'backend':'bundled_cubiomes','mc_enum':cfg.mc_enum,'note':'Exact placement-attempt positions for the bundled Cubiomes version. Final generation still depends on biome/terrain viability.'}
    except Exception as exc:
        spacing,chunk_range,salt=STRUCTURE_RULES.get(name,(32,24,10387312))
        r=max(1,int(radius)); minx=(cx-r)//spacing-1; maxx=(cx+r)//spacing+1; minz=(cz-r)//spacing-1; maxz=(cz+r)//spacing+1
        pts=[]
        for rx in range(minx,maxx+1):
            for rz in range(minz,maxz+1):
                x,z=_region_candidate(int(seed),rx,rz,spacing,chunk_range,salt)
                if abs(x-cx)<=r and abs(z-cz)<=r:pts.append((x,z))
        pts.sort(key=lambda q:(q[0]-cx)**2+(q[1]-cz)**2)
        return {'structure':name,'candidate_chunks':pts,'count':len(pts),'region_size':spacing,'chunk_range':chunk_range,'salt':salt,'backend':'local_uniform_fallback','backend_error':str(exc),'note':'Built-in placement fallback only. Some structures need Cubiomes or generated-world data for full viability checks.'}

def biome_scan(executor,name,p):
    try:
        from .seed.bundled import cubiomes_status
        st=cubiomes_status()
        if not st.available:
            return {'backend':'cubiomes','available':False,'operation':name,'note':'Biome search uses the bundled Cubiomes component, but its local library is not ready yet. Restart F3+ while online so setup can finish.'}
        from .seed.cubiomes_api import biome_at
        seed=_seed(p.get('seed',0)); x=int(p.get('x',0)); y=int(p.get('y',64)); z=int(p.get('z',0)); radius=max(16,int(p.get('radius',256))); step=max(4,int(p.get('step',16)))
        rows=[]
        for dz in range(-radius,radius+1,step):
            for dx in range(-radius,radius+1,step):
                b=biome_at(seed,x+dx,y,z+dz,dimension=0,mc=int(p.get('mc',0)))
                rows.append((x+dx,z+dz,b.biome_id))
        counts={}
        for _,_,b in rows: counts[b]=counts.get(b,0)+1
        return {'operation':name,'samples':len(rows),'biome_counts':counts,'nearest_samples':rows[:64]}
    except Exception as e:
        return {'backend':'cubiomes','available':False,'operation':name,'error':str(e)}

def nav(name,p):
    x1=float(p.get('x1',0));y1=float(p.get('y1',64));z1=float(p.get('z1',0));x2=float(p.get('x2',100));y2=float(p.get('y2',64));z2=float(p.get('z2',100))
    dx,dy,dz=x2-x1,y2-y1,z2-z1; d=math.sqrt(dx*dx+dy*dy+dz*dz); h=math.hypot(dx,dz)
    bearing=(math.degrees(math.atan2(-dx,dz))+360)%360
    if name=='Current Position':return {'action':'capture_current_position','source':'F3+C clipboard parser'}
    if name=='Continuous Capture':return {'action':'continuous_coordinate_capture','interval_seconds':float(p.get('interval',1.0))}
    if name=='Distance Announcer':return {'distance':d,'announcement':f'{d:.1f} blocks'}
    if name=='Bearing Lock':return {'bearing':bearing,'target':(x2,z2)}
    if name=='Coordinate Offset':return {'result':(x1+float(p.get('dx',0)),y1+float(p.get('dy',0)),z1+float(p.get('dz',0)))}
    if name=='Coordinate History':return {'action':'coordinate_history','storage':'Settings.coordinate_history'}
    if name=='Waypoint Groups':return {'action':'waypoint_groups','operations':['create','rename','assign','delete']}
    if name in ('Coordinate Route','Resource Route','Structure Tour','Biome Expedition','Expedition Recorder','Survey Mode','Breadcrumb Recorder'):
        return {'operation':name,'start':(x1,y1,z1),'target':(x2,y2,z2),'distance':d,'horizontal':h,'bearing':bearing}
    if name=='Loop Detection':return {'operation':'route_loop_detection','epsilon':float(p.get('epsilon',4.0)),'algorithm':'spatial revisit detection'}
    if name=='Portal Coverage':
        r=float(p.get('radius',128));return {'radius':r,'diameter':2*r,'area':math.pi*r*r}
    if name=='Multi-Portal Jump':
        return {'overworld':(x1,z1),'nether':(x1/8,z1/8),'second_overworld':(x2,z2),'second_nether':(x2/8,z2/8),'nether_leg':math.hypot(x2/8-x1/8,z2/8-z1/8)}
    return {'operation':name,'distance':d,'bearing':bearing}

def calculator(name,p):
    v=float(p.get('value',p.get('amount',64))); sec=float(p.get('secondary',8)); x=float(p.get('x',0)); z=float(p.get('z',0))
    if name=='Delta XYZ Calculator':return {'dx':float(p.get('x2',100))-float(p.get('x1',0)),'dy':float(p.get('y2',64))-float(p.get('y1',64)),'dz':float(p.get('z2',100))-float(p.get('z1',0))}
    if name=='Material Weight':return {'blocks':int(v),'stacks':math.ceil(v/64),'shulkers':math.ceil(v/(64*27))}
    if name=='Mob Cap':return {'base_hostile_cap':70,'eligible_chunks':int(sec),'scaled_cap':math.floor(70*max(0,sec)/289)}
    if name=='Mob Switch Radius':return {'recommended_distance':max(128.0,v),'diameter':2*max(128.0,v)}
    if name=='Fortress Bounding Box':return {'center':(x,z),'nominal_piece_scan_radius':max(64,v),'note':'Use generated-world/NBT inspection for exact fortress piece boxes.'}
    if name=='Guardian Area':return {'monument_center':(x,z),'recommended_spawnproof_radius':max(128,v),'square_side':2*max(128,v)+1}
    if name=='Gateway Calculator':return {'gateway_ring_radius_approx':1024,'angle_deg':v%360,'x':round(1024*math.cos(math.radians(v%360))),'z':round(1024*math.sin(math.radians(v%360)))}
    if name=='Outer Island Distance':return {'distance':max(1000,v),'gateway_ring_reference':1024}
    if name=='End City Route':return {'start':(x,z),'target':(float(p.get('x2',1000)),float(p.get('z2',1000))),'distance':math.hypot(float(p.get('x2',1000))-x,float(p.get('z2',1000))-z)}
    if name in ('Fortress Farm Planner','Slime Farm Optimizer','Trial Chamber Planner','Blaze Route Planner'):
        return {'operation':name,'center':(x,z),'radius':v,'recommended_buffer':max(32,sec),'area':math.pi*v*v}
    return {'operation':name,'value':v,'secondary':sec}

def rng(name,p):
    prob=max(0.0,min(1.0,float(p.get('probability',0.05)))); attempts=max(1,int(p.get('attempts',20))); seed=int(p.get('seed',12345)); r=random.Random(seed)
    if name in ('Best Enchantment Search','Enchanting Simulator','Enchantment Table Layout','XP Level Planner','Enchantment Odds'):
        rolls=[r.random() for _ in range(attempts)]; return {'operation':name,'seed':seed,'rolls':rolls,'at_least_one':1-(1-prob)**attempts}
    if name in ('Loot Table Simulator','Structure Loot Simulator','Trial Chamber Loot Simulator','Trial Spawner Reward Simulator','Archaeology Loot Simulator','Fishing Loot Simulator','Piglin Barter Simulator','Mob Drop Simulator'):
        hits=[i for i in range(attempts) if r.random()<prob];return {'operation':name,'seed':seed,'attempts':attempts,'success_indices':hits,'successes':len(hits),'empirical_rate':len(hits)/attempts,'expected_rate':prob}
    if name in ('Decoration RNG','Feature Placement RNG','Geode Generator','Ore Placement Simulator','Structure Placement Preview','Tree Generation Simulator','Trial Chamber Generation'):
        pts=[(r.randrange(-16,17),r.randrange(0,256),r.randrange(-16,17)) for _ in range(attempts)];return {'operation':name,'rng_seed':seed,'sample_positions':pts}
    return {'operation':name,'seed':seed,'sequence':[r.getrandbits(31) for _ in range(attempts)]}

def safety(name,p):
    actions={
      'Action Counter':{'counter_limit':int(p.get('limit',1000))},
      'Delayed Start':{'delay_seconds':float(p.get('delay',5))},
      'Recovery Attempts':{'max_attempts':int(p.get('attempts',3))},
      'Restore Hotbar':{'restore_slot':int(p.get('slot',1))},
      'Runtime Limit':{'max_seconds':float(p.get('seconds',3600))},
      'Stuck Detection':{'window_seconds':float(p.get('seconds',10)),'minimum_displacement':float(p.get('distance',0.5))},
    }
    return {'control':name,**actions.get(name,{})}

def utility(name,p):
    if name in ('Backup Settings','Export Profiles','Import Profiles'):
        return {'action':name.lower().replace(' ','_'),'format':'JSON','path':str(p.get('path','F3PlusSettings.json'))}
    if name=='Control Bindings':return {'action':'edit_control_bindings','persistent':True}
    if name=='Coordinate Capture Settings':return {'action':'coordinate_capture_settings','source':'F3+C'}
    if name=='Movement Calibration':return {'action':'movement_calibration','distance':float(p.get('distance',100)),'seconds':float(p.get('seconds',20))}
    if name=='Turn Calibration':return {'action':'turn_calibration','degrees':float(p.get('degrees',360)),'mouse_units':float(p.get('mouse_units',1000))}
    if name=='Community Backend Status':return {'deprecated':True,'replacement':'Bundled/local implementations and explicit Cubiomes/Nether Bedrock integrations'}
    return {'action':name}

def _clusters3d(hits,min_size=2,max_distance=32):
    pts=[(h.get('x',0),h.get('y',0),h.get('z',0),h) for h in hits]
    out=[]
    for i,a in enumerate(pts):
        group=[a[3]]
        for j,b in enumerate(pts):
            if i==j:continue
            if math.dist(a[:3],b[:3])<=max_distance:group.append(b[3])
        if len(group)>=min_size:
            key=tuple(sorted((g['x'],g['y'],g['z']) for g in group))
            if key not in {tuple(sorted((g['x'],g['y'],g['z']) for g in q)) for q in out}:out.append(group)
    out.sort(key=len,reverse=True);return out

def seed_tool(name,submenu,p,executor=None):
    seed=_seed(p.get('seed',12345));cx=int(p.get('cx',0));cz=int(p.get('cz',0));radius=max(1,int(p.get('radius',64)))
    if submenu=='Structures':
        if name=='Structure Finder':
            rows={k:structure_candidates(k,seed,cx,cz,radius)['candidate_chunks'][:8] for k in ('Village','Trial Chamber','Ocean Monument','Pillager Outpost')}
            return {'seed':seed,'candidate_sets':rows}
        if name in STRUCTURE_RULES:return structure_candidates(name,seed,cx,cz,radius)
        if name in ('Compound Search','Structure Chains','Isolated Structure Finder','Structure Cluster Finder','Structure Density','Structure Heatmap','Structure Corridor','Multi-Target Locator','Portal-Optimized Structure Search'):
            sets={k:structure_candidates(k,seed,cx,cz,radius)['candidate_chunks'] for k in ('Village','Trial Chamber','Ocean Monument','Pillager Outpost')}
            total=sum(len(v) for v in sets.values());return {'operation':name,'seed':seed,'radius':radius,'candidate_counts':{k:len(v) for k,v in sets.items()},'total_candidates':total}
        return structure_candidates(name,seed,cx,cz,radius)
    if submenu=='Biomes':return biome_scan(executor,name,p)
    if submenu=='Spawners':
        world=str(p.get('world_path','')).strip()
        if world:
            from .world_scan import scan_spawners
            data=scan_spawners(world,'overworld'); data['operation']=name
            hits=data.get('hits',[])
            if name=='Double Spawner Locator': data['clusters']=_clusters3d(hits,2,32)
            elif name=='Triple Spawner Locator': data['clusters']=_clusters3d(hits,3,32)
            elif name=='Quad Spawner Locator': data['clusters']=_clusters3d(hits,4,32)
            elif name=='Spawner Cluster Ranking': data['clusters']=_clusters3d(hits,2,48)[:100]
            elif name=='Stronghold Silverfish': data['note']='Mob-spawner hits are returned; exact silverfish identification depends on spawned-entity NBT where present.'
            elif name=='Trial Chamber Spawners': data['hits']=[h for h in hits if h['id'] in ('minecraft:trial_spawner','minecraft:vault')]
            return data
        return {'operation':name,'mode':'generated_world_scan','world_path':'','ready':True,'note':'Select a generated Java world save to scan Anvil region NBT for mob/trial spawner block entities.'}
    if submenu=='Local Area':
        slime_count=0
        try:
            from .seed.slime import nearby
            slime_count=len(nearby(seed,cx,cz,min(radius,64)))
        except: pass
        return {'operation':name,'center_chunk':(cx,cz),'radius_chunks':radius,'slime_chunks':slime_count,'sampled_chunks':(2*radius+1)**2}
    if submenu=='Nether':
        if name in ('Bastion Finder','Fortress Finder','Fortress+Bastion Finder'):
            targets=['Bastion','Nether Fortress'] if '+' in name else (['Bastion'] if 'Bastion' in name else ['Nether Fortress'])
            return {'operation':name,'seed':seed,'center_chunk':(cx,cz),'radius_chunks':radius,'results':{t:structure_candidates(t,seed,cx,cz,radius)['candidate_chunks'][:32] for t in targets}}
        if name=='Nether Structure Density':
            f=structure_candidates('Nether Fortress',seed,cx,cz,radius)['candidate_chunks']
            b=structure_candidates('Bastion',seed,cx,cz,radius)['candidate_chunks']
            area=(2*radius+1)**2
            return {'operation':name,'seed':seed,'center_chunk':(cx,cz),'radius_chunks':radius,'fortress_candidates':len(f),'bastion_candidates':len(b),'total_candidates':len(f)+len(b),'sampled_chunks':area,'candidates_per_1000_chunks':(len(f)+len(b))*1000/area}
        if name=='Nether Biome Finder':
            try:
                from .seed.bundled import cubiomes_status
                st=cubiomes_status()
                if not st.available:
                    return {'operation':name,'backend':'cubiomes','available':False,'note':st.note}
                from .seed.cubiomes_api import biome_at
                step=max(1,radius//8); counts={}; samples=[]
                for dz in range(-radius,radius+1,step):
                    for dx in range(-radius,radius+1,step):
                        bx=(cx+dx)*16+8; bz=(cz+dz)*16+8
                        q=biome_at(seed,bx,64,bz,dimension=-1,mc=0)
                        bid=q.biome_id; counts[bid]=counts.get(bid,0)+1
                        if len(samples)<128:samples.append((cx+dx,cz+dz,bid))
                return {'operation':name,'seed':seed,'center_chunk':(cx,cz),'radius_chunks':radius,'step_chunks':step,'biome_counts':counts,'samples':samples,'backend':'cubiomes'}
            except Exception as exc:
                return {'operation':name,'backend':'cubiomes','available':False,'error':str(exc)}
        if name in ('Nether Bedrock Seed Cracker','Bedrock Pattern Helper','Seed Candidate Search','Seed Verification'):
            return {'operation':name,'policy':'World/structure seed recovery is delegated exclusively to Nether Bedrock Cracker.','allowed':True}
        return {'operation':name,'origin':(cx,cz),'radius':radius,'nether_scale':8,'seed':seed}
    if submenu=='World Analysis':
        rows={k:len(structure_candidates(k,seed,cx,cz,radius)['candidate_chunks']) for k in ('Village','Trial Chamber','Ocean Monument','Pillager Outpost')}
        return {'operation':name,'seed':seed,'center_chunk':(cx,cz),'radius':radius,'structure_candidate_counts':rows,'sampled_chunks':(2*radius+1)**2}
    if submenu=='Slime' and name=='Farm Location Ranking':
        from .seed.slime import nearby
        pts=nearby(seed,cx,cz,radius); scored=[]
        ps=set(pts)
        for q in pts:
            x,z=q; score=sum((x+dx,z+dz) in ps for dx in (-1,0,1) for dz in (-1,0,1))
            scored.append((score,q))
        scored.sort(reverse=True);return {'ranked':scored[:50]}
    return {'operation':name,'seed':seed}


def execute(spec,p,executor=None):
    if spec.top=='Navigation':return nav(spec.name,p)
    if spec.top=='Calculators':return calculator(spec.name,p)
    if spec.top=='RNG Tools':return rng(spec.name,p)
    if spec.top=='Safety':return safety(spec.name,p)
    if spec.top=='Utilities':return utility(spec.name,p)
    if spec.top=='Seed Tools':return seed_tool(spec.name,spec.submenu,p,executor)
    raise RuntimeError(f'No restored implementation for {spec.id}')
