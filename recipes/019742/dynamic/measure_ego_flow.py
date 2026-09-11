import cv2,numpy as np,pathlib,json
src=next(pathlib.Path('.').glob('*LNDEA7HF1SH019742*'))
c=cv2.VideoCapture(str(src/'left.mp4'));rows=[];prev=None;dt=1/3
for i in range(int((178-0)/dt)+1):
 t=0+i*dt;c.set(cv2.CAP_PROP_POS_MSEC,(t+1/15)*1000);ok,f=c.read()
 if not ok:continue
 g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY);mask=np.zeros_like(g);mask[65:175,185:600]=255
 if prev is not None:
  pts=cv2.goodFeaturesToTrack(prev,350,.02,8,mask=mask)
  med=0;frac=0;n=0
  if pts is not None and len(pts)>12:
   nxt,status,err=cv2.calcOpticalFlowPyrLK(prev,g,pts,None,winSize=(25,25),maxLevel=3)
   back,st2,err2=cv2.calcOpticalFlowPyrLK(g,prev,nxt,None,winSize=(25,25),maxLevel=3)
   good=(status[:,0]>0)&(st2[:,0]>0)&(np.linalg.norm(back-pts,axis=2)[:,0]<1.5)
   a=pts[good,0];b=nxt[good,0];n=len(a)
   if n>12:
    mat,inl=cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC,ransacReprojThreshold=2)
    if inl is not None:
     dd=(b-a)[inl[:,0]>0];med=float(np.median(dd[:,0]));frac=float(np.mean(inl))
  rows.append({'video_time':round(t,4),'dx_px':med,'speed_proxy':abs(med)/dt,'inlier_fraction':frac,'features':n})
 prev=g
c.release();pathlib.Path('dynamic_replay_019742/evidence/ego_static_flow.json').write_text(json.dumps(rows,indent=2))
for a in range(0,178,2):
 q=[r['speed_proxy'] for r in rows if a<=r['video_time']<a+2];print(a,round(float(np.median(q)),2) if q else 0)
