"""Original sign and civic panel graphics; generic wording where video is unreadable."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1]/'textures'
font='C:/Windows/Fonts/msyhbd.ttc'
signs=[('灯饰照明',(34,66,151)),('五金电器',(172,32,29)),('窗帘布艺',(29,71,128)),('家居建材',(173,40,26)),('生活超市',(19,108,81)),('卫浴洁具',(162,46,27)),('门窗定制',(147,104,37)),('照明电工',(30,64,154)),('装饰材料',(148,36,28)),('厨卫电器',(187,142,35)),('便利生活',(38,116,108)),('商贸中心',(49,83,103))]
for i,(s,col) in enumerate(signs):
 im=Image.new('RGB',(1024,256),col);d=ImageDraw.Draw(im);d.rectangle((8,8,1015,247),outline=(211,194,142),width=3)
 f=ImageFont.truetype(font,122);bb=d.textbbox((0,0),s,font=f);d.text(((1024-bb[2])/2,18-bb[1]),s,font=f,fill=(249,237,200))
 d.text((220,178),'品质生活  ·  用心服务',font=ImageFont.truetype(font,32),fill=(238,233,218));im.save(P/f'sign_{i:02d}.png')
for i,s in enumerate(['文明出行  礼让行人','安全乘车  平安到家','共建美好家园','关爱生命  安全出行']):
 im=Image.new('RGB',(1200,480),(159,202,219));d=ImageDraw.Draw(im)
 d.rectangle((0,342,1200,480),fill=(139,178,107));d.polygon([(0,380),(280,302),(560,388),(850,312),(1200,375),(1200,480),(0,480)],fill=(178,205,127))
 d.ellipse((30,210,160,340),fill=(221,81,65));d.rounded_rectangle((190,175,230,358),10,fill=(62,112,146));d.ellipse((187,123,234,170),fill=(237,212,166))
 f=ImageFont.truetype(font,64);d.text((278,88),s,font=f,fill=(44,77,118));d.text((350,235),'文明城市  你我同行',font=ImageFont.truetype(font,42),fill=(186,73,60))
 # Visual perforation dots; underlying panel remains solid for stable mesh collision.
 for x in range(5,1200,13):
  for y in range(5,480,13):d.ellipse((x,y,x+4,y+4),fill=(66,86,93))
 im.save(P/f'civic_{i}.png')
print('12 storefront signs and 4 perforated-panel graphics')

im=Image.new('RGB',(1024,256),(210,155,35));d=ImageDraw.Draw(im);d.text((75,35),'OPPLE',font=ImageFont.truetype(font,130),fill=(55,62,121));d.text((636,67),'欧普照明',font=ImageFont.truetype(font,61),fill=(249,242,217));im.save(P/'sign_12.png')
