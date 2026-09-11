"""Four-view manual identity/time anchors; estimated metric paths on the delivered map."""
import csv,hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
P=Path(__file__).resolve().parents[1];FPS=30;END=179.
actors=[]
BP={'car':['vehicle.lincoln.mkz_2020','vehicle.tesla.model3'], 'suv':['vehicle.audi.etron','vehicle.nissan.patrol_2021'], 'mpv':['vehicle.volkswagen.t2','vehicle.nissan.patrol'], 'truck':['vehicle.carlamotors.carlacola'], 'motorcycle':['vehicle.vespa.zx125','vehicle.yamaha.yzf'], 'tricycle':['vehicle.vespa.zx125'], 'pedestrian':['walker.pedestrian.0001','walker.pedestrian.0004']}
DIMS={'car':(4.7,1.85,1.5),'suv':(4.8,1.95,1.75),'mpv':(4.9,1.9,1.9),'truck':(6.8,2.25,3.25),'motorcycle':(1.9,.7,1.65),'tricycle':(2.7,1.2,1.6),'pedestrian':(.5,.5,1.73)}
def road(q):
 # Exact right-turn lane centre: approach, road100 straight, R6.65 arc, exit.
 if q<=171.7:return q-180,-1.65,0.
 angle=min(math.pi/2,(q-171.7)/6.65)
 if q<=171.7+6.65*math.pi/2:return -8.3+6.65*math.sin(angle),-8.3+6.65*math.cos(angle),-angle
 return -1.65,-8.3-(q-171.7-6.65*math.pi/2),-math.pi/2

def add(aid,label,kind,keys,color='100,110,120',views='',note='',route=False,confidence='medium'):
 arr=np.array(keys,float);tt=np.linspace(arr[0,0],min(END,arr[-1,0]),round((min(END,arr[-1,0])-arr[0,0])*FPS)+1)
 fs=[PchipInterpolator(arr[:,0],arr[:,i]) for i in range(1,arr.shape[1])]
 if route:
  q=fs[0](tt);poses=np.array([road(v) for v in q]);xy=poses[:,:2];hh=poses[:,2]
 else:
  xy=np.array([f(tt) for f in fs[:2]]).T;vel=np.array([f.derivative()(tt) for f in fs[:2]]).T;hh=np.arctan2(vel[:,1],vel[:,0])
  moving=np.linalg.norm(vel,axis=1)>.005
  if len(fs)>2:hh=np.radians(fs[2](tt))
  elif moving.any():
   ids=np.where(moving)[0]
   for i in range(len(tt)):
    if not moving[i]:hh[i]=hh[ids[max(0,np.searchsorted(ids,i)-1)]]
  hh=np.unwrap(hh)
 samples=[];dist=0
 for i,t in enumerate(tt):
  if i:dist+=float(np.linalg.norm(xy[i]-xy[i-1]))
  samples.append(dict(t=round(float(t),6),video_t=round(float(t),6),x=round(float(xy[i,0]),5),y=round(float(xy[i,1]),5),z=round(.15*max(0,min(1,((5-math.hypot(xy[i,0]+8.3,xy[i,1]+8.3)) if xy[i,1]>-8.3 else (-3.3-xy[i,0]))/.3+.5)),4) if aid=='red_rider' and xy[i,0]>-8.3 else 0.,h=round(float(hh[i]),7),s=round(dist,5),lateral=0.))
 a=dict(id=aid,label_zh=label,category=kind,dimensions_m=dict(zip(['length','width','height'],DIMS[kind])),blueprint_candidates=BP[kind],color=color,start_t=float(tt[0]),end_t=float(tt[-1]),source_keyframes=keys,source_views=views,confidence=confidence,notes=note,samples=samples,preferred_custom_blueprint='static.prop.luobo_boxtruck' if kind=='truck' else None)
 actors.append(a)

