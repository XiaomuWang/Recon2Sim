import sys,math,json,subprocess
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));sys.path.insert(0,str(P.parent/'environment_reconstruction_014346/scripts'));sys.path.insert(0,str(P/'runtime'))
from replay_carla import read_scene,interpolate
from road_layout import pose
import imageio_ffmpeg
d,_=read_scene(P/'scenario.json');W,H=1400,860;FPS=15
font='C:/Windows/Fonts/msyh.ttc';f=ImageFont.truetype(font,20);large=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',32);small=ImageFont.truetype(font,16)
colors=[(224,233,230),(164,156,108),(236,184,76),(58,116,202),(236,115,47),(191,190,179),(105,177,209),(160,196,194),(111,132,126),(111,132,126)]
base=Image.new('RGB',(W,H),(16,27,32));draw=ImageDraw.Draw(base)
draw.text((28,18),'014346 · 动态目标轨迹回放',font=large,fill=(228,237,231));draw.text((30,62),'四视角视频参照 | 当前 XODR 便道 | 轨迹示意预览，非 CARLA 运行画面',font=f,fill=(147,182,172))
draw.rounded_rectangle((1090,105,1380,755),radius=12,fill=(26,42,46));draw.text((1110,125),'场景目标',font=f,fill=(221,232,222))
for i,a in enumerate(d['actors']):
 y=171+i*47;draw.ellipse((1110,y+3,1122,y+15),fill=colors[i]);draw.text((1131,y),a['label_zh'],font=small,fill=(217,225,218))
draw.text((1110,681),'30 Hz 时间戳轨迹',font=small,fill=(133,180,164));draw.text((1110,709),'坐标与现有地图共用原点',font=small,fill=(133,180,164))
arr=np.asarray(base).copy();exe=imageio_ffmpeg.get_ffmpeg_exe();dest=P/'preview/trajectory_replay.mp4'
proc=subprocess.Popen([exe,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
def polygon(img,points,c):cv2.fillPoly(img,[np.array(points,np.int32)],c,lineType=cv2.LINE_AA)
for step in range(round(d['duration_s']*FPS)+1):
 t=step/FPS;ego=interpolate(d['actors'][0]['samples'],t);cx=max(-75,min(20,ego['x']+13));scale=11.4
 def point(x,y):return (round(548+(x-cx)*scale),round(398-y*scale))
 img=arr.copy();cv2.rectangle(img,(25,104),(1067,735),(28,43,43),-1)
 # Road and roadside geometry sampled from the same static scene definition.
 for s in np.arange(0,210,.75):
  q=[pose(s,-2.9),pose(s+.75,-2.9),pose(s+.75,2.9),pose(s,2.9)];polygon(img,[point(p[0],p[1]) for p in q],(76,82,76))
 polygon(img,[point(-6,-3),point(6,-3),point(6,-32),point(-6,-32)],(76,82,76))
 for offset,col in [(4.2,(123,142,127)),(-4.02,(66,136,83)),(3.3,(186,191,178)),(-3.3,(186,191,178))]:
  for s in np.arange(0,210,1):
   if offset<0 and 94<s<106:continue
   if offset==-3.3 and s<106:continue
   a=pose(s,offset);b=pose(s+1,offset);cv2.line(img,point(a[0],a[1]),point(b[0],b[1]),col,3,cv2.LINE_AA)
 for s in np.arange(0,210,1):
  if 92<s<108:continue
  a=pose(s);b=pose(s+1);cv2.line(img,point(a[0],a[1]),point(b[0],b[1]),(206,175,83) if s>100 else (180,184,170),1,cv2.LINE_AA)
 cv2.putText(img,'GATE',(point(0,-13)[0]-25,point(0,-13)[1]),cv2.FONT_HERSHEY_SIMPLEX,.5,(148,183,156),1,cv2.LINE_AA)
 for i,a in enumerate(d['actors']):
  if not a['start_t']<=t<=a['end_t']:continue
  s=interpolate(a['samples'],t);h=s['h'];co=math.cos(h);si=math.sin(h);l=a['dimensions_m']['length']/2;w=a['dimensions_m']['width']/2;c=colors[i]
  def pp(x,y):return point(s['x']+x*co-y*si,s['y']+x*si+y*co)
  polygon(img,[pp(-l,-w),pp(l,-w),pp(l,w),pp(-l,w)],c)
  cv2.line(img,pp(l*.3,-w*.65),pp(l*.3,w*.65),(31,48,53),2,cv2.LINE_AA);cv2.arrowedLine(img,pp(0,0),pp(l+1,0),c,1,cv2.LINE_AA,tipLength=.3)
  x,y=pp(0,0)
  if 40<x<1040 and 120<y<710:cv2.putText(img,str(i),(x-5,y-9),cv2.FONT_HERSHEY_SIMPLEX,.42,(244,246,231),1,cv2.LINE_AA)
 # Clip drawing to map pane without overwriting sidebar/title.
 img[:104]=arr[:104];img[:,1068:]=arr[:,1068:];img[736:]=arr[736:];img[:,:25]=arr[:,:25]
 im=Image.fromarray(img);dr=ImageDraw.Draw(im);dr.text((42,116),'视频 {:06.2f} s    回放 {:06.2f} / 107 s'.format(t+52,t),font=f,fill=(224,237,228))
 active=[e['label_zh'] for e in d['events'] if e['start_t']<=t<=e['end_t']]
 dr.rectangle((32,679,1060,730),fill=(24,38,41));dr.text((44,693),'；'.join(active) if active else '按视频时序推进',font=f,fill=(202,223,207))
 dr.line((35,784,1363,784),fill=(67,92,86),width=6);dr.line((35,784,35+int(1328*t/107),784),fill=(94,206,167),width=6)
 dr.text((35,810),'源视频 52 s',font=small,fill=(147,176,164));dr.text((1246,810),'159 s',font=small,fill=(147,176,164))
 if step in [int(16*FPS),int(32*FPS),int(88*FPS)]:im.save(P/'preview'/('timeline_%03d.png'%round(t+52)))
 proc.stdin.write(np.asarray(im).tobytes())
proc.stdin.close();assert proc.wait()==0
print(dest,dest.stat().st_size)
