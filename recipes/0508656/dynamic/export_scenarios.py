# -*- coding: utf-8 -*-
"""Export the supplied time-event structure with independent, level-triggered actors."""
import copy,csv,hashlib,json,math,sys
from pathlib import Path
from lxml import etree as E
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from replay_carla import interpolate

def sub(parent,tag,**kw):return E.SubElement(parent,tag,{k:str(v) for k,v in kw.items()})
def f(v):return ('%.9f'%float(v)).rstrip('0').rstrip('.') or '0'
def dist(a,b):return math.sqrt(sum((a[k]-b[k])**2 for k in ('x','y','z')))
def sample(a,t):return interpolate(a['samples'],min(a['end_t'],max(a['start_t'],t)))
def pos(p,s,unit):
 h=(s['h']+math.pi)%(2*math.pi)-math.pi
 if unit=='degrees':h=math.degrees(h)
 return sub(sub(p,'Position'),'WorldPosition',x=f(s['x']),y=f(s['y']),z=f(s['z']),h=f(h),p=0,r=0)
def trigger(p,tag,t,name):
 # Level condition remains true if the Act becomes ready after the threshold.
 c=sub(sub(sub(p,tag),'ConditionGroup'),'Condition',name=name,delay=0,conditionEdge='none')
 sub(sub(c,'ByValueCondition'),'SimulationTimeCondition',value=f(t),rule='greaterThan')
def speed(p,v):
 s=sub(sub(p,'LongitudinalAction'),'SpeedAction')
 sub(s,'SpeedActionDynamics',dynamicsShape='linear',value=0,dynamicsDimension='time')
 sub(sub(s,'SpeedActionTarget'),'AbsoluteTargetSpeed',value=f(v))
def path(a,t0,t1):return [sample(a,t0)]+[s for s in a['samples'] if t0<s['t']<t1]+[sample(a,t1)]
def route(a,t0,t1):
 ss=path(a,t0,t1);r=[ss[0]]
 for s in ss[1:-1]:
  if dist(r[-1],s)>=.5:r.append(s)
 if dist(r[-1],ss[-1])>1e-8:r.append(ss[-1])
 return r
def runs(a):
 ss=a['samples'];out=[];begin=None
 for i in range(len(ss)-1):
  moving=dist(ss[i],ss[i+1])/(ss[i+1]['t']-ss[i]['t'])>.03
  if moving and begin is None:begin=ss[i]['t']
  if not moving and begin is not None:out.append((begin,ss[i]['t']));begin=None
 if begin is not None:out.append((begin,ss[-1]['t']))
 return out

def staging_positions(data):
 sys.path.insert(0,str((P/'runtime').resolve()))
 import carla
 m=carla.Map(data['map_name'],(P/data['xodr_file']).read_text(encoding='utf-8'))
 points=[]
 for lane in [-3,-2,2,3]:
  for s in [10,20,30,40,50,60,70]:
   w=m.get_waypoint_xodr(40,lane,s)
   assert w is not None
   p=w.transform
   points.append({'x':p.location.x,'y':-p.location.y,'z':.25,'h':-math.radians(p.rotation.yaw),'road':40,'lane':lane,'road_s':s})
 return {a['id']:points[i] for i,a in enumerate(data['actors'])}

