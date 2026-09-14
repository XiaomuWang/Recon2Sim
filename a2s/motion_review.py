"""Build side-by-side CARLA motion evidence, kept separate from official reports."""
import argparse
import csv
import html
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .common import PROJECT, WORKSPACE, read, write

FONT='C:/Windows/Fonts/msyh.ttc'
BG='#0b1220'; CARD='#142238'; TEXT='#edf5ff'; MUTED='#97acc4'; TEAL='#50dfc5'; ORANGE='#ffbe79'
NAMES={'0508656':'骑行目标 · 变道与速度跟踪','019742':'逆行骑行者 · 朝向与路径跟踪','024388':'行人穿越 · 原生双腿步态'}
TARGET_NAMES={'0508656':'前方骑行目标','019742':'逆行骑行目标','024388':'横穿行人 1（画面中央）'}


def label(im,xy,text,size=20,color=TEXT):
    ImageDraw.Draw(im).text(xy,text,font=ImageFont.truetype(FONT,size),fill=color)


def rows(path):
    with path.open(encoding='utf-8-sig') as f:
        return [{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]


def graph(im,box,series,colors,title,unit,zero=True):
    d=ImageDraw.Draw(im); x,y,w,h=box
    d.rounded_rectangle((x,y,x+w,y+h),12,fill=CARD)
    label(im,(x+16,y+10),title,20);label(im,(x+w-100,y+13),unit,16,MUTED)
    low=min(min(v) for v in series);high=max(max(v) for v in series)
    if zero: low=min(0,low)
    span=max(.1,high-low);lo=0 if zero and low==0 else low-.1*span;hi=high+.1*span
    for i in range(3):
        yy=y+55+(h-85)*i/2;d.line((x+55,yy,x+w-15,yy),fill='#2b3d55')
        label(im,(x+8,yy-10),f'{hi-(hi-lo)*i/2:.1f}',13,MUTED)
    for values,color in zip(series,colors):
        pts=[(x+55+(w-70)*i/max(1,len(values)-1),y+55+(h-85)*(hi-v)/(hi-lo)) for i,v in enumerate(values)]
        d.line(pts,fill=color,width=3)


def build(sid,tag,baseline_tag=None):
    src=PROJECT/'outputs'/sid/'validation/motion_pilot'/tag
    baseline_src=PROJECT/'outputs'/sid/'validation/motion_pilot'/(baseline_tag or tag)/'baseline'
    before,after=read(baseline_src/'run.json'),read(src/'optimized/run.json')
    for key in ('target','hz','start','duration','reference_sha256','loaded_map'):
        if before[key]!=after[key]: raise ValueError('Before/after mismatch: '+key)
    if not before['success'] or not after['success']:raise ValueError('Both captures must complete')
    telemetry=rows(src/'optimized/telemetry.csv'); n=len(telemetry)
    if len(rows(baseline_src/'telemetry.csv'))!=n:raise ValueError('Capture lengths differ')
    dest=PROJECT/'outputs/motion_review';dest.mkdir(exist_ok=True)
    base=Image.new('RGB',(1600,1000),BG);d=ImageDraw.Draw(base)
    label(base,(28,20),'Recon2Sim  /  运动优化试验',18,TEAL)
    label(base,(28,53),NAMES[sid],32)
    label(base,(1040,25),f'CASE {sid}  ·  {after["hz"]} Hz  ·  CARLA 0.9.15',18,MUTED)
    label(base,(28,106),'01  优化前 · 按记录位姿平移',22,ORANGE)
    label(base,(814,106),'02  优化后 · 原生运动控制',22,TEAL)
    label(base,(28,582),'相同地图、时间轴与观察机位；右侧仅对指定目标启用新控制。',17,MUTED)
    label(base,(28,614),'观察目标：'+TARGET_NAMES[sid],18)
    graph(base,(28,657,493,233),[[r['reference_speed'] for r in telemetry],[r['speed'] for r in telemetry]],
          [ORANGE,TEAL],'目标速度 · 参考 / 实际','m/s')
    graph(base,(549,657,493,233),[[r['position_error'] for r in telemetry]],[TEAL],'轨迹位置偏差','m')
    unwrapped_yaw=np.degrees(np.unwrap(np.radians([r['yaw'] for r in telemetry]))).tolist()
    graph(base,(1070,657,502,233),[unwrapped_yaw],[TEAL],'实际偏航角 · 连续显示','°',zero=False)
    m=after['metrics'];status='达到本次跟踪阈值' if after['tracking_accepted'] else '尚未达到跟踪阈值'
    label(base,(28,910),f'{status}   ·   位置 P95 {m["position_p95_m"]:.2f} m   ·   最大 {m["position_max_m"]:.2f} m   ·   偏航 P95 {m["yaw_p95_deg"]:.2f}°',21)
    note='已检测到左右腿骨骼变化' if after.get('gait_detected') else '原生车辆物理控制；无逐帧位置纠偏'
    label(base,(28,950),note+'  |  本片段不代表全部目标或碰撞动力学已验证',17,MUTED)
    exe=str(next((WORKSPACE/'dynamic_data').glob('*/runtime/ffmpeg.exe')))
    video=dest/(sid+'.mp4')
    with (dest/(sid+'_encode.log')).open('w') as log:
        p=subprocess.Popen([exe,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
            '-s','1600x1000','-r',str(after['hz']),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','20',
            '-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE,stderr=log)
        try:
            for i,row in enumerate(telemetry):
                im=base.copy()
                for mode,x in [('baseline',28),('optimized',814)]:
                    folder=baseline_src if mode=='baseline' else src/mode
                    frame=Image.open(folder/'close'/f'{i:06d}.jpg').convert('RGB').resize((758,426),Image.Resampling.LANCZOS)
                    im.paste(frame,(x,146))
                    top=Image.open(folder/'top'/f'{i:06d}.jpg').convert('RGB').resize((200,112),Image.Resampling.LANCZOS)
                    im.paste(top,(x+548,450))
                    ImageDraw.Draw(im).rectangle((x+548,450,x+748,562),outline=TEAL,width=2)
                label(im,(1220,610),f't = {row["t"]:.2f} s',18,TEAL)
                for x,w in [(28,493),(549,493),(1070,502)]:
                    cx=x+55+(w-70)*i/max(1,n-1)
                    ImageDraw.Draw(im).line((cx,708,cx,860),fill='#ffffff',width=1)
                if i==n//2:im.save(dest/(sid+'.jpg'),quality=95)
                p.stdin.write(im.tobytes())
        finally:p.stdin.close()
        if p.wait()!=0:raise RuntimeError('FFmpeg encode failed')
    summary=dict(after,before_metrics=before['metrics'],before_gait_detected=before.get('gait_detected'),
                 video=sid+'.mp4',poster=sid+'.jpg',tag=tag,baseline_tag=baseline_tag or tag)
    write(dest/(sid+'.json'),summary)
    return summary


def page():
    dest=PROJECT/'outputs/motion_review';cards=[]
    for sid in ('024388','0508656','019742'):
        path=dest/(sid+'.json')
        if not path.exists():continue
        r=read(path);m=r['metrics']
        cards.append(f'''<section><div class="eyebrow">CASE {sid} · {TARGET_NAMES[sid]}</div>
<h2>{NAMES[sid]}</h2><video controls preload="metadata" poster="{sid}.jpg" src="{sid}.mp4"></video>
<div class="metrics"><span>位置 P95 <b>{m['position_p95_m']:.2f} m</b></span><span>最大位置偏差 <b>{m['position_max_m']:.2f} m</b></span>
<span>偏航 P95 <b>{m['yaw_p95_deg']:.2f}°</b></span><span>{'跟踪通过' if r['tracking_accepted'] else '跟踪待优化'}</span></div>
<p>左：原有位姿回放；右：原生控制。两侧使用相同参考机位，角落显示路网俯视参考。
<a href="{sid}.json">查看试验记录</a></p></section>''')
    doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Recon2Sim · 运动优化试验</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#edf5ff;font-family:"Microsoft YaHei",sans-serif}
main{max-width:1400px;margin:auto;padding:42px 28px}.eyebrow{color:#50dfc5;font-size:14px;letter-spacing:1px}h1{font-size:36px;margin:14px 0}h2{font-size:24px;font-weight:500}
p{color:#a4b5ca;line-height:1.9}a{color:#50dfc5}section{background:#111e30;border:1px solid #263951;border-radius:18px;padding:24px;margin-top:30px}
video{width:100%;display:block;border-radius:10px;background:black;max-height:76vh}.metrics{display:flex;gap:28px;flex-wrap:wrap;padding:20px 0 0;color:#a4b5ca}.metrics b{color:white;margin-left:8px}
.note{border-left:3px solid #ffbe79;padding:8px 18px;background:#172335}
</style><main><div class="eyebrow">RECON2SIM / MOTION LAB</div><h1>让重建目标自然运动</h1>
<p>保留事故轨迹与场景，在 CARLA 中验证骑行目标转向和行人原生步态。每段视频均包含优化前后对照、俯视参考和实际运行数据。</p>
<p class="note">这是独立试验页，正式七组汇报尚未替换。仅指定目标启用新控制；轨迹跟踪与骨骼变化的通过不等于全部事故碰撞动力学通过。</p>'''+''.join(cards)+'''<p><a href="reference_audit.json">查看原七组目标轨迹筛查</a> · <a href="../index.html">返回正式汇报</a></p></main></html>'''
    (dest/'index.html').write_text(doc,encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--scene',choices=list(NAMES));p.add_argument('--tag',default='review1')
    p.add_argument('--baseline-tag',help='Reuse a separately captured, matching baseline')
    args=p.parse_args()
    if args.scene:build(args.scene,args.tag,args.baseline_tag)
    page()
