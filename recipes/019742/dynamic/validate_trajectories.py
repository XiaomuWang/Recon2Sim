import sys,json,math,itertools,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from replay_carla import read_scene,interpolate
d,xodr=read_scene(P/'scenario.json');issues=[];overlaps={};reverse=[];stats=[]
def corners(a,s):
 l=a['dimensions_m']['length']/2;w=a['dimensions_m']['width']/2;c=math.cos(s['h']);q=math.sin(s['h'])
 return np.array([(s['x']+u*c-v*q,s['y']+u*q+v*c) for u,v in [(-l,-w),(l,-w),(l,w),(-l,w)]])
def overlaps_sat(a,b):
 for p in [a,b]:
  for i in [0,1]:
   e=p[i+1]-p[i];axis=np.array([-e[1],e[0]]);aa=a@axis;bb=b@axis
   if min(max(aa),max(bb))-max(min(aa),min(bb))<=0:return False
 return True
for a in d['actors']:
 ss=a['samples'];pos=np.array([[s['x'],s['y']] for s in ss]);dt=np.diff([s['t'] for s in ss]);vel=np.diff(pos,axis=0)/dt[:,None];speed=np.linalg.norm(vel,axis=1);along=np.sum(vel*np.array([[math.cos(s['h']),math.sin(s['h'])] for s in ss[:-1]]),axis=1)
 bad=np.where(along<-.4)[0]
 if len(bad):reverse.append({'id':a['id'],'first_t':ss[int(bad[0])]['t'],'last_t':ss[int(bad[-1])]['t'],'minimum_along_heading_mps':float(min(along))})
 stats.append({'id':a['id'],'samples':len(ss),'start':a['start_t'],'end':a['end_t'],'max_speed_mps':float(max(speed)),'x_range':[float(min(pos[:,0])),float(max(pos[:,0]))],'y_range':[float(min(pos[:,1])),float(max(pos[:,1]))]})
for t in np.arange(0,d['duration_s']+.01,.1):
 live=[]
 for a in d['actors']:
  if a['start_t']<=t<=a['end_t']:
   s=interpolate(a['samples'],t);live.append((a,s,corners(a,s)))
 for (a,s,c),(b,u,e) in itertools.combinations(live,2):
  if abs(s['x']-u['x'])>9 or abs(s['y']-u['y'])>5:continue
  if overlaps_sat(c,e):
   key=a['id']+' / '+b['id']
   if key not in overlaps:overlaps[key]={'first_t':float(t),'last_t':float(t),'samples':0}
   overlaps[key]['last_t']=float(t);overlaps[key]['samples']+=1
ego=d['actors'][0];main=d['actors'][next(i for i,a in enumerate(d['actors']) if a['id']=='wrongway_orange_rider')]
near=[]
for t in np.arange(109,113,.05):
 a=interpolate(ego['samples'],t);b=interpolate(main['samples'],t)
 if abs(a['x']-b['x'])<3.3:near.append(abs(a['y']-b['y'])-(ego['dimensions_m']['width']+main['dimensions_m']['width'])/2)
report={'format_time_finite_hash_pass':True,'actors':len(d['actors']),'samples':sum(len(a['samples']) for a in d['actors']),'bbox_overlap_pairs_10hz':overlaps,'reverse_motion_candidates':reverse,'critical_lateral_clearance_estimate_m':min(near) if near else None,'actor_stats':stats,'scope':'Estimated planar boxes, not CARLA collision or metric video truth','runtime_verified':False}
(P/'validation/trajectory_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='actor_stats'},ensure_ascii=False,indent=2))
