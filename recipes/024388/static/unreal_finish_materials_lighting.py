"""Optional UE4.27 editor template. Syntax checked, not executed in Unreal.
Run after unreal_import_environment.py in the same Python scope, or set LUOBO_SOURCE_DIR.
Creates dedicated materials and local lights, leaving world/sky/exposure settings to CARLA.
"""
import json
from pathlib import Path
import unreal
SOURCE=Path(globals().get('LUOBO_SOURCE_DIR',r'C:/Users/Administrator/Desktop/accident_data_20260908/environment_reconstruction_024388'))
NAME='LuoboTurn024388';DEST='/Game/'+NAME+'/PBR'
if unreal.EditorAssetLibrary.does_directory_exist(DEST):raise RuntimeError('PBR assets already exist. Reuse them or choose another DEST before rerunning.')
mel=unreal.MaterialEditingLibrary;at=unreal.AssetToolsHelpers.get_asset_tools();mats={};textures={}
material_data=json.loads((SOURCE/'materials.json').read_text())
filenames=sorted({f for m in material_data for f in m['textures'].values()})
tasks=[]
for f in filenames:
 t=unreal.AssetImportTask();t.filename=str(SOURCE/'textures'/f);t.destination_path=DEST+'/Textures';t.automated=True;t.replace_existing=False;t.save=True;tasks.append(t)
at.import_asset_tasks(tasks)
for f,t in zip(filenames,tasks):
 if not t.imported_object_paths:raise RuntimeError('Texture import failed: '+f)
 tx=unreal.EditorAssetLibrary.load_asset(t.imported_object_paths[0]);is_normal='_normal' in f;is_rough='_roughness' in f
 tx.set_editor_property('srgb',not (is_normal or is_rough))
 if is_normal:
  tx.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
  tx.set_editor_property('flip_green_channel',True) # Blender OpenGL +Y normal -> Unreal DirectX -Y normal.
 unreal.EditorAssetLibrary.save_loaded_asset(tx);textures[f]=tx
for dat in material_data:
 mat=at.create_asset('M_'+dat['name'],DEST,unreal.Material,unreal.MaterialFactoryNew());mats[dat['name']]=mat;mat.set_editor_property('two_sided',True)
 def constant(value,prop):
  if isinstance(value,list):
   n=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);n.set_editor_property('constant',unreal.LinearColor(*value,1))
  else:
   n=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);n.set_editor_property('r',float(value))
  mel.connect_material_property(n,'',prop)
 constant(dat['base_color'],unreal.MaterialProperty.MP_BASE_COLOR);constant(dat['roughness'],unreal.MaterialProperty.MP_ROUGHNESS);constant(dat['metallic'],unreal.MaterialProperty.MP_METALLIC)
 for slot,f in dat['textures'].items():
  n=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample);n.set_editor_property('texture',textures[f])
  if slot=='normal':n.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
  elif slot=='roughness':n.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
  prop={'basecolor':unreal.MaterialProperty.MP_BASE_COLOR,'roughness':unreal.MaterialProperty.MP_ROUGHNESS,'normal':unreal.MaterialProperty.MP_NORMAL}[slot]
  mel.connect_material_property(n,'R' if slot=='roughness' else 'RGB',prop)
 if 'emission' in dat:constant([c*dat['emission']['strength'] for c in dat['emission']['color']],unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
count=0
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
 if not actor.get_actor_label().startswith(NAME):continue
 comp=actor.get_component_by_class(unreal.StaticMeshComponent)
 if not comp:continue
 mesh=comp.get_editor_property('static_mesh')
 if not mesh:continue
 for i,slot in enumerate(mesh.get_editor_property('static_materials')):
  old=slot.get_editor_property('material_interface');slotname=str(slot.get_editor_property('material_slot_name'));oldname=old.get_name() if old else slotname
  found=next((m for key,m in mats.items() if oldname==key or slotname==key or oldname.endswith('_'+key)),None)
  if found:mesh.set_material(i,found);count+=1
 unreal.EditorAssetLibrary.save_loaded_asset(mesh)
def cm(p):return unreal.Vector(p[0]*100,-p[1]*100,p[2]*100)
existing={a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors()}
lights=json.loads((SOURCE/'lighting.json').read_text())['lights'];num=0
for dat in lights:
 label=NAME+'_Light_'+dat['name']
 if label in existing:continue
 is_area=dat['type']=='AREA';cls=unreal.RectLight if is_area else unreal.PointLight;loc=cm(dat['xyz_m']);rot=unreal.Rotator(0,0,0)
 if is_area:rot=unreal.MathLibrary.find_look_at_rotation(loc,cm(dat['target_m']))
 actor=unreal.EditorLevelLibrary.spawn_actor_from_class(cls,loc,rot);actor.set_actor_label(label);actor.set_folder_path('LuoboEnvironment/Lighting')
 comp=actor.get_component_by_class(unreal.RectLightComponent if is_area else unreal.PointLightComponent);comp.set_mobility(unreal.ComponentMobility.MOVABLE)
 comp.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);comp.set_editor_property('intensity',dat['energy_w']*15)
 comp.set_light_color(unreal.LinearColor(*dat['color'],1));comp.set_editor_property('attenuation_radius',1800.)
 if is_area:
  comp.set_editor_property('source_width',dat['size_m']*100);comp.set_editor_property('source_height',dat['size_m']*100)
 else:comp.set_editor_property('source_radius',dat['radius_m']*100)
 num+=1
unreal.log('Assigned {} material slots; added {} local lights. Artistic light conversion only; tune exposure and CARLA sky/weather before final use. Save the level explicitly.'.format(count,num))
