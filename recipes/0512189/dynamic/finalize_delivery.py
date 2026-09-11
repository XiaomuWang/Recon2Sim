# -*- coding: utf-8 -*-
from pathlib import Path
import json,html,hashlib,zipfile,cv2
P=Path(__file__).resolve().parents[1]
d=json.loads((P/'scenario.json').read_text(encoding='utf-8'))
audit=json.loads((P/'validation/trigger_audit.json').read_text(encoding='utf-8'))
assert audit['all_passed'];assert json.loads((P/'validation/protocol_tests.json').read_text())['pass'];assert json.loads((P/'validation/trajectory_validation.json').read_text())['overlap_pairs']==0
cap=cv2.VideoCapture(str(P/'preview/trajectory_replay.mp4'));assert cap.isOpened();n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS);fourcc=int(cap.get(cv2.CAP_PROP_FOURCC));codec=''.join(chr((fourcc>>(8*i))&255) for i in range(4));assert n==1201 and fps==10
checks=[]
for t in [0,51,105,119]:
 cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,im=cap.read();assert ok and im.shape==(900,1440,3) and im.std()>15;checks.append(t)
cap.release();(P/'validation/preview_validation.json').write_text(json.dumps({'frames':n,'fps':fps,'duration_s':n/fps,'codec':codec,'decoded_seconds':checks,'type':'diagram, not CARLA capture','pass':True},indent=2))
original=Path('C:/Users/Administrator/Desktop/模板/scenario - 2026-09-08T142648.948.xosc')
source_hash=hashlib.sha256(original.read_bytes()).hexdigest() if original.exists() else None
rows=''.join('<tr><td>'+html.escape(a['label'])+'</td><td><code>'+a['entity']+'</code></td><td>'+str(round(a['activation_s'],2))+'</td><td>'+('静止' if a['first_motion_s'] is None else str(round(a['first_motion_s'],2)))+'</td></tr>' for a in audit['files'][0]['actor_audit'])
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>美团 0512189 · 动态场景</title><style>body{margin:0;background:#0e1922;color:#e2ecec;font:16px/1.8 'Microsoft YaHei',sans-serif}main{max-width:1120px;margin:auto;padding:45px 28px}h1{font-size:34px;line-height:1.4}h2{margin-top:45px}p{color:#adbdc8}a{color:#88dac5}header{border-bottom:1px solid #33424a;padding-bottom:24px}.pill{display:inline-block;margin:5px 10px 5px 0;background:#1c3e43;padding:5px 14px;border-radius:30px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{padding:20px;background:#172933;border-radius:12px}video,img{width:100%;border-radius:12px}figure{margin:0}figcaption{font-size:14px;color:#a4bbc1}table{width:100%;border-collapse:collapse}th,td{text-align:left;border-bottom:1px solid #2c4049;padding:9px}th{background:#1e343c}code{font-size:13px}pre{background:#172933;padding:18px;overflow:auto}small{color:#91a8b2}@media(max-width:760px){.grid{grid-template-columns:1fr}h1{font-size:26px}}</style><main><header><small>MEITUAN · LA71AUB13S0512189 · 0814 变道</small><h1>动态目标恢复与场景回放</h1><span class="pill">34 个目标</span><span class="pill">120 秒</span><span class="pill">2,074 个事件</span><span class="pill">CARLA 0.9.15</span><p>前后左右视频参考；与此前 OpenDRIVE 共用世界坐标。每个目标已配置初始位置与独立时间事件。当前完成离线检查，尚未在 CARLA 0.9.15 引擎内实跑。</p></header><h2>导入入口</h2><div class="grid"><div class="card"><b>用户模板平台</b><p>保留模板的路线、速度与时间事件结构；角度形式与附件一致。</p><a href="MeituanLane0512189_Timeline.xosc">模板 XOSC</a> · <a href="MeituanLane0512189_Timeline_Radians.xosc">弧度 XOSC</a></div><div class="card"><b>CARLA / ScenarioRunner</b><p>官方 ScenarioRunner 选 SR015；视频时间轨迹回放选 Python。</p><a href="MeituanLane0512189_SR015.xosc">SR015 XOSC</a> · <a href="README.md">完整运行说明</a></div></div><h2>完整时间轴预览</h2><p>这是恢复轨迹的俯视示意，非 CARLA 录屏。播放可核对公交车、货车、自车变道与后段行人的出场时序。</p><video controls preload="metadata" poster="preview/timeline_105.png" src="preview/trajectory_replay.mp4"></video><h2>同一三维环境中的关键帧</h2><div class="grid">'''
for t,caption in [(51,'51 秒 · 绿色货运车与右侧厢式货车'),(86,'86 秒 · 自车向右移入外侧车道'),(105,'105 秒 · 公交车经过，自车再次缓行'),(118,'118 秒 · 左前方公交车及路侧行人')]:page+='<figure><img loading="lazy" src="preview/scene_%03d.png"><figcaption>%s（Blender 预览）</figcaption></figure>'%(t,caption)
page+='''</div><p><a href="preview/MeituanLane0512189_Animated.blend">下载可编辑三维动画</a> · <a href="逐目标触发清单.md">逐目标清单</a> · <a href="validation/trigger_audit.json">条件检查记录</a></p><h2>逐目标出场时间</h2><p>时间为仿真秒。运动统一比视频延后 0.30 秒；定位事件提前 0.20 秒。时间条件持续满足且只执行一次；不依赖其他车辆通过或碰撞触发。</p><table><thead><tr><th>视频目标</th><th>场景实体</th><th>出场定位</th><th>首次运动</th></tr></thead><tbody>'''+rows+'''</tbody></table><h2>最短启动步骤</h2><p>CARLA 0.9.15 已启动且已载入此前烘焙的 MeituanLane0512189 地图后，在本目录执行：</p><pre>python replay_carla.py --preflight
python replay_carla.py</pre><p>如仅检查道路与轨迹，可用 --road-only，它将替换当前世界，不含建筑和绿化。六个可选车辆外观模型需要先按 README 导入；默认原生车型与视频有差异。</p><small>尺度、遮挡轨迹和相机参数是视频参考估计；没有标定真值。检验范围与使用方法见 README 和 validation。</small></main></html>'''
(P/'START_HERE.html').write_text(page,encoding='utf-8')
script_names={'audit_triggers.py','audit_video.py','build_animated_preview.py','build_dynamic_assets.py','check_time.py','encode_preview.py','export_template.py','export_xosc.py','generate_scenario.py','measure_ego_flow.py','render_topdown.py','test_replay_protocol.py','validate_assets.py','validate_trajectories.py','finalize_delivery.py'}
files=[]
for f in P.rglob('*'):
 if not f.is_file():continue
 rel=f.relative_to(P)
 if '__pycache__' in rel.parts or f.suffix in ['.log','.blend1'] or f.name in ['protocol_run.json','manifest.json','trajectory_replay_mp4v.mp4','package_validation.json']:continue
 if rel.parts[0]=='scripts' and f.name not in script_names:continue
 files.append(f)
manifest={'name':'MeituanLane0512189 dynamic replay','target_carla':'0.9.15','runtime_verified':False,'source_template_sha256':source_hash,'actors':34,'duration_s':120,'poses':sum(len(a['samples']) for a in d['actors']),'events_per_timeline_xosc':2074,'condition_edge':'none','event_maximum_execution_count':1,'xosc_motion_offset_s':.30,'xosc_activation_lead_s':.20,'xosc_stop_s':120.60,'coordinates':d['coordinates'],'xodr_sha256':d['xodr_sha256'],'limitations':d['limitations'],'validation':'XML schema + event logic model + 7 fake-world protocol tests + offline map/estimated bbox + Blender FBX roundtrip. No CARLA 0.9.15 engine run.','files':[{'path':f.relative_to(P).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(files)]}
(P/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');files.append(P/'manifest.json')
zpath=P.parent/'MeituanLane0512189_Dynamic_CARLA0915.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in files:z.write(f,'MeituanLane0512189_Dynamic/'+f.relative_to(P).as_posix())
with zipfile.ZipFile(zpath) as z:assert z.testzip() is None
report={'zip':zpath.name,'bytes':zpath.stat().st_size,'files':len(files),'zip_crc_pass':True,'sha256':hashlib.sha256(zpath.read_bytes()).hexdigest(),'runtime_verified':False}
(P/'validation/package_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
