"""Four camera visual reconstruction, not calibrated photogrammetry. Blender 4.2."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scene_lib import *
from architecture import building
for n,c in [('MintTile',(.66,.70,.65)),('WarmTile',(.66,.53,.43)),('CreamTile',(.78,.74,.63)),('RoseTile',(.53,.34,.28)),('Plinth',(.26,.28,.27)),('WindowFrame',(.70,.73,.71)),('LeafTrunkWhite',(.73,.73,.65)),('Tactile',(.71,.60,.35)),('RoofTile',(.15,.21,.20)),('BridgeSteel',(.72,.73,.67)),('BridgeGlass',(.31,.44,.46)),('SignalUnlit',(.02,.027,.025)),('SignalLens',(.08,.19,.13)),('HedgeLight',(.38,.51,.055)),('HedgeDark',(.20,.33,.027)),('Flower',(.72,.18,.055))]:material(n,c,.8 if 'Glass' not in n else .25)
for i in range(12):
 m=material('Sign'+str(i),(1,1,1));t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/'textures'/f'sign_{i:02d}.png'));m.node_tree.links.new(t.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])

def line(m,p,q,w,mat='PaintWhite',z=.012):
 dx=q[0]-p[0];dy=q[1]-p[1];l=math.hypot(dx,dy)
 if l<.0001:return
 nx=-dy/l*w/2;ny=dx/l*w/2
 m.face([(p[0]+nx,p[1]+ny,z),(p[0]-nx,p[1]-ny,z),(q[0]-nx,q[1]-ny,z),(q[0]+nx,q[1]+ny,z)],mat)
def strip(m,r,a,b,t1,t2,z,mat):
 m.face([road_point(r,a,t1,z),road_point(r,b,t1,z),road_point(r,b,t2,z),road_point(r,a,t2,z)],mat)
def rb(m,r,s,t,z,d,mat):m.box(road_point(r,s,t,z),d,mat,r['h'])
def tube(m,p,q,r,mat='Galvanized',n=8):m.cyl(p,q,r,r,mat,n)
def fence(m,r,a,b,t,height=.98,color='WhiteMetal'):
 for s in [a+i*2.5 for i in range(int((b-a)/2.5)+1)]:
  tube(m,road_point(r,s,t,.18),road_point(r,s,t,height+.18),.035,color)
 for z in [.32,height+.18]:tube(m,road_point(r,a,t,z),road_point(r,b,t,z),.025,color)
 for i in range(int((b-a)/.20)):
  s=a+i*.20;tube(m,road_point(r,s,t,.32),road_point(r,s,t,height+.16),.010,color,5)

print('Build shared road geometry',flush=True)
side=Mesh('Curbs_Tactile_Paving','Sidewalk');lines=Mesh('Lane_Markings','RoadLines');rail=Mesh('Pedestrian_And_Median_Rails','Fence');drain=Mesh('Drainage_And_Repair','Props')
for r in ROADS:
 half=r['median']+r['n']*r['w'];L=r['length']
 for a in range(0,int(math.ceil(L)),25):
  b=min(a+25,L);m=Mesh('Road_%d_%d'%(r['id'],a),'Road');strip(m,r,a,b,-half-2,half+2,0,'Asphalt');m.done()
 # Curbs, detailed paving and linear lawn strips outside the bicycle lane.
 for a in range(int(L)):
  for sg in [-1,1]:
   rb(side,r,a+.5,sg*(half+2.12),.1,(1,.24,.20),'Concrete')
   rb(side,r,a+.5,sg*(half+2.9),.16,(1,1.35,.15),'Grass')
   rb(side,r,a+.5,sg*(half+6.1),.095,(1,5.0,.19),'Paving')
   rb(side,r,a+.5,sg*(half+4),.205,(1,.38,.018),'Tactile')
   for offset in [-.11,0,.11]:rb(side,r,a+.5,sg*(half+4)+offset,.22,(1,.022,.018),'Tactile')
   rb(side,r,a,sg*(half+6.1),.192,(.012,5.,.005),'Joint')
  # Raised center bed, with distinct pale curb and chartreuse hedges.
  rb(side,r,a+.5,0,.13,(1,r['median']*2,.26),'Concrete')
  rb(side,r,a+.5,0,.27,(1,r['median']*2-.30,.06),'Earth')
  for sg in [-1,1]:rb(side,r,a+.5,sg*(r['median']-.08),.22,(1,.16,.18),'Concrete')
 for sg in [-1,1]:
  for t in [r['median']+.1,half-.02]:strip(lines,r,0,L,sg*t-.055,sg*t+.055,.014,'PaintYellow')
  for a in range(2,int(L-4),9):strip(lines,r,a,a+3.5,sg*(r['median']+r['w'])-.055,sg*(r['median']+r['w'])+.055,.015,'PaintWhite')
  for a in range(14,int(L-10),44):
   for ln in [1,2]:
    t=sg*(r['median']+(ln-.5)*r['w']);dd=-sg
    line(lines,road_point(r,a-dd*1.6,t),road_point(r,a+dd*1.2,t),.18)
    lines.face([road_point(r,a+dd*2.5,t,.017),road_point(r,a+dd*.8,t-.6,.017),road_point(r,a+dd*.8,t+.6,.017)],'PaintWhite')
  # bollards line the observed outer cycle strip on the incident boulevard.
  if r['id']==20:
   for a in range(4,int(L),8):
    x,y,z=road_point(r,a,sg*(half+.3),0);drain.cyl((x,y,.01),(x,y,.9),.068,.045,'DarkSteel',8);drain.cyl((x,y,.58),(x,y,.72),.058,.052,'PaintYellow',8)
  # Drain covers and kerb inlets.
  for a in range(8,int(L),21):
   rb(drain,r,a,sg*(half+1.77),.015,(.6,.4,.025),'DarkSteel')
   for k in range(8):rb(drain,r,a-.25+k*.07,sg*(half+1.77),.031,(.028,.36,.022),'Galvanized')
  fence(rail,r,0,L,sg*(half+3.6),.84,'DarkSteel')
 if r['id']==30:
  # Narrow, shaded approach seen at 0-40 s: railing and repeated yellow rumble bars.
  fence(rail,r,0,170,-r['median'],1.02)
  for a in [8,42,83,125,160]:
   for k in range(4):strip(lines,r,a+k*1.3,a+k*1.3+.34,-half,-r['median'],.016,'PaintYellow')
  for a in [60,145]:
   for t in [(-half)+k*.85 for k in range(8)]:strip(lines,r,a,a+3.5,t,t+.40,.018,'PaintWhite')
 # central railing is seen beyond the low median plants at incident.
 if r['id']==20:fence(rail,r,0,L,.25,.75,'DarkSteel')
side.done();lines.done();rail.done();drain.done()

# Intersection paved region, with actual lane swept ribbons used by the parser.
paths=json.loads((ROOT/'validation/junction_paths.json').read_text())
jroad=Mesh('Junction_Paved_Apron','Road')
# Curved pavement boundary follows the four approach widths, instead of a square apron.
def corner_xy(c,t,off=0):
 rx=20.4-off;ry=22.2-off
 return [(32-rx*math.sin(t),32-ry*math.cos(t)),(-32+rx*math.cos(t),32-ry*math.sin(t)),(-32+rx*math.sin(t),-32+ry*math.cos(t)),(32-rx*math.cos(t),-32+ry*math.sin(t))][c]
outline=[]
for c in range(4):
 for k in range(25):
  x,y=corner_xy(c,k*math.pi/48);outline.append((JX+x,y,0))
jroad.face(outline,'Asphalt')
corners=Mesh('Curved_Corner_Sidewalks','Sidewalk');edge=Mesh('Curved_Junction_Edges','RoadLines')
for c in range(4):
 for k in range(48):
  ta=k*math.pi/96;tb=(k+1)*math.pi/96
  for a,b,z,mat in [(0,.22,.16,'Concrete'),(.22,1.6,.18,'Grass'),(1.6,6.6,.18,'Paving')]:
   pts=[corner_xy(c,ta,a),corner_xy(c,tb,a),corner_xy(c,tb,b),corner_xy(c,ta,b)]
   corners.face([(JX+x,y,z) for x,y in pts],mat)
  p=corner_xy(c,ta,-.11);q=corner_xy(c,tb,-.11);line(edge,(JX+p[0],p[1]),(JX+q[0],q[1]),.12,'PaintYellow')
corners.done();edge.done()
for path in paths:
 pp=path['points']
 for i,(p,q) in enumerate(zip(pp,pp[1:])):
  dx=q[0]-p[0];dy=q[1]-p[1];le=math.hypot(dx,dy);nx=-dy/le*1.8;ny=dx/le*1.8
  jroad.face([(p[0]+nx,p[1]+ny,0),(p[0]-nx,p[1]-ny,0),(q[0]-nx,q[1]-ny,0),(q[0]+nx,q[1]+ny,0)],'Asphalt')
jroad.done()
cross=Mesh('Crosswalks_And_Channelization','RoadLines')
for r in ROADS:
 a=5 if r['junction_end']=='start' else r['length']-8;half=r['median']+6.6
 for sg in [-1,1]:
  for k in range(8):
   t=sg*(r['median']+.2+k*.8);strip(cross,r,a,a+3.5,t-.22,t+.22,.018,'PaintWhite')
cross.done()
# Triangular landscaped islands outside all drivable swept paths.
island=Mesh('Corner_Triangle_And_Bollards','Sidewalk')
def safe_island(x,y,radius):
 return all(math.hypot(x-p[0],y-p[1])>radius+2.1 for path in paths for p in path['points'])
for x,y,rad in [(JX+22,-23,3.0),(JX-22,23,3.0)]:
 if safe_island(x,y,rad):
  island.cyl((x,y,0),(x,y,.28),rad,rad,'Concrete',3);island.cyl((x,y,.28),(x,y,.65),rad-.30,rad-.40,'HedgeLight',3)
  for k in range(3):
   a=k*math.tau/3;tube(island,(x+(rad+.4)*math.cos(a),y+(rad+.4)*math.sin(a),.05),(x+(rad+.4)*math.cos(a),y+(rad+.4)*math.sin(a),.9),.065,'PaintYellow')
island.done()

print('Observed architecture and covered pedestrian bridge',flush=True)
# Incident corridor buildings: pale six-storey blocks, close shopfronts, taller towers behind.
for vals in [(-235,-1,32,21,61,0,19),(-192,-1,42,22,84,1,19),(-145,-1,37,20,31,0,19),(-98,-1,35,20,25,1,19),(-54,-1,34,19,25,0,19),(-10,-1,36,19,23,0,19),(31,-1,35,20,24,0,19),(90,-1,37,20,24,1,19),(137,-1,42,20,25,0,19),(181,-1,36,20,23,1,19),(-230,1,37,22,28,0,21),(-185,1,36,23,37,1,23),(-133,1,37,21,29,1,20),(-87,1,39,20,27,0,19),(-39,1,36,21,24,0,19),(10,1,39,20,22,0,19),(88,1,38,19,25,1,19),(137,1,35,21,25,0,19),(180,1,35,20,26,1,19)]:
 x,sg,w,d,h,sty,front=vals;building(x,sg,w,d,h,sty,yfront=front)
# Pitched dark roof accents on the incident's pale residential blocks.
roof=Mesh('Residential_Roof_Profiles','Building')
for x,y,w,d,h in [(31,-29,35,20,24),(10,29.5,39,21,22),(90,-29,37,20,24),(-10,-28.5,36,19,23)]:
 roof.face([(x-w/2,y-d/2,h+.7),(x+w/2,y-d/2,h+.7),(x+w/2,y,h+3),(x-w/2,y,h+3)],'RoofTile')
 roof.face([(x-w/2,y,h+3),(x+w/2,y,h+3),(x+w/2,y+d/2,h+.7),(x-w/2,y+d/2,h+.7)],'RoofTile')
 for sg in [-1,1]:roof.face([(x+sg*w/2,y-d/2,h+.7),(x+sg*w/2,y+d/2,h+.7),(x+sg*w/2,y,h+3)],'BuildingIvory')
roof.done()
# Wider commercial towers at the right-turn corner and an ochre landmark on the far side.
for v in [(-247,-1,25,26,95,0,42),(-324,1,25,24,102,3,38),(-360,1,30,27,52,1,42),(-154,-1,24,22,79,1,55),(-28,1,25,24,57,1,59),(97,-1,24,23,63,0,53),(143,1,27,25,61,1,53)]:
 x,sg,w,d,h,sty,f=v;building(x,sg,w,d,h,sty,yfront=f)
# Approach facades use the same detailed construction rotated into the northbound street.
for yy,w,h,sty in [(-284,32,28,0),(-244,34,25,1),(-201,37,25,0),(-156,38,26,0),(-112,38,41,1),(-67,37,67,0)]:
 ob=building(yy,-1,w,21,h,sty,yfront=21)
 # local x -> north; local y negative -> east of approach
 ob.rotation_euler.z=math.pi/2;ob.location.x=JX
for yy in [-285,-235,-181,-130,-82]:
 ob=building(yy,1,39,23,random.choice([22,28,38]),1,yfront=25);ob.rotation_euler.z=math.pi/2;ob.location.x=JX

# Distinctive covered footbridge: wavy longitudinal roof profile, slim columns, glass rail panels.
br=Mesh('Covered_Pedestrian_Overbridge','Building');bx=58.;deck=5.7
br.box((bx,0,deck),(4.2,37,.42),'Concrete')
for yy in [-16.7,16.7]:
 for xx in [bx-1.4,bx+1.4]:
  br.cyl((xx,yy,.2),(xx,yy,5.49),.34,.27,'BridgeSteel',12)
for sg in [-1,1]:
 xx=bx+sg*2.0
 for yy in [i*1.8-18 for i in range(21)]:
  roofz=8.55+.55*(abs(yy)/18)**1.5
  tube(br,(xx,yy,deck+.25),(xx,yy,roofz),.072,'BridgeSteel',10)
 for i in range(36):
  ya=-18+i;yb=ya+1;za=8.55+.55*(abs(ya)/18)**1.5;zb=8.55+.55*(abs(yb)/18)**1.5
  br.face([(xx-.16,ya,za),(xx+.16,ya,za),(xx+.16,yb,zb),(xx-.16,yb,zb)],'BridgeSteel')
  for zz in [deck+.56,deck+.76,deck+.96,deck+1.16,deck+1.34]:tube(br,(xx,ya,zz),(xx,yb,zz),.018,'WhiteMetal',6)
 for zz in [deck+.48,deck+1.43]:tube(br,(xx,-18,zz),(xx,18,zz),.041,'WhiteMetal',8)
for i in range(72):
 ya=-18+i*.5;yb=ya+.5;za=8.55+.55*(abs(ya)/18)**1.5;zb=8.55+.55*(abs(yb)/18)**1.5
 br.face([(bx-2.3,ya,za+.09),(bx+2.3,ya,za+.09),(bx+2.3,yb,zb+.09),(bx-2.3,yb,zb+.09)],'BridgeSteel')
 if i%3==0:tube(br,(bx-2.2,ya,za),(bx+2.2,ya,za),.07,'BridgeSteel')
for sg in [-1,1]:
 yy=sg*17.5
 # Approach stairs parallel to the road; remain outside vehicle and bicycle lanes.
 for k in range(33):
  x=bx-15.5+k*.42;z=.2+(deck+.21-.2)*(k+1)/33;br.box((x,yy,z/2),(.43,2.7,z),'Concrete')
 for off in [-1.28,1.28]:
  tube(br,(bx-15.7,yy+off,1.2),(bx-1.6,yy+off,deck+1.2),.045,'WhiteMetal')
  for k in range(0,33,3):
   x=bx-15.5+k*.42;z=.2+(deck+.21-.2)*(k+1)/33;tube(br,(x,yy+off,z),(x,yy+off,z+1.0),.024,'WhiteMetal',6)
br.done()

print('Street furniture and road wear',flush=True)
prop=Mesh('Streetlights_Shelters_Signage','Props')
for r in ROADS:
 half=r['median']+6.6
 for a in range(20,int(r['length']),34):
  x,y,z=road_point(r,a,0,0);prop.cyl((x,y,.2),(x,y,10.7),.13,.065,'Galvanized',12)
  for sg in [-1,1]:
   p=road_point(r,a,sg*3.4,11.1);tube(prop,(x,y,10.5),p,.055,'Galvanized');prop.box(p,(.78,.25,.14),'DarkSteel',r['h'])
 for a in range(16,int(r['length']),55):
  for sg in [-1,1]:
   x,y,z=road_point(r,a,sg*(half+4.2),0);prop.box((x,y,.55),(.55,.45,1.0),'DarkSteel',r['h']);prop.box((x,y,1.10),(.59,.48,.1),'WhiteMetal',r['h'])
 # traffic hardware around junction, unlit static geometry
 s=12 if r['junction_end']=='start' else r['length']-12
 x,y,z=road_point(r,s,-half-2.5,0);q=road_point(r,s,-r['median']-2,6.5)
 tube(prop,(x,y,0),(x,y,6.5),.12);tube(prop,(x,y,6.5),q,.075)
 prop.box(q,(.40,1.12,.45),'DarkSteel',r['h'])
 for k in [-1,0,1]:
  pp=road_point(r,s-.23,-r['median']-2+k*.31,6.5);qq=road_point(r,s-.25,-r['median']-2+k*.31,6.5);prop.cyl(pp,qq,.11,.11,'SignalUnlit',16)
# Bus shelter and streetside canopy adjacent to incident bridge.
for x,sg in [(83,-1),(-155,-1),(-109,1)]:
 yy=sg*14.2
 prop.box((x,yy,3.0),(9,2.1,.18),'DarkSteel')
 for dx in [-3.8,0,3.8]:tube(prop,(x+dx,yy+sg*.7,.2),(x+dx,yy+sg*.7,2.95),.06,'Galvanized')
 prop.box((x,yy+sg*.74,1.65),(7.4,.05,2.05),'BridgeGlass');prop.box((x,yy,.7),(6,.5,.09),'BuildingBeige')
 for dx in [-2,2]:prop.box((x+dx,yy,.44),(.12,.44,.5),'DarkSteel')
# Empty bicycle stands preserve the streetscape without adding vehicles.
for x in range(-237,191,12):
 if 39<x<67:continue
 for k in range(5):
  xx=x+k*.70;y=-15.5;tube(prop,(xx,y,.2),(xx,y,1.0),.025,'DarkSteel');tube(prop,(xx,y,1.0),(xx,y+.55,1.0),.025,'DarkSteel');tube(prop,(xx,y+.55,1.0),(xx,y+.55,.2),.025,'DarkSteel')
prop.done()
wear=Mesh('Asphalt_Seams_And_Patches','Props')
for xx in range(-245,196,19):
 for sg in [-1,1]:
  yy=sg*random.uniform(2.2,7.4);wear.cyl((xx,yy,.002),(xx,yy,.009),.28,.28,'DarkSteel',20)
  for offset in [-.12,0,.12]:line(wear,(xx-.16,yy+offset),(xx+.16,yy+offset),.014,'Galvanized',.012)
for sg in [-1,1]:
 p=(-250,sg*4.,.018)
 for xx in range(-246,200,4):
  q=(xx,sg*4+random.uniform(-.3,.3),.018);line(wear,p,q,random.uniform(.018,.037),'Joint',.018);p=q
wear.done()

print('Detailed foliage',flush=True)
protos=[]
for variant in range(5):
 m=Mesh('TREE_PROTO_%d'%variant,'Vegetation');height=9+variant*.5
 m.cyl((0,0,0),(.13,0,height*.65),.26,.095,'Bark',10);m.cyl((0,0,0),(.02,0,1.28),.27,.24,'LeafTrunkWhite',10)
 for b in range(14):
  ang=b*2.4;rr=random.uniform(1.5,2.6);zz=height*random.uniform(.55,.85);c=(rr*math.cos(ang),rr*math.sin(ang),zz)
  m.cyl((.1,0,zz*.6),c,.075,.018,'Bark',6)
  for j in range(420):
   az=random.random()*math.tau;z=random.uniform(-1,1);rd=random.random()**(1/3);rad=math.sqrt(1-z*z)
   pt=(c[0]+1.45*rd*rad*math.cos(az),c[1]+1.45*rd*rad*math.sin(az),c[2]+1.3*rd*z)
   m.leaf(pt,random.uniform(.14,.24),'Leaf'+str(random.randrange(6)))
 o=m.done();o.hide_render=True;o.hide_viewport=True;protos.append(o)
def tree(x,y,scale=1):
 proto=random.choice(protos);o=bpy.data.objects.new(NAME+'_Vegetation_StreetTree',proto.data);link(o,'Vegetation');o.location=(x,y,.22);o.rotation_euler.z=random.random()*math.tau;o.scale=(scale,)*3
for r in ROADS:
 half=r['median']+6.6
 for a in range(5,int(r['length']),11):
  for sg in [-1,1]:
   x,y,z=road_point(r,a,sg*(half+2.85))
   if r['id']==20 and 39<x<68:continue
   tree(x,y,random.uniform(.8,1.12))
  if r['id'] in [30,40] and a%22<11:
   x,y,z=road_point(r,a,0);tree(x,y,.96)
# Repeated clipped hedge blocks have individual leaves, avoiding plain green boxes.
hedges=[]
for j in range(3):
 m=Mesh('HEDGE_PROTO_%d'%j,'Vegetation');m.box((0,0,.46),(3.96,.65,.32),'HedgeDark')
 for k in range(4300):
  x=random.uniform(-2,2);y=random.uniform(-.48,.48);z=random.uniform(.25,.76)
  if k%3==0:z=random.uniform(.73,.82)
  elif k%3==1:y=random.choice([-1,1])*random.uniform(.39,.48)
  m.leaf((x,y,z),random.uniform(.035,.065),'HedgeLight' if random.random()<.64 else 'HedgeDark')
 o=m.done();o.hide_render=True;o.hide_viewport=True;hedges.append(o)
for r in ROADS:
 for a in range(2,int(r['length']-1),4):
  for t in [-r['median']*.52,r['median']*.52]:
   p=random.choice(hedges);o=bpy.data.objects.new(NAME+'_Vegetation_MedianHedge',p.data);link(o,'Vegetation');o.location=road_point(r,a,t,.15);o.rotation_euler.z=r['h']
terra=Mesh('Ground_Base','Terrain');terra.box((-90,-88,-.46),(655,550,.70),'Earth');terra.done()

print('Export and render',flush=True)
def camera(n,loc,target,lens=25):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);link(o,'Cameras');o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=1800;return o
cams={
 '00_aerial':camera('Aerial_Incident',(-29,-27,74),(45,0,0),37),
 '01_forward':camera('Forward_Incident',(0,-2.85,1.72),(65,-2.85,2.5),25),
 '02_rear':camera('Rear_Incident',(0,-2.85,1.72),(-90,-2.85,2.9),23),
 '03_left':camera('Left_Incident',(0,-2.85,1.72),(3,25,5.2),21),
 '04_right':camera('Right_Incident',(0,-2.85,1.72),(4,-25,5.4),21),
 '05_approach':camera('Tree_Lined_Approach',(-282.05,-265,1.72),(-282,-195,2.3),24),
 '06_right_turn':camera('Right_Turn',(-281,-33,1.72),(-259,-5,2.3),24),
 '07_junction_aerial':camera('Junction_Aerial',(-300,-61,150),(-290,0,0),35),
 '08_complete_route':camera('Complete_Route',(126,-411,340),(-122,-89,0),45)}
ld=bpy.data.lights.new('Sun','SUN');lo=bpy.data.objects.new('Sun',ld);link(lo,'Lighting');lo.rotation_euler=Vector((26,32,-90)).to_track_quat('-Z','Y').to_euler();ld.energy=2.6;ld.angle=.045
world=bpy.data.worlds.new('Summer_Daylight');world.use_nodes=True;scene.world=world;ns=world.node_tree.nodes;lk=world.node_tree.links;bg=ns.get('Background');bg.inputs['Strength'].default_value=.38
sky=ns.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_disc=False;sky.sun_elevation=1.05;sky.sun_rotation=2.4;sky.air_density=1.0;sky.dust_density=1.2;lk.new(sky.outputs['Color'],bg.inputs['Color'])
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for dev in prefs.devices:dev.use=dev.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception as e:print(e)
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.3;scene.camera=cams['01_forward']
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH' and not o.hide_render:o.select_set(True)
exported=[o for o in scene.objects if o.select_get()]
stats={'objects':len(exported),'vertices_instances':sum(len(o.data.vertices) for o in exported),'polygons_instances':sum(len(o.data.polygons) for o in exported),'materials':len(bpy.data.materials),'coordinate_system':'RH metres +X forward after turn +Y left +Z up; CARLA=(X,-Y,Z)','vehicles_included':False,'method':'manual parameterized visual reconstruction based on four views; no SfM, no calibrated photogrammetry','roads_m':[r['length'] for r in ROADS],'textures':'UV-mapped PBR; embedded FBX textures','runtime_tested':False}
for o in exported:o['source']='four-view visual environment reconstruction';o['survey_accuracy']='estimated'
bpy.ops.export_scene.fbx(filepath=str(ROOT/(NAME+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False)
for o in protos+hedges:bpy.data.objects.remove(o,do_unlink=True)
for im in bpy.data.images:
 if im.source=='FILE':im.filepath='//textures/'+Path(im.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(NAME+'.blend')))
(ROOT/'validation/mesh_statistics.json').write_text(json.dumps(stats,indent=2));print(stats,flush=True)
for name,cam in cams.items():
 scene.camera=cam;scene.render.filepath=str(ROOT/'renders'/(name+'.png'));print('RENDER',name,flush=True);bpy.ops.render.render(write_still=True)
print('FINISHED',flush=True)


