# -*- coding: utf-8 -*-
"""Scene-aligned visual recovery: reviewed anchors + masked image flow + PCHIP.
No calibrated depth or object detector is claimed. Canonical time = front MP4 playback.
"""
import json,math,csv,hashlib
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import median_filter,gaussian_filter1d
P=Path(__file__).resolve().parents[1];STATIC=P.parent/'environment_reconstruction_0508656';FPS=30;END=123.
curve=next(r for r in json.loads((STATIC/'validation/junction_paths.json').read_text()) if r['id']==113)
cp=np.array(curve['points']);cs=np.r_[0,np.cumsum(np.linalg.norm(np.diff(cp,axis=0),axis=1))];TURN=float(cs[-1]);BASE=278+TURN;INCIDENT=BASE+258
def route_pose(q,delta=0):
 if q<278:x=-282.05;y=-310+q;h=math.pi/2
 elif q<=BASE:
  u=q-278;x=float(np.interp(u,cs,cp[:,0]));y=float(np.interp(u,cs,cp[:,1]));j=min(len(cp)-2,max(0,int(np.searchsorted(cs,u)-1)));h=math.atan2(cp[j+1,1]-cp[j,1],cp[j+1,0]-cp[j,0])
 else:x=-258+q-BASE;y=-6.15;h=0
 return x-delta*math.sin(h),y+delta*math.cos(h),0,h
flow=json.loads((P/'evidence/ego_static_flow.json').read_text());ft=np.array([r['video_time'] for r in flow]);fv=median_filter(np.array([r['speed_proxy'] for r in flow]),size=5)
def progress(a,b,qa,qb,ramp_in=False,ramp_out=True):
 t=np.linspace(a,b,round((b-a)*FPS)+1);v=np.maximum(.10,np.interp(t,ft,fv));v=np.clip(v,0,np.percentile(v,90)*1.4+.1);v=gaussian_filter1d(v,FPS*.75)
 if ramp_out:v*=np.sin(np.minimum(1,(b-t)/.8)*math.pi/2)**2
 if ramp_in:v*=np.sin(np.minimum(1,(t-a)/.7)*math.pi/2)**2
 s=np.r_[0,np.cumsum((v[1:]+v[:-1])/2*np.diff(t))];return PchipInterpolator(t,qa+(qb-qa)*s/s[-1])
f1=progress(0,5.3,35,55);f2=progress(12,36,55,161,True);f3=progress(38,59.6,161,268,True)
# Metric speed after the turn is station-normalized, not recovered directly from flow.
f5=PchipInterpolator([66.3,67.3,69,71,73,75,80,85,90,95,98,100,101,101.8,102.5,103.0],[268,268.9,279,295,311,BASE+6,BASE+38,BASE+78,BASE+125,BASE+173,BASE+204,BASE+232,BASE+245.4,BASE+254.0,BASE+257.2,INCIDENT])
def ego_q(t):
 if t<5.3:return float(f1(t))
 if t<12:return 55.
 if t<36:return float(f2(t))
 if t<38:return 161.
 if t<59.6:return float(f3(t))
 if t<66.3:return 268.
 if t<103:return float(f5(t))
 return INCIDENT
