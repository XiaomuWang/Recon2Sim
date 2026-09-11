"""Offline OpenDRIVE parser, XSD, route and coordinate checks."""
import json,math,pathlib,xml.etree.ElementTree as ET,importlib.metadata
import carla
from lxml import etree
from road_layout import *
P=pathlib.Path(__file__).resolve().parents[1];xml=(P/(NAME+'.xodr')).read_text();m=carla.Map(NAME,xml);root=ET.fromstring(xml)
schema=etree.XMLSchema(etree.parse(str(P/'validation/schema/opendrive_17_core.xsd')));valid=schema.validate(etree.fromstring(xml.encode()))
errors=[];maxxy=0;maxz=0;samples=[]
for r in ROADS:
 for i in range(1,int(r['length']*4)):
  s=i/4
  for ln in [-3,-2,2,3]:
   w=m.get_waypoint_xodr(r['id'],ln,s)
   if not w:errors.append(['missing',r['id'],ln,s]);continue
   t=(1 if ln>0 else -1)*(r['median']+(abs(ln)-1.5)*r['w']);p=road_point(r,s,t);l=w.transform.location
   e=math.hypot(l.x-p[0],l.y+p[1]);maxxy=max(maxxy,e);maxz=max(maxz,abs(l.z))
   if e>.002:errors.append(['coordinate',r['id'],ln,s,e])
for w in m.generate_waypoints(.5):
 l=w.transform.location;samples.append({'road':w.road_id,'lane':w.lane_id,'s':w.s,'xyz_rh':[l.x,-l.y,l.z]})
checks=[]
for r in root.findall('road'):
 if r.get('junction')=='-1':continue
 rid=int(r.get('id'));L=float(r.get('length'));la=r.find('lanes/laneSection/right/lane');lk=r.find('link');rec={'road':rid}
 for which,s in [('predecessor',0),('successor',L)]:
  l=lk.find(which);other=int(l.get('elementId'));cp=l.get('contactPoint');ol=int(la.find('link/'+which).get('id'));rr=root.find("road[@id='%d']"%other);os=0 if cp=='start' else float(rr.get('length'))
  w=m.get_waypoint_xodr(rid,-1,max(.001,min(L-.001,s)));v=m.get_waypoint_xodr(other,ol,max(.001,os-.001) if os else .001)
  gap=w.transform.location.distance(v.transform.location);yaw=abs((w.transform.rotation.yaw-v.transform.rotation.yaw+180)%360-180);rec[which+'_gap_m']=gap;rec[which+'_yaw_deg']=yaw
  if gap>.005 or yaw>.05:errors.append(['junction',rid,which,gap,yaw])
 checks.append(rec)
# Walk the actual right-turn route into the incident carriageway.
w=m.get_waypoint_xodr(30,-3,250);route=[]
for i in range(400):
 route.append([w.road_id,w.lane_id,w.s]);nxt=w.next(1.)
 if not nxt:break
 preferred=[v for v in nxt if v.road_id in [30,113,20]]
 if not preferred:errors.append(['route_unexpected',[(v.road_id,v.lane_id) for v in nxt]]);break
 w=preferred[0]
 if w.road_id==20 and w.s>270:break
route_pass=any(v[0]==113 for v in route) and any(v[0]==20 and v[2]>258 for v in route)
if not route_pass:errors.append('observed_route_failed')
wp=m.get_waypoint_xodr(20,-3,258);adj=wp.get_left_lane();lane_change_pass=adj is not None and adj.road_id==20 and adj.lane_id==-2
if not lane_change_pass:errors.append('incident_lane_change_failed')
report={'xsd_1_7_pass':valid,'xsd_errors':str(schema.error_log),'carla_version':importlib.metadata.version('carla'),'offline_parse_pass':True,'road_count':len(root.findall('road')),'junction_count':1,'topology_edges':len(m.get_topology()),'waypoints_0_5m':len(samples),'max_reference_xy_error_m':maxxy,'max_reference_z_error_m':maxz,'junction_endpoint_checks':checks,'observed_route_traversal_pass':route_pass,'incident_adjacent_lane_pass':lane_change_pass,'errors':errors,'runtime_tested':False,'scope':'Internal geometry consistency, not real-world survey accuracy. No Unreal import or driving dynamics test.'}
(P/'validation/carla_validation.json').write_text(json.dumps(report,indent=2));(P/'validation/carla_waypoints.json').write_text(json.dumps(samples));(P/'validation/observed_route.json').write_text(json.dumps(route));print(json.dumps(report,indent=2));assert valid and not errors

