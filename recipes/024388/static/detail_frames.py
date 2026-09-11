import cv2,pathlib
from PIL import Image,ImageDraw
P=pathlib.Path(__file__).resolve().parents[1];src=next(P.parent.glob('*LNDEA7HF1SH024388*'))
for t in [78,88,94,98,102,106,110]:
 sh=Image.new('RGB',(1280,780));d=ImageDraw.Draw(sh)
 for i,n in enumerate(['front','rear','left','right']):
  c=cv2.VideoCapture(str(src/(n+'.mp4')));c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read();c.release()
  if ok:
   im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.save(P/'evidence'/f'{n}_{t:03d}_detail.jpg')
   x=i%2*640;y=i//2*390;sh.paste(im.resize((640,360)),(x,y+25));d.text((x+10,y+5),f'{n} {t} seconds',fill='white')
 sh.save(P/'evidence'/f'sync_{t:03d}.jpg')
