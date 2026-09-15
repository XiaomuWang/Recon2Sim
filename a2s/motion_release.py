"""Stage, audit and publish the original seven motion-updated reports."""
import argparse
import csv
import shutil
import subprocess
import time
from pathlib import Path
import cv2
from .common import PROJECT, read, write, sha
from .motion import ORIGINAL_SCENES

STAGE=PROJECT/'work/motion_release'
ORDER=['024388','0512189','0508656','ANA031','014346','019742','016955']


def run():
    from concurrent.futures import ThreadPoolExecutor
    from .motion_full import replay
    jobs={};status={}
    with ThreadPoolExecutor(max_workers=1) as composer:
        for sid in ['ANA031']+[s for s in ORDER if s!='ANA031']:
            prepare(sid)
            try:
                record=STAGE/'outputs'/sid/'validation/carla_imported/runtime_report.json'
                if record.parent.exists() and any(record.parent.iterdir()) and (not record.exists() or not read(record).get('success')):
                    failed=PROJECT/'work/motion_failures'/(sid+'_'+str(time.time_ns()))
                    record.parent.resolve().relative_to((PROJECT/'work').resolve());failed.resolve().relative_to((PROJECT/'work').resolve())
                    failed.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(record.parent),str(failed))
                if not record.exists():replay(sid,capture_root=record.parent)
                audit(sid)
                if (STAGE/'outputs'/sid/'presentation/report_manifest.json').exists():status[sid]='ready'
                else:jobs[sid]=composer.submit(compose,sid);status[sid]='captured; composition queued'
            except Exception as e:
                status[sid]='failed: '+str(e)
            write(STAGE/'progress.json',status);print('MOTION_RELEASE',sid,status[sid],flush=True)
        for sid,job in jobs.items():
            try:job.result();status[sid]='ready'
            except Exception as e:status[sid]='failed: '+str(e)
            write(STAGE/'progress.json',status);print('MOTION_RELEASE',sid,status[sid],flush=True)
    if any(v!='ready' for v in status.values()):raise RuntimeError(str(status))


def prepare(sid):
    source=PROJECT/'outputs'/sid;dest=STAGE/'outputs'/sid
    dest.mkdir(parents=True,exist_ok=True);(dest/'validation').mkdir(exist_ok=True)
    for name in ['scene_config.json','entity_mapping.json','trajectories.csv','analysis/ego_metrics.json',
                 'validation/waypoints.json']:
        target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,target)
    # Only this compact reference composite is needed, not raw video/frame trees.
    target=dest/'preview/six_panel_comparison.mp4';target.parent.mkdir(exist_ok=True)
    if not target.exists():shutil.copy2(source/'preview/six_panel_comparison.mp4',target)


