"""Template event dialect + radians variant + stock ScenarioRunner 0.9.15 setup."""
from pathlib import Path
import copy,json,math,sys,hashlib,shutil
from lxml import etree as E
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));from replay_carla import interpolate
d=json.loads((P/'scenario.json').read_text(encoding='utf8'));template=E.parse(str(P/'evidence/source_template.xosc')).getroot()
schema=E.XMLSchema(E.parse(str(P/'validation/OpenSCENARIO.xsd')))
def sub(parent,tag,**kw):return E.SubElement(parent,tag,{k:str(v) for k,v in kw.items()})
def f(v):return f'{float(v):.8f}'.rstrip('0').rstrip('.') or '0'
def world(p,s,unit,zoff=0):
 h=(s['h']+math.pi)%(2*math.pi)-math.pi
 return sub(sub(p,'Position'),'WorldPosition',x=f(s['x']),y=f(s['y']),z=f(s['z']+zoff),h=f(math.degrees(h) if unit=='degrees' else h),p=0,r=0)
def trigger(p,tag,t,name,guard=None):
 group=sub(sub(p,tag),'ConditionGroup');c=sub(group,'Condition',name=name,delay=0,conditionEdge='none');sub(sub(c,'ByValueCondition'),'SimulationTimeCondition',value=f(t),rule='greaterThan')
 if guard:
  c=sub(group,'Condition',name=name+'_ActivationComplete',delay=0,conditionEdge='none');sub(sub(c,'ByValueCondition'),'StoryboardElementStateCondition',storyboardElementType='event',storyboardElementRef=guard,state='completeState')
def distance(a,b):return math.hypot(a['x']-b['x'],a['y']-b['y'])
def path(a,begin,end):return [interpolate(a['samples'],begin)]+[s for s in a['samples'] if begin<s['t']<end]+[interpolate(a['samples'],end)]
def route_points(a,begin,end):
 ss=path(a,begin,end);pp=[ss[0]]
 for s in ss[1:-1]:
  if distance(pp[-1],s)>=.4:pp.append(s)
 if distance(pp[-1],ss[-1])>1e-8:pp.append(ss[-1])
 return pp
def motion_runs(a):
 runs=[];first=None;ss=a['samples']
 for i,(s,q) in enumerate(zip(ss,ss[1:])):
  moving=distance(s,q)/(q['t']-s['t'])>.02
  if moving and first is None:first=i
  if not moving and first is not None:runs.append((ss[first]['t'],s['t']));first=None
 if first is not None:runs.append((ss[first]['t'],ss[-1]['t']))
 return runs
