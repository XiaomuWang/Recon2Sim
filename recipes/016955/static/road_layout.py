"""Estimated local RH metre coordinates; origin at second T junction; east along approach."""
import math
NAME='GreenRail016955'
LANE=3.5
# Each ordinary road reference runs in +X or +Y, all at z=0.
ROADS={
 10:dict(name='Boulevard_bus_stop_approach',x=-180.,y=-200.,h=math.pi/2,length=180.,n=3,median=1.2,succ=1),
 11:dict(name='Boulevard_north_context',x=-180.,y=20.,h=math.pi/2,length=100.,n=3,median=1.2,pred=1),
 20:dict(name='Elevated_guideway_street',x=-160.,y=0.,h=0.,length=140.,n=1,median=0.,pred=1,succ=2),
 30:dict(name='Green_hoarding_exit',x=0.,y=-200.,h=math.pi/2,length=180.,n=1,median=0.,succ=2),
 31:dict(name='Guideway_street_east_continuation',x=20.,y=0.,h=0.,length=50.,n=1,median=0.,pred=2),
}
def pose(rid,s,t=0,z=0):
 r=ROADS[rid];h=r['h'];return (r['x']+s*math.cos(h)-t*math.sin(h),r['y']+s*math.sin(h)+t*math.cos(h),z,h)
def lane_id(rid,side,ordinal=1):return side*(ordinal+(1 if ROADS[rid]['median'] else 0))
def lane_t(rid,lid):
 r=ROADS[rid];i=abs(lid)-(1 if r['median'] else 0);return math.copysign(r['median']+(i-.5)*LANE,lid)
def endpoint(rid,cp,incoming,ordinal=1):
 # RHT traffic: negative lanes follow reference, positive lanes oppose it.
 side=-1 if (cp=='end')==incoming else 1;lid=lane_id(rid,side,ordinal)
 p=pose(rid,0 if cp=='start' else ROADS[rid]['length'],lane_t(rid,lid))
 return dict(rid=rid,cp=cp,lane=lid,p=(p[0],p[1],p[3]+(math.pi if lid>0 else 0)))
JUNCTIONS={1:dict(name='Boulevard_first_right_turn',arms=[(10,'end'),(11,'start'),(20,'start')]),2:dict(name='Green_hoarding_second_right_turn',arms=[(20,'end'),(31,'start'),(30,'end')])}
def maneuvers():
 result=[]
 for jid,j in JUNCTIONS.items():
  arms=j['arms'];idx=0
  for a in arms:
   for b in arms:
    if a==b:continue
    through=jid==1 and a[0] in [10,11] and b[0] in [10,11]
    for ordinal in (range(1,4) if through else [1]):
     # Turn to branch from boulevard outer lane; left turn from inner lane.
     ai=ordinal;bi=ordinal
     if jid==1 and not through:
      if a[0]==10:ai=3
      if b[0]==11:bi=3
     aa=endpoint(*a,True,ai);bb=endpoint(*b,False,bi)
     p=aa['p'];q=bb['p'];dist=math.hypot(q[0]-p[0],q[1]-p[1])
     d=dist/2.25 if abs(math.sin(q[2]-p[2]))>.5 else dist/3
     control=[p[:2],(p[0]+d*math.cos(p[2]),p[1]+d*math.sin(p[2])),(q[0]-d*math.cos(q[2]),q[1]-d*math.sin(q[2])),q[:2]]
     dh=(q[2]-p[2]+math.pi)%math.tau-math.pi
     if abs(dh)<.01:segments=[dict(x=p[0],y=p[1],h=p[2],length=dist,k=0)]
     else:
      sign=1 if dh>0 else -1
      U=(q[0]-p[0])*math.cos(p[2])+(q[1]-p[1])*math.sin(p[2]);V=-(q[0]-p[0])*math.sin(p[2])+(q[1]-p[1])*math.cos(p[2])
      radius=(6.25 if jid==1 else 8.75) if sign<0 else min(14.,U,abs(V))
      segments=[];x,y,h=p
      for ll,k in [(U-radius,0),(radius*math.pi/2,sign/radius),(abs(V)-radius,0)]:
       if ll<.000001:continue
       segments.append(dict(x=x,y=y,h=h,length=ll,k=k))
       if k:x+=(math.sin(h+k*ll)-math.sin(h))/k;y-=(math.cos(h+k*ll)-math.cos(h))/k;h+=k*ll
       else:x+=ll*math.cos(h);y+=ll*math.sin(h)
      assert math.hypot(x-q[0],y-q[1])<1e-6
     result.append(dict(id=100*jid+idx,junction=jid,a=aa,b=bb,control=control,segments=segments));idx+=1
 return result
def bez(P,t):return tuple((1-t)**3*P[0][j]+3*(1-t)**2*t*P[1][j]+3*(1-t)*t*t*P[2][j]+t**3*P[3][j] for j in [0,1])
def tangent(P,t):
 v=[3*(1-t)**2*(P[1][j]-P[0][j])+6*(1-t)*t*(P[2][j]-P[1][j])+3*t*t*(P[3][j]-P[2][j]) for j in [0,1]]
 return math.atan2(v[1],v[0])
