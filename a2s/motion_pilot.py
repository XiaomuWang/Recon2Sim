"""Isolated CARLA motion experiments. Never overwrites official replay captures.

Run using a matching CARLA 0.9.15 client; see scripts/run_motion_pilot.ps1.
"""
import argparse
import csv
import math
import queue
import time
import traceback
import carla
import cv2
import numpy as np
from .common import PROJECT, read, write, tracks, interpolate, sha, wrap
from .motion import RiderFollower, reference, walker_command, motion_kind
from .replay import ground_transform, receive_frame

PILOTS = {
    '0508656': dict(actor='red_rider', start=78., duration=8.),
    '019742': dict(actor='wrongway_orange_rider', start=107., duration=8.),
    '024388': dict(actor='cross_person_1', start=84., duration=6.5),
}


def bbox_center(actor, transform):
    return transform.transform(carla.Location(actor.bounding_box.location))


def camera_pose(pose, top=False, scene=None):
    a = math.radians(pose['yaw_carla_deg'])
    # Same reference-based camera path for both modes, not attached to actor.
    if top:
        return carla.Transform(carla.Location(x=pose['x'], y=pose['y'], z=pose['z']+18),
                               carla.Rotation(pitch=-89.9, yaw=pose['yaw_carla_deg']))
    back,lateral,height,pitch=(4,-2,4,-34) if scene=='019742' else (5,4,2.6,-15)
    x = pose['x']-back*math.cos(a)+lateral*math.sin(a)
    y = pose['y']-back*math.sin(a)-lateral*math.cos(a)
    yaw = math.degrees(math.atan2(pose['y']-y, pose['x']-x))
    return carla.Transform(carla.Location(x=x, y=y, z=pose['z']+height),
                           carla.Rotation(pitch=pitch, yaw=yaw))


