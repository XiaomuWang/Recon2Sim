"""Estimate last ego-motion timing from static bands; offsets remain approximate."""
import cv2,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];src=next(P.parent.glob('*LHTDA4B45SYANA031*'));out={}
for name,a,b in [('front',20,30),('rear',27,38),('left',20,31),('right',27,40)]:
 c=cv2.VideoCapture(str(src/(name+'.mp4')));prev=None;rows=[]
 for t in np.arange(a,b,.1):
  c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
  if not ok:break
  g=cv2.cvtColor(cv2.resize(f,(640,360)),cv2.COLOR_BGR2GRAY);mask=np.zeros_like(g)
  if name in ['left','right']:mask[35:120,135:500]=255
  else:mask[35:125,20:210]=255;mask[35:125,460:620]=255
  if prev is not None:
   pts=cv2.goodFeaturesToTrack(prev,300,.01,5,mask=mask);v=0.;n=0
   if pts is not None and len(pts)>10:
    nxt,st,_=cv2.calcOpticalFlowPyrLK(prev,g,pts,None,winSize=(21,21),maxLevel=3);good=st[:,0]>0;aa=pts[good,0];bb=nxt[good,0]
    if len(aa)>10:
     _,inl=cv2.estimateAffinePartial2D(aa,bb,method=cv2.RANSAC,ransacReprojThreshold=1.3)
     if inl is not None:v=float(np.median(np.linalg.norm(bb-aa,axis=1)[inl[:,0]>0]))/.1;n=int(inl.sum())
   rows.append({'file_t':round(float(t),3),'flow_px_s':v,'inliers':n})
  prev=g
 c.release();out[name]=rows
 arr=np.array([r['flow_px_s'] for r in rows]);print(name,'peak',rows[int(np.argmax(arr))]['file_t'],'last>3',max(r['file_t'] for r in rows if r['flow_px_s']>3))
(P/'evidence/sync_static_flow.json').write_text(json.dumps(out,indent=2))
