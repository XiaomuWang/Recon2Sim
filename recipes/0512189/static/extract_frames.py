import cv2,pathlib,json
from PIL import Image,ImageDraw
root=next(pathlib.Path('.').glob('*LA71AUB13S0512189*'));out=pathlib.Path('environment_reconstruction_0512189/evidence');meta={}
for name in ['front','rear','left','right']:
 c=cv2.VideoCapture(str(root/(name+'.mp4')));fps=c.get(5);n=c.get(7);duration=n/fps
 meta[name]={'fps':fps,'frames':n,'width':c.get(3),'height':c.get(4),'duration':duration}
 times=[round(i*duration/15,2) for i in range(15)]
 sheet=Image.new('RGB',(1280,5*265),(24,28,34));d=ImageDraw.Draw(sheet)
 for i,t in enumerate(times):
  c.set(0 if False else cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
  if not ok:continue
  im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.save(out/f'{name}_{t:06.2f}.jpg');im.thumbnail((426,240));x=i%3*426;y=i//3*265;sheet.paste(im,(x,y+25));d.text((x+10,y+5),f'{name} {t:.2f}s',fill='white')
 sheet.save(out/f'{name}_contact.jpg');c.release()
(out/'video_metadata.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))

