"""CARLA synchronous trajectory replay and frame-exact camera evidence.

python -m a2s.replay --scene 014346 --mode xodr --duration 8
python -m a2s.replay --scene 014346 --mode imported
"""
import argparse
import csv
import math
import queue
import time
import traceback
from pathlib import Path
import carla
import cv2
import numpy as np
from .common import PROJECT, read, write, tracks, interpolate, sha, wrap


def ground_transform(actor, pose):
    """Convert measured bbox ground-center into the blueprint's actor origin."""
    if pose.get('roll_carla_deg') or pose.get('pitch_carla_deg'):
        rotation=carla.Rotation(yaw=pose['yaw_carla_deg'],roll=pose.get('roll_carla_deg',0),pitch=pose.get('pitch_carla_deg',0))
        frame=carla.Transform(carla.Location(),rotation);bb=actor.bounding_box
        center=frame.transform(carla.Location(x=bb.location.x,y=bb.location.y,z=bb.location.z))
        corners=[frame.transform(carla.Location(x=x*bb.extent.x,y=y*bb.extent.y,z=z*bb.extent.z)) for x in [-1,1] for y in [-1,1] for z in [-1,1]]
        height=-min(p.z for p in corners)
        return carla.Transform(carla.Location(x=pose['x']-center.x,y=pose['y']-center.y,z=pose['z']-center.z+height+.02),rotation)
    bb=actor.bounding_box; angle=math.radians(pose['yaw_carla_deg'])
    bx,by=bb.location.x,bb.location.y
    return carla.Transform(carla.Location(x=pose['x']-bx*math.cos(angle)+by*math.sin(angle),
        y=pose['y']-bx*math.sin(angle)-by*math.cos(angle),z=pose['z']-bb.location.z+bb.extent.z+0.02),
        carla.Rotation(yaw=pose['yaw_carla_deg']))


def receive_frame(q, frame):
    deadline=time.monotonic()+30
    while True:
        image=q.get(timeout=max(0.01,deadline-time.monotonic()))
        if image.frame==frame: return image
        if image.frame>frame: raise RuntimeError('Sensor skipped simulation frame '+str(frame))