mapping={a['id']:('ego_vehicle' if a['id']=='ego' else 'pedestrian_001' if a['category']=='pedestrian' else 'vehicle_%03d'%i) for i,a in enumerate(d['actors'])}
reports=[];all_events=[]
for unit,suffix,stock in [('degrees','Timeline',False),('radians','Timeline_Radians',False),('radians','CARLA0915',True)]:
 root=E.Element('OpenSCENARIO');h=copy.deepcopy(template.find('FileHeader'));h.set('date','2026-09-08T00:00:00');h.set('description','RainJunctionANA031 video-estimated dynamics; right-handed metric coordinates');root.append(h)
 root.append(copy.deepcopy(template.find('ParameterDeclarations')));root.append(copy.deepcopy(template.find('CatalogLocations')))
 sub(sub(root,'RoadNetwork'),'LogicFile',filepath=d['xodr_file'] if stock else d['map_name']);en=sub(root,'Entities')
 for a in d['actors']:
  so=copy.deepcopy(template.find('Entities/ScenarioObject'));so.set('name',mapping[a['id']]);en.append(so);obj=so.find('Vehicle');dm=a['dimensions_m']
  if a['category']=='pedestrian':
   idx=so.index(obj);so.remove(obj);obj=E.Element('Pedestrian',name=a['blueprint_candidates'][0],model=a['blueprint_candidates'][0],mass='75',pedestrianCategory='pedestrian');so.insert(idx,obj);bb=sub(obj,'BoundingBox');sub(bb,'Center',x=0,y=0,z=f(dm['height']/2));sub(bb,'Dimensions',**{k:f(v) for k,v in dm.items()});sub(obj,'Properties')
  else:
   obj.set('name',a['blueprint_candidates'][0]);obj.set('vehicleCategory','car')
   for ax in obj.findall('Axles/*'):
    ax.set('positionX',f(dm['length']*(.3 if ax.tag=='FrontAxle' else -.3)));ax.set('trackWidth',f(dm['width']*.8));ax.set('maxSteering','.7' if ax.tag=='FrontAxle' else '0')
   center=obj.find('BoundingBox/Center');center.set('x','0');center.set('y','0');center.set('z',f(dm['height']/2))
   for k,v in dm.items():obj.find('BoundingBox/Dimensions').set(k,f(v))
  props=obj.find('Properties')
  if a.get('color'):sub(props,'Property',name='color',value=a['color'])
  if stock:sub(props,'Property',name='type',value='ego_vehicle' if a['id']=='ego' else 'simulation')
 sb=sub(root,'Storyboard');ini=sub(sub(sb,'Init'),'Actions');ga=copy.deepcopy(template.find('Storyboard/Init/Actions/GlobalAction'));ini.append(ga)
 ga.find('.//TimeOfDay').set('dateTime','2026-08-27T02:34:44');weather=ga.find('.//Weather');weather.set('cloudState','overcast');weather.find('Sun').set('intensity','0');weather.find('Sun').set('elevation',f(math.radians(-25)));weather.find('Fog').set('visualRange','800');weather.find('Precipitation').set('precipitationType','rain');weather.find('Precipitation').set('intensity','.35');ga.find('.//RoadCondition').set('frictionScaleFactor','.8')
 if True:
  for a in d['actors']:
   # v0.9.15 creates all declared other actors during initialization. Stage the
   # late pedestrian outside the incident view, then use the template's timed teleport.
   initial=dict(a['samples'][0])
   if a['start_t']>0:initial.update(x=-150.,y=18.)
   private=sub(ini,'Private',entityRef=mapping[a['id']]);world(sub(sub(private,'PrivateAction'),'TeleportAction'),initial,unit,(.95 if a['category']=='pedestrian' else .20) if stock else 0)
   speed=sub(sub(sub(private,'PrivateAction'),'LongitudinalAction'),'SpeedAction');sub(speed,'SpeedActionDynamics',dynamicsShape='step',value=0,dynamicsDimension='time');sub(sub(speed,'SpeedActionTarget'),'AbsoluteTargetSpeed',value=0)
 story=sub(sb,'Story',name='MyStory');act=sub(story,'Act',name='Act1');eventrows=[]
 for a in d['actors']:
  name=mapping[a['id']];group=sub(act,'ManeuverGroup',maximumExecutionCount=1,name=name+'_ManeuverGroup');sub(sub(group,'Actors',selectTriggeringEntities='false'),'EntityRef',entityRef=name);man=sub(group,'Maneuver',name=name+'_EventsManeuver')
  events=[{'t':a['start_t']+.10,'kind':'activation','pose':a['samples'][0],'speed':0.,'route':None}]
  for begin,end in motion_runs(a):
   times=sorted(set([begin,end]+[round(begin+i*.2,6) for i in range(1,math.ceil((end-begin)/.2)) if begin+i*.2<end]+[k[0] for k in a['source_keyframes'] if begin<k[0]<end]))
   for i,(ta,tb) in enumerate(zip(times,times[1:])):
    ss=path(a,ta,tb);v=sum(distance(s,q) for s,q in zip(ss,ss[1:]))/(tb-ta)
    events.append({'t':ta+.25,'kind':'motion_start' if i==0 else 'speed_update','pose':None,'speed':v,'route':route_points(a,begin,end) if i==0 else None})
   events.append({'t':end+.25,'kind':'stop','pose':None,'speed':0.,'route':None})
  events.sort(key=lambda e:e['t'])
  for idx,e in enumerate(events):
   ev=sub(man,'Event',name=f'{name}_Event_{idx+1}',priority='parallel',maximumExecutionCount=1);ai=0
   def action():
    global ai
    ac=sub(ev,'Action',name=f'{name}_Action_{idx}_{ai}');ai+=1;return ac
   if e['pose'] is not None:
    world(sub(sub(action(),'PrivateAction'),'TeleportAction'),e['pose'],unit,(.95 if a['category']=='pedestrian' else .20) if stock else 0)
   # Avoid scheduling private speed changes simultaneously with late creation in stock runner.
   if True:
    speed=sub(sub(sub(action(),'PrivateAction'),'LongitudinalAction'),'SpeedAction');sub(speed,'SpeedActionDynamics',dynamicsShape='linear',value=0,dynamicsDimension='time');sub(sub(speed,'SpeedActionTarget'),'AbsoluteTargetSpeed',value=f(e['speed']))
   if e['route']:
    r=sub(sub(sub(sub(action(),'PrivateAction'),'RoutingAction'),'AssignRouteAction'),'Route',closed='false',name='route_event')
    for s in e['route']:world(sub(r,'Waypoint',routeStrategy='shortest'),s,unit,(.95 if a['category']=='pedestrian' else .20) if stock else 0)
   trigger(ev,'StartTrigger',e['t'],f'Cond_{idx}_0_0_{name}',None if e['kind']=='activation' else name+'_Event_1')
   eventrows.append({'entity':name,'source_id':a['id'],'time_s':e['t'],'type':e['kind'],'speed_mps':e['speed'],'route_points':len(e['route']) if e['route'] else 0})
 trigger(act,'StartTrigger',0,'ActStartCondition')
 stop=copy.deepcopy(template.find('Storyboard/Story/Act/StopTrigger'));stop.find('.//SimulationTimeCondition').set('value',f(d['duration_s']+.4));act.append(stop);sub(sb,'StopTrigger')
 dest=P/(d['map_name']+'_'+suffix+'.xosc');E.ElementTree(root).write(str(dest),encoding='utf8',xml_declaration=True,pretty_print=True)
 assert schema.validate(root),str(schema.error_log)
 names=set(root.xpath('./Entities/ScenarioObject/@name'));assert len(names)==len(d['actors']);assert all(n in names for n in root.xpath('//@entityRef'))
 assert E.tostring(root.find('ParameterDeclarations'))==E.tostring(template.find('ParameterDeclarations'))
 for man in root.findall('.//Maneuver'):
  times=[float(e.find('.//SimulationTimeCondition').get('value')) for e in man.findall('Event')];assert times==sorted(times)
 newtags=sorted(set(n.tag for n in root.iter())-set(n.tag for n in template.iter()))
 if not stock:assert set(newtags)<={'Pedestrian','Private','StoryboardElementStateCondition'}
 reports.append({'file':dest.name,'heading_unit':unit,'xsd_pass':True,'entities':len(names),'events':len(eventrows),'routes':len(root.findall('.//Route')),'template_parameters_exact':True,'added_element_types':newtags,'time_order_pass':True,'entity_reference_pass':True,'runtime_tested':False,'flavor':'stock ScenarioRunner 0.9.15 initialization' if stock else 'user template timeline dialect'})
 if suffix=='Timeline':all_events=eventrows
(P/'validation/xosc_validation.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
(P/'timeline_events.json').write_text(json.dumps({'activation_offset_s':.10,'motion_start_offset_s':.25,'trigger_policy':'level-triggered conditions, one execution per event; each motion event AND-guards own activation completeState','events':all_events},ensure_ascii=False,indent=2),encoding='utf8')
(P/'entity_mapping.json').write_text(json.dumps([{'source_id':a['id'],'entity':mapping[a['id']],'label':a['label_zh'],'blueprint':a['blueprint_candidates'][0],'active_replay_s':[a['start_t'],a['end_t']],'evidence':a['visible_evidence'],'notes':a['notes']} for a in d['actors']],ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(reports,ensure_ascii=False,indent=2))

