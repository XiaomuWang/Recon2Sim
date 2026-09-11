"""Build the four-view informed, environment-only CARLA source scene."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from asset_lib import *

def graphic(n,f):
 m=material(n,(1,1,1),.65);p=m.node_tree.nodes.get('Principled BSDF');t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/'textures'/f));m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
for i in range(12):graphic('Sign'+str(i),f'sign_{i:02d}.png')
graphic('Yield','yield.png');graphic('MergeNotice','merge_notice.png')
material('RedFascia',(.58,.028,.039),.35,.12)
material('PetrolCream',(.76,.74,.65),.52)
material('PetrolDisplay',(.013,.025,.025),.23)
material('WetPatch',(.031,.035,.036),.44)
material('WetConcrete',(.28,.29,.27),texture='concrete',normal=.25)
material('BridgeConcrete',(.48,.49,.47),texture='concrete',normal=.25)
material('Hedge',(.13,.23,.047),.88)
material('Netting',(.11,.25,.20),.84)
material('ConstructionDark',(.18,.25,.23),.9)
material('CraneIvory',(.56,.58,.53),.55,.3)

def strip(m,a,b,y1,y2,z,mat):ribbon(m,a,b,y1,y2,z,mat,step=2)
def line(m,p,q,w,mat='PaintWhite',z=.003):
 dx=q[0]-p[0];dy=q[1]-p[1];l=math.hypot(dx,dy)
 if l<1e-5:return
 nx=-dy/l*w/2;ny=dx/l*w/2
 m.face([(p[0]+nx,p[1]+ny,z),(p[0]-nx,p[1]-ny,z),(q[0]-nx,q[1]-ny,z),(q[0]+nx,q[1]+ny,z)],mat)
def textplane_x(m,x,y,z,w,h,mat):
 m.face([(x,y+w/2,z-h/2),(x,y-w/2,z-h/2),(x,y-w/2,z+h/2),(x,y+w/2,z+h/2)],mat,[(0,0),(1,0),(1,1),(0,1)])

print('Wet carriageway and angled parking',flush=True)
for x in range(-150,125,25):
 m=Mesh('Asphalt_%d'%x,'Road');strip(m,x,min(x+25,XMAX),-PAVED_HALF,PAVED_HALF,0,'Asphalt');m.done()
m=Mesh('Parking_And_Petrol_Access','Road');strip(m,-77,8,-47,-10.7,0,'WetConcrete');strip(m,8,72,-17.0,-10.7,0,'Asphalt');m.done()
mark=Mesh('Lane_Markings','RoadLines')
for sg in [-1,1]:
 for x in range(-150,125,9):
  for n in [1,2]:
   y=sg*(MEDIAN_HALF+n*LANE);strip(mark,x,min(x+3,125),y-.06,y+.06,.003,'PaintWhite')
 for y in [sg*.25,sg*10.45]:strip(mark,XMIN,XMAX,y-.055,y+.055,.003,'PaintYellow' if abs(y)<1 else 'PaintWhite')
for x in range(9,68,3):
 line(mark,(x,-10.72),(x+4.6,-16.5),.12)
line(mark,(9,-10.72),(68,-10.72),.12);line(mark,(13.6,-16.5),(72.6,-16.5),.12)
for x in range(-74,4,4):line(mark,(x,-12),(x+3.0,-18),.12)
for x in [-115,-70,87,116]:
 for sg in [-1,1]:
  for n in [1,2,3]:
   y=lane_y(sg*n);direction=-sg
   line(mark,(x-direction*2,y),(x+direction*1,y),.17)
   mark.face([(x+direction*2.2,y,.004),(x+direction*.45,y-.48,.004),(x+direction*.45,y+.48,.004)],'PaintWhite')
mark.done()
side=Mesh('Sidewalks_And_Curbs','Sidewalk');seam=Mesh('Paving_Detail','Sidewalk')
for x in range(-150,155):
 for sg in [-1,1]:
  if sg<0 and -78<x<8:continue
  edge=17 if sg<0 and 8<=x<73 else 10.7
  end=20 if sg<0 and 8<=x<73 else edge+4.2
  side.box((x+.5,sg*(edge+.15),.09),(1,.30,.18),'Concrete')
  yy=sorted([sg*(edge+.3),sg*end]);strip(side,x,x+1,*yy,.17,'Paving')
  side.box((x+.5,sg*(edge+1.55),.185),(1,.36,.03),'Tactile')
  for j in range(3):side.box((x+.5,sg*(edge+1.55)+(j-1)*.1,.205),(1,.025,.017),'Tactile')
  for z in range(1,8):seam.box((x+.5,sg*(edge+.4+z*.46),.173),(1,.008,.004),'Joint')
  seam.box((x,sg*(edge+(end-edge)/2),.174),(.008,end-edge,.004),'Joint')
side.done();seam.done()
details=Mesh('Road_Drainage_And_Manholes','Props')
for x in range(-140,120,13):
 for sg in [-1,1]:
  y=sg*10.57
  details.box((x,y,.006),(.88,.26,.012),'DarkSteel')
  for j in range(12):details.box((x-.39+j*.07,y,.015),(.025,.23,.012),'Galvanized')
for x,y in [(4,-9.75),(29,-10.0),(56,-9.65),(91,-6.4),(-54,-5.3),(-101,5.6)]:
 details.cyl((x,y,.001),(x,y,.014),.37,.37,'DarkSteel',32)
 for j in range(-5,6):line(details,(x-.23,y+j*.044),(x+.23,y+j*.044),.015,'Galvanized',.018)
 if x>0 and x<70:
  for dy in [-.6,.6]:line(details,(x-.65,y+dy),(x+.65,y+dy),.07,'PaintYellow')
  for dx in [-.65,.65]:line(details,(x+dx,y-.6),(x+dx,y+.6),.07,'PaintYellow')
details.done()
patches=Mesh('Wet_Surface_Repairs','RoadLines')
for j in range(55):
 x=random.uniform(-145,123);y=random.choice([-10.25,-6.7,-3.3,4.2,8.7])+random.uniform(-.25,.25);rx=random.uniform(.20,1.3);ry=random.uniform(.10,.32)
 patches.face([(x+math.cos(i*math.tau/13)*rx*random.uniform(.8,1.2),y+math.sin(i*math.tau/13)*ry,.001) for i in range(13)],'WetPatch')
for j in range(25):
 x=random.uniform(-140,120);y=random.uniform(-10,10)
 for k in range(8):
  xx=x+random.uniform(.10,.35);yy=y+random.uniform(-.22,.22);line(patches,(x,y),(xx,yy),.015,'Joint',.005);x,y=xx,yy
patches.done()

print('Median railing and left green verge',flush=True)
for a in range(-150,150,30):
 f=Mesh('Median_Railing_%d'%a,'Fence')
 for x in range(a,a+30,3):
  f.box((x,0,.06),(.45,.42,.12),'CurbYellow');f.cyl((x,0,.12),(x,0,1.10),.038,.03,'WhiteMetal',8)
  for z in [.22,1.03]:f.cyl((x,0,z),(x+3,0,z),.025,.025,'WhiteMetal',6)
  for j in range(14):f.cyl((x+.12+j*.21,0,.22),(x+.12+j*.21,0,1.02),.014,.014,'WhiteMetal',5)
 f.done()
g=Mesh('Planted_Left_Embankment','Terrain');g.box((0,25,-.15),(350,20,.3),'Earth');g.box((0,17.1,.2),(350,3.8,.4),'Grass');g.done()
f=Mesh('Left_Verge_Fence','Fence')
for x in range(-150,161,3):
 f.box((x,15.3,.65),(.065,.065,1.3),'Galvanized')
 for z in [.22,1.2]:f.box((x+1.5,15.3,z),(3,.04,.04),'Galvanized')
 for j in range(12):f.box((x+j*.25,15.3,.70),(.018,.025,.98),'Galvanized')
f.done()

print('Elevated viaduct: segmented box girder, parapets, piers',flush=True)
def vy(x):return 23+max(0,x-70)**2*.00025
for a in range(-165,180,30):
 b=Mesh('Viaduct_Span_%d'%a,'Building')
 for x in range(a,a+30,2):
  yy=vy(x+1);b.box((x+1,yy,13.8),(2.01,8.3,.55),'BridgeConcrete');b.box((x+1,yy,12.8),(2.01,5.9,1.45),'BridgeConcrete')
  b.box((x+1,yy,14.10),(2.01,7.6,.07),'Asphalt')
  for sg in [-1,1]:
   b.box((x+1,yy+sg*4.0,14.40),(2.01,.26,.8),'Concrete');b.box((x+1,yy+sg*4.0,14.83),(2.01,.34,.08),'WhiteMetal')
   b.box((x+1,yy+sg*3.58,13.46),(2.01,.20,.17),'DarkSteel')
 b.box((a+.015,vy(a),14.142),(.04,7.7,.014),'Joint');b.done()
for x in [-130,-70,-10,50,110,170]:
 p=Mesh('Viaduct_Pier_%d'%x,'Building');y=vy(x)
 p.box((x,y,.32),(5.1,6.2,.64),'Concrete');p.cyl((x,y,.6),(x,y,11.8),1.14,.94,'BridgeConcrete',24)
 p.box((x,y,11.83),(2.7,7.0,.62),'BridgeConcrete')
 for dy in [-2,2]:p.box((x,y+dy,12.20),(1.6,1.2,.16),'DarkSteel')
 p.done()

print('Petrol station on right rear, canopy and forecourt',flush=True)
m=Mesh('Petrol_Station','Building');x=-31;y=-32
m.box((x,y,5.62),(33,18,.48),'PetrolCream');m.box((x,y,5.96),(33.5,18.5,.28),'RedFascia');m.box((x,y,6.15),(32.6,17.6,.10),'PetrolCream')
for dx in [-11,0,11]:
 for dy in [-5.4,5.4]:
  m.box((x+dx,y+dy,2.7),(.55,.55,5.4),'PetrolCream');m.box((x+dx,y+dy,.55),(.59,.59,1.1),'RedFascia')
  m.box((x+dx,y+dy,5.345),(2.2,.65,.055),'WhiteMetal')
m.box((-33,-47,2.1),(37,8,4.2),'PetrolCream');m.box((-33,-42.92,2.0),(33,.10,2.8),'GlassDark');m.box((-33,-42.81,3.75),(37,.17,.60),'RedFascia')
for xx in range(-50,-14,3):m.box((xx,-42.82,1.9),(.09,.18,2.7),'WhiteMetal')
for dx in [-11,0,11]:
 for dy in [-3.5,3.5]:
  xx=x+dx;yy=y+dy;m.box((xx,yy,.10),(3.6,1.35,.20),'Concrete');m.box((xx,yy,.9),(1.02,.62,1.65),'PetrolCream');m.box((xx,yy,1.5),(1.04,.64,.65),'RedFascia')
  frontface(m,xx,yy+.326,1.47,.66,.29,'PetrolDisplay',1)
  for k in [-1,1]:
   prev=(xx+k*.57,yy,1.6)
   for j in range(1,13):
    u=j/12;pt=(xx+k*(.57+.16*math.sin(u*math.pi)),yy+.12*math.sin(u*math.pi),1.6-u*1.05);m.cyl(prev,pt,.024,.024,'DarkSteel',6);prev=pt
   m.box((xx+k*.58,yy,.69),(.08,.12,.23),'DarkSteel')
m.done()
sign=Mesh('Petrol_Pylon_And_Hedges','Props');sign.box((-7,-19,4.6),(1.10,.45,8.6),'PetrolCream');sign.box((-7,-19,8.45),(1.14,.48,.85),'RedFascia')
for z in [3.7,4.8,5.9,7]:sign.box((-7,-18.755,z),(.82,.04,.52),'PetrolDisplay')
sign.box((-70,-17,.52),(12,2.3,1.04),'Hedge');sign.box((-70,-17,.14),(12.4,2.6,.28),'Concrete');sign.done()

print('Distinctive streetfronts and background construction',flush=True)
for vals in [(16,-1,17,14,17,0,20),(35,-1,19,14,18,1,20),(56,-1,20,15,16,0,20),(97,-1,26,18,24,0,28),(-62,-1,13,14,13,1,27),(-105,-1,26,19,25,4,22),(-139,-1,27,18,22,1,22),(-94,1,28,20,47,1,46),(102,1,26,22,63,1,48),(140,-1,20,22,55,1,37)]:building(*vals)
cl=Mesh('Green_Construction_Scaffold','Building');cl.box((-63,41,15),(43,20,30),'Netting')
for x in range(-84,-40,3):
 for y in [30.92,51.08]:cl.box((x,y,15),(.065,.08,30),'Galvanized')
for z in range(1,31,2):
 cl.box((-63,30.84,z),(43,.065,.065),'Galvanized');cl.box((-63,51.1,z),(43,.065,.065),'Galvanized')
for x in range(-84,-43,6):
 for z in range(0,27,4):cl.cyl((x,30.77,z),(x+6,30.77,z+4),.025,.025,'ConstructionDark',5)
cl.box((-63,41,30.4),(43.8,20.8,.35),'Concrete');cl.done()
c=Mesh('Tower_Crane','Props');cx=-73;cy=47
for sx in [-1,1]:
 for sy in [-1,1]:c.cyl((cx+sx*.65,cy+sy*.65,0),(cx+sx*.65,cy+sy*.65,45),.055,.055,'CraneIvory',6)
for z in range(0,45,2):
 for sy in [-1,1]:c.cyl((cx-.65,cy+sy*.65,z),(cx+.65,cy+sy*.65,z+2),.035,.035,'CraneIvory',5)
 for sx in [-1,1]:c.cyl((cx+sx*.65,cy-.65,z),(cx+sx*.65,cy+.65,z+2),.035,.035,'CraneIvory',5)
for dx in range(-12,43,2):
 for dy in [-.6,.6]:c.cyl((cx+dx,cy+dy,44),(cx+dx+2,cy+dy,44),.05,.05,'CraneIvory',5);c.cyl((cx+dx,cy+dy,44),(cx+dx+2,cy,45.2),.025,.025,'CraneIvory',5)
 c.cyl((cx+dx,cy,45.2),(cx+dx+2,cy,45.2),.04,.04,'CraneIvory',5)
c.box((cx-10,cy,43.3),(3,2,2),'Concrete');c.cyl((cx+29,cy,44),(cx+29,cy,32),.015,.015,'DarkSteel',5);c.done()

print('Street trees, saplings, understorey and roadside hardware',flush=True)
for x in [-143,-126,-107,-87,13,28,44,61,78,91,108,123,141]:
 y=-18 if 8<x<73 else -12.9
 o=tree(x,y,.18,random.uniform(1.18,1.4));o.scale.x*=1.28;o.scale.y*=1.28
for x in range(-153,175,12):
 tree(x+random.uniform(-2,2),18.3,.2,random.uniform(.83,1.05))
 if x%3==0:tree(x+5,32,.05,1.15)
for x in [-49,-35,-21]:tree(x,-51,.1,.76)
for x in range(-150,171,17):
 tree(x,58,.1,random.uniform(1.1,1.6))
 tree(x,-61,.1,random.uniform(1.0,1.5))
for y in [-30,-3,24]:
 o=building(y,-1,24,16,random.choice([18,21,24]),1,175);o.rotation_euler.z=math.pi/2
under=Mesh('Hedge_Leaves','Vegetation')
for x in range(-150,166,2):
 for j in range(115):under.leaf((x+random.uniform(-1,1),random.uniform(16,18),random.uniform(.3,1.35)),random.uniform(.08,.18),'Leaf'+str(random.randrange(5)))
under.done()
props=Mesh('Street_Lights_And_Cameras','Props')
for x in range(-140,150,32):
 for sg in [-1,1]:
  y=sg*(18 if sg<0 and 8<x<73 else 11.4)
  if sg<0 and -78<x<8:continue
  props.cyl((x,y,.18),(x,y,8.7),.105,.06,'Galvanized',12);props.cyl((x,y,8.5),(x,sg*8.7,9.1),.06,.04,'Galvanized',8);props.box((x,sg*8.45,9.1),(.40,1.0,.15),'WhiteMetal')
  props.box((x,y,.34),(.5,.5,.4),'Concrete')
for x in [26,94]:
 basey=-17.7 if x==26 else -11.7
 props.cyl((x,basey,.1),(x,basey,6.4),.10,.065,'Galvanized',10);props.cyl((x,basey,6.4),(x,1.5,6.4),.07,.05,'Galvanized',10)
 for yy in [-8,-4,0]:props.box((x-.12,yy,6.28),(.35,.20,.16),'WhiteMetal');props.cyl((x-.31,yy,6.28),(x-.34,yy,6.28),.07,.07,'PetrolDisplay',12)
props.done()
sgn=Mesh('Yield_Merge_Signs','Props')
for x in [83,109]:
 y=-11.25;sgn.cyl((x,y,.18),(x,y,4.5),.045,.035,'Galvanized',10)
 sgn.face([(x-.041,y+.48,4.40),(x-.041,y-.48,4.40),(x-.041,y,3.56)],'Yield',[(0,1),(1,1),(.5,0)])
 textplane_x(sgn,x-.045,y,2.85,.36,1.20,'MergeNotice')
sgn.done()
# Small corrugated kiosk under right tree, seen in the latter front/right frames.
k=Mesh('Right_Kiosk_And_Utilities','Building');k.box((89,-16,1.7),(8,3.5,3.4),'DarkSteel');k.box((89,-14.21,1.8),(6.8,.07,2.4),'GlassDark');k.box((89,-16,3.47),(8.5,4.1,.15),'Galvanized')
for xx in range(86,93):k.box((xx,-14.10,1.9),(.05,.12,2.4),'Galvanized')
k.done()
# Distant junction is background only: not part of the navigable XODR segment.
bg=Mesh('Distant_Intersection_Visual_Only','Terrain');bg.box((150,0,-.105),(50,130,.2),'Asphalt');bg.done()
sig=Mesh('Distant_Signal_Furniture_Unconfigured','Props')
for sg in [-1,1]:
 sig.cyl((148,sg*12,0),(148,sg*12,6.5),.12,.07,'Galvanized',12);sig.cyl((148,sg*12,6.4),(148,sg*1,6.4),.08,.065,'Galvanized',10)
 for yy in [sg*3,sg*7]:
  sig.box((148,yy,6.05),(.26,1.12,.36),'DarkSteel')
  for k in [-1,0,1]:sig.cyl((147.84,yy+k*.32,6.05),(147.81,yy+k*.32,6.05),.105,.105,'SignalUnlit',14)
sig.done()
terr=Mesh('Context_Ground','Terrain');terr.box((0,0,-.48),(370,180,.70),'Earth');terr.done()

def camera(n,loc,target,lens=25):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);link(o,'Cameras');o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=1500;return o
cams={
 '00_aerial':camera('VIEW_Aerial',(84,77,74),(-5,-11,3),38),
 '01_front':camera('VIEW_Front',(0,-8.75,1.55),(70,-8.75,2.15),23),
 '02_rear':camera('VIEW_Rear',(0,-8.75,1.55),(-62,-8.75,2.4),22),
 '03_left':camera('VIEW_Left',(0,-8.75,1.55),(0,27,8),20),
 '04_right':camera('VIEW_Right',(0,-8.75,1.55),(-7,-34,3),20),
 '05_parking_detail':camera('VIEW_Parking',(11,-8.8,2.3),(44,-18.9,3.1),28),
 '06_after_lane_change':camera('VIEW_Later',(86,-8.75,1.65),(145,-8,2.2),24),
 '07_full_extent':camera('VIEW_Overview',(-208,-231,193),(0,0,0),40)}
ld=bpy.data.lights.new('Cloud_Filtered_Sun','SUN');lo=bpy.data.objects.new('Cloud_Filtered_Sun',ld);link(lo,'Lighting');lo.rotation_euler=Vector((15,25,-90)).to_track_quat('-Z','Y').to_euler();ld.energy=1.25;ld.angle=.28
world=bpy.data.worlds.new('Bright_Overcast');world.use_nodes=True;scene.world=world;ns=world.node_tree.nodes;lk=world.node_tree.links;bg=ns.get('Background');bg.inputs['Strength'].default_value=.40
sky=ns.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_disc=False;sky.sun_elevation=.80;sky.sun_rotation=2.5;sky.air_density=1.4;sky.dust_density=2.5;lk.new(sky.outputs['Color'],bg.inputs['Color'])
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception as e:print(e)
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.25;scene.render.image_settings.file_format='PNG';scene.camera=cams['01_front']
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH' and not o.hide_render:o.select_set(True)
exported=[o for o in scene.objects if o.select_get()]
stats={'objects':len(exported),'mesh_vertices_instances':sum(len(o.data.vertices) for o in exported),'polygons_instances':sum(len(o.data.polygons) for o in exported),'materials':len(M),'excluded':'vehicles, pedestrians, cameras, lights, hidden prototypes','accuracy':'multi-view visual reconstruction, estimated scale, not photogrammetric survey','navigable_extent_x_m':[XMIN,XMAX]}
for o in exported:o['source']='four-view parameterized visual reconstruction';o['metric_accuracy']='estimated'
print('Export FBX',stats,flush=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/(NAME+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False)
for o in tree_protos:bpy.data.objects.remove(o,do_unlink=True)
for img in bpy.data.images:
 if img.source=='FILE':img.filepath='//textures/'+Path(img.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(NAME+'.blend')))
(ROOT/'validation/mesh_statistics.json').write_text(json.dumps(stats,indent=2))
for name,cam in cams.items():
 scene.camera=cam;scene.render.filepath=str(ROOT/'renders'/(name+'.png'));print('RENDER',name,flush=True);bpy.ops.render.render(write_still=True)
print('FINISHED',flush=True)
