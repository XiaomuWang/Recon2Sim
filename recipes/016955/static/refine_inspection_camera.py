import bpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'GreenRail016955.blend'))
s=bpy.context.scene;c=bpy.data.objects['VIEW_05_Right_106s'];c.rotation_euler=(Vector((-36,-12,3.0))-c.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'GreenRail016955.blend'))
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
s.camera=c;s.render.filepath=str(P/'renders/05_approach_right.png');bpy.ops.render.render(write_still=True)
