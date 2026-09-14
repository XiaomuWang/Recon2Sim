import math
import unittest
from a2s.motion import reference, motion_kind, RiderFollower, walker_command


def path(points):
    return [dict(actor_id='target', replay_time_s=t, x=x, y=y, z=0,
                 speed=999, yaw_carla_deg=yaw) for t,x,y,yaw in points]


class MotionTests(unittest.TestCase):
    def test_wrongway_direction_uses_displacement(self):
        rows=path([(0,10,0,179),(1,8,0,-179),(2,6,0,179)])
        r=reference(rows,1)
        self.assertAlmostEqual(abs(r['motion_yaw']),180)
        self.assertAlmostEqual(r['motion_speed'],2)

    def test_stop_preserves_heading_and_stops_walker(self):
        rows=path([(0,1,2,70),(1,1,2,70)])
        self.assertEqual(reference(rows,.5)['motion_yaw'],70)
        self.assertEqual(walker_command(rows,.5,1,2)['speed'],0)
        self.assertIsNone(reference(rows,2))

    def test_semantic_substitutes_are_not_two_wheelers(self):
        for aid in ('sweeper','canopy_tricycle','access_cargo_trike'):
            self.assertTrue(motion_kind(dict(actor_id=aid,type='bicycle')).startswith('unsupported_'))

    def test_rider_turns_toward_path_without_throttle_brake_conflict(self):
        rows=path([(0,0,0,0),(1,4,1,14),(2,8,2,14)])
        cmd=RiderFollower().step(rows,.5,2,-1,0,4,.1)
        self.assertGreater(cmd['steer'],0)
        self.assertEqual(cmd['throttle']*cmd['brake'],0)

    def test_heading_wrap_does_not_reverse_steering(self):
        rows=path([(0,0,0,180),(1,-3,0,-180),(2,-6,0,180)])
        for yaw in (180,-180):
            cmd=RiderFollower().step(rows,1,-3,0,yaw,3,.1)
            self.assertAlmostEqual(cmd['steer'],0,places=6)

    def test_walker_catches_up_without_teleport(self):
        rows=path([(0,0,0,0),(2,2,0,0)])
        cmd=walker_command(rows,1,.5,0)
        self.assertEqual(cmd['dx'],1)
        self.assertGreater(cmd['speed'],1)
        self.assertLessEqual(cmd['speed'],3)


if __name__=='__main__': unittest.main()
