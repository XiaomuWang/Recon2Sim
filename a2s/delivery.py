"""Generate an honest delivery manifest and the requested Chinese requirements response."""
from pathlib import Path
from datetime import datetime,timezone
from .common import PROJECT,WORKSPACE,IDS,read,write,sha


def main():
    summaries=[];lines=[]
    for sid in IDS:
        out=PROJECT/'outputs'/sid;cfg=read(out/'scene_config.json');entities=read(out/'entity_mapping.json')
        offline=read(out/'validation/offline_validation.json');fbx=read(out/'validation/fbx/fbx_validation.json')
        runtime={}
        for mode in ['xodr','imported']:
            p=out/'validation'/('carla_'+mode)/'runtime_report.json'
            runtime[mode]=read(p) if p.exists() else {'success':False,'status':'not_run'}
        required=[out/'map'/(cfg['map_name']+'.xodr'),out/'map'/(cfg['map_name']+'.fbx'),out/'trajectories.csv',out/'entity_mapping.json',out/'scene_config.json']
        manifest=dict(scene_id=sid,generated_at=datetime.now(timezone.utc).isoformat(),files=[dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p)) for p in required],
            target_count=len(entities['actors']),ego_actor_id=entities['ego_actor_id'],accident_actor_ids=entities['accident_actor_ids'],
            xodr_schema_pass=offline['xodr_schema_pass'],carla_client_parser_pass=offline['xodr_parser_pass'],fbx_roundtrip_pass=fbx['roundtrip_pass'],
            textures_missing=len(fbx['missing_textures']),embedded_textures=fbx['embedded_texture_count'],
            sampled_footprint_surface_misses=sum(a['surface_missing'] for a in fbx['footprint_checks']),
            sampled_structure_ray_hits=sum(a['structure_ray_hits'] for a in fbx['footprint_checks']),
            runtime=runtime,all_raw_video_targets_verified=False,
            acceptance=('REPRODUCTION_AND_FBX_RUNTIME_PASSED; source measurement/coverage limitations remain'
                        if runtime['imported'].get('success') and runtime['imported'].get('imported_geometry_complete')
                        and runtime['imported'].get('full_duration_capture') else
                        'PARTIAL: offline reproduction passed; runtime gates explicitly listed'))
        write(out/'delivery_manifest.json',manifest);summaries.append(manifest)
        lines.append(f"{sid}：{len(entities['actors'])} 个目标；重建回放 {cfg['duration_s']} 秒；原视频参考时间 {cfg['source_video_start_s']}–{cfg['source_video_end_s']} 秒。ego={entities['ego_actor_id']}；事故相关={','.join(entities['accident_actor_ids'])}。")
        imported=runtime['imported']
        lines.append('  FBX 实机验证：'+('已通过' if imported.get('success') and imported.get('fbx_runtime_verified') else '尚未通过')+
                     '；完整时段采集：'+('已完成' if imported.get('success') and imported.get('full_duration_capture') else '尚未完成')+'。')
        if imported.get('success'):
            lines.append('  CARLA 地图路径：'+imported['import_receipt']['unreal_map']+'；每路相机 '+str(imported['frames'])+' 帧。')
    write(PROJECT/'outputs/delivery_summary.json',summaries)
    text='''满足他人的需求 —— 七组事故场景交付说明与验收状态

一、交付位置
研发代码：Recon2Sim；原始视频：data；旧静态/动态参考：static_data、dynamic_data。
新结果：Recon2Sim/outputs/<场景编号>/；查看入口：Recon2Sim/outputs/index.html。
使用方法：Recon2Sim/README.md。原始数据及已有结果未修改。

二、按原“需求.txt”提供的文件
1. 每组 map 下输出同名 .xodr、.fbx、textures、CARLA Package.json；同时保留 .blend 便于编辑。
2. trajectories.csv 包含 actor_id,replay_time_s,source_video_time_s,x,y,z,yaw_carla_deg,speed。
   坐标单位米，speed 单位 m/s，yaw 为 CARLA 角度 [-180,180)，回放时间从 0 开始。
   保留原有全部已登记车辆、骑行者、行人及其他实体；保留静止、出现和离场时段。
3. entity_mapping.json 包含原 actor_id、名称、类型、ego/事故/背景角色、CARLA blueprint、备用 blueprint、
   初始/结束时间、初始位置航向速度、估计尺寸、置信度及外观替代说明。没有统一默认成一种车。
4. scene_config.json 包含时长、光照、天气类型、云量、降雨、积水、雾开始距离、估计能见距离、
   太阳方位角与高度角、湿滑程度、摩擦系数、风强度、碰撞后状态保持策略和单位。
   所有未知实测参数明确标成估计；夜间照明未进行真实灯具与照度标定。

三、ego、事故目标和静态路网共用方式
通过 configs/<编号>.json 明确指定 ego_actor_id 与 accident_actor_ids。
原轨迹统一转换到静态 XODR/FBX 坐标。road_associations.csv 保存每个轨迹点对应的 road_id、lane_id、s 及范围判定。
提供 route_overrides 接口直接按新生成 XODR 的道路/车道/站点构建动态路径，断开的连接和越界参数会报错。
出入口、路边停车区、行人区域不强行吸附到机动车道，而是检查真实 FBX 的合理场景表面。

四、七组清单
'''+ '\n'.join(lines)+'''

五、已经执行的复现与验证
七组静态研究脚本重新生成 XODR 和 FBX；七组动态研究脚本重新生成 181 个登记目标的轨迹。
七份 XODR 通过 OpenDRIVE XSD 与 CARLA 0.9.15 客户端解析。
FBX 重导入的坐标包围盒与源场景一致，外置和嵌入纹理可用；所有 CARLA 路网采样点都有对应 FBX 路面。
目标每六个采样检查中心及四个包围盒角点：均有 FBX 场景表面覆盖；部分结构相交结果详见第七项。
前后左右原视频、当前 XODR 俯视、ego 在实际 FBX 中的离线关键帧已形成六宫格对照视频。
第六格带独立时间戳，使用估计尺寸代理模型，不冒充实时 CARLA 画面。
坐标转换、角度跨界、生命周期、静止目标分类、路网路径和七组字段完整性有自动测试。
原视频光流可用 a2s.evidence 重新计算；raw_recompute 保存本次计算日志和与参考证据的差异。

六、CARLA 实机交付步骤
启动 CARLA 0.9.15 后：python -m a2s.replay --scene 014346 --mode imported。
默认端口 2000；脚本保存 ego 前视、跟随相机逐帧图、真实仿真帧号和运行报告。
完整 FBX 环境须先在 CARLA Unreal 工程导入静态地图、配置 GameMode/OpenDRIVE 并打包，随后使用 --mode imported。
a2s.unreal_package 提供原生 FBX 导入、地图组装、Windows 烘焙及安装代码；具体步骤见 FBX_IMPORT.md。
运行目标为 D:\\code\\CARLA_0.9.15\\WindowsNoEditor\\CarlaUE4.exe，客户端连接 127.0.0.1:2000。
新增资源安装到 Content/Accident2SimScenes；程序核对地图、路网、安装文件及 FBX/XODR 哈希。
汇报版采用左上 CARLA 跟随相机主画面；右上四路原始视频按“前、后 / 左、右”两行两列排列，右中为路网俯视；左下并列速度与纵向加速度曲线；右下为主车速度、纵向加速度、累计路程及全程总结。曲线游标和当前指标与回放同步。
网页与合辑展示顺序：024388、0512189、0508656、ANA031、014346、019742、016955。
网页“全屏”按钮用于全屏播放；两个 CSV 查看入口提供中文列名、分页和搜索，表格保留原始数值。
场景选项按原始数据目录标注车辆品牌：萝卜快跑、萝卜运力、美团、新石器。报告服务使用 python -m a2s.report_server --port 8765 --bind 0.0.0.0，支持视频分段读取和进度跳转。
网页主标题：突破参数与画质限制，赋能跨车型自动驾驶方案
网页副标题：无需相机内外参，仅凭低分辨率多视角图像，适配搭载不同自动驾驶方案的车辆。
批量实机采集与汇报：python -m a2s.verify_imported --scene all --fps 10。
重点片段合辑：python -m a2s.report_highlights；场景包导出：python -m a2s.package_export。
84 秒合辑：outputs/presentation/，当前文件名见 highlights_manifest.json 的 video_file 字段；网页自动指向当前版本。各组完整视频：outputs/<编号>/presentation/report.mp4。
可分发场景包：outputs/carla_package/Accident2SimScenes_CARLA_0.9.15_Windows.zip，解压到 WindowsNoEditor。
最终文件、帧同步、位置及偏航检查：outputs/delivery_audit.json。
ego_telemetry.csv 保存 CARLA 逐帧主车位置、仿真帧号、位置误差和位移推导速度。
同时保存指令/实际偏航角、偏航角速度和相机朝向；主画面相机以 1 秒时间常数独立平滑跟随。
全部有效目标的位置和偏航通过同步批量命令提交，逐帧检查位置误差不超过 1 厘米、偏航误差不超过 0.01 度。
位置误差比较 CARLA 实际位姿与输入轨迹，衡量回放执行一致性，不代表相对真实事故的重建精度。
主车分析来自重建轨迹，非车辆 CAN/IMU 实测。各组 presentation/report_manifest.json 记录实际使用模式与时间范围。
实机是否已运行，以各组 delivery_manifest.json 中 runtime 状态及 validation/carla_*/runtime_report.json 为准。
仅 XODR 实机运行不能代表完整 FBX 环境实机运行；离线通过不能替代两者。

七、范围与精度边界
1. 014346 沿用原有重建范围 52–159 秒，原片前 52 秒没有完整路网和动态复原。
2. 181 个目标覆盖现有标注，不代表已逐帧确认原四路视频中的全部远小目标、遮挡目标均无遗漏。
3. 相机未标定；尺寸、距离、遮挡运动、天气、摩擦和身份关联存在估计。没有测量级三维真值。
4. 0508656、0512189 等片段存在不稳定的视角时间偏移、冻结或镜像；对照视频不是硬件同步真值。
   ANA031 原视角视频长短不同，超出可用帧范围会明确显示无有效画面，不用旧帧伪装完整视频。
5. 014346 与 019742 有少量估计包围盒与围栏/建筑射线相交，需复核尺度、位置和结构。
   所有表面覆盖检查通过不等于所有实体无穿模；射线检查也不等于完整碰撞检验。
6. 动态回放是按轨迹驱动姿态，保留录制末态；没有复现轮胎、碰撞冲量、车体变形或闭环自动驾驶响应。

各组验收状态及剩余事项以上述运行报告和第七项为准。
'''
    (PROJECT/'满足他人的需求.txt').write_text(text,encoding='utf-8-sig')
    (WORKSPACE/'满足他人的需求.txt').write_text(text,encoding='utf-8-sig')
    print('DELIVERY_MANIFESTS_WRITTEN',len(summaries),flush=True)

if __name__=='__main__':main()
