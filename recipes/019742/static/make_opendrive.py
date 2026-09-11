import math,json,pathlib,xml.etree.ElementTree as E
from road_layout import *
OUT=pathlib.Path(__file__).resolve().parents[1]
def add(e,tag,**kw):return E.SubElement(e,tag,{k:str(v) for k,v in kw.items()})
root=E.Element('OpenDRIVE')
head=add(root,'header',revMajor=1,revMinor=7,name=NAME,version='1.0',date='2026-09-08',north=100,south=-100,east=120,west=-420,vendor='Four-view visual reconstruction')
add(head,'userData',code='accuracy',value='Estimated visual reconstruction, no calibrated cameras or survey georeference')
def base(rid,name,length,junc=-1,pred=None,succ=None):
 r=add(root,'road',name=name,length='%.9f'%length,id=rid,junction=junc,rule='RHT')
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
for dat in ROADS:
 cp=dat['junction_end'];r=base(dat['id'],dat['name'],dat['length'],pred=('junction',1,None) if cp=='start' else None,succ=('junction',1,None) if cp=='end' else None)
 pv=add(r,'planView');add(add(pv,'geometry',s=0,x=dat['x'],y=dat['y'],hdg=dat['h'],length=dat['length']),'line');profile(r)
 ls=add(r,'lanes');sec=add(ls,'laneSection',s=0)
 left=add(sec,'left')
 for i in range(1,dat['n']+1):lane(left,i,dat['w'],mark='broken' if i<dat['n'] else 'solid')
 shoulder=PAVED_HALF-WIDTH/2 if dat['n']==2 else 1.25
 lane(left,dat['n']+1,shoulder,'shoulder','none');lane(left,dat['n']+2,.3,'border','none');lane(left,dat['n']+3,4.7 if dat['n']==2 else 3.0,'sidewalk','none')
 lane(add(sec,'center'),0,typ='none',mark='solid',color='yellow')
 right=add(sec,'right')
 for i in range(1,dat['n']+1):lane(right,-i,dat['w'],mark='broken' if i<dat['n'] else 'solid')
 lane(right,-dat['n']-1,shoulder,'shoulder','none');lane(right,-dat['n']-2,.3,'border','none');lane(right,-dat['n']-3,4.7 if dat['n']==2 else 3.0,'sidewalk','none')
 add(r,'userData',code='traffic_assumption',value='Two main lanes per direction and one side-street lane per direction; widths, legal turn rules and 30 km/h provisional')
# Junction has two through main lanes and a single lane per cross-street direction.
ends={}
for key,dat in zip('ABCD',ROADS):
 cp=dat['junction_end'];sgn=-1 if cp=='end' else 1;s=dat['length'] if cp=='end' else 0
 def endpoint(i,out=False):
  lid=(-sgn if out else sgn)*i;t=(abs(lid)-.5)*dat['w']*(1 if lid>0 else -1);x,y,z=road_point(dat,s,t)
  h=dat['h']+(math.pi if lid>0 else 0);return (x,y,h,lid)
 ends[key]={'r':dat,'cp':cp,'in':[endpoint(i) for i in range(1,dat['n']+1)],'out':[endpoint(i,True) for i in range(1,dat['n']+1)]}
paths=[];conns=[]
moves=[('A','B',0,0),('A','B',1,1),('B','A',0,0),('B','A',1,1),('C','D',0,0),('D','C',0,0),('A','C',1,0),('A','D',0,0),('B','C',0,0),('B','D',1,0),('C','A',0,1),('C','B',0,1),('D','A',0,1),('D','B',0,1)]
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
 w=a['r']['w'];dw=(b['r']['w']-w)/length
 ls=add(r,'lanes');add(ls,'laneOffset',s=0,a=w/2,b=dw/2,c=0,d=0);sec=add(ls,'laneSection',s=0);lane(add(sec,'center'),0,typ='none',mark='none');lane(add(sec,'right'),-1,w,mark='none',links={'predecessor':p[3],'successor':q[3]},b=dw)
 conns.append((rid,a['r']['id'],p[3]));paths.append({'id':rid,'from':a['r']['id'],'to':b['r']['id'],'start_lane':p[3],'end_lane':q[3],'points':pp[::10],'width_start':w,'width_end':b['r']['w']})
j=add(root,'junction',name='Observed_signalized_crossroads',id=1,type='default')
for i,(rid,inc,ln) in enumerate(conns):
 c=add(j,'connection',id=i,incomingRoad=inc,connectingRoad=rid,contactPoint='start');add(c,'laneLink',**{'from':ln,'to':-1})
add(j,'userData',code='signalization',value='Signal furniture in FBX only; configure functional CARLA traffic-light actors and phases in Unreal')
E.indent(root,space='  ');E.ElementTree(root).write(OUT/(NAME+'.xodr'),encoding='utf-8',xml_declaration=True)
(OUT/'validation/junction_paths.json').write_text(json.dumps(paths,indent=2))
(OUT/'road_parameters.json').write_text(json.dumps({'main_extent_x_m':[XMIN,XMAX],'main_lane_width_m':LANE,'main_driving_width_m':WIDTH,'paved_halfwidth_m':PAVED_HALF,'junction_center_x_m':JX,'side_street_lane_width_m':SIDE_W,'incident_reference_xyz':[0,-4.95,0],'right_panel_y_m':-6.95,'center_barrier_y_m':0,'curb_y_abs_m':9.15,'facade_y_abs_m':14.5,'coordinate_system':'RH metres, +X ego forward, +Y ego left, +Z up; CARLA=(X,-Y,Z)','accuracy':'all metric dimensions estimated from four views; no survey; main street straightened; flat elevation assumed','minor_visual_accesses':ACCESSES},indent=2))
(OUT/(NAME+'Package.json')).write_text(json.dumps({'maps':[{'name':NAME,'source':NAME+'.fbx','xodr':NAME+'.xodr','use_carla_materials':False}],'props':[]},indent=2))
print('Generated 4 approach roads, 14 connectors, 1 junction')
