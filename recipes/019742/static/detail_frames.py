import cv2,pathlib
from PIL import Image,ImageDraw
p=next(pathlib.Path('.').glob('*LNDEA7HF1SH019742*'));out=pathlib.Path('environment_reconstruction_019742/evidence')
for t in [80,100,115,140]:
 sheet=Image.new('RGB',(1280,770),(20,24,30));d=ImageDraw.Draw(sheet)
 for i,name in enumerate(['front','rear','left','right']):
  c=cv2.VideoCapture(str(p/(name+'.mp4')));c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read();c.release()
  im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im=im.resize((640,360));x=i%2*640;y=i//2*385;sheet.paste(im,(x,y+25));d.text((x+10,y+5),name+' '+str(t)+'s',fill='white')
 sheet.save(out/f'sync_{t}.jpg')
