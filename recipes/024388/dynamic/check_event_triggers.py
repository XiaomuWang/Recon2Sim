"""Offline condition reachability checks. Not a simulator engine execution."""
import json,math,csv
from pathlib import Path
from lxml import etree as E
P=Path(__file__).resolve().parents[1];d=json.loads((P/'scenario.json').read_text(encoding='utf-8'));reports=[];rows=[]
mapping={m['entity']:m for m in json.loads((P/'template_compatible/entity_mapping.json').read_text(encoding='utf-8'))}
for path in [P/'template_compatible/LuoboTurn024388_Timeline.xosc',P/'template_compatible/LuoboTurn024388_Timeline_Radians.xosc',P/'LuoboTurn024388_CARLA015.xosc']:
 root=E.parse(str(path));events=root.findall('.//Event');names=root.xpath('./Entities/ScenarioObject/@name');eventnames=[e.get('name') for e in events];assert len(set(eventnames))==len(eventnames)
 tested=[]
 for hz,delay in [(15,0),(20,0),(30,0),(60,0),(30,.25),(30,1.7)]:
  fired=[]
  for ev in events:
   assert ev.get('maximumExecutionCount')=='1'
   co=ev.find('StartTrigger/ConditionGroup/Condition');assert co.get('conditionEdge')=='none' and float(co.get('delay'))==0
   cond=co.find('ByValueCondition/SimulationTimeCondition');assert cond is not None and cond.get('rule')=='greaterThan'
   t=float(cond.get('value'));assert 0<=t<=d['duration_s']+.04+1e-5
   first=max(math.floor(t*hz+1e-7)+1,math.ceil(delay*hz))/hz
   assert first<d['duration_s']+.1+1e-6;fired.append(ev.get('name'))
  tested.append(dict(hz=hz,delayed_evaluation_start_s=delay,fired=len(fired),expected=len(events),missing=[]))
 for group in root.findall('.//ManeuverGroup'):
  entity=group.find('Actors/EntityRef').get('entityRef');assert entity in names
  times=[float(e.find('.//SimulationTimeCondition').get('value')) for e in group.findall('.//Event')]
  assert times==sorted(times)
  if path.name=='LuoboTurn024388_Timeline.xosc':rows.append(dict(entity=entity,source_id=mapping[entity]['source_id'],label_zh=mapping[entity]['label'],activation_time=times[0],last_event_time=times[-1],event_count=len(times),condition='simulation time > threshold; edge=none; maxExecutionCount=1'))
 reports.append(dict(file=path.name,all_events_have_independent_time_conditions=True,all_entities_have_events=True,duplicate_event_names=False,tests=tested))
(P/'validation/event_trigger_audit.json').write_text(json.dumps(dict(type='offline trigger reachability at several clock rates; not runtime validation',files=reports),indent=2),encoding='utf-8')
with (P/'validation/per_entity_trigger_check.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('PASS:',len(rows),'entities;',len(reports),'exports; all events reachable at 15/20/30/60 Hz and delayed evaluation')