def build(data,template,unit,stock,stages):
 root=E.Element('OpenSCENARIO');head=copy.deepcopy(template.find('FileHeader'));head.set('date','2026-09-08T16:00:00');root.append(head)
 for tag in ['ParameterDeclarations','CatalogLocations']:root.append(copy.deepcopy(template.find(tag)))
 sub(sub(root,'RoadNetwork'),'LogicFile',filepath=data['map_name'])
 entities=sub(root,'Entities');proto=template.find('Entities/ScenarioObject')
 mapping={a['id']:('ego_vehicle' if a['id']=='ego' else a['id']) for a in data['actors']}
 for a in data['actors']:
  entity=copy.deepcopy(proto);entity.set('name',mapping[a['id']]);entities.append(entity)
  obj=entity.find('Vehicle');dims=a['dimensions_m']
  if a['category']=='pedestrian':
   entity.remove(obj);obj=E.Element('Pedestrian',name=a['blueprint_candidates'][0],model=a['blueprint_candidates'][0],mass='75',pedestrianCategory='pedestrian');entity.insert(0,obj)
   box=sub(obj,'BoundingBox');sub(box,'Center',x=0,y=0,z=f(dims['height']/2));sub(box,'Dimensions',**{k:f(v) for k,v in dims.items()});sub(obj,'Properties')
  else:
   obj.set('name',a['blueprint_candidates'][0]);obj.set('vehicleCategory',{'truck':'truck','bus':'bus','motorcycle':'motorbike'}.get(a['category'],'car'))
   obj.find('BoundingBox/Center').attrib.update({'x':'0','y':'0','z':f(dims['height']/2)})
   obj.find('BoundingBox/Dimensions').attrib.update({k:f(v) for k,v in dims.items()})
   for ax in obj.find('Axles'):
    ax.set('positionX',f(dims['length']*(.3 if ax.tag=='FrontAxle' else -.3)));ax.set('trackWidth',f(dims['width']*.8))
  props=obj.find('Properties')
  for c in list(props):props.remove(c)
  if a.get('color'):sub(props,'Property',name='color',value=a['color'])
  if a['id']=='ego':sub(props,'Property',name='type',value='ego_vehicle')
 sb=sub(root,'Storyboard');init=sub(sub(sb,'Init'),'Actions')
 init.append(copy.deepcopy(template.find('Storyboard/Init/Actions/GlobalAction')))
 if stock:
  init.find('.//Sun').set('intensity','0.85');init.find('.//TimeOfDay').set('animation','false')
 # All entities have valid, separate initial positions. Late entities wait away
 # from the filmed route on north road 40, then enter through their own event.
 for a in data['actors']:
  pr=sub(init,'Private',entityRef=mapping[a['id']]);pose=a['samples'][0] if a['start_t']==0 else stages[a['id']]
  pos(sub(sub(pr,'PrivateAction'),'TeleportAction'),pose,unit)
  speed(sub(pr,'PrivateAction'),0)
 story=sub(sb,'Story',name='MyStory');act=sub(story,'Act',name='Act1');rows=[]
 for a in data['actors']:
  name=mapping[a['id']];group=sub(act,'ManeuverGroup',maximumExecutionCount=1,name=name+'_ManeuverGroup')
  sub(sub(group,'Actors',selectTriggeringEntities='false'),'EntityRef',entityRef=name)
  man=sub(group,'Maneuver',name=name+'_EventsManeuver')
  events=[dict(t=a['start_t'],kind='enter',pose=a['samples'][0],speed=0,route=None)]
  for begin,end in runs(a):
   times={begin,end};times.update(round(begin+i*.5,6) for i in range(1,int((end-begin)/.5)+1) if begin+i*.5<end)
   times.update(float(k[0]) for k in a['source_keyframes'] if begin<float(k[0])<end);ts=sorted(times)
   for i,(ta,tb) in enumerate(zip(ts,ts[1:])):
    ss=path(a,ta,tb);v=sum(dist(x,y) for x,y in zip(ss,ss[1:]))/(tb-ta)
    events.append(dict(t=ta+.10,kind='drive' if i==0 else 'speed',pose=None,speed=v,route=route(a,begin,end) if i==0 else None))
   events.append(dict(t=end+.10,kind='stop',pose=None,speed=0,route=None))
  if a['end_t']<data['duration_s']:events.append(dict(t=a['end_t']+.20,kind='retire',pose=stages[a['id']],speed=0,route=None))
  for i,e in enumerate(sorted(events,key=lambda e:e['t'])):
   en=name+'_%04d_%s'%(i,e['kind']);ev=sub(man,'Event',name=en,priority='parallel',maximumExecutionCount=1)
   if e['pose'] is not None:pos(sub(sub(sub(ev,'Action',name=en+'_place'),'PrivateAction'),'TeleportAction'),e['pose'],unit)
   speed(sub(sub(ev,'Action',name=en+'_speed'),'PrivateAction'),e['speed'])
   if e['route']:
    rt=sub(sub(sub(sub(sub(ev,'Action',name=en+'_route'),'PrivateAction'),'RoutingAction'),'AssignRouteAction'),'Route',name=en+'_path',closed='false')
    for s in e['route']:pos(sub(rt,'Waypoint',routeStrategy='shortest'),s,unit)
   trigger(ev,'StartTrigger',e['t'],en+'_clock')
   rows.append(dict(entity=name,source_id=a['id'],event=en,t=e['t'],kind=e['kind'],speed_mps=e['speed']))
 trigger(act,'StartTrigger',0,'ActStartClock')
 # Collision-based Act stops from the example are intentionally replaced with
 # the replay duration. A minor contact must not suppress every late vehicle.
 trigger(act,'StopTrigger',data['duration_s']+.5,'ActEndClock')
 trigger(sb,'StopTrigger',data['duration_s']+.6,'ScenarioEndClock')
 return root,rows

