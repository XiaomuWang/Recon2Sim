from pathlib import Path
import json
P=Path(__file__).resolve().parents[1]
p=P/'scripts/scene_lib.py';s=p.read_text(encoding='utf-8-sig').replace("NAME='UrbanBrake019742'","NAME='RainJunctionANA031'")
p.write_text(s,encoding='utf8')
p=P/'scripts/make_opendrive.py';s=p.read_text(encoding='utf-8-sig')
s=s.replace("north=100,south=-100,east=120,west=-420","north=110,south=-110,east=170,west=-180")
s=s.replace("max=30","max=40").replace("dat['n']==2","dat['id'] in [10,20]")
s=s.replace("Two main lanes per direction and one side-street lane per direction; widths, legal turn rules and 30 km/h provisional","Four main lanes and three cross-street lanes per direction are simulation estimates; hidden cross street, legal turns and 40 km/h are provisional")
a=s.index('moves=[');b=s.index('\nfor idx',a)
s=s[:a]+"moves=[('A','B',i,i) for i in range(4)]+[('B','A',i,i) for i in range(4)]+[('C','D',i,i) for i in range(3)]+[('D','C',i,i) for i in range(3)]+[('A','C',3,2),('A','D',0,0),('B','C',0,0),('B','D',3,2),('C','A',2,3),('C','B',0,0),('D','A',0,0),('D','B',2,3)]"+s[b:]
s=s.replace("'incident_reference_xyz':[0,-4.95,0]","'incident_reference_xyz':[0,-5.25,0]").replace("'right_panel_y_m':-6.95,",'').replace("'curb_y_abs_m':9.15","'curb_y_abs_m':14.85").replace("'facade_y_abs_m':14.5","'facade_y_abs_m':22.0").replace('14 connectors','22 connectors')
s=s.replace('E.indent(root,space=',"E.indent(root,space=") # Runtime is Python >=3.9 for XML indentation.
p.write_text(s,encoding='utf8')
for fn in ['validate_fbx.py','unreal_import_environment.py','carla_check_loaded_map.py']:
 p=P/'scripts'/fn;s=p.read_text(encoding='utf-8-sig').replace('NanshanGate014346','RainJunctionANA031').replace('NANSHAN_SOURCE_DIR','RAINJUNCTION_SOURCE_DIR').replace('environment_reconstruction_014346','environment_reconstruction_ANA031').replace('NanshanEnvironment','RainJunctionEnvironment')
 p.write_text(s,encoding='utf8')
