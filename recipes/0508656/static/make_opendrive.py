import math,json,pathlib,xml.etree.ElementTree as E
from road_layout import *
OUT=pathlib.Path(__file__).resolve().parents[1]
def add(e,tag,**kw):return E.SubElement(e,tag,{k:str(v) for k,v in kw.items()})
root=E.Element('OpenDRIVE')
hd=add(root,'header',revMajor=1,revMinor=7,name=NAME,version='1.0',date='2026-09-08',north=130,south=-330,east=220,west=-410,vendor='Four-view visual reconstruction')
add(hd,'userData',code='accuracy',value='Visual estimates; uncalibrated cameras; no survey or GPS; flat ground; camera streams have independent timing and dropouts')
def base(rid,name,length,junc=-1,pred=None,succ=None):
 r=add(root,'road',name=name,length=f'{length:.9f}',id=rid,junction=junc,rule='RHT')
 if pred or succ:
  lk=add(r,'link')
  for tag,dat in [('predecessor',pred),('successor',succ)]:
   if dat:
    typ,i,cp=dat;a={'elementType':typ,'elementId':i}
    if typ=='road':a['contactPoint']=cp
    add(lk,tag,**a)
 ty=add(r,'type',s=0,type='town');add(ty,'speed',max=30,unit='km/h')
 return r
def profile(r):
 ep=add(r,'elevationProfile');add(ep,'elevation',s=0,a=0,b=0,c=0,d=0);add(r,'lateralProfile')
def lane(parent,i,w=0,typ='driving',mark='broken',color='white',links=None,b=0):
 la=add(parent,'lane',id=i,type=typ,level='false')
 if links:
  ll=add(la,'link')
  for tag,val in links.items():add(ll,tag,id=val)
 if i:add(la,'width',sOffset=0,a=w,b=b,c=0,d=0)
 add(la,'roadMark',sOffset=0,type=mark,weight='standard',color=color,width=.12,laneChange='both' if mark=='broken' else 'none')
 return la
# Median is a real border lane, so driving lane ids are +/-2 and +/-3.
for dat in ROADS:
 cp=dat['junction_end'];r=base(dat['id'],dat['name'],dat['length'],pred=('junction',1,None) if cp=='start' else None,succ=('junction',1,None) if cp=='end' else None)
 pv=add(r,'planView');add(add(pv,'geometry',s=0,x=dat['x'],y=dat['y'],hdg=dat['h'],length=dat['length']),'line');profile(r)
 ls=add(r,'lanes');sec=add(ls,'laneSection',s=0)
 for side,sg in [('left',1),('center',0),('right',-1)]:
  par=add(sec,side)
  if sg==0:lane(par,0,typ='none',mark='none');continue
  lane(par,sg,dat['median'],'border','solid','yellow')
  for i in range(1,dat['n']+1):lane(par,sg*(i+1),dat['w'],mark='broken' if i<dat['n'] else 'solid',color='white' if i<dat['n'] else 'yellow')
  lane(par,sg*4,2.,'biking','solid','yellow');lane(par,sg*5,1.6,'border','none');lane(par,sg*6,5.,'sidewalk','none')
 add(r,'userData',code='assumptions',value='Lane width and 30 km/h estimated. Opposite approaches and legal turns completed for simulation. Minor driveways decorative.')
ends={}
for key,dat in zip('ABCD',ROADS):
 cp=dat['junction_end'];sgn=-1 if cp=='end' else 1;s=dat['length'] if cp=='end' else 0
 def endpoint(i,out=False):
  lid=(-sgn if out else sgn)*(i+1);t=(dat['median']+(i-.5)*dat['w'])*(1 if lid>0 else -1);x,y,z=road_point(dat,s,t)
  return (x,y,dat['h']+(math.pi if lid>0 else 0),lid)
 ends[key]={'r':dat,'cp':cp,'in':[endpoint(i) for i in range(1,3)],'out':[endpoint(i,True) for i in range(1,3)]}
