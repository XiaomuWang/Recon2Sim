"""Four-view parameterized environment reconstruction for CARLA, Blender 4.2."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scene_lib import *
from road_layout import ROADS,LANE,pose
from mathutils.geometry import tessellate_polygon
material('BridgeConcrete',(.61,.63,.61),.9)
material('CycleAsphalt',(.22,.245,.24),.95)
material('BlueCladding',(.24,.36,.48),.65,.1)
material('LightCladding',(.72,.73,.71),.74)
material('Coping',(.53,.55,.53),.85)
material('Tactile',(.68,.60,.36),.9)
material('PaintBlue',(.04,.23,.43),.65)
material('PaverDark',(.20,.24,.25),.9)
material('BusRoof',(.20,.25,.26),.48,.35)
material('SignWhite',(.90,.91,.85),.8)
material('SignalDark',(.018,.022,.024),.5)
def path(m,pts,width,mat,z=.012):
 for a,b in zip(pts,pts[1:]):
  dx=b[0]-a[0];dy=b[1]-a[1];d=math.hypot(dx,dy)
  if d<1e-7:continue
  nx=-dy/d*width/2;ny=dx/d*width/2
  m.face([(a[0]-nx,a[1]-ny,z),(b[0]-nx,b[1]-ny,z),(b[0]+nx,b[1]+ny,z),(a[0]+nx,a[1]+ny,z)],mat)
def polygon(m,pts,mat,z=0):
 vv=[Vector((p[0],p[1],z)) for p in pts]
 for tri in tessellate_polygon([vv]):
  tri=[vv[v] if isinstance(v,int) else v for v in tri]
  if (tri[1]-tri[0]).cross(tri[2]-tri[0]).z<0:tri=list(reversed(tri))
  m.face(tri,mat)
def rect(m,x1,y1,x2,y2,mat,z=0):m.face([(x1,y1,z),(x2,y1,z),(x2,y2,z),(x1,y2,z)],mat)
def arc(cx,cy,r,a,b,n=32):return [(cx+r*math.cos(a+(b-a)*i/n),cy+r*math.sin(a+(b-a)*i/n)) for i in range(n+1)]
def localpt(x,y,origin,h):return (origin[0]+x*math.cos(h)-y*math.sin(h),origin[1]+x*math.sin(h)+y*math.cos(h))
def curbwalk(points,outward=1,width=3.0,name='Curb'):
 m=Mesh(name,'Sidewalk');tact=Mesh(name+'_Tactile','Sidewalk')
 for i,(a,b) in enumerate(zip(points,points[1:])):
  dx=b[0]-a[0];dy=b[1]-a[1];le=math.hypot(dx,dy)
  if le<.001:continue
  nx=dy/le*outward;ny=-dx/le*outward;h=math.atan2(dy,dx)
  for j in range(max(1,math.ceil(le/.85))):
   n=max(1,math.ceil(le/.85));u=(j+.5)/n
   m.box((a[0]+dx*u+nx*.13,a[1]+dy*u+ny*.13,.09),(le/n-.012,.26,.18),'Coping',h)
  polygon(m,[(a[0]+nx*.26,a[1]+ny*.26),(b[0]+nx*.26,b[1]+ny*.26),(b[0]+nx*width,b[1]+ny*width),(a[0]+nx*width,a[1]+ny*width)],'Paving',.17)
  for j in range(int(le/.5)):
   u=j*.5/le;aa=(a[0]+dx*u,a[1]+dy*u)
   path(m,[(aa[0]+nx*.27,aa[1]+ny*.27),(aa[0]+nx*width,aa[1]+ny*width)],.012,'Joint',.173)
  if width>=2:
   for offset in [1.1,1.4]:path(tact,[(a[0]+nx*offset,a[1]+ny*offset),(b[0]+nx*offset,b[1]+ny*offset)],.07,'Tactile',.176)
 m.done();tact.done()
print('Road mesh from shared reference geometry',flush=True)
mark=Mesh('Lane_Paint','RoadLines')
for rid,r in ROADS.items():
 hw=r['n']*LANE+r['median'];m=Mesh('Segment_'+str(rid),'Road')
 for s in range(0,int(r['length']),20):
  a=pose(rid,s,-hw);b=pose(rid,min(s+20,r['length']),hw)
  polygon(m,[pose(rid,s,-hw),pose(rid,min(s+20,r['length']),-hw),pose(rid,min(s+20,r['length']),hw),pose(rid,s,hw)],'Asphalt')
 m.done()
 for t in [-hw+.12,hw-.12]:path(mark,[pose(rid,0,t),pose(rid,r['length'],t)],.10,'PaintYellow' if rid in [20,30,31] else 'PaintWhite')
 if r['median']:
  for sgn in [-1,1]:
   for k in [1,2]:
    t=sgn*(r['median']+k*LANE)
    for s in range(2,int(r['length'])-4,9):path(mark,[pose(rid,s,t),pose(rid,s+4,t)],.12,'PaintWhite')
  med=Mesh('Median_'+str(rid),'Terrain');p=pose(rid,r['length']/2)
  med.box((p[0],p[1],.12),(r['length'],2*r['median'],.24),'Grass',r['h']);med.done()
  for sign in [-1,1]:curbwalk([pose(rid,0,sign*r['median']),pose(rid,r['length'],sign*r['median'])],outward=sign,width=.26,name='MedianEdge')
 else:
  if rid==30:
   for s in range(0,130,9):path(mark,[pose(rid,s),pose(rid,min(s+4,130))],.12,'PaintYellow')
   path(mark,[pose(rid,130),pose(rid,r['length'])],.12,'PaintYellow')
  else:path(mark,[pose(rid,0),pose(rid,r['length'])],.12,'PaintYellow')
 # Ordinary sidewalk: a segregated bike strip lies on the south side of the guideway street.
 for sign in [-1,1]:
  pts=[pose(rid,0,sign*hw),pose(rid,r['length'],sign*hw)]
  curbwalk(pts,outward=-sign,width=3.6 if rid in [10,11] else (4.4 if rid in [30,31] else 3.1),name='Sidewalk_%s_%s'%(rid,sign))
 if rid==20:
  cycle=Mesh('Segregated_Cycleway','Sidewalk');rect(cycle,-160,-6.7,-20,-3.85,'CycleAsphalt',.185);cycle.done()
  path(mark,[(-160,-6.35),(-20,-6.35)],.10,'PaintWhite',.19)
# Junction surfaces are T outlines with real curb fillets, not painted square pads.
for jid,cx,hw,mirror in [(1,-180,11.7,-1),(2,0,3.5,1)]:
 r=4.5 if jid==1 else 7.;b=3.5
 lower=[(-20,-b),(-hw-r,-b)]+arc(-hw-r,-b-r,r,math.pi/2,0)+[(-hw,-20)]
 upper=[(-hw,20),(-hw,b+r)]+arc(-hw-r,b+r,r,0,-math.pi/2)+[(-20,b)]
 pts=lower+[(hw,-20),(hw,20)]+upper
 trans=lambda seq:[(cx+mirror*x,y) if jid==1 else (-y,x) for x,y in seq]
 m=Mesh('T_Junction_'+str(jid),'Road');polygon(m,trans(pts),'Asphalt');m.done()
 for seq in [lower,[(hw,-20),(hw,20)],upper]:curbwalk(trans(seq),outward=mirror,width=3.1,name='Junction_%s_Fillet'%jid)
 for seq in [lower,upper]:path(mark,trans(seq),.10,'PaintYellow')
# Zebra crossings on all observed right-turn mouths; stop lines end at lane edge.
def zebra(cx,cy,w,h=0,depth=3.6):
 for u in range(int(w/.9)):
  xx=-w/2+.15+u*.9
  pts=[localpt(xx, -depth/2,(cx,cy),h),localpt(xx+.45,-depth/2,(cx,cy),h),localpt(xx+.45,depth/2,(cx,cy),h),localpt(xx,depth/2,(cx,cy),h)]
  polygon(mark,pts,'PaintWhite',.018)
zebra(-156,0,7,math.pi/2);zebra(-15.7,0,7,math.pi/2);zebra(0,-15.2,7);zebra(15.7,0,7,math.pi/2)
path(mark,[(-19.2,-3.3),(-19.2,-.2)],.35,'PaintWhite');path(mark,[(.2,-18.3),(3.3,-18.3)],.35,'PaintWhite')
def arrow(cx,cy,h=0,kind='straight',size=1):
 # Local forward +X. Connected, correctly oriented lane symbols.
 def p(x,y):return localpt(x*size,y*size*.62,(cx,cy),h)
 path(mark,[p(-1.5,0),p(.65,0)],.21*size,'PaintWhite',.02)
 if kind in ['straight','both']:polygon(mark,[p(1.7,0),p(.55,-.48),p(.55,.48)],'PaintWhite',.022)
 if kind in ['right','both','leftright']:
  path(mark,[p(-.4,0),p(.25,-.63),p(.25,-1.05)],.23*size,'PaintWhite',.022);polygon(mark,[p(.25,-1.7),p(-.22,-.92),p(.72,-.92)],'PaintWhite',.022)
 if kind=='leftright':
  path(mark,[p(-.4,0),p(.25,.63),p(.25,1.05)],.23*size,'PaintWhite',.022);polygon(mark,[p(.25,1.7),p(-.22,.92),p(.72,.92)],'PaintWhite',.022)
for x in [-118,-75,-30]:arrow(x,-1.75,0,'both' if x==-30 else 'straight')
for y in [-30,-78,-140]:arrow(1.75,y,math.pi/2,'leftright' if y==-30 else 'straight');arrow(-1.75,y,-math.pi/2)
for x in [-132,-62]:
 for sign in [-1,1]:path(mark,[(x-1.3,sign*1.75),(x,sign*1.75-.55),(x+1.3,sign*1.75),(x,sign*1.75+.55),(x-1.3,sign*1.75)],.10,'PaintWhite')
for y in [-58,-120,-178]:path(mark,[(-1.75,y-1.2),(-2.3,y),(-1.75,y+1.2),(-1.2,y),(-1.75,y-1.2)],.1,'PaintWhite')
# Bus-bay and yellow keep-clear grid seen in front / left before the first turn.
for y in range(-190,-123,6):path(mark,[(-169.0,y),(-169.0,y+3)],.16,'PaintYellow')
for y in [-190,-123]:path(mark,[(-169.0,y),(-168.45,y)],.16,'PaintYellow')
rect(mark,-170.95,-27,-168.45,-9,'PaintYellow',.005)
# Overlay asphalt inset produces the thin perimeter; diagonal lines remain actual geometry.
rect(mark,-170.8,-26.85,-168.6,-9.15,'Asphalt',.009)
for y in range(-26,-9,3):
 path(mark,[(-170.8,y),(-168.6,min(y+2.2,-9.15))],.10,'PaintYellow',.025)
 path(mark,[(-168.6,y),(-170.8,min(y+2.2,-9.15))],.10,'PaintYellow',.025)
mark.done()
# Drainage grates and repaired asphalt seams, below wheel surface tolerance.
gr=Mesh('Drainage_Manholes','Props');repair=Mesh('Asphalt_Repairs','RoadLines')
for x in range(-151,-22,15):
 gr.box((x,-3.21,.012),(.85,.34,.02),'DarkSteel')
 for j in range(9):gr.box((x-.37+j*.09,-3.21,.027),(.025,.32,.018),'Galvanized')
for y in range(-188,-20,18):
 for x in [-3.23,3.23]:
  gr.box((x,y,.009),(.32,.8,.018),'DarkSteel')
  for j in range(8):gr.box((x,y-.34+j*.095,.025),(.29,.026,.016),'Galvanized')
for x,y in [(-40,-1),(-100,1.4),(1,-45),(-1.3,-111),(-171,-65)]:
 gr.cyl((x,y,.001),(x,y,.008),.34,.34,'DarkSteel',32)
 for d in [-.18,-.09,0,.09,.18]:path(gr,[(x-.23,y+d),(x+.23,y+d)],.012,'Galvanized',.012)
for i in range(45):
 x=random.uniform(-154,-24);y=random.uniform(-3,3);w=random.uniform(.2,1.2);polygon(repair,[(x,y),(x+w,y+.05),(x+w+.1,y+.25),(x-.1,y+.19)],'Patch',.004)
gr.done();repair.done()

print('Elevated double guideway and arch bridge',flush=True)
rail=Mesh('Elevated_DualBeam','Building');support=Mesh('Guideway_Piers','Building');steel=Mesh('Bridge_ArchAndHangers','Building')
for x in range(-225,58,28):
 for y in [-7.2,-10.2]:
  rail.box((x+13.95,y,10.05),(27.9,1.25,1.5),'BridgeConcrete')
  rail.box((x+13.95,y,10.86),(27.9,1.05,.12),'Coping')
  for dy in [-.49,.49]:rail.box((x+13.95,y+dy,10.99),(27.9,.075,.15),'Galvanized')
  for xx in [x,x+27.9]:rail.box((xx,y,10.83),(.08,1.2,.06),'DarkSteel')
for x in [-218,-148,-120,-92,-64,-36,-10,20,48]:
 # Tapered capitals and Y braces are prominent in the side cameras.
 support.box((x,-8.7,.15),(2.6,2.8,.3),'Concrete')
 support.box((x,-8.7,4.5),(1.6,1.7,8.8),'BridgeConcrete')
 for yy in [-7.2,-10.2]:
  support.cyl((x,-8.7,7.7),(x,yy,9.6),.78,.63,'BridgeConcrete',4)
  support.box((x,yy,9.32),(2.15,1.5,.38),'Coping');support.box((x,yy,9.54),(.9,.8,.14),'DarkSteel')
 support.box((x,-8.7,1.2),(1.62,1.72,.46),'CurbYellow')
 for k in [-.55,0,.55]:support.box((x+k,-9.566,1.2),(.10,.015,.44),'BridgeConcrete')
# Two pale steel arches spanning the boulevard, suspended deck, no column in traffic lanes.
for yy in [-6.5,-10.9]:
 points=[]
 for k in range(81):
  u=k/80;points.append((-219+72*u,yy,10.6+10.8*4*u*(1-u)))
 for a,b in zip(points,points[1:]):steel.cyl(a,b,.36,.36,'LightCladding',8)
 for k in range(6,76,6):
  p=points[k];steel.cyl((p[0],yy,10.8),p,.035,.035,'Galvanized',6)
for x in [-212,-203,-194,-185,-176,-167,-158]:
 u=(x+219)/72;z=10.6+10.8*4*u*(1-u);steel.cyl((x,-6.5,z),(x,-10.9,z),.14,.14,'LightCladding',8)
rail.done();support.done();steel.done()

print('Architecture and observed boundary walls',flush=True)
def building(name,x,y,w,d,h,style='striped'):
 m=Mesh(name,'Building');m.box((x,y,h/2),(w,d,h),'LightCladding' if style=='striped' else 'DarkSteel')
 floor=3.7;nf=int(h/floor)
 for j in range(1,nf):
  z=j*floor
  for side in [-1,1]:
   mat='BlueCladding' if style=='striped' else 'GlassDark'
   m.box((x,y+side*(d/2+.04),z),(w-.3,.10,1.25 if style=='striped' else 2.8),mat)
   m.box((x+side*(w/2+.04),y,z),(.10,d-.3,1.25 if style=='striped' else 2.8),mat)
   for xx in range(int(-w/2+2),int(w/2-1),3):
    m.box((x+xx,y+side*(d/2+.11),z+1.2),(1.6,.08,1.35),'GlassBlue')
    m.box((x+xx,y+side*(d/2+.17),z+1.2),(.06,.09,1.4),'WhiteMetal')
   for yy in range(int(-d/2+2),int(d/2-1),3):m.box((x+side*(w/2+.10),y+yy,z+1.2),(.07,1.6,1.35),'GlassBlue')
 if style!='striped':
  for xx in range(int(-w/2),int(w/2+1),2):
   for side in [-1,1]:m.box((x+xx,y+side*(d/2+.40),h/2),(.20,.85,h),'Coping')
  for yy in range(int(-d/2),int(d/2+1),2):
   for side in [-1,1]:m.box((x+side*(w/2+.4),y+yy,h/2),(.85,.2,h),'Coping')
 for z in [h+.25,.25]:m.box((x,y,z),(w+.8,d+.8,.5),'Coping')
 m.box((x,y,h+1.0),(w*.5,d*.35,1.5),'Concrete')
 for xx in [-w*.28,0,w*.28]:
  m.box((x+xx,y,h+1.2),(2.5,2,1.9),'WhiteMetal')
  for k in range(7):m.box((x+xx,y-1.02,h+.5+k*.19),(2.2,.04,.035),'DarkSteel')
 m.done()
building('BlueWhite_Industrial_Block',-87,30,80,29,32)
building('Industrial_Wing',-132,26,26,26,23)
building('Dark_Fin_Office_AcrossBoulevard',-226,-11,42,42,42,'fins')
building('Boulevard_BackgroundOffice',-230,-117,31,40,26,'fins')
building('Distant_East_Office',47,49,48,24,21,'fins')
building('NorthWhite_Wing',-27,53,23,24,26)
for vals in [('Skyline_A',-225,-225,16,20,83),('Skyline_B',-209,-242,19,19,68),('Skyline_C',37,-226,17,22,66)]:building(*vals,style='fins')
wall=Mesh('Grey_CompoundWall','Wall');fence=Mesh('Compound_VerticalRailFence','Fence')
for x in range(-152,70,3):
 wall.box((x+1.48,7.3,1.02),(2.96,.35,2.04),'Concrete');wall.box((x+1.48,7.3,2.12),(3.05,.5,.15),'Coping');wall.box((x,7.3,1.25),(.42,.5,2.5),'Coping')
 fence.box((x+1.5,7.3,3.25),(3,.08,.08),'DarkSteel')
 for k in range(13):fence.box((x+k*.23,7.3,2.73),(.033,.04,1.13),'Galvanized')
wall.done();fence.done()
hut=Mesh('Low_Compound_ServiceBuilding','Building');hut.box((-33,14,2.1),(25,8,4.2),'Concrete');hut.box((-33,14,4.3),(26,9,.25),'DarkSteel')
for x in range(-44,-20,4):
 hut.box((x,9.96,2.1),(2.7,.1,1.5),'GlassDark')
 for k in range(7):hut.box((x-1.25+k*.4,9.84,2.1),(.04,.04,1.5),'WhiteMetal')
hut.done()
def hoarding(name,points):
 m=Mesh(name,'Fence');fr=Mesh(name+'_Frame','Fence')
 for a,b in zip(points,points[1:]):
  dx=b[0]-a[0];dy=b[1]-a[1];le=math.hypot(dx,dy);h=math.atan2(dy,dx);n=math.ceil(le/2.5)
  for i in range(n):
   u=(i+.5)/n;x=a[0]+dx*u;y=a[1]+dy*u
   m.box((x,y,1.65),(le/n,.13,3.2),'GreenHoarding',h)
   fr.box((a[0]+dx*i/n,a[1]+dy*i/n,1.67),(.045,.15,3.25),'Galvanized',h)
  fr.box(((a[0]+b[0])/2,(a[1]+b[1])/2,3.28),(le,.17,.075),'DarkSteel',h)
 m.done();fr.done()
hoarding('InsideCorner_GreenWall',[(-160,-12.2),(-13,-12.2),(-11.5,-14),(-11.5,-22),(-9,-28),(-9,-205)])
hoarding('Opposite_GreenWall',[(8,-205),(8,-28),(10.5,-23),(10.5,-15),(14,-12.2),(75,-12.2)])
hoarding('Boulevard_EastBoundary',[(-159,-200),(-159,-24)])
# Continuous north compound wall established from rear 114-150 sec.

# Legible regulatory symbols from the video; advertising artwork is interpreted, not transcribed.
try:font=bpy.data.fonts.load('C:/Windows/Fonts/msyhbd.ttc')
except:font=None
def lettering(name,body,loc,size,h=0,cat='Props',color='SignWhite'):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.extrude=.0005;cu.align_x='CENTER';cu.align_y='CENTER'
 if font:cu.font=font
 ob=bpy.data.objects.new(NAME+'_'+cat+'_'+name,cu);link(ob,cat);ob.location=loc;ob.rotation_euler=(math.pi/2,0,h);cu.materials.append(M[color])
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH');return ob
def discface(m,center,r,mat,h=0):
 x,y,z=center;pts=[]
 for i in range(48):
  a=i*math.tau/48;u=r*math.cos(a);pts.append((x+u*math.cos(h),y+u*math.sin(h),z+r*math.sin(a)))
 m.face(pts,mat)
def signpost(x,y,h=0,kind='speed'):
 m=Mesh('TrafficSign_'+kind,'Props');m.cyl((x,y,.17),(x,y,3.9),.045,.035,'Galvanized',10)
 norm=(math.sin(h),-math.cos(h))
 def pt(u,v,z):return (x+u*math.cos(h)+v*norm[0],y+u*math.sin(h)+v*norm[1],z)
 if kind=='speed':
  discface(m,pt(0,.07,3.4),.38,'WarningRed',h);discface(m,pt(0,.077,3.4),.305,'SignWhite',h)
  lettering('ObservedSpeed30','30',pt(0,.085,3.4),.40,h,color='DarkSteel')
  discface(m,pt(0,.07,2.47),.34,'WarningRed',h);discface(m,pt(0,.078,2.47),.27,'SignBlue',h)
  for sg in [-1,1]:m.cyl(pt(-.19,.085,2.47-sg*.19),pt(.19,.085,2.47+sg*.19),.025,.025,'WarningRed',8)
 else:
  m.box((x,y,3.2),(.78,.08,.9),'SignBlue',h)
  m.face([pt(-.31,.055,2.91),pt(.31,.055,2.91),pt(0,.055,3.51)],'SignWhite')
  for z in [3.08,3.0]:m.cyl(pt(-.20,.063,z),pt(.20,.063,z),.015,.015,'SignBlue',6)
  m.cyl(pt(.02,.08,3.34),pt(.02,.08,3.37),.037,.037,'DarkSteel',10)
  for a,b in [((.015,3.28),(-.025,3.16)),((-.025,3.16),(-.12,3.08)),((-.025,3.16),(.11,3.07)),((.01,3.25),(-.13,3.19)),((.01,3.25),(.12,3.19))]:m.cyl(pt(a[0],.08,a[1]),pt(b[0],.08,b[1]),.023,.023,'DarkSteel',6)
 m.done()
for x,y,h in [(-23,-7,-math.pi/2),(-6.9,-25,math.pi),(6.9,-17,0),(-145,-7,-math.pi/2)]:signpost(x,y,h,'speed')
for x,y,h in [(-17,6.1,-math.pi/2),(6.2,-22,math.pi),(-6.3,-21,0),(-153,5.5,-math.pi/2)]:signpost(x,y,h,'crossing')

posts=Mesh('Reflective_Bollards','Props')
def bollard(x,y):
 posts.cyl((x,y,.17),(x,y,.85),.085,.075,'Galvanized',12)
 for z in [.50,.64,.77]:posts.cyl((x,y,z),(x,y,z+.055),.088,.083,'CurbYellow',12)
 posts.cyl((x,y,.13),(x,y,.20),.14,.14,'DarkSteel',12)
for x,y in [(-17,-4.2),(-15,-4.2),(-13,-4.3),(-11,-4.7),(-9,-5.5),(-7.3,-7),(-6,-9),(-5.3,-11),(-4.6,-13),(-4.4,-15),(-4.4,-17),(-17,4.2),(-14,4.3),(-11,4.7),(-8,6),(-5,10),(-4.2,14),(-4.2,17)]:bollard(x,y)
for x,y in [(4.4,-18),(4.4,-16),(4.6,-14),(5.1,-11),(6,-9),(7.3,-7),(9,-5.5),(11,-4.7),(14,-4.25),(17,-4.25)]:bollard(x,y)
for x in [-157,-154,-151]:
 for y in [-4.25,4.25]:bollard(x,y)
posts.done()

# Cycle symbols and an offset cycleway trace through the second corner.
plaza=Mesh('Paved_Corner_Aprons','Sidewalk')
corner=[(-20,-3.5),(-10.5,-3.5)]+arc(-10.5,-10.5,7,math.pi/2,0)+[(-3.5,-20),(-10.9,-20),(-10.9,-14),(-13,-11.8),(-20,-11.8)]
polygon(plaza,corner,'CycleAsphalt',.165);polygon(plaza,[(-x,y) for x,y in corner],'CycleAsphalt',.165);plaza.done()
cyclepaint=Mesh('Cycleway_Symbols','RoadLines')
for x in [-144,-94,-46]:
 for xx in [x-.62,x+.62]:path(cyclepaint,arc(xx,-5.18,.40,0,math.tau,28),.045,'PaintWhite',.19)
 path(cyclepaint,[(x-.62,-5.18),(x-.22,-4.60),(x+.4,-5.18),(x-.62,-5.18),(x,-5.18),(x-.22,-4.60)],.045,'PaintWhite',.19)
 path(cyclepaint,[(x+.62,-5.18),(x+.31,-4.37),(x+.10,-4.37)],.045,'PaintWhite',.19)
cyclepaint.done()

# Bus shelter is required by rear/right views at 0-50 sec, with a slim continuous roof.
bus=Mesh('BusStop_ContinuousShelter','Props')
bus.box((-165.0,-156,3.35),(3.7,49,.18),'BusRoof')
bus.box((-165.0,-156,3.47),(3.85,49.3,.10),'Galvanized')
for y in range(-179,-131,6):
 for x in [-166.35,-163.9]:bus.box((x,y,1.77),(.15,.15,3.2),'WhiteMetal')
 bus.box((-164.0,y+2.8,1.85),(.08,5.3,2.5),'GlassBlue')
 bus.box((-165.0,y+2.7,.63),(.48,3.9,.12),'DarkSteel')
 bus.box((-164.75,y+2.7,.93),(.09,3.9,.5),'DarkSteel')
 for yy in [y+1.3,y+4.1]:bus.box((-165.0,yy,.37),(.15,.13,.55),'Galvanized')
 bus.box((-164.09,y+2.8,2.10),(.035,3.6,1.7),'SignWhite')
 bus.box((-164.12,y+2.8,2.49),(.025,3.4,.35),'PaintBlue')
 for yy in [y+1.5,y+2.3,y+3.1,y+3.9]:bus.box((-164.13,yy,1.89),(.02,.49,.65),'Leaf2')
bus.done()
lettering('BusStop_Name','公交站',(-166.95,-137,3.0),.45,-math.pi/2)
for yy in [-181,-130]:
 s=Mesh('BusStop_Timetable','Props');s.box((-164.5,yy,1.62),(.15,1.1,2.9),'PaintBlue');s.box((-164.6,yy,1.66),(.06,.9,2.35),'SignWhite');s.done()

# Replace unreadable hoarding posters with color/layout approximations; never bake cars into textures.
panel=Mesh('Hoarding_DisplayPanels','Fence')
for i,y in enumerate([-182,-151,-112,-76,-44,-15]):
 x=7.89 if y<-28 else 10.39;w=8 if i%3 else 5.6
 panel.box((x,y,1.7),(.06,w,2.15),'SignWhite')
 panel.box((x-.045,y,1.7),(.018,w-.18,1.96),'PaintBlue' if i%3==1 else 'LightCladding')
 # Pale green / blue landscape ribbons, stylized interpretation of visible public notices.
 for k in range(22):
  yy=y-w/2+.18+k*(w-.36)/22;z=.9+.22*math.sin(k*.45+i)
  panel.box((x-.06,yy,z),(.02,(w-.34)/22,.35+random.random()*.22),'Leaf2' if i%2 else 'GlassBlue')
 for j in range(4):panel.box((x-.065,y-w*.1,2.2-j*.12),(.015,w*.54,.026),'WhiteMetal' if i%3==1 else 'PaverDark')
panel.done()

# Lighting poles with slim bent arms, cabinet boxes, tactile crossing landings.
lamps=Mesh('StreetLights_Cabinets','Props')
for axis,values in [('x',range(-149,70,27)),('y',range(-190,-20,28))]:
 for val in values:
  x,y=(val,5.8) if axis=='x' else (6.2,val);z=7.6
  lamps.cyl((x,y,.17),(x,y,z),.085,.045,'WhiteMetal',10)
  dx,dy=(0,-1.6) if axis=='x' else (-1.6,0)
  lamps.cyl((x,y,z-.3),(x+dx,y+dy,z+.18),.05,.035,'WhiteMetal',8);lamps.box((x+dx,y+dy,z+.14),(.64,.30,.10),'WhiteMetal');lamps.box((x+dx,y+dy,z+.08),(.5,.24,.02),'SignWhite')
for y in range(-189,111,32):
 x=-166.7;lamps.cyl((x,y,.2),(x,y,10),.10,.055,'WhiteMetal',10);lamps.cyl((x,y,9.6),(x-2.5,y,10.25),.06,.04,'WhiteMetal',8);lamps.box((x-2.5,y,10.24),(.75,.35,.13),'WhiteMetal')
for x,y in [(-12,-10.7),(-18,-10.7),(8.1,-21),(-156,-16)]:
 lamps.box((x,y,.7),(.7,.5,1.1),'PaverDark');lamps.box((x,y,.9),(.71,.51,.065),'Galvanized')
 for i in range(5):lamps.box((x,y-.259,.58+i*.08),(.45,.015,.02),'DarkSteel')
lamps.done()

print('Planting, individual leaves and branch structure',flush=True)
from tree_lib import tree,tree_protos
def shrub_strip(a,b,width=1.2):
 m=Mesh('Low_Hedge','Vegetation');dx=b[0]-a[0];dy=b[1]-a[1];le=math.hypot(dx,dy);h=math.atan2(dy,dx);n=max(1,int(le/1.5))
 for i in range(n):
  u=(i+.5)/n;x=a[0]+dx*u;y=a[1]+dy*u
  m.box((x,y,.27),(le/n,width,.74),'Leaf1',h)
  for k in range(48):
   xx,yy=localpt(random.uniform(-le/n/2,le/n/2),random.uniform(-width/2,width/2),(x,y),h)
   m.leaf((xx,yy,random.uniform(.59,.82)),random.uniform(.12,.22),'Leaf'+str(random.randrange(6)))
 m.done()
shrub_strip((-158,-10.9),(-18,-10.9),1.3)
for x in [-8.2,7.4]:shrub_strip((x,-201),(x,-29),.85)
for y1,y2 in [(-199,-21),(21,119)]:shrub_strip((-180,y1),(-180,y2),2.0)
shrub_strip((-164.6,-119),(-164.6,-28),1.2)
shrub_strip((-197,-190),(-197,111),1.4)
for x in range(-146,-17,10):tree(x,5.9,.17,random.uniform(.82,1.02))
for x in [-139,-108,-80,-51,-24]:tree(x,-9.6,.17,random.uniform(.80,1.02))
for side in [-1,1]:
 for y in range(-194,-22,11):
  if side==-1 and -22<y<23:continue
  x=side*(6.1 if side==1 else 6.3)
  o=tree(x,y,.17,random.uniform(.90,1.06));o.scale.x*=.70;o.scale.y*=.72;o.scale.z*=1.16
for x in [-197,-160]:
 for y in range(-192,114,15):
  if -24<y<24:continue
  tree(x,y,.1,random.uniform(.92,1.16))
for y in range(-188,110,23):
 if abs(y)>23:tree(-180,y,.28,.65)
# Tree pits and young-tree braces are visible in both side cameras.
pits=Mesh('TreeBeds_AndBraces','Sidewalk');braces=Mesh('Tree_Supports','Props')
for side in [-1,1]:
 for y in range(-194,-22,11):
  if side==-1 and -22<y<23:continue
  x=side*(6.1 if side==1 else 6.3);pits.box((x,y,.19),(1.55,2.5,.12),'Grass')
  for dx in [-.83,.83]:pits.box((x+dx,y,.22),(.14,2.75,.17),'Coping')
  for dy in [-1.3,1.3]:pits.box((x,y+dy,.22),(1.8,.14,.17),'Coping')
  if y%3==0:
   for ang in [0,2.1,4.2]:
    braces.cyl((x+math.cos(ang)*.8,y+math.sin(ang)*.8,.3),(x+math.cos(ang)*.13,y+math.sin(ang)*.13,1.9),.025,.025,'Bark',6)
pits.done();braces.done()
# Behind hoardings: subdued trees/grass, kept lower detail because the source is occluded.
for i in range(48):
 x=random.uniform(-155,-20);y=random.uniform(-160,-22);tree(x,y,0,random.uniform(.6,.98))
for i in range(30):
 x=random.uniform(14,52);y=random.uniform(-198,57);sc=random.uniform(.65,1.0)
 if y<-18 or y>12:tree(x,y,0,sc)
for x in range(-137,-17,18):tree(x,11,.1,.84)
ground=Mesh('Terrain_Base','Terrain');ground.box((-95,-45,-.38),(410,415,.55),'Earth');ground.done()
gardens=Mesh('Planted_Parcels','Terrain')
for bounds in [(-158,-202,-12,-13),(11,-205,60,80),(-260,-204,-198,128),(-150,9,-14,65),(-166,-200,-158,-20)]:rect(gardens,*bounds,'Grass',-.09)
gardens.done()

print('Export and multi-view rendering',flush=True)
def camera(name,loc,target,lens=25):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);link(o,'Cameras');o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=2500;return o
cams={
 '00_junction_aerial':camera('VIEW_00_Junction_Aerial',(-47,-62,35),(-8,-3,2),34),
 '01_approach_front':camera('VIEW_01_Front_106s',(-36,-1.75,1.75),(-2,-1.4,3),23),
 '02_exit_front':camera('VIEW_02_Front_146s',(-1.75,-25,1.75),(-1.75,-85,2.7),24),
 '03_exit_rear':camera('VIEW_03_Rear_146s',(-1.75,-24,1.75),(-2,8,3),22),
 '04_approach_left':camera('VIEW_04_Left_106s',(-37,-1.75,1.75),(-31,12,4.0),22),
 '05_approach_right':camera('VIEW_05_Right_106s',(-34,-1.75,1.75),(-36,-12,3.0),22),
 '06_boulevard_entry':camera('VIEW_06_FirstTurn_68s',(-169.6,-34,1.8),(-173,8,4.5),22),
 '07_network_overview':camera('VIEW_07_Network_Overview',(-332,-350,237),(-105,-50,0),43),
}
ld=bpy.data.lights.new('Daylight_Sun','SUN');lo=bpy.data.objects.new('Daylight_Sun',ld);link(lo,'Lighting');lo.rotation_euler=Vector((30,60,-100)).to_track_quat('-Z','Y').to_euler();ld.energy=1.7;ld.angle=.22
world=bpy.data.worlds.new('Soft_Daylight');world.use_nodes=True;scene.world=world;ns=world.node_tree.nodes;lk=world.node_tree.links;bg=ns.get('Background');bg.inputs['Strength'].default_value=.40
sky=ns.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_disc=False;sky.sun_elevation=.8;sky.sun_rotation=2.;sky.air_density=1.2;sky.dust_density=2.1;lk.new(sky.outputs['Color'],bg.inputs['Color'])
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.1;scene.render.image_settings.file_format='PNG'
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH' and not o.hide_render:o.select_set(True)
exported=[o for o in scene.objects if o.select_get()]
stats=dict(objects=len(exported),mesh_vertices_instances=sum(len(o.data.vertices) for o in exported),polygons_instances=sum(len(o.data.polygons) for o in exported),materials=len(bpy.data.materials),coordinates='RH metre X approach, Y left, Z up',coverage='Two right-turn T junctions, boulevard/bus shelter, 140m inter-junction segment and 180m green hoarding exit',excluded='vehicles, pedestrians, cameras, lights, hidden source prototypes',accuracy='Four-view visual reconstruction, estimated dimensions; not calibrated photogrammetry')
for o in exported:o['source']='front rear left right video, estimated geometry'
print('EXPORT',stats,flush=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/(NAME+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',global_scale=1.,axis_forward='Y',axis_up='Z',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False)
for o in tree_protos:bpy.data.objects.remove(o,do_unlink=True)
for im in bpy.data.images:
 if im.source=='FILE':im.filepath='//textures/'+Path(im.filepath).name
scene.camera=cams['00_junction_aerial'];bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(NAME+'.blend')))
(ROOT/'validation/mesh_statistics.json').write_text(json.dumps(stats,indent=2))
manifest={}
for name,mat in M.items():
 p=mat.node_tree.nodes.get('Principled BSDF')
 manifest[name]=dict(base_color=list(p.inputs['Base Color'].default_value),roughness=p.inputs['Roughness'].default_value,metallic=p.inputs['Metallic'].default_value,textures=[Path(n.image.filepath).name for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image])
(ROOT/'material_manifest.json').write_text(json.dumps(manifest,indent=2))
for name,cam in cams.items():
 scene.camera=cam;scene.render.filepath=str(ROOT/'renders'/(name+'.png'));print('RENDER',name,flush=True);bpy.ops.render.render(write_still=True)
print('FINISHED',flush=True)
