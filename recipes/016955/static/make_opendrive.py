import math,json,pathlib,xml.etree.ElementTree as E
from road_layout import *
OUT=pathlib.Path(__file__).resolve().parents[1]
def add(e,tag,**kw):return E.SubElement(e,tag,{k:str(v) for k,v in kw.items()})
root=E.Element('OpenDRIVE');head=add(root,'header',revMajor=1,revMinor=7,name=NAME,version='1.0',date='2026-09-08',north=150,south=-220,east=70,west=-280,vendor='Four view environment reconstruction')
add(head,'userData',code='accuracy',value='Video informed visual reconstruction. Uncalibrated cameras; estimated metric scale; no survey or georeference.')
def base(rid,name,length,junction=-1,pr=None,su=None):
 r=add(root,'road',name=name,length=length,id=rid,junction=junction,rule='RHT')
 if pr or su:
  lk=add(r,'link')
  for tag,val in [('predecessor',pr),('successor',su)]:
   if val:
    typ,num,cp=val;kw=dict(elementType=typ,elementId=num)
    if typ=='road':kw['contactPoint']=cp
    add(lk,tag,**kw)
 ty=add(r,'type',s=0,type='town');add(ty,'speed',max=30,unit='km/h')
 return r
def elevation(r):
 add(add(r,'elevationProfile'),'elevation',s=0,a=0,b=0,c=0,d=0);add(r,'lateralProfile')
def lanes(r,n=1,median=0,link=None):
 ls=add(r,'lanes')
 if link:add(ls,'laneOffset',s=0,a=LANE/2,b=0,c=0,d=0)
 sec=add(ls,'laneSection',s=0)
 def lane(parent,i,typ,width=0,mark='none',color='white'):
  la=add(parent,'lane',id=i,type=typ,level='false')
  if link and i:
   ll=add(la,'link');add(ll,'predecessor',id=link[0]);add(ll,'successor',id=link[1])
  if i:add(la,'width',sOffset=0,a=width,b=0,c=0,d=0)
  add(la,'roadMark',sOffset=0,type=mark,weight='standard',color=color,width=.12,laneChange='none' if mark!='broken' else 'both')
 if not link:
  left=add(sec,'left')
  if median:lane(left,1,'median',median)
  for k in range(1,n+1):lane(left,k+(1 if median else 0),'driving',LANE,'solid' if k==n else 'broken')
 lane(add(sec,'center'),0,'none',mark='none' if median or link else 'solid',color='yellow')
 right=add(sec,'right')
 if median:lane(right,-1,'median',median)
 for k in range(1,n+1):lane(right,-k-(1 if median else 0),'driving',LANE,'none' if link else ('solid' if k==n else 'broken'))
for rid,r in ROADS.items():
 road=base(rid,r['name'],r['length'],pr=('junction',r['pred'],None) if 'pred' in r else None,su=('junction',r['succ'],None) if 'succ' in r else None)
 pv=add(road,'planView');add(add(pv,'geometry',s=0,x=r['x'],y=r['y'],hdg=r['h'],length=r['length']),'line');elevation(road);lanes(road,r['n'],r['median'])
 if rid==30:
  center=road.find('lanes/laneSection/center/lane');center.find('roadMark').set('type','broken');add(center,'roadMark',sOffset=130,type='solid',weight='standard',color='yellow',width=.12,laneChange='none')
 add(road,'userData',code='evidence',value='Four video views; dimensions and lane organization estimated. Untraveled continuation is abbreviated context.' if rid in [11,31] else 'Four video views; dimensions estimated.')
conns=maneuvers();paths=[]
for c in conns:
 p=c['a']['p'];pts=[];L=sum(g['length'] for g in c['segments']);a=c['a'];b=c['b']
 r=base(c['id'],str(a['rid'])+'_to_'+str(b['rid']),L,c['junction'],('road',a['rid'],a['cp']),('road',b['rid'],b['cp']))
 pv=add(r,'planView');ss=0
 for seg in c['segments']:
  x=seg['x'];y=seg['y'];h=seg['h'];k=seg['k'];ll=seg['length'];g=add(pv,'geometry',s=ss,x=x,y=y,hdg=h,length=ll)
  add(g,'arc',curvature=k) if k else add(g,'line')
  for i in range(101):
   u=ll*i/100
   pts.append((x+(math.sin(h+k*u)-math.sin(h))/k,y-(math.cos(h+k*u)-math.cos(h))/k) if k else (x+u*math.cos(h),y+u*math.sin(h)))
  ss+=ll
 elevation(r);lanes(r,link=(a['lane'],b['lane']))
 paths.append(dict(id=c['id'],junction=c['junction'],from_road=a['rid'],to_road=b['rid'],start_lane=a['lane'],end_lane=b['lane'],length=L,segments=c['segments'],points=pts))
for jid,j in JUNCTIONS.items():
 ju=add(root,'junction',name=j['name'],id=jid,type='default')
 for i,c in enumerate(x for x in conns if x['junction']==jid):
  co=add(ju,'connection',id=i,incomingRoad=c['a']['rid'],connectingRoad=c['id'],contactPoint='start');add(co,'laneLink',**{'from':c['a']['lane'],'to':-1})
 add(ju,'userData',code='traffic_rules',value='Editable simulation topology inferred from visible layout; no U-turns, no signal timing reconstruction.')
E.ElementTree(root).write(OUT/(NAME+'.xodr'),encoding='utf-8',xml_declaration=True)
(OUT/'validation/junction_paths.json').write_text(json.dumps(paths,indent=2))
(OUT/'road_parameters.json').write_text(json.dumps(dict(roads=ROADS,lane_width_m=LANE,local_origin='second right-turn T junction',axes='RH metres; X approach direction; Y left; Z up; CARLA (X,-Y,Z)',guideway_y_m=[-7.2,-10.2],guideway_deck_top_m=10.8,hoarding_height_m=3.2,estimated=True,georeference=None),indent=2))
(OUT/(NAME+'Package.json')).write_text(json.dumps(dict(maps=[dict(name=NAME,source='./'+NAME+'.fbx',xodr='./'+NAME+'.xodr',use_carla_materials=False)],props=[]),indent=2))
print('Created',len(ROADS),'ordinary roads,',len(conns),'connectors,',len(JUNCTIONS),'junctions')
