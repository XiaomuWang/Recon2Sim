"""Evaluate every event's actual XML condition at multiple tick rates."""
import csv,json,math
from pathlib import Path
from xml.etree import ElementTree as E
P=Path(__file__).resolve().parents[1];root=E.parse(P/'GreenRail016955_Timeline.xosc').getroot();rows=[];events=[];act=root.find('.//Act')
end=float(act.find('StopTrigger/ConditionGroup/Condition/ByValueCondition/SimulationTimeCondition').get('value'))
assert not root.findall('.//CollisionCondition')
for obj in root.findall('Entities/ScenarioObject'):
 name=obj.get('name');props={p.get('name'):p.get('value') for p in obj.findall('.//Property')};groups=[g for g in root.findall('.//ManeuverGroup') if g.find('Actors/EntityRef').get('entityRef')==name];assert len(groups)==1
 evs=groups[0].findall('Maneuver/Event');activation=[];motion=[];stops=[]
 for ev in evs:
  assert ev.get('maximumExecutionCount')=='1';conditions=ev.findall('StartTrigger/ConditionGroup/Condition');assert len(conditions)==1
  co=conditions[0];assert co.get('conditionEdge')=='none' and float(co.get('delay'))==0
  st=co.find('ByValueCondition/SimulationTimeCondition');assert st is not None and st.get('rule')=='greaterThan';t=float(st.get('value'));assert 0<t<end
  assert not co.findall('.//EntityRef');events.append((ev.get('name'),t))
  if ev.find('.//TeleportAction') is not None:activation.append(t)
  if ev.find('.//AssignRouteAction') is not None:
   assert float(ev.find('.//AbsoluteTargetSpeed').get('value'))>0;motion.append(t)
  if float(ev.find('.//AbsoluteTargetSpeed').get('value'))==0:stops.append(t)
 assert len(activation)==1
 assert not motion or min(motion)>=activation[0]+.299
 rows.append(dict(entity=name,id=props['source_id'],label=props['label_zh'],activation_s=activation[0],motion_start_s=motion[0] if motion else None,event_count=len(evs),routes=len(motion),stop_conditions=stops))
simulations=[]
for hz in [10,20,30,60]:
 for initial in [.0,.017,.13]:
  seen={};pending=dict(events);n=math.ceil((end+.2-initial)*hz)
  for i in range(n+1):
   t=initial+i/hz
   if t>=end:break
   for name,threshold in list(pending.items()):
    if t>threshold:seen[name]=t;del pending[name]
  assert not pending,pending
  simulations.append(dict(hz=hz,initial_evaluation_s=initial,total_events=len(events),fired_once=len(seen),missing=0,max_tick_delay_s=max(seen[n]-t for n,t in events)))
with (P/'事件触发清单.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['目标ID','模板实体名','目标说明','出现条件（仿真秒）','首次行驶条件（仿真秒）','事件数','路线数','边沿类型','执行次数上限','依赖其他车辆'])
 for r in rows:w.writerow([r['id'],r['entity'],r['label'],'SimulationTime > '+str(r['activation_s']),'SimulationTime > '+str(r['motion_start_s']) if r['motion_start_s'] is not None else '静止目标，仅定位显示',r['event_count'],r['routes'],'none（持续满足）',1,'无'])
(P/'validation/trigger_audit.json').write_text(json.dumps(dict(pass_all=True,actors=len(rows),event_count=len(events),global_end_s=end,activation_offset_s=.2,motion_offset_s=.5,own_activation_lead_s=.3,all_events_have_time_condition=True,no_cross_actor_dependency=True,no_collision_global_early_stop=True,every_entity_has_one_teleport_activation=True,simulated_schedulers=simulations,per_actor=rows,scope='XML predicate dry run, not actual user platform or ScenarioRunner execution'),ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS:',len(rows),'actors,',len(events),'events,',len(simulations),'scheduler simulations; no missing activation')
