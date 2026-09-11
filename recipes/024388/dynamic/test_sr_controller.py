"""Uses official v0.9.15 BasicControl source + fake actors/clock. No CARLA engine."""
import importlib.util,json,sys,types,math,contextlib,io
from pathlib import Path
import carla
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
spec=importlib.util.spec_from_file_location('basic',P/'reference/sr015_basic_control.py');basic=importlib.util.module_from_spec(spec);spec.loader.exec_module(basic)
clock=types.SimpleNamespace(t=0.,get_time=lambda:clock.t)
sys.modules['srunner.scenariomanager.actorcontrols.basic_control']=types.SimpleNamespace(BasicControl=basic.BasicControl)
sys.modules['srunner.scenariomanager.timer']=types.SimpleNamespace(GameTime=clock)
import luobo_replay_control as replay
from replay_carla import interpolate,transform_for
class Actor:
 def __init__(self):self.bounding_box=carla.BoundingBox(carla.Location(x=.1,z=.5),carla.Vector3D(x=2,y=1,z=.7));self.t=carla.Transform(carla.Location(x=-500,y=500,z=5));self.physics=True
 def set_simulate_physics(self,v):self.physics=v
 def get_transform(self):return self.t
 def set_transform(self,v):self.t=v
d=json.loads((P/'scenario.json').read_text(encoding='utf-8'));checks=[]
with contextlib.redirect_stdout(io.StringIO()):
 ctrls=[replay.LuoboReplayControl(Actor(),dict(source_id=a['id'])) for a in d['actors']]
 clock.t=3.25;ctrls[0].update_target_speed(0)
 for a,c in zip(d['actors'],ctrls):
  clock.t=3.25+a['start_t']-.001;c.run_step()
  if a['id']!='ego':assert not c.visible
  clock.t=3.25+a['start_t']+.15;c.update_target_speed(0);c.run_step();assert c.visible and not c._actor.physics
  expected=transform_for(carla,interpolate(a['samples'],a['start_t']+.15),c.bb)
  assert c._actor.t.location.distance(expected.location)<1e-4
  clock.t=3.25+a['end_t']+.1;c.run_step();assert not c.visible and c._actor.t.location.z==-60
  checks.append(dict(actor=a['id'],late_activation_pass=True,pose_pass=True,expiry_pass=True))
 for c in ctrls:c.reset();c.reset()
 assert not replay._SESSIONS
report=dict(type='official BasicControl interface, fake actor and fake game clock; not engine execution',all_37_actors_pass=True,checks=checks)
(P/'validation/sr_controller_tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('PASS: 37 independent activations, delayed event evaluation, timestamp transforms, expiry and session reset')
