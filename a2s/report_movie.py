"""1920x1080 presentation composition with genuine CARLA footage as the hero."""
import argparse
import math
import subprocess
import bisect
import csv
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from .common import PROJECT,WORKSPACE,IDS,read,write,tracks,interpolate,sha
from .preview import plan_base

W,H=1920,1080
BG='#0b1220';CARD='#141f31';BORDER='#25364b';WHITE='#f0f6fc';MUTED='#9eb0c6';TEAL='#48d9d0';ORANGE='#f2ae62'
FONT='C:/Windows/Fonts/msyh.ttc';BOLD='C:/Windows/Fonts/msyhbd.ttc'
FONTS={n:ImageFont.truetype(FONT,n) for n in [13,14,15,16,17,18,20,22,24,28,32,40,46]}
FONTS['title']=ImageFont.truetype(BOLD,32)
NAMES={'014346':'货车横向驶出','019742':'避让逆行骑行者急刹','016955':'路口右转与清扫车交互','024388':'路口右转与行人穿越',
       '0512189':'拥堵路段变道','0508656':'变道后急刹','ANA031':'雨夜减速与停驶'}
CRITICAL={'014346':17,'019742':110,'016955':114,'024388':64,'0512189':85,'0508656':82,'ANA031':26.8}
REPORT_IDS=['157116','024388','0512189','0508656','ANA031','014346','019742','016955']
NAMES['157116']='直路行驶中两轮车交互与停车'
CRITICAL['157116']=15.7


def txt(im,xy,s,size=18,fill=WHITE):ImageDraw.Draw(im).text(xy,str(s),font=FONTS[size],fill=fill)


def card(im,box):ImageDraw.Draw(im).rounded_rectangle(box,radius=15,fill=CARD,outline=BORDER,width=1)


