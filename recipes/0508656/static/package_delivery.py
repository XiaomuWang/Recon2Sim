from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,zipfile
P=Path(__file__).resolve().parents[1];NAME='MeituanBrake0508656'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',25);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19);title=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',38)
im=Image.new('RGB',(1800,1350),(18,32,32));d=ImageDraw.Draw(im)
d.text((42,26),'0508656  /  美团 · 变道后急刹环境',font=title,fill=(239,240,223));d.text((44,83),'四路视频参照  ·  环境模型  ·  FBX + OpenDRIVE  ·  不含车辆',font=small,fill=(177,205,183))
for i,(n,label) in enumerate([('01_forward','前向 / 中央绿篱与人行天桥'),('02_rear','后向 / 商住街区与来向道路'),('03_left','左向 / 隔离带及对侧住宅'),('04_right','右向 / 树木、商铺与路侧设施')]):
 x=40+(i%2)*880;y=135+(i//2)*572
 pic=Image.open(P/'renders'/(n+'.png')).resize((840,525),Image.Resampling.LANCZOS);im.paste(pic,(x,y));d.text((x,y+533),label,font=font,fill=(231,235,222))
d.text((42,1301),'预览来自交付模型。依据视频做视觉近似还原，尺寸与遮挡区域为估计；尚未在 Unreal 运行。',font=small,fill=(177,200,184))
im.save(P/'renders/four_views_overview.jpg',quality=94)
# Side-by-side evidence: views are semantic comparisons, not a calibrated reprojection.
im=Image.new('RGB',(1680,2010),(22,29,32));d=ImageDraw.Draw(im)
d.text((30,20),'视频证据 / 交付模型',font=title,fill='white')
d.text((30,76),'左：各路约120秒抽帧（非严格同步）    右：事件参考点模型预览（非像素配准）',font=small,fill=(180,194,196))
for i,(view,render) in enumerate([('front','01_forward'),('rear','02_rear'),('left','03_left'),('right','04_right')]):
 y=120+i*467
 for j,p in enumerate([P/'evidence'/f'{view}_120.jpg',P/'renders'/(render+'.png')]):
  pic=Image.open(p);pic.thumbnail((800,425));im.paste(pic,(30+j*825+(800-pic.width)//2,y+(425-pic.height)//2))
 d.text((30,y+430),view,font=small,fill='white')
im.save(P/'renders/video_model_comparison.jpg',quality=92)
f=json.loads((P/'validation/fbx_validation.json').read_text());c=json.loads((P/'validation/carla_validation.json').read_text())
assert f['fbx_reimport_pass'] and not f['textures_missing'] and not f['static_obstruction_centerline_hits'] and not f['road_surface_missing_hits']
assert c['xsd_1_7_pass'] and not c['errors'] and c['observed_route_traversal_pass']
files={}
for n in [NAME+'.fbx',NAME+'.xodr',NAME+'.blend']:
 p=P/n;files[n]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
manifest={'name':NAME,'created':'2026-09-08','asset_type':'CARLA source assets; not a cooked map','source_folder':'美团_LA71AUB1XS0508656_0806_变道后急刹','source_views':['front','rear','left','right'],'vehicles_included':False,'photogrammetry_or_sfm':False,'survey_grade':False,'method':'parameterized manual visual reconstruction from four camera views','unreal_import_tested':False,'carla_server_runtime_tested':False,'files':files,'fbx_validation':f,'opendrive_validation':c}
(P/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
zpath=P/(NAME+'_CARLA_Source.zip')
with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for q in sorted(P.rglob('*')):
  if not q.is_file():continue
  rel=q.relative_to(P)
  if any(v in ['__pycache__','previews'] for v in rel.parts):continue
  if q.suffix in ['.zip','.blend1','.log','.pyc']:continue
  z.write(q,Path(NAME+'Package')/rel)
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 print(json.dumps({'zip':str(zpath),'zip_bytes':zpath.stat().st_size,'zip_files':len(z.namelist()),'primary_files':files},indent=2))
