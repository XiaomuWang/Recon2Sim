from pathlib import Path
p=Path('dynamic_replay_0512189/replay_carla.py');s=p.read_text(encoding='utf-8')
s=s.replace("    print('CARLA',server_version)","    if server_version.split('-')[0] not in data['target_carla_versions']:raise RuntimeError('This package targets CARLA 0.9.15; received '+server_version)\n    print('CARLA',server_version)")
s=s.replace("dt=1/data['fps'];wall_start=time.monotonic();camera_count={};report['frame_timeline']=[]", "dt=1/data['fps'];wall_start=time.monotonic();camera_count={};report['frame_timeline']=[]\n    report['expected_actor_ids']=[a['id'] for a in data['actors'] if a['end_t']>=args.start and a['start_t']<=end];report['actor_lifecycle']={}")
s=s.replace("owned[aid]=obj;started.add(aid);bbs[aid]", "report['actor_lifecycle'][aid]={'spawn_replay_t':round(t,6),'scheduled_start_t':a['start_t'],'blueprint':mapping[aid],'status':'spawned'}\n                    owned[aid]=obj;started.add(aid);bbs[aid]")
s=s.replace("owned[aid].destroy();finished.add(aid);continue", "owned[aid].destroy();finished.add(aid);report['actor_lifecycle'][aid].update(status='completed_track',exit_replay_t=round(t,6));continue")
s=s.replace("        report['runtime_verified']=True", "        missing=set(report['expected_actor_ids'])-started\n        if missing:raise RuntimeError('Scheduled actors did not spawn: '+str(sorted(missing)))\n        report['all_scheduled_actors_spawned']=True\n        report['runtime_verified']=True")
p.write_text(s,encoding='utf-8')
p=Path('dynamic_replay_0512189/scripts/test_replay_protocol.py');s=p.read_text(encoding='utf-8');s=s.replace(' def test_ground_centre_to_blueprint_pivot(self):',''' def test_full_clip_all_34_entities_spawn(self):
  w=World();self.assertEqual(self.run_fake(w,'--start','0','--end','120'),0)
  report=json.loads((P/'validation/protocol_run.json').read_text());self.assertEqual(len(report['actor_lifecycle']),34);self.assertTrue(report['all_scheduled_actors_spawned']);self.assertEqual(len(w.actors),34)
  self.assertAlmostEqual(report['actor_lifecycle']['bus_yellow_ad']['spawn_replay_t'],90,places=4)
  self.assertTrue(all(not a.alive for a in w.actors.values()))
 def test_spawn_failure_is_explicit_and_restores_settings(self):
  w=World();w.try_spawn_actor=lambda bp,t:None
  with self.assertRaisesRegex(RuntimeError,'Spawn failed for ego'):self.run_fake(w)
  report=json.loads((P/'validation/protocol_run.json').read_text());self.assertEqual(report['spawn_failures'],['ego']);self.assertFalse(w.settings.synchronous_mode)
 def test_ground_centre_to_blueprint_pivot(self):''');p.write_text(s,encoding='utf-8')
p=Path('dynamic_replay_0512189/scripts/validate_trajectories.py');s=p.read_text(encoding='utf-8').replace('assert not errors','assert not errors;assert not overlaps');p.write_text(s,encoding='utf-8')
