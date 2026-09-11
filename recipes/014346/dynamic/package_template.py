from pathlib import Path
import hashlib,json,zipfile
P=Path(__file__).resolve().parents[1]
O=P/'template_compatible'
files=[O/name for name in ['NanshanGate014346_Timeline.xosc','NanshanGate014346_Timeline_Radians.xosc','NanshanGate014346.xodr','README.md','entity_mapping.json','timeline_events.json','validation.json','template_analysis.json']]
(O/'manifest.json').write_text(json.dumps({'primary_file':'NanshanGate014346_Timeline.xosc','runtime_verified':False,'files':[{'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]},ensure_ascii=False,indent=2),encoding='utf-8')
files.append(O/'manifest.json');archive=O/'NanshanGate014346_Template_Timeline.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,p.name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
readme=P/'README.md';s=readme.read_text(encoding='utf-8')
note='附件模板适配更新：按用户指定的第一份时间轴模板，另行导出 template_compatible/NanshanGate014346_Timeline.xosc，使用时间触发的位置、路线与分时速度事件。模板平台优先使用该版本；同目录附弧度版和专用说明。原连续轨迹 XOSC 与 Python 回放仍保留。\n\n'
if note not in s:readme.write_text(s.split('\n',1)[0]+'\n\n'+note+s.split('\n',1)[1].lstrip(),encoding='utf-8')
f=P/'scripts/finalize_delivery.py';s=f.read_text(encoding='utf-8');s=s.replace("['assets','preview','evidence','validation','scripts']","['assets','preview','evidence','validation','scripts','template_compatible']").replace("{'.log','.pyc','.blend1'}","{'.log','.pyc','.blend1','.zip'}");f.write_text(s,encoding='utf-8')
print(json.dumps({'file':str(archive),'bytes':archive.stat().st_size,'files':len(files),'crc_pass':True},indent=2))