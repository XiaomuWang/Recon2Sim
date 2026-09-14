"""Controller/constraint tests using CARLA value types, without a server."""
import unittest
from types import SimpleNamespace
try:
    import carla
except ImportError:
    carla=None

if carla is not None:
    from a2s.motion_runtime import MotionRuntime


@unittest.skipIf(carla is None,'CARLA value types are optional in offline CI')
class RuntimeTests(unittest.TestCase):
    class Walker:
        type_id='walker.pedestrian.0001'
        def __init__(self,x=0):
            self.pose=carla.Transform(carla.Location(x=x,z=.9))
            self.bounding_box=carla.BoundingBox(carla.Location(),carla.Vector3D(.2,.2,.9))
            self.control=None
        def get_transform(self):return self.pose
        def get_velocity(self):return carla.Vector3D()
        def set_transform(self,tr):self.pose=tr
        def blend_pose(self,value):self.blend=value
        def apply_control(self,control):self.control=control
        def get_physics_control(self):raise AssertionError('Walker must not query vehicle physics')

    def runtime(self,points):
        rows=[dict(actor_id='p',replay_time_s=t,x=x,y=0,z=0,speed=0,yaw_carla_deg=0) for t,x in points]
        return MotionRuntime([dict(actor_id='p',type='pedestrian')],{'p':rows},1/30)

    def test_stationary_walker_has_zero_speed(self):
        r=self.runtime([(0,0),(1,0)]);a=self.Walker()
        r.initialize('p',a,0);r.control('p',a,.5)
        self.assertEqual(a.control.speed,0)
        self.assertEqual(r.states['p']['corrections'],0)

    def test_small_tracking_error_needs_no_position_tether(self):
        r=self.runtime([(0,.1),(1,.1)]);a=self.Walker()
        r.initialize('p',a,0);r.control('p',a,.5)
        self.assertEqual(a.pose.location.x,0)
        self.assertGreater(a.control.speed,0)
        self.assertEqual(r.states['p']['corrections'],0)

    def test_tether_is_bounded_and_explicitly_counted(self):
        r=self.runtime([(0,.6),(1,.6)]);a=self.Walker()
        r.initialize('p',a,0);r.control('p',a,.5)
        self.assertAlmostEqual(a.pose.location.x,.18,places=6)
        self.assertEqual(r.states['p']['corrections'],1)
        self.assertAlmostEqual(r.states['p']['max_correction_m'],.18)

    def test_large_input_discontinuity_is_not_hidden_in_metrics(self):
        r=self.runtime([(0,2),(1,2)]);a=self.Walker()
        r.initialize('p',a,0);r.control('p',a,.5)
        self.assertAlmostEqual(r.states['p']['max_correction_m'],1.8)
        self.assertFalse(r.summary()['free_collision_dynamics_validated'])

    def test_semantic_substitutes_stay_out_of_native_two_wheeler_path(self):
        entities=[dict(actor_id='sweeper',type='bicycle'),dict(actor_id='cargo_trike',type='motorbike')]
        r=MotionRuntime(entities,{},1/30)
        self.assertFalse(r.native('sweeper'));self.assertFalse(r.native('cargo_trike'))

    def test_recorded_exception_is_explicit_and_excluded_from_native_metrics(self):
        exceptions={'r':dict(mode='recorded',reason='Static geometry conflict')}
        r=MotionRuntime([dict(actor_id='r',type='motorbike')],{},1/30,overrides=exceptions)
        self.assertFalse(r.native('r'))
        self.assertEqual(r.summary()['recorded_exceptions'],exceptions)
        self.assertEqual(r.summary()['actors'],{})
        with self.assertRaises(ValueError):
            MotionRuntime([],{},1/30,overrides=exceptions)

    def test_high_speed_assistance_does_not_reset_at_each_gearbox_decrement(self):
        class Rider(self.Walker):
            type_id='vehicle.vespa.zx125'
            def get_velocity(self):return carla.Vector3D(x=10)
            def set_target_velocity(self,velocity):self.assisted=velocity.x
            def get_physics_control(self):
                return SimpleNamespace(wheels=[SimpleNamespace(position=carla.Vector3D(x=x),max_steer_angle=70) for x in (-65,65)])
        rows=[dict(actor_id='r',replay_time_s=t,x=15*t,y=0,z=0,speed=15,yaw_carla_deg=0) for t in (0,1,2)]
        runtime=MotionRuntime([dict(actor_id='r',type='motorbike')],{'r':rows},1/30)
        actor=Rider();runtime.initialize('r',actor,0)
        runtime.states['r']['reference_speed_command']=10
        for _ in range(30):runtime.control('r',actor,0)
        self.assertAlmostEqual(actor.assisted,14,places=4)
        self.assertEqual(runtime.states['r']['speed_assists'],30)


if __name__=='__main__':unittest.main()
