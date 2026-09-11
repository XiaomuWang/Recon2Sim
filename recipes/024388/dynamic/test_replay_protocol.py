"""Protocol tests with a fake CARLA world; real installed CARLA only parses XODR.
These tests are NOT simulator/runtime validation.
"""
import sys,copy,tempfile,unittest,types,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));import replay_carla
import carla as geometry
class BP:
 def __init__(self,n):self.id=n
 def has_attribute(self,n):return n=='role_name'
 def set_attribute(self,n,v):pass
class Actor:
 def __init__(self,i,t):self.id=i;self.t=t;self.alive=True;self.bounding_box=geometry.BoundingBox(geometry.Location(x=.1,z=.5),geometry.Vector3D(x=1,y=.4,z=.6))
 def destroy(self):self.alive=False;return True
 def get_location(self):return self.t.location
 def get_transform(self):return self.t
 def set_transform(self,t):self.t=t
 def set_simulate_physics(self,b):pass
class World:
 def __init__(self,fail=False,wrong=False):
  self.settings=types.SimpleNamespace(synchronous_mode=False,fixed_delta_seconds=None);self.actors={};self.counter=1;self.frame=0;self.fail=fail;self.applies=0;self.spectator=Actor(999,geometry.Transform());self.map=geometry.Map('Wrong' if wrong else 'LuoboTurn024388',(P/'LuoboTurn024388.xodr').read_text())
 def get_map(self):return self.map
 def get_blueprint_library(self):return types.SimpleNamespace(find=lambda n:BP(n))
 def get_settings(self):return copy.deepcopy(self.settings)
 def apply_settings(self,s):self.applies+=1;self.settings=copy.deepcopy(s)
 def get_spectator(self):return self.spectator
 def try_spawn_actor(self,bp,t):
  a=Actor(self.counter,t);self.counter+=1;self.actors[a.id]=a;return a
 def tick(self):
  self.frame+=1
  if self.fail and self.frame==2:raise RuntimeError('Injected tick failure')
  return self.frame
class Client:
 def __init__(self,w):self.w=w
 def set_timeout(self,t):pass
 def get_server_version(self):return '0.9.15'
 def get_client_version(self):return '0.9.15'
 def get_world(self):return self.w
 def apply_batch_sync(self,commands,tick):
  for aid,t in commands:self.w.actors[aid].t=t
  return [types.SimpleNamespace(has_error=lambda:False) for c in commands]
class Tests(unittest.TestCase):
 def run_fake(self,w,*args):
  fake=types.SimpleNamespace(Client=lambda h,p:Client(w),Map=geometry.Map,Location=geometry.Location,Rotation=geometry.Rotation,Transform=geometry.Transform,command=types.SimpleNamespace(ApplyTransform=lambda aid,t:(aid,t)))
  previous=sys.modules['carla'];sys.modules['carla']=fake
  try:return replay_carla.main(['--scene',str(P/'scenario.json'),'--start','47.9','--end','48.2','--fast','--report',str(P/'validation/protocol_run.json'),*args])
  finally:sys.modules['carla']=previous
 def test_success_restores_settings_and_destroys_owned_actors(self):
  w=World();self.assertEqual(self.run_fake(w),0);self.assertFalse(w.settings.synchronous_mode);self.assertIsNone(w.settings.fixed_delta_seconds);self.assertTrue(all(not a.alive for a in w.actors.values()));self.assertTrue(w.spectator.alive)
 def test_tick_failure_still_cleans_up(self):
  w=World(fail=True)
  with self.assertRaisesRegex(RuntimeError,'Injected'):self.run_fake(w)
  self.assertFalse(w.settings.synchronous_mode);self.assertTrue(all(not a.alive for a in w.actors.values()))
 def test_preflight_does_not_modify_world(self):
  w=World();self.run_fake(w,'--preflight');self.assertEqual(w.applies,0);self.assertEqual(len(w.actors),0)
 def test_wrong_map_rejected_before_modification(self):
  w=World(wrong=True)
  with self.assertRaisesRegex(RuntimeError,'Current map'):self.run_fake(w)
  self.assertEqual(w.applies,0);self.assertEqual(len(w.actors),0)
 def test_ground_centre_to_blueprint_pivot(self):
  s={'x':3,'y':4,'z':2,'h':1.5707963267948966};bb=geometry.BoundingBox(geometry.Location(x=.3,z=.6),geometry.Vector3D(x=2,y=1,z=.8));t=replay_carla.transform_for(geometry,s,bb)
  self.assertAlmostEqual(t.location.x,3,places=5);self.assertAlmostEqual(t.location.y,-3.7,places=5);self.assertAlmostEqual(t.location.z,2.225,places=5);self.assertAlmostEqual(t.rotation.yaw,-90,places=5)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));(P/'validation/protocol_tests.json').write_text(json.dumps({'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'pass':result.wasSuccessful(),'type':'fake-world protocol tests, NOT CARLA engine execution'},indent=2));raise SystemExit(0 if result.wasSuccessful() else 1)
