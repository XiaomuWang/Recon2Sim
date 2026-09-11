"""Simplified video-informed truck/trike props, +X front, ground-centre origin, metres."""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];(P/'assets').mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(512189);mats={}
def mat(n,c,metal=0,rough=.7):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;mats[n]=m
for n,c,me,ro in [('OliveDust',(.39,.34,.19),.25,.83),('Bed',(.24,.21,.15),.5,.8),('Steel',(.12,.13,.12),.8,.5),('Rubber',(.022,.024,.022),0,.94),('Window',(.075,.13,.14),.3,.2),('Lamp',(.72,.67,.48),.2,.22),('RedLamp',(.42,.035,.018),.1,.3),('Blue',(.025,.07,.24),.5,.65),('Seat',(.075,.036,.024),0,.9),('Skin',(.38,.24,.14),0,.9),('Cloth',(.08,.11,.16),0,.85)]:mat(n,c,me,ro)
parts=[]
def finish(o,ma,bevel=0):
 o.data.materials.append(mats[ma]);parts.append(o)
 if bevel:
  mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o

def box(c,d,ma,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,ma,bevel)
def cyl(c,r,depth,ma,axis='Y',vertices=20):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=c);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 elif axis=='X':o.rotation_euler.y=math.pi/2
 return finish(o,ma,.008)
def bar(a,b,r,ma):
 v=Vector(b)-Vector(a);o=cyl((Vector(a)+Vector(b))/2,r,v.length,ma,'Z',10);o.rotation_euler=v.to_track_quat('Z','Y').to_euler();return o
def join(name):
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');parts.clear()
 return o

