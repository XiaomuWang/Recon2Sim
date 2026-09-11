"""Four-camera manually associated tracks, static-flow ego timing, estimated metric anchors."""
import json,math,sys,csv,hashlib,shutil
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import median_filter,gaussian_filter1d
P=Path(__file__).resolve().parents[1];STATIC=P.parent/'environment_reconstruction_019742'
START=0.;END=178.;FPS=30
flow=json.loads((P/'evidence/ego_static_flow.json').read_text());ft=np.array([r['video_time'] for r in flow]);fv=median_filter(np.array([r['speed_proxy'] for r in flow]),5)
# Anchors align visible crosswalks/accesses to the already-delivered estimated map.
EK=[[0,-391],[8,-355],[12,-338],[24,-294],[36,-246],[40,-237],[42,-236.2],[48,-218],[60,-164],[64,-146.8],[67.5,-143.5],[78.3,-143.5],[84,-130],[90,-118],[96,-97],[100,-77],[104,-57],[108,-38],[109,-33],[110,-28],[110.5,-25.8],[111,-24.2],[112,-23.4],[120,-23.4],[123,-15.4],[126,-8.4],[129,-6.4],[135,-1.2],[143,0],[154,0],[160,1.8],[178,1.8]]
base=PchipInterpolator(np.array(EK)[:,0],np.array(EK)[:,1]);times=np.arange(0,END+1/FPS/2,1/FPS);ego_x=np.array(base(times))
# Optical flow redistributes progression only in clearly moving intervals; local critical braking remains anchor constrained.
for a,b in [(0,8),(8,12),(12,24),(24,36),(42,48),(48,60),(78.3,84),(90,96),(96,100),(100,104),(104,108),(120,123),(123,126)]:
 ix=np.where((times>=a)&(times<=b))[0];tt=times[ix];v=np.interp(tt,ft,fv);v=gaussian_filter1d(np.maximum(v,.5),FPS*.25)
 integ=np.r_[0,np.cumsum((v[:-1]+v[1:])/2*np.diff(tt))];xx=float(base(a))+(float(base(b))-float(base(a)))*integ/integ[-1]
 # Blend to preserve estimated smooth speed at landmarks.
 ego_x[ix]=.75*ego_x[ix]+.25*xx
ego_func=PchipInterpolator(times,ego_x)
EY=[[0,-1.65],[90,-1.65],[96,-1.85],[100,-2.9],[105,-4.75],[109,-4.85],[110.6,-4.35],[112,-4.4],[120,-4.4],[124,-4.8],[130,-4.95],[178,-4.95]]
ego_lat=PchipInterpolator(np.array(EY)[:,0],np.array(EY)[:,1])
actors=[]
BP={'car':['vehicle.lincoln.mkz_2020','vehicle.tesla.model3'],'sedan':['vehicle.tesla.model3','vehicle.lincoln.mkz_2020'],'suv':['vehicle.audi.etron','vehicle.nissan.patrol_2021'],'van':['vehicle.volkswagen.t2_2021','vehicle.mercedes.sprinter'],'boxtruck':['vehicle.mercedes.sprinter','vehicle.carlamotors.carlacola'],'truck':['vehicle.carlamotors.carlacola'],'scooter':['vehicle.vespa.zx125','vehicle.yamaha.yzf'],'micro':['vehicle.bmw.isetta','vehicle.citroen.c3'],'bicycle':['vehicle.diamondback.century','vehicle.gazelle.omafiets']}
DIMS={'car':(4.8,1.9,1.6),'sedan':(4.65,1.85,1.5),'suv':(4.8,1.9,1.7),'van':(4.5,1.75,1.95),'boxtruck':(5.7,1.9,2.65),'truck':(8,2.45,3.1),'scooter':(1.8,.65,1.6),'micro':(2.55,1.4,1.8),'bicycle':(1.8,.6,1.65)}
def actor(name,kind,label,keys,color=None,note='',confidence='medium',ego=False):
 a=np.array(keys,float);fs=[PchipInterpolator(a[:,0],a[:,i]) for i in range(1,4)];ss=[]
 for t in np.linspace(a[0,0],a[-1,0],round((a[-1,0]-a[0,0])*FPS)+1):
  if ego:
   x=float(ego_func(t));y=float(ego_lat(t));dx=float(ego_func.derivative()(t));dy=float(ego_lat.derivative()(t));h=math.atan2(dy,dx) if math.hypot(dx,dy)>.05 else 0
  else:x,y,deg=[float(f(t)) for f in fs];h=math.radians(deg)
  ss.append({'t':round(float(t),6),'video_t':round(float(t),6),'s':round(x,5),'lateral':round(y,5),'x':round(x,5),'y':round(y,5),'z':0.,'h':round(h,8)})
 ar={'id':name,'label_zh':label,'category':'parked' if name.startswith('parked_') else 'motorcycle' if kind=='scooter' else 'bicycle' if kind=='bicycle' else 'truck' if kind in ['truck','boxtruck'] else 'car','visual_type':kind,'dimensions_m':dict(zip(['length','width','height'],DIMS[kind])),'blueprint_candidates':BP[kind],'preferred_custom_blueprint':None,'color':color,'start_t':float(a[0,0]),'end_t':float(a[-1,0]),'source_keyframes':keys,'confidence':confidence+'; identity/time qualitative, metric depth estimated','notes':note,'samples':ss}
 actors.append(ar)
