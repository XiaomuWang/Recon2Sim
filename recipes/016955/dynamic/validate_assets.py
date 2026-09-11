import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];expected={'greenrail_coach':(11.8,2.5,3.65),'greenrail_sweeper':(1.65,1.18,1.85),'greenrail_boxtruck':(7.2,2.45,3.35),'greenrail_container':(15.2,2.5,4.)};rows=[]
for name,dims in expected.items():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.fbx(filepath=str(P/'assets'/(name+'.fbx')))
 verts=[o.matrix_world@v.co for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices];lo=[min(v[i] for v in verts) for i in range(3)];hi=[max(v[i] for v in verts) for i in range(3)];actual=[hi[i]-lo[i] for i in range(3)]
 assert max(abs(a-b) for a,b in zip(actual,dims))<.001,(name,actual)
 assert abs(lo[2])<.001;assert abs(lo[0]+hi[0])<.001 and abs(lo[1]+hi[1])<.001
 rows.append(dict(file=name+'.fbx',dimensions_m=actual,ground_centre_origin_pass=True,vertices=len(verts)))
(P/'validation/asset_fbx_roundtrip.json').write_text(json.dumps(dict(pass_all=True,files=rows,scope='Blender FBX roundtrip, not Unreal import or cooked asset validation'),indent=2))
print('All four FBX props passed metric/origin roundtrip')
