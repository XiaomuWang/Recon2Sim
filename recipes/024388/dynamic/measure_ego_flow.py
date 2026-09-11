import cv2,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];src=next(P.parent.glob('*LNDEA7HF1SH024388*'));rows=[]
for cam in ['right','left']:
 cap=cv2.VideoCapture(str(src/(cam+'.mp4')));prev=None
 for j in range(0,179*3+1):
  t=j/3;cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read()
  if not ok:continue
  g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY);mask=np.zeros_like(g)
  if cam=='right':mask[70:175,70:390]=255
  else:mask[70:175,75:260]=255
  if prev is not None:
   pts=cv2.goodFeaturesToTrack(prev,250,.012,5,mask=mask);v=0.;ratio=0.;count=0
   if pts is not None and len(pts)>12:
    nxt,st,_=cv2.calcOpticalFlowPyrLK(prev,g,pts,None,winSize=(25,25),maxLevel=3)
    back,sb,_=cv2.calcOpticalFlowPyrLK(g,prev,nxt,None,winSize=(25,25),maxLevel=3)
    good=(st[:,0]>0)&(sb[:,0]>0)&(np.linalg.norm(back-pts,axis=2)[:,0]<1.2);a=pts[good,0];b=nxt[good,0];count=len(a)
    if count>12:
     M,ins=cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC,ransacReprojThreshold=1.5)
     if ins is not None:v=float(np.median(np.linalg.norm((b-a)[ins[:,0]>0],axis=1)))*3;ratio=float(ins.mean())
   rows.append({'camera':cam,'video_time':round(t,6),'speed_proxy_px_s':v,'inlier_fraction':ratio,'features':count})
  prev=g
 cap.release()
(P/'evidence/ego_static_flow.json').write_text(json.dumps(rows,indent=2))
for start in range(0,179,5):
 q=[r['speed_proxy_px_s'] for r in rows if r['camera']=='right' and start<=r['video_time']<start+5];print(start,round(float(np.median(q)),2))