# Timing comes from inspected four-camera stills plus static image flow stop corroboration.
# Low-inlier flow is NOT interpreted as a metric speed measurement.
add('ego','自车','car',[[0,15],[10,37],[20,65],[30,95],[40,124],[45,135],[49,141],[52,143],[72.5,143],[77,152],[82,161],[86,166.3],[90,166.3],[94,168.2],[98,169.7],[102,170.7],[106,172.1],[110,175],[114,178.08],[179,178.08]],'225,231,228','front/right/left/rear',route=True,confidence='high timing / estimated metric',note='Holds at 52-72.5, 86-90 and 114-179 s. Final turn is incomplete, as in video. Spatial scale follows existing XODR; flow only corroborates holds.')
add('lead_white','前方停车白轿车','car',[[0,-142,-1.95],[35,-50,-1.95],[45,-30,-2.05],[66,-30,-2.05],[70,-19,-1.9],[74,-8.5,-1.65],[77,-1.65,-7],[86,-1.65,-47]],'225,228,225','front 45/53/65/69',note='Departure visible; subsequent exit after occlusion inferred.')
add('silver_pass','第一辆左侧超车银轿车','car',[[0,-177,-1.65],[20,-128,-1.65],[40,-64,-1.65],[52,-44,-1.65],[60,-44,-1.65],[63,-40,1.65],[65,-32,1.65],[69,-15,1.65],[72,-3,0],[75,1.5,-16],[84,1.5,-70]],'165,179,183','rear 0-63 / front 65',note='Rear-to-front identity supported; exit branch after disappearance inferred.')
add('dark_pass','第二辆左侧超车深色轿车','car',[[57,-70,-1.65],[63,-50,-1.65],[65,-46,-1.65],[67,-40,1.65],[69,-32,1.65],[72,-16,1.65],[74,-3,0],[76,1.5,-9],[90,1.5,-62]],'38,44,55','rear61/65 / front69')
add('silver_suv_left','第三辆超车后左转SUV','suv',[[63,-73,-1.65],[69,-46,-1.65],[71,-40,1.65],[73,-32,1.65],[77,-20,-1.65],[81,-10,-1.65],[83,-5,-.8],[85,1.65,4],[88,1.65,17],[98,1.65,70]],'173,189,198','rear65-73 / front73/80/84/86',note='Left turn at 84-87 s visible in front.')
add('white_mpv_pass','左超后右转白色MPV','mpv',[[73,-51,-1.65],[80,-31,-1.65],[86,-22,-1.65],[94,-21,-1.65],[98,-18,-1.65],[100,-12,1.65],[102,-5,1.0],[104,1.5,-5],[108,1.5,-22],[118,1.5,-73]],'225,226,220','rear73-100 / left102 / front102-104',note='Stock T2 is a shape substitute; source is a modern MPV.')
add('box_truck','绿橙厢式货车（同一辆）','truck',[[69,-77,-1.65,0],[82,-43,-1.65,0],[94,-30,-1.65,0],[100,-25,-1.65,0],[103,-18.5,.7,15],[106,-9.5,1.65,0],[108,-4.5,.5,-25],[110,.2,-3.3,-65],[114,1.5,-9.2,-90],[179,1.5,-9.2,-90]],'45,106,70','rear69-106 / left106-110 / front110-179',note='Observed truck passes left and stops left-front. Stock CarlaCola fallback differs in cab/body livery.',confidence='high identity and timing / estimated metric')
add('oncoming_white','迎面白轿车','car',[[76,-2,1.65],[78,-12,1.65],[80,-25,1.65],[84,-43,1.65],[100,-140,1.65]],'220,222,214','front77/80 / rear84',note='Different identity from white MPV overtaking from rear.')
add('cross_gray_suv','路口横向灰SUV','suv',[[88,-1.65,25],[92,-1.65,13],[95,-1.65,2],[98,-1.65,-13],[108,-1.65,-72]],'126,142,150','front90-98')
for aid,label,x,ts,col in [('cross_person_1','车前横穿行人一',-9.7,[84,86,88,91],'190,185,164'),('cross_person_2','车前横穿行人二',-10.5,[84.7,86.7,88.7,91.7],'180,141,125')]:
 add(aid,label,'pedestrian',[[ts[0],x,4.7],[ts[1],x,1.8],[ts[2],x,-1.2],[ts[3],x,-5.7]],col,'front84-90',confidence='high timing / estimated metric')
