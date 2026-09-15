"""Verify and copy the local-only four-camera preview; never publish a page."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from a2s.common import PROJECT, read, sha, write
from a2s.local_preview import verify
import cv2
import shutil

root = PROJECT / 'outputs/157116'
verify('157116')
cap = cv2.VideoCapture(str(root / 'presentation/report.mp4'))
count = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    count += 1
cap.release()
assert count == 210, count
dest = PROJECT / 'outputs/fourview157116_preview'
dest.mkdir(exist_ok=True)
video = dest / '小马157116_四视角重建仿真预览_静态重建v2.mp4'
shutil.copy2(root / 'presentation/report.mp4', video)
shutil.copy2(root / 'presentation/report_poster.png', dest / '静态重建v2_封面.png')
write(dest / 'preview_manifest.json', dict(scene_id='157116', video=str(video),
    video_sha256=sha(video), decoded_frames=count, width=1920, height=1080, fps=10,
    duration_s=21, source_interval_s=[.9, 21.8], operation='copy_verified_local_video',
    validation=str(root / 'presentation/preview_audit.json')))
(dest / '审阅说明.txt').write_text(
    '小马157116四视角重建与CARLA预览\n\n'
    '21秒，1920×1080，10fps。网页同版式：CARLA主画面、四路原视频、路网俯视图、速度及加速度曲线。\n'
    '原片200帧、9.1fps；从0.9秒开始，跳过开头约0.88秒灰屏解码异常，结束于21.8秒。\n'
    '本次按原七组方法重做详细立面、逐片树叶、PBR材质、铺装及护栏；12个主要目标沿用既有轨迹。\n'
    '四路输入均为鱼眼；未提供内参、畸变和外参，原片保持原样，CARLA主画面为观察视角。\n'
    '尺度、车速、身份关联及姿态按画面估计，未做相机标定，也无实车CAN；车辆为现有车型代理，'
    '人员倒地是简化刚体姿态，未验证碰撞动力学。\n'
    'Verified local copy. Website publication is separate.\n', encoding='utf-8')
print('FULL_DECODE_PASS', count)
