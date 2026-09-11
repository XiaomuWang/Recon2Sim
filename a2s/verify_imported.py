"""Verify each installed FBX map in CARLA and generate presentation evidence."""
import argparse
import traceback
from concurrent.futures import ThreadPoolExecutor
from .common import IDS,PROJECT,write,read
from .replay import replay
from .report_movie import build as compose
from .report_page import build as page
from .delivery import main as delivery


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--scene',default='all')
    p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=2000)
    p.add_argument('--fps',type=int,default=10);p.add_argument('--duration',type=float)
    a=p.parse_args();ids=list(IDS) if a.scene=='all' else a.scene.split(',')
    results=[];pending=[]
    summary=PROJECT/'outputs/imported_verification_summary.json'
    previous={r['scene_id']:r for r in read(summary)} if summary.exists() else {}

    def commit(result):
        results.append(result);previous[result['scene_id']]=result
        write(summary,[previous[key] for key in IDS if key in previous])
        page();delivery()
        print('VERIFY_END',result['scene_id'],result['success'],flush=True)

    def collect(wait=False):
        for job in list(pending):
            sid,r,future=job
            if not wait and not future.done():continue
            try:
                future.result()
                result=dict(scene_id=sid,success=True,frames=r['frames'],full_duration=r['full_duration_capture'],
                            imported_objects=r['imported_environment_object_count'],surface_check=r['engine_surface_check'])
            except Exception as e:
                result=dict(scene_id=sid,success=False,error=str(e),traceback=traceback.format_exc())
            pending.remove(job);commit(result)

    # Composition reads a completed capture from another scene; only the main
    # thread changes CARLA or writes the shared delivery/page status.
    with ThreadPoolExecutor(max_workers=1) as composer:
        for sid in ids:
            collect();print('VERIFY_BEGIN',sid,flush=True)
            try:
                r=replay(sid,'imported',a.host,a.port,a.duration,a.fps)
                pending.append((sid,r,composer.submit(compose,sid,a.fps,'imported')))
            except Exception as e:
                print('VERIFY_FAILED',sid,str(e),flush=True)
                commit(dict(scene_id=sid,success=False,error=str(e),traceback=traceback.format_exc()))
        collect(wait=True)
    if any(not r['success'] for r in results):raise SystemExit(1)


if __name__=='__main__':main()
