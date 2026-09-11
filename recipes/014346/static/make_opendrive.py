import math,json,pathlib,xml.etree.ElementTree as E
from road_layout import *
OUT=pathlib.Path(__file__).resolve().parents[1]
NAME='NanshanGate014346'
def add(e,tag,**kw):return E.SubElement(e,tag,{k:str(v) for k,v in kw.items()})
root=E.Element('OpenDRIVE')
head=add(root,'header',revMajor=1,revMinor=7,name=NAME,version='1.0',date='2026-09-08',north=95,south=-70,east=170,west=-450,vendor='Four-view environment reconstruction')
add(head,'userData',code='accuracy',value='Visual reconstruction; estimated metric scale; no georeference; not surveyed')
def base(rid,name,length,junc=-1,pred=None,succ=None):
 r=add(root,'road',name=name,length=f'{length:.9f}',id=rid,junction=junc,rule='RHT')
 if pred or succ:
  lk=add(r,'link')
  for tag,dat in [('predecessor',pred),('successor',succ)]:
   if dat:
    typ,i,cp=dat;a={'elementType':typ,'elementId':i}
    if typ=='road':a['contactPoint']=cp
    add(lk,tag,**a)
 ty=add(r,'type',s=0,type='town');add(ty,'speed',max=20,unit='km/h')
 return r
def lanes(r,center='solid',color='yellow',single=False,prelane=None,suclane=None):
 ls=add(r,'lanes')
 if single:add(ls,'laneOffset',s=0,a=WIDTH/4,b=0,c=0,d=0)
 sec=add(ls,'laneSection',s=0)
 def lane(parent,i,typ='driving'):
  la=add(parent,'lane',id=i,type=typ,level='false')
  if i:
   if prelane is not None or suclane is not None:
    ll=add(la,'link')
    if prelane is not None:add(ll,'predecessor',id=prelane)
    if suclane is not None:add(ll,'successor',id=suclane)
   add(la,'width',sOffset=0,a=WIDTH/2,b=0,c=0,d=0)
  add(la,'roadMark',sOffset=0,type=(center if i==0 else ('none' if single else 'solid')),weight='standard',color=color if i==0 else 'white',width=.12 if i==0 else .1,laneChange='none')
  return la
 if not single:lane(add(sec,'left'),1)
 lane(add(sec,'center'),0,'none')
 lane(add(sec,'right'),-1)
 return ls
for rid,n,a,b,pr,su in [(10,'Descending_access_approach',0,92,None,('junction',1,None)),(20,'Retaining_wall_curve',108,210,('junction',1,None),None)]:
 r=base(rid,n,b-a,pred=pr,succ=su);pv=add(r,'planView')
 for s,l,p,k in pieces(a,b):
  g=add(pv,'geometry',s=s-a,x=p[0],y=p[1],hdg=p[3],length=l)
  add(g,'arc',curvature=k) if k else add(g,'line')
 ep=add(r,'elevationProfile')
 for s,aa,bb,c,d in elevations(a,b):add(ep,'elevation',s=s,a=aa,b=bb,c=c,d=d)
 add(r,'lateralProfile');lanes(r,color='white' if rid==10 else 'yellow')
 add(r,'userData',code='evidence',value='front/rear/left/right 52-155 sec; width, curvature, grade estimated')
r=base(30,'Construction_gate_driveway',25,succ=('junction',1,None));pv=add(r,'planView');add(add(pv,'geometry',s=0,x=0,y=-32,hdg=math.pi/2,length=25),'line')
ep=add(r,'elevationProfile');add(ep,'elevation',s=0,a=0,b=0,c=0,d=0);add(r,'lateralProfile');lanes(r,center='none')
add(r,'userData',code='evidence',value='right 68-75 sec; opening observed; interior drive alignment inferred beyond occlusion')
# Each maneuver reference follows the lane center; laneOffset=width/2 places lane -1 center on reference.
ends={'A':{'rid':10,'cp':'end','in':(-8,-WIDTH/4,0),'out':(-8,WIDTH/4,math.pi),'inlane':-1,'outlane':1},
      'B':{'rid':20,'cp':'start','in':(8,WIDTH/4,math.pi),'out':(8,-WIDTH/4,0),'inlane':1,'outlane':-1},
      'C':{'rid':30,'cp':'end','in':(WIDTH/4,-7,math.pi/2),'out':(-WIDTH/4,-7,-math.pi/2),'inlane':-1,'outlane':1}}
