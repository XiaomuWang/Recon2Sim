from pathlib import Path
import json,hashlib,zipfile,math
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];NAME='GreenRail016955'
fontpath='C:/Windows/Fonts/msyh.ttc'
def font(n):return ImageFont.truetype(fontpath,n)
def loadfit(file,w,h):
 im=Image.open(file).convert('RGB');im.thumbnail((w,h));out=Image.new('RGB',(w,h),(20,26,32));out.paste(im,((w-im.width)//2,(h-im.height)//2));return out
# Qualitative side-by-side evidence; does not imply calibrated camera alignment.
sheet=Image.new('RGB',(2240,880),(16,24,29));d=ImageDraw.Draw(sheet)
d.text((30,17),'016955  |  四视角环境参照',font=font(32),fill=(236,242,240))
d.text((30,60),'视频关键帧 / 交付模型渲染 · 相机与尺寸未经标定，比较静态要素关系',font=font(20),fill=(156,180,179))
pairs=[('前视：右转后道路','front_146_detail.png','02_exit_front.png'),('后视：院墙与高架','rear_146_detail.png','03_exit_rear.png'),('左视：院墙和蓝白楼','left_106_detail.png','04_approach_left.png'),('右视：高架与非机动车道','right_106_detail.png','05_approach_right.png')]
for i,(title,ref,render) in enumerate(pairs):
 x=i%2*1120;y=105+i//2*385
 d.text((x+18,y+4),title,font=font(24),fill=(117,219,187))
 sheet.paste(loadfit(P/'evidence'/ref,540,305),(x+15,y+48));sheet.paste(loadfit(P/'renders'/render,540,305),(x+563,y+48))
 d.text((x+18,y+356),'视频',font=font(17),fill=(174,192,194));d.text((x+567,y+356),'模型',font=font(17),fill=(174,192,194))
sheet.save(P/'renders/08_four_view_comparison.jpg',quality=94)

# Draw navigable geometry directly from CARLA samples, emphasizing the recorded two-turn path.
waypoints=json.loads((P/'validation/carla_waypoints.json').read_text());plan=Image.new('RGB',(1200,1180),(18,28,35));d=ImageDraw.Draw(plan)
d.text((40,25),'GreenRail016955  |  OpenDRIVE 路网',font=font(31),fill='white')
d.text((40,74),'局部右手坐标，单位米；两次右转路径以绿色标出',font=font(20),fill=(156,180,186))
def xy(x,y):return (int(90+(x+205)*3.15),int(170+(125-y)*2.85))
groups={}
for p in waypoints:groups.setdefault((p['road'],p['lane']),[]).append(p)
for (rid,lane),pts in groups.items():
 pts.sort(key=lambda p:p['s']);coords=[xy(*p['xyz_rh'][:2]) for p in pts]
 selected=(rid,lane) in [(10,-4),(103,-1),(20,-1),(201,-1),(30,1)]
 d.line(coords,fill=(81,220,160) if selected else (118,145,163),width=5 if selected else 2)
for title,x,y,dx,dy in [('第一处右转',-180,0,-145,-20),('第二处右转',0,0,-110,-52),('公交大道 · 10',-180,-145,-180,0),('沿高架道路 · 20',-94,0,-110,-42),('右转后道路 · 30',0,-130,20,0),('直行延续 · 31',45,0,-30,-35)]:
 xx,yy=xy(x,y);d.text((max(20,xx+dx),yy+dy),title,font=font(20),fill=(222,231,233))
d.line([xy(-205,-8.7),xy(75,-8.7)],fill=(215,180,112),width=4)
d.text((600,1110),'金色：高架位置（静态环境，不是可行车路网）',font=font(19),fill=(215,180,112))
plan.save(P/'renders/09_opendrive_plan.png')

c=json.loads((P/'validation/carla_validation.json').read_text());f=json.loads((P/'validation/fbx_validation.json').read_text())
assert c['xsd_1_7_pass'] and c['carla_offline_parse_pass'] and not c['errors']
for key in ['mesh_errors','textures_missing','road_surface_missing_hits','lane_inner_edge_missing_hits','lane_centres_blocked_below_3_5m','tree_bases_on_road']:assert not f[key],key
assert f['fbx_reimport_pass']
required=[NAME+'.fbx',NAME+'.xodr',NAME+'.blend',NAME+'Package.json','README_交付与CARLA导入.md']
for n in required:assert (P/n).is_file(),n
allowed={'textures','scripts','validation','evidence','renders'}
files=[p for p in P.rglob('*') if p.is_file() and ((p.parent==P and p.suffix in ['.fbx','.xodr','.blend','.json','.md']) or p.relative_to(P).parts[0] in allowed) and not any(s in p.parts for s in ['__pycache__']) and p.suffix not in ['.log','.pyc','.blend1'] and p.name!='delivery_manifest.json']
entries=[]
for p in sorted(files):
 entries.append(dict(path=p.relative_to(P).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
manifest=dict(map_name=NAME,artifact_type='FBX + OpenDRIVE source assets, not cooked CARLA map',source_views=['front','rear','left','right'],validation=dict(carla_offline=True,xsd_1_7=True,fbx_reimport=True,waypoints=f['carla_waypoints_tested'],lane_edge_samples=f['lane_inner_edges_tested'],runtime_tested=False),files=entries)
(P/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');files.append(P/'delivery_manifest.json')
dest=P/(NAME+'Package.zip')
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(files):z.write(p,NAME+'Package/'+p.relative_to(P).as_posix())
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
digest=hashlib.sha256(dest.read_bytes()).hexdigest();(P/(dest.name+'.sha256')).write_text(digest+'  '+dest.name+'\n')
print(json.dumps(dict(zip=str(dest),bytes=dest.stat().st_size,files=len(files),sha256=digest,fbx_bytes=(P/(NAME+'.fbx')).stat().st_size),indent=2))
