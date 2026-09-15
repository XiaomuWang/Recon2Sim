"""Coordinate checks for estimated rolled actors; no server required."""
import unittest
import a2s
import carla
from a2s.replay import ground_transform
from a2s.common import interpolate

class RolledActorTests(unittest.TestCase):
    def test_rolled_bbox_stays_on_ground_at_requested_center(self):
        class Actor:
            bounding_box=carla.BoundingBox(carla.Location(x=.3,y=.2,z=.7),carla.Vector3D(x=1,y=.3,z=.7))
        for roll in [20,88,90]:
            pose=dict(x=12,y=-4,z=0,yaw_carla_deg=90,roll_carla_deg=roll)
            transform=ground_transform(Actor(),pose)
            center=transform.transform(carla.Location(x=.3,y=.2,z=.7))
            vertices=Actor.bounding_box.get_world_vertices(transform)
            self.assertAlmostEqual(center.x,12,places=4)
            self.assertAlmostEqual(center.y,-4,places=4)
            self.assertAlmostEqual(min(v.z for v in vertices),.02,places=4)
            self.assertAlmostEqual(transform.rotation.roll,roll,places=4)
    def test_roll_interpolation_preserves_existing_yaw_contract(self):
        a=dict(replay_time_s=0,x=0,y=0,z=0,speed=0,yaw_carla_deg=179,roll_carla_deg=0)
        b=dict(a,replay_time_s=1,yaw_carla_deg=-179,roll_carla_deg=88)
        result=interpolate([a,b],.5)
        self.assertEqual(result['roll_carla_deg'],44)
        self.assertEqual(result['yaw_carla_deg'],-180)

if __name__=='__main__':unittest.main()
