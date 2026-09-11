"""Four-camera visual anchors, shared XODR geometry, bounded optical-flow timing."""
import csv,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d
P=Path(__file__).resolve().parents[1]; STATIC=P.parent/'environment_reconstruction_016955'
sys.path.insert(0,str(STATIC/'scripts'))
from road_layout import ROADS,maneuvers
FPS=30;END=180.;actors=[]
segments=[dict(x=-170.05,y=-200,h=math.pi/2,length=180,k=0)]
conns={r['id']:r for r in maneuvers()}
segments+=conns[103]['segments']
S20=sum(r['length'] for r in segments)
segments.append(dict(x=-160,y=-1.75,h=0,length=140,k=0))
S201=S20+140
segments+=conns[201]['segments'];S30=sum(r['length'] for r in segments)
segments.append(dict(x=-1.75,y=-20,h=-math.pi/2,length=180,k=0))
def route(s,off=0):
 rem=s
 for g in segments:
  if rem<=g['length']+1e-8:break
  rem-=g['length']
 rem=max(0,min(rem,g['length']));x,y,h,k=g['x'],g['y'],g['h'],g['k']
 if k:x+=(math.sin(h+k*rem)-math.sin(h))/k;y-=(math.cos(h+k*rem)-math.cos(h))/k;h+=k*rem
 else:x+=rem*math.cos(h);y+=rem*math.sin(h)
 return x-off*math.sin(h),y+off*math.cos(h),h
# The near-side sweeper pause occurs before the second right turn is fully completed.
stop=S201+9.5+8.75*math.radians(80)
anchors=[[0,52],[41.3,52],[44,53.8],[48,66],[51,81],[54,99],[58,125],[62,151],[66,171],[69,181],[72,190],[75,S20-2],[78,S20+9],[84,S20+29],[90,S20+58],[96,S20+88],[102,S20+115],[108,S20+138],[111,S201+11],[114,stop-3.8],[117,stop],[132,stop],[135,stop+.12],[137,stop+.12],[139,stop+.36],[141,stop+.36],[147,S30+1],[150,S30+6],[154,S30+8],[158,S30+22],[162,S30+40],[166,S30+60],[170,S30+78],[174,S30+94],[176,S30+97],[180,S30+97]]
flow=json.loads((P/'evidence/ego_static_flow.json').read_text(encoding='utf-8'))
ft=np.array([r['video_time'] for r in flow['right']]);fv=np.array([r['speed_proxy'] for r in flow['right']]);fv=gaussian_filter1d(fv,2)
base=PchipInterpolator(*np.array(anchors).T);refined=[]
for (ta,sa),(tb,sb) in zip(anchors,anchors[1:]):
 ts=np.linspace(ta,tb,max(3,round((tb-ta)*2)+1));vals=base(ts)
 if sb>sa and tb-ta>2 and ta>=41.3:
  v=np.interp(ts,ft,fv);v=np.clip(v/max(np.median(v),.01),.5,1.5);cum=np.r_[0,np.cumsum((v[1:]+v[:-1])/2*np.diff(ts))];f=sa+(sb-sa)*cum/max(cum[-1],1e-8)
  vals=.85*vals+.15*f
 refined.extend(zip(ts[:-1],vals[:-1]))
