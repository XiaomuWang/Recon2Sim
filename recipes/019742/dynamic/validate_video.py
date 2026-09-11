import cv2,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];v=P/'preview/UrbanBrake019742_TrajectoryPreview.mp4';cap=cv2.VideoCapture(str(v));assert cap.isOpened()
n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS);w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT));assert n==2671 and abs(fps-15)<.001 and (w,h)==(1280,720)
decoded=[]
for i in [0,1095,1658,2505,n-1]:
 cap.set(cv2.CAP_PROP_POS_FRAMES,i);ok,im=cap.read();assert ok and im.shape[:2]==(720,1280);decoded.append(i)
 if i==1658:cv2.imwrite(str(P/'preview/video_quality_check.png'),im)
cap.release();r={'file':v.name,'frames':n,'fps':fps,'duration_s':n/fps,'width':w,'height':h,'sample_frames_decoded':decoded,'pass':True,'not_carla_footage':True};(P/'validation/video_validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
