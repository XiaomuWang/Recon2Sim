"""Shared estimated geometry, metres. Origin: change-lane area, road median."""
NAME='MeituanLane0512189'
XMIN=-150.0
XMAX=125.0
LANE=3.4
MEDIAN_HALF=.25
PAVED_HALF=10.7
LENGTH=XMAX-XMIN
SEGMENTS=[(10,-150.0,100.0),(20,-50.0,125.0),(30,75.0,50.0)]
def pose(s,t=0,zoff=0):return (s,t,zoff,0)
def lane_y(i):return (1 if i>0 else -1)*(MEDIAN_HALF+(abs(i)-.5)*LANE)
