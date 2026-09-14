"""Verify pilot metrics, video decoding and optional report HTTP byte ranges."""
import argparse
import csv
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from a2s.common import PROJECT, read, sha, write


def check(url=None):
    root=PROJECT/'outputs/motion_review'; results=[]
    for sid in ('024388','0508656','019742'):
        r=read(root/(sid+'.json'))
        assert r['success'] and r['tracking_accepted'], sid+' capture / tracking failed'
        assert r['target_teleports_after_initialization']==0
        assert r['reference_sha256']==sha(PROJECT/'outputs'/sid/'trajectories.csv')
        capture=PROJECT/'outputs'/sid/'validation/motion_pilot'/r['tag']/'optimized'
        with (capture/'telemetry.csv').open(encoding='utf-8-sig') as f:
            telemetry=list(csv.DictReader(f))
        assert len(telemetry)==r['metrics']['frames']
        times=np.array([float(x['t']) for x in telemetry]);frames=[int(x['frame']) for x in telemetry]
        assert np.allclose(np.diff(times),1/r['hz'])
        assert all(b==a+1 for a,b in zip(frames,frames[1:]))
        position=np.array([float(x['position_error']) for x in telemetry])
        assert abs(np.percentile(position,95)-r['metrics']['position_p95_m'])<1e-8
        assert abs(position.max()-r['metrics']['position_max_m'])<1e-8
        for mode,tag in [('optimized',r['tag']),('baseline',r['baseline_tag'])]:
            folder=PROJECT/'outputs'/sid/'validation/motion_pilot'/tag/mode
            run=read(folder/'run.json')
            assert run['success']
            for key in ('start','duration','hz','reference_sha256','target','loaded_map'):
                assert run[key]==r[key],sid+' mismatch '+key
            for camera in ('close','top'):
                assert len(list((folder/camera).glob('*.jpg')))==len(telemetry)
        if sid=='024388':
            assert r['gait_detected'] and not r['before_gait_detected']
            for side in ('L','R'):
                assert r['bone_component_range_m']['crl_foot__'+side]>.08
        movie=root/r['video']; cap=cv2.VideoCapture(str(movie))
        try:
            assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT))==len(telemetry)
            assert abs(cap.get(cv2.CAP_PROP_FPS)-r['hz'])<.01
            for i in (0,len(telemetry)//2,len(telemetry)-1):
                cap.set(cv2.CAP_PROP_POS_FRAMES,i);ok,frame=cap.read()
                assert ok and frame.shape[:2]==(1000,1600)
        finally: cap.release()
        item=dict(scene_id=sid,success=True,frames=len(telemetry),metrics=r['metrics'],video_sha256=sha(movie))
        if url:
            request=Request(url.rstrip('/')+'/'+r['video'],headers={'Range':'bytes=65536-65567'})
            with urlopen(request,timeout=10) as response:
                assert response.status==206
                actual=response.read(); assert len(actual)==32
                with movie.open('rb') as f: f.seek(65536);assert actual==f.read(32)
                item['http_range_verified']=True
        results.append(item)
    if url:
        with urlopen(url,timeout=10) as response:
            assert response.status==200
            page=response.read().decode('utf-8')
            assert all(s+'.mp4' in page for s in ('024388','0508656','019742'))
    write(root/'verification.json',dict(success=True,scope='three selected-actor pilots, not all seven full replays',results=results))
    print(json.dumps(results,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--url')
    check(parser.parse_args().url)