def fit(frame,size):
    if isinstance(frame,np.ndarray):frame=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
    frame=frame.copy();frame.thumbnail(size,Image.Resampling.LANCZOS);out=Image.new('RGB',size,'#070d16');out.paste(frame,((size[0]-frame.width)//2,(size[1]-frame.height)//2));return out


def chart(values,times,size,title,unit,color,zero=False):
    im=Image.new('RGB',size,CARD);d=ImageDraw.Draw(im);txt(im,(18,10),title,18);txt(im,(size[0]-100,14),unit,14,MUTED)
    l,r,top,bottom=48,size[0]-20,44,size[1]-29
    lo=min(0,min(values));hi=max(values);span=max(1,hi-lo);lo=lo-span*.10 if zero else 0;hi+=span*.12
    def pt(t,v):return (l+(r-l)*t/max(times[-1],.1),bottom-(v-lo)/(hi-lo)*(bottom-top))
    for value in np.linspace(lo,hi,3):
        yy=pt(0,value)[1];d.line((l,yy,r,yy),fill=BORDER);txt(im,(6,yy-8),f'{value:.0f}',13,MUTED)
    if zero:d.line((l,pt(0,0)[1],r,pt(0,0)[1]),fill='#66768a',width=1)
    d.line([pt(t,v) for t,v in zip(times,values)],fill=color,width=3)
    for t in np.linspace(0,times[-1],5):txt(im,(pt(t,lo)[0]-10,bottom+5),f'{t:.0f}',13,MUTED)
    return im,pt,(top,bottom)


def build(sid,fps=10,mode='imported',poster_only=False):
    root=PROJECT/'outputs'/sid;cfg=read(root/'scene_config.json');entities=read(root/'entity_mapping.json');data=tracks(root/'trajectories.csv')
    metrics=read(root/'analysis/ego_metrics.json');series=metrics['samples'];summary=metrics['summary'];times=[r['t'] for r in series]
    runtime_folder=root/'validation'/('carla_'+mode);report=read(runtime_folder/'runtime_report.json')
    if not report.get('success'):raise RuntimeError('Successful genuine CARLA capture required for '+sid)
    has_fbx=bool(report.get('fbx_runtime_verified'))
    if mode=='imported' and not has_fbx:raise RuntimeError('Verified imported FBX footage required')
    timeline=read(runtime_folder/'frame_times.json');capture_times=[r['replay_time_s'] for r in timeline]
    with (runtime_folder/'ego_telemetry.csv').open(encoding='utf-8-sig',newline='') as f:telemetry=list(csv.DictReader(f))
    start=capture_times[0];end=capture_times[-1];dest=root/'presentation';dest.mkdir(exist_ok=True)
    layout=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(layout)
    d.rounded_rectangle((40,20,115,51),radius=7,fill='#1e4650');txt(layout,(49,23),'场景复现',14,TEAL)
    txt(layout,(130,16),NAMES.get(sid,cfg.get('title',sid)), 'title');txt(layout,(42,65),f'CASE {sid}   /   CARLA 0.9.15 运行验证   /   {len(entities["actors"])} 个重建目标',17,MUTED)
    txt(layout,(1460,36),'ACCIDENT  /  RECONSTRUCTION',17,MUTED)
    d.line((40,96,1880,96),fill=BORDER,width=1)
    card(layout,(39,108,1241,816));txt(layout,(58,113),'仿真输出 · CARLA 事故场景复原回放',18)
    txt(layout,(862,115),'主车跟随视角 · XODR + FBX' if has_fbx else 'XODR 路网实机回放 · 未加载 FBX 环境',14,TEAL if has_fbx else ORANGE)
    # Right references are ordered front/rear, then left/right.
    card(layout,(1280,108,1880,514))
    txt(layout,(1297,112),'原始输入 · 四视角原始行车视频',18,'#89baff')
    for i,label in enumerate(['前视 FRONT','后视 REAR','左视 LEFT','右视 RIGHT']):
        x=1290+(i%2)*300;y=141+(i//2)*184
        txt(layout,(x+3,y),label,14,MUTED)
        d.rectangle((x-1,y+25,x+281,y+184),outline=BORDER)
    if cfg.get('source_recording'):
        d.rectangle((1280,108,1880,514),fill=BG);card(layout,(1280,108,1880,514))
        txt(layout,(1297,112),'原始输入 · 多视角录屏（完整界面）',18,'#89baff')
    txt(layout,(40,825),'主车运动分析',20,TEAL)
    txt(layout,(205,830),'基于重建轨迹 · 曲线与当前指标随回放同步更新',14,MUTED)
    d.line((590,841,1880,841),fill=BORDER,width=1)
    for x in [1280,1485,1690]:card(layout,(x,857,x+190,937))
    txt(layout,(1297,864),'主车速度',14,MUTED);txt(layout,(1502,864),'纵向加速度*',14,MUTED);txt(layout,(1707,864),'累计路程',14,MUTED)
    card(layout,(1280,526,1880,807));txt(layout,(1300,536),'重建输出 · 路网与目标位置 · 俯视图',18)
    txt(layout,(1300,780),'● ego',14,'#ffc140');txt(layout,(1380,780),'● 事故相关',14,'#ff6b64');txt(layout,(1510,780),'● 其他目标',14,'#519dcb')
    road_base,point,scale=plan_base(root,(560,210))
    speed,sp,(spt,spb)=chart([r['speed_kmh'] for r in series],times,(585,184),'主车速度曲线','km/h',TEAL)
    accel,ap,(apt,apb)=chart([r['acceleration_m_s2'] for r in series],times,(585,184),'主车纵向加速度曲线*','m/s²',ORANGE,True)
    layout.paste(speed,(40,857));layout.paste(accel,(655,857))
    card(layout,(1280,945,1880,1043));txt(layout,(1297,950),'全程总结',16,TEAL)
    txt(layout,(1297,974),f'行驶 {summary["distance_m"]:.1f} m   ·   最高速度 {summary["peak_speed_kmh"]:.1f} km/h',14)
    txt(layout,(1297,997),f'停车 {summary["stop_count"]} 次 / {summary["stopped_duration_s"]:.1f} s   ·   最大减速度 {abs(summary["maximum_deceleration_m_s2"]):.2f} m/s²',14)
    txt(layout,(1297,1021),'总结为全时段统计；上方指标随回放时间更新。',13,MUTED)
    txt(layout,(40,1052),'* 加速度由重建轨迹推导并作 1.0 s 平滑，非实测 CAN / IMU。原视频按已有时间估计对齐，参考窗 4 fps。',14,MUTED)
    if sid == '157116':
        d.rectangle((35,1048,1885,1079),fill=BG)
        txt(layout,(40,1052),'* 视觉估计重建：道路尺度、速度与姿态均未标定；倒地为姿态回放，未验证碰撞动力学。四视角原片 9.1 fps。',14,MUTED)
    if cfg.get('source_recording'):
        d.rectangle((40,1049,1880,1080),fill=BG)
        txt(layout,(40,1052),'* 视觉估计重建；界面速度读数辅助，非原始 CAN / IMU。倒地为姿态回放，未验证碰撞动力学；右侧保留完整录屏。',14,MUTED)
    reference_path=WORKSPACE/cfg['source_recording'] if cfg.get('source_recording') else root/'preview/six_panel_comparison.mp4'
    reference=cv2.VideoCapture(str(reference_path));ref_fps=reference.get(cv2.CAP_PROP_FPS);last_ref=-1;ref_frame=None
    roles={a['actor_id']:a['role'] for a in entities['actors']};colors={'ego':(255,193,64),'accident_related':(255,107,100),'context':(81,157,203)}
    exe=str(next((WORKSPACE/'dynamic_data').glob('*/runtime/ffmpeg.exe')))
    pending=dest/'report.pending.mp4'
    args=[exe,'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart','-threads','4',str(pending)]
    log=(dest/'encode.log').open('w') if not poster_only else None
    proc=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=log) if not poster_only else None
    poster_time=min(end,max(start,CRITICAL.get(sid,cfg.get('critical_time_s',cfg['duration_s']/2))));poster_index=round((poster_time-start)*fps)
    try:
        for step in ([poster_index] if poster_only else range(round((end-start)*fps)+1)):
            t=start+step/fps;im=layout.copy();draw=ImageDraw.Draw(im)
            ix=min(len(timeline)-1,max(0,bisect.bisect_left(capture_times,t)))
            if ix and abs(capture_times[ix-1]-t)<abs(capture_times[ix]-t):ix-=1
            hero=Image.open(runtime_folder/'ego_chase'/('%06d.'%timeline[ix]['index']+report.get('image_extension','png'))).convert('RGB');im.paste(fit(hero,(1200,675)),(40,140))
            # Small event annotation is tied to the same replay clock as the capture.
            events=[e['label_zh'] for e in cfg['events'] if e['start_t']<=t<=e['end_t']]
            event_text=' / '.join(events[:2]) if events else '连续轨迹回放'
            event_font=next((size for size in [17,16,15,14] if FONTS[size].getlength(event_text)<=560),14)
            draw.rounded_rectangle((63,159,650,201),radius=7,fill='#111d2c');txt(im,(77,168),event_text,event_font)
            draw.rounded_rectangle((1030,157,1220,199),radius=7,fill='#111d2c');txt(im,(1044,164),f'{t:06.1f} / {cfg["duration_s"]:.1f} s',20,TEAL)
            measured=telemetry[ix]
            if 'yaw_rate_deg_s' in measured:
                draw.rounded_rectangle((660,758,1220,802),radius=7,fill='#111d2c')
                txt(im,(678,768),f'偏航 {float(measured["yaw_carla_deg"]):+.1f}°   |   偏航角速度 {float(measured["yaw_rate_deg_s"]):+.1f}°/s',17,TEAL)
            ref_time=t+cfg['source_video_start_s'] if cfg.get('source_recording') else t
            ref_index=min(int(ref_time*ref_fps),int(reference.get(cv2.CAP_PROP_FRAME_COUNT))-1)
            if ref_index!=last_ref:
                if last_ref<0 or ref_index<last_ref or ref_index-last_ref>max(10,ref_fps*2):
                    reference.set(cv2.CAP_PROP_POS_FRAMES,ref_index)
                else:
                    for _ in range(ref_index-last_ref-1):
                        if not reference.grab():raise RuntimeError('Reference frame skipped unexpectedly')
                ok,ref_frame=reference.read()
                if not ok:raise RuntimeError('Reference composite frame missing')
                last_ref=ref_index
            if cfg.get('source_recording'):
                im.paste(fit(ref_frame,(580,348)),(1290,144))
                txt(im,(1300,491),f'录屏文件时间 {ref_time:.1f}s · 子视窗同步未标定',13,MUTED)
            else:
                for i,v in enumerate(['front','rear','left','right']):
                    xx=(i%2)*480;yy=95+(i//2)*295;crop=ref_frame[yy:yy+270,xx:xx+480]
                    x=1290+(i%2)*300;y=141+(i//2)*184
                    im.paste(fit(crop,(280,158)),(x,y+26))
                    file_t=t+cfg['source_video_start_s']+cfg['camera_file_time_offsets_s'][v]
                    txt(im,(x+205,y+3),f'{file_t:.1f}s',14,MUTED)
            j=min(len(series)-1,int(round(t*10)));now=series[j]
            txt(im,(1295,887),f'{now["speed_kmh"]:.1f}',32,TEAL);txt(im,(1423,916),'km/h',14,MUTED)
            txt(im,(1500,887),f'{now["acceleration_m_s2"]:+.1f}',32,ORANGE);txt(im,(1635,916),'m/s²',14,MUTED)
            txt(im,(1705,887),f'{now["distance_m"]:.0f}',32);txt(im,(1840,916),'m',14,MUTED)
            road=road_base.copy()
            for aid,rows in data.items():
                p=interpolate(rows,t)
                if p is None:continue
                center=point(p['x'],p['y']);color=colors[roles[aid]];radius=5 if roles[aid]!='context' else 3
                cv2.circle(road,center,radius,color,-1,cv2.LINE_AA)
                if roles[aid]=='ego':
                    cv2.circle(road,center,10,color,1,cv2.LINE_AA)
                    cv2.putText(road,'EGO',(center[0]+12,center[1]-8),cv2.FONT_HERSHEY_SIMPLEX,.42,color,1,cv2.LINE_AA)
            im.paste(Image.fromarray(road),(1300,566))
            for xy,func,value,bounds in [((40,857),sp,now['speed_kmh'],(spt,spb)),((655,857),ap,now['acceleration_m_s2'],(apt,apb))]:
                cx,cy=func(t,value);draw.line((xy[0]+cx,xy[1]+bounds[0],xy[0]+cx,xy[1]+bounds[1]),fill='#d9e5ee',width=1)
                draw.ellipse((xy[0]+cx-4,xy[1]+cy-4,xy[0]+cx+4,xy[1]+cy+4),fill=WHITE)
            if proc:proc.stdin.write(np.asarray(im).tobytes())
            if step==poster_index:im.save(dest/('layout_preview.png' if poster_only else 'report_poster.pending.png'))
            if step%300==0:print('COMPOSE',sid,round(t,1),flush=True)
        if proc:
            proc.stdin.close()
            if proc.wait()!=0:raise RuntimeError('Report video encoding failed')
    finally:
        reference.release()
        if log:log.close()
        if proc and proc.poll() is None:proc.terminate();proc.wait()
    if poster_only:return
    pending.replace(dest/'report.mp4')
    (dest/'report_poster.pending.png').replace(dest/'report_poster.png')
    write(dest/'report_manifest.json',dict(scene_id=sid,width=W,height=H,fps=fps,start_s=start,end_s=end,main_source='CARLA 0.9.15 '+mode+' runtime ego_chase',
        main_is_actual_carla=True,fbx_environment_loaded=has_fbx,source_recording_sha256=sha(reference_path) if cfg.get('source_recording') else None,reference_fps=ref_fps,reference_kind='source_recording' if cfg.get('source_recording') else 'four_views',analytics_source='reconstructed ego trajectory',full_duration=report['full_duration_capture'],
        body_yaw_verified=bool(report.get('max_actor_yaw_errors_deg')),chase_camera=report.get('chase_camera'),
        runtime_report_sha256=sha(runtime_folder/'runtime_report.json'),layout_version='report_v3_input_output_labels',
        layout=dict(hero='upper_left',references='complete source recording' if cfg.get('source_recording') else [['front','rear'],['left','right']],road='right_middle',charts=['lower_left_speed','lower_left_longitudinal_acceleration'],metrics='lower_right',summary='lower_right',analytics_group='主车运动分析',input_title='四视角原始行车视频',output_title='CARLA 事故场景复原回放')))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--scene',default='all');p.add_argument('--fps',type=int,default=10);p.add_argument('--mode',choices=['imported','xodr'],default='imported');p.add_argument('--poster-only',action='store_true');a=p.parse_args()
    for sid in IDS if a.scene=='all' else [a.scene]:build(sid,a.fps,a.mode,a.poster_only)
