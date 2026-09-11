"""Source-video / XODR-trajectory comparison. NOT CARLA footage."""
import cv2,numpy as np,json,math,sys,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from replay_carla import read_scene,interpolate
import os,shutil
d,_=read_scene(P/'scenario.json');SRC=next(P.parent.glob('*LHTDA4B45SYANA031*'));caps={n:cv2.VideoCapture(str(SRC/(n+'.mp4'))) for n in ['front','rear','left','right']}
W,H=1600,960;FPS=12;dur=d['duration_s'];font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18);big=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',29);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
colors=[(72,191,228),(200,216,218),(233,238,232),(240,217,145),(150,221,184),(194,202,218),(218,185,208),(100,155,238),(120,132,144),(185,175,145),(139,161,151),(251,139,86)]
base=Image.new('RGB',(W,H),(14,23,33));dr=ImageDraw.Draw(base);dr.text((28,20),'ANA031  /  雨夜停驶 · 动态场景复原',font=big,fill=(231,239,240));dr.text((30,64),'左：当前 XODR 上的估计轨迹   右：按偏移对齐的原视频   |   非 CARLA 运行录屏',font=font,fill=(155,180,192))
for i,a in enumerate(d['actors']):
 x=1020+(i%2)*280;y=540+(i//2)*42;dr.ellipse((x,y+5,x+9,y+14),fill=colors[i]);dr.text((x+17,y),f'{i:02d} '+a['label_zh'].split('（')[0],font=small,fill=(212,222,226))
dr.text((1020,815),'鱼眼原图保留；侧面像素不直接当作米制坐标',font=small,fill=(141,168,181));dr.text((1020,844),'偏移：左 +0.9 s · 右 +7.4 s · 后 +7.5 s（估计）',font=small,fill=(141,168,181))
exe=os.environ.get('FFMPEG_EXE') or shutil.which('ffmpeg') or str(P.parent/'dynamic_replay_024388/runtime/ffmpeg.exe');dest=P/'preview/video_trajectory_comparison.mp4';proc=subprocess.Popen([exe,'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
arr=np.asarray(base)
def poly(im,pts,c):cv2.fillPoly(im,[np.array(pts,np.int32)],c,cv2.LINE_AA)
for step in range(round(dur*FPS)+1):
 t=min(dur,step/FPS);ego=interpolate(d['actors'][0]['samples'],t);cx=ego['x']+18;scale=7.;im=arr.copy()
 def pt(x,y):return (round(510+(x-cx)*scale),round(460-y*scale))
 cv2.rectangle(im,(24,105),(990,866),(28,44,47),-1)
 poly(im,[pt(-170,-14.7),pt(160,-14.7),pt(160,14.7),pt(-170,14.7)],(65,74,83));poly(im,[pt(35,-100),pt(59,-100),pt(59,100),pt(35,100)],(65,74,83))
 for a,b in [(-170,25),(69,160)]:
  for y in [-14,14,-.2,.2]:cv2.line(im,pt(a,y),pt(b,y),(165,161,131),1,cv2.LINE_AA)
  for y in [-10.5,-7,-3.5,3.5,7,10.5]:
   for x in range(a,b,8):cv2.line(im,pt(x,y),pt(min(x+4,b),y),(123,137,148),1,cv2.LINE_AA)
 for x in [29,65]:
  for y in np.arange(-14,14,.95):poly(im,[pt(x-2,y),pt(x+2,y),pt(x+2,y+.45),pt(x-2,y+.45)],(156,165,168))
 for x in range(-160,159,11):
  if 23<x<73:continue
  for sg in [-1,1]:cv2.circle(im,pt(x,sg*18),7,(46,85,74),-1,cv2.LINE_AA)
 poly(im,[pt(-14,-21),pt(10,-21),pt(10,-17),pt(-14,-17)],(92,115,122))
 for i,a in enumerate(d['actors']):
  if not a['start_t']<=t<=a['end_t']:continue
  s=interpolate(a['samples'],t);co=math.cos(s['h']);si=math.sin(s['h']);l=a['dimensions_m']['length']/2;w=a['dimensions_m']['width']/2
  def q(x,y):return pt(s['x']+x*co-y*si,s['y']+x*si+y*co)
  trail=[pt(v['x'],v['y']) for v in a['samples'][::6] if t-5<=v['t']<=t]
  if len(trail)>1:cv2.polylines(im,[np.array(trail,np.int32)],False,colors[i],1,cv2.LINE_AA)
  poly(im,[q(-l,-w),q(l,-w),q(l,w),q(-l,w)],colors[i]);cv2.line(im,q(l*.3,-w*.7),q(l*.3,w*.7),(25,35,43),2,cv2.LINE_AA);x,y=q(0,0)
  if 40<x<975 and 128<y<844:cv2.putText(im,f'{i:02d}',(x-8,y-12),cv2.FONT_HERSHEY_SIMPLEX,.44,(245,244,233),1,cv2.LINE_AA)
 im[:105]=arr[:105];im[867:]=arr[867:];im[:,:24]=arr[:,:24];im[:,991:]=arr[:,991:];image=Image.fromarray(im);draw=ImageDraw.Draw(image)
 for k,name in enumerate(['front','rear','left','right']):
  cap=caps[name];file_t=t+d['camera_file_time_offsets_s'][name];x=1010+(k%2)*292;y=109+(k//2)*202;length=cap.get(7)/cap.get(5);draw.text((x,y),f'{name.upper()}  文件 {file_t:.1f}s'+('  鱼眼' if name in ['left','right'] else ''),font=small,fill=(193,213,225))
  if file_t<length-.07:
   cap.set(cv2.CAP_PROP_POS_MSEC,file_t*1000);ok,frame=cap.read()
   if ok:image.paste(Image.fromarray(cv2.cvtColor(cv2.resize(frame,(280,158)),cv2.COLOR_BGR2RGB)),(x,y+25))
  else:draw.rectangle((x,y+25,x+280,y+183),fill=(25,35,45));draw.text((x+43,y+88),'该视角视频已结束',font=font,fill=(119,143,155))
 draw.text((40,122),f'回放 {t:05.1f} / 63.7 s',font=font,fill=(221,239,240));draw.text((40,154),'米制坐标 · +X 前进 / +Y 左侧',font=small,fill=(132,164,174));active=[e['label_zh'] for e in d['events'] if e['start_t']<=t<=e['end_t']];draw.rectangle((36,798,981,854),fill=(20,33,42));draw.text((45,812),'；'.join(active[:2]),font=font,fill=(191,218,220))
 draw.line((30,909,1570,909),fill=(52,73,87),width=6);draw.line((30,909,30+1540*t/dur,909),fill=(69,184,201),width=6);draw.text((30,926),'视频参照的视觉估计；远处与遮挡目标已在说明中标注。',font=small,fill=(132,158,169))
 if step in [int(24*FPS),int(33*FPS),int(45*FPS),int(60*FPS)]:image.save(P/'preview'/f'comparison_{round(t):02d}.png')
 proc.stdin.write(np.asarray(image).tobytes())
proc.stdin.close();assert proc.wait()==0
for c in caps.values():c.release()
print(dest,dest.stat().st_size)

