"""Export the user's sutpc time-event dialect (first template), plus a radians variant.

No FollowTrajectoryAction, AddEntityAction, distance trigger, or external controller.
Routes and time-indexed speed targets approximate the source poses under the platform driver.
"""
import argparse,copy,hashlib,json,math,shutil,sys,zipfile
from pathlib import Path
from datetime import datetime
from lxml import etree as E
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from replay_carla import interpolate
O=P/'template_compatible';O.mkdir(exist_ok=True)

def sub(parent,tag,**attrs):return E.SubElement(parent,tag,{k:str(v) for k,v in attrs.items()})
def fmt(v):return format(float(v),'.9f').rstrip('0').rstrip('.') or '0'
def distance(a,b):return math.sqrt(sum((a[k]-b[k])**2 for k in ['x','y','z']))
def sample(a,t):return interpolate(a['samples'],min(a['end_t'],max(a['start_t'],t)))
def world(parent,s,unit):
 h=(s['h']+math.pi)%(2*math.pi)-math.pi
 if unit=='degrees':h=math.degrees(h)
 return sub(sub(parent,'Position'),'WorldPosition',x=fmt(s['x']),y=fmt(s['y']),z=fmt(s['z']),h=fmt(h),p=0,r=0)
def trigger(parent,tag,t,name):
 condition=sub(sub(sub(parent,tag),'ConditionGroup'),'Condition',name=name,delay=0,conditionEdge='rising')
 sub(sub(condition,'ByValueCondition'),'SimulationTimeCondition',value=fmt(t),rule='greaterThan')
def speed_action(event,name,value):
 action=sub(event,'Action',name=name);speed=sub(sub(sub(action,'PrivateAction'),'LongitudinalAction'),'SpeedAction')
 sub(speed,'SpeedActionDynamics',dynamicsShape='linear',value=0,dynamicsDimension='time')
 sub(sub(speed,'SpeedActionTarget'),'AbsoluteTargetSpeed',value=fmt(value))
def teleport_action(event,name,s,unit):
 world(sub(sub(sub(event,'Action',name=name),'PrivateAction'),'TeleportAction'),s,unit)
def route_action(event,name,points,unit):
 route=sub(sub(sub(sub(sub(event,'Action',name=name),'PrivateAction'),'RoutingAction'),'AssignRouteAction'),'Route',closed='false',name='route_event')
 for s in points:world(sub(route,'Waypoint',routeStrategy='shortest'),s,unit)

def motion_runs(a):
 ss=a['samples'];runs=[];start=None
 for i in range(len(ss)-1):
  moving=distance(ss[i],ss[i+1])/(ss[i+1]['t']-ss[i]['t'])>.03
  if moving and start is None:start=i
  if not moving and start is not None:runs.append((ss[start]['t'],ss[i]['t']));start=None
 if start is not None:runs.append((ss[start]['t'],ss[-1]['t']))
 return runs
def path_samples(a,start,end):
 ss=[sample(a,start)]+[s for s in a['samples'] if start<s['t']<end]+[sample(a,end)]
 return ss
def route_points(a,start,end):
 ss=path_samples(a,start,end);pts=[ss[0]]
 for s in ss[1:-1]:
  if distance(pts[-1],s)>=.5:pts.append(s)
 if distance(pts[-1],ss[-1])>1e-7:pts.append(ss[-1])
 if len(pts)<2:pts.append(ss[-1])
 return pts
def mean_speed(a,start,end):
 ss=path_samples(a,start,end)
 return sum(distance(x,y) for x,y in zip(ss,ss[1:]))/(end-start)