paths=[];conns=[]
moves=[('A','B',0,0),('A','B',1,1),('B','A',0,0),('B','A',1,1),('C','D',0,0),('C','D',1,1),('D','C',0,0),('D','C',1,1),('A','C',1,1),('A','D',0,0),('B','C',0,0),('B','D',1,1),('C','A',0,0),('C','B',1,1),('D','A',1,1),('D','B',0,0)]
for idx,(aa,bb,li,lj) in enumerate(moves):
 a=ends[aa];b=ends[bb];p=a['in'][li];q=b['out'][lj];rid=100+idx;d=math.hypot(q[0]-p[0],q[1]-p[1])/2.1
 P=[p[:2],(p[0]+d*math.cos(p[2]),p[1]+d*math.sin(p[2])),(q[0]-d*math.cos(q[2]),q[1]-d*math.sin(q[2])),q[:2]]
 def bez(t):return tuple((1-t)**3*P[0][j]+3*(1-t)**2*t*P[1][j]+3*(1-t)*t*t*P[2][j]+t**3*P[3][j] for j in [0,1])
 pp=[bez(k/2000) for k in range(2001)];length=sum(math.dist(u,v) for u,v in zip(pp,pp[1:]))
 r=base(rid,aa+'_to_'+bb+'_lane'+str(li+1),length,1,('road',a['r']['id'],a['cp']),('road',b['r']['id'],b['cp']))
 pv=add(r,'planView');g=add(pv,'geometry',s=0,x=p[0],y=p[1],hdg=p[2],length=length)
 local=[((u-p[0])*math.cos(p[2])+(v-p[1])*math.sin(p[2]),-(u-p[0])*math.sin(p[2])+(v-p[1])*math.cos(p[2])) for u,v in P]
 cf=[]
 for j in [0,1]:
  v=[pt[j] for pt in local];cf.append((v[0],3*(v[1]-v[0]),3*(v[2]-2*v[1]+v[0]),v[3]-3*v[2]+3*v[1]-v[0]))
 add(g,'paramPoly3',aU=cf[0][0],bU=cf[0][1],cU=cf[0][2],dU=cf[0][3],aV=cf[1][0],bV=cf[1][1],cV=cf[1][2],dV=cf[1][3],pRange='normalized');profile(r)
 w=a['r']['w'];ls=add(r,'lanes');add(ls,'laneOffset',s=0,a=w/2,b=0,c=0,d=0);sec=add(ls,'laneSection',s=0);lane(add(sec,'center'),0,typ='none',mark='none');lane(add(sec,'right'),-1,w,mark='none',links={'predecessor':p[3],'successor':q[3]})
 conns.append((rid,a['r']['id'],p[3]));paths.append({'id':rid,'from':a['r']['id'],'to':b['r']['id'],'start_lane':p[3],'end_lane':q[3],'points':pp[::10],'width_start':w,'width_end':w})
j=add(root,'junction',name='Observed_right_turn_intersection',id=1,type='default')
for i,(rid,inc,ln) in enumerate(conns):
 c=add(j,'connection',id=i,incomingRoad=inc,connectingRoad=rid,contactPoint='start');add(c,'laneLink',**{'from':ln,'to':-1})
add(j,'userData',code='signals',value='Static FBX furniture only. Functional traffic signals and timing must be configured in Unreal.')
from xml.dom import minidom
(OUT/(NAME+'.xodr')).write_bytes(minidom.parseString(E.tostring(root)).toprettyxml(indent='  ',encoding='utf-8'))
(OUT/'validation/junction_paths.json').write_text(json.dumps(paths))
(OUT/'road_parameters.json').write_text(json.dumps({'roads':ROADS,'incident_xyz_rh':[0,-2.85,0],'bridge_x_m':58,'coordinate_system':'RH meters; X=post-turn forward, Y=left; CARLA=(X,-Y,Z)','accuracy':'estimated, not surveyed','observed_route':{'roads':[30,113,20],'lanes':[-3,-1,-3]}},indent=2))
(OUT/(NAME+'Package.json')).write_text(json.dumps({'maps':[{'name':NAME,'source':NAME+'.fbx','xodr':NAME+'.xodr','use_carla_materials':False}],'props':[]},indent=2))
print('Generated 4 approaches + 16 connectors; observed right turn 30/-3 -> 113/-1 -> 20/-3')
