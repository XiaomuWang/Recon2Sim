"""Offline XSD / CARLA validation, connected route traversal and explicit geometry checks."""
import json,math,pathlib,xml.etree.ElementTree as E
from lxml import etree
import carla
from road_layout import *
P=pathlib.Path(__file__).resolve().parents[1];xml=(P/(NAME+'.xodr')).read_text(encoding='utf-8');root=E.fromstring(xml)
schema=etree.XMLSchema(etree.parse(str(P/'validation/schema/opendrive_17_core.xsd')));valid=schema.validate(etree.fromstring(xml.encode()))
m=carla.Map(NAME,xml);errors=[];max_xy=0;paths=json.loads((P/'validation/junction_paths.json').read_text());samples=[]
for r in ROADS:
 for i in range(1,int(r['length']*4)):
  s=i*.25
  for lane in [-1,1]:
   w=m.get_waypoint_xodr(r['id'],lane,s);x,y,z=road_point(r,s,lane*LANE/2);loc=w.transform.location;err=math.hypot(x-loc.x,y+loc.y);max_xy=max(max_xy,err)
   if err>.002:errors.append({'reference_error':[r['id'],lane,s,err]})
checks=[]
for path in paths:
 rid=path['id'];r=root.find("road[@id='%d']"%rid);L=path['length'];la=r.find('lanes/laneSection/right/lane');rec={'road':rid,'radius_m':6.65 if 'segments' in path else (1/abs(path['k']) if path['k'] else None)}
 for tag,s in [('predecessor',.0001),('successor',L-.0001)]:
  lk=r.find('link/'+tag);other=int(lk.get('elementId'));cp=lk.get('contactPoint');ln=int(la.find('link/'+tag).get('id'));oroad=root.find("road[@id='%d']"%other);os=.0001 if cp=='start' else float(oroad.get('length'))-.0001
  w=m.get_waypoint_xodr(rid,-1,s);v=m.get_waypoint_xodr(other,ln,os);gap=w.transform.location.distance(v.transform.location);yaw=abs((w.transform.rotation.yaw-v.transform.rotation.yaw+180)%360-180)
  rec[tag+'_gap_m']=gap;rec[tag+'_yaw_deg']=yaw
  if gap>.005 or yaw>.05:errors.append({'junction_end_error':rec})
 for i in range(1,80):
  s=L*i/80;w=m.get_waypoint_xodr(rid,-1,s);x,y,z,h=path_pose(path,s);loc=w.transform.location;err=math.hypot(x-loc.x,y+loc.y);max_xy=max(max_xy,err)
  if err>.002:errors.append({'arc_error':[rid,s,err]})
 checks.append(rec)
for w in m.generate_waypoints(.5):
 l=w.transform.location;samples.append({'road':w.road_id,'lane':w.lane_id,'s':w.s,'xyz_rh':[l.x,-l.y,l.z]})
# Walk actual CARLA successor topology through the requested A->B right-turn route.
visited=[];w=m.get_waypoint_xodr(10,-1,160);route_ok=False
for i in range(200):
 visited.append(w.road_id)
 if w.road_id==20 and w.s>15:route_ok=True;break
 nxt=[q for q in w.next(.5) if q.road_id in [10,100,20]]
 if not nxt:break
 w=nxt[0]
if not route_ok:errors.append({'right_turn_route_traversal_failed':visited})
try:
 import pkg_resources
 version=pkg_resources.get_distribution('carla').version
except:version='unknown'
report={'xsd_1_7_pass':valid,'xsd_errors':str(schema.error_log),'carla_version':version,'carla_offline_parse_pass':True,'roads':len(root.findall('road')),'junctions':len(root.findall('junction')),'topology_edges':len(m.get_topology()),'waypoints_0_5m':len(samples),'max_analytic_to_carla_xy_m':max_xy,'connectors':checks,'requested_right_turn_traversal_pass':route_ok,'right_turn_road_sequence':list(dict.fromkeys(visited)),'errors':errors,'scope':'Offline parser and internal consistency. Does not establish surveyed accuracy, vehicle swept-volume clearance, Unreal collision or cooked runtime validation.'}
(P/'validation/carla_validation.json').write_text(json.dumps(report,indent=2));(P/'validation/carla_waypoints.json').write_text(json.dumps(samples));print(json.dumps(report,indent=2));assert valid and not errors
