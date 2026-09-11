# Recon2Sim

七组事故场景的重建代码与静态汇报主页。GitHub 仓库包含源码、研究脚本、配置、测试及 `docs/` 展示文件；不包含原始数据、CARLA 场景安装包、逐帧采集、Unreal 工程或预装运行时。完整复现仍需下文说明的外部数据与工具。

只查看汇报时，无需安装 CARLA：运行 `python -m a2s.report_server --bind 127.0.0.1 --port 8000 --directory docs`，打开 `http://127.0.0.1:8000/`。GitHub Pages 部署与更新方法见 [PUBLISHING.md](PUBLISHING.md)。

项目目录和名称已统一为 `Recon2Sim`。Python 模块入口继续使用 `a2s`；已安装的 CARLA 资源命名空间 `Accident2SimScenes` 和对应资源包文件名保留兼容。历史运行报告中的原始绝对路径保留为执行时记录。

七组事故视频的静态与动态复现代码。输入使用上一级的 `data`、`static_data`、`dynamic_data`，研发代码、隔离构建目录和新结果均在本项目中。原始输入不修改。

本项目已经重新执行七组静态建模、OpenDRIVE 导出及动态生成脚本。使用原始研究中人工复核的身份、事件、尺度与空间锚点，以及静态区域光流约束和 PCHIP 插值；**不是从未标定四路视频自动获得精确三维真值**。`recipes` 保存可编辑的原始研究算法，`a2s` 提供统一构建、坐标、实体映射、道路绑定、检查和回放实现。

## 快速使用

在本目录执行（本机已有 Python 3.8、CARLA 0.9.15 客户端及相关依赖；Blender/FFmpeg 自动查找整理后的输入目录中的运行时）：

```powershell
python -m unittest discover -s tests -v
python -m a2s.pipeline build --scene all --with-preview
```

这会依次执行静态 XODR、FBX → 动态轨迹 → 格式与道路检查 → FBX 重导入与关键帧渲染 → 六宫格对照视频。只处理一组时使用 `--scene 019742`。首次复现无需重新下载已有依赖，也无需连接服务器。

分步命令：

```powershell
python -m a2s.pipeline init
python -m a2s.pipeline static --scene all
python -m a2s.pipeline dynamic --scene all
python -m a2s.pipeline validate --scene all
python -m a2s.pipeline fbx-review --scene all
python -m a2s.preview --scene all --fps 4
python -m a2s.delivery
```

七组完整实机采集、汇报合成和验收入口：

```powershell
python -m a2s.verify_imported --scene all --host 127.0.0.1 --fps 10
python -m a2s.report_highlights
python -m a2s.package_export
python -m a2s.report_page
```

`outputs/presentation` 中的合辑汇集七组重点片段（当前文件名见 `highlights_manifest.json` 的 `video_file` 字段；旧文件被占用时自动发布新文件名，网页指向当前版本）；各组完整视频位于 `outputs/<编号>/presentation/report.mp4`。可分发资源包位于 `outputs/carla_package`，解压到另一套匹配的 CARLA 0.9.15 WindowsNoEditor 目录后，按包内完整地图路径加载。场景包只在七组完整网格和引擎路面检查通过后导出。

查看 `outputs/index.html`，或双击 `start_report_lan.cmd` 启动局域网报告服务。等价命令是在本目录执行 `python -m a2s.report_server --port 8765 --bind 0.0.0.0`。服务支持 HTTP Range 分段读取，视频可通过进度条跳转。本机仍访问 `http://127.0.0.1:8765/`；同网段设备访问 `http://10.192.41.46:8765/`。视频和下载资源由本机提供，查看期间保持电脑和服务运行。若电脑 IP 改变，请使用新的局域网 IPv4 地址。

