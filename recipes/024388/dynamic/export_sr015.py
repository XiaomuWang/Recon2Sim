"""Version-specific adapter: valid Init positions + explicit custom BasicControl.
Template dialect exports are kept separate and unchanged by this exporter.
"""
import copy,json,sys
from pathlib import Path
from lxml import etree as E
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from export_template_timeline import sub,world,fmt
d=json.loads((P/'scenario.json').read_text(encoding='utf-8'));mapping=json.loads((P/'template_compatible/entity_mapping.json').read_text(encoding='utf-8'))
root=E.parse(str(P/'template_compatible/LuoboTurn024388_Timeline_Radians.xosc')).getroot()
root.find('FileHeader').set('description','LuoboTurn024388 CARLA 0.9.15 timestamp replay with supplied BasicControl adapter')
actions=root.find('Storyboard/Init/Actions')
for i,(a,mp) in enumerate(zip(d['actors'],mapping)):
 name=mp['entity'];entity=root.find("Entities/ScenarioObject[@name='%s']"%name)
 obj=entity.find('Vehicle') if a['category']!='pedestrian' else entity.find('Pedestrian')
 sub(obj.find('Properties'),'Property',name='type',value='ego_vehicle' if a['id']=='ego' else 'simulation')
 oc=entity.find('ObjectController')
 if oc is not None:entity.remove(oc)
 private=sub(actions,'Private',entityRef=name)
 # Unique, non-overlapping staging spawn. Controller parks invisibly before the active window.
 staging=dict(x=-500-12*i,y=-500,z=5,h=0)
 world(sub(sub(private,'PrivateAction'),'TeleportAction'),staging,'radians')
 ca=sub(sub(private,'PrivateAction'),'ControllerAction');ctrl=sub(sub(ca,'AssignControllerAction'),'Controller',name='LuoboReplayControl')
 props=sub(ctrl,'Properties')
 for k,v in [('module','luobo_replay_control.py'),('scene_file','scenario.json'),('source_id',a['id'])]:sub(props,'Property',name=k,value=v)
 override=sub(ca,'OverrideControllerValueAction')
 for tag in ['Throttle','Brake','Clutch','ParkingBrake','SteeringWheel']:sub(override,tag,active='false',value=0)
 sub(override,'Gear',active='false',number=0)
 man=root.find(".//Maneuver[@name='%s_EventsManeuver']"%name)
 events=man.findall('Event')
 # Only birth + final stop are needed: the controller supplies every 30 Hz pose.
 # Final ego stop keeps the Story alive to the full 179 s.
 for ev in events[1:-1]:man.remove(ev)
 for ev in man.findall('Event'):
  for action in list(ev.findall('Action')):
   if action.find('.//TeleportAction') is not None or action.find('.//RoutingAction') is not None:ev.remove(action)
  for target in ev.findall('.//AbsoluteTargetSpeed'):target.set('value','0')
path=P/'LuoboTurn024388_CARLA015.xosc';E.ElementTree(root).write(str(path),encoding='utf-8',xml_declaration=True,pretty_print=True)
schema=E.XMLSchema(E.parse(str(P/'validation/OpenSCENARIO.xsd')));schema.assertValid(root)
assert len(root.findall('Storyboard/Init/Actions/Private'))==len(d['actors'])
report=dict(file=path.name,schema_pass=True,entities=len(d['actors']),init_placements=len(d['actors']),controller_assignments=len(root.findall('.//AssignControllerAction')),independent_events=len(root.findall('.//Event')),heading_unit='radians',engine_run_verified=False,requires=['ScenarioRunner v0.9.15','CARLA client/server 0.9.15','luobo_replay_control.py','replay_carla.py','scenario.json','cooked LuoboTurn024388 map'],note='All actors spawned at distinct staging positions; custom controller disables physics and applies timestamp poses, including late activation. No default-origin spawn collision.')
(P/'validation/sr015_export.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
