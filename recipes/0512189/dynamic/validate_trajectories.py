import json,sys,math,hashlib
from pathlib import Path
import numpy as np
import carla
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));from replay_carla import read_scene,interpolate
d,xodr=read_scene(P/'scenario.json');m=carla.Map(d['map_name'],xodr.read_text());errors=[];motion=[];overlaps={}
def sat(a,sa,b,sb):
 ca=np.array([sa['x'],sa['y']]);cb=np.array([sb['x'],sb['y']]);delta=cb-ca
 ua=np.array([math.cos(sa['h']),math.sin(sa['h'])]);va=np.array([-ua[1],ua[0]]);ub=np.array([math.cos(sb['h']),math.sin(sb['h'])]);vb=np.array([-ub[1],ub[0]])
 ha=np.array([a['dimensions_m']['length'],a['dimensions_m']['width']])/2;hb=np.array([b['dimensions_m']['length'],b['dimensions_m']['width']])/2
 pen=100
 for axis in [ua,va,ub,vb]:
  r=ha[0]*abs(axis@ua)+ha[1]*abs(axis@va)+hb[0]*abs(axis@ub)+hb[1]*abs(axis@vb)-abs(delta@axis)
  if r<=0:return 0
  pen=min(pen,r)
 return float(pen)
for a in d['actors']:
 ss=a['samples'];t=np.array([s['t'] for s in ss]);xy=np.array([[s['x'],s['y']] for s in ss]);vel=np.diff(xy,axis=0)/np.diff(t)[:,None];v=np.linalg.norm(vel,axis=1);acc=np.linalg.norm(np.diff(vel,axis=0)*d['fps'],axis=1)
 motion.append({'id':a['id'],'max_speed_mps':float(v.max()),'max_accel_mps2':float(acc.max()),'duration':a['end_t']-a['start_t']})
 if not np.isfinite(xy).all():errors.append(a['id']+' nonfinite')
 if v.max()>18:errors.append(a['id']+' excessive estimated speed')
 if a['category'] not in ['pedestrian','parked','parked_vehicle']:
  for s in ss[::3]:
   w=m.get_waypoint(carla.Location(x=s['x'],y=-s['y'],z=0),project_to_road=False,lane_type=carla.LaneType.Driving)
   if w is None:errors.append(a['id']+' center outside XODR at '+str(s['t']));break
for t in np.arange(0,120.001,.1):
 active=[(a,interpolate(a['samples'],float(t))) for a in d['actors'] if a['start_t']<=t<=a['end_t']]
 for i,(a,sa) in enumerate(active):
  for b,sb in active[i+1:]:
   if abs(sa['x']-sb['x'])>(a['dimensions_m']['length']+b['dimensions_m']['length'])/2+2:continue
   if abs(sa['y']-sb['y'])>(a['dimensions_m']['length']+b['dimensions_m']['length'])/2+2:continue
   depth=sat(a,sa,b,sb)
   if depth>.04:
    k=a['id']+' / '+b['id'];r=overlaps.setdefault(k,{'pair':k,'first_t':round(float(t),2),'last_t':round(float(t),2),'samples':0,'max_penetration_m':0});r['last_t']=round(float(t),2);r['samples']+=1;r['max_penetration_m']=max(r['max_penetration_m'],depth)
report={'data_valid':not errors,'errors':errors,'actors':len(d['actors']),'pose_count':sum(len(a['samples']) for a in d['actors']),'motion_limits':motion,'estimated_bbox_overlaps':list(overlaps.values()),'overlap_pairs':len(overlaps),'sampling_hz':10,'xodr_sha256':hashlib.sha256(xodr.read_bytes()).hexdigest(),'runtime_verified':False,'scope':'Map center coverage and estimated oriented-box clearance; not native blueprint collision or real-world accuracy.'}
(P/'validation/trajectory_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({'errors':errors,'overlaps':list(overlaps.values()),'max_speed':max(r['max_speed_mps'] for r in motion)},indent=2));assert not errors;assert not overlaps
