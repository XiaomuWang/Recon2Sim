import cv2,pathlib
from PIL import Image,ImageDraw
p=next(pathlib.Path('.').glob('*LNDEA7HF1SH019742*'));out=pathlib.Path('dynamic_replay_019742/evidence')
for name in ['front','rear','left','right']:
 for label,times in [('early',list(range(0,100,4))),('event',list(range(96,179,3)))]:
  sheet=Image.new('RGB',(1280,((len(times)+3)//4)*205),(22,27,33));d=ImageDraw.Draw(sheet);c=cv2.VideoCapture(str(p/(name+'.mp4')))
  for i,t in enumerate(times):
   c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
   if not ok:continue
   im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.save(out/f'{name}_{t:03d}.jpg');im=im.resize((320,180));x=i%4*320;y=i//4*205;sheet.paste(im,(x,y+25));d.text((x+8,y+5),name+' '+str(t)+'s',fill='white')
  c.release();sheet.save(out/(name+'_'+label+'_contact.jpg'))
