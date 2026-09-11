from pathlib import Path
import shutil
P=Path(__file__).resolve().parents[1];old=P.parent/'environment_reconstruction_014346'
for d in ['textures','renders','validation','scripts','evidence']:(P/d).mkdir(exist_ok=True)
s=(old/'scripts/build_scene.py').read_text(encoding='utf-8-sig')
lib=s[:s.index("print('Building road and architecture")]
lib=lib.replace('from road_layout import pose,LENGTH,WIDTH','from road_layout import *').replace('random.seed(14346)','random.seed(24388)').replace("NAME='NanshanGate014346'","NAME='LuoboTurn024388'")
(P/'scripts/scene_lib.py').write_text(lib,encoding='utf-8')
for n in ['concrete','road','asphalt','hoarding','paving','soil','bark']:
 for suf in ['basecolor','roughness','normal']:shutil.copy2(old/'textures'/f'{n}_{suf}.png',P/'textures'/f'{n}_{suf}.png')
shutil.copytree(old/'validation/schema',P/'validation/schema',dirs_exist_ok=True)
for filename in ['unreal_import_environment.py','carla_check_loaded_map.py','validate_fbx.py']:
 t=(old/'scripts'/filename).read_text(encoding='utf-8-sig').replace('NanshanGate014346','LuoboTurn024388').replace('environment_reconstruction_014346','environment_reconstruction_024388').replace('NANSHAN_SOURCE_DIR','LUOBO_SOURCE_DIR').replace('NanshanEnvironment','LuoboEnvironment')
 if filename=='carla_check_loaded_map.py':t=t.replace("[(10,-1,72,'approach'),(20,-1,10,'past_gate'),(30,-1,15,'inside_gate')]","[(10,-1,160,'approach'),(20,-1,10,'right_exit'),(30,-1,15,'left_branch')]")
 (P/'scripts'/filename).write_text(t,encoding='utf-8')
start=s.index('tree_protos=[]');end=s.index('for s in range(5,205,10):')
(P/'scripts/tree_lib.py').write_text('from scene_lib import *\n'+s[start:end],encoding='utf-8')
print('Prepared shared mesh/material tools and import/validation helpers.')