def capture(sid, mode, duration=None, start=None, actor_id=None, hz=30, tag='v1', host='127.0.0.1', port=2000):
    spec = dict(PILOTS[sid]); spec.update({k: v for k, v in
        [('duration', duration), ('start', start), ('actor', actor_id)] if v is not None})
    root = PROJECT/'outputs'/sid
    cfg, mapping = read(root/'scene_config.json'), read(root/'entity_mapping.json')
    data = tracks(root/'trajectories.csv'); aid = spec['actor']
    entity = next(e for e in mapping['actors'] if e['actor_id'] == aid)
    kind = motion_kind(entity)
    if kind not in ('walker', 'two_wheeler'):
        raise ValueError('Unsupported physical actor: '+kind)
    start, duration = spec['start'], spec['duration']
    if interpolate(data[aid], start) is None or interpolate(data[aid], start+duration) is None:
        raise ValueError('Pilot must stay within target lifecycle')
    dest = root/'validation'/'motion_pilot'/tag/mode
    if (dest/'run.json').exists():
        raise FileExistsError('Use a new --tag to preserve earlier experiment: '+str(dest))
    dest.mkdir(parents=True, exist_ok=True)
    report = dict(scene_id=sid, target=aid, motion_kind=kind, mode=mode, hz=hz,
                  start=start, duration=duration, success=False, physical_collision_validated=False,
                  all_actor_dynamics=False, reference_sha256=sha(root/'trajectories.csv'),
                  target_teleports_after_initialization=0 if mode=='optimized' else int(duration*hz),
                  controller=('native WalkerControl' if kind=='walker' else 'VehicleControl pure pursuit / PI') if mode=='optimized' else 'recorded ApplyTransform',
                  acceptance=dict(position_p95_m=.5, position_max_m=1., yaw_p95_deg=10.))
    client = carla.Client(host, port); client.set_timeout(120)
    client.set_files_base_folder(str(PROJECT/'runtime/carla_cache'))
    sensors=[]; actors={}; settings=None; world=None; telemetry=[]; bones=[]
    try:
        report.update(client_version=client.get_client_version(), server_version=client.get_server_version())
        if report['client_version'] != '0.9.15' or report['server_version'] != '0.9.15':
            raise RuntimeError('Both CARLA client and server must be 0.9.15')
        receipt = read(root/'validation/unreal_import_receipt.json')
        for ext in ('fbx', 'xodr'):
            if sha(root/'map'/(cfg['map_name']+'.'+ext)) != receipt[ext+'_sha256']:
                raise RuntimeError('Map receipt hash mismatch')
        for item in receipt['files']:
            from pathlib import Path
            if sha(Path(receipt['installed_directory'])/item['path']) != item['sha256']:
                raise RuntimeError('Installed map changed: '+item['path'])
        world = client.load_world(receipt['unreal_map'])
        report['loaded_map'] = world.get_map().name
        settings = world.get_settings()
        sync = world.get_settings(); sync.synchronous_mode=True; sync.fixed_delta_seconds=1/hz
        sync.substepping=True; sync.max_substep_delta_time=.01; sync.max_substeps=10
        world.apply_settings(sync)
        weather = world.get_weather()
        for k,v in cfg['weather'].items(): setattr(weather,k,v)
        world.set_weather(weather)
        library=world.get_blueprint_library()
        def spawn(e, pose):
            bp = next((library.find(b) for b in e['blueprint_candidates'] if library.filter(b)), None)
            if bp is None: raise RuntimeError('Missing blueprint '+e['actor_id'])
            if e.get('color') and bp.has_attribute('color'): bp.set_attribute('color',e['color'])
            if bp.has_attribute('is_invincible'): bp.set_attribute('is_invincible','true')
            if bp.has_attribute('role_name'): bp.set_attribute('role_name','motion_pilot_'+e['actor_id'])
            actor=world.spawn_actor(bp,carla.Transform(carla.Location(x=pose['x'],y=pose['y'],z=100+len(actors)*5)))
            actors[e['actor_id']]=actor
            native = mode=='optimized' and e['actor_id']==aid
            if not native: actor.set_simulate_physics(False)
            actor.set_transform(ground_transform(actor,pose))
            if isinstance(actor,carla.Vehicle) and cfg['weather']['sun_altitude_angle']<0:
                actor.set_light_state(carla.VehicleLightState(carla.VehicleLightState.Position|carla.VehicleLightState.LowBeam))
            if native and kind=='walker': actor.blend_pose(0.)
            return actor
        for e in mapping['actors']:
            p=interpolate(data[e['actor_id']],start)
            if p is not None: spawn(e,p)
        target=actors[aid]; report['blueprint']=target.type_id
        follower=RiderFollower()
        # CARLA/PhysX cannot safely inspect vehicle physics after the vehicle's
        # simulation has been disabled for a recorded-pose baseline.
        if kind=='two_wheeler' and mode=='optimized':
            physics=target.get_physics_control(); wheels=physics.wheels
            angles=[w.max_steer_angle for w in wheels if w.max_steer_angle>0]
            xs=[w.position.x for w in wheels]
            wheelbase=max(.8,min(3.,(max(xs)-min(xs))/100))
            follower=RiderFollower(wheelbase,max(angles) if angles else 50)
            report['vehicle_geometry']=dict(wheelbase_m=wheelbase,max_steer_degrees=max(angles) if angles else 50)
        if mode=='optimized' and kind=='two_wheeler':
            # Warm engine and engage drive before imposing the measured initial
            # state. An idle automatic gearbox otherwise loses the first seconds.
            target.apply_control(carla.VehicleControl(throttle=.5))
        initial_speed=reference(data[aid],start)['motion_speed']
        warmup=3.5 if kind=='two_wheeler' and initial_speed>5 else 2.
        for _ in range(int(warmup*hz)): world.tick(60)
        if mode=='optimized' and kind=='two_wheeler':
            r=reference(data[aid],start)
            target.set_transform(ground_transform(target,r))
            target.set_target_velocity(carla.Vector3D(x=r['vx'],y=r['vy']))  # initial condition only
            follower.integral=1.
            report['initialization']=f'{warmup}s engine/suspension warmup, then set recorded initial pose and velocity once'
        queues={}
        for name in ('close','top'):
            bp=library.find('sensor.camera.rgb')
            bp.set_attribute('image_size_x','960');bp.set_attribute('image_size_y','540')
            bp.set_attribute('fov','70');bp.set_attribute('motion_blur_intensity','0')
            # Equal exposure in before/after footage; night source weather stays intact.
            bp.set_attribute('exposure_compensation','1.5')
            sensor=world.spawn_actor(bp,camera_pose(interpolate(data[aid],start),name=='top',sid))
            q=queue.Queue();sensor.listen(q.put);sensors.append(sensor);queues[name]=(sensor,q)
            (dest/name).mkdir(exist_ok=True)
        for step in range(int(duration*hz)):
            t=start+step/hz; next_t=t+1/hz
            commands=[]
            for e in mapping['actors']:
                eid=e['actor_id'];p=interpolate(data[eid],next_t)
                if p is None:
                    if eid in actors: actors.pop(eid).destroy()
                    continue
                if eid not in actors: spawn(e,p)
                if mode=='optimized' and eid==aid: continue
                commands.append(carla.command.ApplyTransform(actors[eid].id,ground_transform(actors[eid],p)))
            tr=target.get_transform();center=bbox_center(target,tr);vel=target.get_velocity()
            speed=math.hypot(vel.x,vel.y)
            control={}
            if mode=='optimized':
                if kind=='walker':
                    control=walker_command(data[aid],t,center.x,center.y)
                    target.apply_control(carla.WalkerControl(direction=carla.Vector3D(x=control['dx'],y=control['dy']),speed=control['speed']))
                else:
                    control=follower.step(data[aid],t,center.x,center.y,tr.rotation.yaw,speed,1/hz)
                    target.apply_control(carla.VehicleControl(throttle=control['throttle'],brake=control['brake'],steer=control['steer']))
            pose=interpolate(data[aid],next_t)
            for name,(sensor,q) in queues.items():
                commands.append(carla.command.ApplyTransform(sensor.id,camera_pose(pose,name=='top',sid)))
            responses=client.apply_batch_sync(commands,False)
            if any(r.has_error() for r in responses): raise RuntimeError(str([r.error for r in responses if r.has_error()]))
            frame=world.tick(60)
            for name,(_,q) in queues.items():
                img=receive_frame(q,frame)
                a=np.frombuffer(img.raw_data,dtype=np.uint8).reshape(img.height,img.width,4)[:,:,:3]
                if not cv2.imwrite(str(dest/name/f'{step:06d}.jpg'),a,[cv2.IMWRITE_JPEG_QUALITY,94]):
                    raise RuntimeError('Image write failed')
            snap=world.get_snapshot()
            if snap.frame != frame: raise RuntimeError('Snapshot / camera frame mismatch')
            state=snap.find(target.id);actual=state.get_transform();c=bbox_center(target,actual);v=state.get_velocity()
            r=reference(data[aid],next_t)
            row=dict(frame=frame,t=next_t,ref_x=pose['x'],ref_y=pose['y'],x=c.x,y=c.y,z=c.z,
                position_error=math.hypot(c.x-pose['x'],c.y-pose['y']),yaw=actual.rotation.yaw,
                yaw_error=abs(wrap(actual.rotation.yaw-r['motion_yaw'])),roll=actual.rotation.roll,
                speed=math.hypot(v.x,v.y),reference_speed=r['motion_speed'],
                throttle=control.get('throttle',0),brake=control.get('brake',0),steer=control.get('steer',0))
            telemetry.append(row)
            if kind=='walker':
                pose_bones=target.get_bones().bone_transforms
                selected={b.name:dict(x=b.component.location.x,y=b.component.location.y,z=b.component.location.z)
                    for b in pose_bones if any(s in b.name.lower() for s in ('foot','toe','leg'))}
                bones.append(dict(frame=frame,t=next_t,bones=selected))
            if step%hz==0: print(sid,mode,round(next_t,2),'error',round(row['position_error'],3),flush=True)
        errors=np.array([r['position_error'] for r in telemetry])
        report['metrics']=dict(position_p95_m=float(np.percentile(errors,95)),position_max_m=float(errors.max()),
            yaw_p95_deg=float(np.percentile([r['yaw_error'] for r in telemetry],95)),
            max_abs_roll_deg=max(abs(wrap(r['roll'])) for r in telemetry),frames=len(telemetry))
        if bones:
            motion={}
            for name in bones[0]['bones']:
                samples=np.array([[r['bones'][name][k] for k in ('x','y','z')] for r in bones])
                motion[name]=float(np.linalg.norm(samples.max(axis=0)-samples.min(axis=0)))
            report['bone_component_range_m']=motion
            report['gait_detected']=max(motion.values(),default=0)>.08
            write(dest/'bones.json',bones)
        report['tracking_accepted']=all(report['metrics'][k]<=limit for k,limit in report['acceptance'].items())
        report['success']=True
    except Exception:
        report['error']=traceback.format_exc()
        raise
    finally:
        # Save evidence before cleanup: a stopped server must not erase the
        # original error or leave a long sequence of 120-second RPC waits.
        if telemetry:
            with (dest/'telemetry.csv').open('w',encoding='utf-8-sig',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(telemetry[0]));writer.writeheader();writer.writerows(telemetry)
        write(dest/'run.json',report)
        client.set_timeout(2)
        try:
            client.get_server_version()
            for sensor in sensors:
                try: sensor.stop();sensor.destroy()
                except RuntimeError: pass
            for actor in actors.values():
                try: actor.destroy()
                except RuntimeError: pass
            if world is not None and settings is not None: world.apply_settings(settings)
        except RuntimeError as error:
            report['cleanup_error']=str(error)
            write(dest/'run.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scene',choices=list(PILOTS),required=True)
    p.add_argument('--mode',choices=['baseline','optimized'],required=True)
    p.add_argument('--duration',type=float);p.add_argument('--start',type=float);p.add_argument('--actor')
    p.add_argument('--tag',default='v1');p.add_argument('--hz',type=int,default=30)
    p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=2000)
    a=p.parse_args()
    if not 10<=a.hz<=100: p.error('--hz must be between 10 and 100')
    capture(a.scene,a.mode,a.duration,a.start,a.actor,a.hz,a.tag,a.host,a.port)
