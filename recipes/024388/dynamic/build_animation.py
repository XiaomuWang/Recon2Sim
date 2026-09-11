"""Editable scene preview and optional green/orange box-truck mesh; not CARLA footage."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];D=json.loads((P/'scenario.json').read_text(encoding='utf-8'));(P/'assets').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'environment_reconstruction_024388/LuoboTurn024388.blend'))
scene=bpy.context.scene;parts=[]
def mat(n,col,metal=0,rough=.4,emit=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*col,1);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emit:p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=emit
 return m
paint=mat('Dynamic paint',(.35,.4,.43),.35);glass=mat('Dynamic smoked glass',(.018,.045,.061),.5,.16);rubber=mat('Dynamic tyres',(.022,.025,.026),0,.8);alloy=mat('Dynamic alloy',(.44,.47,.48),.85,.28);white=mat('Dynamic lamp white',(.83,.91,1),.1,.3,3);red=mat('Dynamic brake lamp',(.85,.015,.008),.1,.25,2);green=mat('Truck green corrugated box',(.043,.18,.085),.25,.48);orange=mat('Truck orange rear',(.72,.22,.026),.15,.52);teal=mat('Truck teal cab',(.035,.17,.17),.25,.38);skin=mat('Dynamic skin',(.52,.32,.2));cloth=mat('Dynamic rider jacket',(.19,.23,.3));black=mat('Dynamic black',(.035,.04,.045))
def cube(c,d,m,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:
  mo=o.modifiers.new('Soft edges','BEVEL');mo.width=bevel;mo.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mo.name)
 parts.append(o);return o
def cyl(c,r,depth,m,axis='Y'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=depth,location=c);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 o.data.materials.append(m);parts.append(o)
 for p in o.data.polygons:p.use_smooth=True
 return o
def sphere(c,r,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=r,location=c);o=bpy.context.object;o.data.materials.append(m);parts.append(o)
def join(name):
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');parts.clear();return o
def wheels(xs,y,r):
 for x in xs:
  for sign in [-1,1]:
   cyl((x,sign*y,r),r,.24,rubber);cyl((x,sign*(y+.125),r),r*.58,.015,alloy)
def car():
 cube((0,0,.63),(4.6,1.84,.65),paint,.16);cube((-.2,0,1.11),(2.55,1.64,.65),glass,.18);cube((-.25,0,1.45),(2.2,1.56,.09),paint,.05)
 for x in [-1.15,.75]:
  for y in [-.81,.81]:cube((x,y,1.15),(.08,.08,.59),paint,.015)
 cube((1.65,0,.99),(1.05,1.77,.10),paint,.05);cube((-1.75,0,.96),(.95,1.75,.10),paint,.04)
 for y in [-.62,.62]:cube((2.3,y,.77),(.035,.46,.17),white,.025);cube((-2.3,y,.82),(.035,.47,.12),red,.02)
 cube((2.31,0,.52),(.03,.8,.2),black,.03);wheels([-1.4,1.43],.88,.34)
 return join('ProxyCar')
carproto=car()
cube((-.55,0,1.9),(4.9,2.23,2.65),green,.025);cube((-3.02,0,1.9),(.045,2.24,2.65),orange,.01);cube((0,0,.48),(6.7,1.92,.29),black,.04)
for x in [v*.18-2.85 for v in range(26)]:
 for y in [-1.13,1.13]:cube((x,y,1.9),(.035,.018,2.55),green,.008)
for y in [-1.06,0,1.06]:cube((-3.055,y,1.9),(.028,.035,2.5),alloy,.005)
for y in [-.58,.58]:cube((-3.08,y,1.9),(.035,.03,2.1),alloy,.004);cube((-3.1,y,1.58),(.04,.22,.03),black,.01)
cube((2.43,0,1.22),(1.8,2.2,1.95),teal,.14);cube((2.78,0,2.25),(1.1,2.1,.72),glass,.07);cube((2.64,0,2.66),(1.42,2.16,.1),teal,.04)
cube((3.36,0,.94),(.05,1.25,.43),black,.02);cube((3.37,0,.61),(.08,2.15,.2),alloy,.04)
for y in [-.84,.84]:cube((3.38,y,1.04),(.045,.36,.2),white,.02);cube((-3.12,y,.62),(.04,.31,.14),red,.02)
for y in [-1.28,1.28]:cube((2.7,y,2.09),(.25,.10,.4),black,.035)
wheels([-1.98,2.35],1.02,.45);truckproto=join('LuoboBoxTruck')
bpy.ops.object.select_all(action='DESELECT');truckproto.select_set(True);bpy.context.view_layer.objects.active=truckproto
bpy.ops.export_scene.fbx(filepath=str(P/'assets/LuoboBoxTruck.fbx'),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False,add_leaf_bones=False,path_mode='COPY',embed_textures=True)
def human():
 for y in [-.13,.13]:cyl((0,y,.46),.085,.73,black,'Z');cube((.08,y,.075),(.29,.18,.13),black,.04)
 cube((0,0,1.08),(.32,.46,.56),cloth,.07)
 for y in [-.29,.29]:cyl((0,y,1.03),.065,.52,cloth,'Z')
 sphere((0,0,1.57),.15,skin);return join('ProxyHuman')
humanproto=human()
cube((-.13,0,.54),(1.45,.42,.43),paint,.14);cube((-.25,0,.83),(.63,.44,.12),black,.05);cube((.62,0,.98),(.17,.4,.7),paint,.05)
for x in [-.63,.65]:cyl((x,0,.28),.28,.12,rubber)
cube((.65,0,1.26),(.11,.6,.05),alloy,.02);cube((.76,0,1.12),(.035,.23,.15),white,.04);cube((-.8,0,.6),(.03,.2,.09),red,.02)
cube((-.23,0,1.14),(.31,.42,.46),cloth,.09);sphere((-.18,0,1.51),.155,cloth)
for y in [-.19,.19]:cube((.03,y,.84),(.56,.14,.16),black,.06)
scootproto=join('ProxyScooterRider');protos={'car':carproto,'suv':carproto,'mpv':carproto,'truck':truckproto,'pedestrian':humanproto,'motorcycle':scootproto,'tricycle':scootproto}
coll=bpy.data.collections.new('Video_Recovered_Targets');scene.collection.children.link(coll)
for a in D['actors']:
 proto=protos[a['category']];o=proto.copy();o.data=proto.data.copy();o.name=a['id'];coll.objects.link(o)
 c=tuple((int(x)/255)**2.2 for x in a['color'].split(','));acol=mat('Actor_'+a['id'],c,.3 if a['category'] in ['car','suv','mpv'] else 0)
 for slot in o.material_slots:
  if slot.material in [paint,cloth]:slot.material=acol
 vs=[Vector(v) for v in o.bound_box];lo=Vector([min(v[i] for v in vs) for i in range(3)]);hi=Vector([max(v[i] for v in vs) for i in range(3)]);dim=hi-lo;o.scale=[a['dimensions_m'][k]/dim[i] for i,k in enumerate(['length','width','height'])];cen=(lo+hi)/2;centre=Vector([cen[i]*o.scale[i] for i in range(3)]);bottom=lo.z*o.scale.z
 ss=a['samples'][::6]
 if ss[-1]!=a['samples'][-1]:ss.append(a['samples'][-1])
 for s in ss:
  fr=1+s['t']*30;h=s['h'];o.location=(s['x']-centre.x*math.cos(h)+centre.y*math.sin(h),s['y']-centre.x*math.sin(h)-centre.y*math.cos(h),s['z']-bottom+.025);o.rotation_euler=(0,0,h);o.keyframe_insert('location',frame=fr);o.keyframe_insert('rotation_euler',frame=fr)
 start=1+a['start_t']*30;end=1+a['end_t']*30
 for fr,hide in [(0,True),(max(.01,start-.01),True),(start,False),(end,False),(end+.01,True)]:o.hide_render=hide;o.hide_viewport=hide;o.keyframe_insert('hide_render',frame=fr);o.keyframe_insert('hide_viewport',frame=fr)
 for fc in o.animation_data.action.fcurves:
  for kp in fc.keyframe_points:kp.interpolation='CONSTANT' if 'hide_' in fc.data_path else 'LINEAR'
 o['source_views']=a['source_views'];o['metric_confidence']='estimated';o['blueprint_fallback']=a['blueprint_candidates'][0]
for o in [carproto,truckproto,humanproto,scootproto]:bpy.data.objects.remove(o,do_unlink=True)
scene.frame_start=1;scene.frame_end=5371;scene.render.fps=30
cd=bpy.data.cameras.new('DynamicReview');cam=bpy.data.objects.new('DynamicReview',cd);scene.collection.objects.link(cam);scene.camera=cam;cd.lens=24
cam.location=(-1,-18,24);cam.rotation_euler=(Vector((-6,-2,.2))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.view_settings.exposure+=.45
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
 for device in pref.devices:device.use=device.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
for t in [88,104,114]:
 scene.frame_set(1+t*30);scene.render.filepath=str(P/'preview'/('scene_%03d.png'%t));bpy.ops.render.render(write_still=True)
scene.frame_set(3421);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'LuoboTurn024388_AnimatedPreview.blend'));print('Saved 37 animated targets and optional box-truck FBX')
