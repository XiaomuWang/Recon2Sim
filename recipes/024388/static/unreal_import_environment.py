"""Optional Unreal Editor Python import helper (UE4.26/4.27 API; not executed here).
Open a new empty level named LuoboTurn024388, then run from Unreal Python:
exec(open(r'C:/.../scripts/unreal_import_environment.py', encoding='utf-8').read())
Set SOURCE_DIR below first when using exec. Enable Python Editor Script Plugin.
Imports only; does not overwrite an existing level or package/cook a map.
"""
import os,json,shutil
from pathlib import Path
import unreal
SOURCE_DIR=Path(globals().get('LUOBO_SOURCE_DIR',r'C:/Users/Administrator/Desktop/accident_data_20260908/environment_reconstruction_024388'))
NAME='LuoboTurn024388';DEST='/Game/LuoboTurn024388/Assets'
if not (SOURCE_DIR/(NAME+'.fbx')).is_file():raise RuntimeError('Set LUOBO_SOURCE_DIR or SOURCE_DIR to the extracted asset folder.')
if unreal.EditorAssetLibrary.does_directory_exist(DEST):raise RuntimeError('Destination assets already exist. Use the existing import or explicitly choose a new DEST; this helper avoids replacing assets.')
task=unreal.AssetImportTask();task.filename=str(SOURCE_DIR/(NAME+'.fbx'));task.destination_path=DEST;task.automated=True;task.replace_existing=False;task.save=True
ui=unreal.FbxImportUI();ui.import_mesh=True;ui.import_as_skeletal=False;ui.import_materials=True;ui.import_textures=True;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
d=ui.static_mesh_import_data;d.combine_meshes=False;d.auto_generate_collision=False;d.convert_scene=True;d.convert_scene_unit=True;d.force_front_x_axis=False;d.transform_vertex_to_absolute=True;d.generate_lightmap_u_vs=True;d.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
task.options=ui;unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
created=[];meshes=0;materials=0
for asset_path in task.imported_object_paths:
 asset=unreal.EditorAssetLibrary.load_asset(asset_path)
 if isinstance(asset,unreal.StaticMesh):
  label=asset.get_name();category='Other'
  for token,cat in [('Road_Road','Road'),('Road_Marking','RoadLines'),('Road_Sidewalk','SideWalk'),('_Vegetation_','Vegetation'),('_Building_','Building'),('_Wall_','Wall'),('_Fence_','Fence'),('_Terrain_','Terrain')]:
   if token in label:category=cat;break
  target='/Game/Carla/Static/'+category+'/'+NAME+'/'+label
  unreal.EditorAssetLibrary.make_directory(target.rsplit('/',1)[0])
  if unreal.EditorAssetLibrary.rename_asset(asset.get_path_name(),target):asset=unreal.EditorAssetLibrary.load_asset(target)
  if category in ['Road','SideWalk','Wall','Fence','Building','Terrain'] or any(t in label for t in ['Bollards_Street_Furniture','Hotel_Corner_Planters']):
   bs=asset.get_editor_property('body_setup')
   if bs:bs.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  actor=unreal.EditorLevelLibrary.spawn_actor_from_object(asset,unreal.Vector(0,0,0),unreal.Rotator(0,0,0));actor.set_actor_label(label);actor.set_folder_path('LuoboEnvironment/'+category)
  created.append(label);unreal.EditorAssetLibrary.save_loaded_asset(asset);meshes+=1
 elif isinstance(asset,unreal.Material):
  # W-beams, leaves and hoarding use thin surfaces. FBX lacks an agreed two-sided flag.
  asset.set_editor_property('two_sided',True);unreal.EditorAssetLibrary.save_loaded_asset(asset);materials+=1
content=Path(unreal.Paths.project_content_dir());od=content/'Carla/Maps/OpenDrive';od.mkdir(parents=True,exist_ok=True)
target=od/(NAME+'.xodr')
if not target.exists():shutil.copy2(SOURCE_DIR/(NAME+'.xodr'),target)
unreal.log('Imported {} meshes and {} materials. Add CARLA BaseMap lighting; save level as LuoboTurn024388; attach the OpenDRIVE actor for your CARLA version. Check waypoint overlay before cooking.'.format(meshes,materials))
