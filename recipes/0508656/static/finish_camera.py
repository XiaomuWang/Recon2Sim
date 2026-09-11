import bpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];name='MeituanBrake0508656'
bpy.ops.wm.open_mainfile(filepath=str(P/(name+'.blend')))
o=bpy.data.objects['Junction_Aerial'];o.location=(-300,-61,150);o.rotation_euler=(Vector((-290,0,0))-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=35
scene=bpy.context.scene;scene.camera=o;scene.render.filepath=str(P/'renders/07_junction_aerial.png')
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for dev in prefs.devices:dev.use=dev.type=='OPTIX'
scene.cycles.device='GPU';bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects['Forward_Incident'];bpy.ops.wm.save_as_mainfile(filepath=str(P/(name+'.blend')))
