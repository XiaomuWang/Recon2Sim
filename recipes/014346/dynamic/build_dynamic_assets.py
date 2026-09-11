"""Simplified video-informed truck/trike props, +X front, ground-centre origin, metres."""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];(P/'assets').mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(14346);mats={}
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
def export(o,name):
 # Match the complete visible envelope to the trajectory's estimated dimensions.
 target=(8.4,2.5,3.3) if 'Truck' in name or 'dumptruck' in name else (2.8,1.25,1.6)
 coords=[v.co.copy() for v in o.data.vertices]
 lo=[min(c[i] for c in coords) for i in range(3)];hi=[max(c[i] for c in coords) for i in range(3)]
 origin=[(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]]
 for v in o.data.vertices:
  for i in range(3):v.co[i]=(v.co[i]-origin[i])*target[i]/(hi[i]-lo[i])
 name='nanshan_dumptruck' if target[0]>5 else 'nanshan_cargotrike'
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
 bpy.ops.export_scene.fbx(filepath=str(P/'assets'/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE')
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
# Truck: six wheels, cab-over form, ribbed open dump body and rear lifting frame.
box((-.4,0,.91),(7.1,.85,.34),'Steel');box((2.55,0,1.61),(2.55,2.35,1.85),'OliveDust',.1);box((2.52,0,2.81),(2.3,2.27,.27),'OliveDust',.1)
box((3.83,0,1.05),(.2,2.5,.34),'Steel');box((3.853,0,1.64),(.024,1.65,.48),'Steel',.004)
for z in [1.46,1.57,1.68,1.79]:box((3.871,0,z),(.019,1.55,.025),'Bed',0)
box((3.818,0,2.37),(.04,2.06,.7),'Window',.03)
box((3.85,0,2.36),(.06,.05,.75),'OliveDust',.005)
for y in [-1.19,1.19]:
 box((2.75,y,2.38),(1.85,.04,.72),'Window',.035);box((2.68,y,1.54),(1.94,.03,.56),'OliveDust',.02);box((2.12,y*1.01,1.8),(.28,.035,.055),'Steel',.012)
 box((3.84,y*.75,1.26),(.065,.45,.24),'Lamp',.03);box((2.4,y*1.04,.65),(1.3,.22,.11),'Steel')
 bar((3.29,y,2.49),(3.44,y*1.22,2.56),.023,'Steel');box((3.46,y*1.22,2.39),(.11,.2,.4),'Steel')
for x in [2.55,-1.4,-2.75]:
 for y in [-1.04,1.04]:
  cyl((x,y,.57),.56,.41,'Rubber');cyl((x,y*1.21,.57),.29,.045,'Steel')
  for j in range(8):
   ang=j*math.tau/8;cyl((x+math.sin(ang)*.205,y*1.235,.57+math.cos(ang)*.205),.027,.015,'OliveDust',vertices=8)
  box((x,y,1.14),(1.5,.47,.09),'Bed')
box((-1.3,0,1.35),(5.5,2.45,.2),'Bed')
for y in [-1.2,1.2]:
 box((-1.3,y,2.05),(5.5,.12,1.35),'Bed')
 box((-1.3,y,2.76),(5.6,.16,.13),'OliveDust')
 for x in [-3.8,-2.9,-2,-1.1,-.2,1]:box((x,y*1.04,2.05),(.11,.14,1.4),'OliveDust')
 for i in range(24):box((random.uniform(-3.8,1.2),y*1.056,random.uniform(1.53,2.62)),(random.uniform(.05,.3),.012,.022),'Steel',0)
box((-4.05,0,2.05),(.13,2.43,1.35),'Bed');box((1.44,0,2.05),(.13,2.43,1.35),'OliveDust')
for y in [-1.08,1.08]:bar((-3.6,y,1.52),(1.0,y,3.23),.085,'OliveDust');box((-4.15,y,1.13),(.1,.22,.17),'RedLamp')
truck=join('NanshanDumpTruck');export(truck,'nanshan_dumptruck')
# Cargo tricycle includes a simple rider silhouette; no brand or license-plate invention.
box((-.3,0,.55),(1.8,.65,.13),'Steel');box((-.5,0,.83),(1.7,1.17,.12),'Blue')
for y in [-.57,.57]:
 box((-.5,y,1.05),(1.75,.07,.4),'Blue');box((-.5,y,1.27),(1.8,.045,.04),'Steel')
 for x in [-1.2,-.7,-.2,.3]:box((x,y,1.05),(.04,.07,.42),'Steel',.005)
box((-1.34,0,1.05),(.07,1.17,.4),'Blue');box((.34,0,1.05),(.07,1.17,.4),'Blue')
for x,y in [(-.9,-.52),(-.9,.52),(1.03,0)]:cyl((x,y,.31),.3,.13,'Rubber');cyl((x,y-.07,.31),.17,.024,'Steel')
bar((.5,0,.5),(1.06,0,1.07),.05,'Steel');bar((1.06,-.35,1.07),(1.06,.35,1.07),.035,'Steel');box((.49,0,.92),(.39,.42,.14),'Seat')
box((.55,0,1.24),(.3,.37,.48),'Cloth',.07);bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.16,location=(.65,0,1.61));finish(bpy.context.object,'Skin')
for y in [-.18,.18]:bar((.6,y,1.35),(1,y,1.06),.045,'Cloth');bar((.49,y,.99),(.72,y,.56),.06,'Cloth')
trike=join('NanshanCargoTrike');export(trike,'nanshan_cargotrike');trike.location=(0,5,0)
camd=bpy.data.cameras.new('AssetCamera');cam=bpy.data.objects.new('AssetCamera',camd);scene.collection.objects.link(cam);cam.location=(12,-13,8);cam.rotation_euler=(Vector((0,1.6,1))-cam.location).to_track_quat('-Z','Y').to_euler();camd.lens=42;scene.camera=cam
world=bpy.data.worlds.new('Studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.65,.8,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8;scene.world=world
ld=bpy.data.lights.new('Key','AREA');lo=bpy.data.objects.new('Key',ld);scene.collection.objects.link(lo);lo.location=(3,-5,10);ld.energy=1800;ld.shape='DISK';ld.size=8
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
try:
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
 for dev in p.devices:dev.use=dev.type=='OPTIX'
 scene.cycles.device='GPU'
except:pass
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True;scene.render.filepath=str(P/'preview/dynamic_assets.png')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'assets/NanshanDynamicAssets.blend'));bpy.ops.render.render(write_still=True)
(P/'NanshanDynamicProps.json').write_text(json.dumps({'maps':[],'props':[{'name':'nanshan_dumptruck','size':'big','tag':'Static','source':'./assets/nanshan_dumptruck.fbx'},{'name':'nanshan_cargotrike','size':'medium','tag':'Static','source':'./assets/nanshan_cargotrike.fbx'}]},indent=2))
print('Custom props exported')
