"""Four-camera event anchors, map-constrained manual metric estimates and PCHIP fitting.
No calibrated detection/tracking or survey accuracy is claimed.
"""
import json,math,csv,hashlib
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
P=Path(__file__).resolve().parents[1];FPS=30;END=120.;actors=[]
# Ego motion windows follow source front/right fixed landmarks. Flow is diagnostic only:
# repeated video frames make median flow collapse to zero; no metric scale is claimed.
ego_keys=[[0,0,-7.15],[78,0,-7.15],[81,1,-7.15],[83,7,-7.45],[85,21,-8.30],[88,48,-8.75],[90,60,-8.75],[91.5,63,-8.75],[98,63,-8.75],[100,66,-8.75],[102,72,-8.75],[104,78,-8.75],[105.5,80,-8.75],[120,80,-8.75]]
def add(aid,kind,label,keys,dims,bp,color=None,notes='',custom=None,heading=None,confidence='medium'):
 ar=np.array(keys,float);fx=PchipInterpolator(ar[:,0],ar[:,1]);fy=PchipInterpolator(ar[:,0],ar[:,2]);fz=None
 ts=np.linspace(ar[0,0],ar[-1,0],round((ar[-1,0]-ar[0,0])*FPS)+1);samples=[];prev=0
 for t in ts:
  vx=float(fx.derivative()(t));vy=float(fy.derivative()(t))
  h=math.atan2(vy,vx) if math.hypot(vx,vy)>.06 else prev
  if heading is not None:h=math.radians(heading)
  prev=h;x=float(fx(t));y=float(fy(t));z=.18 if kind in ['pedestrian','parked'] and abs(y)>10.7 else 0
  samples.append({'t':round(float(t),6),'video_t':round(float(t),6),'s':round(x+150,6),'lateral':round(y,6),'x':round(x,6),'y':round(y,6),'z':z,'h':round(h,8)})
 actors.append({'id':aid,'category':kind,'label_zh':label,'dimensions_m':dict(zip(['length','width','height'],dims)),'blueprint_candidates':bp,'preferred_custom_blueprint':custom,'color':color,'start_t':float(ts[0]),'end_t':float(ts[-1]),'source_keyframes':keys,'confidence':confidence+'; metric positions estimated','notes':notes,'samples':samples})
