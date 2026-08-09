from __future__ import annotations
from dataclasses import dataclass
import math
from pathlib import Path

from .catalog_ids import FeatureSpec, BY_ID, BY_NAME
from .calculators import core as calc
from .calculators import technical
from .rng_tools import at_least_one, sequence, lapis_cost, bookshelf_power, grindstone_plan, mob_drop
from .rng_recovery import recover_from_next_int_pair, recover_from_next_long, inspect_state, enchantment_cracker_status
from .villagers import load_for_version
from .gameplay.presets import MACRO_PRESETS
from .gameplay.recorder import TEMPLATES
from .seed.slime import nearest as slime_nearest, nearby as slime_nearby, clusters as slime_clusters
from .seed.portal import Portal, routing_margin, link_matrix, cycles, compression, asymmetric_sequence, network_summary, optimize_candidate
from .navigation.routes import Point, route_report, greedy_route, breadcrumb_simplify, cardinal_from_bearing
from .seed.bundled import cubiomes_status, bedrock_status, build_cubiomes
from .seed import bedrock
from . import wizards
from . import restored_features

@dataclass
class FeatureResult:
    feature: str
    feature_id: str
    status: str
    data: dict
    note: str = ''

MACRO_NAMES=MACRO_PRESETS

# Dialog field tuple: key, label, default, kind.  The GUI uses this to turn a menu
# feature into a real parameterized operation instead of executing canned examples.
COMMON_FIELDS={
    'points2':[('x1','Start X',0.0,'float'),('z1','Start Z',0.0,'float'),('x2','Target X',100.0,'float'),('z2','Target Z',100.0,'float')],
    'points3':[('x1','Start X',0.0,'float'),('y1','Start Y',64.0,'float'),('z1','Start Z',0.0,'float'),('x2','Target X',100.0,'float'),('y2','Target Y',70.0,'float'),('z2','Target Z',100.0,'float')],
    'dims':[('width','Width',16,'int'),('length','Length',20,'int'),('height','Height',8,'int')],
    'seedchunk':[('seed','World seed',123456789,'text'),('cx','Chunk X',0,'int'),('cz','Chunk Z',0,'int'),('radius','Radius (chunks)',32,'int')],
}

