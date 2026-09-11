import json,math,sys,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from replay_carla import read_scene,interpolate
d,xodr=read_scene(P/'scenario.json');hits={};rows=[]
def box(a,s):
 h=s['h'];rot=np.array([[math.cos(h),-math.sin(h)],[math.sin(h),math.cos(h)]])
 l=a['dimensions_m']['length']/2;w=a['dimensions_m']['width']/2
 return np.array([[-l,-w],[l,-w],[l,w],[-l,w]])@rot.T+[s['x'],s['y']]
def overlap(p,q):
 depth=1000
 for b in [p,q]:
  for i in [0,1]:
   v=b[i+1]-b[i];n=np.array([-v[1],v[0]])/np.linalg.norm(v);a=p@n;c=q@n
   delta=min(a.max(),c.max())-max(a.min(),c.min())
   if delta<=0:return 0
   depth=min(depth,delta)
 return depth
for a in d['actors']:
 ss=a['samples'];xy=np.array([[s['x'],s['y']] for s in ss]);tt=np.array([s['t'] for s in ss]);speed=np.linalg.norm(np.diff(xy,axis=0),axis=1)/np.diff(tt)
 rows.append(dict(id=a['id'],max_speed_m_s=round(float(speed.max()),3),distance_m=round(float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()),2)))
for t in np.arange(0,d['duration_s']+.001,.2):
 active=[a for a in d['actors'] if a['start_t']<=t<=a['end_t']];ps=[box(a,interpolate(a['samples'],t)) for a in active]
 for i,a in enumerate(active):
  for j in range(i+1,len(active)):
   b=active[j]
   if np.linalg.norm(ps[i].mean(axis=0)-ps[j].mean(axis=0))>8:continue
   dep=overlap(ps[i],ps[j])
   if dep>.03:
    key=a['id']+' / '+b['id'];r=hits.setdefault(key,dict(pair=key,start=round(float(t),2),end=0.,max_overlap_m=0.));r['end']=round(float(t),2);r['max_overlap_m']=round(max(r['max_overlap_m'],float(dep)),3)
report=dict(poses_valid=True,xodr_sha256=hashlib.sha256(xodr.read_bytes()).hexdigest(),same_as_static=hashlib.sha256((P.parent/'environment_reconstruction_024388/LuoboTurn024388.xodr').read_bytes()).hexdigest()==d['xodr_sha256'],actor_count=len(rows),pose_count=sum(len(a['samples']) for a in d['actors']),stats=rows,estimated_bbox_overlap_windows=list(hits.values()),sample_step_s=.2,runtime_verified=False)
(P/'validation/trajectory_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(list(hits.values()),indent=2));print('max speed',max(rows,key=lambda x:x['max_speed_m_s']))
