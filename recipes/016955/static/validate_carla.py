"""CARLA 0.9.x offline map/XSD checks; does not require or mutate a running server."""
import json,math,pathlib,xml.etree.ElementTree as ET,importlib.metadata
from lxml import etree
import carla
from road_layout import *
P=pathlib.Path(__file__).resolve().parents[1];xml=(P/(NAME+'.xodr')).read_text();root=ET.fromstring(xml)
schema=etree.XMLSchema(etree.parse(str(P/'validation/schema/opendrive_17_core.xsd')));valid=schema.validate(etree.fromstring(xml.encode()))
m=carla.Map(NAME,xml);errors=[];samples=[];maxpos=0.;checks=[]
for rid,r in ROADS.items():
 for ordinal in range(1,r['n']+1):
  for side in [-1,1]:
   lid=lane_id(rid,side,ordinal)
   for i in range(1,int(r['length']*4)):
    s=i/4;w=m.get_waypoint_xodr(rid,lid,s)
    if not w:errors.append(['missing waypoint',rid,lid,s]);continue
    p=pose(rid,s,lane_t(rid,lid));l=w.transform.location;err=math.sqrt((l.x-p[0])**2+(l.y+p[1])**2+l.z**2);maxpos=max(maxpos,err)
    if err>.002:errors.append([rid,lid,s,err])
for c in maneuvers():
 rid=c['id'];r=root.find("road[@id='%d']"%rid);L=float(r.get('length'));rec=dict(road=rid)
 for tag,s,ep in [('start',.00001,c['a']),('end',L-.00001,c['b'])]:
  other=ROADS[ep['rid']];os=.00001 if ep['cp']=='start' else other['length']-.00001
  w=m.get_waypoint_xodr(rid,-1,s);v=m.get_waypoint_xodr(ep['rid'],ep['lane'],os)
  gap=w.transform.location.distance(v.transform.location);yaw=abs((w.transform.rotation.yaw-v.transform.rotation.yaw+180)%360-180)
  rec[tag+'_gap_m']=gap;rec[tag+'_yaw_deg']=yaw
  if gap>.005 or yaw>.05:errors.append([rid,tag,gap,yaw])
 # Confirm next() can leave the connector onto intended outgoing road.
 w=m.get_waypoint_xodr(rid,-1,L-.1);nxt=w.next(.5)
 rec['outgoing_next_pass']=any(v.road_id==c['b']['rid'] and v.lane_id==c['b']['lane'] for v in nxt)
 if not rec['outgoing_next_pass']:errors.append([rid,'bad successor route'])
 checks.append(rec)
for w in m.generate_waypoints(.5):
 l=w.transform.location;samples.append(dict(road=w.road_id,lane=w.lane_id,s=w.s,xyz_rh=[l.x,-l.y,l.z],heading_rh=-math.radians(w.transform.rotation.yaw)))
# Check the recorded route through both right turns using CARLA next(), without creating actors.
target=[(c['id'],c['a']['rid'],c['b']['rid']) for c in maneuvers() if (c['a']['rid'],c['b']['rid']) in [(10,20),(20,30)]]
route=[]
for cid,a,b in target:
 c=next(x for x in maneuvers() if x['id']==cid);r=ROADS[a];s=r['length']-.2 if c['a']['cp']=='end' else .2;w=m.get_waypoint_xodr(a,c['a']['lane'],s)
 route.append(dict(from_road=a,connector=cid,to_road=b,entry_next_pass=any(v.road_id==cid for v in w.next(.8))))
 if not route[-1]['entry_next_pass']:errors.append(['route entry',cid])
report=dict(xsd_1_7_pass=valid,xsd_errors=str(schema.error_log),carla_version=importlib.metadata.version('carla'),carla_offline_parse_pass=True,road_count=len(root.findall('road')),junction_count=len(root.findall('junction')),topology_edges=len(m.get_topology()),waypoints_0_5m=len(samples),max_reference_error_m=maxpos,junction_checks=checks,observed_right_turn_route=route,errors=errors,scope='Offline parser, geometry and next() topology only. No Unreal runtime, cooking, georeference or metric survey validation.')
(P/'validation/carla_validation.json').write_text(json.dumps(report,indent=2));(P/'validation/carla_waypoints.json').write_text(json.dumps(samples));print(json.dumps(report,indent=2));assert valid and not errors
