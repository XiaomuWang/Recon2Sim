"""Read current map; optionally draw temporary waypoints. No load_world, spawning or settings changes."""
import argparse,json
from pathlib import Path
import carla
p=argparse.ArgumentParser();p.add_argument('--host',default='localhost');p.add_argument('--port',type=int,default=2000);p.add_argument('--draw',action='store_true');a=p.parse_args()
c=carla.Client(a.host,a.port);c.set_timeout(15);w=c.get_world();m=w.get_map()
if m.name.split('/')[-1]!='GreenRail016955':raise RuntimeError('Current map is '+m.name+'; load GreenRail016955 using your existing CARLA workflow first.')
ids={v.road_id for v in m.generate_waypoints(5)}
if not {10,11,20,30,31,103,201}.issubset(ids):raise RuntimeError('Expected road IDs absent. Check the XODR associated with this level.')
for rid,lane,s in [(20,-1,130),(30,1,160),(10,-4,170)]:
 q=m.get_waypoint_xodr(rid,lane,s);print(rid,lane,q.transform)
if a.draw:
 for q in m.generate_waypoints(2):
  loc=q.transform.location+carla.Location(z=.08);w.debug.draw_point(loc,size=.06,color=carla.Color(45,220,130),life_time=45)
print('Current-map structure checked. Inspect waypoint overlay against FBX road and curb geometry; no server world was replaced.')
