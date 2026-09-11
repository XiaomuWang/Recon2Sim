import math,json,pathlib,xml.etree.ElementTree as E
from xml.dom import minidom
from road_layout import *
P=pathlib.Path(__file__).resolve().parents[1]
def add(e,tag,**kw):return E.SubElement(e,tag,{k:str(v) for k,v in kw.items()})
root=E.Element('OpenDRIVE')
head=add(root,'header',revMajor=1,revMinor=7,name=NAME,version='1.0',date='2026-09-08',north=100,south=-115,east=75,west=-195,vendor='Four-view visual reconstruction')
add(head,'userData',code='accuracy',value='Video referenced estimated scale; no calibration, survey or georeference')
def base(rid,name,length,junc=-1,pred=None,succ=None):
 r=add(root,'road',name=name,length=length,id=rid,junction=junc,rule='RHT')
 lk=add(r,'link')
 for tag,dat in [('predecessor',pred),('successor',succ)]:
  if dat:
   typ,i,cp=dat;a={'elementType':typ,'elementId':i}
   if typ=='road':a['contactPoint']=cp
   add(lk,tag,**a)
 ty=add(r,'type',s=0,type='town');add(ty,'speed',max=15,unit='km/h')
 return r
def geom(r,x,y,h,L,k=0):
 pv=add(r,'planView');g=add(pv,'geometry',s=0,x=x,y=y,hdg=h,length=L)
 add(g,'arc',curvature=k) if k else add(g,'line')
 ep=add(r,'elevationProfile');add(ep,'elevation',s=0,a=0,b=0,c=0,d=0);add(r,'lateralProfile')
def lane(parent,i,mark='none',color='white',links=None):
 la=add(parent,'lane',id=i,type='driving' if i else 'none',level='false')
 if links:
  lk=add(la,'link')
  for tag,ln in links.items():add(lk,tag,id=ln)
 if i:add(la,'width',sOffset=0,a=LANE,b=0,c=0,d=0)
 add(la,'roadMark',sOffset=0,type=mark,weight='standard',color=color,width=.1,laneChange='none')
def lanes(r,single=False,pre=None,succ=None):
 ls=add(r,'lanes')
 if single:add(ls,'laneOffset',s=0,a=LANE/2,b=0,c=0,d=0)
 sec=add(ls,'laneSection',s=0)
 if not single:lane(add(sec,'left'),1,'solid','yellow')
 lane(add(sec,'center'),0,'none' if single else 'solid solid','yellow')
 lane(add(sec,'right'),-1,'none' if single else 'solid','yellow',{'predecessor':pre,'successor':succ} if single else None)
for r in ROADS:
 cp=r['junction_end'];out=base(r['id'],r['name'],r['length'],pred=('junction',1,None) if cp=='start' else None,succ=('junction',1,None) if cp=='end' else None)
 geom(out,r['x'],r['y'],r['h'],r['length']);lanes(out)
 add(out,'userData',code='evidence',value='Approach double yellow and two-way street visible. Cross-street centerline, 3.3m lane widths and 15km/h are editable simulation assumptions.')
ends={}
for key,r in zip('ABC',ROADS):
 cp=r['junction_end'];sgn=-1 if cp=='end' else 1;s=r['length'] if cp=='end' else 0
 def endpoint(out=False):
  ln=-sgn if out else sgn;x,y,_=road_point(r,s,ln*LANE/2);h=r['h']+(math.pi if ln>0 else 0);return (x,y,h,ln)
 ends[key]={'r':r,'cp':cp,'in':endpoint(),'out':endpoint(True)}
paths=[];conns=[]
for i,(aa,bb) in enumerate([('A','B'),('B','A'),('A','C'),('C','A'),('B','C'),('C','B')]):
 a,b=ends[aa],ends[bb];p,q=a['in'],b['out'];delta=(q[2]-p[2]+math.pi)%(2*math.pi)-math.pi
 if abs(delta)<1e-8:k=0.;L=math.hypot(q[0]-p[0],q[1]-p[1])
 else:R=math.hypot(q[0]-p[0],q[1]-p[1])/math.sqrt(2);k=(1 if delta>0 else -1)/R;L=abs(delta/k)
 rid=100+i
 segments=None
 if i in [0,3]:
  lead=3.7;radius=6.65;arcL=radius*math.pi/2
  first={'x':p[0],'y':p[1],'h':p[2],'k':0,'length':lead};end=path_pose(first,lead)
  arc={'x':end[0],'y':end[1],'h':end[3],'k':-1/radius,'length':arcL};end=path_pose(arc,arcL)
  last={'x':end[0],'y':end[1],'h':end[3],'k':0,'length':lead};segments=[first,arc,last];L=lead*2+arcL
 r=base(rid,aa+'_to_'+bb,L,1,('road',a['r']['id'],a['cp']),('road',b['r']['id'],b['cp']))
 geom(r,p[0],p[1],p[2],L,k)
 if segments:
  pv=r.find('planView');pv.clear();station=0
  for part in segments:
   g=add(pv,'geometry',s=station,x=part['x'],y=part['y'],hdg=part['h'],length=part['length'])
   add(g,'arc',curvature=part['k']) if part['k'] else add(g,'line');station+=part['length']
 lanes(r,True,p[3],q[3])
 rec={'id':rid,'from':a['r']['id'],'to':b['r']['id'],'start_lane':p[3],'end_lane':q[3],'x':p[0],'y':p[1],'h':p[2],'k':k,'length':L}
 if segments:rec['segments']=segments
 rec['points']=[path_pose(rec,L*j/160)[:2] for j in range(161)];paths.append(rec);conns.append((rid,a['r']['id'],p[3]))
j=add(root,'junction',name='Construction_gate_T_junction',id=1,type='default')
for i,(rid,inc,ln) in enumerate(conns):
 c=add(j,'connection',id=i,incomingRoad=inc,connectingRoad=rid,contactPoint='start');add(c,'laneLink',**{'from':ln,'to':-1})
add(j,'userData',code='traffic',value='All six turn/through connections included for simulation. Gate across street is closed static environment and not navigable. No traffic-signal phasing inferred.')
(P/(NAME+'.xodr')).write_text(minidom.parseString(E.tostring(root)).toprettyxml(indent='  '),encoding='utf-8')
(P/'validation/junction_paths.json').write_text(json.dumps(paths,indent=2))
(P/'road_parameters.json').write_text(json.dumps({'roads':ROADS,'junction_origin':[0,0,0],'lane_width_m':LANE,'road_width_m':2*LANE,'curb_height_m':.16,'corner_radius_m':5,'gate_center':[8.7,0,0],'hotel_corner':[-10,-10,0],'right_turn_road':100,'right_turn_radius_m':6.65,'coordinate_system':'RH metre; +X toward gate on approach, +Y left, Z up; CARLA=(X,-Y,Z); Unreal cm=(100X,-100Y,100Z)','accuracy':'Estimated widths, distances, elevations, facade sizes, tree spacing and turn rules; no survey. Flat ground assumption.'},indent=2))
(P/(NAME+'Package.json')).write_text(json.dumps({'maps':[{'name':NAME,'source':NAME+'.fbx','xodr':NAME+'.xodr','use_carla_materials':False}],'props':[]},indent=2))
print('Created 3 streets, 6 exact arc/line connectors and 1 T-junction.')
