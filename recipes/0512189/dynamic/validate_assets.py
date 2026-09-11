import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];expected=json.loads((P/'assets/dimensions.json').read_text());rows=[]
for name,dim in expected.items():
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(P/'assets'/(name+'.fbx')))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box];lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)];actual=[hi[i]-lo[i] for i in range(3)]
 assert meshes and all(abs(x-y)<.005 for x,y in zip(actual,dim)),(name,actual,dim)
 assert abs(lo[2])<.005 and abs(hi[0]+lo[0])<.005 and abs(hi[1]+lo[1])<.005
 rows.append({'asset':name,'dimensions_m':actual,'expected_m':dim,'mesh_count':len(meshes),'fbx_roundtrip_pass':True})
(P/'validation/asset_validation.json').write_text(json.dumps({'assets':rows,'runtime_verified':False,'scope':'Blender FBX reimport and metric origin/dimension checks; Unreal import and material/collision setup not tested.'},indent=2));print('PASS',len(rows),'FBX assets')
