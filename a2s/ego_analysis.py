"""Reproducible ego metrics from reconstructed trajectories, not vehicle CAN measurements."""
import csv
import numpy as np
from scipy.signal import savgol_filter
from .common import PROJECT,IDS,read,write,tracks


def analyze(sid):
    out=PROJECT/'outputs'/sid;cfg=read(out/'scene_config.json');data=tracks(out/'trajectories.csv');ego=data[cfg['ego_actor_id']]
    raw_t=np.array([r['replay_time_s'] for r in ego]);t=np.arange(raw_t[0],raw_t[-1]+.00001,.1)
    x=np.interp(t,raw_t,[r['x'] for r in ego]);y=np.interp(t,raw_t,[r['y'] for r in ego])
    v=np.interp(t,raw_t,[r['speed'] for r in ego])
    smooth=np.maximum(0,savgol_filter(v,11,2,mode='interp')) if len(v)>=11 else v
    a=np.gradient(smooth,t);distance=np.r_[0,np.cumsum(np.hypot(np.diff(x),np.diff(y)))]
    stopped=v<.1;stops=[];begin=None
    for i,flag in enumerate(stopped):
        if flag and begin is None:begin=i
        if begin is not None and (not flag or i==len(t)-1):
            end=i if not flag else len(t)-1
            if t[end]-t[begin]>=1:stops.append(dict(start_s=float(t[begin]),end_s=float(t[end]),duration_s=float(t[end]-t[begin])))
            begin=None
    nearest=[]
    for i,time in enumerate(t):
        distances=[]
        for aid in cfg['accident_actor_ids']:
            rows=data[aid]
            if rows[0]['replay_time_s']<=time<=rows[-1]['replay_time_s']:
                at=[r['replay_time_s'] for r in rows]
                distances.append(np.hypot(x[i]-np.interp(time,at,[r['x'] for r in rows]),y[i]-np.interp(time,at,[r['y'] for r in rows])))
        nearest.append(float(min(distances)) if distances else None)
    summary=dict(scene_id=sid,duration_s=cfg['duration_s'],distance_m=float(distance[-1]),
        peak_speed_kmh=float(v.max()*3.6),mean_speed_kmh=float(distance[-1]/(t[-1]-t[0])*3.6),
        maximum_acceleration_m_s2=float(a.max()),maximum_deceleration_m_s2=float(a.min()),
        stop_count=len(stops),stopped_duration_s=sum(s['duration_s'] for s in stops),stops=stops,
        minimum_related_actor_center_distance_m=min((d for d in nearest if d is not None),default=None),
        method='Reconstructed metric trajectory; 10 Hz interpolation; acceleration = derivative of speed after 11-point quadratic Savitzky-Golay smoothing (1.0 s span). Stops: speed <0.1 m/s for >=1 s.',
        limitations='Estimated scene trajectories, not measured CAN/IMU. Center distance is not bumper clearance or TTC. Kinematic replay acceleration is not physical controller response.')
    samples=[dict(t=round(float(tt),3),speed_kmh=float(vv*3.6),acceleration_m_s2=float(aa),distance_m=float(dd),
                  related_center_distance_m=nn,x=float(xx),y=float(yy)) for tt,vv,aa,dd,nn,xx,yy in zip(t,v,a,distance,nearest,x,y)]
    folder=out/'analysis';folder.mkdir(exist_ok=True);write(folder/'ego_metrics.json',dict(summary=summary,samples=samples))
    with (folder/'ego_metrics.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(samples[0]));w.writeheader();w.writerows(samples)
    plot(folder,summary,t,v*3.6,a,distance,cfg)
    return dict(summary=summary,samples=samples)


def plot(folder,summary,t,v,a,distance,cfg):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    plt.rcParams['font.sans-serif']=['Microsoft YaHei'];plt.rcParams['axes.unicode_minus']=False
    fig,axs=plt.subplots(3,1,figsize=(13.3,7.5),sharex=True,gridspec_kw={'hspace':.22})
    for ax,values,label,color in zip(axs,[v,a,distance],['速度 / km/h','加速度 / m/s²','累计路程 / m'],['#008c9c','#d67b27','#3366ac']):
        ax.plot(t,values,color=color,lw=1.8);ax.set_ylabel(label);ax.grid(alpha=.18);ax.spines[['top','right']].set_visible(False)
        for s in summary['stops']:ax.axvspan(s['start_s'],s['end_s'],color='#879aa5',alpha=.12)
    axs[1].axhline(0,color='#6e7a83',lw=.6);axs[-1].set_xlabel('重建回放时间 / s');axs[-1].set_xlim(t[0],t[-1])
    fig.suptitle(cfg['scene_id']+' · 主车运动分析',x=.09,ha='left',fontsize=18,fontweight='bold')
    fig.text(.09,.015,'数据为重建轨迹推导；加速度采用 1.0 s 窗口平滑。灰色区域为停车时段，不作为实车制动性能测量。',fontsize=10,color='#536573')
    fig.subplots_adjust(left=.09,right=.97,top=.9,bottom=.1);fig.savefig(folder/'ego_analysis.png',dpi=180,facecolor='white');plt.close(fig)

if __name__=='__main__':
    for sid in IDS:analyze(sid);print('ANALYSIS',sid,flush=True)
