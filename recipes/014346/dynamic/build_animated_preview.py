"""Inspectable Blender animation using the delivered environment; NOT CARLA footage."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];STATIC=P.parent/'environment_reconstruction_014346';data=json.loads((P/'scenario.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(STATIC/'NanshanGate014346.blend'))
scene=bpy.context.scene;coll=bpy.data.collections.new('Dynamic_Replay');scene.collection.children.link(coll)
with bpy.data.libraries.load(str(P/'assets/NanshanDynamicAssets.blend'),link=False) as (src,dst):dst.objects=['NanshanDumpTruck','NanshanCargoTrike']
truck,trike=dst.objects;protos={'truck':truck,'gate_truck':truck,'tricycle':trike}
def mat(n,col):
 m=bpy.data.materials.new(n);m.diffuse_color=(*col,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*col,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.5;return m
white=mat('D_White',(.72,.75,.72));silver=mat('D_Silver',(.4,.51,.5));glass=mat('D_Glass',(.025,.06,.08));rubber=mat('D_Rubber',(.025,.025,.024));orange=mat('D_Orange',(.88,.2,.02));gray=mat('D_Gray',(.43,.42,.35));skin=mat('D_Skin',(.48,.28,.16));blue=mat('D_Blue',(.03,.07,.19))
parts=[]
def cube(c,d,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);parts.append(o);return o
def cylinder(c,r,l,m,rot=0):
 bpy.ops.mesh.primitive_cylinder_add(vertices=14,radius=r,depth=l,location=c);o=bpy.context.object;o.rotation_euler.x=rot;o.data.materials.append(m);parts.append(o)
def join(n):
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=n;bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');parts.clear();return o
def car(n,paint):
 cube((0,0,.6),(4.65,1.86,.62),paint);cube((-.3,0,1.1),(2.65,1.68,.61),glass);cube((-.3,0,1.44),(2.7,1.72,.1),paint)
 for x in [-1.5,1.4]:
  for y in [-.9,.9]:cylinder((x,y,.35),.35,.22,rubber,math.pi/2)
 return join(n)
carwhite=car('Preview_Ego_Proxy',white);carsilver=car('Preview_Sedan_Proxy',silver)
def human(n,cloth):
 for y in [-.13,.13]:cylinder((0,y,.43),.07,.72,rubber)
 cube((0,0,1.09),(.31,.45,.62),cloth)
 for y in [-.28,.28]:cylinder((0,y,1.01),.065,.53,cloth)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.14,location=(0,0,1.58));o=bpy.context.object;o.data.materials.append(skin);parts.append(o);return join(n)
h1=human('Preview_OrangeWorker_Proxy',orange);h2=human('Preview_GrayWorker_Proxy',gray)
cube((0,0,.58),(1.5,.45,.48),blue);cube((-.3,0,.92),(.65,.45,.1),rubber)
for x in [-.65,.65]:cylinder((x,0,.3),.3,.14,rubber,math.pi/2)
scoot=join('Preview_Scooter_Proxy')
protos.update({'car':carwhite,'motorcycle':scoot,'parked':scoot,'pedestrian':h1})
for a in data['actors']:
 proto=protos[a['category']]
 if a['id']=='silver_sedan':proto=carsilver
 if a['id']=='worker_gray':proto=h2
 o=proto.copy();o.data=proto.data;o.name='Replay_'+a['id'];coll.objects.link(o)
 # Scale proxies to the same conservative envelope used by offline clearance checks.
 vs=[Vector(v) for v in o.bound_box];lo=Vector([min(v[i] for v in vs) for i in range(3)]);hi=Vector([max(v[i] for v in vs) for i in range(3)]);dim=hi-lo;desired=Vector([a['dimensions_m'][k] for k in ['length','width','height']]);o.scale=[desired[i]/max(dim[i],.01) for i in range(3)];cen=(lo+hi)/2
 centre=Vector([cen[i]*o.scale[i] for i in range(3)]);bottom=lo.z*o.scale.z
 ss=a['samples'][::6]
 if ss[-1]!=a['samples'][-1]:ss.append(a['samples'][-1])
 for s in ss:
  frame=1+s['t']*30;h=s['h'];o.location=(s['x']-centre.x*math.cos(h)+centre.y*math.sin(h),s['y']-centre.x*math.sin(h)-centre.y*math.cos(h),s['z']-bottom+.025);o.rotation_euler=(0,0,h);o.keyframe_insert('location',frame=frame);o.keyframe_insert('rotation_euler',frame=frame)
 start=1+a['start_t']*30;end=1+a['end_t']*30
 for fr,hide in [(0,True),(max(.01,start-.01),True),(start,False),(end,False),(end+.01,True)]:o.hide_render=hide;o.hide_viewport=hide;o.keyframe_insert('hide_render',frame=fr);o.keyframe_insert('hide_viewport',frame=fr)
 for fc in o.animation_data.action.fcurves:
  for kp in fc.keyframe_points:kp.interpolation='CONSTANT' if 'hide_' in fc.data_path else 'LINEAR'
 o['reconstruction']='video-referenced estimated kinematic trajectory';o['video_time_offset']=52
for o in [carwhite,carsilver,h1,h2,scoot]:bpy.data.objects.remove(o,do_unlink=True)
scene.frame_start=1;scene.frame_end=3211;scene.render.fps=30
cd=bpy.data.cameras.new('Dynamic_Aerial');cam=bpy.data.objects.new('Dynamic_Aerial',cd);scene.collection.objects.link(cam);cd.lens=36;scene.camera=cam
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.cycles.samples=32
for video_t,pos,target in [(68,(-18,-28,21),(0,0,1)),(84,(-14,-29,24),(3,0,1)),(140,(6,-38,28),(22,0,1))]:
 scene.frame_set(round((video_t-52)*30)+1);cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(P/'preview'/('scene_%03d.png'%video_t));bpy.ops.render.render(write_still=True)
scene.frame_set(481);cam.location=(-18,-28,21);cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'NanshanGate014346_AnimatedPreview.blend'))
print('Animated scene preview saved')
