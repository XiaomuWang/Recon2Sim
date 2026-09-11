"""Validate XML conditions, timeline roundtrip, map support and v0.9.15 coordinate semantics."""
import ast,json,math,sys,hashlib
from pathlib import Path
from lxml import etree as E
import numpy as np
import carla
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));from replay_carla import read_scene,interpolate
from play_xosc_carla import decode_xosc
d,xodr=read_scene(P/'scenario.json');mapping=json.loads((P/'entity_mapping.json').read_text(encoding='utf8'));idmap={r['source_id']:('ego' if r['entity']=='ego_vehicle' else r['entity']) for r in mapping}
decoded,_=decode_xosc(P/'RainJunctionANA031_Timeline.xosc','degrees');radians,_=decode_xosc(P/'RainJunctionANA031_Timeline_Radians.xosc','radians')
by={a['id']:a for a in decoded['actors']};reports=[]
for a in d['actors']:
 b=by[idmap[a['id']]];err=[]
 for t in np.arange(a['start_t'],a['end_t']+.00001,.1):
  s=interpolate(a['samples'],t);q=interpolate(b['samples'],t+.25);err.append(math.hypot(s['x']-q['x'],s['y']-q['y']))
 reports.append({'id':a['id'],'max_timeline_vs_source_xy_m':max(err),'mean_timeline_vs_source_xy_m':float(np.mean(err))})
assert max(r['max_timeline_vs_source_xy_m'] for r in reports)<.20,reports
unit_err=0.
for a,b in zip(decoded['actors'],radians['actors']):
 for p,q in zip(a['samples'],b['samples']):unit_err=max(unit_err,abs(p['x']-q['x']),abs(p['y']-q['y']),abs((p['h']-q['h']+math.pi)%(2*math.pi)-math.pi))
assert unit_err<1e-6
m=carla.Map(d['map_name'],xodr.read_text());off=[];tested=0
for a in d['actors']:
 if a['category']=='pedestrian':continue
 for s in a['samples'][::6]:
  tested+=1;wp=m.get_waypoint(carla.Location(x=s['x'],y=-s['y'],z=0),project_to_road=False,lane_type=carla.LaneType.Driving)
  if wp is None:off.append([a['id'],s['t'],s['x'],s['y']])
assert not off,off[:10]
root=E.parse(str(P/'RainJunctionANA031_CARLA0915.xosc')).getroot();events=root.findall('.//Event');names={e.get('name') for e in events};assert len(names)==len(events)
trigger_rows=[]
for group in root.findall('.//ManeuverGroup'):
 entity=group.find('Actors/EntityRef').get('entityRef');evs=group.findall('Maneuver/Event');activation=evs[0].get('name');assert evs[0].find('.//TeleportAction') is not None
 assert root.find("Storyboard/Init/Actions/Private[@entityRef='%s']"%entity) is not None
 for i,e in enumerate(evs):
  assert e.get('maximumExecutionCount')=='1'
  conditions=e.findall('StartTrigger/ConditionGroup/Condition');assert all(c.get('conditionEdge')=='none' for c in conditions)
  assert e.find('.//SimulationTimeCondition') is not None
  guards=e.findall('.//StoryboardElementStateCondition')
  if i:assert len(guards)==1 and guards[0].get('storyboardElementRef')==activation and guards[0].get('state')=='completeState'
  else:assert not guards
 trigger_rows.append({'entity':entity,'activation_event':activation,'activation_s':float(evs[0].find('.//SimulationTimeCondition').get('value')),'events':len(evs),'explicit_init':True,'motion_requires_own_activation':True})
# Discrete scheduling model tests level conditions even when first observation skips zero.
schedules=[]
for step,start,skip in [(.05,0.,False),(.10,.20,False),(.05,0.,True)]:
 completed={};first_motion={}
 for t in np.arange(start,64.4,step):
  if skip and (24.9<t<25.2 or 31.05<t<31.25):continue
  ready=[]
  for e in events:
   name=e.get('name')
   if name in completed:continue
   if t<=float(e.find('.//SimulationTimeCondition').get('value')):continue
   guard=e.find('.//StoryboardElementStateCondition')
   if guard is not None and guard.get('storyboardElementRef') not in completed:continue
   ready.append(name)
  for n in ready:completed[n]=float(t)
 assert len(completed)==len(events),(step,start,len(completed),len(events))
 schedules.append({'step_s':step,'first_observation_s':start,'skipped_boundary_observations':skip,'events_reached':len(completed),'total_events':len(events),'pass':True})
src=P/'validation/reference/openscenario_parser.py';tree=ast.parse(src.read_text(encoding='utf8'));cl=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='OpenScenarioParser');fn=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='convert_position_to_transform');fn.decorator_list=[]
module=ast.Module(body=[fn],type_ignores=[]);ns={'carla':carla,'math':math,'ParameterRef':lambda x:float(x),'OpenScenarioParser':type('Parser',(object,),{'use_carla_coordinate_system':False})};exec(compile(ast.fix_missing_locations(module),str(src),'exec'),ns)
maxerr=0
for n in root.findall('.//Position'):
 wp=n.find('WorldPosition');tf=ns['convert_position_to_transform'](n);maxerr=max(maxerr,abs(tf.location.x-float(wp.get('x'))),abs(tf.location.y+float(wp.get('y'))),abs(tf.rotation.yaw+math.degrees(float(wp.get('h')))))
assert maxerr<.0001
report={'trajectory_samples':sum(len(a['samples']) for a in d['actors']),'vehicle_surface_samples_checked':tested,'off_driving_surface':off,'template_motion_offset_s':.25,'timeline_roundtrip':reports,'degrees_radians_max_difference':unit_err,'official_v0915_position_method_max_error':maxerr,'official_parser_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'per_entity_trigger_checks':trigger_rows,'trigger_schedule_tests':schedules,'scope':'XML, simple scheduling model, kinematic and map checks plus isolated official parser method. No CARLA 0.9.15 engine or controller execution.','runtime_verified':False}
(P/'validation/delivery_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
