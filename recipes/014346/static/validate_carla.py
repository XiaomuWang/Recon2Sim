"""Offline CARLA parser, XSD, reference geometry and junction continuity checks."""
import sys,json,math,pathlib,xml.etree.ElementTree as ET,importlib.metadata
from lxml import etree
import carla
from road_layout import pose,WIDTH
P=pathlib.Path(__file__).resolve().parents[1];name='NanshanGate014346'
xml=(P/(name+'.xodr')).read_text();m=carla.Map(name,xml);root=ET.fromstring(xml)
schema=etree.XMLSchema(etree.parse(str(P/'validation/schema/opendrive_17_core.xsd')))
valid=schema.validate(etree.fromstring(xml.encode()))
errors=[];samples=[];max_pos=0;max_z=0
for rid,a,b in [(10,0,92),(20,108,210)]:
 for i in range(1,int(b-a)*4):
  s=i/4
  for lane in [-1,1]:
   wp=m.get_waypoint_xodr(rid,lane,s);p=pose(a+s,lane*WIDTH/4);l=wp.transform.location
   err=math.hypot(l.x-p[0],l.y+p[1]);ze=abs(l.z-p[2]);max_pos=max(max_pos,err);max_z=max(max_z,ze)
   if err>.002 or ze>.002:errors.append([rid,lane,s,err,ze])
for w in m.generate_waypoints(.5):
 l=w.transform.location;samples.append({'road':w.road_id,'lane':w.lane_id,'s':w.s,'xyz_rh':[l.x,-l.y,l.z]})
junctions=[]
for r in root.findall('road'):
 rid=int(r.get('id'))
 if r.get('junction')=='-1':continue
 L=float(r.get('length'));la=r.find('lanes/laneSection/right/lane');lk=r.find('link')
 rec={'road':rid}
 for which,s in [('predecessor',0),('successor',L)]:
  l=lk.find(which);other=int(l.get('elementId'));cp=l.get('contactPoint');ol=int(la.find('link/'+which).get('id'));otherroad=root.find("road[@id='%d']"%other);os=0 if cp=='start' else float(otherroad.get('length'))
  w=m.get_waypoint_xodr(rid,-1,max(.00001,min(L-.00001,s)));v=m.get_waypoint_xodr(other,ol,max(.00001,os-.00001) if os else .00001)
  gap=w.transform.location.distance(v.transform.location);yaw=abs((w.transform.rotation.yaw-v.transform.rotation.yaw+180)%360-180)
  rec[which+'_gap_m']=gap;rec[which+'_yaw_deg']=yaw
  if gap>.005 or yaw>.05:errors.append({'junction':rid,'end':which,'gap':gap,'yaw':yaw})
 junctions.append(rec)
report={'xsd_1_7_pass':valid,'xsd_errors':str(schema.error_log),'carla_version':importlib.metadata.version('carla'),'carla_offline_parse_pass':True,'road_count':len(root.findall('road')),'junction_count':len(root.findall('junction')),'topology_edges':len(m.get_topology()),'waypoints_0_5m':len(samples),'max_reference_xy_error_m':max_pos,'max_reference_z_error_m':max_z,'junction_endpoint_checks':junctions,'errors':errors,'scope':'Offline parser and generated geometry consistency only. No real-world survey validation; no Unreal runtime or vehicle dynamics test. No georeference is intentionally supplied.'}
(P/'validation/carla_validation.json').write_text(json.dumps(report,indent=2));(P/'validation/carla_waypoints.json').write_text(json.dumps(samples))
print(json.dumps(report,indent=2));assert valid and not errors
