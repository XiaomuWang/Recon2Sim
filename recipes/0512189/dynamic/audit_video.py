from pathlib import Path
from lxml import etree as E
import json,cv2
from PIL import Image,ImageDraw
p=Path('dynamic_replay_0512189');src=next(Path('.').glob('*LA71AUB13S0512189*'))
template=E.parse(r'C:\Users\Administrator\Desktop\模板\scenario - 2026-09-08T142648.948.xosc')
(p/'evidence/template.pretty.xml').write_bytes(E.tostring(template,pretty_print=True,encoding='utf-8'))
r=template.getroot();summary={'header':dict(r.find('FileHeader').attrib),'entities':len(r.findall('Entities/ScenarioObject')),'tags':sorted(set(e.tag for e in r.iter())),'heading_values':sorted(set(r.xpath('//@h'))),'init':E.tostring(r.find('Storyboard/Init')).decode()}
(p/'evidence/template_analysis.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2)[:4200])
for cam in ['front','rear','left','right']:
 c=cv2.VideoCapture(str(src/(cam+'.mp4')))
 for begin,end in [(0,40),(40,80),(80,120)]:
  times=list(range(begin,end,4));sheet=Image.new('RGB',(1536,4*436),'#14202a');d=ImageDraw.Draw(sheet)
  for i,t in enumerate(times):
   c.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=c.read()
   if not ok:continue
   im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.thumbnail((512,410));x=i%3*512;y=i//3*436;sheet.paste(im,(x,y+26));d.text((x+10,y+6),f'{cam} file time {t:.1f} s',fill='white')
  sheet.save(p/'evidence'/f'{cam}_{begin:03d}_{end:03d}.jpg',quality=92)
 c.release()
