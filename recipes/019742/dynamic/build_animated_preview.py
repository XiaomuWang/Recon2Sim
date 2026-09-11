"""Editable Blender dynamic preview, environment and proxy actors. Not CARLA footage."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));from replay_carla import interpolate
data=json.loads((P/'scenario.json').read_text(encoding='utf-8'));bpy.ops.wm.open_mainfile(filepath=str(P.parent/'environment_reconstruction_019742/UrbanBrake019742.blend'));scene=bpy.context.scene
coll=bpy.data.collections.new('Dynamic_Replay');scene.collection.children.link(coll);parts=[]
def mat(n,col,rough=.4,metal=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*col,1);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
glass=mat('D_Glass',(.035,.07,.095),.2,.45);rubber=mat('D_Rubber',(.018,.021,.023),.8);chrome=mat('D_Chrome',(.45,.48,.49),.25,.8);skin=mat('D_Skin',(.55,.35,.24),.8);orange=mat('D_OrangeVest',(.92,.29,.025),.8);helmet=mat('D_Helmet',(.83,.82,.77),.4);white=mat('D_White',(.82,.82,.77),.55);red=mat('D_BrakeLens',(.58,.025,.02),.28)
def cube(c,d,m,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:
  mod=o.modifiers.new('Round_Edges','BEVEL');mod.width=bevel;mod.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 parts.append(o);return o
def cyl(c,r,depth,m,axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r,depth=depth,location=c);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 o.data.materials.append(m);parts.append(o);return o
def ball(c,scale,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=c);o=bpy.context.object;o.scale=scale;o.data.materials.append(m);parts.append(o)
def rod(a,b,r,m):
 a=Vector(a);b=Vector(b);o=cyl((a+b)/2,r,(b-a).length,m);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
def join(name):
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');parts.clear()
 for c in list(o.users_collection):c.objects.unlink(o)
 coll.objects.link(o);return o
def create_actor(a):
 kind=a['visual_type'];col=[float(x)/255 for x in (a.get('color') or '160,166,170').split(',')];paint=mat('D_Paint_'+a['id'],col,.32,.22)
 if kind in ['scooter','bicycle']:
  for xx in [-.68,.64]:cyl((xx,0,.26),.26,.13,rubber,'Y');cyl((xx,0,.26),.15,.15,chrome,'Y')
  cube((-.10,0,.42),(1.05,.31,.15),paint,.045);cube((-.28,0,.68),(.58,.37,.16),rubber,.04);cube((.45,0,.64),(.23,.38,.58),paint,.07)
  rod((.54,0,.46),(.36,0,1.03),.035,chrome);rod((.36,-.28,1.03),(.36,.28,1.03),.024,chrome)
  # Simple seated rider; vest and head are visible in all four views.
  cloth=orange if a['id']=='wrongway_orange_rider' else paint
  cube((-.22,0,1.03),(.30,.43,.49),cloth,.07)
  for sg in [-1,1]:
   rod((-.23,sg*.17,.83),(.16,sg*.20,.59),.08,rubber);rod((.16,sg*.20,.59),(.1,sg*.20,.39),.065,rubber)
   rod((-.13,sg*.25,1.18),(.35,sg*.25,1.01),.065,cloth)
  ball((-.20,0,1.43),(.135,.145,.17),skin);ball((-.22,0,1.52),(.16,.165,.125),helmet)
  if 'canopy' in a['id'] or 'trike' in a['id']:
   for xx in [-.66,.5]:
    for yy in [-.45,.45]:rod((xx,yy,.45),(xx,yy,1.72),.017,chrome)
   cube((-.08,0,1.77),(1.55,1.1,.10),paint,.07)
 elif kind in ['van','boxtruck','micro']:
  L,W,H=[a['dimensions_m'][k] for k in ['length','width','height']]
  cube((0,0,.65),(L*.96,W*.98,.72),paint,.12);cube((-.12,0,(H+1.0)/2),(L*.86,W*.91,H-1.0),paint,.10)
  cube((L*.43,0,H*.67),(.07,W*.83,H*.31),glass,.02)
  for sg in [-1,1]:
   if kind!='boxtruck':cube((-.06,sg*W*.458,H*.69),(L*.70,.025,H*.28),glass,.02)
   cube((L*.3,sg*W*.458,H*.69),(L*.17,.028,H*.28),glass,.02)
   for xx in [-L*.31,L*.31]:cyl((xx,sg*W*.46,.34),.34,.20,rubber,'Y');cyl((xx,sg*W*.48,.34),.21,.21,chrome,'Y')
  cube((-L*.482,0,.89),(.04,W*.87,.06),chrome)
  if a['id']=='parked_lead_white_van':
   cube((-L*.49,0,H*.75),(.025,W*.83,.11),red);cube((-L*.493,0,.57),(.025,.82,.22),mat('D_GreenPlate',(.09,.49,.30)))
 else:
  L,W,H=[a['dimensions_m'][k] for k in ['length','width','height']]
  cube((0,0,.57),(L,W,.63),paint,.15);cube((-.24,0,1.05),(L*.58,W*.90,H*.36),glass,.12);cube((-.24,0,H-.13),(L*.53,W*.89,.16),paint,.07)
  for xx in [-L*.31,L*.31]:
   for yy in [-W*.46,W*.46]:cyl((xx,yy,.32),.32,.23,rubber,'Y');cyl((xx,yy*1.02,.32),.21,.24,chrome,'Y')
  for yy in [-W*.35,W*.35]:cube((L*.494,yy,.72),(.035,W*.2,.13),white,.018);cube((-L*.494,yy,.72),(.035,W*.2,.13),red,.018)
  cube((L*.501,0,.5),(.025,W*.49,.17),glass)
  if a['id']=='blue_white_robotaxi':
   for yy in [-W*.503,W*.503]:cube((-.18,yy,.76),(L*.38,.027,.47),mat('D_TaxiBlue',(.10,.47,.77)))
   cyl((-.25,0,H+.08),.19,.17,glass);cube((-.4,0,H+.01),(1,.65,.08),chrome)
 o=join('Replay_'+a['id']);return o
for a in data['actors']:
 o=create_actor(a)
 # Normalize proxy envelope to the same estimated dimensions used by clearance checks.
 v=[Vector(q) for q in o.bound_box];lo=Vector([min(q[i] for q in v) for i in range(3)]);hi=Vector([max(q[i] for q in v) for i in range(3)]);dim=hi-lo;desired=Vector([a['dimensions_m'][k] for k in ['length','width','height']]);o.scale=[desired[i]/max(dim[i],.01) for i in range(3)];cen=(lo+hi)/2;center=Vector([cen[i]*o.scale[i] for i in range(3)]);bottom=lo.z*o.scale.z
 ss=a['samples'][::6]
 if ss[-1]!=a['samples'][-1]:ss.append(a['samples'][-1])
 for s in ss:
  f=1+s['t']*30;h=s['h'];o.location=(s['x']-center.x*math.cos(h)+center.y*math.sin(h),s['y']-center.x*math.sin(h)-center.y*math.cos(h),s['z']-bottom+.025);o.rotation_euler=(0,0,h);o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
 start=1+a['start_t']*30;end=1+a['end_t']*30
 for f,hide in [(0,True),(max(.01,start-.01),True),(start,False),(end,False),(end+.01,True)]:o.hide_render=hide;o.hide_viewport=hide;o.keyframe_insert('hide_render',frame=f);o.keyframe_insert('hide_viewport',frame=f)
 for fc in o.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='CONSTANT' if 'hide_' in fc.data_path else 'LINEAR'
 o['source']='four-view estimated dynamic proxy';o['not_carla_blueprint']=True
scene.frame_start=1;scene.frame_end=5341;scene.render.fps=30;scene.render.resolution_x=1400;scene.render.resolution_y=875;scene.cycles.samples=32
cd=bpy.data.cameras.new('Dynamic_Follow');cam=bpy.data.objects.new('Dynamic_Follow',cd);scene.collection.objects.link(cam);cd.lens=29;scene.camera=cam
for t in range(179):
 s=interpolate(data['actors'][0]['samples'],t);cam.location=(s['x']-11,s['y']-1,7.5);cam.rotation_euler=(Vector((s['x']+6,s['y'],.8))-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=1+t*30);cam.keyframe_insert('rotation_euler',frame=1+t*30)
for fc in cam.animation_data.action.fcurves:
 for k in fc.keyframe_points:k.interpolation='LINEAR'
for t in [73,110.5,113,167]:
 scene.frame_set(round(t*30)+1);scene.render.filepath=str(P/'preview'/('scene_%06.1f.png'%t));bpy.ops.render.render(write_still=True)
scene.frame_set(3316);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'UrbanBrake019742_AnimatedPreview.blend'))
(P/'validation/animation_validation.json').write_text(json.dumps({'actors':len(coll.objects),'frame_start':1,'frame_end':5341,'fps':30,'keyframes_hz':5,'packed_environment':True,'preview_only_not_carla':True},indent=2))
print('Saved dynamic preview')
