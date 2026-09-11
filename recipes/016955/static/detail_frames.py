import cv2,pathlib
from PIL import Image,ImageDraw
root=next(pathlib.Path('.').glob('*LNDEA7HF3SH016955*'));out=pathlib.Path('environment_reconstruction_016955/evidence')
for t in [64,68,72,76,84,96,106,110,114,118,140,146,155,175]:
 sheet=Image.new('RGB',(1280,760),(20,25,30));d=ImageDraw.Draw(sheet)
 for i,name in enumerate(['front','rear','left','right']):
  c=cv2.VideoCapture(str(root/(name+'.mp4')));c.set(0 if False else cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read();c.release()
  if not ok:continue
  im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.save(out/f'{name}_{t:03d}_detail.png');im=im.resize((640,360))
  x=i%2*640;y=i//2*380;sheet.paste(im,(x,y+20));d.text((x+8,y+3),f'{name} @ {t}s',fill='white')
 sheet.save(out/f'sync_{t:03d}.jpg')

