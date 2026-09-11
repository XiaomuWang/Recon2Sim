"""Read-only runtime alignment check. Does not load worlds or spawn actors."""
import argparse,carla
ap=argparse.ArgumentParser();ap.add_argument('--host',default='localhost');ap.add_argument('--port',type=int,default=2000);ap.add_argument('--draw',action='store_true');a=ap.parse_args()
c=carla.Client(a.host,a.port);c.set_timeout(10);world=c.get_world();m=world.get_map()
if m.name.split('/')[-1]!='MeituanLane0512189':raise SystemExit('Load MeituanLane0512189 first. Current map: '+m.name)
for rid,lid,s in [(10,-4,80),(20,-4,50),(20,-3,50),(30,-4,20)]:
 w=m.get_waypoint_xodr(rid,lid,s)
 if w is None:raise RuntimeError('Missing waypoint '+str((rid,lid,s)))
 print(rid,lid,s,w.transform)
print('Topology edges:',len(m.get_topology()))
if a.draw:
 for w in m.generate_waypoints(2):world.debug.draw_point(w.transform.location+carla.Location(z=.12),size=.07,color=carla.Color(30,220,160),life_time=30)
 print('Compare green points with the FBX road surface in the simulator.')
