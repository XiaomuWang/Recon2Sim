from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import numpy as np
P=Path(__file__).resolve().parents[1]/'textures'
rng=np.random.default_rng(512189);N=1024
def noise(n):return np.array(Image.fromarray(rng.integers(0,255,(n,n),dtype=np.uint8)).resize((N,N),Image.Resampling.BICUBIC),float)/255
coarse=noise(12);fine=noise(1024);mid=noise(128)
base=np.clip(41+mid*4+fine*19,0,255)
Image.fromarray(np.stack([base*.94,base*.98,base],axis=-1).astype('uint8')).save(P/'asphalt_basecolor.png')
rough=np.clip(115+mid*12+fine*5,110,140).astype('uint8');Image.fromarray(rough).save(P/'asphalt_roughness.png')
dy,dx=np.gradient((fine*.65+mid*.3));norm=np.stack([-dx,-dy,np.ones_like(dx)],-1);norm/=np.linalg.norm(norm,axis=-1)[...,None]
Image.fromarray(((norm*.5+.5)*255).astype('uint8')).save(P/'asphalt_normal.png')
font='C:/Windows/Fonts/msyhbd.ttc'
# Storefront lettering is representative: source lettering is not reliably readable.
texts=['汽车服务','轮胎 · 保养','便利商店','五金机电','家常小吃','生活超市','汽配维修','烟酒茶','便民服务','综合商行','汽车养护','社区商铺']
colors=[('#e6bd24','#243d6b'),('#164586','#f2dc63'),('#932b22','#f8dfb6'),('#126754','#f4e7ba')]
for i,txt in enumerate(texts):
 bg,fg=colors[i%4];im=Image.new('RGB',(1024,192),bg);d=ImageDraw.Draw(im);f=ImageFont.truetype(font,108);bb=d.textbbox((0,0),txt,font=f);d.text(((1024-bb[2])/2,28-bb[1]),txt,font=f,fill=fg);d.line((8,175,1016,175),fill=fg,width=3);im.save(P/f'sign_{i:02d}.png')
im=Image.new('RGB',(256,650),'#ecebdc');d=ImageDraw.Draw(im);f=ImageFont.truetype(font,64)
for i,ch in enumerate('注意右侧车辆汇入'):d.text((90,i*73+8),ch,font=f,fill='#27392f')
im.save(P/'merge_notice.png')
im=Image.new('RGB',(512,512),'#f2efe4');d=ImageDraw.Draw(im);d.polygon([(20,40),(492,40),(256,482)],fill='#b32b30');d.polygon([(86,82),(426,82),(256,402)],fill='#f2efe4');d.text((189,102),'让',font=ImageFont.truetype(font,134),fill='#1f2725');im.save(P/'yield.png')
print('Created wet asphalt PBR and 14 sign graphics')