def relkeys(rows):
 return [[t,round(float(ego_func(t))+dx,3),y,h] for t,dx,y,h in rows]
def rel(name,kind,label,rows,color=None,note='',confidence='medium'):
 actor(name,kind,label,relkeys(rows),color,note,confidence)
actor('ego','car','自车',[[0,-391,-1.65,0],[178,1.8,-4.95,0]],'236,237,232',ego=True,note='Map-aligned static optical-flow timing. Red-light stop 67.5–78.3; critical brake 110–112; hold 112–120; creep then hold. Lateral clearance estimated.')
# Early forward and rear traffic. Identity is not extended through unresolvable occlusions.
actor('early_black_sedan','sedan','前段黑色轿车',[[0,-368,-1.65,0],[4,float(ego_func(4))+12,-1.65,0],[7,float(ego_func(7))+12,-3.6,-20],[9,float(ego_func(9))+9,-5.3,-15],[12,-334,-5.6,0],[18,-320,-5.6,0]],'35,40,43',note='Front 0–10 then moves toward right at first crossing; identity beyond 18s not asserted.')
rel('early_white_follower','car','前段后方白色轿车',[[0,-38,-1.65,0],[12,-14,-1.65,0],[20,-20,-1.65,0],[28,-9,-1.65,0],[32,-7,-1.7,0],[36,-6,-3.3,-5],[38,-1,-5,0],[40,4,-5.1,0],[42,10,-5.1,0],[48,28,-4.95,0]],'226,228,222',note='Rear 12–36, right 38–42. Same identity across pass inferred from matching white body.')
actor('early_right_whitevan','van','前段右侧白色厢式车',[[0,-349,-7.92,0],[20,-349,-7.92,0]],'228,226,212')
actor('early_blue_truck','boxtruck','前段右侧蓝色货车',[[10,-317,-7.98,0],[24,-317,-7.98,0]],'45,83,145',note='Outside driving lanes in road-side space. Body replaced with stock van/truck.')
actor('early_ad_van','van','前段带后窗广告面包车',[[16,-285,-5.3,0],[22,-279,-5.3,0],[28,-270,-5.3,0],[32,-267,-5.3,0],[42,-267,-5.3,0]],'212,206,186')
rel('micro_delivery','micro','后方小型封闭配送车',[[36,-38,-1.65,0],[44,-10,-1.65,0],[52,-22,-1.65,0],[60,-33,-1.65,0],[67,-14,-1.65,0],[72,-5.7,-1.65,0],[78,-5.7,-1.65,0],[84,-10,-1.65,0],[92,-7,-1.65,0],[98,-18,-1.65,0],[108,-40,-1.65,0]],'231,231,208',note='Rear-view compact enclosed vehicle. Stock Isetta only approximates silhouette; not the original delivery robot.')
rel('dark_suv_overtake','suv','右侧跟进并超越的深色 SUV',[[44,-18,-4.95,0],[50,-22,-4.95,0],[58,-22,-4.95,0],[66,-10,-4.95,0],[78,-8,-4.95,0],[86,-6,-4.95,0],[90,-2,-4.95,0],[92,3,-4.95,0],[94,11,-3.6,9],[96,20,-2.2,2],[103,29,-1.65,0],[110,42,-1.65,0],[118,70,-1.65,0]],'43,48,53',note='Rear 48–88, right pass 90–94, lead front 95–110; linking inferred.')
rel('blue_white_robotaxi','suv','右侧蓝白无人出租车',[[52,-7,-4.95,0],[58,-7,-4.95,0],[64,-4,-4.95,0],[68,0,-4.95,0],[78,0,-4.95,0],[82,2,-4.95,0],[85,8,-4.95,0],[88,14,-4.95,0],[92,24,-4.95,0],[100,40,-4.95,0]],'207,225,230',note='Right 56–82, front 83–92. Stock etron lacks Pony.ai decals and roof sensors.')
# Riders lead to and leave the signalized crossroad.
rel('lead_yellow_rider','scooter','路口前方黄衣骑行者',[[42,5,-5.8,0],[46,8,-4.5,0],[50,18,-3.1,0],[60,18,-2.9,0],[66,8,-2.9,0],[76,8,-2.9,0],[80,16,-2.9,0],[88,27,-2.9,0],[96,46,-2.9,0]],'214,178,38')
rel('lead_dark_rider','scooter','路口前方深衣骑行者',[[44,7,-6.1,0],[48,8,-5.0,0],[54,22,-5.3,0],[64,12,-5.3,0],[77,10,-5.3,0],[82,23,-5.5,0],[91,38,-5.7,0],[98,60,-5.7,0]],'33,43,49')
actor('crossing_sedan','sedan','红灯期间横穿路口的白色轿车',[[64,-120,22,-90],[67,-120,9,-90],[69,-120,0,-90],[72,-120,-15,-90],[77,-120,-45,-90]],'221,225,220',note='Front 67–70 cross traffic. Exact turn beyond visible junction unknown.')
actor('crossing_scooter','scooter','红灯期间横穿电动车',[[60,-134,-11,90],[63,-134,-4,90],[66,-134,5,90],[70,-134,13,90]],'48,61,87',note='Zebra crossing maneuver, not lane-following.')
actor('canopy_tricycle','scooter','带遮阳篷的三轮车',[[69,-167,-6.45,0],[74,-155,-6.45,0],[78,-146,-6.45,0],[81,-138,-6.45,0],[87,-119,-6.45,0],[94,-93,-6.45,0],[101,-65,-6.45,0]],'44,77,153',note='Rear canopy appearance then front 80s. Stock scooter cannot reproduce cargo/roof shape.',confidence='low')
actor('junction_white_boxvan','boxtruck','路口横向白色货车',[[71,-116,49,-90],[76,-116,18,-90],[78.5,-116,0,-90],[82,-116,-25,-90],[86,-116,-52,-90]],'219,222,214',note='Side-road pass around signalized junction; occluded portion estimated.')
# Critical rear/side neighbors and wrong-way encounter.
rel('silver_minivan','van','左后方银色面包车',[[89,-28,-4.95,0],[96,-12,-4.95,0],[99,-12,-1.65,8],[102,-14,-1.65,0],[108,-8.5,-1.65,0],[111,-4.5,-1.65,0],[114,-1.8,-1.65,0],[120,-1.8,-1.65,0],[126,-6,-1.65,0],[130,-5,-1.65,0],[135,-.5,-1.65,0],[140,1.7,-1.65,0],[154,1.7,-1.65,0],[160,1.4,-1.65,0],[178,1.4,-1.65,0]],'171,180,178',note='Continuous rear/left association 95–178. Dimensions deliberately approximate a small van, stock T2 appearance differs.',confidence='high')
rel('blue_sedan_rear','sedan','后方蓝色轿车',[[96,-32,-4.95,0],[104,-15,-4.95,0],[110,-12,-4.8,0],[113,-8,-4.65,0],[120,-8,-4.65,0],[127,-12,-4.8,0],[136,-9.0,-4.8,0],[145,-8.2,-4.8,0],[154,-8.2,-4.8,0],[160,-8.2,-4.8,0],[178,-8.2,-4.8,0]],'88,124,157',confidence='high')
actor('parked_gray_suv','suv','右侧灰色 SUV',[[96,-27.8,-8.04,0],[178,-27.8,-8.04,0]],'132,141,143',note='Front 108–110, right 111–130, rear-side thereafter. Held fixed; small creep cannot be distinguished from ego movement. Placed in shoulder clear of existing FBX fence.',confidence='high')
actor('parked_lead_white_van','van','前方路边白色面包车',[[98,10.3,-5.60,0],[178,10.3,-5.60,0]],'219,214,195',note='Stable vehicle ahead from 111–178 as ego approaches. No observed departure; held fixed.',confidence='high')
actor('parked_lead_compact','car','白色面包车前方浅色轿车',[[102,17.4,-5.5,0],[178,17.4,-5.5,0]],'206,211,202',note='Partly occluded ahead of white van; approximate stationary context.')
actor('wrongway_orange_rider','scooter','关键目标：橙色背心逆行骑行者',[[103,5,-6.2,180],[106,-7,-6.2,180],[108,-14,-6.15,180],[109,-18,-6.1,180],[110,-22,-5.95,178],[110.5,-24,-6.0,180],[111,-26,-6.05,180],[112,-29,-6.15,180],[114,-34,-6.15,180],[116,-40,-6.15,180],[120,-51,-6.15,180],[125,-69,-6.15,180]],'47,74,119',note='Front 110–111.3, right/rear 112–120. Orange vest / light helmet identify encounter. Lateral path adjusted within estimated video uncertainty for near-pass clearance; no collision dynamics asserted.',confidence='high')
actor('wrongway_white_rider','scooter','前一个白头盔逆行骑行者',[[101,-23,-6.45,180],[104,-35,-6.45,180],[106,-43,-6.45,180],[108,-51,-6.45,180],[110,-59,-6.45,180],[115,-78,-6.45,180]],'200,204,194',note='Front/right near 106–108; rear near 110. Separate from orange-vest rider.')
actor('access_cargo_trike','scooter','小开口处带篷三轮车',[[99,-38,-12,90],[104,-38,-8.7,90],[108,-38,-8.7,90],[112,-38,-8.7,90],[120,-38,-8.7,90],[124,-40,-7.1,170],[132,-62,-6.1,180]],'45,78,150',note='Front/right 105–108 and rear 110–120 at the access; motion behind occlusion is uncertain.',confidence='low')
actor('parked_access_boxtruck','boxtruck','小开口旁白色厢式货车',[[94,-51,-7.92,0],[122,-51,-7.92,0]],'227,228,218',note='Right-side box van visible 102–106 then rear 108–120; stock Sprinter is narrower than source box truck.')
# Opposing traffic with separate observed identities.
actor('opposing_blue_flatbed','boxtruck','对向蓝色平板货车',[[120,40,1.8,180],[125,23,1.8,180],[130,6,1.8,180],[134,-7.6,1.8,180],[142,-37,1.8,180]],'38,94,166',note='Left video 129–134; stock replacement has different cargo bed.')
actor('opposing_bluewhite_car','suv','对向蓝白色轿车',[[119,29,1.65,180],[123,15,1.65,180],[127,1,1.65,180],[132,-18,1.65,180]],'162,196,212')
actor('opposing_dark_suv','suv','对向深色 SUV',[[127,35,4.95,180],[133,12,4.95,180],[139,-11,4.95,180],[146,-39,4.95,180]],'52,57,60')
actor('opposing_early_sedan','car','前段对向黑色轿车',[[0,-310,1.65,180],[10,-347,1.65,180],[18,-380,1.65,180]],'35,38,42')
# End-of-video overtaking riders are supported in rear->left->front views.
for name,label,tpass,col,y in [('late_rider_red','末段红头盔骑行者',166,'52,72,107',-3.12),('late_rider_dark','末段深衣骑行者',169,'41,43,48',-3.20),('late_rider_yellow','末段黄衣骑行者',172,'216,181,30',-3.25),('late_rider_canopy','末段带伞电动车',174.5,'120,105,75',-3.18)]:
 actor(name,'scooter',label,[[tpass-12,-43,y,0],[tpass-7,-26,y,0],[tpass-3,-11,y,0],[tpass,2,y,0],[min(178,tpass+4),2+4*(min(178,tpass+4)-tpass),y,0],[178,2+4*(178-tpass),y,0]] if tpass+4<178 else [[tpass-12,-43,y,0],[tpass-7,-26,y,0],[tpass-3,-11,y,0],[tpass,2,y,0],[178,2+4*(178-tpass),y,0]],col,note='Rear/left/front track correspondence near video end. Rider clothing is only approximated with stock actor color.')
