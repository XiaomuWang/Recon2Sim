"""Build editable animation on the delivered environment; render illustrative stills."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));from replay_carla import interpolate
D=json.loads((P/'scenario.json').read_text(encoding='utf-8'));S=P.parent/'environment_reconstruction_0512189'
bpy.ops.wm.open_mainfile(filepath=str(S/'MeituanLane0512189.blend'))
scene=bpy.context.scene
for im in bpy.data.images:
 if im.source=='FILE':
  path=S/'textures'/Path(im.filepath).name
  if path.is_file():im.filepath=str(path);im.pack()
with bpy.data.libraries.load(str(P/'assets/MeituanDynamicAssets.blend'),link=False) as (a,b):b.objects=[n for n in a.objects if n.startswith('meituan_')]
protos={o.name:o for o in b.objects if o}
coll=bpy.data.collections.new('DYNAMIC / video seconds x30 +1');scene.collection.children.link(coll)
mats={}
def mat(n,c):
 if n not in mats:
  m=bpy.data.materials.new('Replay_'+n);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*c,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.38;mats[n]=m
 return mats[n]
glass=mat('dark glass',(.025,.055,.065));rubber=mat('rubber',(.018,.02,.023));steel=mat('steel',(.28,.3,.32));skin=mat('skin',(.51,.31,.19));white=mat('lamp',(.8,.83,.75));red=mat('taillamp',(.45,.02,.015));parts=[]
def box(loc,dim,ma,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma)
 if bevel:
  m=o.modifiers.new('Rounded edges','BEVEL');m.width=bevel;m.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
 parts.append(o);return o
def wheel(x,y,z,r):
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r,depth=.14,location=(x,y,z),rotation=(math.pi/2,0,0));o=bpy.context.object;o.data.materials.append(rubber);parts.append(o)
def person(ma,cy=0):
 box((0,cy,1.15),(.36,.46,.59),ma,.08);box((0,cy,1.6),(.27,.26,.28),skin,.09)
 for y in [-.13,.13]:box((0,cy+y,.52),(.15,.15,.70),glass,.045);box((.11,cy+y,.15),(.36,.17,.13),rubber,.04)
 for y in [-.32,.32]:box((0,cy+y,1.1),(.14,.14,.6),ma,.04)
def generic(a):
 dims=a['dimensions_m'];L,W,H=[dims[k] for k in ['length','width','height']];c=[int(n)/255 for n in (a.get('color') or '100,105,110').split(',')];body=mat(a['id'],c)
 if a['category']=='pedestrian':person(body)
 elif a['category'] in ['motorcycle','parked']:
  wheel(-.58,0,.25,.25);wheel(.6,0,.25,.25);box((-.13,0,.51),(1.2,.38,.23),body,.06);box((.50,0,.68),(.20,.38,.8),body,.04);box((-.25,0,.76),(.62,.36,.12),rubber,.04);box((.42,0,1.12),(.12,.62,.05),steel,.01)
  if a['id']!='parked_scooter':
   box((-.22,0,1.25),(.37,.5,.51),body,.08);box((-.17,0,1.63),(.28,.28,.3),white,.09)
 else:
  box((0,0,H*.34),(L*.96,W*.95,H*.39),body,.13);box((-.08*L,0,H*.71),(L*.54,W*.85,H*.42),body,.15);box((.18*L,0,H*.75),(.10,W*.76,H*.28),glass,.015)
  for y in [-1,1]:
   box((-.06*L,y*W*.428,H*.75),(L*.48,.025,H*.25),glass,.045)
   for x in [-L*.29,L*.3]:wheel(x,y*W*.46,H*.2,min(.39,H*.22))
   box((L*.485,y*W*.30,H*.34),(.035,W*.18,.13),white,.015);box((-L*.485,y*W*.30,H*.38),(.03,W*.15,.12),red,.01)
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;parts.clear();scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 pts=[v.co for v in o.data.vertices];lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
 for v in o.data.vertices:
  for i,dim in enumerate([L,W,H]):v.co[i]=(v.co[i]-(lo[i]+hi[i])/2 if i<2 else v.co[i]-lo[i])*dim/(hi[i]-lo[i])
 return o
actors={}
for a in D['actors']:
 key=(a.get('preferred_custom_blueprint') or '').split('.')[-1]
 if key in protos:o=protos[key].copy();o.data=protos[key].data.copy();coll.objects.link(o)
 else:
  o=generic(a)
  for c in list(o.users_collection):c.objects.unlink(o)
  coll.objects.link(o)
 o.name='track_'+a['id'];o.location=(0,0,0);o['label']=a['label_zh'];o['accuracy']='estimated from video; not calibrated ground truth';actors[a['id']]=o
 ss=a['samples'][::6]
 if ss[-1]!=a['samples'][-1]:ss.append(a['samples'][-1])
 for s in ss:
  f=round(s['t']*30)+1;o.location=(s['x'],s['y'],s['z']);o.rotation_euler=(0,0,s['h']);o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
 start=round(a['start_t']*30)+1;end=round(a['end_t']*30)+1
 for f,hidden in [(0,True),(start,False),(end+1,True)]:
  o.hide_render=hidden;o.hide_viewport=hidden;o.keyframe_insert('hide_render',frame=f);o.keyframe_insert('hide_viewport',frame=f)
 for fc in o.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='CONSTANT' if fc.data_path.startswith('hide') else 'LINEAR'
for o in protos.values():bpy.data.objects.remove(o,do_unlink=True)
scene.frame_start=1;scene.frame_end=3601;scene.render.fps=30
for t,label in [(0,'VIDEO START'),(46,'green van / box truck'),(81,'EGO START'),(85,'EGO RIGHT SHIFT'),(94,'TEAL BUS'),(103,'AD BUS'),(112,'PURPLE PEDESTRIAN')]:scene.timeline_markers.new(label,frame=t*30+1)
camdata=bpy.data.cameras.new('Dynamic review');cam=bpy.data.objects.new('Dynamic review',camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.lens=32
scene.render.resolution_x=1440;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.cycles.samples=24
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for device in prefs.devices:device.use=device.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception:pass
ego=next(a for a in D['actors'] if a['id']=='ego')
for t in [51,86,105,118]:
 scene.frame_set(t*30+1);s=interpolate(ego['samples'],t);x=s['x'];cam.location=(x-14,-4,24);target=Vector((x+12,-5,1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(P/'preview'/('scene_%03d.png'%t));bpy.ops.render.render(write_still=True)
scene.frame_set(105*30+1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'preview/MeituanLane0512189_Animated.blend'));print('ANIMATED PREVIEW COMPLETE',flush=True)


