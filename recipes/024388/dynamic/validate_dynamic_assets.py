import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];path=P/'assets/LuoboBoxTruck.fbx'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(path));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==1;o=meshes[0]
bpy.context.view_layer.objects.active=o;o.select_set(True)
vs=[o.matrix_world@Vector(v) for v in o.bound_box];lo=Vector([min(v[i] for v in vs) for i in range(3)]);hi=Vector([max(v[i] for v in vs) for i in range(3)])
before=list(hi-lo)
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
dim=o.dimensions;o.scale=[v/dim[i] for i,v in enumerate([6.8,2.25,3.25])];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
vs=[Vector(v) for v in o.bound_box];lo=Vector([min(v[i] for v in vs) for i in range(3)]);hi=Vector([max(v[i] for v in vs) for i in range(3)]);offset=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
for v in o.data.vertices:v.co-=offset
o.location=(0,0,0);o.name='LuoboBoxTruck'
bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False,add_leaf_bones=False,path_mode='COPY',embed_textures=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(path));o=next(o for o in bpy.context.scene.objects if o.type=='MESH');dims=list(o.dimensions);assert all(abs(x-y)<.001 for x,y in zip(dims,[6.8,2.25,3.25]))
report=dict(file=path.name,fbx_reimport_pass=True,dimensions_m=dims,material_count=len(o.material_slots),mesh_count=1,forward_axis='+X in Blender reconstructed scene',origin='XY bbox centre at ground plane',carla_blueprint_registered=False)
(P/'validation/dynamic_asset_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
