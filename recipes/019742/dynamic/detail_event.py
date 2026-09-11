import cv2,pathlib
from PIL import Image,ImageDraw
p=next(pathlib.Path('.').glob('*LNDEA7HF1SH019742*'));o=pathlib.Path('dynamic_replay_019742/evidence')
for name in ['front','right','rear']:
 times=[104,106,108,109,110,110.5,111,111.5,112,112.5,113,114]
 sh=Image.new('RGB',(1280,6*385),(22,26,31));d=ImageDraw.Draw(sh);c=cv2.VideoCapture(str(p/(name+'.mp4')))
 for i,t in enumerate(times):
  c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read();im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im=im.resize((640,360));x=i%2*640;y=i//2*385;sh.paste(im,(x,y+25));d.text((x+8,y+5),f'{name} {t}s',fill='white')
 c.release();sh.save(o/(name+'_critical_detail.jpg'))
