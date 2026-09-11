from pathlib import Path
import cv2
from PIL import Image,ImageDraw
p=Path('dynamic_replay_0512189/evidence');src=next(Path('.').glob('*LA71AUB13S0512189*'));im=Image.new('RGB',(1500,4*9*70),'#17202a');d=ImageDraw.Draw(im)
for ci,cam in enumerate(['front','rear','left','right']):
 c=cv2.VideoCapture(str(src/(cam+'.mp4')))
 for j,t in enumerate([0,4,8,20,40,60,80,100,118]):
  c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
  if ok:
   a=Image.fromarray(cv2.cvtColor(f[:42,:700],cv2.COLOR_BGR2RGB));a=a.resize((1400,84));y=(ci*9+j)*70;im.paste(a,(100,y));d.text((2,y+12),f'{cam} {t}',fill='white')
im.save(p/'timestamp_strips.jpg')
