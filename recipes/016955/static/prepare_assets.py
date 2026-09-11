from pathlib import Path
import shutil
P=Path(__file__).resolve().parents[1];old=P.parent/'environment_reconstruction_014346'
s=(old/'scripts/build_scene.py').read_text(encoding='utf-8')
lib=s[:s.index('def sp(')].replace('from road_layout import pose,LENGTH,WIDTH','').replace('NanshanGate014346','GreenRail016955').replace('random.seed(14346)','random.seed(16955)')
(P/'scripts/scene_lib.py').write_text(lib,encoding='utf-8')
trees=s[s.index('tree_protos=[]'):s.index('for s in range(5,205,10):')]
(P/'scripts/tree_lib.py').write_text('from scene_lib import *\n'+trees,encoding='utf-8')
for f in (old/'textures').glob('*.png'):
 if not f.name.startswith('slogan'):shutil.copy2(f,P/'textures'/f.name)
shutil.copytree(old/'validation/schema',P/'validation/schema',dirs_exist_ok=True)
for f in ['validate_fbx.py','unreal_import_environment.py']:
 txt=(old/'scripts'/f).read_text(encoding='utf-8').replace('NanshanGate014346','GreenRail016955').replace('environment_reconstruction_014346','environment_reconstruction_016955').replace('NANSHAN_SOURCE_DIR','GREENRAIL_SOURCE_DIR').replace('NanshanEnvironment','GreenRailEnvironment')
 (P/'scripts'/f).write_text(txt,encoding='utf-8')
print('Prepared reusable mesh utilities, texture assets, schema and import helper')
