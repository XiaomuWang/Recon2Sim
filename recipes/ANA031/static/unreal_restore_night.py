"""Optional UE4.26/4.27 editor template. Run after FBX import. NOT runtime-tested.
Set RAINJUNCTION_SOURCE_DIR to extracted package folder. Creates lights in current level.
Does not control CARLA signal logic or weather. Review intensity in your UE version.
"""
from pathlib import Path
import json
import unreal
P=Path(globals().get('RAINJUNCTION_SOURCE_DIR',r'C:/Users/Administrator/Desktop/accident_data_20260908/environment_reconstruction_ANA031'))
data=json.loads((P/'lighting.json').read_text())
existing={a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors()}
for row in data['lights']:
 label='ANA031_Light_'+row['name']
 if label in existing:continue
 x,y,z=row['xyz_rh_m'];a=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight,unreal.Vector(x*100,-y*100,z*100),unreal.Rotator(0,0,0));a.set_actor_label(label);a.set_folder_path('RainJunctionEnvironment/NightLights')
 c=a.get_component_by_class(unreal.PointLightComponent);c.set_mobility(unreal.ComponentMobility.MOVABLE)
 c.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);c.set_intensity(row['unreal_intensity_lumens_estimate'])
 color=row['color_linear'];c.set_light_color(unreal.LinearColor(*color,1.0));c.set_editor_property('attenuation_radius',2800.0);c.set_editor_property('source_radius',row['source_radius_m']*100)
 # Area lamps intentionally approximated by point lights for the portable template.
for path in unreal.EditorAssetLibrary.list_assets('/Game/RainJunctionANA031/Assets',recursive=True,include_folder=False):
 asset=unreal.EditorAssetLibrary.load_asset(path)
 if not isinstance(asset,unreal.Material):continue
 name=asset.get_name()
 emissions={'LampWhite':(.90,.98,.77,7),'SignalRed':(1,.015,.008,9),'SignalGreen':(.015,1,.34,7),'WindowWarm':(.64,.47,.24,.65),'WindowCool':(.42,.60,.65,.45),'PanelLight':(.46,.68,.8,1.7)}
 match=next((v for k,v in emissions.items() if name==k or name.startswith(k+'_')),None)
 if match:
  node=unreal.MaterialEditingLibrary.create_material_expression(asset,unreal.MaterialExpressionConstant3Vector,-250,100)
  node.set_editor_property('constant',unreal.LinearColor(match[0]*match[3],match[1]*match[3],match[2]*match[3],1))
  unreal.MaterialEditingLibrary.connect_material_property(node,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 if name=='Asphalt' or name.startswith('Asphalt_'):
  node=unreal.MaterialEditingLibrary.create_material_expression(asset,unreal.MaterialExpressionConstant,-250,200);node.set_editor_property('r',.23);unreal.MaterialEditingLibrary.connect_material_property(node,'',unreal.MaterialProperty.MP_ROUGHNESS)
 unreal.MaterialEditingLibrary.recompile_material(asset);unreal.EditorAssetLibrary.save_loaded_asset(asset)
unreal.log('Night light estimates restored. Tune exposure and fog, set night sky, and configure CARLA functional traffic-light actors before simulation. Save the level manually.')