ego_lat=PchipInterpolator([0,30,37,44,50,75,95,98.5,99.5,100.3,101.0,101.8,103,123],[3.3,3.3,3.3,2.5,0,0,0,0,.4,1.35,2.65,3.3,3.3,3.3])
actors=[]
def actor(aid,category,label,keys,dims,bps,color=None,note='',mode='route',ego=False,confidence='medium'):
 arr=np.array(keys,float);fs=[PchipInterpolator(arr[:,0],arr[:,i]) for i in range(1,arr.shape[1])];ta,tb=float(arr[0,0]),float(arr[-1,0]);samples=[];prevh=0
 for t in np.linspace(ta,tb,round((tb-ta)*FPS)+1):
  if ego:q=ego_q(t);lat=float(ego_lat(t));x,y,z,h=route_pose(q,lat)
  elif mode=='world':
   x,y,h=[float(f(t)) for f in fs];q=x+BASE+258;lat=y+6.15;z=0;h=math.radians(h)
  else:
   q,lat=[float(f(t)) for f in fs];x,y,z,h=route_pose(q,lat)
  samples.append({'t':round(t,6),'video_t':round(t,6),'s':round(q,6),'lateral':round(lat,6),'x':round(x,6),'y':round(y,6),'z':z,'h':h})
 if mode!='world':
  xy=np.array([[s['x'],s['y']] for s in samples]);grad=np.gradient(xy,axis=0)
  for i,s in enumerate(samples):
   if np.linalg.norm(grad[i])*FPS>.08:s['h']=math.atan2(grad[i,1],grad[i,0])
   # At a complete stop face the road, avoiding numeric jitter.
   else:s['h']=route_pose(s['s'],s['lateral'])[3]
   s['h']=round(s['h'],8)
 ar={'id':aid,'label_zh':label,'category':category,'dimensions_m':dict(zip(['length','width','height'],dims)),'blueprint_candidates':bps,'preferred_custom_blueprint':None,'color':color,'start_t':ta,'end_t':tb,'source_keyframes':keys,'keyframe_space':mode,'confidence':confidence,'notes':note,'samples':samples}
 actors.append(ar);return ar
car=(4.65,1.86,1.55);scooter=(1.95,.70,1.55);ped=(.5,.5,1.75)
actor('ego','car','自车：变道后停车',[[0,35,3.3],[123,INCIDENT,3.3]],(4.1,1.8,1.65),['vehicle.mini.cooper_s','vehicle.citroen.c3'],'245,245,240',ego=True,confidence='high_event_medium_pose',note='Stops near 5.3-12,36-38,59.6-66.3s; moves left around 99.5-101.8s and decelerates to rest by about 103s. Exact braking acceleration is estimated, not telemetry. Stock compact car substitutes for delivery vehicle.')
actor('yellow_bus','bus','前方黄色中巴',[[0,56,3.3],[4,68,3.3],[11.5,68,3.3],[15,89,3.3],[20,125,3.3],[27,161,2.2],[31,177,.3],[34,177,0],[39,178,0],[44,244,0],[48,280,0],[50,286,0],[56,286,0],[64,286,0],[69,BASE+9,0],[75,BASE+45,0],[81,BASE+108,0],[90,BASE+205,0]],(7.0,2.15,2.65),['vehicle.mitsubishi.fusorosa','vehicle.volkswagen.t2'],'230,190,28',note='Main leading minibus across the shaded approach and right turn; stopping intervals and relative ordering from front. Stock bus livery differs.')
actor('early_white_suv','car','前段右侧超越的白色 SUV',[[8,41,0],[12,57,0],[15,76,0],[18,101,0],[21,131,0],[23,150,0],[25,168,2.4],[26,179,3.3],[32,207,3.3],[38,246,3.3],[44,276,3.3]],(4.75,1.9,1.65),['vehicle.nissan.patrol_2021','vehicle.nissan.patrol'],'238,240,232',note='Seen rear near 10s, alongside right around 13-15s, then ahead. Track ends before unseen junction decision; no assumed continuation.')
# Parked context objects actually visible beside the approach. Kept separate from moving identities.
for aid,q,bp,col,label in [('parked_van_1',48,'vehicle.mercedes.sprinter','234,231,221','起点右侧白色广告面包车'),('parked_red_1',72,'vehicle.audi.a2','183,30,29','起点右侧红车'),('parked_gray_1',114,'vehicle.nissan.patrol_2021','111,121,123','前段右侧灰色 SUV'),('parked_white_1',137,'vehicle.tesla.model3','233,233,228','前段右侧白色轿车'),('parked_van_2',157,'vehicle.mercedes.sprinter','231,230,217','中段右侧白色面包车'),('parked_red_2',184,'vehicle.audi.a2','162,29,28','中巴旁红色停放车辆')]:
 dims=(5.9,2.0,2.65) if 'van' in aid else car
 actor(aid,'parked_car',label,[[0,q,-2.6],[123,q,-2.6]],dims,[bp],col,note='Stationary context estimated from front/right/rear order; not a moving-track claim.')
