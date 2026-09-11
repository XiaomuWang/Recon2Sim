# -*- coding: utf-8 -*-
import sys,json,math,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));sys.path.insert(0,str((P/'runtime').resolve()))
import carla
from replay_carla import read_scene,interpolate
d,xodr=read_scene(P/'scenario.json');compiled,_=read_scene(P/'scenario_from_xosc.json');byid={a['id']:a for a in compiled['actors']}
m=carla.Map(d['map_name'],xodr.read_text(encoding='utf-8'));rows=[]
for a in d['actors']:
 misses=[];lanes={};delta=[]
 for s in a['samples'][::3]:
  wp=m.get_waypoint(carla.Location(x=s['x'],y=-s['y'],z=s['z']),project_to_road=False,lane_type=carla.LaneType.Any)
  if wp is None:misses.append({'t':s['t'],'x':s['x'],'y':s['y']})
  else:
   key='%s/%s'%(wp.road_id,wp.lane_id);lanes[key]=lanes.get(key,0)+1
  ref=interpolate(byid[a['id']]['samples'],min(byid[a['id']]['end_t'],s['t']+.10));delta.append(math.hypot(ref['x']-s['x'],ref['y']-s['y']))
 ss=a['samples'];xy=np.array([[s['x'],s['y']] for s in ss]);t=np.array([s['t'] for s in ss]);v=np.gradient(xy,t,axis=0);acc=np.gradient(v,t,axis=0)
 rows.append({'id':a['id'],'sampled_centers':len(a['samples'][::3]),'road_center_misses':len(misses),'miss_examples':misses[:8],'roads_lanes':lanes,'xml_path_error_after_0_10s_schedule_offset_max_m':max(delta),'max_acceleration_sample_mps2':float(np.linalg.norm(acc,axis=1).max())})
print('XML trajectory differences:',[(r['id'],round(r['xml_path_error_after_0_10s_schedule_offset_max_m'],4)) for r in rows])
static=P.parent/'environment_reconstruction_0508656'/xodr.name;assert static.read_bytes()==xodr.read_bytes()
report={'client_version':'0.9.15','client_loaded_from':carla.__file__,'xodr_parse_pass':True,'xodr_identical_to_static_delivery':True,'sampled_map_waypoints':len(m.generate_waypoints(2)),'xml_path_max_error_m_after_schedule_offset':max(r['xml_path_error_after_0_10s_schedule_offset_max_m'] for r in rows),'actors':rows,'runtime_server_tested':False,'notes':'Map center coverage only; pedestrian median/crosswalk positions and shoulder parking may not belong to a navigable lane. Estimated trajectories and dimensions, no physical calibration.'}
(P/'validation/map_and_xml_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'max_xml_error_m':max(r['xml_path_error_after_0_10s_schedule_offset_max_m'] for r in rows),'center_misses':{r['id']:r['road_center_misses'] for r in rows if r['road_center_misses']},'top_acceleration':sorted([(r['id'],round(r['max_acceleration_sample_mps2'],2)) for r in rows],key=lambda r:-r[1])[:6]},indent=2))