car=['vehicle.lincoln.mkz_2020'];suv=['vehicle.audi.etron'];van=['vehicle.mercedes.sprinter'];truck=['vehicle.carlamotors.carlacola'];bike=['vehicle.vespa.zx125'];bus=['vehicle.volkswagen.t2'];sedan=['vehicle.tesla.model3']
add('ego','car','美团自车',ego_keys,(3.6,1.65,1.8),['vehicle.nissan.micra'],'237,221,62',notes='Own body unseen completely; stock Micra is a functional substitute, not original delivery body. Lateral movement around 81-88s follows front lane line and right parking landmarks.',custom='static.prop.meituan_delivery_ego',confidence='medium')
add('gray_departing_sedan','car','开头右前灰色轿车',[[0,7,-8.9],[2,15,-8.9],[5,36,-8.8],[10,65,-8.75],[18,93,-8.75],[23,119,-8.75]],(4.8,1.9,1.5),sedan,'110,114,119',notes='Front 0-8; leaves the near right front. Distant continuation inferred.')
add('dark_front_suv','car','左前深灰SUV',[[0,7.5,-4.95],[12,10,-4.95],[16,11,-4.95],[44,11,-4.95],[48,23,-5.1],[52,39,-5.35],[68,42,-5.35],[79,52,-5.35],[86,89,-5.35],[92,121,-5.35]],(4.8,1.95,1.7),suv,'46,44,52',notes='Front 0-48 nearest left-front SUV, then departs; later occluded by green van.')
add('inner_black_mpv','car','内侧黑色MPV',[[0,9,-1.95],[15,13,-1.95],[46,13,-1.95],[51,27,-1.95],[79,29,-1.95],[84,47,-1.95],[89,79,-1.95],[97,120,-1.95]],(5,1.95,1.8),['vehicle.mercedes.coupe_2020'],'28,32,34',notes='Front-left inner lane, slowly queues then advances.')
add('green_delivery_van','van','左侧绿色货运面包车',[[0,-5,-4.95],[4,.2,-4.95],[45,.2,-4.95],[49,7,-5.05],[54,16,-5.35],[75,16,-5.35],[79,24,-5.35],[84,52,-5.35],[90,92,-5.35],[95,121,-5.35]],(5.6,2.0,2.6),van,'26,139,100',notes='Strong front/left/rear association; beside ego until ~46s, then front-left until traffic restarts.',custom='static.prop.meituan_green_van',confidence='high identity')
add('silver_minivan','van','接替绿色车位置的银色面包车',[[0,-19,-4.95],[45,-19,-4.95],[51,-10,-4.95],[56,.3,-4.95],[80,.3,-4.95],[83,12,-5.35],[88,49,-5.35],[93,91,-5.35],[98,121,-5.35]],(4.8,1.85,1.9),['vehicle.volkswagen.t2_2021'],'176,182,178',notes='Left 56-84 clearly shows silver minivan at ego side; reference timestamps offset about 3-4 s.')
add('red_tanker','truck','从右侧驶过的红头罐车',[[0,-56,-9.7],[8,-23,-9.7],[12,-3,-9.7],[16,18,-9.55],[20,43,-9.2],[28,71,-8.75],[44,91,-8.75],[62,121,-8.75]],(12.5,2.5,3.5),truck,'164,38,44',notes='Rear approach then right 12-18 and front 12-22. Native truck substitute differs from tanker.',custom='static.prop.meituan_tanker',confidence='high identity')
add('right_dark_sedan_1','car','右侧通过的第一辆深色轿车',[[12,-48,-9.8],[20,-17,-9.8],[24,2,-9.7],[28,24,-9.3],[34,53,-8.75],[46,78,-8.75],[66,105,-8.75]],(4.8,1.9,1.5),car,'58,64,65',notes='Front/rear/right 22-28; linked using vehicle color and passing order.')
add('right_dark_sedan_2','car','随后通过的黑色轿车',[[18,-43,-9.8],[24,-17,-9.8],[28,3,-9.7],[32,24,-9.3],[37,43,-8.75],[54,68,-8.75],[72,97,-8.75],[84,120,-8.75]],(4.8,1.9,1.5),car,'25,30,31',notes='Separate car after first dark sedan; brief occlusions create identity uncertainty.',confidence='medium-low identity')
add('white_box_truck','truck','右侧白色厢式货车',[[30,-57,-9.7],[40,-29,-9.7],[46,-9,-9.7],[50,10,-9.6],[56,25,-8.75],[76,25,-8.75],[80,34,-8.75],[86,71,-8.75],[92,103,-8.75],[96,120,-8.75]],(6.4,2.2,3.1),truck,'227,227,216',notes='Rear approach 38-46; right side 46-52; remains in front during 56-80. Distinct from parked cab-over truck.',custom='static.prop.meituan_boxtruck',confidence='high identity')
add('front_brown_truck','truck','前方排队的棕色货车',[[0,28,-5.35],[16,39,-5.35],[44,39,-5.35],[52,55,-5.35],[78,62,-5.35],[85,95,-5.35],[90,120,-5.35]],(8.4,2.4,3.2),truck,'118,74,60',notes='Repeated front view queue anchor; distant pose lower confidence.')
add('inner_red_truck','truck','内侧红色货车',[[0,-7,-1.95],[18,-3,-1.95],[47,-3,-1.95],[54,10,-1.95],[80,12,-1.95],[85,31,-1.95],[90,62,-1.95],[100,111,-1.95],[103,120,-1.95]],(8.5,2.45,3.0),truck,'152,39,40',notes='Left camera shows red cab toward +X behind black MPV. Same-direction interpretation, not opposing traffic.')
add('white_sedan_middle','car','后方白色新能源轿车',[[42,-45,-5.35],[55,-18,-5.35],[77,-12,-5.35],[82,0,-5.35],[87,35,-5.35],[91,66,-5.35],[97,102,-5.35],[101,120,-5.35]],(4.7,1.85,1.5),sedan,'233,236,230',notes='Rear 60-84 approach, front 88 white sedan; front/rear identity match estimated.')
add('small_white_van','van','内侧白色小货车',[[48,-30,-1.95],[70,-19,-1.95],[82,-9,-1.95],[89,33,-1.95],[98,83,-1.95],[105,119,-1.95]],(4.7,1.9,2.5),van,'225,226,218',notes='Rear and left background, partly occluded by near-side minivan.',confidence='low depth')
add('red_inner_sedan','car','后段内侧红色轿车',[[80,120,5.35],[86,83,5.35],[90,59,5.35],[95,24,5.35],[102,-27,5.35]],(4.6,1.85,1.5),['vehicle.audi.a2'],'177,29,43',notes='Red car in left background; opposing-lane association is uncertain.')
add('bus_teal','bus','第一辆青绿色公交车',[[84,-25,-5.35],[90,26,-5.35],[94,57,-5.35],[98,88,-5.35],[102,108,-5.35],[105,118,-5.35]],(11.4,2.5,3.2),bus,'39,154,149',notes='Rear/left/front ~94-101 first city bus. Stock VW bus fallback is smaller; custom prop provides the city-bus silhouette.',custom='static.prop.meituan_citybus')
add('bus_yellow_ad','bus','末段黑黄广告公交车',[[90,-28,-5.35],[96,23,-5.35],[100,61,-5.35],[103,80,-5.35],[106,88,-5.35],[120,88,-5.35]],(11.4,2.5,3.2),bus,'207,171,31',notes='Second bus occupies left side from ~103s until clip end; paired with mirrored rear and left close-up.',custom='static.prop.meituan_adbus',confidence='high identity')
add('late_white_suv','car','末段后方白色SUV',[[92,-29,-5.35],[100,18,-5.35],[108,49,-5.35],[115,68,-5.35],[120,77,-5.35]],(4.6,1.85,1.6),suv,'231,232,223',notes='Rear 108-118 close approach. Remains behind the advertising bus.')
add('late_black_sedan','car','末段后方黑色轿车',[[94,-38,-8.75],[103,12,-8.75],[112,46,-8.75],[120,64,-8.75]],(4.8,1.9,1.5),car,'29,33,35',notes='Rear/right final approach, behind ego.')
add('late_flatbed','truck','末段内侧平板货车',[[96,-48,-1.95],[104,17,-1.95],[111,72,-1.95],[118,120,-1.95]],(10.4,2.5,2.8),truck,'146,61,43',notes='Brief rear/left view of long red/brown bed after 108s; appearance approximated.',confidence='low identity')
# Individually observed near-side two-wheelers; no unobserved stochastic traffic.
for aid,label,begin,passing,end,color in [
 ('scooter_white_helmet','白盔骑行者',12,20,33,'99,131,162'),
 ('scooter_yellow_1','黄色骑手',24,32,47,'235,196,21'),
 ('scooter_pink','粉衣骑行者',67,75,87,'213,160,169'),
 ('scooter_gray','灰衣骑行者',74,82,94,'119,124,117'),
 ('scooter_hivis','荧光黄骑行者',93,99,110,'207,234,40'),
 ('scooter_dark_late','末段深色骑行者',105,111,120,'43,47,55')]:
 ef=PchipInterpolator(np.array(ego_keys)[:,0],np.array(ego_keys)[:,1]);xc=float(ef(passing))
 by=-10.42 if aid=='scooter_white_helmet' else -10.05
 add(aid,'motorcycle',label,[[begin,max(-140,xc-36),by],[passing,xc+2,by],[min(passing+3,end),min(118,xc+18),by],[end,min(120,xc+44),by]],(2.0,.68,1.7),bike,color,notes='Observed right-edge pass. Stock scooter rider clothing cannot be forced to exact source colors; lateral clearance adjusted within uncertain image depth.')
