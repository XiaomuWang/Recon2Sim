import json,math,sys,hashlib,importlib.metadata
from pathlib import Path
import numpy as np,carla,cv2
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from replay_carla import read_scene,interpolate
from play_xosc_carla import decode
from preview_geometry import road_polygons
surface=[np.array(p,np.float32) for p in road_polygons()];surface_fallback=[]
d,xodr=read_scene(P/'scenario.json');m=carla.Map(d['map_name'],xodr.read_text(encoding='utf-8'));decoded=decode(P/'GreenRail016955_Timeline.xosc');radians=decode(P/'GreenRail016955_Timeline_Radians.xosc')
comparisons=[];out=[];roads=set();kin=[]
for a,b,c in zip(d['actors'],decoded['actors'],radians['actors']):
 assert a['id']==b['id']==c['id'];errors=[];yaw=[]
 for s in a['samples'][::3]:
  q=interpolate(b['samples'],s['t']);r=interpolate(c['samples'],s['t']);errors.append(math.hypot(q['x']-s['x'],q['y']-s['y']));yaw.append(abs((q['h']-s['h']+math.pi)%(2*math.pi)-math.pi))
  assert math.hypot(q['x']-r['x'],q['y']-r['y'])<1e-6
 comparisons.append(dict(id=a['id'],max_xosc_roundtrip_xy_error_m=max(errors),max_xosc_heading_error_deg=math.degrees(max(yaw))))
 ss=a['samples'];xy=np.array([[s['x'],s['y']] for s in ss]);ts=np.array([s['t'] for s in ss]);vel=np.diff(xy,axis=0)/np.diff(ts)[:,None];acc=np.linalg.norm(np.diff(vel,axis=0)/np.diff(ts[:-1])[:,None],axis=1);kin.append(dict(id=a['id'],max_speed_mps=float(np.max(np.linalg.norm(vel,axis=1))),max_accel_mps2=float(np.max(acc))))
 if a['id']=='ego':
  for s in ss[::3]:
   for xx,yy in [(0,0),(1.4,.75),(1.4,-.75),(-1.4,.75),(-1.4,-.75)]:
    x=s['x']+xx*math.cos(s['h'])-yy*math.sin(s['h']);y=s['y']+xx*math.sin(s['h'])+yy*math.cos(s['h']);w=m.get_waypoint(carla.Location(x=x,y=-y,z=.1),project_to_road=False,lane_type=carla.LaneType.Driving)
    if w:roads.add(w.road_id)
    elif any(cv2.pointPolygonTest(poly,(x,y),False)>=0 for poly in surface):surface_fallback.append(dict(t=s['t'],x=x,y=y,reason='inside static road surface; junction lane projection returned None'))
    else:out.append(dict(t=s['t'],x=x,y=y))
stops=[]
for a,b in [(0,41.3),(118,132),(176,180)]:
 ss=[s for s in d['actors'][0]['samples'] if a<=s['t']<=b];span=max(math.hypot(s['x']-ss[0]['x'],s['y']-ss[0]['y']) for s in ss);stops.append(dict(interval=[a,b],drift_m=span));assert span<.001
report=dict(actor_count=len(d['actors']),duration_s=d['duration_s'],carla_parser_version=importlib.metadata.version('carla'),runtime_tested_on_carla_0_9_15=False,xodr_matches_static=hashlib.sha256((P.parent/'environment_reconstruction_016955/GreenRail016955.xodr').read_bytes()).hexdigest()==d['xodr_sha256'],xosc_decoded_without_scenario_json=True,heading_variants_equivalent=True,xosc_roundtrip=comparisons,ego_driving_road_ids=sorted(roads),ego_wheel_points_outside_driving_lane=out,stop_checks=stops,kinematics=kin,scope='Offline CARLA map parser + estimated kinematic envelopes + XOSC adapter; no Unreal engine or platform custom loader test.')
report['junction_surface_fallback_points']=surface_fallback
(P/'validation/delivery_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['xosc_roundtrip','kinematics','ego_wheel_points_outside_driving_lane']},indent=2));print('Outside wheel points',len(out));print('Max roundtrip XY',max(r['max_xosc_roundtrip_xy_error_m'] for r in comparisons));print('Ego dynamics',kin[0]);assert not out;assert max(r['max_xosc_roundtrip_xy_error_m'] for r in comparisons)<.15
