import cv2,pathlib,json,numpy as np
from PIL import Image,ImageDraw
P=pathlib.Path(__file__).resolve().parents[1];src=next(P.parent.glob('*LA71AUB1XS0508656*'));out=P/'evidence'
meta={}
for cam in ['front','rear','left','right']:
 c=cv2.VideoCapture(str(src/(cam+'.mp4')));duration=c.get(cv2.CAP_PROP_FRAME_COUNT)/c.get(cv2.CAP_PROP_FPS);meta[cam]={'fps':c.get(cv2.CAP_PROP_FPS),'duration':duration,'frames':c.get(cv2.CAP_PROP_FRAME_COUNT)}
 for start,end,step in [(0,81,5),(80,104,2),(104,123,1)]:
  ts=[t for t in range(start,end,step) if t<duration];W=480;H=290;sheet=Image.new('RGB',(W*3,((len(ts)+2)//3)*H),(18,24,29));d=ImageDraw.Draw(sheet)
  for i,t in enumerate(ts):
   c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
   if not ok:continue
   image=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));image.save(out/f'{cam}_{t:03d}.jpg',quality=93);image.thumbnail((W,H-24))
   x=i%3*W;y=i//3*H;sheet.paste(image,(x+(W-image.width)//2,y+24));d.text((x+8,y+5),f'{cam} | source {t:.1f}s',fill='white')
  sheet.save(out/f'{cam}_{start}_{end}_sheet.jpg',quality=90)
 c.release()
(out/'video_metadata.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta))
