"""Create a portable delivery archive, excluding downloaded runtimes and mock run logs."""
import hashlib,json,zipfile,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1]
src=P/'scripts/build_dynamic_assets.py'
txt=src.read_text(encoding='utf-8').replace("export(truck,'NanshanDumpTruck')","export(truck,'nanshan_dumptruck')").replace("export(trike,'NanshanCargoTrike')","export(trike,'nanshan_cargotrike')").replace('./assets/NanshanDumpTruck.fbx','./assets/nanshan_dumptruck.fbx').replace('./assets/NanshanCargoTrike.fbx','./assets/nanshan_cargotrike.fbx')
src.write_text(txt,encoding='utf-8')
config=json.loads((P/'NanshanDynamicProps.json').read_text())
for prop in config['props']:prop['source']='./assets/'+prop['name']+'.fbx'
(P/'NanshanDynamicProps.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
shutil.copy2(P.parent/'environment_reconstruction_014346/scripts/road_layout.py',P/'scripts/road_layout.py')
files=[p for p in P.iterdir() if p.is_file() and p.suffix in {'.json','.csv','.xodr','.xosc','.py','.md','.blend'} and p.name not in {'manifest.json','last_run_report.json'}]
for dirname in ['assets','preview','evidence','validation','scripts','template_compatible']:
 for p in (P/dirname).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.log','.pyc','.blend1','.zip'} and p.name not in {'protocol_run.json','refine_clearance.py','refine_clearance_2.py'}:
   files.append(p)
manifest={'target_versions':['0.9.15','0.9.16'],'source_video_interval_s':[52,159],'actor_count':10,'runtime_verified':False,'validation_scope':'Offline schema, trajectory consistency and mock protocol tests only. Not an engine-tested cooked CARLA package.','files':[{'path':p.relative_to(P).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
(P/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');files.append(P/'manifest.json')
archive=P/'NanshanGate014346_Dynamic_CARLA.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(files):z.write(p,p.relative_to(P).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert 'scenario.json' in z.namelist() and 'README.md' in z.namelist()
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'file_count':len(files),'zip_crc_pass':True},indent=2))