add('pedestrian_purple','pedestrian','末段走向自车的紫衣行人',[[108,98,-10.0],[112,93,-9.1],[116,88,-8.85],[120,83,-8.75]],(.5,.5,1.75),['walker.pedestrian.0004'],notes='Front 112-120 approaching ego on outer-lane side; most visible 118-120.',confidence='high event')
add('pedestrian_white','pedestrian','右侧人行道白衣行人',[[99,82,-13.7],[105,82,-13.7],[111,87,-13.7],[117,92,-13.7],[120,92,-13.7]],(.5,.5,1.72),['walker.pedestrian.0001'],notes='Front/right 104-118; identity across tree occlusion inferred.')
# Stationary observed targets provide occlusion context and remain separate from FBX.
for i,(x,kind,dim,bps,col) in enumerate([(14,'parked_vehicle',(6.1,2.15,2.8),truck,'213,219,204'),(23,'parked_vehicle',(4.7,1.85,1.5),car,'104,113,118'),(32,'parked_vehicle',(4.8,1.9,1.5),sedan,'58,65,68'),(44,'parked_vehicle',(4.7,1.85,1.5),car,'190,192,184'),(56,'parked_vehicle',(4.9,1.9,1.7),suv,'40,46,46')]):
 add('parked_%02d'%i,kind,'右侧停放车辆%02d'%(i+1),[[0,x,-14.0],[120,x,-14.0]],dim,bps,col,heading=129,notes='Stationary parking reference, not a moving track. Slot mapping is estimated.')
