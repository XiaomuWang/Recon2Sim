from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1]
colors=[(66,102,71),(146,33,36),(34,63,86),(59,60,52),(34,109,102),(144,60,40),(91,55,28),(35,85,147),(145,32,39),(42,102,73),(27,53,57),(66,53,45)]
# Small text was not legible in footage: generic editable fascias, not claimed exact brands.
texts=['生活超市','便利店','社区服务','餐饮','健康生活','鲜果茶饮','便民商店','生活服务','社区商铺','日用百货','休闲餐饮','街坊小店']
font=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',105)
for i,(color,txt) in enumerate(zip(colors,texts)):
 im=Image.new('RGB',(1024,224),color);d=ImageDraw.Draw(im);d.rectangle((9,9,1015,215),outline=(200,190,160),width=3)
 bb=d.textbbox((0,0),txt,font=font);d.text(((1024-bb[2])/2,45-bb[1]),txt,font=font,fill=(243,231,199));im.save(P/'textures'/f'sign_{i:02d}.png')
print('Generic editable sign textures prepared')