def build(data,template,ped_template,unit,mapping):
 root=E.Element('OpenSCENARIO')
 header=copy.deepcopy(template.find('FileHeader'));header.set('date',datetime.now().replace(microsecond=0).isoformat());root.append(header)
 root.append(copy.deepcopy(template.find('ParameterDeclarations')));root.append(copy.deepcopy(template.find('CatalogLocations')))
 sub(sub(root,'RoadNetwork'),'LogicFile',filepath=data['map_name'])
 entities=sub(root,'Entities');vproto=template.find('Entities/ScenarioObject');pproto=ped_template.find("Entities/ScenarioObject[Pedestrian]")
 for a in data['actors']:
  entity=copy.deepcopy(pproto if a['category']=='pedestrian' else vproto);entity.set('name',mapping[a['id']]);entities.append(entity)
  obj=entity.find('Pedestrian') if a['category']=='pedestrian' else entity.find('Vehicle')
  obj.set('name',a['blueprint_candidates'][0]);dims=a['dimensions_m']
  if a['category']=='pedestrian':obj.set('model',a['blueprint_candidates'][0])
  else:
   obj.set('vehicleCategory','truck' if a['category'] in ['truck','gate_truck'] else 'motorbike' if a['category'] in ['motorcycle','tricycle','parked'] else 'car')
   ax=obj.find('Axles')
   for axle in ax:
    axle.set('positionX',fmt(dims['length']*(.3 if axle.tag=='FrontAxle' else -.3)))
    axle.set('trackWidth',fmt(dims['width']*.8))
  center=obj.find('BoundingBox/Center');center.set('x','0');center.set('y','0');center.set('z',fmt(dims['height']/2))
  dim=obj.find('BoundingBox/Dimensions')
  for k,v in dims.items():dim.set(k,fmt(v))
  props=obj.find('Properties')
  if props is None:props=sub(obj,'Properties')
  if a.get('color'):sub(props,'Property',name='color',value=a['color'])
 sb=sub(root,'Storyboard');actions=sub(sub(sb,'Init'),'Actions')
 actions.append(copy.deepcopy(template.find('Storyboard/Init/Actions/GlobalAction')))
 actions.find('.//TimeOfDay').set('dateTime',header.get('date'))
 story=sub(sb,'Story',name='MyStory');act=sub(story,'Act',name='Act1');event_rows=[];run_rows=[]
 offset=.04
 for a in data['actors']:
  name=mapping[a['id']];group=sub(act,'ManeuverGroup',maximumExecutionCount=1,name=name+'_ManeuverGroup')
  sub(sub(group,'Actors',selectTriggeringEntities='false'),'EntityRef',entityRef=name)
  man=sub(group,'Maneuver',name=name+'_EventsManeuver');events=[]
  # The first template places each actor using a timed TeleportAction, including late entries.
  events.append({'t':a['start_t'],'pose':a['samples'][0],'speed':0.,'route':None,'type':'activation'})
  runs=motion_runs(a)
  for begin,end in runs:
   if end-begin<1e-5:continue
   times={begin,end}
   times.update(round(begin+i*.5,6) for i in range(1,int((end-begin)/.5)+1) if begin+i*.5<end)
   times.update(float(k[0])-data['source_video_start_s'] for k in a['source_keyframes'] if begin<float(k[0])-data['source_video_start_s']<end)
   ts=sorted(times)
   for i,(ta,tb) in enumerate(zip(ts,ts[1:])):
    events.append({'t':ta+offset,'pose':None,'speed':mean_speed(a,ta,tb),'route':route_points(a,begin,end) if i==0 else None,'type':'motion_start' if i==0 else 'speed_update'})
   events.append({'t':end+offset,'pose':None,'speed':0.,'route':None,'type':'stop'})
   run_rows.append({'id':a['id'],'begin_replay_t':begin,'end_replay_t':end,'route_point_count':len(route_points(a,begin,end))})
  events.sort(key=lambda e:e['t'])
  for idx,e in enumerate(events):
   ev=sub(man,'Event',name=name+'_Event_'+str(idx+1),priority='parallel');action_index=0
   if e['pose'] is not None:
    teleport_action(ev,name+'_Action_'+str(idx)+'_0',e['pose'],unit);action_index+=1
   speed_action(ev,name+'_Action_'+str(idx)+'_'+str(action_index),e['speed']);action_index+=1
   if e['route']:route_action(ev,name+'_Action_'+str(idx)+'_'+str(action_index),e['route'],unit)
   trigger(ev,'StartTrigger',e['t'],'Cond_'+str(idx)+'_0_0_'+name)
   event_rows.append({'entity':name,'source_id':a['id'],'event':ev.get('name'),'simulation_t':round(e['t'],6),'source_video_t':round(e['t']-(0 if e['type']=='activation' else offset)+52,6),'type':e['type'],'target_speed_mps':e['speed']})
 trigger(act,'StartTrigger',0,'ActStartCondition')
 stop=copy.deepcopy(template.find('Storyboard/Story/Act/StopTrigger'))
 stop.find('.//SimulationTimeCondition').set('value',fmt(data['duration_s']+.1));act.append(stop)
 sub(sb,'StopTrigger')
 return root,event_rows,run_rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--template',type=Path,default=Path(r'C:\Users\Administrator\Desktop\模板\scenario - 2026-09-08T142648.948.xosc'));ap.add_argument('--pedestrian-template',type=Path,default=Path(r'C:\Users\Administrator\Desktop\模板\scenario - 2026-09-08T142654.518.xosc'));args=ap.parse_args()
 templates=[E.parse(str(args.template)).getroot(),E.parse(str(args.pedestrian_template)).getroot()]
 data=json.loads((P/'scenario.json').read_text(encoding='utf-8'));mapping={};nv=np=0
 for a in data['actors']:
  if a['id']=='ego':name='ego_vehicle'
  elif a['category']=='pedestrian':np+=1;name='pedestrian_%03d'%np
  else:nv+=1;name='vehicle_%03d'%nv
  mapping[a['id']]=name
 schema=E.XMLSchema(E.parse(str(P/'validation/OpenSCENARIO.xsd')));report={'primary_template':args.template.name,'timeline_trigger':'SimulationTimeCondition','default_heading_unit':'degrees, matching the first supplied template; platform dialect, not standard OSC angular semantics','runtime_verified':False,'files':[]}
 template_tags=set(e.tag for t in templates for e in t.iter())
 for unit,suffix in [('degrees','Timeline'),('radians','Timeline_Radians')]:
  root,events,runs=build(data,*templates,unit,mapping);path=O/('NanshanGate014346_'+suffix+'.xosc')
  E.ElementTree(root).write(str(path),encoding='utf-8',xml_declaration=True,pretty_print=True)
  ok=schema.validate(root);assert ok,str(schema.error_log)
  assert set(e.tag for e in root.iter())<=template_tags
  assert not root.findall('.//FollowTrajectoryAction') and not root.findall('.//ReachPositionCondition')
  assert len(root.findall('.//Event'))==len(root.findall('.//Event/StartTrigger/ConditionGroup/Condition/ByValueCondition/SimulationTimeCondition'))
  names=set(root.xpath('./Entities/ScenarioObject/@name'));assert len(names)==10
  assert all(ref in names for ref in root.xpath('//@entityRef'))
  assert root.find('RoadNetwork/LogicFile').get('filepath')==data['map_name']
  assert E.tostring(root.find('ParameterDeclarations'))==E.tostring(templates[0].find('ParameterDeclarations'))
  for man in root.findall('.//Maneuver'):
   ts=[float(e.find('StartTrigger/ConditionGroup/Condition/ByValueCondition/SimulationTimeCondition').get('value')) for e in man.findall('Event')]
   assert ts==sorted(ts) and max(ts)<=107.04+1e-6
  for a in data['actors']:
   name=mapping[a['id']];pose=root.find('.//Maneuver[@name="'+name+'_EventsManeuver"]/Event/Action/PrivateAction/TeleportAction/Position/WorldPosition')
   assert all(abs(float(pose.get(k))-a['samples'][0][k])<1e-7 for k in ['x','y','z'])
   h=float(pose.get('h'));h=math.radians(h) if unit=='degrees' else h
   assert abs((h-a['samples'][0]['h']+math.pi)%(2*math.pi)-math.pi)<1e-7
  row={'file':path.name,'heading_unit':unit,'XML_schema_pass':ok,'template_tag_subset_pass':True,'entity_references_pass':True,'time_order_pass':True,'initial_pose_roundtrip_pass':True,'entities':len(names),'events':len(events),'routes':len(root.findall('.//Route')),'waypoints':len(root.findall('.//Waypoint')),'runtime_verified':False};report['files'].append(row)
 (O/'timeline_events.json').write_text(json.dumps({'motion_time_offset_s':.04,'events':events,'moving_intervals':runs},ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'entity_mapping.json').write_text(json.dumps([{'source_id':a['id'],'entity':mapping[a['id']],'label':a['label_zh'],'blueprint':a['blueprint_candidates'][0],'active_source_video_s':[52+a['start_t'],52+a['end_t']]} for a in data['actors']],ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 shutil.copy2(P/'NanshanGate014346.xodr',O/'NanshanGate014346.xodr')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
