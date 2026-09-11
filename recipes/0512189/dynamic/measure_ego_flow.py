import cv2,numpy as np,json
from pathlib import Path
p=Path('dynamic_replay_0512189');src=next(Path('.').glob('*LA71AUB13S0512189*'));rows=[];c=cv2.VideoCapture(str(src/'right.mp4'));prev=None
for frame in range(600):
 t=frame*.2;c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
 if not ok:break
 g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY);mask=np.zeros_like(g);mask[60:270,45:880]=255
 if prev is not None:
  pts=cv2.goodFeaturesToTrack(prev,250,.015,8,mask=mask);dx=0.;n=0;frac=0
  if pts is not None and len(pts)>12:
   nxt,st,_=cv2.calcOpticalFlowPyrLK(prev,g,pts,None,winSize=(25,25),maxLevel=3);back,sb,_=cv2.calcOpticalFlowPyrLK(g,prev,nxt,None,winSize=(25,25),maxLevel=3)
   good=(st[:,0]>0)&(sb[:,0]>0)&(np.linalg.norm(back-pts,axis=2)[:,0]<1.2);a=pts[good,0];b=nxt[good,0];n=len(a)
   if n>12:
    mat,inl=cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC,ransacReprojThreshold=2)
    if inl is not None and sum(inl[:,0])>8:dx=float(np.median((b-a)[inl[:,0]>0,0]));frac=float(np.mean(inl))
  rows.append({'right_file_t':t,'front_file_t_approx':t-1.4,'dx':dx,'speed_proxy_px_s':abs(dx)/.2,'features':n,'inlier_fraction':frac})
 prev=g
(p/'evidence/ego_static_flow.json').write_text(json.dumps(rows,indent=2))
for i in range(120):
 a=[r['speed_proxy_px_s'] for r in rows if i<=r['front_file_t_approx']<i+1]
 if a and (i%5==0 or 78<=i<=110):print(i,round(float(np.median(a)),2))