refined.append(anchors[-1]);progress=PchipInterpolator(*np.array(refined).T)
lateral=PchipInterpolator([0,42,46,49,55,59,64,68,72,180],[0,0,1.6,3.5,3.5,3.0,1.0,0,0,0])
corner_clearance=PchipInterpolator([0,108,114,117,141,147,154,180],[0,0,.5,1.2,1.2,.2,0,0])
def add(aid,label,cat,keys,dims,bps,color=None,custom=None,mode='world',note='',confidence='medium'):
 aa=np.array(keys,float);fs=[PchipInterpolator(aa[:,0],aa[:,i]) for i in range(1,aa.shape[1])];samples=[]
 ts=np.linspace(aa[0,0],aa[-1,0],round((aa[-1,0]-aa[0,0])*FPS)+1)
 for t in ts:
  if mode=='ego':s=float(progress(t));off=float(lateral(t));x,y,h=route(s,off);x+=float(corner_clearance(t))
  else:
   x,y,hd=[float(f(t)) for f in fs];h=math.radians(hd);s=0;off=0
  ground=.17 if cat=='pedestrian' else .17*max(0,min(1,(x-3.3))) if cat=='sweeper' else .17*max(0,min(1,(abs(y)-3.5))) if cat=='motorcycle' else 0.
  samples.append(dict(t=round(t,6),video_t=round(t,6),x=round(x,6),y=round(y,6),z=round(ground,6),h=round(h,8),s=round(s,6),lateral=round(off,6)))
 # Align vehicle headings with their path during movement, keeping stable headings at stops.
 if mode=='ego':
  xy=np.array([[s['x'],s['y']] for s in samples]);vv=np.gradient(xy,axis=0);hh=np.unwrap(np.arctan2(vv[:,1],vv[:,0]));moving=np.linalg.norm(vv,axis=1)>.002
  for i,s in enumerate(samples):
   if moving[i]:s['h']=round(float(hh[i]),8)
 actor=dict(id=aid,label_zh=label,category=cat,dimensions_m=dict(zip(['length','width','height'],dims)),blueprint_candidates=bps,preferred_custom_blueprint=custom,color=color,start_t=float(aa[0,0]),end_t=float(aa[-1,0]),source_keyframes=keys,confidence=confidence,notes=note,samples=samples)
 actors.append(actor);return actor
car=['vehicle.lincoln.mkz_2020','vehicle.tesla.model3'];suv=['vehicle.nissan.patrol_2021','vehicle.audi.etron'];truck=['vehicle.carlamotors.carlacola'];scooter=['vehicle.vespa.zx125'];van=['vehicle.mercedes.sprinter']
add('ego','自车','car',anchors,(4.7,1.9,1.65),car,'238,239,231',mode='ego',note='Four-view stops and two right turns; static-scene metric anchors, bounded right-side optical-flow timing; overtakes coach to its left at 48-55 s.',confidence='high timing / estimated metric')
add('coach','红黄大客车','bus',[[0,-169.7,-119,90],[58,-169.7,-119,90],[63,-169.8,-105,90],[69,-170.05,-61,90],[75,-170.05,-7,90],[78,-170.05,20,90],[88,-170.05,110,90]],(11.8,2.5,3.65),truck,'183,31,42','static.prop.greenrail_coach',note='Stationary curbside coach overtaken; rear camera 69-78 s confirms it later continues north. Stock CARLA fallback truck does not match bus body.')
# Resolve the clearly visible initial passing traffic by pass time and type; distant identities are tentative.
traffic=[(2.8,'白色SUV',suv,'224,225,220',-173.55,'car'),(4.4,'深色SUV',suv,'38,42,46',-177.05,'car'),(6.8,'银色轿车',car,'155,161,159',-173.55,'car'),(8.8,'深色轿车',car,'33,35,39',-177.05,'car'),(11.5,'白色SUV',suv,'228,229,224',-173.55,'car'),(15.5,'灰色轿车',car,'116,125,127',-173.55,'car'),(18.4,'白色面包车',van,'222,223,212',-177.05,'van'),(20.5,'灰色SUV',suv,'88,94,99',-173.55,'car'),(23.3,'黑色SUV',suv,'24,28,32',-177.05,'car'),(26.6,'白色厢式货车',truck,'218,223,219',-173.55,'truck'),(29.2,'蓝色厢式货车',truck,'34,65,137',-177.05,'truck'),(35.0,'白色SUV',suv,'225,225,216',-173.55,'car'),(39.3,'白色厢式货车',truck,'220,223,215',-177.05,'truck'),(43.0,'白色小型货车',van,'225,224,218',-173.55,'van')]
for i,(pt,label,bps,col,x,kind) in enumerate(traffic):
 if i==13:x=-177.05  # Inner-lane van remains separate from the white car seen ahead at 51 s.
 speed=6. if i==13 else 7.2 if kind=='truck' else 8.;a=max(0,pt-52/speed);b=min(80,pt+252/speed)
 keys=[[round(a,3),x,-148+(a-pt)*speed,90],[pt,x,-148,90],[round(b,3),x,-148+(b-pt)*speed,90]]
 if keys[0][0]==pt:keys.pop(0)
 add('traffic_%02d'%(i+1),label+' %.1fs'%pt,kind,keys,(7.2,2.45,3.35) if kind=='truck' else (5.9,2.05,2.6) if kind=='van' else (4.6,1.85,1.65),bps,col,custom='static.prop.greenrail_boxtruck' if kind=='truck' else None,note='Pass-time anchor from front/left/rear; unobserved entry and departure extrapolated along boulevard.',confidence='medium timing / low identity linkage')
