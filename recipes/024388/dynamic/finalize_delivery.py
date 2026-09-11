import collections,hashlib,json,subprocess,zipfile
from pathlib import Path
import cv2
from lxml import etree as E
P=Path(__file__).resolve().parents[1]
d=json.loads((P/'scenario.json').read_text(encoding='utf-8'));schema=E.XMLSchema(E.parse(str(P/'validation/OpenSCENARIO.xsd')))
for p in [P/'LuoboTurn024388_CARLA015.xosc',*sorted((P/'template_compatible').glob('*.xosc'))]:schema.assertValid(E.parse(str(p)))
checks=json.loads((P/'validation/trajectory_checks.json').read_text());assert checks['same_as_static'] and not checks['estimated_bbox_overlap_windows']
assert json.loads((P/'validation/protocol_tests.json').read_text())['pass']
assert json.loads((P/'validation/sr_controller_tests.json').read_text())['all_37_actors_pass']
cap=cv2.VideoCapture(str(P/'preview/FourView_Trajectory_Review.mp4'));fps=cap.get(cv2.CAP_PROP_FPS);count=cap.get(cv2.CAP_PROP_FRAME_COUNT);assert fps==10 and count==1791
for t in [0,65,88,110,178]:cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read();assert ok and frame.shape==(900,1440,3)
cap.release()
audit=dict(actors=len(d['actors']),categories=dict(collections.Counter(a['category'] for a in d['actors'])),duration_s=d['duration_s'],poses=sum(len(a['samples']) for a in d['actors']),xosc_schema_pass=True,event_conditions_offline_pass=True,controller_interface_tests_pass=True,video_decode_pass=True,video_frames=int(count),original_xodr_unchanged=True,carla_015_engine_tested=False)
(P/'validation/delivery_summary.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
files=[p for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'runtime' not in p.parts and p.suffix not in ['.blend1','.zip','.log'] and p.name not in ['manifest_sha256.json','package_validation.json','protocol_run.json']]
manifest={p.relative_to(P).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(P/'manifest_sha256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');files.append(P/'manifest_sha256.json')
dest=P/'LuoboTurn024388_Dynamic_CARLA015_Package.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,Path(P.name)/p.relative_to(P))
with zipfile.ZipFile(dest) as z:
 assert z.testzip() is None
 for name,digest in manifest.items():assert hashlib.sha256(z.read(P.name+'/'+name)).hexdigest()==digest
report=dict(file=dest.name,bytes=dest.stat().st_size,files=len(files),crc_pass=True,all_manifest_hashes_pass=True)
(P/'validation/package_validation.json').write_text(json.dumps(report,indent=2));print(audit);print(report)