# ---- video-informed silhouette assets, no brand names or plate identifiers ----
for n,c in [('White',(.73,.75,.71)),('Green',(.025,.35,.20)),('Teal',(.03,.45,.42)),('Yellow',(.76,.57,.045)),('Black',(.025,.03,.035)),('CabRed',(.48,.026,.04)),('Tank',(.54,.51,.40)),('Silver',(.40,.45,.45))]:mat(n,c,.22,.43)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
assets=[];dimensions={}
def export_asset(o,name,dims):
 pts=[v.co for v in o.data.vertices];lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)];origin=[(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]]
 for v in o.data.vertices:
  for i in range(3):v.co[i]=(v.co[i]-origin[i])*dims[i]/(hi[i]-lo[i])
 o.name=name;dimensions[name]=dims;bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
 bpy.ops.export_scene.fbx(filepath=str(P/'assets'/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE')
 assets.append(o)
def wheels(xs,width,r):
 for x in xs:
  for sg in [-1,1]:
   cyl((x,sg*(width/2-.12),r),r,.28,'Rubber');cyl((x,sg*(width/2+.025),r),r*.53,.025,'Silver')
   for k in range(7):
    a=k*math.tau/7;cyl((x+math.sin(a)*r*.34,sg*(width/2+.04),r+math.cos(a)*r*.34),.022,.03,'Steel',vertices=8)
def lights(front,rear,width,z):
 for sg in [-1,1]:
  box((front,sg*width*.34,z),(.04,.32,.15),'Lamp',.015);box((rear,sg*width*.36,z),(.04,.19,.26),'RedLamp',.014)
def van_asset(name,col,L,W,H,box_body=False):
 box((0,0,.63),(L-.15,W-.08,.55),col,.13);box((.0,0,1.55),(L-.55,W-.16,H-1.25),col,.16)
 xf=L/2-.25;box((xf,0,H-.75),(.08,W-.29,.80),'Window',.065)
 for sg in [-1,1]:
  box((xf-.48,sg*(W/2-.015),H-.75),(.83,.025,.73),'Window',.05)
  for xx in [-1.05,.35]:box((xx,sg*(W/2+.012),1.35),(.18,.028,.06),'Steel',.006)
  bar((xf-.05,sg*W/2,H-.73),(xf,sg*(W/2+.16),H-.62),.018,'Steel');box((xf,sg*(W/2+.18),H-.71),(.10,.10,.26),'Black')
  if col=='Green':
   for xx in [-1.4,-.95,-.5,-.05]:box((xx,sg*(W/2+.012),1.45),(.29,.018,.075),'White',0)
 box((L/2-.04,0,.59),(.11,W,.14),'Black');box((-L/2+.04,0,.6),(.12,W,.15),'Black')
 for yy in [-.015,.015]:box((-L/2+.055,yy,1.55),(.04,.02,H-1.1),'Steel',.005)
 wheels([-L*.31,L*.3],W,.35);lights(L/2+.01,-L/2-.01,W,.85)
 export_asset(join(name),name,(L,W,H))
van_asset('meituan_green_van','Green',5.6,2,2.6)
van_asset('meituan_delivery_ego','Yellow',3.6,1.65,1.8)
# Compact cab-over box truck, separate white cargo box and wheels.
box((-.2,0,.7),(6,.8,.28),'Steel');box((2.25,0,1.5),(1.9,2.1,1.75),'White',.10);box((3.18,0,2.04),(.04,1.85,.66),'Window',.04)
for sg in [-1,1]:box((2.25,sg*1.065,2.08),(1.37,.025,.62),'Window',.03)
box((-1,0,1.91),(4.15,2.15,2.2),'White',.04)
for sg in [-1,1]:
 for xx in [-2.95,-1.8,-.65,.5,1.04]:box((xx,sg*1.09,1.91),(.045,.035,2.18),'Silver',0)
for yy in [-.95,0,.95]:box((-3.1,yy,1.9),(.04,.035,2.1),'Silver',0)
wheels([-2,2.3],2.2,.42);lights(3.22,-3.18,2.1,.85);export_asset(join('meituan_boxtruck'),'meituan_boxtruck',(6.4,2.2,3.1))
# Red cab and cylindrical tanker. Approximate appearance, not articulated physics.
box((0,0,.8),(12.1,.9,.35),'Steel');box((4.9,0,1.7),(2.3,2.35,2.2),'CabRed',.15);box((6.06,0,2.35),(.05,2.05,.84),'Window',.06)
for sg in [-1,1]:box((5.0,sg*1.19,2.35),(1.65,.03,.80),'Window',.06)
cyl((-1.25,0,2.05),1.17,9.2,'Tank','X',48)
for x in [-5.7,-3.5,-1.3,.9,3.1]:cyl((x,0,2.05),1.19,.055,'Silver','X',40)
for x in [-3.5,0,2]:cyl((x,0,3.25),.23,.14,'Steel','Z',16)
for sg in [-1,1]:bar((-5.6,sg*.55,3.22),(3.1,sg*.55,3.22),.025,'Steel')
for z in [.9,1.25,1.6,1.95,2.3,2.65,3]:bar((-5.88,-.35,z),(-5.88,.35,z),.025,'Steel')
wheels([-4.8,-3.55,-2.3,4.8],2.4,.48);lights(6.17,-6.17,2.3,.95);export_asset(join('meituan_tanker'),'meituan_tanker',(12.5,2.5,3.5))
def citybus(name,col):
 L=11.4;W=2.5;box((0,0,.73),(11.25,2.45,.73),col,.13);box((0,0,1.88),(11.20,2.40,1.75),'Black',.14);box((0,0,3.0),(11.05,2.36,.25),col,.1)
 box((5.57,0,2.05),(.045,2.14,1.48),'Window',.055);box((-5.57,0,2.1),(.045,2.11,1.16),'Window',.06)
 for sg in [-1,1]:
  for x in [-4.8,-3.2,-1.6,0,1.6,3.2,4.7]:
   box((x,sg*1.218,2.07),(1.4,.025,1.13),'Window',.026);box((x-.74,sg*1.237,2.1),(.055,.035,1.35),'Silver',.002)
  box((0,sg*1.249,1.17),(10.3,.018,.38),col,.01)
  if col=='Yellow':
   for x in [-3.8,-2.7,-1.6,-.5,.6,1.7,2.8]:box((x,sg*1.267,1.21),(.65,.015,.14),'White',0)
 # Two glass passenger doors on vehicle right.
 for x in [4.6,.6]:
  box((x,-1.25,1.55),(1.12,.035,2.15),'Window',.025);box((x,-1.274,1.53),(.055,.02,2.08),'Silver',0)
 for x in [-2.0,.8]:box((x,0,3.12),(2.0,1.35,.14),'Silver',.06)
 wheels([-3.6,3.65],2.5,.48);lights(5.64,-5.64,2.4,.91)
 export_asset(join(name),name,(11.4,2.5,3.2))
citybus('meituan_citybus','Teal');citybus('meituan_adbus','Yellow')
for i,o in enumerate(assets):o.location=(0,i*5,0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'assets/MeituanDynamicAssets.blend'))
(P/'assets/dimensions.json').write_text(json.dumps(dimensions,indent=2))
(P/'MeituanDynamicProps.json').write_text(json.dumps({'maps':[],'props':[{'name':o.name,'size':'big','tag':'Static','source':'./assets/'+o.name+'.fbx'} for o in assets]},indent=2))
print('Exported',len(assets),'optional static props for timestamp replay')
