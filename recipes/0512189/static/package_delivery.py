"""Build a local review page and a verified source ZIP. Run after all validations."""
import pathlib,json,hashlib,zipfile,html,ast
from PIL import Image,ImageDraw,ImageFont
P=pathlib.Path(__file__).resolve().parents[1];NAME='MeituanLane0512189'
cv=json.loads((P/'validation/carla_validation.json').read_text());fv=json.loads((P/'validation/fbx_validation.json').read_text())
assert cv['xsd_1_7_pass'] and not cv['errors'] and fv['fbx_reimport_pass'] and not fv['road_surface_missing_hits'] and not fv['textures_missing']
for f in (P/'scripts').glob('*.py'):ast.parse(f.read_text(encoding='utf-8-sig'))
views=[('前视','front_000','01_front','右侧斜列车位、树荫店面；左侧高架与围栏'),('后视','rear_000','02_rear','右后加油站在回看画面左侧，核对前后及左右关系'),('左视','left_000','03_left','沿道路高架、桥墩、绿化与施工楼体'),('右视','right_000','04_right','加油站前场、红色顶棚与立柱招牌')]
cards=''
for title,src,render,note in views:
 cards+=f'<section><h2>{title}</h2><p>{note}</p><div class="pair"><figure><img src="evidence/detail_{src}.jpg"><figcaption>原视频参考帧（保留原始画面）</figcaption></figure><figure><img src="renders/{render}.png"><figcaption>交付模型渲染 · 视点近似，无相机配准</figcaption></figure></div></section>'
gallery=''.join(f'<figure><img src="renders/{n}.png"><figcaption>{t}</figcaption></figure>' for n,t in [('00_aerial','整体空间关系'),('05_parking_detail','斜列车位与商铺细节'),('06_after_lane_change','后段人行道与让行牌'),('07_full_extent','道路及环境延伸范围')])
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>美团 0512189 · 四向环境复原</title><style>
*{box-sizing:border-box}body{margin:0;background:#111a20;color:#dce5df;font:16px/1.75 'Microsoft YaHei',sans-serif}main{max-width:1360px;margin:auto;padding:50px 30px}small{color:#73cab2;letter-spacing:3px}h1{font-size:40px;line-height:1.35}h2{font-size:25px}p{color:#aebdbf;max-width:1050px}section{padding:24px 0;border-top:1px solid #304149}.hero{width:100%;border-radius:10px}figure{margin:0;background:#1b282f;border-radius:8px;overflow:hidden}figure img{display:block;width:100%;height:350px;object-fit:contain;background:#0a1014}figcaption{padding:12px 17px;color:#b7c8c6;font-size:13px}.pair,.gallery{display:grid;grid-template-columns:1fr 1fr;gap:18px}.stats{display:flex;gap:32px;flex-wrap:wrap;margin:30px 0}.stats b{font-size:29px;color:#8adebc;display:block}a{color:#8adebc}.note{padding:18px 24px;background:#203235;border-left:3px solid #76bea6;border-radius:4px}@media(max-width:800px){.pair,.gallery{grid-template-columns:1fr}h1{font-size:28px}main{padding:24px 16px}}</style><main>
<small>ENVIRONMENT RECONSTRUCTION / 0512189</small><h1>美团 · 0814 变道<br>四向视频环境复原</h1><p>高架与桥墩 / 加油站 / 斜列车位 / 商铺 / 行道树 / 湿润沥青。只含静态环境，FBX 与 OpenDRIVE 使用相同道路尺寸。</p>
<div class="stats"><div><b>275 m</b>可导航道路</div><div><b>6</b>行车道</div><div><b>4</b>视频方向</div><div><b>3,300</b>路面采样点通过</div></div>
<img class="hero" src="renders/01_front.png"><p class="note">这是未标定视频的参数化视觉复原；尺寸、楼栋细节和遮挡部分为估计。四路存在时间偏差，此处是地标对照，不是逐像素匹配。高架、加油站及远处交叉口为环境几何，不提供导航。CARLA / Unreal 运行导入尚未实测。</p>
<p><a href="MeituanLane0512189.fbx">FBX 模型</a> · <a href="MeituanLane0512189.xodr">OpenDRIVE</a> · <a href="README_交付与CARLA导入.md">导入说明</a></p>'''+cards+'<section><h2>模型预览</h2><div class="gallery">'+gallery+'</div></section><section><h2>验证</h2><p>OpenDRIVE 1.7 XSD、CARLA 离线解析、相邻路段连接、变道关系、FBX 回读、轴向单位、嵌入贴图与 3,300 个路点的路面射线检查均通过。验证结果不代表实景测绘精度。</p><a href="validation/carla_validation.json">CARLA 离线报告</a> · <a href="validation/fbx_validation.json">FBX 报告</a></section></main></html>'
(P/'review.html').write_text(page,encoding='utf-8')
# Preview board uses actual final mesh renders only.
im=Image.new('RGB',(1600,1130),'#111a20');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',26)
d.text((28,18),'美团 0512189  |  四向静态环境预览',font=font,fill='#dce5df')
for i,(label,_,n,_) in enumerate(views):
 src=Image.open(P/'renders'/f'{n}.png');src.thumbnail((790,494));x=(i%2)*800;y=68+(i//2)*530;im.paste(src,(x,y));d.text((x+18,y+490),label,font=font,fill='#8adebc')
im.save(P/'renders/preview_board.jpg',quality=94)
files=[]
for f in sorted(P.rglob('*')):
 if not f.is_file() or f.suffix in ['.zip','.blend1','.log','.pyc'] or '.fbm' in str(f) or '__pycache__' in str(f) or f.name in ['delivery_manifest.json','prepare.py']:continue
 files.append(f)
manifest={'name':NAME,'kind':'FBX + OpenDRIVE source assets; not cooked CARLA map','validation_pass':True,'unreal_runtime_tested':False,'files':[{'path':f.relative_to(P).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]}
(P/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2));files.append(P/'delivery_manifest.json')
out=P/(NAME+'_CARLA_Source.zip')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in files:z.write(f,NAME+'Package/'+f.relative_to(P).as_posix())
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print(json.dumps({'archive':str(out),'bytes':out.stat().st_size,'file_count':len(files),'zip_crc_pass':True},indent=2))
