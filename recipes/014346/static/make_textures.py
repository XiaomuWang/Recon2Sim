from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
out=Path('environment_reconstruction_014346/textures');out.mkdir(exist_ok=True)
rng=np.random.default_rng(14346)
N=1024

def noise(scale):
 a=rng.random((scale,scale))*255
 return np.asarray(Image.fromarray(a.astype('uint8')).resize((N,N),Image.Resampling.BICUBIC),dtype=float)/255-.5

def save(name,base,variation,streak=False):
 n=noise(8)*.30+noise(32)*.3+noise(128)*.25+noise(1024)*.15
 if streak:
  st=np.asarray(Image.fromarray((rng.random((16,200))*255).astype('uint8')).resize((N,N),Image.Resampling.BILINEAR))/255
  n-=np.maximum(0,st-.45)*1.4
 a=np.clip(np.array(base)[None,None,:]+n[:,:,None]*variation,0,255).astype('uint8')
 Image.fromarray(a).save(out/(name+'_basecolor.png'))
 Image.fromarray(np.clip(220+n*25,0,255).astype('uint8')).save(out/(name+'_roughness.png'))
 h=n*2
 dy,dx=np.gradient(h);norm=np.stack([-dx*2,-dy*2,np.ones_like(dx)],axis=-1);norm/=np.linalg.norm(norm,axis=-1)[:,:,None]
 Image.fromarray(((norm*.5+.5)*255).astype('uint8')).save(out/(name+'_normal.png'))
save('concrete',(141,140,127),78,True)
save('road',(126,122,109),65)
save('asphalt',(62,66,64),45)
save('hoarding',(72,108,47),75)
save('soil',(102,88,62),65)
save('bark',(89,81,60),100,True)
save('paving',(149,146,130),55)
# Verified legible wording from right 100 and front 110; separate transparent text overlays.
fnt='C:/Windows/Fonts/msyhbd.ttc'
for name,txt in [('slogan_a','南山永不止步'),('slogan_b','生态南山  山海连城')]:
 im=Image.new('RGBA',(2048,320),(0,0,0,0));d=ImageDraw.Draw(im);font=ImageFont.truetype(fnt,158)
 box=d.textbbox((0,0),txt,font=font);d.text(((2048-box[2])/2,60-box[1]),txt,font=font,fill=(232,235,222,255));im.save(out/(name+'.png'))
print('Created texture maps and observed hoarding lettering')
