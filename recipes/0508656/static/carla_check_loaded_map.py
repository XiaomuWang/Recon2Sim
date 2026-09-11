"""Run after importing/cooking/loading the FBX map; does not replace the world."""
import argparse,carla,json
p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=2000);a=p.parse_args()
c=carla.Client(a.host,a.port);c.set_timeout(15);w=c.get_world();m=w.get_map()
if 'MeituanBrake0508656' not in m.name:raise RuntimeError('Load the MeituanBrake0508656 cooked map first. Current map: '+m.name)
for rid,lid,s,label in [(30,-3,45,'approach'),(20,-3,258,'incident_outer_lane'),(20,-2,258,'incident_inner_lane'),(20,-2,316,'under_bridge')]:
 wp=m.get_waypoint_xodr(rid,lid,s)
 if wp is None:raise RuntimeError('Missing waypoint '+label)
 loc=wp.transform.location;w.debug.draw_point(loc+carla.Location(z=.15),size=.15,color=carla.Color(0,255,100),life_time=90)
 w.debug.draw_string(loc+carla.Location(z=1),label,color=carla.Color(255,255,255),life_time=90)
 print(label,wp.transform)
wp=m.get_waypoint_xodr(20,-2,250);t=wp.transform;t.location.z+=2.0;w.get_spectator().set_transform(t)
for wp in m.generate_waypoints(3):w.debug.draw_point(wp.transform.location+carla.Location(z=.08),size=.06,color=carla.Color(0,180,255),life_time=90)
print('Waypoint overlay displayed for 90 seconds. Visually inspect scale, road surface, collision and materials in your CARLA build.')
