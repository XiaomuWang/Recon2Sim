"""Editable road-bound actor reconstruction on the GENERATED OpenDRIVE.

route_overrides in configs/SCENE.json may bind an actor to road/lane sections:
{"ego": {"sections": [{"road_id":10,"lane_id":-1,"s_start":2,"s_end":80}],
          "time_station": [[0,0],[5,20],[12,78]], "lateral_offset_m":0}}
Stations advance in the supplied section order. Never re-snap unrelated actors.
"""
import math
import carla
import numpy as np
from scipy.interpolate import PchipInterpolator


def sample_route(xodr, spec, fps=30):
    m=carla.Map('route_binding',xodr.read_text(encoding='utf-8'))
    sections=spec['sections'];lengths=[abs(s['s_end']-s['s_start']) for s in sections]
    cumulative=np.r_[0,np.cumsum(lengths)];keys=np.array(spec['time_station'],float)
    if any(x<=0 for x in lengths) or len(keys)<2 or np.any(np.diff(keys[:,0])<=0):
        raise ValueError('Invalid route sections/keyframe times')
    if np.any(np.diff(keys[:,1])<0) or keys[:,1].min()<0 or keys[:,1].max()>cumulative[-1]:
        raise ValueError('Route station must be monotone and inside section length')
    func=PchipInterpolator(keys[:,0],keys[:,1],extrapolate=False);samples=[]
    times=np.linspace(keys[0,0],keys[-1,0],round((keys[-1,0]-keys[0,0])*fps)+1)
    # Reject gaps; a continuous visual route must not teleport between roads.
    for a,b in zip(sections,sections[1:]):
        u=m.get_waypoint_xodr(a['road_id'],a['lane_id'],a['s_end'])
        v=m.get_waypoint_xodr(b['road_id'],b['lane_id'],b['s_start'])
        if u is None or v is None or u.transform.location.distance(v.transform.location)>1:
            raise ValueError('Disconnected route sections; add the actual junction connecting road')
    for t in times:
        q=float(func(t));i=min(len(sections)-1,int(np.searchsorted(cumulative,q,side='right')-1))
        section=sections[i];sign=1 if section['s_end']>section['s_start'] else -1
        s=section['s_start']+sign*(q-cumulative[i]);wp=m.get_waypoint_xodr(section['road_id'],section['lane_id'],s)
        if wp is None:raise ValueError('Unknown OpenDRIVE road/lane/station')
        loc=wp.transform.location;h=math.radians(wp.transform.rotation.yaw)
        # CARLA lane yaw points in lane travel direction; reversing station may reverse travel.
        default_sign=1 if section['lane_id']<0 else -1
        if sign!=default_sign:h+=math.pi
        offset=spec.get('lateral_offset_m',0)
        x=loc.x-math.sin(h)*offset;y=loc.y+math.cos(h)*offset
        samples.append(dict(t=round(float(t),6),x=x,y=-y,z=loc.z,h=-h,s=s,lateral=offset))
    return samples
