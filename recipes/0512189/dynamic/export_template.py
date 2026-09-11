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
PLAYBACK_OFFSET=.30
ACTIVATION_LEAD=.20
def staging(index):return {'x':-135+(index%6)*17,'y':-48-(index//6)*6,'z':.25,'h':0}

def sub(parent,tag,**attrs):return E.SubElement(parent,tag,{k:str(v) for k,v in attrs.items()})
def fmt(v):return format(float(v),'.9f').rstrip('0').rstrip('.') or '0'
def distance(a,b):return math.sqrt(sum((a[k]-b[k])**2 for k in ['x','y','z']))
def sample(a,t):return interpolate(a['samples'],min(a['end_t'],max(a['start_t'],t)))
def world(parent,s,unit):
 h=(s['h']+math.pi)%(2*math.pi)-math.pi
 if unit=='degrees':h=math.degrees(h)
 return sub(sub(parent,'Position'),'WorldPosition',x=fmt(s['x']),y=fmt(s['y']),z=fmt(s['z']),h=fmt(h),p=0,r=0)
def trigger(parent,tag,t,name):
 condition=sub(sub(sub(parent,tag),'ConditionGroup'),'Condition',name=name,delay=0,conditionEdge='none')
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
   obj.set('vehicleCategory','truck' if a['category'] in ['truck','gate_truck'] else 'bus' if a['category']=='bus' else 'van' if a['category']=='van' else 'motorbike' if a['category'] in ['motorcycle','tricycle','parked'] else 'car')
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
  if a['id']=='ego':sub(props,'Property',name='type',value='ego_vehicle')
 sb=sub(root,'Storyboard');actions=sub(sub(sb,'Init'),'Actions')
 actions.append(copy.deepcopy(template.find('Storyboard/Init/Actions/GlobalAction')))
 actions.find('.//TimeOfDay').set('dateTime',header.get('date'))
 actions.find('.//Weather').set('cloudState','overcast');actions.find('.//Sun').set('intensity','0.2')
 for index,a in enumerate(data['actors']):
  s=a['samples'][0] if a['start_t']==0 else staging(index)
  private=sub(actions,'Private',entityRef=mapping[a['id']]);world(sub(sub(private,'PrivateAction'),'TeleportAction'),dict(s,z=s['z']+.15),unit)
  sa=sub(sub(sub(private,'PrivateAction'),'LongitudinalAction'),'SpeedAction');sub(sa,'SpeedActionDynamics',dynamicsShape='step',value=0,dynamicsDimension='time');sub(sub(sa,'SpeedActionTarget'),'AbsoluteTargetSpeed',value=0)
 story=sub(sb,'Story',name='MyStory');act=sub(story,'Act',name='Act1');event_rows=[];run_rows=[]
 offset=PLAYBACK_OFFSET
 for index,a in enumerate(data['actors']):
  name=mapping[a['id']];group=sub(act,'ManeuverGroup',maximumExecutionCount=1,name=name+'_ManeuverGroup')
  sub(sub(group,'Actors',selectTriggeringEntities='false'),'EntityRef',entityRef=name)
  man=sub(group,'Maneuver',name=name+'_EventsManeuver');events=[]
  # The first template places each actor using a timed TeleportAction, including late entries.
  events.append({'t':a['start_t']+offset-ACTIVATION_LEAD,'pose':dict(a['samples'][0],z=a['samples'][0]['z']+.15),'speed':0.,'route':None,'type':'activation'})
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
  if a['end_t']<data['duration_s']:
   events.append({'t':a['end_t']+offset+.20,'pose':staging(index),'speed':0.,'route':None,'type':'exit_staging'})
  events.sort(key=lambda e:e['t'])
  for idx,e in enumerate(events):
   ev=sub(man,'Event',name=name+'_Event_'+str(idx+1),priority='parallel',maximumExecutionCount=1);action_index=0
   if e['pose'] is not None:
    teleport_action(ev,name+'_Action_'+str(idx)+'_0',e['pose'],unit);action_index+=1
   speed_action(ev,name+'_Action_'+str(idx)+'_'+str(action_index),e['speed']);action_index+=1
   if e['route']:route_action(ev,name+'_Action_'+str(idx)+'_'+str(action_index),e['route'],unit)
   trigger(ev,'StartTrigger',e['t'],'Cond_'+str(idx)+'_0_0_'+name)
   source_t=a['start_t'] if e['type']=='activation' else a['end_t'] if e['type']=='exit_staging' else e['t']-offset
   event_rows.append({'entity':name,'source_id':a['id'],'event':ev.get('name'),'simulation_t':round(e['t'],6),'source_video_t':round(source_t+data['source_video_start_s'],6),'type':e['type'],'target_speed_mps':e['speed']})
 trigger(act,'StartTrigger',0,'ActStartCondition')
 # Full-clip replay stops on time only, without inherited collision conditions.
 trigger(act,'StopTrigger',data['duration_s']+.60,'ActTimeout')
 trigger(sb,'StopTrigger',data['duration_s']+.60,'ScenarioTimeout')
 return root,event_rows,run_rows

def main():
 data=json.loads((P/'scenario.json').read_text(encoding='utf-8'));template=E.parse(str(P/'evidence/template.pretty.xml')).getroot()
 # The provided template only has vehicles. Add standard OSC 1.0 Pedestrian definitions
 # for two visibly walking people; keep their timed-event structure identical.
 pedtemplate=E.Element('OpenSCENARIO');ent=sub(pedtemplate,'Entities');so=sub(ent,'ScenarioObject',name='pedestrian_proto');pe=sub(so,'Pedestrian',name='walker.pedestrian.0001',model='walker.pedestrian.0001',mass=75,pedestrianCategory='pedestrian')
 bb=sub(pe,'BoundingBox');sub(bb,'Center',x=0,y=0,z=.85);sub(bb,'Dimensions',height=1.7,length=.5,width=.5);sub(pe,'Properties');so.append(copy.deepcopy(template.find('Entities/ScenarioObject/ObjectController')))
 mapping={};counter=0
 for a in data['actors']:
  if a['id']=='ego':mapping[a['id']]='ego_vehicle'
  else:counter+=1;mapping[a['id']]=('pedestrian_' if a['category']=='pedestrian' else 'vehicle_')+str(counter).zfill(3)
 schema=E.XMLSchema(E.parse(str(P/'validation/OpenSCENARIO.xsd')));report=[];outputs=[]
 for unit,suffix in [('degrees','Timeline'),('radians','Timeline_Radians')]:
  root,events,runs=build(data,template,pedtemplate,unit,mapping)
  path=O/('MeituanLane0512189_'+suffix+'.xosc');E.ElementTree(root).write(str(path),encoding='utf-8',xml_declaration=True,pretty_print=True)
  assert schema.validate(root),str(schema.error_log)
  tags=set(e.tag for e in root.iter());allowed=set(e.tag for e in template.iter())|{'Pedestrian','Private'};assert tags<=allowed
  names=set(root.xpath('./Entities/ScenarioObject/@name'));assert len(names)==len(data['actors']) and all(n in names for n in root.xpath('//@entityRef'))
  assert E.tostring(root.find('ParameterDeclarations'))==E.tostring(template.find('ParameterDeclarations'))
  assert not root.findall('.//FollowTrajectoryAction')
  for man in root.findall('.//Maneuver'):
   times=[float(e.find('.//SimulationTimeCondition').get('value')) for e in man.findall('Event')];assert times==sorted(times) and max(times)<=120.50
  # Compare route geometry in both files directly to the source coordinate envelope.
  for a in data['actors']:
   pose=root.find('.//Maneuver[@name="'+mapping[a['id']]+'_EventsManeuver"]/Event/Action/PrivateAction/TeleportAction/Position/WorldPosition')
   assert all(abs(float(pose.get(k))-a['samples'][0][k])<1e-6 for k in ['x','y'])
  report.append({'file':path.name,'schema_pass':True,'template_structure_pass':True,'additional_element':'Pedestrian for visible people; Private for explicit per-entity Init','headings':unit,'actors':len(names),'events':len(events),'routes':len(root.findall('.//Route')),'route_points':len(root.findall('.//Waypoint')),'runtime_verified':False});outputs.append(root)
 # Stock ScenarioRunner expects initial transforms in Init. Keep this extension separate
 # from the template-dialect files and use radians and the map name (cooked map workflow).
 sr=copy.deepcopy(outputs[1]);sr.find('FileHeader').set('description','Meituan video referenced reconstruction; standard RH metres and radians; CARLA 0.9.15 ScenarioRunner')
 for a in data['actors']:
  if a['end_t']<120:
   name=mapping[a['id']];man=sr.find('.//Maneuver[@name="'+name+'_EventsManeuver"]');ev=man.findall('Event')[-1]
   for action in ev.findall('Action'):ev.remove(action)
   action=E.Element('Action',name=name+'_Delete');ev.insert(0,action)
   ea=sub(sub(action,'GlobalAction'),'EntityAction',entityRef=name);sub(ea,'DeleteEntityAction')
 # Storyboard time stop is recognized by standard runner independently of Act completion.
 sr.remove(sr.find('Storyboard')) if False else None
 stop=sr.find('Storyboard/StopTrigger');sr.find('Storyboard').remove(stop);trigger(sr.find('Storyboard'),'StopTrigger',120.60,'ScenarioTimeout')
 assert schema.validate(sr),str(schema.error_log)
 path=P/'MeituanLane0512189_SR015.xosc';E.ElementTree(sr).write(str(path),encoding='utf-8',xml_declaration=True,pretty_print=True)
 report.append({'file':path.name,'schema_pass':True,'kind':'stock ScenarioRunner adapter; explicit Init poses, radians, end-of-track deletes','runtime_verified':False})
 shutil.copy2(O/'MeituanLane0512189_Timeline.xosc',P/'MeituanLane0512189_Timeline.xosc');shutil.copy2(O/'MeituanLane0512189_Timeline_Radians.xosc',P/'MeituanLane0512189_Timeline_Radians.xosc')
 (O/'timeline_events.json').write_text(json.dumps({'motion_time_offset_s':PLAYBACK_OFFSET,'activation_lead_s':ACTIVATION_LEAD,'events':events,'runs':runs},ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'entity_mapping.json').write_text(json.dumps([{'source_id':a['id'],'entity':mapping[a['id']],'label':a['label_zh'],'native_blueprint':a['blueprint_candidates'][0],'optional_custom_prop':a['preferred_custom_blueprint'],'source_front_seconds':[a['start_t'],a['end_t']]} for a in data['actors']],ensure_ascii=False,indent=2),encoding='utf-8')
 (P/'validation/template_validation.json').write_text(json.dumps({'template_sha256':hashlib.sha256((P/'evidence/template.pretty.xml').read_bytes()).hexdigest(),'checks':report,'runtime_verified':False},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

