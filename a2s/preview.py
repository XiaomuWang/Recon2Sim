"""Six-panel evidence: four original views, XODR plan, and explicitly labelled FBX keyframe."""
import html
import math
import os
import shutil
import subprocess
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .common import PROJECT, WORKSPACE, VIEWS, IDS, read, write, tracks, interpolate

FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
SMALL=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)


def text(im,xy,s,color=(228,237,238),font=FONT):
    ImageDraw.Draw(im).text(xy,s,font=font,fill=color)


def fit(frame,w,h):
    if isinstance(frame,np.ndarray): frame=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
    frame=frame.copy();frame.thumbnail((w,h));out=Image.new('RGB',(w,h),(16,24,31))
    out.paste(frame,((w-frame.width)//2,(h-frame.height)//2));return out


def plan_base(out,size=(480,270)):
    wps=read(out/'validation/waypoints.json');xs=[p['x'] for p in wps];ys=[p['y'] for p in wps]
    scale=min((size[0]-30)/max(1,max(xs)-min(xs)),(size[1]-30)/max(1,max(ys)-min(ys)))
    cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2
    def point(x,y):return round(size[0]/2+(x-cx)*scale),round(size[1]/2+(y-cy)*scale)
    base=np.full((size[1],size[0],3),(23,34,37),np.uint8)
    for p in wps: cv2.circle(base,point(p['x'],p['y']),max(1,round(p['width']*scale/2)),(85,91,91),-1)
    return base,point,scale


def preview(sid,fps=4):
    out=PROJECT/'outputs'/sid; cfg=read(out/'scene_config.json');entities=read(out/'entity_mapping.json');data=tracks(out/'trajectories.csv')
    folder=out/'preview';folder.mkdir(exist_ok=True)
    base,point,scale=plan_base(out); meta=read(out/'validation/video_metadata.json')
    caps={v:cv2.VideoCapture(str(WORKSPACE/cfg['video_dir']/(v+'.mp4'))) for v in VIEWS}
    render_manifest=out/'validation/fbx/renders.json'
    renders=read(render_manifest) if render_manifest.exists() else []
    fbx_frames={r['file']:Image.open(out/'validation/fbx'/r['file']).convert('RGB') for r in renders}
    critical={'014346':17,'019742':110,'016955':114,'024388':64,'0512189':85,'0508656':82,'ANA031':26.8}[sid]
    exe=os.environ.get('FFMPEG_EXE') or shutil.which('ffmpeg')
    if not exe: exe=str(next((WORKSPACE/'dynamic_data').glob('*/runtime/ffmpeg.exe')))
    destination=folder/'six_panel_comparison.mp4';W,H=1440,660
    log=(folder/'encode.log').open('w')
    process=subprocess.Popen([exe,'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-',
        '-an','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(destination)],stdin=subprocess.PIPE,stderr=log)
    roles={e['actor_id']:e['role'] for e in entities['actors']};colors={'ego':(250,180,40),'accident_related':(248,85,76),'context':(69,190,220)}
    def make(t):
        image=Image.new('RGB',(W,H),(13,21,28));text(image,(16,10),f'{sid}  四视角原视频 / 静态路网 / ego 复原验证    回放 {t:.2f}s')
        text(image,(16,38),'黄色：ego    红色：事故相关目标    蓝色：其他目标    |    估计重建；右下为离线 FBX 关键帧，非 CARLA 实机',font=SMALL)
        for i,v in enumerate(VIEWS):
            col=i%2;row=i//2;x=col*480;y=70+row*295
            file_t=cfg['source_video_start_s']+t+cfg['camera_file_time_offsets_s'][v]
            text(image,(x+8,y),f'{v.upper()} 原视频  文件时间 {file_t:.2f}s',font=SMALL)
            frame=None
            if 0<=file_t<meta[v]['duration_s']-1/max(meta[v]['fps'],1):
                cap=caps[v]; cap.set(cv2.CAP_PROP_POS_MSEC,file_t*1000);ok,raw=cap.read()
                if ok: frame=fit(raw,480,270)
            if frame is None:
                frame=Image.new('RGB',(480,270),(25,28,33));text(frame,(26,100),'该时刻原视频无有效帧 / 已结束')
            image.paste(frame,(x,y+25))
        road=base.copy()
        for aid,rows in data.items():
            pose=interpolate(rows,t)
            if pose:
                x,y=point(pose['x'],pose['y']);c=colors[roles[aid]]
                cv2.circle(road,(x,y),4 if roles[aid]!='context' else 2,c,-1)
                if roles[aid]=='ego':
                    h=math.radians(pose['yaw_carla_deg']);cv2.line(road,(x,y),(round(x+14*math.cos(h)),round(y+14*math.sin(h))),c,2)
        image.paste(Image.fromarray(road),(960,95));text(image,(968,70),'XODR 全路网俯视图 + 当前全部有效目标',font=SMALL)
        if renders:
            r=min(renders,key=lambda r:abs(r['replay_time_s']-t));image.paste(fit(fbx_frames[r['file']],480,270),(960,390))
            text(image,(968,365),f'FBX离线关键帧 {r["replay_time_s"]:.2f}s（代理模型）',font=SMALL)
        else: text(image,(980,450),'FBX 渲染尚未生成')
        return image
    try:
        for i in range(int(cfg['duration_s']*fps)+1):
            t=i/fps;image=make(t);process.stdin.write(np.asarray(image).tobytes())
            if i==0: image.save(folder/'comparison_start.png')
            if i==round(critical*fps):image.save(folder/'comparison_incident.png')
        process.stdin.close()
        if process.wait()!=0: raise RuntimeError('ffmpeg failed; see '+str(folder/'encode.log'))
    finally:
        for c in caps.values():c.release()
        if process.poll() is None:process.terminate();process.wait()
        log.close()
    road_image=Image.fromarray(base);draw=ImageDraw.Draw(road_image)
    for aid,rows in data.items():
        if roles[aid]=='context': continue
        pts=[point(r['x'],r['y']) for r in rows[::5]]
        if len(pts)>1: draw.line(pts,fill=colors[roles[aid]],width=2)
    road_image.resize((1440,810)).save(folder/'road_topdown.png')
    write(folder/'preview_metadata.json',dict(duration_s=cfg['duration_s'],fps=fps,views=VIEWS,video='six_panel_comparison.mp4',
        panel6='nearest offline FBX keyframe; timestamp explicitly labelled',carla_footage=False))
    print('PREVIEW_COMPLETE',sid,flush=True)
    index()


def index():
    cards=[]
    for sid in IDS:
        out=PROJECT/'outputs'/sid
        if not (out/'scene_config.json').exists():continue
        s=read(out/'scene_config.json');e=read(out/'entity_mapping.json');v=read(out/'validation/offline_validation.json')
        cards.append(f'<article><h2>{sid} · {html.escape(s["map_name"])}</h2><p>{len(e["actors"])} 个目标 / {s["duration_s"]} 秒 / ego: {e["ego_actor_id"]}</p>'
        f'<p>事故相关：{html.escape(", ".join(e["accident_actor_ids"]))}</p>'
        f'<video controls preload="none" poster="{sid}/preview/comparison_incident.png" src="{sid}/preview/six_panel_comparison.mp4"></video>'
        f'<p><a href="{sid}/preview/road_topdown.png">路网俯视图</a> · <a href="{sid}/validation/fbx/fbx_aerial.png">FBX场景俯视图</a> · '
        f'<a href="{sid}/validation/fbx/ego_02.png">ego离线关键帧</a> · <a href="{sid}/validation/offline_validation.json">验证报告</a> · '
        f'<a href="{sid}/scene_config.json">场景配置</a> · <a href="{sid}/entity_mapping.json">实体映射</a> · <a href="{sid}/trajectories.csv">轨迹</a></p></article>')
    content='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Recon2Sim 七组复现验证</title>
<style>body{font:16px system-ui;background:#111d25;color:#dce8eb;max-width:1440px;margin:32px auto;padding:20px}article{background:#1b2b35;padding:24px;margin:24px 0;border-radius:12px}video{width:100%;background:#080e13}a{color:#68d6df}p{line-height:1.7}.note{padding:20px;background:#3b3324}</style>
<h1>七组事故场景 · 复现与验证</h1><p class="note">四路视频保留原始鱼眼画面；XODR 来自本次静态脚本重建。右下为实际导出 FBX 的离线关键帧，显示独立时间戳，车辆是估计尺寸代理模型。CARLA 运行记录保存在各组 validation/carla_xodr 或 carla_imported；离线预览不作为 CARLA 实机证据。全视频目标穷尽性和测量精度尚未验收。</p>'''+''.join(cards)+'</html>'
    (PROJECT/'outputs/index.html').write_text(content,encoding='utf-8')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--scene',default='all');p.add_argument('--fps',type=int,default=4);a=p.parse_args()
    for sid in IDS if a.scene=='all' else [a.scene]:preview(sid,a.fps)
