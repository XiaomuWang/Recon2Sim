"""Shared metric geometry for mesh and OpenDRIVE. No surveyed coordinates."""
import math
LENGTH=210.0
WIDTH=5.8
GATE_S=100.0
def pose(s,t=0,zoff=0):
    if s<70:
        k=.18/70;h=-.18+k*s
        x=-30+math.sin(h)/k;y=(1-math.cos(h))/k
    elif s<=155:
        x=s-100;y=0;h=0
    else:
        h=(s-155)/90;x=55+90*math.sin(h);y=90*(1-math.cos(h))
    if s<90:
        u=max(0,s)/90;z=4.5*(1-3*u*u+2*u*u*u)
    else:z=0
    return (x-math.sin(h)*t,y+math.cos(h)*t,z+zoff,h)
def pieces(a,b):
    cuts=sorted(set([a,b]+[v for v in [70,155] if a<v<b]))
    return [(u,v-u,pose(u),.18/70 if u<70 else (0 if u<155 else 1/90)) for u,v in zip(cuts,cuts[1:])]
def elevations(a,b):
    ans=[]
    if a<90:
        ans.append((0,4.5-13.5*a*a/8100+9*a*a*a/729000,-27*a/8100+27*a*a/729000,-13.5/8100+27*a/729000,9/729000))
    else:ans.append((0,0,0,0,0))
    if a<90<b:ans.append((90-a,0,0,0,0))
    return ans