class FeatureExecutor:
    """Concrete parameterized feature dispatch.

    `dry_run` uses the same handler and default parameters as a real GUI execution.
    There is no generic success fallback: an unimplemented catalog row is an error.
    """
    def __init__(self,minecraft_version='26.3 Snapshot 5'): self.minecraft_version=minecraft_version

    def spec(self,feature):
        if isinstance(feature,FeatureSpec):return feature
        if isinstance(feature,tuple):
            from .catalog_ids import BY_PATH
            return BY_PATH[tuple(feature)]
        if feature in BY_ID:return BY_ID[feature]
        matches=BY_NAME.get(str(feature),[])
        if len(matches)==1:return matches[0]
        if not matches:raise KeyError(f'Unknown feature: {feature}')
        raise KeyError(f'Ambiguous feature name: {feature}. Use feature ID or full menu path.')

    def input_fields(self,feature):
        s=self.spec(feature); n=s.name; top=s.top; sub=s.submenu
        if top=='Gameplay' or top in ('Wizards','Utilities','Safety','Villager Explorer'): return []
        if n in ('Capture Position','Copy Sister Coordinates','Save Sister Waypoint'): return []
        if n in ('Create Waypoint','Rename Waypoint','Delete Waypoint','Nearest Waypoint','Sort Waypoints by Distance','Waypoint Route','Multi-stop Route','Breadcrumb Simplifier'): return []
        if top=='Seed Tools' and sub=='Slime': return COMMON_FIELDS['seedchunk']
        if n=='Cubiomes Biome Query': return [('seed','World seed',12345,'text'),('mc','Cubiomes version enum (0 = bundled newest)',0,'int'),('dimension','Dimension',['Overworld','Nether','End'],'choice'),('x','X',0,'int'),('y','Y',64,'int'),('z','Z',0,'int')]
        if n=='Travel Compression':return [('overworld_gain','Overworld gain',24200.0,'float'),('nether_walk','Nether walk',1510.0,'float'),('overworld_walk','Overworld walk',485.0,'float')]
        if top=='Seed Tools' and sub=='Nether' and n in {'Nether Biome Finder','Fortress Finder','Bastion Finder','Fortress+Bastion Finder','Nether Structure Density'}:
            return [('seed','World seed',123456789,'text'),('cx','Center chunk X',0,'int'),('cz','Center chunk Z',0,'int'),('radius','Radius (chunks)',64,'int')]
        if top=='Seed Tools' and sub=='Nether' and n=='Bedrock Pattern Helper':return []
        if sub=='Portal Helpers' or (top=='Seed Tools' and sub=='Nether'):
            return [('x','Overworld X',800.0,'float'),('y','Y',64.0,'float'),('z','Overworld Z',-800.0,'float'),('other_x','Other portal X',100.0,'float'),('other_y','Other Y',64.0,'float'),('other_z','Other portal Z',100.0,'float')]
        if top=='Navigation' and n=='Bearing': return COMMON_FIELDS['points2']
        if top=='Navigation' and n in ('Distance','Midpoint','Delta XYZ','Axis Distance'): return COMMON_FIELDS['points3']
        if top=='Navigation' and n=='Travel Time': return [('distance','Distance',1000.0,'float'),('speed','Blocks / second',5.6,'float')]
        if top=='Navigation' and n in ('Chunk','Chunk Center','Chunk Border','Chunk Corner','Chunk Line Navigator'):return [('x','Block X',80,'int'),('z','Block Z',-48,'int')]
        if top=='Navigation' and n in ('Region','Region Border'):return [('x','Block X',512,'int'),('z','Block Z',-512,'int')]
        if top=='Navigation' and n=='Cardinal Snap':return [('yaw','Minecraft yaw',37.0,'float')]
        if top=='Navigation' and n=='OW/Nether Conversion':return [('x','X',800.0,'float'),('z','Z',-800.0,'float'),('to_nether','To Nether',True,'bool')]
        if top=='Calculators':
            if sub=='Coordinate':
                if n=='Bearing Calculator':return COMMON_FIELDS['points2']
                if n in ('Distance Calculator','Midpoint Calculator','Delta XYZ Calculator'):return COMMON_FIELDS['points3']
                if n=='Travel Time Calculator':return [('distance','Distance (blocks)',1000.0,'float'),('speed','Speed (blocks/second)',5.6,'float')]
                if n=='Nether Conversion Calculator':return [('x','X',800.0,'float'),('z','Z',-800.0,'float'),('to_nether','Convert to Nether',True,'bool')]
                if n=='Coordinate Snap':return [('x','Block X',800.0,'float'),('z','Block Z',-800.0,'float')]
                return COMMON_FIELDS['points3']
            if sub=='Build':return COMMON_FIELDS['dims']+[('spacing','Spacing / steps per turn',4,'int')]+[('sag','Sag',4.0,'float')]
            if sub=='Shapes':return [('radius','Radius',8,'int'),('height','Height',12,'int'),('secondary','Secondary radius / width',5,'int')]
            if sub=='Redstone':return [('value','Ticks/items/distance',64.0,'float'),('secondary','Secondary value',8.0,'float')]
            if sub=='Storage':return [('items','Items',100000,'int'),('stack_size','Stack size',64,'int'),('shulkers','Inventory shulkers',27,'int')]
            if sub=='Farm':return [('units','Plants/animals/furnaces',64,'int'),('hours','Hours/cycles',1.0,'float'),('spacing','Spacing',4,'int')]
            if sub=='Technical':return [('value','Radius/chunks/count',10.0,'float'),('secondary','Secondary',128.0,'float'),('x','X',0.0,'float'),('z','Z',0.0,'float')]
            if sub=='Speedrunning':return [('x1','Throw 1 X',0.0,'float'),('z1','Throw 1 Z',0.0,'float'),('angle1','Throw 1 yaw',-45.0,'float'),('x2','Throw 2 X',100.0,'float'),('z2','Throw 2 Z',0.0,'float'),('angle2','Throw 2 yaw',-135.0,'float')]
            if sub=='Resource Usage':return [('amount','Actions/rate/XP',10000.0,'float'),('hours','Hours / ending level',8.0,'float'),('level','Starting/Unbreaking level',3,'int')]
        if top=='RNG Tools':
            if sub=='RNG Recovery':
                if n=='Enchantment RNG Seed Cracker':return []
                if n=='Java LCG State Recovery - 2 nextInt':return [('first','First consecutive nextInt output','123456789','text'),('second','Second consecutive nextInt output','-987654321','text')]
                if n=='Java LCG State Recovery - nextLong':return [('observed_long','Observed nextLong output','1234567890123456789','text')]
                if n=='Java LCG State Inspector':return [('state','48-bit internal RNG state','0x1234abcd5678','text'),('steps','Advance / rewind steps',0,'int'),('count','Predicted nextInt outputs',8,'int')]
            return [('probability','Probability 0..1',0.05,'float'),('attempts','Attempts',20,'int'),('seed','RNG seed',12345,'int')]
        if top=='Seed Tools': return [('seed','World seed',123456789,'text'),('cx','Center chunk X',0,'int'),('cz','Center chunk Z',0,'int'),('radius','Radius (chunks)',64,'int'),('world_path','Generated world path','', 'text')]
        if top=='Navigation': return COMMON_FIELDS['points3']+[('dx','Offset X',0.0,'float'),('dy','Offset Y',0.0,'float'),('dz','Offset Z',0.0,'float'),('radius','Radius',128.0,'float')]
        if top=='Calculators': return [('value','Primary value',64.0,'float'),('secondary','Secondary value',8.0,'float'),('x','X',0.0,'float'),('z','Z',0.0,'float'),('x1','X1',0.0,'float'),('y1','Y1',64.0,'float'),('z1','Z1',0.0,'float'),('x2','X2',100.0,'float'),('y2','Y2',64.0,'float'),('z2','Z2',100.0,'float')]
        return []

    def defaults(self,feature):
        out={}
        for key,_,default,kind in self.input_fields(feature):
            out[key]=default[0] if kind=='choice' else default
        return out

    def dry_run(self,feature):return self.execute(feature,self.defaults(feature),dry_run=True)

    def execute(self,feature,params=None,dry_run=False):
        s=self.spec(feature); p=self.defaults(s); p.update(params or {})
        if s.top=='Gameplay': return self._gameplay(s,p)
        if s.top=='Navigation': return self._navigation(s,p)
        if s.top=='Seed Tools': return self._seed(s,p,dry_run)
        if s.top=='Calculators': return self._calculator(s,p)
        if s.top=='RNG Tools': return self._rng(s,p)
        if s.top=='Villager Explorer': return self._villager(s,p)
        if s.top=='Wizards' or s.name.endswith('Wizard') or s.name.endswith('Setup'): return self._wizard(s,p)
        if s.top=='Utilities': return self._utility(s,p,dry_run)
        if s.top=='Safety': return self._safety(s,p)
        raise RuntimeError(f'No handler for {s.id}')

    def _result(self,s,status,data,note=''):return FeatureResult(s.name,s.id,status,data,note)

    def _gameplay(self,s,p):
        n=s.name
        if n in MACRO_NAMES:return self._result(s,'macro',{'preset':n,'implementation':'gameplay.presets.PRESETS','safety':'MacroEngine always releases held inputs on stop/failure'})
        if n=='Strip Mine Optimizer':return self._result(s,'ok',technical.branch_mine_plan(128,3,32))
        if n=='Beacon Mining Planner':return self._result(s,'ok',{'pyramid':technical.beacon_pyramid(4,1),'coverage_side':101})
        if n=='Quarry Planner':return self._result(s,'ok',wizards.quarry())
        if n=='Macro Recorder':return self._result(s,'ok',{'record_types':['tap','click'],'recording_class':'MacroRecording','templates':list(TEMPLATES)})
        if n=='Macro Template':return self._result(s,'ok',{'templates':TEMPLATES})
        if n.endswith('Wizard'):return self._wizard(s,p)
        raise RuntimeError(f'Gameplay feature is not implemented: {s.id}')

    def _navigation(self,s,p):
        n=s.name
        if n=='Capture Position':return self._result(s,'control',{'action':'capture','method':'F3+C clipboard coordinate capture','parser':'coordinates.CoordinateCapture'})
        if n=='Copy Sister Coordinates':return self._result(s,'control',{'action':'copy_sister','conversion':'Overworld / 8 <-> Nether * 8'})
        if n=='Save Sister Waypoint':return self._result(s,'control',{'action':'save_sister_waypoint','storage':'Settings.waypoints'})
        if n in ('Create Waypoint','Rename Waypoint','Delete Waypoint'):return self._result(s,'control',{'action':n.lower().replace(' ','_'),'storage':'Settings.waypoints','persistent':True})
        if n in ('Nearest Waypoint','Sort Waypoints by Distance','Waypoint Route'):
            o=Point(0,64,0,'origin'); pts=[Point(10,64,5,'A'),Point(-20,70,30,'B'),Point(40,64,-5,'C')]
            route=greedy_route(o,pts)
            return self._result(s,'ok',{'operation':n,'route':[q.name for q in route['route']],'distance':route['distance']})
        if n=='Multi-stop Route':
            o=Point(0,64,0);pts=[Point(80,64,0,'A'),Point(80,64,80,'B'),Point(0,64,80,'C')]
            r=greedy_route(o,pts,False);return self._result(s,'ok',{'route':[q.name for q in r['route']],'distance':r['distance']})
        if n=='Breadcrumb Simplifier':
            pts=[Point(i,64,0) for i in (0,1,2,9,10,20)];out=breadcrumb_simplify(pts,8)
            return self._result(s,'ok',{'input_points':len(pts),'output_points':[(q.x,q.y,q.z) for q in out]})
        if n=='Bearing':
            a=Point(float(p['x1']),0.0,float(p['z1']));b=Point(float(p['x2']),0.0,float(p['z2']));r=route_report(a,b)
            return self._result(s,'ok',{'bearing':r['bearing'],'cardinal':r['cardinal']})
        if n in ('Distance','Midpoint','Delta XYZ','Axis Distance'):
            a=Point(float(p['x1']),float(p['y1']),float(p['z1']));b=Point(float(p['x2']),float(p['y2']),float(p['z2']));r=route_report(a,b)
            if n=='Distance':data={'horizontal':r['horizontal'],'distance_3d':r['distance']}
            elif n=='Midpoint':data={'midpoint':((a.x+b.x)/2,(a.y+b.y)/2,(a.z+b.z)/2)}
            elif n=='Delta XYZ':data={'dx':r['dx'],'dy':r['dy'],'dz':r['dz']}
            else:data={'x':abs(r['dx']),'y':abs(r['dy']),'z':abs(r['dz'])}
            return self._result(s,'ok',data)
        if n=='Travel Time':return self._result(s,'ok',{'seconds':calc.travel_time(p['distance'],p['speed'])})
        if n in ('Chunk','Chunk Center','Chunk Border','Chunk Corner','Chunk Line Navigator'):
            cx=math.floor(int(p['x'])/16);cz=math.floor(int(p['z'])/16);b=calc.chunk_bounds(cx,cz)
            if n=='Chunk Center':b['center']=(cx*16+8,cz*16+8)
            elif n=='Chunk Corner':b['corners']=[(b['x_min'],b['z_min']),(b['x_min'],b['z_max']),(b['x_max'],b['z_min']),(b['x_max'],b['z_max'])]
            elif n in ('Chunk Border','Chunk Line Navigator'):b['nearest_lines']={'x':round(int(p['x'])/16)*16,'z':round(int(p['z'])/16)*16}
            b['chunk']=(cx,cz);return self._result(s,'ok',b)
        if n in ('Region','Region Border'):
            cx=math.floor(int(p['x'])/16);cz=math.floor(int(p['z'])/16);rx=math.floor(cx/32);rz=math.floor(cz/32);b=calc.region_bounds(rx,rz);b['region']=(rx,rz);return self._result(s,'ok',b)
        if n=='Cardinal Snap':
            yaw=float(p['yaw']); card=cardinal_from_bearing(yaw); snaps={'South':0,'West':90,'North':180,'East':-90}
            return self._result(s,'ok',{'input_yaw':yaw,'cardinal':card,'snapped_yaw':snaps[card]})
        if n=='OW/Nether Conversion':return self._result(s,'ok',{'converted':calc.nether_convert(p['x'],p['z'],p['to_nether'])})
        if n=='Sister Portal':return self._result(s,'ok',{'nether':calc.nether_convert(p['x'],p['z'],True),'y':p['y']})
        if n in ('Standard Link Calculator','Portal Conflict Analysis','Optimal Portal Placement','Portal Network','Portal Separation'):
            entry=Portal('OW','Overworld',p['x'],p['y'],p['z']); ideal=Portal('N-ideal','Nether',p['x']/8,p['y'],p['z']/8); other=Portal('N-other','Nether',p['other_x'],p['other_y'],p['other_z']); portals=[entry,ideal,other]
            if n=='Standard Link Calculator':return self._result(s,'ok',{'ideal_nether':ideal.point,'ranked':[(d,q.name) for d,q in routing_margin(entry,portals)['ranked']]})
            if n=='Portal Conflict Analysis':return self._result(s,'ok',{'routing':routing_margin(entry,portals),'links':link_matrix(portals)})
            if n=='Optimal Portal Placement':return self._result(s,'ok',optimize_candidate(entry,[ideal,other]) or {'selected':None})
            if n=='Portal Network':return self._result(s,'ok',network_summary(portals))
            return self._result(s,'ok',{'distance_between_exits':math.dist(ideal.point,other.point),'ideal':ideal.point,'other':other.point})
        if n=='Highway Planner':return self._result(s,'ok',technical.portal_highway(abs(float(p['x']))+abs(float(p['z']))))
        return self._result(s,'ok',restored_features.execute(s,p,self))

    def _seed(self,s,p,dry_run):
        n=s.name
        if n=='Nether Bedrock Cracker':
            st=bedrock_status();data={'policy':'only permitted world/structure-seed recovery path','source_available':st.available,'executable':str(st.executable) if st.executable else None,'source_dir':str(st.source_dir),'automatic_acquisition':True}
            if not dry_run:
                proc=bedrock.launch(); data['launched_pid']=proc.pid; st=bedrock_status(); data.update({'source_available':st.available,'executable':str(st.executable) if st.executable else None,'source_dir':str(st.source_dir)})
            note=st.note if st.available else 'Upstream Nether Bedrock Cracker 0.3.0 will be acquired automatically on first use; after acquisition the workflow runs locally.'
            return self._result(s,'tool',data,note)
        if s.submenu=='Slime' and n=='Farm Location Ranking':
            return self._result(s,'ok',restored_features.execute(s,p,self))
        if s.submenu=='Slime':
            seed=int(str(p['seed']).strip());cx=int(p['cx']);cz=int(p['cz']);radius=max(1,int(p['radius']))
            pts=slime_nearby(seed,cx,cz,radius);groups=slime_clusters(set(pts));nearest=slime_nearest(seed,cx,cz,radius)
            if n=='Nearest Slime Chunk':data={'nearest':nearest}
            elif n=='Slime Radius':data={'chunks':pts,'count':len(pts),'radius':radius}
            elif n=='Slime Density':data={'slime_chunks':len(pts),'total_chunks':(radius*2+1)**2,'density':len(pts)/((radius*2+1)**2)}
            elif n=='Largest Connected Cluster':data={'largest':groups[0] if groups else [],'size':len(groups[0]) if groups else 0}
            else:
                target={'Adjacent Pair':2,'2x2 Cluster':4,'Triple Cluster':3,'Quad Cluster':4}[n]
                matches=[g for g in groups if len(g)>=target]
                if n=='2x2 Cluster':
                    matches=[]
                    ps=set(pts)
                    for x,z in pts:
                        q={(x,z),(x+1,z),(x,z+1),(x+1,z+1)}
                        if q<=ps:matches.append(sorted(q))
                data={'minimum_size':target,'matches':matches,'count':len(matches)}
            return self._result(s,'ok',data)
        if n=='Cubiomes Status':
            st=cubiomes_status();return self._result(s,'tool',{'source_available':st.available,'library':str(st.library) if st.library else None,'source_dir':str(st.source_dir)},st.note)
        if n=='Cubiomes Biome Query':
            st=cubiomes_status()
            if dry_run and not st.available:
                return self._result(s,'tool',{'implementation':'bundled Cubiomes biome query','source_available':False},'Bundled source is required.')
            from .seed.cubiomes_api import biome_at
            dim = {'Overworld':0,'Nether':-1,'End':1}.get(str(p['dimension']), int(p['dimension']) if str(p['dimension']).lstrip('-').isdigit() else 0)
            result = biome_at(int(str(p['seed'])), int(p['x']), int(p['y']), int(p['z']), dimension=dim, mc=int(p['mc']))
            return self._result(s,'ok',result.__dict__)
        if n=='Travel Compression':return self._result(s,'ok',compression(p['overworld_gain'],p['nether_walk'],p['overworld_walk']))
        if n in ('Asymmetric Portal Router','Vertical Isolation Analyzer','Reliability Margin','Bidirectional Link Matrix','Portal Graph','Loop Detector'):
            ps=asymmetric_sequence(start_x=p.get('x',0),start_z=p.get('z',0),stages=3);summary=network_summary(ps)
            if n=='Vertical Isolation Analyzer':return self._result(s,'ok',{'vertical_pairs':[{'a':a.name,'b':b.name,'dy':abs(a.y-b.y)} for a in ps for b in ps if a.dimension==b.dimension and a.name<b.name]})
            if n=='Reliability Margin':return self._result(s,'ok',{'margins':link_matrix(ps)})
            if n=='Bidirectional Link Matrix':return self._result(s,'ok',{'links':link_matrix(ps)})
            if n=='Portal Graph':return self._result(s,'ok',summary)
            if n=='Loop Detector':return self._result(s,'ok',{'cycles':cycles(ps)})
            return self._result(s,'ok',summary)
        return self._result(s,'ok',restored_features.execute(s,p,self))

    def _calculator(self,s,p):
        n=s.name;sub=s.submenu
        if sub=='Coordinate':
            if n=='Bearing Calculator':
                return self._result(s,'ok',{'bearing':calc.bearing(p['x1'],p['z1'],p['x2'],p['z2'])})
            if n in ('Distance Calculator','Midpoint Calculator'):
                a=(p['x1'],p['y1'],p['z1']);b=(p['x2'],p['y2'],p['z2'])
                if n=='Distance Calculator':data={'distance_3d':calc.distance3(a,b),'horizontal':calc.distance2((a[0],a[2]),(b[0],b[2]))}
                else:data={'midpoint':calc.midpoint(a,b)}
                return self._result(s,'ok',data)
            if n=='Delta XYZ Calculator':
                return self._result(s,'ok',{'dx':p['x2']-p['x1'],'dy':p['y2']-p['y1'],'dz':p['z2']-p['z1']})
            if n=='Travel Time Calculator':return self._result(s,'ok',{'seconds':calc.travel_time(p['distance'],p['speed'])})
            if n=='Nether Conversion Calculator':return self._result(s,'ok',{'converted':calc.nether_convert(p['x'],p['z'],p['to_nether'])})
            if n=='Coordinate Snap':return self._result(s,'ok',{'block':(round(p['x']),round(p['z'])),'chunk_center':(math.floor(p['x']/16)*16+8,math.floor(p['z']/16)*16+8)})
        if sub=='Build':
            w,l,h,sp=int(p['width']),int(p['length']),int(p['height']),max(1,int(p['spacing']))
            dims=calc.dimensions(w,l,h)
            if n in ('Area','Volume','Surface Area','Perimeter','Block Count','Foundation Planner'):return self._result(s,'ok',{n.lower().replace(' ','_'): dims['volume' if n=='Block Count' else n.lower().replace(' ','_')] if n not in ('Foundation Planner',) else w*l, **dims})
            if n in ('Stacks','Shulkers','Double Chests'):return self._result(s,'ok',calc.storage(dims['volume']))
            if n=='Stair Calculator':return self._result(s,'ok',calc.stair_run(h,sp))
            if n=='Spiral Staircase Planner':return self._result(s,'ok',technical.spiral_staircase(w,h,sp,True))
            if n=='Catenary Calculator':return self._result(s,'ok',technical.catenary_curve(l,p.get('sag',4.0),h))
            if n=='Roof Pitch':return self._result(s,'ok',{'rise':h,'run':w,'pitch':h/max(1,w),'layers':calc.roof_layers(w,h,h/max(1,w))})
            if n=='Wall Segments':return self._result(s,'ok',{'perimeter':2*(w+l),'segments':math.ceil(2*(w+l)/sp)})
            if n=='Bridge Span':return self._result(s,'ok',{'span':l,'supports':calc.bridge_supports(l,sp),'spacing':sp})
            if n=='Grid':return self._result(s,'ok',{'points':technical.lighting_grid(w,l,sp)['positions']})
            if n=='Lighting Grid':return self._result(s,'ok',technical.lighting_grid(w,l,sp))
            if n=='Pillar Spacing':return self._result(s,'ok',{'x_supports':calc.bridge_supports(w,sp),'z_supports':calc.bridge_supports(l,sp)})
            if n=='Road Planner':return self._result(s,'ok',{'length':l,'width':w,'blocks':w*l,'markers':math.ceil(l/sp)+1})
            if n=='Crop Layout':return self._result(s,'ok',{'plots':calc.grid_count(w,l,sp),'area':w*l,'spacing':sp})
            if n=='Gradient Ratio':return self._result(s,'ok',{'rise':h,'run':l,'ratio':h/max(1,l),'percent_grade':100*h/max(1,l)})
            if n=='Chunk Grid Builder':return self._result(s,'ok',{'chunks_x':math.ceil(w/16),'chunks_z':math.ceil(l/16),'chunks':math.ceil(w/16)*math.ceil(l/16)})
            if n=='Circle Layer Export':return self._result(s,'ok',{'radius':w,'points':calc.circle(w,False)})
            if n=='Beacon Offset':return self._result(s,'ok',{'center_offset':(w//2,l//2),'pyramid':technical.beacon_pyramid(min(4,max(1,h)),1)})
        if sub=='Shapes':
            r=max(1,int(p['radius']));h=max(1,int(p['height']));q=max(1,int(p['secondary']))
            if n=='Circle':data={'points':calc.circle(r,False)}
            elif n=='Filled Circle':data={'points':calc.circle(r,True)}
            elif n=='Sphere':data={'points':calc.sphere(r,False)}
            elif n=='Hollow Sphere':data={'points':calc.sphere(r,True)}
            elif n=='Dome':data={'points':calc.dome(r,True)}
            elif n=='Cylinder':data={'points':calc.cylinder(r,h,True)}
            elif n=='Cone':data={'points':calc.cone(r,h)}
            elif n in ('Spiral','Helix'):data={'points':calc.spiral(r,h,2)}
            elif n=='Double Helix':data={'strand_a':calc.spiral(r,h,2),'strand_b':[(-x,y,-z) for x,y,z in calc.spiral(r,h,2)]}
            elif n=='Hexagon':data={'vertices':calc.polygon(r,6)}
            elif n=='Octagon':data={'vertices':calc.polygon(r,8)}
            elif n=='Ellipse':data={'points':calc.ellipse(r,q,False)}
            elif n=='Pyramid':data={'layers':[{'y':y,'half_width':max(0,r-y)} for y in range(min(h,r+1))]}
            elif n=='Diamond':data={'points':[(x,z) for x in range(-r,r+1) for z in range(-r,r+1) if abs(x)+abs(z)==r]}
            elif n=='Rounded Rectangle':data={'width':2*r+q,'length':2*r+q,'corner_radius':r,'straight_section':q}
            elif n=='Arch':data={'points':[(x,round(math.sqrt(max(0,r*r-x*x)))) for x in range(-r,r+1)]}
            else:raise RuntimeError(f'Unhandled shape {n}')
            data['count']=sum(len(v) for v in data.values() if isinstance(v,list)) if any(isinstance(v,list) for v in data.values()) else len(data)
            return self._result(s,'ok',data)
        if sub=='Redstone':
            v=float(p['value']);sec=float(p['secondary'])
            if n=='Tick Converter':data=calc.tick_convert(v)
            elif n=='Hopper Timer':data=calc.hopper_timer(int(v))
            elif n=='Comparator Strength':data={'signal':calc.comparator_strength(int(v),max(1,int(sec)))}
            elif n in ('Repeater Delay','Observer Delay','Pulse Extender','Clock Period','Counter Timing','Signal Timing'):data=calc.repeater_delay([max(1,min(4,int(v))),max(1,min(4,int(sec)))])
            elif n=='Minecart Timing':data={'distance':v,'speed_blocks_per_second':8.0,'seconds':v/8.0,'ticks':v/8.0*20}
            elif n=='Water Stream Timing':data={'distance':v,'assumed_speed':4.0,'seconds':v/4.0,'note':'Approximate transport speed; layout changes actual timing.'}
            elif n=='Ice Boat Timing':data={'distance':v,'speed':sec,'seconds':v/max(.001,sec)}
            elif n=='Crafter Throughput':data={'items_per_hour':calc.crafter_throughput(max(.001,v),sec)}
            else:raise RuntimeError(f'Unhandled redstone {n}')
            return self._result(s,'ok',data)
        if sub=='Storage':
            items=int(p['items']);stack=int(p['stack_size']);sh=int(p['shulkers'])
            if n in ('Storage Capacity','Bulk Materials','Shulker Requirement','Chest Requirement'):data=calc.storage(items,stack)
            elif n=='Item Compression':data=calc.compression(items,9)
            elif n=='Material Logistics':data=calc.logistics(items,36,stack,sh)
            elif n=='Transport Trips':data=technical.shulker_trips(items,sh,stack)
            else:return self._result(s,'ok',restored_features.execute(s,p,self))
            return self._result(s,'ok',data)
        if sub=='Farm':
            units=max(0,int(p['units']));hours=float(p['hours']);sp=max(1,int(p['spacing']))
            if n=='Crop Yield':data={'plants':units,'harvests':hours,'expected_items':units*hours*2.5,'note':'Uses a configurable planning mean of 2.5 items/plant.'}
            elif n=='Tree Yield':data={'trees':units,'cycles':hours,'logs_at_4_per_tree':units*hours*4}
            elif n=='Animal Breeding':data={'starting_adults':units,'cycles':int(hours),'population_upper_bound':calc.breeding_cycles(units,int(hours))}
            elif n=='Villager Breeding':data={'breedings':units,'bread':calc.villager_food(units,'bread'),'carrots':calc.villager_food(units,'carrot')}
            elif n=='Furnace Array':data={'furnaces':units,'items':calc.furnace_throughput(units,10,hours)}
            elif n=='Fuel Optimizer':data={'items_to_smelt':units,'coal_like_fuel':calc.fuel_items(units,8),'bamboo_like_fuel':calc.fuel_items(units,.25)}
            elif n in ('Beacon Pyramid','Beacon Coverage'):data=technical.beacon_pyramid(min(4,max(1,sp)),max(1,units))
            elif n in ('Sugar Cane Layout','Bamboo Layout','Crop Row Calculator'):data={'plants':units,'spacing':sp,'linear_length':units*sp}
            elif n=='Kelp Tower':data={'columns':units,'height':max(1,sp),'plant_blocks':units*max(1,sp)}
            elif n=='Bee Apiary':data={'hives':units,'recommended_flowers':max(units,units*2),'spacing':sp}
            elif n=='Villager Hall Layout':data={'villagers':units,'workstations':units,'beds_if_breeding':units,'aisle_spacing':sp}
            elif n=='Animal Pen':data={'animals':units,'suggested_area':max(4,math.ceil(units*1.5)),'suggested_side':math.ceil(math.sqrt(max(4,units*1.5)))}
            else:return self._result(s,'ok',restored_features.execute(s,p,self))
            return self._result(s,'ok',data)
        if sub=='Technical':
            v=float(p['value']);sec=float(p['secondary']);x=float(p['x']);z=float(p['z'])
            if n=='Mob Cap Calculator':return self._result(s,'ok',technical.mob_cap(max(1,int(x) or 1),max(0,int(sec)),max(0,int(v))))
            if n=='Despawn Radius Planner':return self._result(s,'ok',technical.despawn_shell(x,z,32,v))
            if n=='Item Sorter Planner':return self._result(s,'ok',technical.item_sorter_capacity(max(0,int(v))))
            if n=='Chunk Alignment':data=calc.chunk_bounds(math.floor(x/16),math.floor(z/16))
            elif n=='Region Alignment':data=calc.region_bounds(math.floor(x/512),math.floor(z/512))
            elif n=='Cardinal Alignment':data={'x_axis_distance':abs(x),'z_axis_distance':abs(z),'nearest_axis':'x' if abs(x)<abs(z) else 'z'}
            elif n=='Build Rotation':data={'90':calc.rotate_point(x,z,90),'180':calc.rotate_point(x,z,180),'270':calc.rotate_point(x,z,270)}
            elif n=='Symmetry':data={'mirror_x':calc.mirror_point(x,64,z,0,64,0,'x'),'mirror_z':calc.mirror_point(x,64,z,0,64,0,'z')}
            elif n=='Blueprint Coordinates':data={'origin':(x,z),'chunk':(math.floor(x/16),math.floor(z/16)),'region':(math.floor(x/512),math.floor(z/512))}
            elif n in ('Chunk Loader Planner','Chunk Loader Radius'):data=technical.chunk_loader_grid(max(1,int(v)),max(1,int(v)),max(0,int(sec)))
            elif n in ('Loaded Chunk Area','Render Distance'):data=calc.loaded_chunk_square(int(v))
            elif n=='Simulation Distance':data=technical.simulation_square(int(v))
            elif n=='Spawn Sphere':data=calc.spawn_sphere(v)
            elif n=='Mob Spawn Area':data=technical.mob_spawn_shell(24,v)
            elif n=='Random Tick Area':data=calc.random_tick_square(int(v))
            elif n=='Spawnproof Calculator':data={'radius':v,'square_blocks':math.ceil((2*v+1)**2),'circle_area':math.pi*v*v}
            elif n in ('Farm Separation','Iron Farm Spacing','Villager Gossip Radius','Raid Distance'):data={'distance':calc.distance2((x,z),(x+v,z+sec))}
            elif n=='Perimeter Planner':data=technical.excavation(int(v),int(v),int(sec),4.0)
            elif n=='Branch Density Calculator':data=technical.branch_mine_plan(int(sec),max(1,int(v)),32)
            elif n=='Tunnel Progress':data={'blocks':v,'speed':sec,'seconds':v/max(.001,sec)}
            elif n=='Torch Planner':data={'distance':v,'spacing':max(1,sec),'torches':math.floor(v/max(1,sec))+1}
            else:return self._result(s,'ok',restored_features.execute(s,p,self))
            return self._result(s,'ok',data)
        if sub=='Speedrunning':
            if n=='Eye Throw Triangulation':return self._result(s,'ok',{'target':calc.triangulate_ray((p['x1'],p['z1']),p['angle1'],(p['x2'],p['z2']),p['angle2'])})
            if n=='Stronghold Ring':return self._result(s,'ok',{'rings':[calc.stronghold_ring(i) for i in range(8)]})
            if n=='Blind Travel':
                # Portal conversion math only; the actual speedrun blind destination remains probabilistic.
                tx,tz=calc.nether_convert(p['x2'],p['z2'],True);return self._result(s,'ok',{'target_nether':(tx,tz),'distance':calc.distance2((p['x1'],p['z1']),(tx,tz))})
        if sub=='Resource Usage':
            a=float(p['amount']);hours=float(p['hours']);lvl=int(p['level'])
            if n=='XP Level Calculator':return self._result(s,'ok',technical.xp_between_levels(lvl,int(hours)))
            if n=='Mending Repair Calculator':return self._result(s,'ok',technical.mending_repair(int(a),max(1,lvl)))
            if n=='Anvil Prior-Work Planner':return self._result(s,'ok',technical.anvil_prior_work_plan(int(a)))
            if n in ('Tool Wear','Material Progress'):data=calc.tool_wear(int(a),lvl)
            else:data={'rate_per_hour':a,'hours':hours,'total':calc.consumption(a,hours),'resource':n}
            return self._result(s,'ok',data)
        return self._result(s,'ok',restored_features.execute(s,p,self))

    def _rng(self,s,p):
        n=s.name
        if s.submenu=='RNG Recovery':
            if n=='Enchantment RNG Seed Cracker':
                return self._result(s,'tool',enchantment_cracker_status(),'Opens Earthcomputer EnchantmentCracker v1.9 on first use; this is gameplay/player RNG recovery, not world-seed recovery.')
            if n=='Java LCG State Recovery - 2 nextInt':
                rows=recover_from_next_int_pair(p['first'],p['second'])
                return self._result(s,'ok',{'candidate_count':len(rows),'candidates':rows,'source':'two consecutive unbounded java.util.Random.nextInt() outputs','world_seed_recovery':False})
            if n=='Java LCG State Recovery - nextLong':
                rows=recover_from_next_long(p['observed_long'])
                return self._result(s,'ok',{'candidate_count':len(rows),'candidates':rows,'source':'one java.util.Random.nextLong() output','world_seed_recovery':False})
            if n=='Java LCG State Inspector':
                return self._result(s,'ok',{**inspect_state(p['state'],p['steps'],p['count']),'world_seed_recovery':False})
            raise RuntimeError(f'RNG recovery feature is not implemented: {s.id}')
        prob=max(0,min(1,float(p['probability'])));attempts=max(0,int(p['attempts']));seed=int(p['seed'])
        if n in ('Enchantment Probability','RNG Probability Calculator','Loot Odds Calculator','Rare Drop Odds','Barter Odds','Trial Reward Odds'):return self._result(s,'ok',at_least_one(prob,attempts))
        if n=='Bookshelf Planner':return self._result(s,'ok',bookshelf_power(min(15,attempts)))
        if n=='Lapis Cost Calculator':return self._result(s,'ok',lapis_cost(attempts,3))
        if n=='Grindstone Reset Planner':return self._result(s,'ok',grindstone_plan(attempts))
        if n in ('Enchantment Sequence Simulator','RNG Sequence Viewer','RNG Timeline'):return self._result(s,'ok',{'seed':seed,'sequence':sequence(seed,max(1,attempts))})
        if n=='Mob Drop Simulator':return self._result(s,'ok',mob_drop(prob,attempts))
        return self._result(s,'ok',restored_features.execute(s,p,self))

    def _villager(self,s,p):
        n=s.name; trades,source=load_for_version(self.minecraft_version)
        if s.submenu=='Professions':
            prof=n.lower();rows=[t for t in trades if t.profession==prof]
            return self._result(s,'ok',{'profession':prof,'trades':[t.__dict__ for t in rows],'source_version':source})
        if n in ('Trade Browser','Trade Search','Trade Comparison','Emerald Calculator','Trade Cycle Calculator','Librarian Browser','Refresh Trades From Installed Version'):
            rows=[t.__dict__ for t in trades[:25]]
            return self._result(s,'ok',{'operation':n,'trades_loaded':len(trades),'preview':rows,'source_version':source})
        if n=='Zombie Cure Calculator':return self._result(s,'ok',{'base_cost':20,'discount':5,'result':15,'minimum':1})
        if n=='Villager Hall Calculator':return self._result(s,'ok',wizards.villager_hall())
        if n=='Workstation Count':return self._result(s,'ok',{'villagers':20,'workstations':20})
        if n=='Breeding Food Calculator':return self._result(s,'ok',{'breedings':10,'bread':30,'carrots':120,'potatoes':120,'beetroot':120})
        raise RuntimeError(f'Villager feature is not implemented: {s.id}')

    def _wizard(self,s,p):
        n=s.name
        if 'Branch' in n:return self._result(s,'ok',wizards.branch_mine())
        if 'Quarry' in n:return self._result(s,'ok',wizards.quarry())
        if 'Perimeter' in n:return self._result(s,'ok',wizards.perimeter())
        if 'Crop' in n:return self._result(s,'ok',wizards.crop())
        if 'Tree' in n:return self._result(s,'ok',wizards.tree())
        if 'Villager' in n:return self._result(s,'ok',wizards.villager_hall())
        if 'Highway' in n:return self._result(s,'ok',wizards.nether_highway())
        if 'Asymmetric' in n:return self._result(s,'ok',wizards.asymmetric_portal())
        if 'Portal' in n:return self._result(s,'ok',wizards.portal_network())
        if 'Lighting' in n:return self._result(s,'ok',wizards.lighting())
        if 'Beacon' in n:return self._result(s,'ok',wizards.beacon_network())
        if 'Build Material' in n:return self._result(s,'ok',wizards.build_material())
        raise RuntimeError(f'Wizard is not implemented: {s.id}')

    def _utility(self,s,p,dry_run):
        n=s.name
        if n=='Minecraft Version':return self._result(s,'control',{'selected_version':self.minecraft_version,'editable':True})
        if n=='Compatibility Report':
            cs=cubiomes_status();bs=bedrock_status();return self._result(s,'ok',{'minecraft':self.minecraft_version,'cubiomes_source':cs.available,'cubiomes_library':bool(cs.library),'bedrock_cracker':bs.available,'world_seed_policy':'nether_bedrock_only'})
        if n=='Installed Version Scan':
            home=Path.home(); candidates=[home/'.minecraft'/'versions',home/'Library/Application Support/minecraft/versions',Path.home()/'AppData/Roaming/.minecraft/versions']
            found=[]
            for base in candidates:
                if base.exists():found.extend(sorted(p.name for p in base.iterdir() if p.is_dir()))
            return self._result(s,'ok',{'versions':sorted(set(found)),'searched':[str(x) for x in candidates]})
        if n=='Trade Data Status':
            rows,source=load_for_version(self.minecraft_version);return self._result(s,'ok',{'source':source,'trade_count':len(rows)})
        if n=='Cubiomes Setup & Status':
            st=cubiomes_status();data={'source_available':st.available,'library':str(st.library) if st.library else None}
            if st.available and not dry_run:
                try:data['built_library']=str(build_cubiomes());data['build_ok']=True
                except Exception as exc:data['build_ok']=False;data['error']=str(exc)
            return self._result(s,'tool',data,st.note)
        if n=='Nether Bedrock Cracker Status':
            st=bedrock_status();return self._result(s,'tool',{'available':st.available,'automatic_acquisition':True,'source_dir':str(st.source_dir),'executable':str(st.executable) if st.executable else None},st.note if st.available else 'Not cached yet; acquired automatically from the pinned upstream 0.3.0 release when first used.')
        if n in ('Export Profiles','Import Profiles'):return self._result(s,'control',{'action':n.lower().replace(' ','_'),'format':'JSON','settings_object':'Settings'})
        return self._result(s,'control',restored_features.execute(s,p,self))

    def _safety(self,s,p):
        actions={
            'Emergency Stop':('MacroEngine.stop','Stops worker and releases all held keys/buttons.'),
            'Pause/Resume':('MacroEngine.toggle_pause','Pauses execution without discarding the active routine.'),
            'Release Held Inputs':('InputBackend.release_all','Immediately releases tracked keyboard and mouse holds.'),
            'Focus Loss Stop':('GUI focus hook','Optional stop when Minecraft/application focus is lost; platform verification required.'),
        }
        if s.name not in actions:return self._result(s,'control',restored_features.execute(s,p,self))
        method,behavior=actions[s.name];return self._result(s,'control',{'method':method,'behavior':behavior})
