"""Offline checks: ASAM XSD, CARLA parsing and six lane geometry/adjacency."""
import pathlib,json,math,sys
from lxml import etree as E
import carla
from road_layout import *
P=pathlib.Path(__file__).resolve().parents[1]
xml=(P/(NAME+'.xodr')).read_text(encoding='utf-8');schema=E.XMLSchema(E.parse(str(P/'validation/schema/opendrive_17_core.xsd')))
valid=schema.validate(E.fromstring(xml.encode()));m=carla.Map(NAME,xml)
points=[];errors=[];maxerr=0;changes=[]
for w in m.generate_waypoints(.5):
 l=w.transform.location;points.append({'road':w.road_id,'lane':w.lane_id,'s':w.s,'xyz_rh':[l.x,-l.y,l.z]})
 start=next(seg[1] for seg in SEGMENTS if seg[0]==w.road_id)
 i=(abs(w.lane_id)-1)*(1 if w.lane_id>0 else -1);expected=(start+w.s,lane_y(i),0)
 err=math.sqrt((l.x-expected[0])**2+(l.y+expected[1])**2+l.z**2);maxerr=max(maxerr,err)
 if err>.002:errors.append([w.lane_id,w.s,err])
for i in [-2,-3,-4,2,3,4]:
 w=m.get_waypoint_xodr(20,i,50)
 changes.append({'lane':i,'change':str(w.lane_change),'left':w.get_left_lane().lane_id if w.get_left_lane() else None,'right':w.get_right_lane().lane_id if w.get_right_lane() else None})
 if i in [-3,3] and w.lane_change!=carla.LaneChange.Both:errors.append('middle lane should allow both changes')
crossings=[]
for a,b in zip(SEGMENTS,SEGMENTS[1:]):
 for i in [-2,-3,-4,2,3,4]:
  w=m.get_waypoint_xodr(a[0],i,a[2]-.25) if i<0 else m.get_waypoint_xodr(b[0],i,.25)
  nxt=w.next(.5);target=b[0] if i<0 else a[0]
  ok=any(q.road_id==target and q.lane_id==i for q in nxt);crossings.append({'from':w.road_id,'to':target,'lane':i,'pass':ok})
  if not ok:errors.append('failed road boundary crossing')
if len(m.get_topology())<12:errors.append('missing road routing topology')
report={'xsd_1_7_pass':valid,'xsd_errors':str(schema.error_log),'carla_offline_parse_pass':True,'topology_edges':len(m.get_topology()),'road_boundary_checks':crossings,'waypoints_0_5m':len(points),'max_reference_error_m':maxerr,'lane_change_checks':changes,'errors':errors,'runtime_tested':False,'scope':'Internal XODR/FBX geometry consistency, not real-world survey accuracy; UE import and driving untested'}
(P/'validation/carla_validation.json').write_text(json.dumps(report,indent=2));(P/'validation/carla_waypoints.json').write_text(json.dumps(points));print(json.dumps(report,indent=2));assert valid and not errors
