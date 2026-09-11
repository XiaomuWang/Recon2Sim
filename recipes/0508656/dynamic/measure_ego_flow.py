"""Optical flow over static left-view upper roadside. Not metric odometry."""
import cv2,numpy as np,pathlib,json
P=pathlib.Path(__file__).resolve().parents[1];src=next(P.parent.glob('*LA71AUB1XS0508656*'))
c=cv2.VideoCapture(str(src/'left.mp4'));rows=[];prev=None;dt=.25
for i in range(489):
 t=i*dt;c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
 if not ok:continue
 g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY);g=cv2.resize(g,(558,443));mask=np.zeros_like(g);mask[30:185,120:530]=255
 if prev is not None:
  pts=cv2.goodFeaturesToTrack(prev,260,.02,7,mask=mask);med=0;frac=0;n=0;status_text='insufficient_features'
  if pts is not None and len(pts)>12:
   nxt,st,err=cv2.calcOpticalFlowPyrLK(prev,g,pts,None,winSize=(25,25),maxLevel=3);back,st2,err2=cv2.calcOpticalFlowPyrLK(g,prev,nxt,None,winSize=(25,25),maxLevel=3)
   good=(st[:,0]>0)&(st2[:,0]>0)&(np.linalg.norm(back-pts,axis=2)[:,0]<1.5);a=pts[good,0];b=nxt[good,0];n=len(a)
   if n>12:
    mat,inl=cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC,ransacReprojThreshold=2)
    if inl is not None:
     delta=(b-a)[inl[:,0]>0];med=float(np.median(delta[:,0]));frac=float(np.mean(inl));status_text='ok'
  rows.append({'video_time':round(t,4),'dx_px':med,'speed_proxy':abs(med)/dt,'inlier_fraction':frac,'features':n,'status':status_text,'mean_gray':float(g.mean())})
 prev=g
c.release();(P/'evidence/ego_static_flow.json').write_text(json.dumps(rows,indent=2))
for a in range(0,122,2):
 q=[r['speed_proxy'] for r in rows if a<=r['video_time']<a+2];print(a,round(float(np.median(q)),2) if q else 0)
