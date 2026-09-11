"""Read-only map check with optional debug overlays. Does not spawn vehicles or replace world.
python carla_check_loaded_map.py --host localhost --port 2000 --draw
Requires the matching CARLA client package for your server.
"""
import argparse,json,pathlib,math
import carla
P=pathlib.Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--host',default='localhost');ap.add_argument('--port',type=int,default=2000);ap.add_argument('--draw',action='store_true');args=ap.parse_args()
client=carla.Client(args.host,args.port);client.set_timeout(10)
world=client.get_world();m=world.get_map()
if m.name.split('/')[-1]!='RainJunctionANA031':raise SystemExit('Load the imported RainJunctionANA031 level first. Current map: '+m.name)
print('Server:',client.get_server_version(),'Map:',m.name,'Topology:',len(m.get_topology()))
for rid,lane,s,label in [(10,-1,72,'approach'),(20,-1,10,'past_gate'),(30,-1,15,'inside_gate')]:
 w=m.get_waypoint_xodr(rid,lane,s)
 if not w:raise RuntimeError('Missing road/lane: '+str((rid,lane)))
 print(label,w.transform)
if args.draw:
 for w in m.generate_waypoints(2):
  q=w.transform.location+carla.Location(z=.15);world.debug.draw_point(q,size=.07,color=carla.Color(30,220,160),life_time=30)
 print('Green waypoint overlay visible for 30 seconds. Visually verify it follows the imported road surface.')
