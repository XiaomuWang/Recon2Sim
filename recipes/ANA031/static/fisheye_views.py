"""Exploratory equidistant views; NOT camera calibration. Never use these pixels as metric data."""
import cv2,numpy as np,json
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];out=P/'evidence/fisheye';out.mkdir(exist_ok=True)
records=[]
for direction,t in [('left',25.89),('right',28.47)]:
 im=cv2.imread(str(P/'evidence'/f'{direction}_{t:06.2f}.jpg'));h,w=im.shape[:2]
 sheet=Image.new('RGB',(1200,840),(20,24,30));draw=ImageDraw.Draw(sheet)
 for row,fov in enumerate([170,190,210]):
  for col,yaw in enumerate([-35,0,35]):
   # Nominal equidistant projection: theta=r/f; FOV varied to show uncertainty.
   xx,yy=np.meshgrid(np.arange(400),np.arange(250));f=200/np.tan(np.deg2rad(85)/2)
   rays=np.stack([(xx-200)/f,(yy-125)/f,np.ones_like(xx)],axis=-1).astype(float)
   a=np.deg2rad(yaw);rot=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
   rays=rays@rot.T;rr=np.hypot(rays[:,:,0],rays[:,:,1]);theta=np.arctan2(rr,rays[:,:,2]);scale=(w/np.deg2rad(fov))*theta/np.maximum(rr,1e-8)
   mx=(w/2+rays[:,:,0]*scale).astype('float32');my=(h/2+rays[:,:,1]*scale).astype('float32')
   view=cv2.remap(im,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
   sheet.paste(Image.fromarray(cv2.cvtColor(view,cv2.COLOR_BGR2RGB)),(col*400,row*280+30))
   draw.text((col*400+8,row*280+8),f'ASSUMED {fov} deg | yaw {yaw:+} | NOT calibrated',fill='white')
 sheet.save(out/f'{direction}_projection_sensitivity.jpg')
 records.append({'camera':direction,'time_s':t,'source_resolution':[w,h],'projection':'equidistant assumption','nominal_horizontal_fov_deg':[170,190,210],'yaw_deg':[-35,0,35],'output_pinhole_fov_deg':85,'calibrated':False,'use':'landmark relationship inspection only; original images remain authoritative'})
(out/'projection_assumptions.json').write_text(json.dumps(records,indent=2))
