"""Four original views beside the reconstructed XODR trajectory, not CARLA footage."""
import sys,math,json,subprocess,os,shutil
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));sys.path.insert(0,str(P.parent/'dynamic_replay_014346/runtime'))
from replay_carla import read_scene,interpolate
from preview_geometry import road_polygons,ROADS,pose
d,_=read_scene(P/'scenario.json');src=next(P.parent.glob('*LNDEA7HF3SH016955*'));caps={v:cv2.VideoCapture(str(src/(v+'.mp4'))) for v in ['front','rear','left','right']}
W,H,FPS=1440,900,15;font='C:/Windows/Fonts/msyh.ttc';f=ImageFont.truetype(font,20);small=ImageFont.truetype(font,15);big=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',30)
world=np.full((1600,1600,3),(33,52,48),np.uint8)
def wp(x,y):return (round((x+260)*4),round((160-y)*4))
for poly in road_polygons():cv2.fillPoly(world,[np.array([wp(x,y) for x,y in poly],np.int32)],(87,93,91),cv2.LINE_AA)
for rid,r in ROADS.items():
 for off,col in [(0,(204,176,90)),(-r['n']*3.5-r['median'],(185,187,172)),(r['n']*3.5+r['median'],(185,187,172))]:
  a=pose(rid,0,off);b=pose(rid,r['length'],off);cv2.line(world,wp(a[0],a[1]),wp(b[0],b[1]),col,1,cv2.LINE_AA)
 if r['median']:
  a=pose(rid,0,-1.2);b=pose(rid,r['length'],1.2);cv2.rectangle(world,wp(min(a[0],b[0]),max(a[1],b[1])),wp(max(a[0],b[0]),min(a[1],b[1])),(72,103,60),-1)
  for side in [-1,1]:
   for offset in [4.7,8.2]:
    for s in range(0,int(r['length']),9):
     a=pose(rid,s,side*offset);b=pose(rid,s+4,side*offset);cv2.line(world,wp(a[0],a[1]),wp(b[0],b[1]),(190,191,180),1)
for x in range(-150,55,28):cv2.circle(world,wp(x,-8.7),4,(148,161,153),-1)
for a,b in [((-152,7.3),(70,7.3)),((-155,-12.2),(-13,-12.2)),((-9,-22),(-9,-200)),((8,-22),(8,-200))]:cv2.line(world,wp(*a),wp(*b),(51,124,73),4)
for cx,cy,rot in [(-156,0,True),(-15.7,0,True),(15.7,0,True),(0,-15.2,False)]:
 for i in range(8):
  u=-3.5+i*.9
  a=(cx-1.8,cy+u) if rot else (cx+u,cy-1.8);b=(cx+1.8,cy+u+.45) if rot else (cx+u+.45,cy+1.8);cv2.rectangle(world,wp(a[0],b[1]),wp(b[0],a[1]),(221,222,207),-1)
