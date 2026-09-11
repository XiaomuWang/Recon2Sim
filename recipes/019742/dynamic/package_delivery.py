import csv,hashlib,json,zipfile
from pathlib import Path
P=Path(__file__).resolve().parents[1]
mapping=json.loads((P/'template_compatible/entity_mapping.json').read_text(encoding='utf-8'))
timeline=json.loads((P/'template_compatible/timeline_events.json').read_text(encoding='utf-8'))
rows=[]
for a in mapping:
 events=[e for e in timeline['events'] if e['entity']==a['entity']];first=events[0]
 rows.append({'entity':a['entity'],'source_id':a['source_id'],'label':a['label'],'blueprint':a['blueprint'],'source_visible_start_s':a['active_source_video_s'][0],'source_visible_end_s':a['active_source_video_s'][1],'activation_condition':'SimulationTime > %.6f'%first['simulation_t'],'condition_edge':'none','delay_s':0,'maximum_execution_count':1,'first_event':first['event'],'event_count':len(events),'depends_on_other_actor':False})
with (P/'template_compatible/actor_activation_conditions.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def included(p):
 rel=p.relative_to(P)
 return p.is_file() and not any(q in ['runtime','.compiled','__pycache__'] for q in rel.parts) and p.suffix not in ['.log','.blend1','.avi','.zip','.pyc'] and p.name not in ['protocol_run.json','manifest.json','package_validation.json']
files=sorted(p for p in P.rglob('*') if included(p))
manifest={'map_name':'UrbanBrake019742','target_carla':'0.9.15','runtime_verified':False,'actors':32,'duration_s':178,'events_per_xosc':1795,'source_template_sha256':hashlib.sha256((P/'evidence/source_template.xosc').read_bytes()).hexdigest(),'xodr_sha256':hashlib.sha256((P/'UrbanBrake019742.xodr').read_bytes()).hexdigest(),'files':[{'path':p.relative_to(P).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(P/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8');files.append(P/'manifest.json')
out=P/'UrbanBrake019742_DynamicPackage.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,p.relative_to(P))
with zipfile.ZipFile(out) as z:bad=z.testzip();assert bad is None;count=len(z.infolist())
report={'zip':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'files':count,'crc_pass':True,'runtime_verified':False}
(P/'validation/package_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
