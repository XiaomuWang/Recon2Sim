import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];rows=[]
for filename in ['nanshan_dumptruck.fbx','nanshan_cargotrike.fbx']:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(P/'assets'/filename))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
 points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
 lo=[min(v[i] for v in points) for i in range(3)];hi=[max(v[i] for v in points) for i in range(3)]
 dims=[hi[i]-lo[i] for i in range(3)]
 assert meshes and 2<dims[0]<10 and .8<dims[1]<4 and 1<dims[2]<5
 rows.append({'file':filename,'mesh_count':len(meshes),'dimensions_m':dims,'bbox_min_m':lo,'bbox_max_m':hi,'fbx_reimport_pass':True})
(P/'validation/asset_validation.json').write_text(json.dumps({'assets':rows,'note':'Blender FBX roundtrip only; Unreal materials/collision/import not runtime tested.'},indent=2))
print(rows)
