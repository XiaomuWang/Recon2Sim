"""Run inside CARLA Unreal Editor on a NEW BaseMap-derived level named SCENE map_name.

Set A2S_OUTPUT to the scene output directory before exec(open(...).read()).
Imports actual FBX geometry/materials, uses Unreal centimeters internally, and writes
a hash receipt. CARLA map packaging/cooking still follows the installed CARLA build.
"""
import hashlib
import json
import shutil
from pathlib import Path
import unreal

out=Path(globals()['A2S_OUTPUT']).resolve()
cfg=json.loads((out/'scene_config.json').read_text(encoding='utf-8'));name=cfg['map_name'];folder=out/'map'
world=unreal.EditorLevelLibrary.get_editor_world()
if world.get_name()!=name: raise RuntimeError('Open a new BaseMap-derived level named '+name+' before importing')
destination='/Game/Accident2Sim/'+name+'/Assets'
if unreal.EditorAssetLibrary.does_directory_exist(destination): raise RuntimeError('Destination already exists; use the saved imported map')
task=unreal.AssetImportTask();task.filename=str(folder/(name+'.fbx'));task.destination_path=destination
task.automated=True;task.replace_existing=False;task.save=True
ui=unreal.FbxImportUI();ui.import_mesh=True;ui.import_as_skeletal=False;ui.import_materials=True;ui.import_textures=True
ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
d=ui.static_mesh_import_data;d.combine_meshes=False;d.auto_generate_collision=False;d.convert_scene=True;d.convert_scene_unit=True
d.force_front_x_axis=False;d.transform_vertex_to_absolute=True;d.generate_lightmap_u_vs=True
d.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS;task.options=ui
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);mesh_count=0;material_count=0
for path in task.imported_object_paths:
    asset=unreal.EditorAssetLibrary.load_asset(path)
    if isinstance(asset,unreal.StaticMesh):
        body=asset.get_editor_property('body_setup')
        if body:body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        actor=unreal.EditorLevelLibrary.spawn_actor_from_object(asset,unreal.Vector(0,0,0),unreal.Rotator(0,0,0))
        actor.set_actor_label(asset.get_name());actor.set_folder_path('Accident2SimEnvironment');mesh_count+=1
        unreal.EditorAssetLibrary.save_loaded_asset(asset)
    elif isinstance(asset,unreal.Material):
        asset.set_editor_property('two_sided',True);unreal.EditorAssetLibrary.save_loaded_asset(asset);material_count+=1
if mesh_count==0:raise RuntimeError('FBX import produced no static meshes; inspect Unreal import log')
target=Path(unreal.Paths.project_content_dir())/'Carla/Maps/OpenDrive'/(name+'.xodr')
target.parent.mkdir(parents=True,exist_ok=True)
if target.exists() and target.read_bytes()!=(folder/(name+'.xodr')).read_bytes():
    raise RuntimeError('Different XODR already exists at '+str(target))
shutil.copy2(folder/(name+'.xodr'),target)
unreal.EditorLevelLibrary.save_current_level()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=dict(map_name=name,mesh_count=mesh_count,material_count=material_count,
             fbx_sha256=sha(folder/(name+'.fbx')),xodr_sha256=sha(folder/(name+'.xodr')),
             imported_level=world.get_path_name(),runtime_verified=False,
             next_step='Configure CARLA GameMode/OpenDRIVE actor for this build, cook/package map, then run a2s.replay --mode imported')
(out/'validation/unreal_import_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
unreal.log('Imported Recon2Sim assets. Cook/package the map and validate using the replay client.')
