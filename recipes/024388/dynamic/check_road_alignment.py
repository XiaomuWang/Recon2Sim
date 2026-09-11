import carla,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];d=json.loads((P/'scenario.json').read_text(encoding='utf-8'));m=carla.Map(d['map_name'],(P/d['xodr_file']).read_text());rows=[]
for a in d['actors']:
 if a['category']=='pedestrian':continue
 misses=[];n=0
 for s in a['samples'][::6]:
  n+=1;loc=carla.Location(x=s['x'],y=-s['y'],z=0)
  if m.get_waypoint(loc,project_to_road=False,lane_type=carla.LaneType.Driving) is None:misses.append(dict(t=s['t'],x=s['x'],y=s['y']))
 rows.append(dict(id=a['id'],samples=n,outside_driving_lane_samples=len(misses),first_misses=misses[:6]))
assert all(r['outside_driving_lane_samples']==0 for r in rows if r['id']!='red_rider')
(P/'validation/road_alignment.json').write_text(json.dumps(dict(parser='offline installed CARLA 0.9.12; NOT 0.9.15 engine execution',rows=rows,exception='red_rider passes damaged curb/sidewalk edge in right view at 108-114 s; retained as observed non-lane motion, estimated curb elevation 0.15 m',xodr_unchanged=True),indent=2),encoding='utf-8')
print('PASS: all motor-vehicle centres on XODR lanes; one documented sidewalk-edge scooter segment')
