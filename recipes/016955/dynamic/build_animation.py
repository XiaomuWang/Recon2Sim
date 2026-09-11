"""Blender preview of video-estimated motion on the delivered static environment."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];STATIC=P.parent/'environment_reconstruction_016955';d=json.loads((P/'scenario.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(STATIC/'GreenRail016955.blend'));scene=bpy.context.scene
coll=bpy.data.collections.new('Video_Dynamics_016955');scene.collection.children.link(coll)
with bpy.data.libraries.load(str(P/'assets/GreenRailDynamicAssets.blend'),link=False) as (src,dst):dst.objects=src.objects
protos={o.name:o for o in dst.objects};protos_by_cat={'car':'preview_car','van':'greenrail_boxtruck','truck':'greenrail_boxtruck','bus':'greenrail_coach','sweeper':'greenrail_sweeper','motorcycle':'preview_scooter','pedestrian':'preview_pedestrian'}
for a in d['actors']:
 key='greenrail_container' if a['id']=='container_truck' else protos_by_cat[a['category']];proto=protos[key];o=proto.copy();o.data=proto.data.copy();o.name='Replay_'+a['id'];coll.objects.link(o)
 if a.get('color') and a['category'] not in ['sweeper','bus']:
  m=bpy.data.materials.new('Paint_'+a['id']);rgb=[(int(c)/255)**2.2 for c in a['color'].split(',')];m.diffuse_color=(*rgb,1);m.use_nodes=True;bs=m.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Metallic'].default_value=.25;bs.inputs['Roughness'].default_value=.42
  for i,ma in enumerate(o.data.materials):
   if ma.name.startswith('White'):o.data.materials[i]=m
 lo=[min(v.co[i] for v in o.data.vertices) for i in range(3)];hi=[max(v.co[i] for v in o.data.vertices) for i in range(3)]
 o.scale=[a['dimensions_m'][k]/(hi[i]-lo[i]) for i,k in enumerate(['length','width','height'])]
 ss=a['samples'][::3]
 if ss[-1]!=a['samples'][-1]:ss.append(a['samples'][-1])
 for s in ss:
  fr=1+s['t']*30;o.location=(s['x'],s['y'],s['z']+.025);o.rotation_euler=(0,0,s['h']);o.keyframe_insert('location',frame=fr);o.keyframe_insert('rotation_euler',frame=fr)
 start=1+a['start_t']*30;end=1+a['end_t']*30
 for fr,hide in [(0,True),(max(.01,start-.01),True),(start,False),(end,False),(end+.01,True)]:o.hide_render=hide;o.hide_viewport=hide;o.keyframe_insert('hide_render',frame=fr);o.keyframe_insert('hide_viewport',frame=fr)
 for fc in o.animation_data.action.fcurves:
  for kp in fc.keyframe_points:kp.interpolation='CONSTANT' if 'hide_' in fc.data_path else 'LINEAR'
 o['source_id']=a['id'];o['note']=a['notes'];o['source_video_start']=a['start_t']
for o in protos.values():bpy.data.objects.remove(o,do_unlink=True)
scene.frame_start=1;scene.frame_end=5401;scene.render.fps=30
cd=bpy.data.cameras.new('DynamicPreviewCamera');cam=bpy.data.objects.new('DynamicPreviewCamera',cd);scene.collection.objects.link(cam);scene.camera=cam;cd.lens=33;cd.clip_end=1500
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='CUDA';prefs.get_devices()
 for dev in prefs.devices:dev.use=dev.type=='CUDA'
 scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=1440;scene.render.resolution_y=900;scene.render.resolution_percentage=100
shots=[(51,(-147,-142,24),(-171,-119,1),'01_coach_overtake'),(74,(-144,-36,25),(-166,-6,1),'02_first_right'),(102,(-25,-22,15),(-41,0,1),'03_boxtruck_pass'),(120,(-14,-24,13),(-1.8,-10,1),'04_robot_wait'),(156,(15,-32,18),(0,-12,1),'05_robot_cross'),(169,(-16,-116,20),(0,-93,1),'06_exit_pass')]
for t,pos,target,n in shots:
 scene.frame_set(1+t*30);cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(P/'preview'/(n+'.png'));bpy.ops.render.render(write_still=True)
# Approximate right camera during the prolonged stop, for direct comparison to the video.
scene.frame_set(3601);ego=d['actors'][0]['samples'][3600];h=ego['h'];cam.location=(ego['x']+math.sin(h)*.98,ego['y']-math.cos(h)*.98,1.45);target=cam.location+Vector((math.cos(h-math.pi/2),math.sin(h-math.pi/2),-.05));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=18;scene.render.filepath=str(P/'preview/07_robot_right_camera.png');bpy.ops.render.render(write_still=True)
scene.frame_set(3601);cam.location=(-14,-24,13);cam.rotation_euler=(Vector((-1.8,-10,1))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=33
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'GreenRail016955_AnimatedPreview.blend'));print('Animation saved')