def audit(root,data,unit,rows):
 schema=E.XMLSchema(E.parse(str(P/'validation/OpenSCENARIO.xsd')));schema.assertValid(root)
 names=root.xpath('./Entities/ScenarioObject/@name');assert len(names)==len(set(names))==len(data['actors'])
 assert all(n in names for n in root.xpath('//@entityRef'))
 assert len(root.findall('./Storyboard/Init/Actions/Private'))==len(names)
 assert not root.findall('.//StoryboardElementStateCondition') and not root.findall('.//CollisionCondition')
 out=[]
 for a in data['actors']:
  n='ego_vehicle' if a['id']=='ego' else a['id'];rr=[r for r in rows if r['entity']==n]
  assert rr[0]['kind']=='enter' and abs(rr[0]['t']-a['start_t'])<1e-8
  assert all(rr[i]['t']<=rr[i+1]['t'] for i in range(len(rr)-1))
  assert max(r['t'] for r in rr)<data['duration_s']+.5
  # Model the level trigger at different tick sizes, including a delayed Act
  # start. Every event must become true after its parent becomes active.
  for dt in [1/30,.05,.1]:
   fired=set()
   for tick in range(math.ceil((data['duration_s']+.5)/dt)):
    t=tick*dt
    if t<.2:continue
    for r in rr:
     if t>r['t']:fired.add(r['event'])
   assert len(fired)==len(rr),(n,dt,len(fired),len(rr))
  out.append({'entity':n,'label_zh':a['label_zh'],'enter_s':a['start_t'],'last_visible_s':a['end_t'],'event_count':len(rr),'moving':bool(runs(a)),'independent_clock':True,'init_position':True,'trigger_reachability_pass':True})
 return out

def main():
 data=json.loads((P/'scenario.json').read_text(encoding='utf-8'));template=E.parse(str(P/'evidence/template.xosc')).getroot();stages=staging_positions(data);O=P/'template_compatible';O.mkdir(exist_ok=True)
 reports=[]
 for unit,suffix,stock in [('degrees','Timeline',False),('radians','Timeline_Radians',False),('radians','CARLA0915',True)]:
  root,rows=build(data,template,unit,stock,stages);result=audit(root,data,unit,rows)
  assert E.tostring(root.find('ParameterDeclarations'))==E.tostring(template.find('ParameterDeclarations'))
  file=O/(data['map_name']+'_'+suffix+'.xosc');E.ElementTree(root).write(str(file),pretty_print=True,encoding='utf-8',xml_declaration=True)
  reports.append({'file':file.name,'unit':unit,'schema_valid':True,'actors':len(result),'events':len(rows),'all_events_reachable':True,'runtime_verified':False})
 (O/'timeline_events.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'entity_trigger_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 (P/'validation/xosc_validation.json').write_text(json.dumps({'files':reports,'staging_positions':stages,'collision_stop_removed':True,'trigger_model_only_not_server_runtime':True},ensure_ascii=False,indent=2),encoding='utf-8')
 with (O/'逐目标触发清单.csv').open('w',encoding='utf-8-sig',newline='') as f1:
  w=csv.DictWriter(f1,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
 print(json.dumps(reports,indent=2))
if __name__=='__main__':main()
