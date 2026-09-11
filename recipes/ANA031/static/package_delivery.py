"""Package final source assets, evidence and validation; no runtime or original videos."""
from pathlib import Path
import json,hashlib,zipfile,ast
P=Path(__file__).resolve().parents[1];name='RainJunctionANA031';pkg=name+'Package'
fbx=json.loads((P/'validation/fbx_validation.json').read_text());carla=json.loads((P/'validation/carla_validation.json').read_text())
assert fbx['fbx_reimport_pass'] and not fbx['road_surface_missing_hits'] and not fbx['missing_required_embedded_textures'] and not fbx['textures_missing']
assert carla['xsd_1_7_pass'] and carla['carla_offline_parse_pass'] and not carla['errors']
files=[]
for p in P.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(P)
 if '__pycache__' in rel.parts or '.fbm' in str(rel):continue
 if p.suffix.lower() in ['.blend1','.zip','.log']:continue
 if p.name in ['delivery_manifest.json','prepare.py']:continue
 if rel.parts[0]=='textures' and not any(p.name.endswith('_'+s+'.png') for s in ['basecolor','normal','roughness']):continue
 if rel.parts[0]=='renders' and p.suffix!='.png':continue
 if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(rel))
 files.append(p)
records=[{'path':p.relative_to(P).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
manifest={'map_name':name,'package_kind':'FBX + OpenDRIVE source assets; not cooked CARLA map','validation':{'xsd':True,'carla_offline_version':carla['carla_version'],'fbx_roundtrip':True,'waypoints_on_mesh':fbx['carla_waypoints_tested'],'unreal_runtime_tested':False},'side_cameras':'fisheye; no calibration supplied; exploratory projection only','files':records}
(P/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8');files.append(P/'delivery_manifest.json')
dest=P/(name+'_CARLA_Source.zip')
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,pkg+'/'+p.relative_to(P).as_posix())
with zipfile.ZipFile(dest) as z:
 assert z.testzip() is None
 assert pkg+'/'+name+'.fbx' in z.namelist() and pkg+'/'+name+'.xodr' in z.namelist()
print(json.dumps({'zip':str(dest),'bytes':dest.stat().st_size,'files':len(files),'zip_integrity_pass':True},indent=2))
