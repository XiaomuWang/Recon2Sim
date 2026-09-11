import cv2,json,pathlib,numpy as np
from PIL import Image,ImageDraw
P=pathlib.Path('dynamic_replay_016955');src=next(pathlib.Path('.').glob('*LNDEA7HF3SH016955*'))
for view in ['front','rear','left','right']:
 c=cv2.VideoCapture(str(src/(view+'.mp4')))
 for a,b,step in [(0,48,4),(48,84,3),(84,120,3),(114,150,3),(150,181,3)]:
  ts=list(range(a,b,step));out=Image.new('RGB',(1600,((len(ts)+3)//4)*250),(18,23,28));d=ImageDraw.Draw(out)
  for i,t in enumerate(ts):
   c.set(cv2.CAP_PROP_POS_MSEC,(t+(1/15 if view=='left' else 0))*1000);ok,f=c.read()
   if not ok:continue
   im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.thumbnail((400,225));x=i%4*400;y=i//4*250;out.paste(im,(x,y+23));d.text((x+5,y+5),f'{view} {t}s',fill='white')
  out.save(P/'evidence'/f'{view}_{a:03d}_{b:03d}.jpg',quality=95)
 c.release()
allrows={}
for view in ['left','right']:
 c=cv2.VideoCapture(str(src/(view+'.mp4')));prev=None;rows=[];dt=1/3
 for i in range(541):
  t=i*dt;c.set(cv2.CAP_PROP_POS_MSEC,(t+(1/15 if view=='left' else 0))*1000);ok,f=c.read()
  if not ok:continue
  g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY);mask=np.zeros_like(g);mask[60:275,160:570 if view=='left' else 485]=255
  if prev is not None:
   pts=cv2.goodFeaturesToTrack(prev,280,.02,8,mask=mask);speed=0;frac=0;n=0
   if pts is not None and len(pts)>12:
    nxt,st,er=cv2.calcOpticalFlowPyrLK(prev,g,pts,None,winSize=(25,25),maxLevel=3);back,st2,er2=cv2.calcOpticalFlowPyrLK(g,prev,nxt,None,winSize=(25,25),maxLevel=3)
    good=(st[:,0]>0)&(st2[:,0]>0)&(np.linalg.norm(back-pts,axis=2)[:,0]<1.5);aa=pts[good,0];bb=nxt[good,0];n=len(aa)
    if n>12:
     ma,ins=cv2.estimateAffinePartial2D(aa,bb,method=cv2.RANSAC,ransacReprojThreshold=2)
     if ins is not None:
      dd=(bb-aa)[ins[:,0]>0];speed=float(np.linalg.norm(np.median(dd,axis=0)))/dt;frac=float(np.mean(ins))
   rows.append(dict(video_time=round(t,5),speed_proxy=speed,inlier_fraction=frac,features=n))
  prev=g
 c.release();allrows[view]=rows
(P/'evidence/ego_static_flow.json').write_text(json.dumps(allrows,indent=2))
for a in range(0,180,2):
 print(a,[(v,round(float(np.median([r['speed_proxy'] for r in rows if a<=r['video_time']<a+2])),2)) for v,rows in allrows.items()])
