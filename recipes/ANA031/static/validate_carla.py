"""Offline OpenDRIVE XSD, CARLA waypoint and junction continuity checks."""
import json,math,pathlib,xml.etree.ElementTree as ET,importlib.metadata
from lxml import etree
import carla
from road_layout import *
P=pathlib.Path(__file__).resolve().parents[1];xml=(P/(NAME+'.xodr')).read_text();m=carla.Map(NAME,xml);root=ET.fromstring(xml)
schema=etree.XMLSchema(etree.parse(str(P/'validation/schema/opendrive_17_core.xsd')));valid=schema.validate(etree.fromstring(xml.encode()))
errors=[];samples=[];maxpos=0;maxz=0
for r in ROADS:
 for i in range(1,int(r['length']*4)):
  s=i/4
  for lane in range(-r['n'],r['n']+1):
   if not lane:continue
   w=m.get_waypoint_xodr(r['id'],lane,s)
   if w is None:errors.append(['missing',r['id'],lane,s]);continue
   l=w.transform.location;p=road_point(r,s,(abs(lane)-.5)*r['w']*(1 if lane>0 else -1));err=math.hypot(l.x-p[0],l.y+p[1]);ze=abs(l.z-p[2]);maxpos=max(maxpos,err);maxz=max(maxz,ze)
   if err>.002 or ze>.002:errors.append([r['id'],lane,s,err,ze])
for w in m.generate_waypoints(.5):
 l=w.transform.location;samples.append({'road':w.road_id,'lane':w.lane_id,'s':w.s,'xyz_rh':[l.x,-l.y,l.z]})
jchecks=[]
for r in root.findall('road'):
 if r.get('junction')=='-1':continue
 rid=int(r.get('id'));L=float(r.get('length'));la=r.find('lanes/laneSection/right/lane');lk=r.find('link');rec={'road':rid}
 for which,s in [('predecessor',0),('successor',L)]:
  link=lk.find(which);other=int(link.get('elementId'));cp=link.get('contactPoint');ol=int(la.find('link/'+which).get('id'));otherroad=root.find("road[@id='%d']"%other);os=0 if cp=='start' else float(otherroad.get('length'))
  w=m.get_waypoint_xodr(rid,-1,max(.001,min(L-.001,s)));v=m.get_waypoint_xodr(other,ol,max(.001,os-.001))
  gap=w.transform.location.distance(v.transform.location);yaw=abs((w.transform.rotation.yaw-v.transform.rotation.yaw+180)%360-180)
  rec[which+'_gap_m']=gap;rec[which+'_yaw_deg']=yaw
  if gap>.005 or yaw>.05:errors.append({'road':rid,'end':which,'gap':gap,'yaw':yaw})
 jchecks.append(rec)
report={'xsd_1_7_pass':valid,'xsd_errors':str(schema.error_log),'carla_version':importlib.metadata.version('carla'),'carla_offline_parse_pass':True,'road_count':len(root.findall('road')),'junction_count':len(root.findall('junction')),'topology_edges':len(m.get_topology()),'waypoints_0_5m':len(samples),'max_reference_xy_error_m':maxpos,'max_reference_z_error_m':maxz,'junction_endpoint_checks':jchecks,'errors':errors,'scope':'Offline parser and internal geometry checks only; no calibrated-world accuracy claim; no runtime/cooking/vehicle test; no GNSS reference.'}
(P/'validation/carla_validation.json').write_text(json.dumps(report,indent=2));(P/'validation/carla_waypoints.json').write_text(json.dumps(samples));print(json.dumps(report,indent=2));assert valid and not errors
