# FBX 导入预编译 CARLA

目标程序：`D:\code\CARLA_0.9.15\WindowsNoEditor\CarlaUE4.exe`。
客户端连接 `127.0.0.1:2000`；`0.0.0.0:2000` 是服务端监听地址。

FBX 先经过本机 Unreal 4.26.2 编辑器的原生 ImportAssets 命令转换为网格、材质和纹理，再通过 CARLA 的 PrepareAssetsForCooking 生成关卡、碰撞和 OpenDRIVE 关联，最后烘焙为 WindowsNoEditor 资源。预编译服务加载的是烘焙后的地图。

开发代码在 `a2s/unreal_package.py`。隔离编辑器工程、导入中间结果、日志及烘焙文件在 `ue_import`；新资源命名空间是 `/Game/Accident2SimScenes`。编辑器采用本机现有 0.9.12 工程二进制，运行端保持 0.9.15，因此必须以运行端加载及摄像头证据确认兼容性。

在 Recon2Sim 目录执行：

```powershell
python -m a2s.unreal_package setup
python -m a2s.unreal_package build --scene 014346
python -m a2s.unreal_package install --scene 014346
python -m a2s.replay --scene 014346 --mode imported --duration 8
```

安装阶段仅复制 `Content\Accident2SimScenes` 下的新地图、网格、材质、纹理及对应 XODR，不复制旧版 CARLA 插件、程序或核心内容。若编译进程需要使用引擎自己的临时缓存目录，需使用具有相应文件权限的终端。

可通过 `--from-stage move`、`--from-stage prepare` 或 `--from-stage cook` 从已经检查完成的阶段续跑。不要在缺少对应前置资产时跳过阶段。

验证文件：

- `outputs/<编号>/validation/unreal_native_import.json`：编辑器关卡生成记录；不代表运行验证完成。
- `outputs/<编号>/validation/unreal_import_receipt.json`：实际安装文件及 FBX/XODR 哈希；不代表运行验证完成。
- `outputs/<编号>/validation/carla_imported/runtime_report.json`：运行地图名称、路网对齐误差、导入场景对象数量、参与者及摄像头采集结果。
- `outputs/<编号>/validation/carla_imported/ego_chase`：CARLA 实际 RGB 摄像头画面。

只有运行报告 `success` 与 `fbx_runtime_verified` 都为 true，且实际画面检查通过，才可认定该组完成了 FBX 在预编译 CARLA 中的运行验证。原有 `carla_xodr` 和 Blender 渲染证据不替代此项。

导入副本会将 mesh/material 名称中的 light、sign 等长替换为 lumen、bord，以绕过旧版工具的自动过滤。fbx_import_names.json 保存名称别名、哈希及非名称字节完全一致的检查结果。原始输出 FBX 不改动。
普通网格名中的 `_Tile_` 同样会等长替换为 `_Pave_`，防止人行道铺砖被误判为大地图分块。单场景重建使用独立烘焙目录，成功后合并本组结果，保留其他已完成关卡。
七组批量构建：python -m a2s.unreal_package build --scene all。

七组安装与运行验收：

```powershell
python -m a2s.unreal_package install --scene all
python -m a2s.verify_imported --scene all --host 127.0.0.1 --fps 10
python -m a2s.package_export
```

`outputs/carla_package/Accident2SimScenes_CARLA_0.9.15_Windows.zip` 是通过验证后生成的可复制资源包。新机器解压到 `WindowsNoEditor`，使用包内 `IMPORT_README.txt` 中的完整 `/Game/Accident2SimScenes/Maps/...` 路径加载。若重新构建 FBX 或 XODR，应重新安装并验证，不能沿用旧报告。

构建不生成网格距离场，保留原三角形网格、材质/纹理及三角形碰撞；大场景的 Embree 距离场生成会造成严重耗时。可用 A2S_UE_ENGINE、A2S_EDITOR_PROJECT、A2S_CARLA_ROOT 环境变量配置引擎、编辑器工程和运行版目录。