报告服务已监听 `0.0.0.0:8765`。Windows 防火墙规则 `Accident2Sim Report LAN 8765` 已启用，仅允许 `10.192.41.0/24` 网段访问报告服务的 TCP 8765。服务根目录为 `outputs`，因此同网段访问者可获取其中的报告、视频、分析与场景下载资源；页面资源使用相对路径。已在本机通过回环地址和局域网地址检查页面及视频，均返回 HTTP 200；尚未从另一台设备测试。此设置不改变 CARLA 的 2000 端口。更换网段后需调整防火墙规则。

## 数据与产物

每组 `outputs/<编号>/` 包含：

| 文件 | 用途 |
| --- | --- |
| `map/<地图名>.xodr` | 本次重新生成的路网 |
| `map/<地图名>.fbx`、`map/textures` | 本次重新生成的网格、嵌入纹理及外置纹理 |
| `map/<地图名>.blend` | 可继续编辑的静态场景 |
| `map/<地图名>Package.json` | CARLA 地图导入清单 |
| `trajectories.csv` | 全部已登记目标的米制轨迹、CARLA 航向、速度和原视频时间 |
| `entity_mapping.json` | 原始 ID、ego/事故/背景角色、分类、模型及备选、尺寸、生命周期和初态 |
| `scene_config.json` | 数值天气、光照、湿度、雾、摩擦、时间范围、同步估计及限制 |
| `road_associations.csv` | 每个轨迹点在静态 XODR 中的道路、车道、s 和路网范围检查 |
| `source_anchors.json` | 人工复核关键点、身份与置信度 |
| `preview/six_panel_comparison.mp4` | 前后左右原始视频、XODR 俯视和带时间标识的离线 FBX 关键帧 |
| `preview/road_topdown.png` | 静态路网及 ego/事故目标轨迹 |
| `validation/fbx/ego_*.png` | 实际导出 FBX 重导入后的 ego 关键帧，目标为尺寸代理模型 |
| `validation/fbx/fbx_validation.json` | 网格回环、纹理、路面高度、目标覆盖与结构相交筛查 |
| `validation/offline_validation.json` | 格式、CARLA 客户端解析、目标保留及逐点路网检查 |
| `validation/legacy_comparison.json` | 本次动态重算与旧版最终结果差异 |
| `validation/carla_*/runtime_report.json` | 只有实际服务器运行时才产生的运行结果或明确失败原因 |

原始 CSV 字段各不相同，统一输出列为 `actor_id,replay_time_s,source_video_time_s,x,y,z,yaw_carla_deg,speed`。`x,y,z` 单位米，`speed` 单位 m/s，`yaw_carla_deg` 范围为 [-180,180)。`z` 表示包围盒落地中心，不是 CARLA Actor 的局部原点；回放按实际蓝图包围盒修正。

静态模型和 OpenDRIVE 使用右手米制坐标。导出 CSV 时仅进行一次 `x=X, y=-Y, z=Z, yaw=-degrees(h)` 转换；FBX 元数据保留单位，Unreal 导入转换至厘米。禁止把轨迹再乘 100 或再次反转 y。

## 指定 ego、事故目标和路网

编辑 `configs/<编号>.json` 中 `ego_actor_id` 和 `accident_actor_ids`。所有 ID 必须已经存在，ego 不能重复列为事故相关目标。现有默认角色来自原有事件记录，表示参与事故过程或影响 ego 的目标，不是责任认定。

默认完整保留 181 个已登记实体（包含静止、后方、侧面、出现和离场目标），不把所有目标转换为轿车。骑行者、行人与车辆分类独立；公交车、三轮车、清扫机器人和配送自车使用现有 stock 蓝图时仍存在外观差异，自定义模型建议保留在映射中。

`a2s.routes.sample_route` 可以直接在新生成的 XODR 上按 road_id/lane_id/s 构造轨迹。配置可增加 `route_overrides`，例如只修改 0512189 的 ego：

```json
{
  "route_overrides": {
    "ego": {
      "sections": [{"road_id": 10, "lane_id": -1, "s_start": 10, "s_end": 20}],
      "time_station": [[0, 0], [1, 10]],
      "lateral_offset_m": 0
    }
  }
}
```