add('parked_scooter','parked','右侧牌杆旁停放电动车',[[0,87.5,-12.7],[120,87.5,-12.7]],(1.8,.65,1.4),bike,'35,47,42',heading=15,notes='Visible in final front/right view.')
events=[(0,45,'queue','自车停留，绿色货运车在左侧等待'),(10,22,'tanker_pass','罐车从右侧经过'),(23,34,'sedans_pass','两辆深色轿车先后从右侧经过'),(46,56,'boxtruck_pass','白色厢式货车右侧通过，绿色车驶向前方'),(55,80,'queue_2','银色面包车位于左侧，自车继续等待'),(81,91.5,'ego_lane_change','自车启动，向右移入外侧车道'),(93,102,'first_bus','第一辆公交车从左侧通过'),(100,106,'ego_creep','自车再次向前缓行'),(102,120,'advert_bus','黑黄广告公交车经过后停留在左前方'),(112,120,'pedestrian','紫衣行人朝自车方向走来')]
d={'format_version':1,'scene':'MeituanLane0512189_DynamicReplay','target_carla_versions':['0.9.15'],'map_name':'MeituanLane0512189','xodr_file':'MeituanLane0512189.xodr','xodr_sha256':hashlib.sha256((P/'MeituanLane0512189.xodr').read_bytes()).hexdigest(),'source_video_start_s':0,'source_video_end_s':120,'duration_s':120,'fps':FPS,'coordinates':'RH metres; X forward, Y left; h radians; bbox ground center. CARLA=(x,-y,z), yaw=-degrees(h).','reconstruction_method':'Four-camera manual identity/event anchors, stationary-landmark ego timing, PCHIP spatial interpolation. Static-flow diagnostic rejected as metric input because repeated frames collapse median flow. No calibrated 3D tracking.','limitations':['Metric depth, width, speed and occluded continuation estimated; no calibration.','Rear view has mirrored scene content; compare after horizontal flip. Camera clock differences vary about 1-4s.','Native CARLA fallbacks differ notably for tanker, city buses and delivery ego. Optional custom props support kinematic appearance only.','Template driver route/speed playback is not exact timestamp positioning; use replay_carla.py for timestamp replay.','Only observed near traffic and identifiable parked context modeled; distant occluded traffic not exhaustively recovered.'],'events':[{'id':i,'video_start':a,'video_end':b,'start_t':a,'end_t':b,'label_zh':l} for a,b,i,l in events],'actors':actors}
(P/'scenario.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'evidence/event_anchors.json').write_text(json.dumps({'events':d['events'],'actors':[{k:v for k,v in a.items() if k!='samples'} for a in actors]},ensure_ascii=False,indent=2),encoding='utf-8')
with (P/'trajectories.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['actor_id','replay_time_s','source_front_video_time_s','x_rh_m','y_rh_m','z_ground_m','heading_rh_rad','x_carla_m','y_carla_m','yaw_carla_deg'])
 for a in actors:
  for s in a['samples']:w.writerow([a['id'],s['t'],s['video_t'],s['x'],s['y'],s['z'],s['h'],s['x'],-s['y'],-math.degrees(s['h'])])
print('Generated',len(actors),'actors;',sum(len(a['samples']) for a in actors),'poses')
