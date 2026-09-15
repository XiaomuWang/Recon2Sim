"""Local four-camera 157116 preview recipe; all metric anchors are estimates."""
import math
import shutil
import xml.etree.ElementTree as ET
import numpy as np
from scipy.interpolate import PchipInterpolator
from .common import PROJECT, WORKSPACE, read, write, sha

SID = '157116'
START, FINISH = .9, 21.8
DURATION = FINISH - START
TIMES = np.round(np.arange(0, DURATION + .001, .1), 4)
# No CAN or calibrated cameras were supplied. These are visual motion estimates.
SPEED_TIMES = [.9, 4, 8, 12, 14.5, 15, 15.5, 16, 16.6, 21.8]
SPEEDS = [9, 10, 12, 13, 12, 11, 6, 1, 0, 0]
V = PchipInterpolator(SPEED_TIMES, SPEEDS)(TIMES + START)
STATIONS = 25 + np.r_[0, np.cumsum((V[:-1] + V[1:]) * .05)]
END = float(STATIONS[-1])


def position(file_t):
    return float(np.interp(file_t - START, TIMES, STATIONS))


def configure():
    original = WORKSPACE / 'data/小马_LNBMC1TK5SZ157116_直路两轮车交互'
    aliases = PROJECT / 'work/157116_sources'
    aliases.mkdir(parents=True, exist_ok=True)
    evidence = {}
    for view, name in [('front', '前'), ('rear', '后'), ('left', '左'), ('right', '右')]:
        src = original / (name + '.mp4'); dst = aliases / (view + '.mp4')
        shutil.copy2(src, dst)
        evidence[view] = dict(original=str(src), original_sha256=sha(src), alias_sha256=sha(dst))
    cfg = dict(scene_id=SID, name='PonyFourView157116', title='直路行驶中两轮车交互与停车',
        video_dir=str(original.relative_to(WORKSPACE)), video_files=dict(front='前.mp4',rear='后.mp4',left='左.mp4',right='右.mp4'), vehicle_brand='小马', ego_actor_id='ego', camera_model='fisheye', camera_calibration_status='not supplied; no calibrated metric rectification',
        accident_actor_ids=['yellow_scooter', 'rider_gray', 'person_blue'],
        camera_file_time_offsets_s=dict.fromkeys(evidence, 0),
        camera_sync_status='Equal 200-frame files at 9.1 fps; simultaneous scene events visually consistent; hardware synchronization unknown',
        road_margin_m=.5, carla_host='127.0.0.1', carla_port=2000,
        source_video_start_s=START, source_video_end_s=FINISH)
    write(PROJECT / 'configs/157116.json', cfg)
    write(PROJECT / 'outputs/157116/evidence/source_files.json', evidence)
    return cfg