add('navy_pedestrian','车后横穿深蓝衣行人','pedestrian',[[96,-13.4,4.8],[98,-13.4,-.8],[100,-13.4,-4],[103,-13.4,-5.4],[107,-13.4,-5.4]],'43,51,74','rear98 / right102-106')
add('lead_driver','前车左侧站立人员','pedestrian',[[46,-30,-.55,0],[65,-30,-.55,0],[67,-30,-.55,0]],'141,151,146','front49-65',note='Track ends at occlusion; entry into vehicle not asserted.')
add('shop_pedestrian','前车右侧行人','pedestrian',[[46,-28,-4.7],[55,-32,-4.7],[63,-30,-4.7],[72,-27,-4.7]],'211,191,158','front49-69 / right',note='Association on crowded sidewalk uncertain.')
# Pair crossing the approach from the hotel sidewalk toward opposite apartment sidewalk.
for j in range(2):
 add('late_pair_'+str(j+1),'后段结伴横穿行人'+str(j+1),'pedestrian',[[114+j*.5,-11+j*.7,-5],[117+j*.5,-11+j*.7,-1.5],[120+j*.5,-11+j*.7,2],[123+j*.5,-11+j*.7,5.4]],'215,196,194' if j else '215,215,199','right114-116 / rear116-123',note='Direction from hotel curb toward apartment side; metric crossing station estimated.')

# Later cross-street traffic turns from the north arm toward the approach.
def from_right(aid,label,kind,t,col):
 add(aid,label,kind,[[t-10,-1.65,51],[t-5,-1.65,23],[t-2,-1.65,11],[t,-3,3],[t+2,-8,1.65],[t+5,-23,1.65],[t+14,-75,1.65]],col,'rear at '+str(t)+' s',note='Cross-street continuation outside observed image is inferred.')
from_right('late_black','后段横向黑轿车','car',123,'35,37,44')
from_right('late_blue','后段横向蓝轿车','car',129,'61,91,144')
from_right('late_silver','后段横向银轿车','car',145,'163,175,185')
from_right('late_white','后段横向白轿车','car',150,'217,218,209')
add('late_white_mpv','末段横向白MPV','mpv',[[160,-1.65,51],[165,-1.65,23],[168,-1.65,11],[170,-3,3],[172,-8,1.65],[179,-32,1.65]],'223,223,217','rear168-171',note='Slower continuation behind dark sedan after occlusion estimated.')
# Honda reaches rear then turns to its right along approach, passing the right camera.
# This is an north cross-arm -> approach movement, not another following ego right-turn.
add('honda_wait','车后长时间等候深色轿车','car',[[120,-1.65,51,-90],[127,-1.65,22,-90],[132,-1.65,10,-90],[135,-.6,.8,-115],[164,-.6,.8,-115],[166,-2,1,-150],[168,-5,1.4,-180],[171,-12,1.65,-180],[179,-44,1.65,-180]],'62,64,65','rear132-165 / right168-171',note='Four-view crossing direction estimated; hold 135-164 s strongly supported. Front/rear orientation through occlusion uncertain.')
add('last_suv','末段车后SUV','suv',[[164,-1.65,50,-90],[171,-1.65,18,-90],[175,-.4,.8,-115],[179,-.4,.8,-115]],'72,77,76','rear171-179')

