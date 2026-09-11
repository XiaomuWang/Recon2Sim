"""Four-view visual estimates, not survey. Shared FBX / OpenDRIVE metre geometry."""
import math
NAME='RainJunctionANA031'
XMIN=-170.; XMAX=160.; JX=47.; JHALF=22.
LANE=3.5; WIDTH=28.; PAVED_HALF=14.7; CURB=14.85; WALK_OUT=20.5
SIDE_W=3.5; SIDE_END=100.; SIDE_JOIN=16.
LENGTH=XMAX-XMIN
ACCESSES=[]
def pose(s,t=0,zoff=0):return (s,t,zoff,0)
def in_junction(x):return abs(x-JX)<JHALF
def in_access(x):return in_junction(x)
ROADS=[
 {'id':10,'name':'West_incident_approach','x':XMIN,'y':0,'h':0,'length':JX-JHALF-XMIN,'n':4,'w':LANE,'junction_end':'end'},
 {'id':20,'name':'East_exit','x':JX+JHALF,'y':0,'h':0,'length':XMAX-JX-JHALF,'n':4,'w':LANE,'junction_end':'start'},
 {'id':30,'name':'South_cross_street','x':JX,'y':-SIDE_END,'h':math.pi/2,'length':SIDE_END-SIDE_JOIN,'n':3,'w':SIDE_W,'junction_end':'end'},
 {'id':40,'name':'North_cross_street','x':JX,'y':SIDE_JOIN,'h':math.pi/2,'length':SIDE_END-SIDE_JOIN,'n':3,'w':SIDE_W,'junction_end':'start'}]
def road_point(r,s,t=0):return (r['x']+s*math.cos(r['h'])-t*math.sin(r['h']),r['y']+s*math.sin(r['h'])+t*math.cos(r['h']),0)
