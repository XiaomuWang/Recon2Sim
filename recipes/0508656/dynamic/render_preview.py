# -*- coding: utf-8 -*-
"""Road-aligned plan preview, explicitly not a CARLA recording."""
import sys,math,json,subprocess
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));sys.path.insert(0,str((P/'runtime').resolve()))
from replay_carla import read_scene,interpolate
import carla
d,xodr=read_scene(P/'scenario.json');m=carla.Map(d['map_name'],xodr.read_text(encoding='utf-8'))
W,H,FPS=1400,860,15
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16);large=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',30)
base=Image.new('RGB',(W,H),(17,29,34));dr=ImageDraw.Draw(base)
dr.text((28,16),'0508656 · 四视角动态目标恢复',font=large,fill=(232,241,230));dr.text((30,61),'前视视频时间轴 0–123 s  |  与 MeituanBrake0508656.xodr 共用坐标  |  轨迹示意，非 CARLA 实机画面',font=font,fill=(147,187,173))
dr.rounded_rectangle((1100,106,1380,746),radius=12,fill=(27,45,47));dr.text((1120,126),'当前有效目标',font=font,fill=(225,236,224))
arr=np.asarray(base).copy();roads=[];marks=[]
for road in [10,20,30,40,113]:
 for lane in ([-1] if road==113 else [-4,-3,-2,2,3,4]):
  points=[];left=[];right=[]
  for ss in np.arange(.05,600,.8):
   wp=m.get_waypoint_xodr(road,lane,float(ss))
   if wp is None:break
   pp=wp.transform;h=-math.radians(pp.rotation.yaw);x=pp.location.x;y=-pp.location.y;w=wp.lane_width/2
   points.append((x,y));left.append((x-w*math.sin(h),y+w*math.cos(h)));right.append((x+w*math.sin(h),y-w*math.cos(h)))
  if points:
   roads.append((left+right[::-1],(69,78,77) if abs(lane)<4 else (92,103,98)))
   if abs(lane)==2:marks.append((left if lane<0 else right,True))
   if abs(lane)==3:marks.append((left,False))
exe=P/'runtime/ffmpeg.exe';dest=P/'preview/trajectory_replay.mp4';log=(P/'validation/preview_ffmpeg.log').open('w')
proc=subprocess.Popen([str(exe),'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],stdin=subprocess.PIPE,stderr=log)
for step in range(round(d['duration_s']*FPS)+1):
 t=step/FPS;ego=interpolate(d['actors'][0]['samples'],t);h=ego['h'];co=math.cos(h);si=math.sin(h);scale=7.5
 def pt(x,y):
  dx=x-ego['x'];dy=y-ego['y'];return (round(412+(dx*co+dy*si)*scale),round(399-(-dx*si+dy*co)*scale))
 def poly(p,c):cv2.fillPoly(img,[np.array([pt(*v) for v in p],np.int32)],c,lineType=cv2.LINE_AA)
 img=arr.copy();cv2.rectangle(img,(25,105),(1080,745),(34,59,47),-1)
 poly([(-322,-32),(-258,-32),(-258,32),(-322,32)],(69,78,77))
 for pp,col in roads:poly(pp,col)
 for pp,solid in marks:
  aa=np.array([pt(*v) for v in pp],np.int32)
  if solid:cv2.polylines(img,[aa],False,(213,193,113),1,cv2.LINE_AA)
  else:
   for i in range(0,len(aa)-4,12):cv2.polylines(img,[aa[i:i+5]],False,(216,219,205),1,cv2.LINE_AA)
 poly([(55,-13),(61,-13),(61,13),(55,13)],(105,149,133))
 active=[]
 for i,a in enumerate(d['actors']):
  if not a['start_t']<=t<=a['end_t']:continue
  s=interpolate(a['samples'],t);x,y=pt(s['x'],s['y'])
  if not 25<x<1080 or not 108<y<678:continue
  active.append((i,a));l=a['dimensions_m']['length']/2;w=a['dimensions_m']['width']/2;ch=math.cos(s['h']);sh=math.sin(s['h'])
  pp=[(s['x']+xx*ch-yy*sh,s['y']+xx*sh+yy*ch) for xx,yy in [(-l,-w),(l,-w),(l,w),(-l,w)]]
  color=tuple(int(v) for v in a['color'].split(',')) if a.get('color') else (199,154,112)
  if a['id']=='ego':color=(71,218,171)
  poly(pp,color);cv2.polylines(img,[np.array([pt(*v) for v in pp],np.int32)],True,(219,236,219),1,cv2.LINE_AA)
  tip=pt(s['x']+(l+1)*ch,s['y']+(l+1)*sh);cv2.arrowedLine(img,(x,y),tip,color,1,cv2.LINE_AA,tipLength=.3)
  cv2.putText(img,str(i),(x-4,y-12),cv2.FONT_HERSHEY_SIMPLEX,.43,(247,246,223),1,cv2.LINE_AA)
 img[:105]=arr[:105];img[:,1081:]=arr[:,1081:];img[746:]=arr[746:];img[:,:25]=arr[:,:25]
 im=Image.fromarray(img);dr=ImageDraw.Draw(im);dr.text((42,121),'前视参考时间  {:06.2f} / 123 s'.format(t),font=font,fill=(231,241,228))
 for j,(i,a) in enumerate(active[:13]):dr.text((1115,174+j*35),('%02d  '%i)+a['label_zh'][:13],font=small,fill=(209,228,213))
 dr.text((1118,682),'独立时钟入场 / 30 Hz 轨迹',font=small,fill=(132,187,164));dr.text((1118,710),'数字对应目标清单',font=small,fill=(132,187,164))
 labels=[e['label_zh'] for e in d['events'] if e['start_t']<=t<=e['end_t']]
 dr.rectangle((31,680,1076,737),fill=(24,40,43));dr.text((44,698),'；'.join(labels) if labels else '沿视频时序行驶',font=font,fill=(218,231,214))
 dr.line((35,784,1362,784),fill=(67,93,85),width=6);dr.line((35,784,35+int(1327*t/123),784),fill=(71,218,171),width=6)
 dr.text((35,809),'估计轨迹 · 外观采用 CARLA 原生车型代理 · 不用于碰撞力学结论',font=small,fill=(143,178,163))
 if step in [0,70*FPS,100*FPS,103*FPS,119*FPS,122*FPS]:im.save(P/'preview'/('timeline_%03d.png'%round(t)))
 proc.stdin.write(np.asarray(im).tobytes())
proc.stdin.close();assert proc.wait()==0;log.close();print(dest,dest.stat().st_size)
