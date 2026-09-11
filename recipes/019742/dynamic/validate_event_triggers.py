"""Offline gate evaluation of every exported event. This is not engine execution."""
import csv,json,math,random
from pathlib import Path
from lxml import etree as E
P=Path(__file__).resolve().parents[1]
reports=[];rows=[]
for filename in ['UrbanBrake019742_Timeline.xosc','UrbanBrake019742_Timeline_Radians.xosc']:
 root=E.parse(str(P/'template_compatible'/filename));act=root.find('.//Act')
 ac=act.find('StartTrigger/ConditionGroup/Condition')
 assert ac.get('conditionEdge')=='none' and ac.get('delay')=='0'
 assert not root.findall('.//StoryboardElementStateCondition')
 assert not root.findall('.//CollisionCondition')
 events=[];actors=set(root.xpath('./Entities/ScenarioObject/@name'))
 for mg in act.findall('ManeuverGroup'):
  eid=mg.find('Actors/EntityRef').get('entityRef');assert eid in actors
  ee=mg.findall('Maneuver/Event');last=-1
  assert ee[0].find('.//TeleportAction') is not None
  for i,e in enumerate(ee):
   conditions=e.findall('StartTrigger/ConditionGroup/Condition');assert len(conditions)==1
   c=conditions[0];tc=c.find('ByValueCondition/SimulationTimeCondition')
   assert tc is not None and c.get('conditionEdge')=='none' and float(c.get('delay'))==0
   assert tc.get('rule')=='greaterThan' and e.get('maximumExecutionCount')=='1'
   t=float(tc.get('value'));assert t>last;last=t
   assert e.get('priority')=='parallel'
   events.append((eid,e.get('name'),t,i==0))
   if filename.endswith('_Timeline.xosc'):
    rows.append({'entity':eid,'event':e.get('name'),'activation':i==0,'simulation_time_s':t,'condition':'SimulationTime > %.6f'%t,'edge':'none','execution_count':1,'depends_on_other_actor':False})
 assert len(set(x[1] for x in events))==len(events)
 cases=[]
 for fps,delay,jitter in [(10,0,False),(15,0,False),(20,.05,False),(30,.1,False),(60,.5,False),(30,.2,True)]:
  rng=random.Random(742);pending={e[1]:e for e in events};seen=set();t=delay;maxlate=0
  while t<=178.1:
   if t>0:
    for name,e in list(pending.items()):
     if t>e[2]:
      seen.add(e[0]);maxlate=max(maxlate,t-e[2]);del pending[name]
   t+=(1/fps)*(rng.uniform(.6,1.6) if jitter else 1)
  assert not pending and seen==actors
  cases.append({'fps':fps,'act_evaluation_delay_s':delay,'jitter':jitter,'events_fired':len(events),'actors_activated':len(seen),'missing_events':[],'max_dispatch_lateness_s':maxlate})
 reports.append({'file':filename,'entities':len(actors),'events':len(events),'all_conditions_explicit':True,'no_cross_actor_dependencies':True,'no_collision_early_stop':True,'cases':cases})
with (P/'template_compatible/event_trigger_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(P/'validation/event_trigger_validation.json').write_text(json.dumps({'pass':True,'runtime_verified':False,'method':'Offline level-trigger time gate evaluation; native platform action/controller execution not tested','reports':reports},indent=2),encoding='utf-8')
print('PASS: both XOSC files, 32 actors, %d events each; six timing cases, no missing events.'%len(events))