conn=[];check=[]
for i,(aa,bb) in enumerate([('A','B'),('B','A'),('A','C'),('C','A'),('B','C'),('C','B')]):
 a=ends[aa];b=ends[bb];p=a['in'];q=b['out'];rid=100+i
 distance=math.hypot(q[0]-p[0],q[1]-p[1]);d=distance/2.3
 P=[(p[0],p[1]),(p[0]+d*math.cos(p[2]),p[1]+d*math.sin(p[2])),(q[0]-d*math.cos(q[2]),q[1]-d*math.sin(q[2])),(q[0],q[1])]
 def bez(t):return tuple((1-t)**3*P[0][j]+3*(1-t)**2*t*P[1][j]+3*(1-t)*t*t*P[2][j]+t**3*P[3][j] for j in [0,1])
 pp=[bez(j/2000) for j in range(2001)];length=sum(math.dist(u,v) for u,v in zip(pp,pp[1:]))
 r=base(rid,aa+'_to_'+bb,length,1,('road',a['rid'],a['cp']),('road',b['rid'],b['cp']))
 pv=add(r,'planView');g=add(pv,'geometry',s=0,x=p[0],y=p[1],hdg=p[2],length=length)
 local=[((u-p[0])*math.cos(p[2])+(v-p[1])*math.sin(p[2]),-(u-p[0])*math.sin(p[2])+(v-p[1])*math.cos(p[2])) for u,v in P]
 coeff=[]
 for j in [0,1]:
  v=[pt[j] for pt in local];coeff.append((v[0],3*(v[1]-v[0]),3*(v[2]-2*v[1]+v[0]),v[3]-3*v[2]+3*v[1]-v[0]))
 add(g,'paramPoly3',aU=coeff[0][0],bU=coeff[0][1],cU=coeff[0][2],dU=coeff[0][3],aV=coeff[1][0],bV=coeff[1][1],cV=coeff[1][2],dV=coeff[1][3],pRange='normalized')
 ep=add(r,'elevationProfile');add(ep,'elevation',s=0,a=0,b=0,c=0,d=0);add(r,'lateralProfile');lanes(r,center='none',single=True,prelane=a['inlane'],suclane=b['outlane'])
 conn.append((rid,a['rid'],a['inlane']));check.append({'id':rid,'from':a['rid'],'to':b['rid'],'points':pp[::20],'start_lane':a['inlane'],'end_lane':b['outlane']})
j=add(root,'junction',name='Observed_construction_gate',id=1,type='default')
for i,(rid,inc,ln) in enumerate(conn):
 c=add(j,'connection',id=i,incomingRoad=inc,connectingRoad=rid,contactPoint='start');add(c,'laneLink',**{'from':ln,'to':-1})
add(j,'userData',code='lane_semantics',value='Two narrow opposing lanes are an editable simulation assumption; legal traffic organization was not readable in source')
E.indent(root,space='  ');E.ElementTree(root).write(OUT/(NAME+'.xodr'),encoding='utf-8',xml_declaration=True)
(OUT/'validation').mkdir(exist_ok=True)
(OUT/'validation'/'junction_paths.json').write_text(json.dumps(check,indent=2))
(OUT/'road_parameters.json').write_text(json.dumps({'length_m':LENGTH,'paved_width_m':WIDTH,'lane_width_m':WIDTH/2,'gate_station_m':GATE_S,'gate_clear_width_m':12,'wall_offset_m':4.25,'hoarding_offset_m':-4.05,'wall_height_m':[2.6,5.0],'hoarding_height_m':3.2,'coordinate_system':'right handed X forward at gate, Y left, Z up; metre; CARLA y=-Y','accuracy':'estimated; no calibration, metric control points or survey'},indent=2))
print('OpenDRIVE created: 3 roads, 6 maneuvers, 1 junction')
