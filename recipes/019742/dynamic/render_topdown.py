"""Full-time trajectory diagram, encoded by Blender's bundled FFmpeg afterwards."""
import json,math,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));from replay_carla import interpolate
d=json.loads((P/'scenario.json').read_text(encoding='utf-8'));font='C:/Windows/Fonts/msyh.ttc'
fonts={s:ImageFont.truetype(font,s) for s in [15,18,22,28]};W,H=1280,720;fps=15
writer=cv2.VideoWriter(str(P/'preview/trajectory_intermediate.avi'),cv2.VideoWriter_fourcc(*'MJPG'),fps,(W,H));assert writer.isOpened()
colors={a['id']:tuple(int(x) for x in (a.get('color') or '170,185,200').split(',')) for a in d['actors']};colors['ego']=(61,203,225);colors['wrongway_orange_rider']=(255,135,38)
def frame(t):
 ego=interpolate(d['actors'][0]['samples'],t);center=ego['x']+14;sc=8.0
 im=Image.new('RGB',(W,H),(15,24,36));dr=ImageDraw.Draw(im)
 def xy(x,y):return (round(500+(x-center)*sc),round(395-y*sc))
 def rect(x0,y0,x1,y1,fill):
  p=xy(x0,y0);q=xy(x1,y1);dr.rectangle((min(p[0],q[0]),min(p[1],q[1]),max(p[0],q[0]),max(p[1],q[1])),fill=fill)
 rect(-500,-14,400,14,(71,79,80));rect(-500,-9.15,400,9.15,(48,58,70))
 if abs(center+120)<75:rect(-124.5,-38,-115.5,38,(48,58,70))
 for yy in [-6.6,-3.3,3.3,6.6]:
  for xx in range(-450,350,8):
   if -135<xx<-106:continue
   dr.line([xy(xx,yy),xy(xx+3,yy)],fill=(171,178,183),width=2)
 for yy in [-6.95,0,6.95]:
  for xx in range(-450,350,3):
   if any(abs(xx-c)<r for c,r in [(-340,6),(-230,5),(-120,13),(-38,5)]):continue
   dr.line([xy(xx,yy),xy(xx+2,yy)],fill=(180,187,165) if yy else (242,220,133),width=2)
 for a in d['actors']:
  if not a['start_t']<=t<=a['end_t']:continue
  s=interpolate(a['samples'],t);x,y=xy(s['x'],s['y'])
  if not 0<x<1000:continue
  L=a['dimensions_m']['length']/2;B=a['dimensions_m']['width']/2;h=s['h'];pts=[xy(s['x']+u*math.cos(h)-v*math.sin(h),s['y']+u*math.sin(h)+v*math.cos(h)) for u,v in [(L,B),(L,-B),(-L,-B),(-L,B)]]
  col=colors[a['id']];col=tuple(max(60,c) for c in col);dr.polygon(pts,fill=col,outline=(228,237,243));tip=xy(s['x']+L*math.cos(h),s['y']+L*math.sin(h));dr.line([(x,y),tip],fill=(15,23,30),width=2)
  if a['id'] in ['ego','wrongway_orange_rider']:
   tx,ty=(x-145,y-100) if a['id']=='ego' else (x+42,y+82)
   dr.line([(x,y),(tx+18,ty+20)],fill=col,width=1)
   label='自车' if a['id']=='ego' else '关键目标：橙衣逆行骑手'
   dr.text((tx,ty),label,font=fonts[18],fill=col,stroke_width=2,stroke_fill=(15,24,36))
 dr.rectangle((0,0,1280,135),fill=(15,24,36));dr.rectangle((1005,135,1280,720),fill=(21,33,48))
 dr.text((28,20),'019742 · 四视角动态恢复',font=fonts[28],fill=(232,240,247));dr.text((30,68),'轨迹示意预览 | 非 CARLA 录屏 | 空间尺度为估计值',font=fonts[18],fill=(157,180,197))
 dr.text((890,27),'%06.2f / 178 s'%t,font=fonts[28],fill=(80,208,224))
 phase='正常行驶 / 周边交通'
 if 67.5<=t<78.3:phase='路口停车等待'
 elif 106<=t<110:phase='第一辆逆行电动车接近'
 elif 110<=t<112:phase='橙衣逆行骑手近距通过 · 急刹'
 elif 112<=t<120:phase='急刹后停车等待'
 elif 120<=t<143:phase='低速缓行 · 右侧停放车辆'
 elif t>=164:phase='后方骑手陆续超越'
 dr.text((30,104),phase,font=fonts[22],fill=(255,177,96))
 active=[a for a in d['actors'] if a['start_t']<=t<=a['end_t']]
 dr.text((1023,154),'已激活目标：%d'%len(active),font=fonts[18],fill=(223,235,245))
 for i,a in enumerate(active[:20]):
  yy=193+i*22;dr.ellipse((1025,yy+5,1033,yy+13),fill=colors[a['id']]);dr.text((1041,yy),a['label_zh'][:14],font=fonts[15],fill=(183,201,216))
 dr.rectangle((24,678,980,684),fill=(54,69,84));dr.rectangle((24,678,24+956*t/178,684),fill=(59,201,223));dr.text((24,694),'地图：UrbanBrake019742   +X 行驶方向 →   车体尺寸与轨迹均为视频估计',font=fonts[15],fill=(132,156,177))
 return im
for i in range(178*fps+1):
 t=i/fps;im=frame(t);writer.write(cv2.cvtColor(np.array(im),cv2.COLOR_RGB2BGR))
 if i in [0,round(73*fps),round(110.5*fps),round(167*fps)]:im.save(P/'preview'/('topdown_%06.1f.png'%t))
writer.release();print('AVI frames:',178*fps+1)
