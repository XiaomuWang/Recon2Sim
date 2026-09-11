import json,hashlib,shutil,zipfile,collections
from pathlib import Path
import cv2
P=Path(__file__).resolve().parents[1]
# Package the four source props using the CARLA 0.9.15 source import layout.
imp=P/'assets/CarlaImport/GreenRailDynamic';imp.mkdir(parents=True,exist_ok=True);props=[]
for name in ['greenrail_coach','greenrail_sweeper','greenrail_boxtruck','greenrail_container']:
 folder=imp/'Props'/name;folder.mkdir(parents=True,exist_ok=True);shutil.copy2(P/'assets'/(name+'.fbx'),folder/(name+'.fbx'));props.append(dict(name=name,size='small' if 'sweeper' in name else 'big',source='./Props/'+name+'/'+name+'.fbx',tag='Vehicles'))
(imp/'GreenRailDynamic.json').write_text(json.dumps({'maps':[],'props':props},indent=2),encoding='utf-8')
d=json.loads((P/'scenario.json').read_text(encoding='utf-8'));tr=json.loads((P/'validation/trigger_audit.json').read_text(encoding='utf-8'));proto=json.loads((P/'validation/protocol_tests.json').read_text());dv=json.loads((P/'validation/delivery_validation.json').read_text());xy=json.loads((P/'validation/trajectory_validation.json').read_text());xosc=json.loads((P/'validation/xosc_all_actor_activation_test.json').read_text());asset=json.loads((P/'validation/asset_fbx_roundtrip.json').read_text())
assert tr['pass_all'] and proto['pass'] and proto['tests_run']==7 and xosc['actors_activated']==29 and asset['pass_all'];assert not xy['estimated_bbox_overlaps'] and not dv['ego_wheel_points_outside_driving_lane']
video=P/'preview/GreenRail016955_FourView_Timeline.mp4';cap=cv2.VideoCapture(str(video));frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS);assert frames==2701 and abs(fps-15)<.01
decoded=0
for frame in [0,765,1800,2699,2700]:cap.set(cv2.CAP_PROP_POS_FRAMES,frame);ok,im=cap.read();assert ok and im.shape[:2]==(900,1440);decoded+=1
cap.release();(P/'validation/preview_video_validation.json').write_text(json.dumps(dict(frames=frames,fps=fps,duration_s=frames/fps,width=1440,height=900,decoded_keyframes=decoded,pass_all=True),indent=2))
summary=dict(scene='GreenRail016955',target_carla='0.9.15',source_interval_s=[0,180],actors=len(d['actors']),categories=dict(collections.Counter(a['category'] for a in d['actors'])),trajectory_samples=sum(len(a['samples']) for a in d['actors']),events=tr['event_count'],independent_activation_conditions=29,trigger_scheduler_simulations=12,protocol_tests=7,all_actors_activate_in_fake_world=True,xosc_roundtrip_max_xy_m=max(a['max_xosc_roundtrip_xy_error_m'] for a in dv['xosc_roundtrip']),estimated_bbox_overlaps=0,carla_engine_runtime_verified=False,static_xodr_sha256=d['xodr_sha256'],original_template_sha256=hashlib.sha256((P/'evidence/source_template.xosc').read_bytes()).hexdigest(),entrypoint='python play_xosc_carla.py',main_scenario='GreenRail016955_Timeline.xosc',scope='Video-estimated kinematic reconstruction; template dialect via supplied adapter, not a validated native ScenarioRunner scenario.')
(P/'DELIVERY_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
def include(p):
 rel=p.relative_to(P)
 return p.is_file() and p.suffix not in ['.zip','.blend1','.log','.pyc'] and '__pycache__' not in rel.parts and p.name not in ['protocol_run.json','DELIVERY_MANIFEST.json']
files=sorted([p for p in P.rglob('*') if include(p)]);manifest=[dict(path=p.relative_to(P).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
(P/'DELIVERY_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');files.append(P/'DELIVERY_MANIFEST.json')
dest=P/'GreenRail016955_Dynamic_CARLA0915.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for p in files:z.write(p,arcname='GreenRail016955_Dynamic/'+p.relative_to(P).as_posix())
with zipfile.ZipFile(dest) as z:assert z.testzip() is None;assert len(z.namelist())==len(files)
print(json.dumps(summary,ensure_ascii=False,indent=2));print('ZIP',dest.stat().st_size,'bytes;',len(files),'files; CRC pass')
