"""Video-informed mesh props. +X nose, ground-centre origin, metre scale."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
mats={};parts=[];objects=[]
def mat(n,c,metal=0,rough=.55):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;mats[n]=m
for n,c,m,r in [('Red',(.48,.025,.045),.25,.4),('Yellow',(.85,.65,.06),.2,.4),('White',(.78,.81,.78),.15,.4),('Steel',(.22,.27,.29),.8,.4),('Black',(.018,.025,.031),.25,.35),('Glass',(.025,.075,.09),.3,.17),('Rubber',(.017,.021,.021),0,.9),('Lamp',(.84,.87,.71),.1,.2),('RearLamp',(.65,.015,.008),.1,.2),('Cyan',(.035,.52,.48),.15,.4),('Lime',(.4,.69,.018),.1,.5),('Brush',(.22,.23,.1),0,.95),('Blue',(.02,.06,.16),.2,.45),('Skin',(.49,.32,.21),0,.8)]:mat(n,c,m,r)
def finish(o,ma,b=.025):
 o.data.materials.append(mats[ma]);parts.append(o)
 if b:
  mod=o.modifiers.new('Rounded edges','BEVEL');mod.width=b;mod.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o
def box(c,d,ma,b=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,ma,b)
def cyl(c,r,depth,ma,axis='Y',n=24):
 bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=depth,location=c);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 elif axis=='X':o.rotation_euler.y=math.pi/2
 return finish(o,ma,.007)
def bar(a,b,r,ma):
 d=Vector(b)-Vector(a);o=cyl((Vector(a)+Vector(b))/2,r,d.length,ma,'Z',10);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
def wheel(x,y,r):
 cyl((x,y,r),r,.24,'Rubber');cyl((x,y*1.07,r),r*.56,.08,'Steel')
 for j in range(8):
  a=j*math.tau/8;cyl((x+math.sin(a)*r*.36,y*1.115,r+math.cos(a)*r*.36),.018,.012,'Black',n=8)
def join(n,dims,export=True):
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=n;bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');parts.clear()
 lo=[min(v.co[i] for v in o.data.vertices) for i in range(3)];hi=[max(v.co[i] for v in o.data.vertices) for i in range(3)]
 for v in o.data.vertices:
  for i in range(3):v.co[i]=(v.co[i]-(lo[i] if i==2 else (hi[i]+lo[i])/2))*dims[i]/(hi[i]-lo[i])
 if export:bpy.ops.export_scene.fbx(filepath=str(P/'assets'/(n+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE')
 objects.append(o);return o
# Coach: rear red luggage body, panoramic upper glazing, front yellow fascia.
box((0,0,1.55),(11.7,2.45,2.45),'Red',.2);box((0,0,2.95),(11.55,2.42,1.12),'Steel',.18);box((0,0,3.52),(11.3,2.4,.12),'White',.08)
for y in [-1.235,1.235]:
 for x in [-4.7,-3.1,-1.5,.1,1.7,3.3,4.8]:box((x,y,2.76),(1.46,.034,.98),'Glass',.055)
 box((-.2,y,1.54),(10.5,.035,.09),'Yellow',0)
 for x in [-4.5,-2.5,-.5,1.5]:box((x,y,1.07),(1.8,.04,.6),'Red',.05);box((x+.55,y*1.02,1.22),(.25,.025,.055),'Steel',.01)
 for x in [-3.8,3.65]:wheel(x,y*.93,.51)
 for i in range(12):box((-4.8+i*.11,y*1.015,1.8),(.025,.022,.32),'Black',.003)
box((5.82,0,1.32),(.12,2.42,1.75),'Yellow',.06);box((5.86,0,2.73),(.035,2.2,1.16),'Glass',.07);box((-5.86,0,2.7),(.035,1.95,.82),'Glass',.09)
for y in [-.86,.86]:
 box((5.91,y,.95),(.04,.45,.19),'Lamp',.04);box((-5.91,y,1.23),(.04,.15,.72),'RearLamp',.025)
 bar((5.3,y*1.43,2.7),(5.7,y*1.7,2.6),.035,'Steel');box((5.73,y*1.72,2.36),(.14,.18,.46),'Black',.06)
coach=join('greenrail_coach',(11.8,2.5,3.65))
# Compact driverless sweeper: cyan front shell, lime sides, dark lid, sensors and visible brushes.
box((-.1,0,.88),(1.25,.91,1.34),'Cyan',.16);box((-.07,0,1.58),(1.29,.96,.18),'Black',.055)
for y in [-.464,.464]:
 box((-.22,y,.94),(.9,.025,1.0),'Lime',.035)
 box((-.69,y,.94),(.06,.03,.99),'Red',.015)
 for x in [-.37,.35]:wheel(x,y*.78,.21)
 # Circular graphic accents inspired by the photographed machine, no invented lettering.
 for x in [-.47,-.18,.12]:
  cyl((x,y*1.036,1.18),.07,.009,'White',n=24);cyl((x,y*1.049,1.18),.052,.011,'Lime',n=24)
box((.552,0,.42),(.09,.92,.2),'White',.06)
for y in [-.32,.32]:cyl((.56,y,1.24),.04,.022,'Black','X',16)
cyl((0,0,1.76),.105,.13,'Steel','Z');cyl((0,0,1.83),.11,.065,'Black','Z');box((-.15,0,1.67),(.62,.3,.07),'Cyan',.04)
for x,y in [(.58,-.43),(.58,.43),(-.6,-.44),(-.6,.44)]:
 bar((x*.58,y*.65,.3),(x,y,.13),.023,'Steel');cyl((x,y,.095),.23,.045,'Brush','Z',36);cyl((x,y,.13),.1,.05,'Steel','Z')
 for j in range(40):
  a=j*math.tau/40;bar((x+math.cos(a)*.10,y+math.sin(a)*.10,.11),(x+math.cos(a)*.24,y+math.sin(a)*.24,.025),.005,'Brush')
sweeper=join('greenrail_sweeper',(1.65,1.18,1.85))
def cab(front,body='White'):
 box((front-.6,0,1.45),(1.8,2.15,1.85),body,.12);box((front+.32,0,1.95),(.04,1.85,.73),'Glass',.04)
 for y in [-1.085,1.085]:box((front-.54,y,1.96),(1.4,.025,.74),'Glass',.04);wheel(front-.65,y*.92,.47);box((front+.35,y*.78,1.0),(.06,.39,.2),'Lamp',.025)
 box((front+.34,0,1.1),(.04,1.17,.35),'Black',.02)
cab(3.1);box((-1,0,2.03),(4.3,2.3,2.55),'White',.06);box((-.4,0,.7),(6.8,1,.24),'Steel')
for y in [-1.02,1.02]:wheel(-2.1,y,.47)
for y in [-.58,.58]:box((-3.16,y,2.02),(.03,1.08,2.4),'White',.02);bar((-3.2,y,1),(-3.2,y,3.05),.018,'Steel')
for y in [-1.16,1.16]:box((-1,y,.94),(4.2,.02,.04),'Yellow',0)
boxtruck=join('greenrail_boxtruck',(7.2,2.45,3.35))
cab(7.0,'Red');box((-1.2,0,2.23),(11.3,2.4,3.1),'Red',.04);box((0,0,.7),(14,1.4,.3),'Steel')
for y in [-1.22,1.22]:
 for j in range(59):box((-6.7+j*.19,y,2.23),(.075,.045,2.94),'Red',.009)
 for x in [-5.3,-4.2,3.6,4.65]:wheel(x,y*.86,.49)
for y in [-.6,.6]:box((-6.88,y,2.25),(.04,1.16,2.98),'Red',.02);bar((-6.94,y,.95),(-6.94,y,3.6),.02,'Steel')
container=join('greenrail_container',(15.2,2.5,4))
# Generic visual proxies for inspectable Blender animation.
box((0,0,.64),(4.6,1.82,.72),'White',.18);box((-.15,0,1.16),(2.7,1.64,.67),'Glass',.16);box((-.25,0,1.48),(2.3,1.62,.10),'White',.06)
for y in [-.84,.84]:
 for x in [-1.45,1.4]:wheel(x,y,.34)
for y in [-.6,.6]:box((2.29,y,.8),(.03,.44,.19),'Lamp',.025);box((-2.29,y,.8),(.03,.43,.19),'RearLamp',.025)
car=join('preview_car',(4.7,1.9,1.65),False)
box((0,0,.62),(1.45,.4,.5),'Blue',.12);box((-.15,0,.98),(.7,.42,.12),'Black',.06)
for x in [-.65,.65]:wheel(x,0,.27)
bar((.6,0,.35),(.44,0,1.2),.03,'Steel');bar((.44,-.3,1.2),(.44,.3,1.2),.025,'Steel')
box((-.15,0,1.33),(.35,.43,.5),'Blue',.1);cyl((-.1,0,1.67),.14,.23,'Black','Z')
scoot=join('preview_scooter',(1.95,.7,1.75),False)
for y in [-.14,.14]:bar((0,y,.07),(0,y,.83),.07,'Black')
box((0,0,1.12),(.33,.43,.57),'Blue',.09)
for y in [-.28,.28]:bar((0,y,1.33),(.06,y,.87),.064,'Skin')
bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=.14,location=(0,0,1.59));finish(bpy.context.object,'Skin',0)
human=join('preview_pedestrian',(.5,.5,1.72),False)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'assets/GreenRailDynamicAssets.blend'))
config={'props':[{'name':o.name,'path':'/Game/GreenRailDynamic/'+o.name+'.'+o.name,'size':'Small' if 'sweeper' in o.name else 'Big'} for o in [coach,sweeper,boxtruck,container]]}
(P/'assets/props_registry_entries.json').write_text(json.dumps(config,indent=2))
manifest={'units':'metres','forward':'+X','up':'+Z','origin':'bounding box ground centre','props':[{'name':o.name,'dimensions_m':list(o.dimensions),'vertices':len(o.data.vertices)} for o in objects]};(P/'assets/mesh_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Assets saved')