add('lead_white_car','前方白车','car',[[46,-173.55,-99,90],[54,-173.55,-70,90],[62,-173.55,-28,90],[70,-173.55,24,90],[80,-173.55,104,90]],(4.65,1.85,1.5),car,'225,226,222',note='Front 48-63 s. Continues along boulevard; no evidence of following ego into branch.')
add('lead_yellow','路口黄色小车','car',[[57,-173.55,-65,90],[66,-173.55,-11,90],[75,-173.55,52,90],[82,-173.55,108,90]],(4.1,1.75,1.55),['vehicle.seat.leon','vehicle.audi.a2'],'211,179,48',note='Yellow car visible approaching first junction; distant identity uncertain.')
add('cross_scooter_a','首个路口电动车 A','motorcycle',[[63,-160,-20,90],[69,-160,-6,90],[72,-160,2,90],[76,-160,12,90],[82,-160,27,90]],(1.95,.7,1.6),scooter,'58,68,73',note='Two-wheelers cross the branch mouth ahead of first right turn. Sidewalk continuation inferred.')
add('cross_scooter_b','首个路口电动车 B','motorcycle',[[65,-157.8,16,-90],[69,-157.8,5,-90],[72,-157.8,-4,-90],[77,-157.8,-19,-90]],(1.95,.7,1.6),scooter,'97,110,116',note='Second crossing rider around 69-72 s; direction/metric depth less certain.',confidence='low to medium')
add('container_truck','厂区红色集装箱车','truck',[[78,-60,11.8,180],[112,-60,11.8,180]],(15.2,2.5,4.0),truck,'165,35,31','static.prop.greenrail_container',note='Front/left 90-102 s places container inside north compound driveway. No reliable motion relative to building; held stationary.',confidence='medium placement / uncertain motion')
add('oncoming_boxtruck','沿轨道对向白色厢货','truck',[[87,17,1.75,180],[94,-9,1.75,180],[100,-30,1.75,180],[102,-39,1.75,180],[108,-69,1.75,180],[120,-132,1.75,180],[125,-157,1.75,180]],(7.2,2.45,3.35),truck,'220,226,222','static.prop.greenrail_boxtruck',note='Front/left/rear agree on pass at 102-103 s; westbound on road 20 lane +1.',confidence='high timing / estimated metric')
add('oncoming_dark_suv','沿轨道对向黑色SUV','car',[[94,26,1.75,180],[100,-2,1.75,180],[105,-24,1.75,180],[108,-39,1.75,180],[120,-100,1.75,180],[131,-156,1.75,180]],(4.7,1.88,1.7),suv,'29,33,37',note='Follows white box truck; left 108 s confirms dark SUV moving west.',confidence='high timing / estimated metric')
add('sweeper','彩色无人清扫机器人','sweeper',[[106,-2.8,-9.4,-90],[137,-2.8,-9.4,-90],[145,-2.8,-12,-90],[148,-2.55,-14.5,-55],[150,-1.85,-15.2,-15],[153,.05,-15.2,0],[156,2.05,-15.2,0],[160,4.65,-15.2,0],[164,5.6,-15.2,0],[168,5.8,-15.2,0],[180,5.8,-15.2,0]],(1.65,1.18,1.85),['vehicle.micro.microlino','vehicle.bh.crossbike'],'40,178,170','static.prop.greenrail_sweeper',note='Right view establishes long near-side hold. Rear 150-165 s shows crossing from west to east behind ego. Crossing aligned to existing zebra; metric corner clearance adjusted to existing curb. Detailed brush/body visual prop supplied; stock fallback is approximate.',confidence='high relative timing / estimated metric')
add('exit_white_van','出口对向白色小货车','van',[[157,1.75,-139,90],[163,1.75,-110,90],[166,1.75,-94,90],[169,1.75,-77,90],[174,1.75,-51,90],[180,1.75,-22,90]],(5.2,1.85,2.3),van,'222,225,217',note='Front 165-168 s then rear 171-180 s; inferred to be same white light commercial vehicle.')
add('exit_sedan_a','末段对向浅色轿车','car',[[170,1.75,-192,90],[175,1.75,-167,90],[180,1.75,-137,90]],(4.6,1.85,1.5),car,'172,184,183',note='Approaches in final front frames; does not pass before clip ends.')
add('exit_sedan_b','末段远处白车','car',[[174,1.75,-198,90],[180,1.75,-165,90]],(4.6,1.85,1.5),car,'222,225,217',note='Distant second oncoming car in final front frames.',confidence='low')
add('ped_exit_a','出口左侧行人 A','pedestrian',[[145,5.0,-41,90],[153,5,-41,90],[160,5,-39.5,90],[170,5,-36,90],[180,5,-32,90]],(.5,.5,1.72),['walker.pedestrian.0001'],note='Two people visible front-left 150-159 and rear-right 168-180; small walking displacement estimated.')
add('ped_exit_b','出口左侧行人 B','pedestrian',[[145,5.8,-42,90],[156,5.8,-42,90],[170,5.8,-39,90],[180,5.8,-36,90]],(.5,.5,1.7),['walker.pedestrian.0004'],note='Clothing and gait not recoverable at source resolution.')
events=[(0,41.3,'wait_bus','自车在客车后方等待'),(48,55,'pass_bus','自车从左侧超越客车'),(69,78,'turn_1','第一次右转；两轮车经过路口'),(69,78,'bus_moves','后视确认客车继续直行'),(101,104,'box_pass','白色厢货对向通过'),(105,108,'suv_pass','黑色SUV对向通过'),(110,117,'turn_2','第二次右转；靠近清扫机器人'),(117,142,'wait_robot','机器人旁等待，期间小幅挪动'),(148,168,'robot_cross','清扫机器人在自车后方横过路口'),(168,170,'van_pass','出口道路白色小货车会车'),(176,180,'final_stop','自车末段停车')]
data=dict(format_version=1,scene='GreenRail016955_DynamicReplay',target_carla_versions=['0.9.15'],map_name='GreenRail016955',xodr_file='GreenRail016955.xodr',xodr_sha256=hashlib.sha256((P/'GreenRail016955.xodr').read_bytes()).hexdigest(),source_video_start_s=0,source_video_end_s=180,duration_s=END,fps=FPS,coordinates='Right-handed metres, Z up; heading radians; intended bounding-box ground centre. CARLA x=x, y=-y, yaw=-degrees(h).',reconstruction_method='Four-view manually reviewed motion and identity anchors; static XODR route; bounded masked optical-flow correction to ego timing; PCHIP interpolation. Not calibrated multi-camera 3D tracking.',limitations=['Metric scale, object dimensions, camera intrinsics/extrinsics and occluded motions are estimates.','Video frame times aligned at 15 fps; left video offset +1/15 s from overlay timestamps.','Distant actor identities uncertain; not every pixel-sized background target is tracked.','Stock CARLA appearance differs, especially coach/container/sweeper; optional custom props supplied.','Kinematic replay: no physical collision response or automated-driver validation.'],events=[dict(id=i,start_t=a,end_t=b,video_start=a,video_end=b,label_zh=l) for a,b,i,l in events],actors=actors)
(P/'scenario.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
with (P/'trajectories.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['actor_id','time_s','source_video_s','x_rh_m','y_rh_m','z_ground_m','h_rh_rad','x_carla_m','y_carla_m','yaw_carla_deg'])
 for a in actors:
  for s in a['samples']:w.writerow([a['id'],s['t'],s['video_t'],s['x'],s['y'],s['z'],s['h'],s['x'],-s['y'],-math.degrees(s['h'])])
(P/'evidence/event_anchors.json').write_text(json.dumps({'ego_route':['10/-4','103/-1','20/-1','201/-1','30/+1'],'route_station_boundaries':[S20,S201,S30],'events':data['events'],'actors':[{k:v for k,v in a.items() if k!='samples'} for a in actors]},ensure_ascii=False,indent=2),encoding='utf-8')
print('Generated',len(actors),'actors;',sum(len(a['samples']) for a in actors),'poses; stations',S20,S201,S30)
