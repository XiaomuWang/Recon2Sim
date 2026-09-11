import bpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'LuoboTurn024388_AnimatedPreview.blend'));s=bpy.context.scene
s.camera.location=(-1,-15,17);s.camera.data.lens=31;s.camera.rotation_euler=(Vector((-7,0,.2))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.view_settings.exposure+=.45
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
 for device in pref.devices:device.use=device.type=='OPTIX'
 s.cycles.device='GPU'
except Exception:pass
for t in [88,104,114]:
 s.frame_set(1+t*30);s.render.filepath=str(P/'preview'/('scene_%03d.png'%t));bpy.ops.render.render(write_still=True)
s.frame_set(3421);bpy.ops.wm.save_as_mainfile(filepath=str(P/'LuoboTurn024388_AnimatedPreview.blend'))
