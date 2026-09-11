import cv2,numpy as np,json
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];SRC=next(P.parent.glob('*LHTDA4B45SYANA031*'));OUT=P/'evidence'
for name,times in [('front',[0,4,8,12,16,20,22,24,25,26,27,28,30,32,34]),('rear',[7,15,23,29,33,35,37,39,41,43,45,47,49,51,53]),('left',[0,8,16,24,28,30,32,34,36,40,44,48,54,60,64]),('right',[0,8,12,16,20,24,28,30,32,34,36,38,40,44,47])]:
 c=cv2.VideoCapture(str(SRC/(name+'.mp4')));sheet=Image.new('RGB',(1500,5*310),(18,23,30));dr=ImageDraw.Draw(sheet)
 for i,t in enumerate(times):
  c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
  if not ok:continue
  cv2.imwrite(str(OUT/f'{name}_{t:05.1f}.jpg'),f)
  im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.thumbnail((500,281));x=i%3*500;y=i//3*310;sheet.paste(im,(x,y+27));dr.text((x+8,y+6),f'{name} FILE {t:.1f}s',fill='white')
 sheet.save(OUT/(name+'_dynamic_contact.jpg'));c.release()
# Fisheye side upper static band, restricted to buildings/trees; excludes near traffic and car body.
c=cv2.VideoCapture(str(SRC/'left.mp4'));rows=[];prev=None;dt=.2
for i in range(325):
 t=i*dt;c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
 if not ok:break
 g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY);mask=np.zeros_like(g);mask[35:123,130:505]=255
 if prev is not None:
  pts=cv2.goodFeaturesToTrack(prev,250,.01,5,mask=mask);med=0.;n=0;frac=0.
  if pts is not None and len(pts)>10:
   nxt,st,_=cv2.calcOpticalFlowPyrLK(prev,g,pts,None,winSize=(21,21),maxLevel=3);back,st2,_=cv2.calcOpticalFlowPyrLK(g,prev,nxt,None,winSize=(21,21),maxLevel=3)
   valid=(st[:,0]>0)&(st2[:,0]>0)&(np.linalg.norm(back-pts,axis=2)[:,0]<1.3);a=pts[valid,0];b=nxt[valid,0];n=len(a)
   if n>10:
    _,inl=cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC,ransacReprojThreshold=1.5)
    if inl is not None:med=float(np.median((b-a)[inl[:,0]>0,0]));frac=float(np.mean(inl))
  rows.append({'side_file_t':round(t,3),'dx_px':med,'speed_proxy_px_s':abs(med)/dt,'features':n,'inlier_fraction':frac})
 prev=g
(OUT/'ego_static_flow.json').write_text(json.dumps(rows,indent=2))
for a in range(0,64,2):
 vals=[r['speed_proxy_px_s'] for r in rows if a<=r['side_file_t']<a+2];print(a,round(float(np.median(vals)),3) if vals else None)
