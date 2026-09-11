import cv2,pathlib
p=next(pathlib.Path('.').glob('*LA71AUB13S0512189*'));out=pathlib.Path('environment_reconstruction_0512189/evidence')
for name,ts in [('front',[0,45,85,92,118]),('rear',[0,85,118]),('left',[0,90,106]),('right',[0,42,90,100,118])]:
 c=cv2.VideoCapture(str(p/(name+'.mp4')))
 for t in ts:
  c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
  if ok:cv2.imwrite(str(out/f'detail_{name}_{t:03d}.jpg'),f)
