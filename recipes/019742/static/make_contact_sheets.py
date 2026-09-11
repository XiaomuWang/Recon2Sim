from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
P=Path('environment_reconstruction_019742');font='C:/Windows/Fonts/msyh.ttc';f=ImageFont.truetype(font,25);sm=ImageFont.truetype(font,18)
canvas=Image.new('RGB',(1600,1120),(22,28,34));d=ImageDraw.Draw(canvas)
d.text((32,16),'019742 | 城市道路环境 · 前后左右检查',font=f,fill=(234,239,244))
for i,(name,label) in enumerate([('01_forward','前视 · 行进方向'),('02_rear','后视 · 回看信号灯路口'),('03_left','左视 · 中央隔离栏与对向商铺'),('04_right','右视 · 宣传围栏与沿街商住楼')]):
 x=i%2*800;y=60+i//2*525;im=Image.open(P/'renders'/(name+'.png'));im.thumbnail((792,495));canvas.paste(im,(x+4,y+27));d.text((x+15,y),label,font=sm,fill=(229,234,239))
d.text((30,1100),'四路视频参照的视觉复原；尺度估计。无车辆、无人物。',font=sm,fill=(193,206,216));canvas.save(P/'renders/four_views_overview.jpg',quality=93)
# Original footage and actual render next to each other; not a calibrated reprojection claim.
comp=Image.new('RGB',(1280,4*435+80),(22,28,34));d=ImageDraw.Draw(comp);d.text((22,16),'视频依据 / 交付模型 · 同向参照（非标定重投影）',font=f,fill='white')
for i,(vid,render) in enumerate([('front','01_forward'),('rear','02_rear'),('left','03_left'),('right','04_right')]):
 import cv2
 root=next(Path('.').glob('*LNDEA7HF1SH019742*'));c=cv2.VideoCapture(str(root/(vid+'.mp4')));c.set(cv2.CAP_PROP_POS_MSEC,140000);ok,frame=c.read();c.release();y=80+i*435
 im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));im=im.resize((640,360));comp.paste(im,(0,y+40));r=Image.open(P/'renders'/(render+'.png'));r.thumbnail((640,400));comp.paste(r,(640,y+20));d.text((15,y),vid+' · 原视频 140s',font=sm,fill='white');d.text((655,y),'模型 · 同向环境',font=sm,fill='white')
comp.save(P/'evidence/video_model_comparison.jpg',quality=92)
