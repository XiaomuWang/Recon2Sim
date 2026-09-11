import pathlib,json,copy
from lxml import etree as E
from road_layout import *
P=pathlib.Path(__file__).resolve().parents[1]
def add(e,tag,**kw):return E.SubElement(e,tag,{k:str(v) for k,v in kw.items()})
root=E.Element('OpenDRIVE')
h=add(root,'header',revMajor=1,revMinor=7,name=NAME,version='1.0',date='2026-09-08',north=80,south=-90,east=190,west=-170,vendor='Four-view visual reconstruction')
add(h,'userData',code='accuracy',value='Uncalibrated visual reconstruction; estimated metric dimensions; no survey or GNSS reference')
r=add(root,'road',id=10,name='Lane_change_surface_corridor',length=LENGTH,junction=-1,rule='RHT')
t=add(r,'type',s=0,type='town');add(t,'speed',max=40,unit='km/h')
pv=add(r,'planView');add(add(pv,'geometry',s=0,x=XMIN,y=0,hdg=0,length=LENGTH),'line')
add(add(r,'elevationProfile'),'elevation',s=0,a=0,b=0,c=0,d=0)
add(r,'lateralProfile')
ls=add(r,'lanes');sec=add(ls,'laneSection',s=0)
def lane(parent,i,w,typ,mark='none',color='white'):
 la=add(parent,'lane',id=i,type=typ,level='false')
 if i:add(la,'width',sOffset=0,a=w,b=0,c=0,d=0)
 rm=add(la,'roadMark',sOffset=0,type=mark,weight='standard',color=color,width=.12,laneChange='both' if mark=='broken' else 'none')
 if mark=='broken':
  tt=add(rm,'type',name='3m_dash_6m_gap',width=.12)
  add(tt,'line',length=3,space=6,tOffset=0,sOffset=0,rule='none',width=.12)
 return la
for sg,tag in [(1,'left'),(0,'center'),(-1,'right')]:
 side=add(sec,tag)
 if sg==0:lane(side,0,0,'none');continue
 lane(side,sg,MEDIAN_HALF,'border','solid','yellow')
 for n in range(1,4):lane(side,sg*(n+1),LANE,'driving','broken' if n<3 else 'solid')
 lane(side,sg*5,PAVED_HALF-(MEDIAN_HALF+3*LANE),'shoulder')
 # Parking apron and variable sidewalk exist in the visual mesh, not driving lanes.
add(r,'userData',code='traffic_assumptions',value='3 estimated lanes each direction; median border lane +/-1; driving lane IDs +/-2, +/-3, +/-4. 40 km/h provisional. Flat straight local segment. No navigable viaduct, petrol station or distant junction.')
# Split into linked roads so CARLA exposes useful routing topology on the open corridor.
template=copy.deepcopy(r);root.remove(r)
for index,(rid,start,length) in enumerate(SEGMENTS):
 r=copy.deepcopy(template);root.append(r);r.set('id',str(rid));r.set('length',str(length));r.set('name','Corridor_'+str(rid))
 geom=r.find('planView/geometry');geom.set('x',str(start));geom.set('length',str(length))
 lk=E.Element('link');r.insert(0,lk)
 if index:add(lk,'predecessor',elementType='road',elementId=SEGMENTS[index-1][0],contactPoint='end')
 if index<len(SEGMENTS)-1:add(lk,'successor',elementType='road',elementId=SEGMENTS[index+1][0],contactPoint='start')
 for la in r.findall('lanes/laneSection/*/lane'):
  if la.get('id')=='0':continue
  ll=E.Element('link');la.insert(0,ll)
  if index:add(ll,'predecessor',id=la.get('id'))
  if index<len(SEGMENTS)-1:add(ll,'successor',id=la.get('id'))
E.indent(root,space='  ');E.ElementTree(root).write(P/(NAME+'.xodr'),encoding='utf-8',xml_declaration=True)
(P/(NAME+'Package.json')).write_text(json.dumps({'maps':[{'name':NAME,'source':NAME+'.fbx','xodr':NAME+'.xodr','use_carla_materials':False}],'props':[]},indent=2))
(P/'road_parameters.json').write_text(json.dumps({'extent_x_m':[XMIN,XMAX],'length_m':LENGTH,'lane_width_m':LANE,'driving_lanes':[-2,-3,-4,2,3,4],'median_halfwidth_m':MEDIAN_HALF,'lane_center_y_m':{str(sg*(i+1)):lane_y(sg*i) for sg in [-1,1] for i in range(1,4)},'coordinate_system':'RH metres +X ego forward, +Y left, +Z up; CARLA=(X,-Y,Z); UE centimetres=(100X,-100Y,100Z)','landmarks_estimated_m':{'petrol_canopy':[-30,-32,5.7],'parking_apron':[10,68,-16,-10.7],'shopfront_y':-20,'viaduct_center_y':23,'viaduct_deck_z':14,'yield_sign':[88,-11.1,3.4]},'accuracy':'All dimensions inferred visually. Core 0..105 m; end extensions and hidden sides simplified; far junction and elevated deck visual only.'},indent=2))
print('Generated OpenDRIVE 1.7, 275 m, six driving lanes, three linked roads')
