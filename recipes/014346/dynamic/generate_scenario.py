"""Video-referenced reconstruction. Manual spatial anchors + masked image-flow timing.
All distances are scene-aligned estimates, not calibrated 3D measurements.
"""
import json,math,sys,csv,hashlib,shutil
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import median_filter,gaussian_filter1d
P=Path(__file__).resolve().parents[1];STATIC=P.parent/'environment_reconstruction_014346'
sys.path.insert(0,str(STATIC/'scripts'))
from road_layout import pose
START=52.;END=159.;FPS=30
flow=json.loads((P/'evidence/ego_static_flow.json').read_text())
ft=np.array([r['video_time'] for r in flow]);fv=median_filter(np.array([r['speed_proxy'] for r in flow]),size=5)
def progression(a,b,s0,s1):
 ts=np.linspace(a,b,round((b-a)*FPS)+1);v=np.interp(ts,ft,fv);v=gaussian_filter1d(v,FPS*.35)
 # Ramp to/from a held pose. Only time distribution comes from optical flow.
 ramp=np.minimum(1,np.maximum(0,(b-ts)/.6));v*=np.sin(ramp*math.pi/2)**2
 if a>90:v*=np.sin(np.minimum(1,(ts-a)/.6)*math.pi/2)**2
 cum=np.r_[0,np.cumsum((v[1:]+v[:-1])/2*np.diff(ts))];ss=s0+(s1-s0)*cum/max(cum[-1],1e-6)
 return PchipInterpolator(ts,ss)
f1=progression(52,68,3,94);f2=PchipInterpolator([68,69,70,71,71.8],[94,97.8,100.8,103.5,104]);f3=progression(92.1,110.6,104,135)
def ego_s(t):
 return float(f1(t) if t<68 else f2(t) if t<71.8 else 104 if t<92.1 else f3(t) if t<110.6 else 135)
def spline(keys):
 a=np.array(keys,float);return [PchipInterpolator(a[:,0],a[:,i],extrapolate=False) for i in range(1,a.shape[1])],a[0,0],a[-1,0]
actors=[]
def actor(name,kind,label,keys,dims,bps,color=None,custom=None,note='',ego=False):
 fs,a,b=spline(keys);samples=[]
 lateral=PchipInterpolator([52,64,66,67.3,68.5,70,71.8,92.1,96,98,100,102,104,110.6,159],[-1.25,-1.2,-1.1,-1.1,.95,.95,.5,.5,-.35,-.45,-.5,-.9,-1.3,-1.3,-1.3])
 for t in np.linspace(a,b,round((b-a)*FPS)+1):
  if ego:
   s=ego_s(t);off=float(lateral(t));x,y,z,h=pose(s,off);yaw=math.degrees(h)
  else:
   vals=[float(f(t)) for f in fs]
   if kind=='gate_truck':
    s,off,yaw=vals;x,y,z,h=pose(s,off);yaw+=math.degrees(h)
   else:
    s,off,yaw=vals;x,y,z,h=pose(s,off);yaw+=math.degrees(h)
  if kind=='parked':z+=.15
  samples.append({'t':round(t-START,6),'video_t':round(t,6),'s':round(s,5),'lateral':round(off,5),'x':round(x,5),'y':round(y,5),'z':round(z,5),'h':round(math.radians(yaw),7)})
 ar={'id':name,'label_zh':label,'category':kind,'dimensions_m':dict(zip(['length','width','height'],dims)),'blueprint_candidates':bps,'preferred_custom_blueprint':custom,'color':color,'start_t':round(a-START,6),'end_t':round(b-START,6),'source_keyframes':keys,'confidence':'qualitative motion and timing supported; metric poses estimated','notes':note,'samples':samples}
 actors.append(ar)