events=[(39,42,'early_slow','前段开口减速'),(67.5,78.3,'signal_wait','信号灯路口等待'),(82,94,'junction_departure','路口起步，蓝白出租车与深色 SUV 前行'),(105.5,108.5,'first_wrongway','第一辆逆行电动车经过右侧'),(110,111.4,'critical_wrongway','橙色背心骑行者逆行贴近右前方'),(110.2,112,'emergency_brake','自车减速至停驶'),(112,120,'brake_hold','自车停留，银色面包车和蓝色轿车靠近'),(120,143,'creep_forward','自车缓慢向前方白色面包车靠近'),(143,154,'queue_hold','自车停留'),(154,160,'last_creep','自车末段小幅前移'),(162,178,'rider_overtakes','多辆电动车从后方经左侧通过')]
for ar in actors:
 if ar['id']=='ego':continue
 half=ar['dimensions_m']['length']/2
 valid=[q for q in ar['samples'] if -399+half<=q['x']<=99-half]
 if not valid:raise RuntimeError('No in-map samples for '+ar['id'])
 ar['samples']=valid;ar['start_t']=valid[0]['t'];ar['end_t']=valid[-1]['t']
 ar['notes']+=' Longitudinal visibility trimmed to built XODR extent where necessary.'
data={'format_version':1,'scene':'UrbanBrake019742_DynamicReplay','target_carla_versions':['0.9.15'],'map_name':'UrbanBrake019742','xodr_file':'UrbanBrake019742.xodr','xodr_sha256':hashlib.sha256((STATIC/'UrbanBrake019742.xodr').read_bytes()).hexdigest(),'source_video_start_s':START,'source_video_end_s':END,'duration_s':END,'fps':FPS,'coordinates':'RH metres +X ego forward, +Y left, +Z up, h radians. Bbox ground centre. CARLA=(x,-y,z), yaw=-degrees(h).','reconstruction_method':'Manual four-view identity/event anchors, masked static-region optical-flow ego timing blended with map landmark constraints, PCHIP interpolation. Not calibrated multiview 3D tracking.','limitations':['Only visible salient targets modeled; not exhaustive all distant traffic.','Metric distance, depth, dimensions and occluded motion estimated.','Stock CARLA vehicles/riders replace nonstandard robotaxis, minivans and cargo tricycles.','Kinematic pose replay; wheel/pedestrian animation and closed-loop response not reconstructed.','No CARLA 0.9.15 engine run performed at authoring time.'],'events':[{'id':i,'video_start':a,'video_end':b,'start_t':a,'end_t':b,'label_zh':l} for a,b,i,l in events],'actors':actors}
(P/'scenario.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');shutil.copy2(STATIC/'UrbanBrake019742.xodr',P/'UrbanBrake019742.xodr')
with (P/'trajectories.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['actor_id','replay_time_s','source_video_time_s','x_rh_m','y_rh_m','z_ground_m','heading_rh_rad','x_carla_m','y_carla_m','yaw_carla_deg'])
 for ar in actors:
  for s in ar['samples']:w.writerow([ar['id'],s['t'],s['video_t'],s['x'],s['y'],s['z'],s['h'],s['x'],-s['y'],-math.degrees(s['h'])])
(P/'evidence/event_anchors.json').write_text(json.dumps({'ego_longitudinal_anchors':EK,'ego_lateral_anchors':EY,'events':data['events'],'actors':[{k:v for k,v in a.items() if k!='samples'} for a in actors]},ensure_ascii=False,indent=2),encoding='utf-8')
print('Generated',len(actors),'actors,',sum(len(a['samples']) for a in actors),'poses')
