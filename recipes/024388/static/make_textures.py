from pathlib import Path
import numpy as np,cv2
from PIL import Image
P=Path(__file__).resolve().parents[1]/'textures';rng=np.random.default_rng(24388);N=1024
n=rng.random((N,N));cloud=cv2.GaussianBlur(rng.random((N,N)).astype('float32'),(0,0),25);cloud=(cloud-cloud.min())/(cloud.max()-cloud.min())
grain=rng.normal(0,3.4,(N,N));a=43+grain+cloud*3
col=np.stack([a*.94,a*.98,a],axis=-1);pores=n<.025;col[pores]*=.52
Image.fromarray(np.clip(col,0,255).astype('uint8')).save(P/'asphalt_basecolor.png')
rough=115+cloud*25+rng.normal(0,5,(N,N));Image.fromarray(np.clip(rough,0,255).astype('uint8')).save(P/'asphalt_roughness.png')
h=cv2.GaussianBlur(n.astype('float32'),(0,0),.6);gy,gx=np.gradient(h);normal=np.stack([-gx*.8,-gy*.8,np.ones_like(gx)],axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
Image.fromarray(((normal*.5+.5)*255).astype('uint8')).save(P/'asphalt_normal.png')
print('Wrote damp asphalt PBR texture set, 1024 x 1024.')
def surface(name,base,tile=0):
 noise=rng.normal(0,1.3,(N,N));height=rng.random((N,N))*.015
 a=np.ones((N,N,3))*np.array(base)[None,None,:]+noise[:,:,None]+(cloud[:,:,None]-.5)*4
 if tile:
  for y in range(0,N,tile):
   for x in range(0,N,tile):a[y:y+tile,x:x+tile]+=rng.uniform(-4,4)
  grid=(np.indices((N,N))[0]%tile<2)|(np.indices((N,N))[1]%tile<2)
  a[grid]*=.68;height[grid]-=.1
 Image.fromarray(np.clip(a,0,255).astype('uint8')).save(P/(name+'_basecolor.png'))
 Image.fromarray(np.clip(185+noise,0,255).astype('uint8')).save(P/(name+'_roughness.png'))
 gy,gx=np.gradient(height);nn=np.stack([-gx,-gy,np.ones_like(gx)],-1);nn/=np.linalg.norm(nn,axis=-1,keepdims=True)
 Image.fromarray(((nn*.5+.5)*255).astype('uint8')).save(P/(name+'_normal.png'))
surface('concrete',[161,164,159])
surface('facade',[103,107,107],256)
surface('paving',[151,146,135],128)