示例只说明接口，不是事故事实。覆盖完整片段需填写完整时间范围及连接道路；断开的道路或越界 s 会报错。路网之外的停车区、出入口、行人区域保留原坐标，由 FBX 表面检查，不会自动吸附到车道中心改变事故过程。

## 从原始视频重新计算证据

```powershell
python -m a2s.evidence --scene all
```

这会从 `data` 的原视频重新执行各组原有静态区域掩膜、稀疏 Lucas-Kanade 光流、前后向一致性和 RANSAC 计算，结果放在 `raw_recompute`，并与已有证据逐项比较。光流只有像素速度，作为停走时序代理；米制尺度仍来自经复核的空间锚点。场景几何、目标身份和遮挡部分无法仅凭这一算法自动确定。

如需将重新计算的证据用于轨迹：先运行静态阶段，再运行 `python -m a2s.evidence --scene all --promote`，随后执行 `dynamic`、`validate`、`fbx-review` 和 `preview`。不要在 promote 之后再次运行 static，因为 static 会重新暂存原始证据。`--existing-dynamic` 可以只标准化已有最终场景，输出 provenance 会明确标记该模式。

## CARLA 运行与完整 FBX 环境

先启动 CARLA 0.9.15 服务，默认 `localhost:2000`。路网实机验证及关键阶段录制示例：

```powershell
python -m a2s.replay --scene 019742 --mode xodr --start 106 --duration 10 --fps 10
python -m a2s.replay --scene 019742 --mode xodr
```

第一条录关键阶段，第二条录完整重建时段。脚本生成路网、校验道路位置、按生命周期创建全部相关实体，禁用这些实体的物理模拟，按时间推进姿态，保存逐帧前视及跟随相机画面和帧时间表；异常时记录失败并清理自己创建的实体、传感器、摩擦体，恢复天气与同步设置。不能用该运动学回放评价制动力、轮胎动力学或碰撞后的物理响应。

