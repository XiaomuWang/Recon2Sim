import cv2, pathlib, json
from PIL import Image, ImageDraw
P=pathlib.Path(__file__).resolve().parents[1]
root=next(P.parent.glob('*LNDEA7HF1SH024388*'))
out=P/'evidence';out.mkdir(exist_ok=True)
meta={}
for name in ['front','rear','left','right']:
 c=cv2.VideoCapture(str(root/(name+'.mp4')))
 fps=c.get(cv2.CAP_PROP_FPS);n=c.get(cv2.CAP_PROP_FRAME_COUNT)
 meta[name]={'fps':fps,'frames':n,'width':c.get(3),'height':c.get(4),'duration':n/fps}
 times=[round(i*(n/fps-0.3)/11,2) for i in range(12)]
 sheet=Image.new('RGB',(1280,6*390),(24,28,34));d=ImageDraw.Draw(sheet)
 for i,t in enumerate(times):
  c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
  if not ok:continue
  im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.save(out/f'{name}_{t:06.2f}.jpg')
  im=im.resize((640,360));x=(i%2)*640;y=(i//2)*390
  sheet.paste(im,(x,y+25));d.text((x+10,y+5),f'{name}  {t}s',fill='white')
 sheet.save(out/f'{name}_contact.jpg');c.release()
(out/'video_metadata.json').write_text(json.dumps(meta,indent=2))
print(json.dumps(meta,indent=2))