def static(sid=SID, mesh=True):
    from .pipeline import blender_exe, run_log
    cfg=configure(); out=PROJECT/'outputs'/sid; dest=out/'map';dest.mkdir(parents=True,exist_ok=True)
    length=END+90
    root=ET.Element('OpenDRIVE');ET.SubElement(root,'header',revMajor='1',revMinor='6',name=cfg['name'],version='1.0',date='2026-09-15',north='50',south='-50',east=str(length),west='0',vendor='Recon2Sim visual estimate')
    road=ET.SubElement(root,'road',name=cfg['name'],length=str(length),id='1',junction='-1');ET.SubElement(road,'link')
    typ=ET.SubElement(road,'type',s='0',type='town');ET.SubElement(typ,'speed',max='50',unit='km/h')
    plan=ET.SubElement(road,'planView');geo=ET.SubElement(plan,'geometry',s='0',x='0',y='0',hdg='0',length=str(length));ET.SubElement(geo,'line')
    ep=ET.SubElement(road,'elevationProfile');ET.SubElement(ep,'elevation',s='0',a='0',b='0',c='0',d='0');ET.SubElement(road,'lateralProfile')
    sec=ET.SubElement(ET.SubElement(road,'lanes'),'laneSection',s='0')
    for tag,ids in [('left',[3,2,1]),('center',[0]),('right',[-1,-2,-3])]:
        group=ET.SubElement(sec,tag)
        for lid in ids:
            lane=ET.SubElement(group,'lane',id=str(lid),type='driving' if lid else 'none',level='false');ET.SubElement(lane,'link')
            if lid:ET.SubElement(lane,'width',sOffset='0',a='3.5',b='0',c='0',d='0')
            ET.SubElement(lane,'roadMark',sOffset='0',type='broken' if lid else 'solid',weight='standard',color='white' if lid else 'yellow',width='.15',laneChange='both' if lid else 'none')
    ET.SubElement(road,'objects');ET.SubElement(road,'signals')
    ET.ElementTree(root).write(str(dest/(cfg['name']+'.xodr')),encoding='utf-8',xml_declaration=True)
    (dest/'textures').mkdir(exist_ok=True)
    for texture in (WORKSPACE/'static_data/environment_reconstruction_0508656/textures').glob('*.png'):
        if not texture.name.startswith('sign_'): shutil.copy2(texture,dest/'textures'/texture.name)
    write(dest/'road_parameters.json',dict(start_station_m=0,end_station_m=length,incident_station_m=END,turn_start_m=10000,turn_end_m=10001,radius_m=10,lane_width_m=3.5,estimated=True))
    write(dest/'coordinate_contract.json',dict(source_frame='RH metres',carla_frame='x=X,y=-Y,z=Z,yaw=-heading',accuracy='Visual estimates, no surveyed/calibrated metric ground truth'))
    write(dest/(cfg['name']+'Package.json'),dict(maps=[dict(name=cfg['name'],source=cfg['name']+'.fbx',xodr=cfg['name']+'.xodr',use_carla_materials=False)],props=[]))
    shutil.copytree(PROJECT/'work/environment_reconstruction_019742/validation/schema',PROJECT/('work/environment_reconstruction_'+sid)/'validation/schema',dirs_exist_ok=True)
    if mesh:run_log([blender_exe(),'--background','--python-exit-code','1','--python',PROJECT/'recipes/157116/build_scene.py','--',out],out/'validation/static_fbx_build.log')


def actor(aid,label,kind,points,bp,color=None,dimensions=(4.7,1.9,1.5)):
    """Points: original-file time, X station, RH lateral, heading degrees, roll."""
    funcs=[PchipInterpolator([p[0] for p in points],[p[k] for p in points]) for k in [1,2,3,4]]
    ts=np.linspace(points[0][0],points[-1][0],round((points[-1][0]-points[0][0])*20)+1)
    samples=[]
    for t in ts:
        x,y,h,r=[float(f(t)) for f in funcs]
        samples.append(dict(t=round(float(t-START),5),video_t=float(t),x=x,y=y,z=0,h=math.radians(h),roll_carla_deg=r))
    return dict(id=aid,label_zh=label,category=kind,blueprint_candidates=bp,color=color,
        dimensions_m=dict(zip(['length','width','height'],dimensions)),confidence='low',
        notes='Visually estimated identity, path, scale and rigid pose; stock appearance proxy; no impact or articulated body dynamics',anchors=points,samples=samples)


