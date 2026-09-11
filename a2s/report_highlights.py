"""Join seven traceable accident excerpts into one presentation video."""
import subprocess
import time
import cv2
from .common import PROJECT,WORKSPACE,read,write
from .report_movie import CRITICAL,NAMES,REPORT_IDS


def build():
    dest=PROJECT/'outputs/presentation';segments=dest/'segments'
    segments.mkdir(parents=True,exist_ok=True)
    exe=str(next((WORKSPACE/'dynamic_data').glob('*/runtime/ffmpeg.exe')))
    clips=[]
    for sid in REPORT_IDS:
        root=PROJECT/'outputs'/sid
        m=read(root/'presentation/report_manifest.json')
        if not m.get('main_is_actual_carla') or not m.get('fbx_environment_loaded'):
            raise RuntimeError('Verified FBX CARLA report required: '+sid)
        start=max(m['start_s'],min(CRITICAL[sid]-6,m['end_s']-12))
        duration=min(12,m['end_s']-start)
        if duration<1:raise RuntimeError('Insufficient captured interval: '+sid)
        clips.append(dict(scene_id=sid,title=NAMES[sid],start_s=start,end_s=start+duration,
                          input_offset_s=start-m['start_s'],duration_s=duration,layout_version=m.get('layout_version')))
    with (dest/'encode.log').open('w',encoding='utf-8') as log:
        for c in clips:
            sid=c['scene_id'];source=PROJECT/'outputs'/sid/'presentation/report.mp4'
            subprocess.run([exe,'-y','-hide_banner','-loglevel','warning','-i',str(source),
                '-ss',str(c['input_offset_s']),'-t',str(c['duration_s']),'-an','-vf','fps=10',
                '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',
                str(segments/(sid+'.mp4'))],stdout=log,stderr=log,check=True)
        listing=dest/'segments.txt'
        listing.write_text(''.join("file 'segments/"+c['scene_id']+".mp4'\n" for c in clips),encoding='utf-8')
        target=dest/'highlights.pending.mp4'
        subprocess.run([exe,'-y','-hide_banner','-loglevel','warning','-f','concat','-safe','1','-i',str(listing),
                        '-c','copy','-movflags','+faststart',str(target)],stdout=log,stderr=log,check=True)
    publish(dest,clips)


def publish(dest,clips):
    target=dest/'highlights.pending.mp4'
    cap=cv2.VideoCapture(str(target));frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS)
    size=[int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))];cap.release()
    if size!=[1920,1080] or not fps or abs(frames/fps-sum(c['duration_s'] for c in clips))>.3:
        raise RuntimeError('Highlight video metadata validation failed')
    published=dest/'highlights.mp4'
    try:target.replace(published)
    except PermissionError:
        published=dest/('highlights_'+str(time.time_ns())+'.mp4')
        target.replace(published)
    target=published
    write(dest/'highlights_manifest.json',dict(clips=clips,width=1920,height=1080,fps=fps,frames=frames,
                                             duration_s=frames/fps,all_main_frames_are_actual_carla=True,video_file=target.name))
    print('HIGHLIGHTS_READY',target,frames/fps,flush=True)


if __name__=='__main__':build()