def replay(sid,mode='xodr',host='localhost',port=2000,duration=None,fps=10,start=0):
    out=PROJECT/'outputs'/sid; cfg=read(out/'scene_config.json'); mapping=read(out/'entity_mapping.json')
    data=tracks(out/'trajectories.csv'); xodr=out/'map'/(cfg['map_name']+'.xodr')
    capture=out/'validation'/('carla_'+mode); capture.mkdir(parents=True,exist_ok=True)
    image_ext=cfg.get('capture_image_format','png')
    if image_ext not in ['png','jpg']:raise ValueError('Unsupported capture format')
    report=dict(image_extension=image_ext,scene_id=sid,mode=mode,success=False,carla_runtime_verified=False,fbx_runtime_verified=False,
                physical_collision_validated=False,camera_model='approximate uncalibrated rectilinear',frames=0,spawn_failures=[],blueprints={},
                xodr_sha256=sha(xodr),kinematic=True)
    client=carla.Client(host,port); client.set_timeout(180)
    cache=PROJECT/'runtime/carla_cache';cache.mkdir(parents=True,exist_ok=True)
    client.set_files_base_folder(str(cache))
    world=None; settings=None; weather=None; spectator_pose=None; owned={}; sensors=[]; friction=None
    try:
        report['server_version']=client.get_server_version();report['client_version']=client.get_client_version()
        if not report['server_version'].startswith('0.9.15'): raise RuntimeError('Expected CARLA 0.9.15')
        # RPC can listen before a cold-start default map has an active episode.
        ready_deadline=time.monotonic()+300;client.set_timeout(10)
        while True:
            try:client.get_world().get_snapshot();break
            except RuntimeError:
                if time.monotonic()>ready_deadline:raise
                print('WAIT_WORLD_READY',sid,flush=True);time.sleep(1)
        client.set_timeout(180)
        if mode=='xodr':
            world=client.generate_opendrive_world(xodr.read_text(encoding='utf-8'),
                carla.OpendriveGenerationParameters(vertex_distance=1.0,wall_height=0.0,additional_width=0.0))
        else:
            receipt=out/'validation/unreal_import_receipt.json'
            if not receipt.exists(): raise RuntimeError('FBX cooked-map import receipt required; run a2s.unreal_package build and install')
            r=read(receipt)
            if r['fbx_sha256']!=sha(out/'map'/(cfg['map_name']+'.fbx')) or r['xodr_sha256']!=sha(xodr):
                raise RuntimeError('Imported asset hash mismatch')
            if r.get('installed_directory'):
                for item in r.get('files',[]):
                    asset=Path(r['installed_directory'])/item['path']
                    if not asset.is_file() or sha(asset)!=item['sha256']:
                        raise RuntimeError('Installed cooked asset missing or changed: '+str(asset))
            # Reload also clears actors left by an interrupted capture.
            world=client.load_world(r.get('unreal_map',cfg['map_name']))
            report['fresh_world_loaded']=True
        m=world.get_map(); report['loaded_map']=m.name
        reference=read(out/'validation/waypoints.json')
        errors=[]
        for w in reference[::max(1,len(reference)//200)]:
            p=m.get_waypoint_xodr(w['road_id'],w['lane_id'],w['s'])
            if p is None: raise RuntimeError('Loaded map missing expected lane')
            loc=p.transform.location; errors.append(math.sqrt((loc.x-w['x'])**2+(loc.y-w['y'])**2+(loc.z-w['z'])**2))
        report['max_map_alignment_error_m']=max(errors)
        if max(errors)>.05: raise RuntimeError('Loaded map does not match rebuilt XODR')
        if mode=='imported':
            report['import_receipt']=r
            objects=world.get_environment_objects(carla.CityObjectLabel.Any)
            imported=[o for o in objects if cfg['map_name'] in o.name]
            report['environment_object_count']=len(objects)
            report['imported_environment_object_count']=len(imported)
            report['imported_environment_names']=[o.name for o in imported]
            if r.get('method','').startswith('native') and not imported:
                raise RuntimeError('Loaded map contains no identifiable imported FBX objects')
            if r.get('name_aliases'):
                report['expected_imported_mesh_count']=r['mesh_count']
                report['imported_geometry_complete']=len(imported)==r['mesh_count']
                if not report['imported_geometry_complete']:
                    raise RuntimeError('Imported FBX actor count does not match source mesh count')
            surface=[]
            for point in reference[::max(1,len(reference)//100)]:
                hits=world.cast_ray(carla.Location(x=point['x'],y=point['y'],z=point['z']+2),
                                    carla.Location(x=point['x'],y=point['y'],z=point['z']-1))
                surface.append(dict(road_id=point['road_id'],lane_id=point['lane_id'],s=point['s'],
                    error_m=min([abs(h.location.z-point['z']) for h in hits],default=None)))
            missed=[p for p in surface if p['error_m'] is None or p['error_m']>.25]
            report['engine_surface_check']=dict(samples=len(surface),misses=len(missed),
                max_error_m=max([p['error_m'] for p in surface if p['error_m'] is not None],default=None),rows=surface)
            if missed:raise RuntimeError('Cooked FBX road surface does not match XODR samples')
        settings=world.get_settings(); weather=world.get_weather(); spectator_pose=world.get_spectator().get_transform()
        sync=world.get_settings();sync.synchronous_mode=True;sync.fixed_delta_seconds=1/fps
        world.apply_settings(sync)
        w=world.get_weather()
        for k,v in cfg['weather'].items(): setattr(w,k,v)
        world.set_weather(w)
        library=world.get_blueprint_library(); resolved={}
        for e in mapping['actors']:
            candidates=[b for b in e['blueprint_candidates'] if b]
            bp=None
            for candidate in candidates:
                try: bp=library.find(candidate); break
                except (RuntimeError,IndexError): pass
            if bp is None: raise RuntimeError('No compatible blueprint: '+e['actor_id'])
            if bp.has_attribute('role_name'): bp.set_attribute('role_name','hero' if e['role']=='ego' else e['actor_id'])
            if e.get('color') and bp.has_attribute('color'): bp.set_attribute('color',e['color'])
            if bp.has_attribute('is_invincible'): bp.set_attribute('is_invincible','true')
            resolved[e['actor_id']]=bp
            report['blueprints'][e['actor_id']]=bp.id
        # Friction is recorded/applied to a trigger volume; kinematic replay does not use tire dynamics.
        fb=library.find('static.trigger.friction');fb.set_attribute('friction',str(cfg['friction_coefficient']))
        for axis in ['x','y','z']: fb.set_attribute('extent_'+axis,'100000')
        friction=world.spawn_actor(fb,carla.Transform(carla.Location(z=0)))
        if start<0 or start>=cfg['duration_s']:raise ValueError('Start time outside scenario')
        end=min(cfg['duration_s'],start+duration) if duration is not None else cfg['duration_s']
        camera_queues={}; camera_counts={}; timestamp_rows=[]; telemetry=[]; max_pose_error=0;activated=set();actor_errors={};yaw_errors={};roll_errors={}
        chase_sensor=None;chase_heading=None;spectator=world.get_spectator()
        for step in range(int(math.floor((end-start)*fps))+1):
            t=start+step/fps
            commands=[];expected_transforms={}
            for e in mapping['actors']:
                aid=e['actor_id']; pose=interpolate(data[aid],t)
                if pose is None:
                    if aid in owned: owned.pop(aid).destroy()
                    continue
                if aid not in owned:
                    # Spawn clear of other actors, disable physics, then place at recorded ground center.
                    spawn=carla.Transform(carla.Location(x=pose['x'],y=pose['y'],z=pose['z']+100+len(owned)*5))
                    actor=world.try_spawn_actor(resolved[aid],spawn)
                    if actor is None:
                        report['spawn_failures'].append(dict(actor_id=aid,time_s=t)); raise RuntimeError('Actor spawn failed: '+aid)
                    owned[aid]=actor;commands.append(carla.command.SetSimulatePhysics(actor.id,False));activated.add(aid)
                    if isinstance(actor,carla.Vehicle) and cfg['weather']['sun_altitude_angle']<0:
                        actor.set_light_state(carla.VehicleLightState(carla.VehicleLightState.Position | carla.VehicleLightState.LowBeam))
                actor=owned[aid];expected_transforms[aid]=ground_transform(actor,pose)
                commands.append(carla.command.ApplyTransform(actor.id,expected_transforms[aid]))
            ego=owned.get(mapping['ego_actor_id'])
            if ego is None: raise RuntimeError('Ego must exist across capture interval')
            if not sensors:
                for name,transform in [('ego_front',carla.Transform(carla.Location(x=1.1,z=1.7))),
                                       ('ego_chase',carla.Transform(carla.Location(x=-7,z=4),carla.Rotation(pitch=-15)))]:
                    bp=library.find('sensor.camera.rgb');bp.set_attribute('image_size_x','1280' if name=='ego_chase' else '960');bp.set_attribute('image_size_y','720' if name=='ego_chase' else '540');bp.set_attribute('fov','90')
                    if bp.has_attribute('motion_blur_intensity'):bp.set_attribute('motion_blur_intensity','0')
                    sensor=world.spawn_actor(bp,transform,attach_to=ego) if name=='ego_front' else world.spawn_actor(bp,carla.Transform())
                    if name=='ego_chase':chase_sensor=sensor
                    q=queue.Queue()
                    sensor.listen(q.put); sensors.append(sensor); camera_queues[name]=q; camera_counts[name]=0
                    (capture/name).mkdir(exist_ok=True)
            ep=interpolate(data[mapping['ego_actor_id']],t)
            target=expected_transforms[mapping['ego_actor_id']]
            chase_heading=ep['yaw_carla_deg'] if chase_heading is None else wrap(chase_heading+wrap(ep['yaw_carla_deg']-chase_heading)*(1-math.exp(-1/fps)))
            ca=math.radians(chase_heading)
            follow=carla.Transform(carla.Location(x=target.location.x-7*math.cos(ca),y=target.location.y-7*math.sin(ca),z=target.location.z+4),
                                   carla.Rotation(pitch=-15,yaw=chase_heading))
            commands.extend([carla.command.ApplyTransform(chase_sensor.id,follow),carla.command.ApplyTransform(spectator.id,follow)])
            responses=client.apply_batch_sync(commands,False)
            command_errors=[response.error for response in responses if response.has_error()]
            if command_errors:raise RuntimeError('Synchronous actor command failed: '+str(command_errors))
            frame=world.tick(60)
            # tick() can return before the asynchronous snapshot cache advances.
            # Bind telemetry to the immutable snapshot of the camera's frame.
            deadline=time.monotonic()+30
            snapshot=world.get_snapshot()
            while snapshot.frame<frame and time.monotonic()<deadline:
                time.sleep(.001);snapshot=world.get_snapshot()
            if snapshot.frame!=frame:raise RuntimeError('World snapshot does not match requested camera frame')
            ego_snapshot=snapshot.find(ego.id)
            if ego_snapshot is None:raise RuntimeError('Ego missing from frame snapshot')
            for aid,transform in expected_transforms.items():
                observed=snapshot.find(owned[aid].id)
                if observed is None:raise RuntimeError('Actor missing from frame snapshot: '+aid)
                error=observed.get_transform().location.distance(transform.location)
                actor_errors[aid]=max(actor_errors.get(aid,0),error)
                yaw_error=abs(wrap(observed.get_transform().rotation.yaw-transform.rotation.yaw))
                yaw_errors[aid]=max(yaw_errors.get(aid,0),yaw_error)
                roll_error=abs(wrap(observed.get_transform().rotation.roll-transform.rotation.roll))
                roll_errors[aid]=max(roll_errors.get(aid,0),roll_error)
                if roll_error>.01:raise RuntimeError('Frame-synchronous actor roll error exceeds 0.01 degree: '+aid)
                if yaw_error>.01:
                    report['yaw_mismatch']=dict(actor_id=aid,time_s=t,frame=frame,error_deg=yaw_error)
                    raise RuntimeError('Frame-synchronous actor yaw error exceeds 0.01 degree: '+aid)
                if error>.01:
                    report['pose_mismatch']=dict(actor_id=aid,time_s=t,frame=frame,error_m=error)
                    raise RuntimeError('Frame-synchronous actor position error exceeds 1 cm: '+aid)
            ep=interpolate(data[mapping['ego_actor_id']],t); expected=ground_transform(ego,ep)
            pose_actual=ego_snapshot.get_transform();actual=pose_actual.location
            max_pose_error=max(max_pose_error,actual.distance(expected.location))
            angle=math.radians(pose_actual.rotation.yaw);bb=ego.bounding_box
            gx=actual.x+bb.location.x*math.cos(angle)-bb.location.y*math.sin(angle)
            gy=actual.y+bb.location.x*math.sin(angle)+bb.location.y*math.cos(angle)
            observed_speed=(math.hypot(gx-telemetry[-1]['ground_x'],gy-telemetry[-1]['ground_y'])*fps) if telemetry else None
            yaw_rate=wrap(pose_actual.rotation.yaw-telemetry[-1]['yaw_carla_deg'])*fps if telemetry else 0.0
            telemetry.append(dict(replay_time_s=t,carla_frame=frame,snapshot_frame=snapshot.frame,ground_x=gx,ground_y=gy,
                ground_z=actual.z+bb.location.z-bb.extent.z-.02,yaw_carla_deg=pose_actual.rotation.yaw,
                commanded_yaw_deg=ep['yaw_carla_deg'],yaw_rate_deg_s=yaw_rate,chase_camera_yaw_deg=chase_heading,
                commanded_speed_m_s=ep.get('speed'),position_derived_speed_m_s=observed_speed,
                origin_error_m=actual.distance(expected.location)))
            for name,q in camera_queues.items():
                im=receive_frame(q,frame)
                pixels=np.frombuffer(im.raw_data,dtype=np.uint8).reshape(im.height,im.width,4)[:,:,:3]
                destination=capture/name/('%06d.'%step+image_ext)
                encode_options=[cv2.IMWRITE_JPEG_QUALITY,cfg.get('capture_jpeg_quality',93)] if image_ext=='jpg' else [cv2.IMWRITE_PNG_COMPRESSION,1]
                if not cv2.imwrite(str(destination),pixels,encode_options):
                    raise RuntimeError('Failed to save CARLA camera frame')
                if step==0:
                    reference_image=capture/(name+'_native_encoding_reference.png');im.save_to_disk(str(reference_image))
                    if image_ext=='png' and not np.array_equal(cv2.imread(str(reference_image)),cv2.imread(str(destination))):
                        raise RuntimeError('Fast PNG encoding changed the camera RGB pixels')
                camera_counts[name]+=1
            timestamp_rows.append(dict(index=step,carla_frame=frame,replay_time_s=t,source_video_time_s=t+cfg['source_video_start_s']))
            report['frames']+=1
            if step%100==0:print('CAPTURE',sid,'t=',round(t,1),'actors=',len(owned),'frame=',frame,flush=True)
        report.update(success=True,carla_runtime_verified=True,fbx_runtime_verified=(mode=='imported'),
                      command_submission='apply_batch_sync before tick',max_actor_origin_errors_m=actor_errors,
                      max_actor_yaw_errors_deg=yaw_errors,max_actor_roll_errors_deg=roll_errors,chase_camera='independent world camera; heading smoothing time constant 1 s',
                      encoding=('JPEG quality '+str(cfg.get('capture_jpeg_quality',93))+'; native first-frame PNG retained' if image_ext=='jpg' else 'lossless PNG compression 1; RGB equality checked against CARLA native encoder'),
                      max_ego_origin_error_m=max_pose_error,camera_counts=camera_counts,capture_start_s=start,capture_duration_s=end-start,
                      activated_actor_ids=sorted(activated),full_duration_capture=start==0 and abs(end-cfg['duration_s'])<1/fps)
        expected={e['actor_id'] for e in mapping['actors'] if e['end_time_s']>=start and e['start_time_s']<=end}
        report['missing_actor_ids']=sorted(expected-activated)
        if report['missing_actor_ids']:raise RuntimeError('Expected actors never spawned: '+str(report['missing_actor_ids']))
        if max_pose_error>.01:raise RuntimeError('Ego frame-synchronous pose error exceeds 1 cm')
        write(capture/'frame_times.json',timestamp_rows)
        with (capture/'ego_telemetry.csv').open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=list(telemetry[0]));writer.writeheader();writer.writerows(telemetry)
    except Exception as e:
        report.update(success=False,carla_runtime_verified=False,fbx_runtime_verified=False,error=str(e),traceback=traceback.format_exc())
        raise
    finally:
        for sensor in sensors:
            try: sensor.stop();sensor.destroy()
            except RuntimeError: pass
        for actor in list(owned.values())+([friction] if friction else []):
            try: actor.destroy()
            except RuntimeError: pass
        if world is not None and settings is not None:
            report['cleanup_errors']=[]
            for restore in [lambda:world.set_weather(weather),lambda:world.get_spectator().set_transform(spectator_pose),lambda:world.apply_settings(settings)]:
                try:restore()
                except RuntimeError as error:report['cleanup_errors'].append(str(error))
        write(capture/'runtime_report.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--scene',required=True)
    p.add_argument('--mode',choices=['xodr','imported'],default='xodr');p.add_argument('--host',default='localhost')
    p.add_argument('--port',type=int,default=2000);p.add_argument('--duration',type=float);p.add_argument('--fps',type=int,default=10)
    p.add_argument('--start',type=float,default=0)
    a=p.parse_args()
    if a.fps<=0 or a.fps>100 or a.duration is not None and a.duration<0: p.error('Invalid FPS/duration')
    replay(a.scene,a.mode,a.host,a.port,a.duration,a.fps,a.start)

if __name__=='__main__': main()