# Junction and post-turn two-wheelers.
actor('yellow_rider_early','motorcycle','右转口及右侧黄色骑手',[[59,277,-.5],[66,280,-.5],[70,BASE+4,-.6],[75,BASE+20,-.4],[80,BASE+49,-1.5],[85,BASE+73,-1.8],[90,BASE+98,-1.9],[96,BASE+128,-1.9]],scooter,['vehicle.vespa.zx125','vehicle.yamaha.yzf'],'227,192,30',note='Yellow rider ahead/right at turn; ego gradually overtakes after 82s. Blueprint color does not reproduce rider clothing.')
actor('red_rider','motorcycle','主路前方红衣骑手',[[73,BASE+7,2.6],[75,BASE+23,2.2],[80,BASE+55,.1],[84,BASE+84,-.2],[88,BASE+114,-1.45],[92,BASE+143,-1.45],[93,BASE+149,-1.45],[94,BASE+155,-.2],[98,BASE+181,-.2]],scooter,['vehicle.vespa.zx125'],'154,45,47',note='Front red-clad rider shifts toward roadside as ego gains; association after occlusion estimated.')
actor('white_helmet_rider','motorcycle','左侧超越的浅色头盔骑手',[[79,BASE+22,3.45],[81,BASE+47,3.45],[83,BASE+81,3.2],[87,BASE+143,3.2],[94,BASE+245,3.2]],scooter,['vehicle.vespa.zx125'],'198,207,184',note='Left camera around 80s and front around 82s establish overtake.')
actor('dark_overtaking_car','car','主路左侧超越的深色轿车',[[81,BASE+15,3.3],[84,BASE+48,3.3],[86,BASE+82,3.3],[88,BASE+112,3.3],[92,BASE+172,3.3],[99,BASE+270,3.3]],car,['vehicle.lincoln.mkz_2020','vehicle.tesla.model3'],'37,49,54',note='Visible on ego left around 85-86s, then pulling ahead.')
actor('roadside_gray_sedan','parked_car','主路右侧被自车驶过的灰色轿车',[[75,BASE+158,-2.55],[123,BASE+158,-2.55]],car,['vehicle.lincoln.mkz_2020'],'104,112,122',note='Front 86-92s, right 94s and rear 92-94s. Treated as stopped/very slow roadside car; exact low speed uncertain.')
actor('white_left_sedan','car','变道前左侧经过的白色轿车',[[89,BASE+92,3.3],[92,BASE+128,3.3],[94,BASE+160,3.3],[96,BASE+194,3.3],[99,BASE+252,3.3],[103,BASE+319,3.3]],car,['vehicle.tesla.model3'],'230,235,228',note='Left view around 94s; inferred continuation ahead after passing. Kept distinct from later close following white car.')
actor('blue_box_courier','motorcycle','带货箱电动车：左侧超越',[[94,BASE+147,3.5],[96,BASE+174,3.5],[98,BASE+216,3.3],[100,BASE+245,2.4],[102,BASE+276,2.6],[106,BASE+331,2.8],[111,BASE+401,2.8]],scooter,['vehicle.vespa.zx125'],'40,115,140',note='Rear 94s, left 96s, front 98-100s. Rider/cargo box shape is not reproduced by stock scooter.')
actor('white_following_car','car','急刹后靠近的白色后车',[[94,BASE+126,3.3],[97,BASE+172,3.3],[99,BASE+204,3.3],[100,BASE+220,3.3],[101,BASE+234,3.3],[102,BASE+245,3.3],[103,BASE+250,3.3],[104,BASE+251.7,3.3],[123,BASE+251.7,3.3]],car,['vehicle.tesla.model3','vehicle.lincoln.mkz_2020'],'232,234,228',confidence='high_event_medium_pose',note='Rear is roughly 2.1s ahead of front in the late portion; approaching/close-stop anchor was shifted onto front time, not matched by identical MP4 timestamps.')
actor('black_delivery_truck','truck','前方右车道黑色厢式货车',[[85,INCIDENT+19,0],[123,INCIDENT+19,0]],(7.4,2.3,3.15),['vehicle.carlamotors.carlacola'],'42,43,41',note='At right lane near bridge, nearly unchanged after ego stops. Static/slow ambiguity resolved as stationary context; exact brand/cargo silhouette approximate.')
actor('truckside_sedan','parked_car','货车右侧灰色停放轿车',[[85,INCIDENT+22,-2.65],[123,INCIDENT+22,-2.65]],car,['vehicle.lincoln.mkz_2020'],'124,123,131',note='Visible beside truck in front view; occupies road-edge/cycle strip as in footage.')
actor('silver_suv_late','car','停车后从右侧超越并切入的银灰 SUV',[[109,INCIDENT-52,0],[112,INCIDENT-31,0],[114,INCIDENT-17,0],[116,INCIDENT-6,0],[117,INCIDENT-.8,.0],[118,INCIDENT+3.6,.55],[119,INCIDENT+7.8,2.1],[120,INCIDENT+14.4,3.3],[121,INCIDENT+25,3.3],[122,INCIDENT+38,3.3],[123,INCIDENT+51,3.3]],(4.7,1.9,1.65),['vehicle.nissan.patrol_2021','vehicle.nissan.patrol'],'147,157,164',confidence='high_event_medium_pose',note='Rear/side/front identity linked using grey body and profile; overtakes stationary ego, changes from outer to inner lane at 118-120s, then accelerates away. It is NOT asserted to cause the earlier ego stop.')
actor('gray_sedan_late','car','银灰 SUV 后方的深灰轿车',[[112,INCIDENT-59,0],[115,INCIDENT-34,0],[118,INCIDENT-15,0],[120,INCIDENT-5,0],[121,INCIDENT-.7,0],[122,INCIDENT+3.5,0],[123,INCIDENT+7.0,0]],car,['vehicle.lincoln.mkz_2020'],'91,94,94',note='Seen rear and right after SUV. Motion ends at clip boundary; future interaction with truck not reconstructed.')
actor('yellow_scooter_late','motorcycle','末段右后方黄色电动车',[[116,INCIDENT-50,1.4],[119,INCIDENT-27,1.4],[121,INCIDENT-11,1.4],[122,INCIDENT-4.5,1.4],[123,INCIDENT+2,1.4]],scooter,['vehicle.vespa.zx125'],'236,177,20',note='Rear 119-121s corresponds to front around 121-123s. Do not extrapolate later pass beyond clip.')
actor('pink_rider_late','motorcycle','末段后方粉色骑手',[[117,INCIDENT-57,.9],[120,INCIDENT-33,.9],[123,INCIDENT-15,.9]],scooter,['vehicle.vespa.zx125'],'190,55,114',confidence='low',note='Small late rear-view target; approximate motion, identity and appearance uncertain.')
actor('curb_rider','motorcycle','货车旁路边慢行骑手',[[98,INCIDENT+8,-3.0],[111,INCIDENT+14,-3.0],[117,INCIDENT+14,-3.0],[123,INCIDENT+16,-3.0]],scooter,['vehicle.vespa.zx125'],'65,90,105',confidence='low',note='Small front-right roadside rider, kept out of motorway lanes; no exact apparel reconstruction.')
actor('man_near_median','pedestrian','末段绿篱旁向自车走来的男子',[[117.5,-9.2,-1.55,0],[119,-7,-1.55,0],[121,-4.6,-1.55,0],[123,-2.4,-1.55,0]],ped,['walker.pedestrian.0004','walker.pedestrian.0001'],mode='world',note='Late left/rear view shows person walking next to stopped white car toward ego; apparel uses stock walker.')
actor('junction_walker_1','pedestrian','右转口行人 A',[[56,-291,-30,0],[60,-286.6,-30,0],[63,-282.8,-30,0],[67,-282.8,-30,0],[69.5,-279,-30,0]],ped,['walker.pedestrian.0001'],mode='world',confidence='low',note='Junction front/left pedestrian cluster represented by two visible figures; identity and position estimated. Uses the open median end and a short inferred wait to avoid the planted bed and rider; ends before the curved curb.')
actor('junction_walker_2','pedestrian','右转口行人 B',[[57,-292,-28.5,0],[62,-286.5,-28.5,0],[65,-284,-28.5,0],[70,-284,-28.5,0]],ped,['walker.pedestrian.0005'],mode='world',confidence='low',note='Second approximate junction walker. Approaches the open median end, then waits beside the ego turning path; the occluded pause is an inference. Track ends without extrapolating unseen continuation.')
events=[(5.3,12,'follow_stop_1','跟随中巴第一次短暂停车'),(12,20,'white_suv_pass','白色 SUV 从右侧通过'),(36,38,'follow_stop_2','跟随中巴再次等待'),(59.6,66.3,'junction_wait','右转口等待'),(66.3,75,'right_turn','沿已建路口右转'),(80,83,'scooter_pass_1','浅色头盔骑手左侧通过'),(85,88,'car_pass','深色轿车左侧通过'),(95,100,'courier_pass','货箱电动车从左侧超越'),(99.5,101.8,'ego_lane_change','自车从外侧车道向内侧变道'),(101,103,'ego_braking','自车减速至停车'),(101,104,'following_brake','白色后车靠近并停下'),(103,123,'ego_hold','自车保持停止'),(117,120,'silver_suv_pass','银灰 SUV 右侧超越并切入'),(119,123,'late_traffic','后续轿车、电动车与绿篱旁行人')]
data={'format_version':1,'scene':'MeituanBrake0508656_DynamicReplay','target_carla_versions':['0.9.15'],'map_name':'MeituanBrake0508656','xodr_file':'MeituanBrake0508656.xodr','xodr_sha256':hashlib.sha256((P/'MeituanBrake0508656.xodr').read_bytes()).hexdigest(),'source_video_start_s':0,'source_video_end_s':END,'duration_s':END,'fps':FPS,'coordinates':'RH metres, X post-turn forward, Y left, Z up; h radians. Desired bbox ground-centre. CARLA=(x,-y,z),yaw=-degrees(h).','route_reference':{'roads':[30,113,20],'nominal_lanes':[-3,-1,-3],'south_length':278,'turn_length':TURN,'post_turn_station_origin':BASE,'incident_q':INCIDENT},'reconstruction_method':'Reviewed four-view event/identity anchors + masked static optical flow for ego timing + PCHIP interpolation. NOT calibrated multi-camera 3D tracking.','time_alignment':{'master':'front.mp4 playback','late_rear_video_t_approximately':'front_t - 2.1 s','late_right_video_t_approximately':'front_t + 1.3 s','late_left_video_t_approximately':'front_t + 0.0 s','scope':'Approximate late stable segment based on burned-in clocks; not global synchronization. Early freezes and playback stalls reviewed separately.'},'limitations':['Spatial dimensions, depths and occluded trajectories estimated on the existing approximate map.','Selected observable targets reconstructed; distant unidentifiable traffic and rows of parked two-wheelers omitted.','CARLA stock blueprints approximate silhouettes and colors; riders/clothing and cargo attachments differ.','Timestamp replay is kinematic visual playback, not a closed-loop braking/collision experiment.','No causal assertion that the later silver SUV caused the earlier stop.'],'events':[{'id':i,'video_start':a,'video_end':b,'start_t':a,'end_t':b,'label_zh':l} for a,b,i,l in events],'actors':actors}
(P/'scenario.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
with (P/'trajectories.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['actor_id','front_reference_time_s','x_rh_m','y_rh_m','z_ground_m','heading_rh_rad','x_carla_m','y_carla_m','yaw_carla_deg','route_station_m','lateral_from_outer_lane_m'])
 for a in actors:
  for s in a['samples']:w.writerow([a['id'],s['t'],s['x'],s['y'],s['z'],s['h'],s['x'],-s['y'],-math.degrees(s['h']),s['s'],s['lateral']])
(P/'evidence/event_anchors.json').write_text(json.dumps({'events':data['events'],'time_alignment':data['time_alignment'],'actors':[{k:v for k,v in a.items() if k!='samples'} for a in actors]},indent=2,ensure_ascii=False),encoding='utf-8')
print('Actors:',len(actors),'Poses:',sum(len(a['samples']) for a in actors),'Duration:',END,'Incident q:',INCIDENT)
