import cv2,pathlib,json,numpy as np
from PIL import Image,ImageDraw
src=next(pathlib.Path('.').glob('*LNDEA7HF1SH014346*'));out=pathlib.Path('dynamic_replay_014346/evidence')
for cam in ['front','rear','left','right']:
 c=cv2.VideoCapture(str(src/(cam+'.mp4')))
 for start,end in [(52,80),(80,108),(108,160)]:
  ts=list(range(start,end,2 if start<108 else 4));sheet=Image.new('RGB',(1280,((len(ts)+1)//2)*385),(18,24,29));d=ImageDraw.Draw(sheet)
  for i,t in enumerate(ts):
   c.set(cv2.CAP_PROP_POS_MSEC,(t+(0 if cam=='front' else 1/15))*1000);ok,f=c.read()
   if not ok:continue
   im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((640,360));x=i%2*640;y=i//2*385;sheet.paste(im,(x,y+25));d.text((x+8,y+5),f'{cam} | source {t:.1f}s',fill='white')
  sheet.save(out/f'{cam}_{start}_{end}.jpg',quality=90)
 c.release()
print('Saved detailed multi-view timelines')
