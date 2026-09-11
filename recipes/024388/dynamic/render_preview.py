"""Synchronized source frames + map trajectories. This is NOT CARLA engine footage."""
import json,math,subprocess,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));sys.path.insert(0,str(P.parent/'dynamic_replay_014346/runtime'))
from replay_carla import read_scene,interpolate
import carla
d,xodr=read_scene(P/'scenario.json');m=carla.Map(d['map_name'],xodr.read_text());wps=m.generate_waypoints(.7)
src=P.parent/'萝卜运力_LNDEA7HF1SH024388_0814_路口右转';cams=['front','rear','left','right'];caps=[cv2.VideoCapture(str(src/(n+'.mp4'))) for n in cams]
W,H,FPS=1440,900,10;font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19);sm=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16);big=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',30)
base=Image.new('RGB',(W,H),(17,27,34));dr=ImageDraw.Draw(base);dr.text((28,16),'024388 · 路口右转动态恢复',font=big,fill=(234,241,236));dr.text((30,61),'原视频四视角对照 / 37 个目标 / 共用已交付 XODR 坐标 / 估计轨迹预览，非 CARLA 运行画面',font=font,fill=(153,187,183));arr=np.array(base)
colors=[tuple(int(x) for x in a['color'].split(',')) for a in d['actors']];colors[0]=(71,218,187)
exe=str(P/'runtime/ffmpeg.exe');dest=P/'preview/FourView_Trajectory_Review.mp4'
proc=subprocess.Popen([exe,'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-crf','21','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
lut=np.array([round((i/255)**.65*255) for i in range(256)],np.uint8)
for step in range(round(d['duration_s']*FPS)+1):
 t=step/FPS;ego=interpolate(d['actors'][0]['samples'],t);cx=min(-13,ego['x']+15);cy=0;scale=7.5
 def point(x,y):return (round(423+(x-cx)*scale),round(428-y*scale))
 im=arr.copy();cv2.rectangle(im,(25,105),(820,789),(36,56,50),-1)
 for r in wps:
  x,y=r.transform.location.x,-r.transform.location.y;px,py=point(x,y)
  if 10<px<835 and 90<py<804:cv2.circle(im,(px,py),round(r.lane_width*scale/2),(78,82,84),-1)
 for xywh in [(-32,-20,43,19),(-16,24,22,18),(12,24,8,19)]:
  x,y,w,h=xywh;p1=point(x-w/2,y+h/2);p2=point(x+w/2,y-h/2);cv2.rectangle(im,p1,p2,(68,100,101),-1)
 for z in np.arange(-175,-14,5):cv2.line(im,point(z,0),point(z+2.5,0),(205,168,66),1)
 for y in np.arange(-2.9,3.2,.75):cv2.line(im,point(-12.7,y),point(-9.3,y),(198,203,195),3)
 for x in np.arange(-2.9,3.2,.75):
  for y in [-9.4,9.4]:cv2.line(im,point(x,y-1.4),point(x,y+1.4),(198,203,195),3)
 cv2.line(im,point(8.7,-7),point(8.7,7),(73,128,162),4)
 active=[]
 for i,a in enumerate(d['actors']):
  if not a['start_t']<=t<=a['end_t']:continue
  active.append((i,a));s=interpolate(a['samples'],t);h=s['h'];co,si=math.cos(h),math.sin(h);l,w=a['dimensions_m']['length']/2,a['dimensions_m']['width']/2
  def pp(x,y):return point(s['x']+x*co-y*si,s['y']+x*si+y*co)
  p=np.array([pp(-l,-w),pp(l,-w),pp(l,w),pp(-l,w)],np.int32);cv2.fillPoly(im,[p],colors[i],lineType=cv2.LINE_AA);cv2.polylines(im,[p],True,(223,231,225),1,cv2.LINE_AA);cv2.arrowedLine(im,pp(0,0),pp(l+1,0),(231,234,224),1,tipLength=.3)
  x,y=pp(0,0)
  if 40<x<795 and 160<y<740:cv2.putText(im,str(i),(x-5,y-9),cv2.FONT_HERSHEY_SIMPLEX,.4,(245,245,239),1,cv2.LINE_AA)
 im[:105]=arr[:105];im[:,821:]=arr[:,821:];im[790:]=arr[790:];im[:,:25]=arr[:,:25]
 for j,cap in enumerate(caps):
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read()
  if not ok:continue
  frame=cv2.cvtColor(cv2.LUT(frame,lut),cv2.COLOR_BGR2RGB);frame=cv2.resize(frame,(276,155));x=846+(j%2)*289;y=143+(j//2)*190;im[y:y+155,x:x+276]=frame
 out=Image.fromarray(im);dr=ImageDraw.Draw(out);dr.text((42,119),'视频时间 {:06.2f} s / 179 s'.format(t),font=font,fill=(229,241,232))
 for j,n in enumerate(['前视','后视','左视','右视']):dr.text((846+(j%2)*289,116+(j//2)*190),n+' · 原视频提亮',font=sm,fill=(176,203,194))
 dr.text((846,522),'当前活动目标：'+str(len(active)),font=font,fill=(223,233,225))
 # Nearby targets have priority in the concise live legend.
 near=sorted(active,key=lambda ia:0 if ia[1]['id']=='ego' else (interpolate(ia[1]['samples'],t)['x']-ego['x'])**2+(interpolate(ia[1]['samples'],t)['y']-ego['y'])**2)[:8]
 for j,(i,a) in enumerate(near):dr.text((846,559+j*27),f"{i:02d}  {a['label_zh']}",font=sm,fill=colors[i] if max(colors[i])>130 else (172,188,196))
 ev=[e['label_zh'] for e in d['events'] if e['start_t']<=t<=e['end_t']];dr.rectangle((31,730,810,783),fill=(21,36,40));dr.text((42,744),'；'.join(ev[:1]) if ev else '按视频时序推进',font=font,fill=(185,222,210))
 dr.line((30,837,1410,837),fill=(64,88,85),width=5);dr.line((30,837,30+round(1380*t/179),837),fill=(72,214,179),width=5);dr.text((30,858),'位置、尺寸与遮挡段为地图约束下的估计；原始视频未修改。',font=sm,fill=(142,177,166))
 if step in [650,880,1040,1100,1400]:out.save(P/'preview'/('review_%03d.png'%round(t)))
 proc.stdin.write(np.array(out).tobytes())
proc.stdin.close();assert proc.wait()==0
for c in caps:c.release()
print(dest,dest.stat().st_size)
