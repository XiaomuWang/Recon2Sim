from pathlib import Path
import shutil
p=Path('dynamic_replay_0512189');old=Path('dynamic_replay_014346')
for file in ['replay_carla.py','scripts/test_replay_protocol.py','validation/OpenSCENARIO.xsd']:
 s=(old/file).read_text(encoding='utf-8-sig').replace('NanshanGate014346','MeituanLane0512189').replace('0.9.15 / 0.9.16','0.9.15').replace('[(10,-1,50),(20,-1,10),(30,-1,15)]','[(10,-4,50),(20,-4,50),(30,-4,15)]')
 if file=='replay_carla.py':
  s=s.replace("('front',1.4,0,1.45,0,512,288),('rear',-1.7,0,1.5,180,640,360),('left',.2,-1.05,1.45,-90,640,360),('right',.2,1.05,1.45,90,640,360)","('front',1.4,0,1.5,0,1280,720),('rear',-1.5,0,1.5,180,960,768),('left',.2,-.9,1.45,-90,960,768),('right',.2,.9,1.45,90,960,768)")
 (p/file).write_text(s,encoding='utf-8')
shutil.copy2('environment_reconstruction_0512189/MeituanLane0512189.xodr',p/'MeituanLane0512189.xodr')
# Reuse standard-schema trajectory exporter as optional exchange format, independent of primary template.
s=(old/'scripts/export_xosc.py').read_text().replace('NanshanGate014346','MeituanLane0512189').replace('Observed_52_to_159_seconds','Observed_0_to_120_seconds')
(p/'scripts/export_xosc.py').write_text(s)
