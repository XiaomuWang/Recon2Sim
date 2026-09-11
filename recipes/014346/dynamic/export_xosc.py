"""OpenSCENARIO 1.0 timed trajectory interchange; Python replay is authoritative for CARLA timing."""
from pathlib import Path
from lxml import etree as E
import json
P=Path(__file__).resolve().parents[1];d=json.loads((P/'scenario.json').read_text(encoding='utf-8'))
def sub(e,tag,**kw):return E.SubElement(e,tag,{k:str(v) for k,v in kw.items()})
def world(e,s):return sub(sub(e,'Position'),'WorldPosition',x=s['x'],y=s['y'],z=s['z']+.15,h=s['h'],p=0,r=0)
def trigger(e,tag,t=None,event=None):
 c=sub(sub(sub(e,tag),'ConditionGroup'),'Condition',name=('at_'+str(t) if event is None else 'after_'+event),delay=0,conditionEdge='rising')
 v=sub(c,'ByValueCondition')
 if event:sub(v,'StoryboardElementStateCondition',storyboardElementType='event',storyboardElementRef=event,state='completeState')
 else:sub(v,'SimulationTimeCondition',value=t,rule='greaterThan')
root=E.Element('OpenSCENARIO');sub(root,'FileHeader',revMajor=1,revMinor=0,date='2026-09-08T00:00:00',description='Four-view visual reconstruction; RH metric world; estimated geometry; timed trajectory interchange',author='Video reconstruction')
sub(root,'ParameterDeclarations');sub(root,'CatalogLocations');rn=sub(root,'RoadNetwork');sub(rn,'LogicFile',filepath='NanshanGate014346.xodr')
en=sub(root,'Entities')
for a in d['actors']:
 so=sub(en,'ScenarioObject',name=a['id']);dims=a['dimensions_m'];bp=a['blueprint_candidates'][0]
 if a['category']=='pedestrian':o=sub(so,'Pedestrian',name=bp,model=bp,mass=75,pedestrianCategory='pedestrian')
 else:o=sub(so,'Vehicle',name=bp,vehicleCategory='truck' if a['category'] in ['truck','gate_truck'] else 'motorbike' if a['category'] in ['motorcycle','tricycle','parked'] else 'car')
 sub(o,'ParameterDeclarations');bb=sub(o,'BoundingBox');sub(bb,'Center',x=0,y=0,z=dims['height']/2);sub(bb,'Dimensions',width=dims['width'],length=dims['length'],height=dims['height'])
 if a['category']!='pedestrian':
  sub(o,'Performance',maxSpeed=25,maxAcceleration=4,maxDeceleration=8);ax=sub(o,'Axles')
  for tag,x in [('FrontAxle',dims['length']*.3),('RearAxle',-dims['length']*.3)]:sub(ax,tag,maxSteering=.7 if tag=='FrontAxle' else 0,wheelDiameter=.65,trackWidth=dims['width']*.8,positionX=x,positionZ=.325)
 props=sub(o,'Properties');sub(props,'Property',name='type',value='ego_vehicle' if a['id']=='ego' else 'simulation')
 if a.get('color'):sub(props,'Property',name='color',value=a['color'])
 sub(props,'Property',name='reconstruction_confidence',value='estimated')
sb=sub(root,'Storyboard');init=sub(sub(sb,'Init'),'Actions')
for a in d['actors']:
 if a['start_t']==0:
  ga=sub(init,'GlobalAction');ea=sub(ga,'EntityAction',entityRef=a['id']);world(sub(ea,'AddEntityAction'),a['samples'][0])
story=sub(sb,'Story',name='Observed_52_to_159_seconds');sub(story,'ParameterDeclarations');act=sub(story,'Act',name='Visual_replay')
for a in d['actors']:
 group=sub(act,'ManeuverGroup',name='group_'+a['id'],maximumExecutionCount=1);sub(sub(group,'Actors',selectTriggeringEntities='false'),'EntityRef',entityRef=a['id']);man=sub(group,'Maneuver',name='motion_'+a['id']);sub(man,'ParameterDeclarations')
 spawn=None
 if a['start_t']>0:
  spawn='spawn_'+a['id'];ev=sub(man,'Event',name=spawn,priority='parallel',maximumExecutionCount=1);ea=sub(sub(sub(ev,'Action',name=spawn+'_action'),'GlobalAction'),'EntityAction',entityRef=a['id']);world(sub(ea,'AddEntityAction'),a['samples'][0]);trigger(ev,'StartTrigger',a['start_t'])
 ev=sub(man,'Event',name='follow_'+a['id'],priority='parallel',maximumExecutionCount=1)
 f=sub(sub(sub(sub(ev,'Action',name='trajectory_'+a['id']),'PrivateAction'),'RoutingAction'),'FollowTrajectoryAction')
 tr=sub(f,'Trajectory',name=a['id']+'_timed',closed='false');sub(tr,'ParameterDeclarations');poly=sub(sub(tr,'Shape'),'Polyline')
 ss=a['samples'][::6]
 if ss[-1]!=a['samples'][-1]:ss.append(a['samples'][-1])
 for s in ss:world(sub(poly,'Vertex',time=s['t']),s)
 sub(sub(f,'TimeReference'),'Timing',domainAbsoluteRelative='absolute',scale=1,offset=0);sub(f,'TrajectoryFollowingMode',followingMode='position');trigger(ev,'StartTrigger',0 if not spawn else None,spawn)
 if a['end_t']<d['duration_s']:
  ev=sub(man,'Event',name='remove_'+a['id'],priority='parallel',maximumExecutionCount=1);sub(sub(sub(sub(ev,'Action',name='remove_action_'+a['id']),'GlobalAction'),'EntityAction',entityRef=a['id']),'DeleteEntityAction');trigger(ev,'StartTrigger',a['end_t']+.05)
trigger(act,'StartTrigger',0);sub(act,'StopTrigger');trigger(sb,'StopTrigger',d['duration_s']+.1)
path=P/'NanshanGate014346_Dynamic.xosc';E.ElementTree(root).write(str(path),encoding='utf-8',xml_declaration=True,pretty_print=True)
schema=E.XMLSchema(E.parse(str(P/'validation/OpenSCENARIO.xsd')));ok=schema.validate(E.parse(str(path)));report={'OpenSCENARIO_1_0_schema_pass':ok,'errors':str(schema.error_log),'vertices':len(root.findall('.//Vertex')),'target':'interchange; ScenarioRunner temporal behavior must be tested on target version','runtime_tested':False};(P/'validation/xosc_validation.json').write_text(json.dumps(report,indent=2));print(report);assert ok
