"""Local presentation viewer. Files are generated offline; no external dependencies."""
import json
import shutil
from .common import PROJECT,read,sha
from .report_movie import NAMES,REPORT_IDS


def build():
    out=PROJECT/'outputs';scenes=[]
    for sid in REPORT_IDS:
        root=out/sid;cfg=read(root/'scene_config.json');mapping=read(root/'entity_mapping.json')
        source_config=read(PROJECT/'configs'/(sid+'.json'))
        brand=source_config.get('vehicle_brand') or source_config['video_dir'].replace('\\','/').rsplit('/',1)[-1].split('_',1)[0]
        analysis=read(root/'analysis/ego_metrics.json')['summary']
        manifest=root/'presentation/report_manifest.json';movie=read(manifest) if manifest.exists() else None
        mode='imported' if movie and movie.get('fbx_environment_loaded') else 'xodr'
        report=root/'validation'/('carla_'+mode)/'runtime_report.json';runtime=read(report) if report.exists() else {}
        ready=bool(movie) and runtime.get('success',False)
        if ready and movie.get('runtime_report_sha256'):ready=movie['runtime_report_sha256']==sha(report)
        scenes.append(dict(id=sid,brand=brand,title=NAMES[sid],duration=cfg['duration_s'],actors=len(mapping['actors']),ego=mapping['ego_actor_id'],
            related=mapping['accident_actor_ids'],metrics=analysis,ready=ready,movie=movie,mode=mode,runtime=runtime.get('success',False),
            media_version=str((root/'presentation/report.mp4').stat().st_mtime_ns)+'_range1' if ready else 'pending'))
    template=(PROJECT/'templates/report.html').read_text(encoding='utf-8')
    downloads=[]
    highlight_manifest=out/'presentation/highlights_manifest.json'
    highlight_name=read(highlight_manifest).get('video_file','highlights.mp4') if highlight_manifest.exists() else 'highlights.mp4'
    for path,label in [('presentation/'+highlight_name,'七组事故重点片段 · 84 秒'),
                       ('carla_package/Accident2SimScenes_CARLA_0.9.15_Windows.zip','下载 CARLA 场景导入包')]:
        if (out/path).is_file():downloads.append('<a href="'+path+'?v='+str((out/path).stat().st_mtime_ns)+'_range1" '+('target="_blank"' if path.endswith('.mp4') else 'download')+'>'+label+'</a>')
    template=template.replace('__GLOBAL_DOWNLOADS__',' · '.join(downloads))
    if not (out/'offline.html').exists():shutil.copy2(out/'index.html',out/'offline.html')
    (out/'index.html').write_text(template.replace('__SCENE_DATA__',json.dumps(scenes,ensure_ascii=False).replace('</','<\/')),encoding='utf-8')
    viewer=(PROJECT/'templates/csv_viewer.html').read_text(encoding='utf-8')
    (out/'csv_viewer.html').write_text(viewer.replace('__SCENE_NAMES__',json.dumps(NAMES,ensure_ascii=False)),encoding='utf-8')
    print('REPORT_PAGE_UPDATED',sum(s['ready'] for s in scenes),flush=True)

if __name__=='__main__':build()
