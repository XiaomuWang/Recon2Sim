"""Diagram of reconstructed timestamp tracks; not a CARLA recording."""
import json,math,sys,cv2
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));from replay_carla import interpolate
d=json.loads((P/'scenario.json').read_text(encoding='utf-8'));W,H=1440,900;FPS=10
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16);title=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',29)
writer=cv2.VideoWriter(str(P/'preview/trajectory_replay_mp4v.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),FPS,(W,H));assert writer.isOpened()
def xy(x,y):return (55+(x+150)*4.7,380-y*6.0)
def draw_rect(dr,x1,y1,x2,y2,fill):
 a=xy(x1,y1);b=xy(x2,y2);dr.rectangle((min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])),fill=fill)
base=Image.new('RGB',(W,H),'#101c25');dr=ImageDraw.Draw(base)
dr.text((40,24),'美团 0512189  |  动态目标时序复原',font=title,fill='#e5eee9');dr.text((40,69),'四路视频参考 · 世界坐标轨迹图 · 非 CARLA 录屏 · 尺寸和遮挡轨迹为估计',font=small,fill='#a1b8bb')
draw_rect(dr,-150,-10.7,125,10.7,'#36444d');draw_rect(dr,-150,19,125,27,'#607272')
for x in range(-150,125,10):
 for sg in [-1,1]:
  for yy in [3.65,7.05]:dr.line([xy(x,sg*yy),xy(x+3,sg*yy)],fill='#afb9ba',width=2)
dr.line([xy(-150,0),xy(125,0)],fill='#d8bf69',width=3)
draw_rect(dr,-48,-23,-14,-41,'#704440');draw_rect(dr,8,-17,72,-21,'#526365')
dr.text(xy(-48,-44),'加油站',font=small,fill='#cba795');dr.text(xy(12,-24),'斜列停车区 / 商铺',font=small,fill='#a5baba');dr.text(xy(-40,31),'左侧高架',font=small,fill='#a6bec1')
for x in range(10,69,4):dr.line([xy(x,-10.7),xy(x+4.6,-16.5)],fill='#9dabaf',width=1)
for x in [-150,-100,-50,0,50,100,125]:dr.text(xy(x,12),str(x)+'m',font=small,fill='#9baeb8')
watch=['ego','green_delivery_van','red_tanker','white_box_truck','bus_teal','bus_yellow_ad','pedestrian_purple']
for frame in range(1201):
 t=frame/FPS;im=base.copy();dr=ImageDraw.Draw(im);active=[]
 for a in d['actors']:
  if not a['start_t']<=t<=a['end_t']:continue
  s=interpolate(a['samples'],t);le=a['dimensions_m']['length']/2;wi=a['dimensions_m']['width']/2;h=s['h'];co=math.cos(h);si=math.sin(h)
  col=tuple(map(int,a['color'].split(','))) if a.get('color') else (193,124,166)
  points=[xy(s['x']+u*co-v*si,s['y']+u*si+v*co) for u,v in [(le,0),(le*.65,wi),(-le,wi),(-le,-wi),(le*.65,-wi)]]
  dr.polygon(points,fill=col,outline='#e4ebe4' if a['id']=='ego' else '#111921')
  if a['id']=='ego':x,y=xy(s['x'],s['y']);dr.ellipse((x-15,y-20,x+15,y+20),outline='#f1dc69',width=2)
  if a['id'] in watch:active.append(a)
 dr.text((42,115),f'前视视频 / 回放时间  {t:06.2f} s / 120 s',font=font,fill='#b0e4cd')
 es=[e['label_zh'] for e in d['events'] if e['start_t']<=t<=e['end_t']]
 dr.rounded_rectangle((35,735,1405,797),radius=10,fill='#223b42');dr.text((54,753),'；'.join(es) if es else '车辆按观测时序运动',font=font,fill='#e0e8db')
 for i,a in enumerate(active[:7]):
  xx=45+(i%4)*342;yy=666+(i//4)*31;col=tuple(map(int,a['color'].split(','))) if a.get('color') else (193,124,166);dr.rounded_rectangle((xx,yy+4,xx+16,yy+17),radius=3,fill=col);dr.text((xx+23,yy),a['label_zh'],font=small,fill='#b3ccc6')
 dr.line((40,837,1400,837),fill='#385254',width=6);dr.line((40,837,40+1360*t/120,837),fill='#77d6b2',width=6)
 dr.text((40,855),'0 s',font=small,fill='#a4beb5');dr.text((1300,855),'120 s',font=small,fill='#a4beb5')
 if frame in [160,510,860,1050,1180]:im.save(P/'preview'/f'timeline_{t:03.0f}.png')
 writer.write(cv2.cvtColor(np.array(im),cv2.COLOR_RGB2BGR))
writer.release();print('Wrote 120.1 s diagram video, 10 fps')
