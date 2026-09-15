import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
out=Path(sys.argv[sys.argv.index('--')+1]);root=out/'map'
bpy.ops.wm.open_mainfile(filepath=str(root/'PonyFourView157116.blend'))
scene=bpy.context.scene;end=json.loads((root/'road_parameters.json').read_text())['incident_station_m'];folder=out/'validation/fisheye_static';folder.mkdir(exist_ok=True)
scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=480;scene.render.resolution_y=384;scene.render.resolution_percentage=100
for name,direction in [('front',(1,0,0)),('rear',(-1,0,0)),('left',(0,1,0)),('right',(0,-1,0))]:
 data=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,data);scene.collection.objects.link(cam);cam.location=(end,-1.75,1.7)
 cam.rotation_euler=Vector(direction).to_track_quat('-Z','Y').to_euler();data.type='PANO';data.panorama_type='FISHEYE_EQUIDISTANT';data.fisheye_fov=math.pi
 scene.camera=cam;scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
(folder/'camera_assumptions.json').write_text(json.dumps(dict(projection='equidistant fisheye',fov_deg=180,calibrated=False,scope='Qualitative static QA only; not the known input intrinsics',eye_rh_m=[end,-1.75,1.7]),indent=2))
