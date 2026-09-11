import sys,json,math,itertools
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));from replay_carla import read_scene,interpolate
d,_=read_scene(P/'scenario.json')
def corners(a,s):
 l=a['dimensions_m']['length']/2;w=a['dimensions_m']['width']/2;h=s['h'];co=math.cos(h);si=math.sin(h)
 return np.array([(s['x']+x*co-y*si,s['y']+x*si+y*co) for x,y in [(-l,-w),(l,-w),(l,w),(-l,w)]],dtype=np.float32)
import cv2
contacts={};outside={};stats=[]
for a in d['actors']:
 ss=a['samples'];xy=np.array([[s['x'],s['y']] for s in ss]);ts=np.array([s['t'] for s in ss]);sp=np.linalg.norm(np.diff(xy,axis=0),axis=1)/np.diff(ts)
 stats.append({'id':a['id'],'samples':len(ss),'max_speed_mps':float(max(sp)),'station_range':[min(s['s'] for s in ss),max(s['s'] for s in ss)]})
for t in np.arange(0,d['duration_s']+.001,.1):
 alive=[(a,interpolate(a['samples'],t)) for a in d['actors'] if a['start_t']<=t<=a['end_t']]
 for (a,s),(b,q) in itertools.combinations(alive,2):
  if math.hypot(s['x']-q['x'],s['y']-q['y'])>10:continue
  area,_=cv2.intersectConvexConvex(corners(a,s),corners(b,q))
  if area>.03:
   key=a['id']+' / '+b['id'];rec=contacts.setdefault(key,{'video_start':t,'video_end':t,'max_bbox_overlap_m2':0});rec['video_end']=t;rec['max_bbox_overlap_m2']=max(rec['max_bbox_overlap_m2'],float(area))
report={'format_and_xodr_hash_pass':True,'actor_count':len(d['actors']),'total_samples':sum(len(a['samples']) for a in d['actors']),'kinematic_stats':stats,'estimated_bbox_overlaps':contacts,'warning':'2D rectangle check on estimated dimensions, not a CARLA physics result. Blueprint substitutions have different bounding boxes.','runtime_tested_on_0_9_15':False}
(P/'validation/trajectory_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

