"""Verify local CARLA preview integrity independently of publication."""
import cv2
from .common import PROJECT,read,write,sha

def verify(sid):
    root=PROJECT/'outputs'/sid;folder=root/'presentation';runtime=root/'validation/carla_imported'
    report=read(runtime/'runtime_report.json');manifest=read(folder/'report_manifest.json');timeline=read(runtime/'frame_times.json')
    cap=cv2.VideoCapture(str(folder/'report.mp4'));fps=cap.get(cv2.CAP_PROP_FPS);frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    checks=dict(actual_carla=report['success'] and report['fbx_runtime_verified'],complete_geometry=report['imported_geometry_complete'],road_surface=report['engine_surface_check']['misses']==0,all_registered_actors=not report['missing_actor_ids'],runtime_traceability=manifest['runtime_report_sha256']==sha(runtime/'runtime_report.json'),full_duration=report['full_duration_capture'] and manifest['full_duration'],dimensions=(int(cap.get(3)),int(cap.get(4)))==(1920,1080),frames=frames==round((manifest['end_s']-manifest['start_s'])*fps)+1)
    decoded=[]
    for index in [0,frames//2,frames-1]:cap.set(cv2.CAP_PROP_POS_FRAMES,index);ok,im=cap.read();decoded.append(bool(ok and im is not None))
    cap.release();checks['decode_samples']=all(decoded)
    checks['pose_execution']=all(e<=.01 for e in report['max_actor_origin_errors_m'].values())
    checks['yaw_execution']=all(e<=.01 for e in report['max_actor_yaw_errors_deg'].values())
    checks['roll_execution']=all(e<=.01 for e in report.get('max_actor_roll_errors_deg',{}).values())
    checks['camera_frames']=all((runtime/camera/('%06d.'%t['index']+report.get('image_extension','png'))).is_file() for camera in ['ego_front','ego_chase'] for t in timeline)
    result=dict(scene_id=sid,passed=all(checks.values()),checks=checks,duration_s=frames/fps,fps=fps,video_sha256=sha(folder/'report.mp4'),scope='Visual estimated reconstruction and actual CARLA kinematic replay; not calibrated ground truth or validated collision dynamics.')
    write(folder/'preview_audit.json',result)
    if not result['passed']:raise RuntimeError(str(result))
    print('LOCAL_PREVIEW_VERIFIED',sid,round(frames/fps,2),flush=True)
    return result
