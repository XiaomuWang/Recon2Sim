import cv2, pathlib, json
from PIL import Image, ImageDraw
root=next(pathlib.Path('.').glob('*LNDEA7HF1SH014346*'))
out=pathlib.Path('environment_reconstruction_014346/evidence')
meta={}
for name in ['front','rear','left','right']:
 c=cv2.VideoCapture(str(root/(name+'.mp4')))
 fps=c.get(cv2.CAP_PROP_FPS); n=c.get(cv2.CAP_PROP_FRAME_COUNT)
 meta[name]={'fps':fps,'frames':n,'width':c.get(3),'height':c.get(4),'duration':n/fps}
 times=list(range(0,160,10))
 times=[t for t in times if t<n/fps]
 sheet=Image.new('RGB',(960, (len(times)+1)//2*300),(24,28,34));d=ImageDraw.Draw(sheet)
 for i,t in enumerate(times):
  c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
  if not ok:continue
  im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.save(out/f'{name}_{t:02d}.jpg')
  im.thumbnail((480,270));x=(i%2)*480;y=(i//2)*300
  sheet.paste(im,(x,y+25));d.text((x+10,y+5),f'{name}  {t}s',fill='white')
 sheet.save(out/f'{name}_contact.jpg')
 c.release()
(out/'video_metadata.json').write_text(json.dumps(meta,indent=2))
print(json.dumps(meta,indent=2))


