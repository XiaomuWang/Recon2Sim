import math
import unittest
from a2s.common import wrap,interpolate,PROJECT,IDS,read,tracks
from a2s.pipeline import entity_type
from a2s.routes import sample_route


class CoordinateTests(unittest.TestCase):
    def test_heading_wrap_and_shortest_arc(self):
        a=dict(replay_time_s=0,x=0,y=0,z=0,speed=0,yaw_carla_deg=179)
        b=dict(replay_time_s=1,x=10,y=2,z=0,speed=2,yaw_carla_deg=-179)
        p=interpolate([a,b],.5)
        self.assertEqual(p['x'],5);self.assertEqual(p['yaw_carla_deg'],-180)
        self.assertEqual(wrap(540),-180)

    def test_actor_lifecycle_no_extrapolation(self):
        row=dict(replay_time_s=2,x=0,y=0,z=0,speed=0,yaw_carla_deg=70)
        self.assertIsNone(interpolate([row],1.9));self.assertIsNone(interpolate([row],2.1))
        self.assertEqual(interpolate([row],2)['yaw_carla_deg'],70)

    def test_parked_actor_is_not_generic_car(self):
        self.assertEqual(entity_type(dict(category='parked',blueprint_candidates=['vehicle.vespa.zx125'])),'motorbike')
        self.assertEqual(entity_type(dict(category='motorcycle',blueprint_candidates=['vehicle.gazelle.omafiets'])),'bicycle')
        self.assertEqual(entity_type(dict(category='bus',blueprint_candidates=['vehicle.carlamotors.carlacola'])),'bus')


class ArtifactTests(unittest.TestCase):
    def test_all_scene_contracts_and_role_integrity(self):
        for sid in IDS:
            root=PROJECT/'outputs'/sid;cfg=read(root/'scene_config.json');entities=read(root/'entity_mapping.json');data=tracks(root/'trajectories.csv')
            self.assertEqual(len(data),len(entities['actors']));self.assertIn(entities['ego_actor_id'],data)
            self.assertTrue(all(a in data for a in entities['accident_actor_ids']))
            self.assertNotIn(entities['ego_actor_id'],entities['accident_actor_ids'])
            self.assertEqual(min(r['replay_time_s'] for rows in data.values() for r in rows),0)
            for aid,rows in data.items():
                self.assertTrue(all(b['replay_time_s']>a['replay_time_s'] for a,b in zip(rows,rows[1:])))
                self.assertTrue(all(-180<=r['yaw_carla_deg']<180 and r['speed']>=0 for r in rows))
                self.assertTrue(all(math.isfinite(r[k]) for r in rows for k in ['x','y','z','speed']))
            self.assertIn('friction_coefficient',cfg);self.assertIn('fog_visibility_distance_m',cfg)

    def test_bbox_ground_origin_conversion(self):
        import carla
        from a2s.replay import ground_transform
        class Actor:
            bounding_box=carla.BoundingBox(carla.Location(x=1,y=2,z=1),carla.Vector3D(x=2,y=1,z=.8))
        p=dict(x=10,y=20,z=3,yaw_carla_deg=90)
        t=ground_transform(Actor(),p)
        self.assertAlmostEqual(t.location.x,12,places=5);self.assertAlmostEqual(t.location.y,19,places=5)
        self.assertAlmostEqual(t.location.z,2.82,places=5)

    def test_generated_road_route_binding(self):
        root=PROJECT/'outputs/0512189';cfg=read(root/'scene_config.json')
        route=dict(sections=[dict(road_id=10,lane_id=-1,s_start=10,s_end=20)],time_station=[[0,0],[1,10]])
        points=sample_route(root/'map'/(cfg['map_name']+'.xodr'),route)
        self.assertEqual(len(points),31);self.assertAlmostEqual(points[-1]['x']-points[0]['x'],10,places=3)
        self.assertAlmostEqual(points[0]['h'],0,places=3)
        route['time_station']=[[0,0],[1,1000]]
        with self.assertRaises(ValueError):sample_route(root/'map'/(cfg['map_name']+'.xodr'),route)

    def test_native_mesh_names_do_not_trigger_legacy_filters(self):
        for sid in IDS:
            result=read(PROJECT/'outputs'/sid/'validation/fbx_import_names.json')
            self.assertTrue(result['geometry_and_all_non_name_bytes_identical'])
            self.assertEqual(result['mesh_count'],read(PROJECT/'outputs'/sid/'validation/fbx/fbx_validation.json')['mesh_count'])
            for name in result['mesh_names']:
                self.assertNotRegex(name.lower(),r'light|sign|_tile_',msg=sid+': '+name)

if __name__=='__main__':unittest.main()
