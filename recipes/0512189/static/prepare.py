from pathlib import Path
import shutil
p=Path('environment_reconstruction_0512189');old=Path('environment_reconstruction_014346');src=Path('environment_reconstruction_019742/scripts')
for n in ['concrete','road','asphalt','hoarding','paving','soil','bark']:
 for suf in ['basecolor','roughness','normal']:shutil.copy2(old/'textures'/f'{n}_{suf}.png',p/'textures'/f'{n}_{suf}.png')
shutil.copytree(old/'validation/schema',p/'validation/schema',dirs_exist_ok=True)
s=(src/'scene_lib.py').read_text(encoding='utf-8-sig').replace('UrbanBrake019742','MeituanLane0512189').replace('random.seed(19742)','random.seed(512189)')
(p/'scripts/scene_lib.py').write_text(s,encoding='utf-8')
s=(src/'build_scene.py').read_text(encoding='utf-8-sig')
asset='from scene_lib import *\n'+s[s.index("material('MintTile'"):s.index('def graphic')]+s[s.index('def frontface'):s.index("print('Roads")]+s[s.index('def building'):s.index('# Distinctive blocks')]+s[s.index('tree_protos=[]'):s.index("wells=Mesh")]
asset=asset.replace('range(540)','range(350)')
(p/'scripts/asset_lib.py').write_text(asset,encoding='utf-8')
for file in ['unreal_import_environment.py','validate_fbx.py']:
 s=(src/file).read_text(encoding='utf-8-sig').replace('UrbanBrake019742','MeituanLane0512189').replace('environment_reconstruction_019742','environment_reconstruction_0512189').replace('URBAN_SOURCE_DIR','MEITUAN_SOURCE_DIR').replace('UrbanEnvironment','MeituanEnvironment')
 (p/'scripts'/file).write_text(s,encoding='utf-8')