actor('ego','car','自车',[[52,3,-1.25,0],[159,135,-1.3,0]],(4.7,1.9,1.65),['vehicle.lincoln.mkz_2020','vehicle.tesla.model3'],'235,235,230',ego=True,note='Pose follows the existing reconstructed road. Two stops from front/static flow. No calibrated camera extrinsics.')
actor('oncoming_truck','truck','先会车的渣土车',[[52,115,1.45,180],[58,103,1.45,180],[62,94,1.45,180],[64,88,1.45,180],[66,86,1.45,180],[159,86,1.45,180]],(8.4,2.5,3.3),['vehicle.carlamotors.carlacola'],'176,164,105','static.prop.nanshan_dumptruck',note='Passes the ego around 64-66s, then its rear remains visible. Subsequent static pose inferred from rear view.')
actor('gate_truck','gate_truck','右侧横向驶出货车',[[52,100,-8,90],[65,100,-8,90],[66.8,100,-5.8,90],[68.5,100,-4.8,90],[120,100,-4.8,90],[128,100.3,-3.5,80],[132,101.3,-1.9,60],[136,105,0,10],[140,113,1.35,0],[144,126,1.4,0],[148,139,1.4,0],[152,154,1.4,0],[156,170,1.4,0],[159,183,1.4,0]],(8.4,2.5,3.3),['vehicle.carlamotors.carlacola'],'176,164,105','static.prop.nanshan_dumptruck',note='Emerges around 66-70s; waits beside ego; rear view shows renewed departure around 120-140s and passing ego around 144-152s. Occupies opposing lane while passing, as observed; not a legal route assertion.')
actor('cargo_tricycle','tricycle','蓝色货运三轮车',[[52,150,1.9,180],[68,125,1.9,180],[72,120,1.9,180],[76,116,1.75,180],[78,114.5,1.6,190],[79.5,114,.85,250],[80.5,115,-.25,315],[82,120,-1.2,360],[86,137,-1.25,360],[92,164,-1.25,360],[100,204,-1.25,360]],(2.8,1.25,1.6),['vehicle.vespa.zx125','vehicle.yamaha.yzf'],'40,65,130','static.prop.nanshan_cargotrike',note='Approaches in front view then turns around at 79-82s. Stock fallback is a scooter and does not match cargo silhouette.')
actor('worker_orange','pedestrian','橙色反光背心工作人员',[[65,103,2.35,0],[79.8,103,2.35,0],[82,107,1.6,-90],[84,107,-.15,-90],[86,107,-2.05,-90],[87,107,-2.05,90],[90,107.5,1.15,100],[91,107.5,2.35,180],[94,103,2.95,180],[120,103,2.95,0],[128,108,2.95,0],[136,111,2.95,0],[150,111,2.95,0],[159,116,2.95,0]],(.5,.5,1.75),['walker.pedestrian.0001','walker.pedestrian.0004'],note='Crosses ego front, returns to left verge. Pedestrian clothing and skeletal gait are not matched by stock CARLA walkers.')
actor('worker_gray','pedestrian','灰衣工作人员',[[84,94,1.9,0],[90,99,1.9,0],[96,107,2.1,0],[99,107,2.95,0],[110,107,2.95,0],[125,112,2.95,0],[136,114,2.95,0],[150,114,2.95,0],[159,119,2.95,0]],(.5,.5,1.75),['walker.pedestrian.0004','walker.pedestrian.0001'],note='Identity linkage across rear/left occlusions is tentative.')
actor('delivery_scooter','motorcycle','后方电动车',[[78,80,-1.8,0],[84,93,-1.8,0],[87,97,-1.7,0],[92.4,97,-1.7,0],[93,97,-.7,50],[94,100,.25,0],[95,106,-.5,-10],[96,111,-1.9,0],[98,119,-2.05,0],[100,128,-2.05,0],[104,146,-1.4,0],[110,176,-1.35,0],[116,205,-1.35,0]],(2,.7,1.6),['vehicle.vespa.zx125','vehicle.yamaha.yzf'],'25,40,70',note='Waits behind ego, then passes on ego right at about 98-100s. Appearance uses stock scooter.')
actor('silver_sedan','car','后方驶来的银灰轿车',[[100,93,.8,0],[104,106,1.45,0],[106,115,1.45,0],[108,125,1.45,0],[110,137,1.45,0],[112,150,1.45,0],[116,175,-.5,0],[121,204,-1.25,0]],(4.7,1.85,1.45),['vehicle.tesla.model3','vehicle.audi.a2'],'161,179,178',note='Appears beside gate in rear view at 104-108s and passes left about 109-111s; link to front appearance uncertain after occlusion.')
actor('parked_scooter_1','parked','左护栏旁停放电动车',[[52,108,3.72,0],[159,108,3.72,0]],(1.9,.65,1.3),['vehicle.vespa.zx125'],'30,32,34',note='Stationary context actor, not a recovered moving track.')
actor('parked_scooter_2','parked','前方护栏旁停放电动车',[[52,155,3.72,180],[159,155,3.72,180]],(1.9,.65,1.3),['vehicle.vespa.zx125'],'70,70,65',note='Stationary context actor; position estimated from front/left views.')
events=[(64,66,'oncoming_pass','先会车货车从自车左侧通过'),(66.8,70.5,'gate_emergence','右侧工地货车驶出并停在便道边'),(71.8,92.1,'ego_stop_1','自车第一次停车'),(79,82,'tricycle_turn','三轮车在前方掉头驶离'),(82,90.5,'worker_crossing','工作人员横穿车前并返回'),(98,100.5,'scooter_pass','电动车从右侧驶过'),(108.5,111.5,'sedan_pass','银灰轿车从左侧驶过'),(110.6,159,'ego_stop_2','自车第二次停车'),(120,140,'truck_departure','工地货车重新驶出并转向'),(143,153,'truck_pass_ego','货车从自车左侧驶过')]
data={'format_version':1,'scene':'NanshanGate014346_DynamicReplay','target_carla_versions':['0.9.15','0.9.16'],'map_name':'NanshanGate014346','xodr_file':'NanshanGate014346.xodr','xodr_sha256':hashlib.sha256((STATIC/'NanshanGate014346.xodr').read_bytes()).hexdigest(),'source_video_start_s':START,'source_video_end_s':END,'duration_s':END-START,'fps':FPS,'coordinates':'right-handed metres, X forward at gate, Y left, Z up; h radians; position is intended bbox ground-centre. CARLA uses (x,-y,z), yaw=-degrees(h)','reconstruction_method':'Manually reviewed four-view event/identity anchors; masked static optical-flow timing for ego, normalized to estimated scene stations; PCHIP keyframe interpolation. Not calibrated 3D object tracking.','limitations':['Only 52-159s lies in current detailed XODR; 0-52s boulevard excluded.','Metric depth, object dimensions and occluded movement estimated.','Stock blueprint appearance and wheel/pedestrian animation do not match source.','Kinematic visual replay, no closed-loop response or collision dynamics validation.'],'events':[{'id':i,'video_start':a,'video_end':b,'start_t':a-START,'end_t':b-START,'label_zh':l} for a,b,i,l in events],'actors':actors}
(P/'scenario.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');shutil.copy2(STATIC/'NanshanGate014346.xodr',P/'NanshanGate014346.xodr')
with (P/'trajectories.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['actor_id','replay_time_s','source_video_time_s','x_rh_m','y_rh_m','z_ground_m','heading_rh_rad','x_carla_m','y_carla_m','yaw_carla_deg','road_station_m','lateral_offset_m'])
 for ar in actors:
  for s in ar['samples']:w.writerow([ar['id'],s['t'],s['video_t'],s['x'],s['y'],s['z'],s['h'],s['x'],-s['y'],-math.degrees(s['h']),s['s'],s['lateral']])
(P/'evidence/event_anchors.json').write_text(json.dumps({'events':data['events'],'actors':[{k:v for k,v in a.items() if k!='samples'} for a in actors]},indent=2,ensure_ascii=False),encoding='utf-8')
print('Generated',len(actors),'actors;',sum(len(a['samples']) for a in actors),'poses; duration',data['duration_s'])

