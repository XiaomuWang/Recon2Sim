"""Refresh only the FBX panel after rerendering, without seeking all source videos again."""
import subprocess
from pathlib import Path
import cv2
from PIL import Image
from .common import PROJECT,WORKSPACE,IDS,read


def refresh(sid):
    out=PROJECT/'outputs'/sid;folder=out/'preview';video=folder/'six_panel_comparison.mp4'
    renders=read(out/'validation/fbx/renders.json')
    fps=read(folder/'preview_metadata.json')['fps'];cfg=read(out/'scene_config.json')
    cap=cv2.VideoCapture(str(video));count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));cap.release()
    exe=str(next((WORKSPACE/'dynamic_data').glob('*/runtime/ffmpeg.exe')))
    args=[exe,'-y','-i',str(video)]
    for r in renders:args+=['-loop','1','-framerate',str(fps),'-i',str(out/'validation/fbx'/r['file'])]
    filters=[]
    for i,r in enumerate(renders):
        filters.append(f'[{i+1}:v]scale=480:270[img{i}]')
        lo=(renders[i-1]['replay_time_s']+r['replay_time_s'])/2 if i else None
        hi=(renders[i+1]['replay_time_s']+r['replay_time_s'])/2 if i<len(renders)-1 else None
        condition=(f'gt(t,{lo})' if lo is not None else '1')+(f'*lte(t,{hi})' if hi is not None else '')
        previous='0:v' if i==0 else f'v{i-1}'
        filters.append(f"[{previous}][img{i}]overlay=960:390:enable='{condition}'[v{i}]")
    temp=folder/'six_panel_updated.mp4'
    args+=['-filter_complex',';'.join(filters),'-map',f'[v{len(renders)-1}]','-frames:v',str(count),'-an','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(temp)]
    with (folder/'refresh.log').open('w') as log:subprocess.run(args,stdout=log,stderr=log,check=True)
    temp.replace(video)
    critical={'014346':17,'019742':110,'016955':114,'024388':64,'0512189':85,'0508656':82,'ANA031':26.8}[sid]
    cap=cv2.VideoCapture(str(video))
    for name,t in [('comparison_start.png',0),('comparison_incident.png',round(critical*fps)/fps)]:
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read()
        if not ok:raise RuntimeError('Cannot decode refreshed comparison')
        Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).save(folder/name)
    cap.release();print('PREVIEW_REFRESHED',sid,flush=True)

if __name__=='__main__':
    for sid in IDS:refresh(sid)