add('early_scooter_1','前段迎面电动车','motorcycle',[[4,-114,2.5],[10,-140,2.5],[17,-176,2.5]],'55,58,67','front10',confidence='medium timing / low depth')
add('early_minivan','前段迎面面包车','mpv',[[18,-70,1.65],[25,-108,1.65],[37,-174,1.65]],'152,154,155','front25')
add('early_red_scooter','前段红色电动车','motorcycle',[[28,-50,2.5],[35,-83,2.5],[50,-172,2.5]],'174,48,44','front35')
add('yellow_delivery_1','前段黄色配送骑手','motorcycle',[[53,-53,-3.25],[57,-41,-3.25],[59,-33.3,-3.25],[60,-33.3,.65],[61,-29,.65],[64,-22,.65],[69,-6,-.5],[74,0,-22]],'213,179,30','rear57 / front61',note='Link between rear and front rider is tentative.')
add('yellow_delivery_2','后段黄色配送骑手','motorcycle',[[69,-51,-3.25],[77,-37,-3.25],[86,-20,-3.25],[96,-18,-3.25],[102,-14,-3.25]],'218,178,25','rear69-102',note='Ends at rear-view occlusion. Rider in right view 108 s is not assigned the same identity.')
add('orange_oncoming','迎面橙衣骑手','motorcycle',[[78,-3,2.6],[82,-20,2.6],[88,-42,2.6],[98,-99,2.6]],'195,95,32','front82 / rear88')
add('cross_scooter_1','路口横向白电动车','motorcycle',[[94,-2.6,27],[98,-2.6,5],[101,-2.6,-11],[112,-2.6,-64]],'196,198,193','front98-100')
add('red_rider','右侧通过骑手','motorcycle',[[100,-36,-2.8],[106,-17,-2.8],[108,-9,-2.8],[111,-4,-10],[122,-2.7,-64]],'151,47,53','rear106 / right108-110',note='Rider passes on damaged curb/sidewalk edge, as visible in right view; keep off-lane segment, with estimated 0.15 m curb elevation.')
for aid,lab,t,col in [('blue_light_scooter','蓝灯电动车',120,'74,86,130'),('white_helmet_scooter','白盔电动车',126,'214,214,204'),('late_scooter','后段电动车',156,'56,64,73'),('last_white_scooter','末段白色电动车',173,'212,210,193')]:
 from_right(aid,lab,'motorcycle',t,col)
from_right('cargo_trike','紫色货运三轮车','tricycle',147,'118,72,147')
add('final_red_person','末段前方红衣行人','pedestrian',[[174,-4,-24],[177,-4,-20],[179,-4,-17.5]],'177,59,56','front177',note='Identity/occluded earlier movement not inferred.')
events=[(52,72.5,'hold1','自车停车，连续三辆车从左侧超过'),(84,91.7,'cross','两名行人横穿，自车短暂停车'),(98,106,'mpv','白色MPV左超后右转'),(103,114,'truck','同一辆绿橙货车从后方左超并右转'),(114,179,'hold2','自车与货车在路口停留'),(114,123.5,'pair','结伴行人从酒店侧横穿'),(135,164,'honda','深色轿车在车后等候'),(168,174,'late','等候轿车及白色电动车通过右侧视野')]
d=dict(format_version=1,scene='LuoboTurn024388_DynamicReplay',target_carla_versions=['0.9.15'],map_name='LuoboTurn024388',xodr_file='LuoboTurn024388.xodr',xodr_sha256=hashlib.sha256((P/'LuoboTurn024388.xodr').read_bytes()).hexdigest(),source_video_start_s=0,source_video_end_s=END,duration_s=END,fps=FPS,coordinates='Right-handed metres; h radians; XY bbox ground centre. CARLA X=x Y=-y yaw=-degrees(h).',reconstruction_method='Four-view manual identity/time anchors, static optical-flow stop corroboration, PCHIP metric path interpolation on existing estimated map. No calibrated multi-camera triangulation.',limitations=['Metric positions, hidden continuations and dimensions estimated.','Stock vehicle and walker appearance differs from video.','Distant ambiguous riders are not exhaustively reconstructed.','Kinematic playback; not a collision/dynamics-valid driving policy.','CARLA 0.9.15 engine unavailable during generation.'],events=[dict(start_t=a,end_t=b,video_start=a,video_end=b,id=i,label_zh=l) for a,b,i,l in events],actors=actors)
(P/'scenario.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'evidence/event_anchors.json').write_text(json.dumps(dict({k:v for k,v in d.items() if k!='actors'},actors=[{k:v for k,v in a.items() if k!='samples'} for a in actors]),ensure_ascii=False,indent=2),encoding='utf-8')
with (P/'trajectories.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['actor_id','time_s','video_time_s','x_rh_m','y_rh_m','z_ground_m','h_rh_rad','carla_x','carla_y','carla_yaw_deg'])
 for a in actors:
  for s in a['samples']:w.writerow([a['id'],s['t'],s['video_t'],s['x'],s['y'],s['z'],s['h'],s['x'],-s['y'],-math.degrees(s['h'])])
print('Generated',len(actors),'actors;',sum(len(a['samples']) for a in actors),'poses')
