import cv2,pathlib
from PIL import Image,ImageDraw
root=next(pathlib.Path('.').glob('*LNDEA7HF1SH014346*'));out=pathlib.Path('environment_reconstruction_014346/evidence')
for t in [48,52,56,62,66,68,70,72,75,78,82,88,94,100,105,110,115,155]:
 sheet=Image.new('RGB',(1280,760),(20,25,30));d=ImageDraw.Draw(sheet)
 for i,name in enumerate(['front','rear','left','right']):
  c=cv2.VideoCapture(str(root/(name+'.mp4')));c.set(0 if False else cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read();c.release()
  if not ok:continue
  im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.save(out/f'{name}_{t:03d}_detail.png');im=im.resize((640,360))
  x=i%2*640;y=i//2*380;sheet.paste(im,(x,y+20));d.text((x+8,y+3),f'{name} @ {t}s',fill='white')
 sheet.save(out/f'sync_{t:03d}.jpg')