def audit(sid):
    root=STAGE/'outputs'/sid;capture=root/'validation/carla_imported'
    r=read(capture/'runtime_report.json');times=read(capture/'frame_times.json')
    with (capture/'ego_telemetry.csv').open(encoding='utf-8-sig') as f:ego=list(csv.DictReader(f))
    records=set(r['recorded_actor_ids']);moving=set(r['motion_actor_ids']);all_ids=set(r['activated_actor_ids'])
    checks=dict(full_capture=r['success'] and r['full_duration_capture'],map=r['fbx_runtime_verified'] and r['imported_geometry_complete'],
        surface=r['engine_surface_check']['misses']==0,all_actors=not r['missing_actor_ids'],
        actor_partition=(records|moving)==all_ids and not records&moving,
        recorded_position=all(x<=.01 for x in r['max_actor_origin_errors_m'].values()),
        recorded_yaw=all(x<=.01 for x in r['max_actor_yaw_errors_deg'].values()),
        motion=r['motion_tracking_accepted'],
        frame_sync=len(ego)==len(times)==r['frames'] and all(int(a['carla_frame'])==int(a['snapshot_frame'])==b['carla_frame'] for a,b in zip(ego,times)))
    walkers=[a for a in r['motion']['actors'].values() if a['kind']=='walker' and a['moving_samples']>=10]
    checks['walking_feet_animated']=all(len(a['foot_component_ranges_m'])>=2 and min(a['foot_component_ranges_m'].values())>.03 for a in walkers)
    checks['explicit_exceptions']=all(aid in records and aid not in moving and bool(e.get('reason')) for aid,e in r['motion'].get('recorded_exceptions',{}).items())
    for camera in ('ego_chase','ego_front'):
        checks[camera]=len(list((capture/camera).glob('*.jpg')))==r['frames']
    manifest=root/'presentation/report_manifest.json'
    if manifest.exists():
        m=read(manifest);checks['provenance']=m['runtime_report_sha256']==sha(capture/'runtime_report.json')
        video=cv2.VideoCapture(str(root/'presentation/report.mp4'))
        count=int(video.get(cv2.CAP_PROP_FRAME_COUNT));fps=video.get(cv2.CAP_PROP_FPS)
        checks['movie_frames']=count==len(times) and fps==10
        checks['decode']=True
        for index in (0,count//2,count-1):
            video.set(cv2.CAP_PROP_POS_FRAMES,index);ok,frame=video.read()
            checks['decode'] &= bool(ok and frame.shape[:2]==(1080,1920))
        video.release()
    result=dict(scene_id=sid,passed=all(checks.values()),checks=checks,motion=r['motion'])
    write(root/'validation/motion_audit.json',result)
    if not result['passed']:raise RuntimeError('Failed motion release checks: '+sid+' '+str(checks))
    return result


def compose(sid):
    from . import motion_movie
    motion_movie.PROJECT=STAGE
    prepare(sid);audit(sid);motion_movie.build(sid);return audit(sid)


def refresh():
    from . import report_highlights,report_page
    report_highlights.build()
    report_page.build()


def promote():
    results=[audit(sid) for sid in ORDER]
    for sid in ORDER:
        if not (STAGE/'outputs'/sid/'presentation/report_manifest.json').is_file():raise RuntimeError('Composition missing: '+sid)
    backup=STAGE/'previous_release'
    journal=STAGE/'promotion.json';done=read(journal) if journal.exists() else []
    for sid in ORDER:
        if sid in done:continue
        source=STAGE/'outputs'/sid;dest=PROJECT/'outputs'/sid
        for rel in ('validation/carla_imported','presentation'):
            old=dest/rel;new=source/rel;save=backup/sid/rel
            for p in (old,new,save):p.resolve().relative_to(PROJECT.resolve())
            save.parent.mkdir(parents=True,exist_ok=True)
            if save.exists():raise FileExistsError('Backup exists; inspect incomplete promotion: '+str(save))
            shutil.move(str(old),str(save));shutil.move(str(new),str(old))
        shutil.copy2(source/'validation/motion_audit.json',dest/'validation/motion_audit.json')
        done.append(sid);write(journal,done)
    write(PROJECT/'outputs/motion_update_audit.json',dict(passed=True,scenes=results,scope='Original seven, native motion with reconstruction constraints'))
    from . import delivery
    refresh()
    delivery.IDS=list(ORIGINAL_SCENES);delivery.main()
    from .delivery_check import build as delivery_audit
    delivery_audit(list(ORIGINAL_SCENES))
    # Replace legacy exact-pose wording in the generated requirements response.
    for path in (PROJECT/'满足他人的需求.txt',PROJECT.parent/'满足他人的需求.txt'):
        text=path.read_text(encoding='utf-8-sig')
        text=text.replace('启动 CARLA 0.9.15 后：python -m a2s.replay --scene 014346 --mode imported。',
            '启动 CARLA 0.9.15 并配置匹配客户端后：python -m a2s.motion_full --scene 014346 --mode imported。原 a2s.replay 保留为记录位姿基线。')
        text=text.replace('批量实机采集与汇报：python -m a2s.verify_imported --scene all --fps 10。',
            '新版七组批量采集、合成和检查：python -m a2s.motion_release run；检查通过后执行 promote。已发布目录需指定新的 --stage work/motion_release_新版本。')
        text=text.replace('全部有效目标的位置和偏航通过同步批量命令提交，逐帧检查位置误差不超过 1 厘米、偏航误差不超过 0.01 度。',
            '主车及记录位姿目标保留 1 厘米 / 0.01 度执行校验；适用骑行目标与行人采用 30 Hz 原生运动控制，含明示的轨迹约束与速度辅助。动态目标单独检查位置 P95 ≤ 0.5 m、最大 ≤ 1 m、运动中偏航 P95 ≤ 15°。')
        text=text.replace('6. 动态回放是按轨迹驱动姿态，保留录制末态；没有复现轮胎、碰撞冲量、车体变形或闭环自动驾驶响应。',
            '6. 新版骑行目标使用 CARLA 原生车辆控制，行人使用原生行走动画；为保留估计事故时序，必要的轨迹约束、速度辅助与替代模型均记录在 motion 字段中。三轮车、清扫车等不匹配替代模型及两条与静态障碍冲突的骑行轨迹保留记录位姿。未验证真实碰撞冲量、车体变形或闭环自动驾驶响应。')
        text+='\n八、本次七组运动优化验收\n'
        for result in results:
            actors=result['motion']['actors']
            counts={kind:sum(a['kind']==kind for a in actors.values()) for kind in ('two_wheeler','walker')}
            text+=f"{result['scene_id']}：原生骑行控制 {counts['two_wheeler']} 个，原生行人控制 {counts['walker']} 个；全程、帧同步、跟踪与行走骨骼检查通过。\n"
            for aid,exception in result['motion'].get('recorded_exceptions',{}).items():
                text+=f"  记录位姿例外 {aid}：与重建静态几何冲突，保留原位置、偏航和时序，不计入原生物理跟踪通过。\n"
        text+='逐目标误差、约束次数、脚部运动证据和例外理由见 outputs/motion_update_audit.json；旧版正式帧和视频保留于本次工作目录的 previous_release。\n'
        path.write_text(text,encoding='utf-8-sig')
    print('SEVEN_MOTION_REPORTS_PROMOTED',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','compose','audit','promote','run','refresh'])
    parser.add_argument('--scene',default='all');parser.add_argument('--stage',help='Isolated release directory inside this project/work')
    args=parser.parse_args()
    if args.stage:
        STAGE=Path(args.stage).resolve();STAGE.relative_to((PROJECT/'work').resolve())
    if args.action=='run' and (STAGE/'promotion.json').exists():
        raise RuntimeError('This release has been promoted. Select a new --stage inside project/work for another release.')
    if args.action=='promote':promote()
    elif args.action=='run':run()
    elif args.action=='refresh':refresh()
    else:
        for sid in ORDER if args.scene=='all' else [args.scene]:globals()[args.action](sid)
