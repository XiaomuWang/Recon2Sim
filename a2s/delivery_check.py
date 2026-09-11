"""Check traceability and readable final presentation artifacts for all scenes."""
import csv
import math
import cv2
from .common import PROJECT,IDS,read,write,sha


def build():
    results=[];runtime_summary=[]
    for sid in IDS:
        root=PROJECT/'outputs'/sid;capture=root/'validation/carla_imported'
        r=read(capture/'runtime_report.json');m=read(root/'presentation/report_manifest.json')
        times=read(capture/'frame_times.json')
        with (capture/'ego_telemetry.csv').open(encoding='utf-8-sig',newline='') as f:
            telemetry=list(csv.DictReader(f))
        checks={
            'runtime_pass':r.get('success') and r.get('fbx_runtime_verified'),
            'full_duration':r.get('full_duration_capture') and m.get('full_duration'),
            'all_meshes':r.get('imported_geometry_complete'),
            'road_surface':r['engine_surface_check']['misses']==0,
            'all_actors':not r['missing_actor_ids'],
            'frame_tables':len(times)==len(telemetry)==r['frames'],
            'frame_synchronization':all(int(p['carla_frame'])==int(p['snapshot_frame'])==t['carla_frame']
                and abs(float(p['replay_time_s'])-t['replay_time_s'])<1e-7 for p,t in zip(telemetry,times)),
            'ego_pose':all(math.isfinite(float(p['origin_error_m'])) and float(p['origin_error_m'])<=.01 for p in telemetry),
            'all_actor_poses':r.get('command_submission')=='apply_batch_sync before tick'
                and set(r.get('max_actor_origin_errors_m',{}))==set(r['activated_actor_ids'])
                and all(error<=.01 for error in r.get('max_actor_origin_errors_m',{}).values()),
            'all_actor_yaw':set(r.get('max_actor_yaw_errors_deg',{}))==set(r['activated_actor_ids'])
                and all(error<=.01 for error in r.get('max_actor_yaw_errors_deg',{}).values()) and m.get('body_yaw_verified'),
            'fresh_world':r.get('fresh_world_loaded'),
            'report_traceability':m.get('runtime_report_sha256')==sha(capture/'runtime_report.json'),
        }
        for camera in ['ego_front','ego_chase']:
            checks[camera+'_frames']=all((capture/camera/('%06d.png'%t['index'])).is_file() for t in times)
        video=cv2.VideoCapture(str(root/'presentation/report.mp4'))
        count=int(video.get(cv2.CAP_PROP_FRAME_COUNT));fps=video.get(cv2.CAP_PROP_FPS)
        width=int(video.get(cv2.CAP_PROP_FRAME_WIDTH));height=int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        checks['video_metadata']=(width,height)==(1920,1080) and abs(fps-m['fps'])<1e-6 and count==round((m['end_s']-m['start_s'])*fps)+1
        decoded=[]
        for index in [0,count//2,max(0,count-1)]:
            video.set(cv2.CAP_PROP_POS_FRAMES,index);ok,frame=video.read()
            decoded.append(bool(ok and frame is not None and frame.shape[:2]==(1080,1920)))
        video.release();checks['video_decode_samples']=all(decoded)
        results.append(dict(scene_id=sid,passed=all(checks.values()),checks=checks,video_frames=count,
                            video_fps=fps,telemetry_rows=len(telemetry),max_ego_execution_error_m=r['max_ego_origin_error_m']))
        runtime_summary.append(dict(scene_id=sid,success=all(checks.values()),frames=r['frames'],
            full_duration=r.get('full_duration_capture'),imported_objects=r.get('imported_environment_object_count'),
            surface_check=r['engine_surface_check']))
    write(PROJECT/'outputs/delivery_audit.json',dict(passed=all(r['passed'] for r in results),scenes=results,
          note='Replay execution consistency and artifact integrity; not real-world reconstruction accuracy.'))
    write(PROJECT/'outputs/imported_verification_summary.json',runtime_summary)
    print('DELIVERY_AUDIT',sum(r['passed'] for r in results),'/',len(results),flush=True)
    if not all(r['passed'] for r in results):raise SystemExit(1)


if __name__=='__main__':build()