def generate(sid=SID):
    cfg=read(PROJECT/'configs/157116.json');e=END
    lateral=PchipInterpolator([START,5,7,9,FINISH],[-5.25,-5.25,-3.8,-1.75,-1.75])(TIMES+START)
    ego_points=[[float(t+START),float(s),float(l),0,0] for t,s,l in zip(TIMES,STATIONS,lateral)]
    actors=[actor('ego','小马主车','car',ego_points,['vehicle.lincoln.mkz_2020','vehicle.tesla.model3'],'235,235,235')]
    scooter=[[14.8,e+1.8,-8,80,0],[15.2,e+1.8,-5.3,95,0],[15.5,e+1.7,-2.9,100,20],[15.9,e+3,-3.1,25,72],[16.5,e+5.5,-4.5,15,88],[FINISH,e+5.5,-4.5,15,88]]
    gray=[[14.8,e+1.8,-8,80,0],[15.5,e+1.7,-2.9,100,0],[16,e+2.5,-2.7,30,25],[16.6,e+4,-2.2,20,82],[18.8,e+4,-2.2,20,82],[20,e+4.3,-2.5,80,35],[FINISH,e+4.3,-2.5,80,35]]
    blue=[[14.8,e+2,-8.5,80,0],[15.5,e+2,-3.4,100,0],[16,e+3.1,-4.2,30,40],[16.8,e+5.5,-5.2,0,85],[18,e+5.8,-5.3,0,55],[19,e+6.1,-5.5,180,0],[FINISH,e+4.8,-4.8,180,0]]
    actors.append(actor('yellow_scooter','黄色两轮车（外观代理）','motorcycle',scooter,['vehicle.vespa.zx125','vehicle.yamaha.yzf'],'235,185,30',(1.9,.7,1.4)))
    actors.append(actor('rider_gray','深色上衣人员','pedestrian',gray,['walker.pedestrian.0001'],dimensions=(.5,.5,1.7)))
    actors.append(actor('person_blue','蓝衣人员','pedestrian',blue,['walker.pedestrian.0002'],dimensions=(.5,.5,1.7)))
    def traffic(aid,label,bp,color,pts,kind='car',dim=(4.7,1.9,1.6)):
        actors.append(actor(aid,label,kind,pts,[bp],color,dim))
    traffic('lead_red','前方红色车','vehicle.audi.a2','185,30,28',[[START,60,-5.25,0,0],[10,position(10)+18,-5.25,0,0],[14,position(14)+20,-5.25,0,0],[FINISH,e+60,-5.25,0,0]])
    traffic('silver_sedan','右侧银色轿车','vehicle.lincoln.mkz_2017','190,190,185',[[9,position(9)+14,-5.25,0,0],[12,position(12),-5.25,0,0],[16,e-12,-5.25,0,0],[FINISH,e-12,-5.25,0,0]])
    traffic('white_suv','右侧白色SUV','vehicle.audi.etron','230,230,230',[[11.5,position(11.5)+18,-5.25,0,0],[14,position(14),-5.25,0,0],[16,e-6,-5.25,0,0],[FINISH,e-6,-5.25,0,0]])
    traffic('dark_mpv','右前深色MPV（车型代理）','vehicle.nissan.patrol_2021','18,20,24',[[12,position(12)+22,-5.25,0,0],[14.5,position(14.5)+8,-5.25,0,0],[15.5,e-2,-5.25,0,0],[16.6,e-3,-5.25,0,0],[FINISH,e-3,-5.25,0,0]],'suv',(5.1,2,1.9))
    traffic('white_ahead','事故点右前白车','vehicle.tesla.model3','230,230,230',[[14,e+13,-5.25,0,0],[16,e+13,-5.25,0,0],[FINISH,e+15,-5.25,0,0]])
    traffic('roadside_truck','道路右侧货车','vehicle.carlamotors.carlacola','75,115,160',[[4,position(9)+6,-8.75,0,0],[12,position(9)+6,-8.75,0,0]],'truck',(7,2.4,3))
    traffic('opposing_white','对向白车','vehicle.tesla.model3','230,230,230',[[8,position(13)+15,1.75,180,0],[15,position(13)-35,1.75,180,0]])
    traffic('opposing_gray','对向灰车','vehicle.audi.a2','80,85,90',[[13,e+30,1.75,180,0],[FINISH,e-45,1.75,180,0]])
    limitations=['Metric speed and road scale are visual estimates, with assumed 3.5 m lanes; no CAN or camera calibration supplied.',
        'First 0.88 s of each source is visibly undecoded; preview begins at 0.9 s. Last 0.18 s is outside the chosen valid comparison interval.',
        'Equal file frame counts and visibly corresponding events support zero-offset comparison; hardware synchronization is unverified.',
        'Principal visible actors only; no exhaustive traffic inventory. Stock vehicles and rigid human poses approximate appearance; no articulated fall or physical impact validation.',
        'Roadside accesses and divider openings are visual geometry, not surveyed junction topology.']
    scenario=dict(scene_id=sid,map_name=cfg['name'],duration_s=DURATION,source_video_start_s=START,source_video_end_s=FINISH,actors=actors,fps=20,
        weather=dict(cloudiness=30,sun_altitude_angle=45,wetness=0),
        events=[dict(start_t=0,end_t=13.9,label_zh='直路行驶与向左侧车道靠拢'),dict(start_t=13.9,end_t=15.9,label_zh='两轮车进入前方、接触与倒地（估计姿态）'),dict(start_t=15.9,end_t=DURATION,label_zh='主车停车与人员后续动作')],
        reconstruction_method='Four-camera visual anchors, assumed lane scale and PCHIP; explicit estimated speed profile',limitations=limitations)
    write(PROJECT/('work/dynamic_replay_'+sid)/'scenario.json',scenario)
    write(PROJECT/'outputs'/sid/'evidence/video_audit.json',dict(source_speed_times_s=SPEED_TIMES,estimated_speed_m_s=SPEEDS,metric_ground_truth=False,source_time_range_s=[START,FINISH],critical_source_times_s=[15.2,15.5,16.8],limitations=limitations))