base=Image.new('RGB',(W,H),(15,25,30));dr=ImageDraw.Draw(base);dr.text((24,18),'016955 · 两次右转动态恢复',font=big,fill=(232,239,232));dr.text((26,61),'现有 XODR 坐标 · 29 个目标 · 四视角对照 · 轨迹示意，非 CARLA 运行画面',font=f,fill=(151,184,169))
exe=os.environ.get('FFMPEG_EXE') or shutil.which('ffmpeg') or str(P.parent/'dynamic_replay_0508656/runtime/ffmpeg.exe');out=P/'preview/GreenRail016955_FourView_Timeline.mp4';proc=subprocess.Popen([exe,'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-threads','4','-preset','fast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
snapshots=[51,74,102,120,156,169];mini=cv2.resize(world[120:1490,220:1390],(272,318));previous={}
for frame in range(2701):
 t=frame/FPS;ego=interpolate(d['actors'][0]['samples'],t);cx,cy=ego['x'],ego['y'];mx,my=wp(cx,cy)
 im=base.copy();dr=ImageDraw.Draw(im);local=cv2.getRectSubPix(world,(420,338),(float(mx),float(my)));local=cv2.resize(local,(840,676),interpolation=cv2.INTER_LINEAR)
 def pt(x,y):return (round(420+(x-cx)*8),round(338-(y-cy)*8))
 active=[]
 for i,a in enumerate(d['actors']):
  if not a['start_t']<=t<=a['end_t']:continue
  active.append(a);s=interpolate(a['samples'],t);l=a['dimensions_m']['length']/2;w=a['dimensions_m']['width']/2;h=s['h'];co,si=math.cos(h),math.sin(h)
  color=(234,243,234) if a['id']=='ego' else (63,213,178) if a['category']=='sweeper' else (224,92,101) if a['category']=='bus' else (232,181,91) if a['category']=='truck' else (92,177,216) if a['category']=='pedestrian' else (158,194,212)
  q=[pt(s['x']+x*co-y*si,s['y']+x*si+y*co) for x,y in [(-l,-w),(l,-w),(l,w),(-l,w)]];cv2.fillConvexPoly(local,np.array(q,np.int32),color,cv2.LINE_AA);x,y=pt(s['x'],s['y']);p=pt(s['x']+l*.6*co,s['y']+l*.6*si);cv2.arrowedLine(local,(x,y),p,(30,48,53),2,tipLength=.4)
  if 10<x<825 and 20<y<660:cv2.putText(local,str(i),(x-4,y-10),cv2.FONT_HERSHEY_SIMPLEX,.44,(245,243,220),1,cv2.LINE_AA)
 im.paste(Image.fromarray(local),(24,112));dr=ImageDraw.Draw(im);dr.rounded_rectangle((34,122,370,165),radius=6,fill=(19,35,37));dr.text((46,132),f'视频 {t:06.2f} s    活跃目标 {len(active):02d}',font=f,fill=(229,238,226))
 for j,(view,cap) in enumerate(caps.items()):
  if frame==0 and view=='left':cap.read()
  ok,vid=cap.read()
  if ok:previous[view]=vid
  vid=previous[view];vid=cv2.resize(cv2.cvtColor(vid,cv2.COLOR_BGR2RGB),(268,151));x=882+(j%2)*278;y=140+(j//2)*187;im.paste(Image.fromarray(vid),(x,y));dr.text((x,y-23),{'front':'原始前视','rear':'原始后视','left':'原始左视','right':'原始右视'}[view],font=small,fill=(187,205,192))
 dr.text((884,509),'同一时刻的四路原始视频',font=f,fill=(185,211,195));im.paste(Image.fromarray(mini),(882,547));dr=ImageDraw.Draw(im)
 px=882+(mx-220)*272/1170;py=547+(my-120)*318/1370;dr.ellipse((px-4,py-4,px+4,py+4),fill=(240,115,82));dr.text((1166,552),'全局路网定位',font=small,fill=(164,197,180))
 labels=[('白色','自车'),('红色','大客车'),('绿色','清扫机器人'),('黄色','货车'),('蓝色','其他目标')]
 for j,(c,l) in enumerate(labels):dr.text((1166,589+j*30),c+' · '+l,font=small,fill=(181,208,193))
 active_events=[e['label_zh'] for e in d['events'] if e['start_t']<=t<=e['end_t']];dr.rounded_rectangle((25,797,864,854),radius=8,fill=(25,42,43));dr.text((39,812),'；'.join(active_events[:2]) or '沿视频时间轴推进',font=f,fill=(219,230,211));dr.line((25,876,1416,876),fill=(54,82,76),width=5);dr.line((25,876,25+int(1391*t/180),876),fill=(85,201,163),width=5)
 if any(frame==round(v*FPS) for v in snapshots):im.save(P/'preview'/('timeline_%03d.png'%round(t)))
 proc.stdin.write(np.asarray(im).tobytes())
proc.stdin.close();assert proc.wait()==0
for c in caps.values():c.release()
print('Saved',out,out.stat().st_size)
