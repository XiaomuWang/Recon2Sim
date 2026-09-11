import math
NAME='MeituanBrake0508656'
LANE=3.3
JX=-290.
ROADS=[
 dict(id=10,name='West_context',x=-390.,y=0.,h=0.,length=68.,n=2,w=LANE,median=1.2,junction_end='end'),
 dict(id=20,name='Incident_boulevard',x=-258.,y=0.,h=0.,length=458.,n=2,w=LANE,median=1.2,junction_end='start'),
 dict(id=30,name='Tree_lined_approach',x=JX,y=-310.,h=math.pi/2,length=278.,n=2,w=LANE,median=3.,junction_end='end'),
 dict(id=40,name='North_context',x=JX,y=32.,h=math.pi/2,length=78.,n=2,w=LANE,median=3.,junction_end='start')]
def road_point(r,s,t=0,z=0):
 return (r['x']+s*math.cos(r['h'])-t*math.sin(r['h']),r['y']+s*math.sin(r['h'])+t*math.cos(r['h']),z)
def pose(s,t=0,z=0):return s,t,z,0
def lane_t(r,lane):return (1 if lane>0 else -1)*(r['median']+(abs(lane)-1.5)*r['w'])
