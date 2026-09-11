from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,zipfile
P=Path('environment_reconstruction_014346');f='C:/Windows/Fonts/msyh.ttc';font=ImageFont.truetype(f,27);small=ImageFont.truetype(f,19);big=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',38)
im=Image.new('RGB',(1800,1350),(19,28,31));d=ImageDraw.Draw(im)
d.text((40,25),'014346  /  工地便道环境复原',font=big,fill=(234,238,227));d.text((42,80),'四路视频参照  ·  静态环境  ·  FBX + OpenDRIVE  ·  米制局部坐标',font=small,fill=(163,193,179))
for i,(n,label) in enumerate([('01_forward','前向 · 便道、挡墙、前方弯道'),('02_rear','后向 · 入口回看与工地开口'),('04_left','左向 · 挂藤挡墙与波形护栏'),('03_gate','右向 · 工地驶出口与围挡断口')]):
 x=40+i%2*880;y=135+i//2*575
 pic=Image.open(P/'renders'/(n+'.png'));pic=pic.resize((840,525),Image.Resampling.LANCZOS);im.paste(pic,(x,y))
 d.text((x,y+533),label,font=font,fill=(222,230,222))
d.text((42,1301),'依据可见要素复原；尺度与遮挡区域为估计。预览来自实际交付模型，并非测绘成果。',font=small,fill=(166,187,177))
im.save(P/'renders/four_views_overview.jpg',quality=94)
# Reusable file manifest, with hash checks for primary assets.
files={}
for name in ['NanshanGate014346.fbx','NanshanGate014346.xodr','NanshanGate014346.blend']:
 q=P/name;files[name]={'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}
manifest={'name':'NanshanGate014346','created':'2026-09-08','type':'CARLA source assets; not cooked map','files':files,'source_views':['front','rear','left','right'],'vehicles_included':False,'survey_grade':False,'road_network_scope':'210m access road with construction driveway junction; boulevard is decorative context','fbx_validation':json.loads((P/'validation/fbx_validation.json').read_text()),'carla_validation_summary':{k:v for k,v in json.loads((P/'validation/carla_validation.json').read_text()).items() if k not in ['junction_endpoint_checks']}}
(P/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
# Root folder can be placed directly under CARLA/Import.
zipname=P/'NanshanGate014346_CARLA_Source.zip'
with zipfile.ZipFile(zipname,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for q in sorted(P.rglob('*')):
  if not q.is_file():continue
  rel=q.relative_to(P)
  if any(v in ['runtime','__pycache__'] for v in rel.parts):continue
  if q.suffix in ['.zip','.blend1','.log','.pyc']:continue
  z.write(q,Path('NanshanGate014346Package')/rel)
with zipfile.ZipFile(zipname) as z:
 assert z.testzip() is None
 print('ZIP',zipname,'bytes',zipname.stat().st_size,'files',len(z.namelist()))
print('MAIN FILES',json.dumps(files,indent=2))
