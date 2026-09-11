from pathlib import Path
import json,zipfile,hashlib,math
from PIL import Image,ImageDraw,ImageFont,ImageOps
P=Path(__file__).resolve().parents[1];NAME='LuoboTurn024388';fontpath='C:/Windows/Fonts/msyh.ttc'
font=ImageFont.truetype(fontpath,24);small=ImageFont.truetype(fontpath,17);title=ImageFont.truetype(fontpath,38)
# Compact render index, only images from the final model.
im=Image.new('RGB',(1600,1160),(17,25,34));d=ImageDraw.Draw(im)
d.text((36,23),'024388  |  路口右转 · 静态环境',font=title,fill='#e6edf4')
d.text((38,80),'四视角参照复原  /  FBX + OpenDRIVE  /  不含车辆和人物  /  尺寸为估计',font=small,fill='#9eafbf')
items=[('01_approach_night','前视 · 夜景门楼'),('04_right_night','右视 · 转角商铺'),('00_aerial_day','鸟瞰 · 路口关系'),('03_left_day','左视 · 住宅街面')]
for i,(file,label) in enumerate(items):
 x=30+i%2*785;y=123+i//2*511
 pic=Image.open(P/'renders'/(file+'.png')).convert('RGB');pic=ImageOps.fit(pic,(755,472));im.paste(pic,(x,y));d.text((x,y+475),label,font=font,fill='#e6edf4')
im.save(P/'renders/preview_board.jpg',quality=94)
# Native scaled geometry diagram of OpenDRIVE route; source XY, not geographic north.
plan=Image.new('RGB',(1440,1100),'#111b26');dr=ImageDraw.Draw(plan)
dr.text((40,24),'道路连接与坐标 / OpenDRIVE',font=title,fill='#e5edf4')
dr.text((42,79),'局部米制坐标，非地理北向；绿色为 10 → 100 → 20 右转线路',font=small,fill='#9cacbc')
S=12;origin=(750,540)
def xy(p):return (origin[0]+p[0]*S,origin[1]-p[1]*S)
dr.rectangle([xy((-54,3.3)),xy((3.3,-3.3))],fill='#3a4755')
dr.rectangle([xy((-3.3,34)),xy((3.3,-34))],fill='#3a4755')
for sign in [-1,1]:
 pts=[(-12,sign*3.3),(-8.3,sign*3.3)]+[(-8.3+5*math.cos(math.pi/2-i*math.pi/2/30),sign*(8.3-5*math.sin(math.pi/2-i*math.pi/2/30))) for i in range(31)]+[(-3.3,sign*12),(3.3,sign*12),(3.3,0),(-12,0)]
 dr.polygon([xy(p) for p in pts],fill='#3a4755')
paths=json.loads((P/'validation/junction_paths.json').read_text())
for path in paths:dr.line([xy(p) for p in path['points']],fill='#6684a2',width=2)
route=[(-54,-1.65),(-12,-1.65)]+paths[0]['points']+[(-1.65,-34)]
dr.line([xy(p) for p in route],fill='#4bebbc',width=6)
for p,txt in [((-44,7),'10 进场道路'),((5,-30),'20 右转出场'),((5,28),'30 左侧横街'),((-19,-12),'100 右转连接'),((10,2),'门楼（不通行）')]:dr.text(xy(p),txt,font=small,fill='#e5edf4')
dr.line([xy((8.7,-7)),xy((8.7,7))],fill='#60a3ff',width=8)
dr.ellipse((origin[0]-5,origin[1]-5,origin[0]+5,origin[1]+5),fill='white');dr.text((origin[0]+8,origin[1]+8),'(0, 0)',font=small,fill='white')
dr.line([(1050,955),(1170,955)],fill='#dce6ef',width=3);dr.text((1068,965),'10 m',font=small,fill='#dce6ef')
dr.text((40,1040),'3 条道路分支 · 6 条连接 · 双向各一车道 · 车道宽 3.3 m · 右转半径 6.65 m（估计）',font=small,fill='#9cacbc')
plan.save(P/'renders/road_network.png')
# Refuse to package a known failing or incomplete asset set.
carla=json.loads((P/'validation/carla_validation.json').read_text());fbx=json.loads((P/'validation/fbx_validation.json').read_text())
assert carla['xsd_1_7_pass'] and carla['requested_right_turn_traversal_pass'] and not carla['errors']
assert fbx['fbx_reimport_pass'] and not fbx['road_surface_missing_hits'] and not fbx['junction_lane_band_missing_hits'] and not fbx['textures_missing']
for ext in ['fbx','xodr','blend']:assert (P/(NAME+'.'+ext)).stat().st_size>1000
for f in (P/'scripts').glob('*.py'):compile(f.read_text(encoding='utf-8-sig'),str(f),'exec')
files=[]
for f in P.rglob('*'):
 if not f.is_file():continue
 rel=f.relative_to(P)
 if '__pycache__' in rel.parts or any(p.endswith('.fbm') for p in rel.parts):continue
 if f.suffix in ['.log','.blend1','.zip','.pyc'] or f.name=='delivery_manifest.json':continue
 files.append(f)
files.sort()
manifest={'map':NAME,'asset_type':'FBX + OpenDRIVE source package; not a cooked CARLA map','source_video_views':['front','rear','left','right'],'accuracy':'uncalibrated, estimated-scale visual reconstruction','validation_summary':{'xsd':True,'carla_offline_version':carla['carla_version'],'right_turn_route':carla['right_turn_road_sequence'],'road_waypoint_samples':fbx['carla_waypoints_tested'],'lane_band_samples':fbx['junction_lane_band_samples'],'fbx_mesh_objects':fbx['imported_mesh_objects'],'embedded_textures':fbx['embedded_texture_count'],'unreal_runtime_tested':False},'files':[{'path':f.relative_to(P).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]}
(P/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');files.append(P/'delivery_manifest.json')
out=P/(NAME+'Package.zip')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for f in files:z.write(f,NAME+'Package/'+f.relative_to(P).as_posix())
with zipfile.ZipFile(out) as z:
 bad=z.testzip();assert bad is None
summary={'zip':str(out),'bytes':out.stat().st_size,'files':len(files),'archive_crc_pass':True,'zip_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
print(json.dumps(summary,indent=2))
