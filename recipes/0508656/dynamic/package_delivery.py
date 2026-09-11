# -*- coding: utf-8 -*-
import json,hashlib,zipfile
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def read(file):return json.loads((P/file).read_text(encoding='utf-8'))
data=read('scenario.json');xosc=read('validation/xosc_validation.json');trace=read('scenario_from_xosc.events.json');protocol=read('validation/protocol_tests.json');geo=read('validation/static_surface_validation.json');traj=read('validation/trajectory_validation.json');comparison=read('validation/map_and_xml_validation.json')
assert all(f['schema_valid'] and f['all_events_reachable'] for f in xosc['files'])
assert trace['all_events_executed_in_offline_timeline'] and trace['entities']==27
assert protocol['pass'] and protocol['tests_run']==7
assert not traj['estimated_bbox_overlaps']
assert all(not a['road_surface_missing_count'] and not a['static_structure_ray_hits'] for a in geo['actors'])
assert comparison['xodr_identical_to_static_delivery'] and comparison['xml_path_max_error_m_after_schedule_offset']<.40
template_source=Path(r'C:\Users\Administrator\Desktop\模板\scenario - 2026-09-08T142648.948.xosc')
assert template_source.read_bytes()==(P/'evidence/template.xosc').read_bytes()
summary={'map':data['map_name'],'target_carla':'0.9.15','actors':len(data['actors']),'reference_duration_s':data['duration_s'],'reference_poses':sum(len(a['samples']) for a in data['actors']),'xosc_events':trace['events'],'all_entity_initialization_and_clock_conditions_checked':True,'all_events_reachable_offline':True,'full_xosc_fake_world_actor_lifecycle_pass':True,'protocol_tests_passed':7,'estimated_2d_bbox_overlaps_over_0_03_m2':0,'static_road_and_structure_footprint_ray_checks':sum(a['checks'] for a in geo['actors']),'static_surface_missing_rays':0,'static_structure_intersection_rays':0,'xodr_parsed_by_carla_pythonapi':'0.9.15','xodr_unchanged_from_static_delivery':True,'template_source_sha256':hashlib.sha256(template_source.read_bytes()).hexdigest(),'xml_timeline_vs_reference_max_xy_difference_m_after_0_10s_motion_offset':comparison['xml_path_max_error_m_after_schedule_offset'],'real_carla_server_runtime_verified':False,'notes':['Reconstruction is a visual estimate without camera calibration or ground truth.','Protocol tests use a fake world, not CARLA engine execution.','Bounds use estimated dimensions, not server blueprint bounding boxes.','The preview is a schematic plan recording.']}
(P/'validation/delivery_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
files=[]
for f in sorted(P.rglob('*')):
 rel=f.relative_to(P)
 if not f.is_file() or any(t in rel.parts for t in ['runtime','__pycache__']):continue
 if f.suffix in ['.zip','.log','.pyc'] or f.name in ['protocol_run.json','last_run_report.json','manifest.json']:continue
 if not f.stat().st_size:continue
 files.append(f)
manifest={'format':1,'files':[{'path':str(f.relative_to(P)).replace('\\','/'),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]}
(P/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');files.append(P/'manifest.json')
dest=P/'MeituanBrake0508656_CARLA0915_Dynamic.zip'
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in files:z.write(f,'MeituanBrake0508656_Dynamic/'+str(f.relative_to(P)).replace('\\','/'))
with zipfile.ZipFile(dest) as z:
 assert z.testzip() is None
 for r in manifest['files']:
  assert hashlib.sha256(z.read('MeituanBrake0508656_Dynamic/'+r['path'])).hexdigest()==r['sha256']
print(json.dumps(summary,ensure_ascii=False,indent=2));print('PACKAGE',dest,'BYTES',dest.stat().st_size,'FILES',len(files))
