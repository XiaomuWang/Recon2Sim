"""Shared visual reconstruction parameters, metres, right handed. Not survey data."""
import math
NAME='UrbanBrake019742'
XMIN=-400.0
XMAX=100.0
JX=-120.0
JHALF=12.0
LANE=3.3
WIDTH=13.2
PAVED_HALF=9.0
CURB=9.15
WALK_OUT=14.0
LENGTH=XMAX-XMIN
SIDE_W=3.25
SIDE_END=65.0
SIDE_JOIN=10.0
# Minor accesses are observed visually but not surveyed or represented as navigable junctions.
ACCESSES=[(-340,6.0),(-230,5.0),(-38,5.0)]
def pose(s,t=0,zoff=0):return (s,t,zoff,0)
def in_access(x):return any(abs(x-a)<w for a,w in ACCESSES) or abs(x-JX)<JHALF
def in_junction(x):return abs(x-JX)<JHALF
ROADS=[
 {'id':10,'name':'West_approach','x':XMIN,'y':0,'h':0,'length':JX-JHALF-XMIN,'n':2,'w':LANE,'junction_end':'end'},
 {'id':20,'name':'East_incident_corridor','x':JX+JHALF,'y':0,'h':0,'length':XMAX-JX-JHALF,'n':2,'w':LANE,'junction_end':'start'},
 {'id':30,'name':'South_cross_street','x':JX,'y':-SIDE_END,'h':math.pi/2,'length':SIDE_END-SIDE_JOIN,'n':1,'w':SIDE_W,'junction_end':'end'},
 {'id':40,'name':'North_cross_street','x':JX,'y':SIDE_JOIN,'h':math.pi/2,'length':SIDE_END-SIDE_JOIN,'n':1,'w':SIDE_W,'junction_end':'start'}]
def road_point(r,s,t=0):return (r['x']+s*math.cos(r['h'])-t*math.sin(r['h']),r['y']+s*math.sin(r['h'])+t*math.cos(r['h']),0)
