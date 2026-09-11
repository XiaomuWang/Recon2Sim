"""Recompute source-video optical flow using each scene's reviewed static-region mask.

Outputs are isolated in raw_recompute; supplied evidence is never overwritten.
Use --promote only to make recomputed evidence feed the next dynamic build.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path
from .common import IDS, PROJECT, WORKSPACE, read, write, sha
from .pipeline import init, run_log


def recompute(sid,promote=False):
    cfg=read(PROJECT/'configs'/(sid+'.json'))
    source=PROJECT/'recipes'/sid/'dynamic'
    recipe='audit_video.py' if sid in ['016955','ANA031'] else 'measure_ego_flow.py'
    root=PROJECT/'raw_recompute'/('dynamic_replay_'+sid)
    (root/'scripts').mkdir(parents=True,exist_ok=True);(root/'evidence').mkdir(exist_ok=True)
    code=(source/recipe).read_text(encoding='utf-8-sig')
    # Only replace video discovery; preserve original optical-flow mathematics and masks.
    video=repr(str(WORKSPACE/cfg['video_dir']))
    # re.sub replacement strings interpret backslashes; use a callable for literal Windows paths.
    original=(source/recipe).read_text(encoding='utf-8-sig')
    code=re.sub(r"next\((?:pathlib\.Path\('\.'\)|Path\('\.'\)|P\.parent)\.glob\([^\n]*?\)\)",
                lambda _: "__import__('pathlib').Path("+video+")",original)
    script=root/'scripts'/recipe;script.write_text(code,encoding='utf-8')
    run_log([sys.executable,PROJECT/'scripts/run_recipe.py',script],root/'recompute.log',root.parent)
    legacy=WORKSPACE/'dynamic_data'/('dynamic_replay_'+sid)/'evidence'
    comparison=[]
    for path in (root/'evidence').glob('*.json'):
        old=legacy/path.name
        comparison.append(dict(file=path.name,recomputed_sha256=sha(path),legacy_sha256=sha(old) if old.exists() else None,
                               semantically_identical=read(path)==read(old) if old.exists() else None))
        if promote:
            dest=PROJECT/'work'/('dynamic_replay_'+sid)/'evidence'/path.name
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    write(root/'recompute_report.json',dict(scene_id=sid,source_videos=cfg['video_dir'],recipe_sha256=sha(source/recipe),
          status='recomputed_from_raw_video',promoted=promote,comparisons=comparison,
          method='Masked sparse Lucas-Kanade flow, forward/backward consistency, RANSAC. Pixels/s are timing proxies, not metric velocity.'))
    print('RAW_EVIDENCE_COMPLETE',sid,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--scene',default='all',choices=['all']+IDS);ap.add_argument('--promote',action='store_true')
    args=ap.parse_args();init()
    for sid in IDS if args.scene=='all' else [args.scene]:recompute(sid,args.promote)