CARLA 的 `generate_opendrive_world` 仅生成道路网格，不加载 FBX 建筑和环境。见[官方 OpenDRIVE standalone 文档](https://carla.readthedocs.io/en/0.9.15/adv_opendrive/)。完整地图必须通过 CARLA 的 Unreal 构建导入和打包流程；FBX 与 XODR 名称、原点和单位必须匹配。见[官方地图导入说明](https://carla.readthedocs.io/en/0.9.15/content_authoring_large_maps/)。

本机已建立原生命令行导入与烘焙流程，目标为 `D:\code\CARLA_0.9.15\WindowsNoEditor\CarlaUE4.exe`。本机 Unreal 4.26.2 编辑器用于生成资源，CARLA 运行程序仍使用用户的预编译 0.9.15。具体机制与文件位置见 [FBX_IMPORT.md](FBX_IMPORT.md)。

```powershell
python -m a2s.unreal_package build --scene all
python -m a2s.unreal_package install --scene all
python -m a2s.replay --scene 014346 --mode imported --host 127.0.0.1
python -m a2s.report_movie --scene 014346 --mode imported
python -m a2s.report_page
python -m a2s.delivery
```

`install` 写入预编译 CARLA 的 `Content/Accident2SimScenes`，需要该目录的写权限；不复制编辑器的旧版 CARLA 核心程序或内容。地图构建阶段的错误会直接中止，运行报告只在实际加载、轨迹推进与相机采集成功后标记通过。核查内容包括原始 FBX/XODR 哈希、安装资源哈希、完整场景对象数量、XODR 道路位置和引擎内 FBX 路面射线。各组当前完成状态以 `validation/carla_imported/runtime_report.json` 为准。

旧版 CARLA 导入工具会过滤名字含 light/sign 的网格或材质。本流程只在导入副本中对这些名称做等长替换，原始 FBX 与全部非名称字节不变，别名审计保存在 `validation/fbx_import_names.json`。烘焙采用明确的新增资产清单，避免只烘焙关卡而漏掉网格/纹理，也避免重新生成已由运行版提供的核心资产。

网格名中的 `_Tile_` 会让旧工具误判为大地图分块，因此普通铺装对象中的该标记也会等长改名为 `_Pave_`。每次完整导入先清理本组隔离工程的旧资产；单场景烘焙使用独立目录，成功后合并该组，保留其他关卡。

汇报视频为 1920×1080：左上为主车 CARLA 跟随主画面；右上四路参考视频按“前、后 / 左、右”两行两列排列，其下为路网俯视；左下速度与纵向加速度曲线一行两列；右下显示当前主车速度、纵向加速度、累计路程及全程总结。当前指标和曲线游标随回放同步，全程总结保持全时段统计。程序根据实际捕获模式标注是否已加载 FBX；完整时间范围见 `presentation/report_manifest.json`。

布局代码在 `a2s/report_movie.py`。先执行 `python -m a2s.report_movie --scene all --poster-only` 生成七组 `presentation/layout_preview.png` 预览，再执行 `python -m a2s.report_movie --scene all` 重新合成视频，最后执行 `python -m a2s.report_highlights` 与 `python -m a2s.report_page` 更新合辑和网页。可复用已录制的 CARLA 帧，无需重新运行仿真。网页的补充分析和验证记录默认折叠，展开后仍可查看、下载。

网页与合辑的展示顺序为 `024388 → 0512189 → 0508656 → ANA031 → 014346 → 019742 → 016955`，由 `REPORT_IDS` 管理。按钮名称为“全屏”。“查看主车分析 CSV”和“查看 CARLA 主车位姿 CSV”打开 `csv_viewer.html` 表格页，支持中文列名、搜索和分页，保留原始数值，也可下载原表。CSV 在线查看通过上述 HTTP 服务使用。

场景选项同时显示编号、原始资料中的车辆品牌和事件名称；品牌优先使用 `configs/<编号>.json` 的 `vehicle_brand`，缺省时从原始 `video_dir` 目录名读取，不使用 CARLA 代理车型作为品牌。

车辆位置与车身偏航通过 `apply_batch_sync` 同步提交，再推进仿真；所有有效目标均检查同一帧快照中的位置与偏航角。主画面使用独立相机，方向按 1 秒时间常数平滑跟随，让转弯时车身偏航可见。`ego_telemetry.csv` 包含实际偏航、指令偏航、偏航角速度、相机方向及匹配的仿真帧号。车身朝向采用轨迹中的 CARLA 偏航角，不受相机平滑影响。

最终交付检查：`python -m a2s.delivery_check`。它检查摄像头、位姿、视频与运行报告的对应关系，以及全部目标的偏航和位置执行误差。

## 已知验收边界

- 014346 的现有静态重建只支持原片 52–159 秒；前 52 秒道路与动态目标没有据此补造。
- ANA031 的各相机长度不同，按偏移对齐后部分时刻没有前、后或右视画面；对照视频明确显示无有效帧。
- 0508656、0512189 存在冻结、黑帧、镜像或随时间变化的视角偏移。没有完成逐帧标定同步；默认同文件时钟展示不等于硬件同步。配置中的固定偏移仅为已知估计。
- 181 个实体是旧版已经登记的全部实体，不等于已证明四路完整视频中没有漏掉任何目标；远小目标、遮挡身份仍需人工标注验收。
- 天气、能见度、摩擦和尺寸为明确标注的估计。CARLA `fog_distance` 是雾开始距离，另外输出的能见距离不是该字段的别名。
- 路网以外的目标具有 FBX 表面覆盖；014346 与 019742 中仍有少量估计包围盒与结构的射线相交，需复核模型尺寸、位置和可通行空间。该筛查不是完整碰撞检测。
- 离线 FBX 中的黄色/红色/蓝色模型是尺寸代理，不是 CARLA 原生实体。离线截图、原有 validation 文件以及单独的 XODR 运行都不能替代完整 XODR+FBX 的 CARLA 实机验收。
