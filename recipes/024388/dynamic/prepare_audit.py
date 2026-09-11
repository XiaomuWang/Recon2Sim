from pathlib import Path
import cv2,json,shutil,urllib.request,collections
from PIL import Image,ImageDraw,ImageFont
from lxml import etree as E
P=Path(__file__).resolve().parents[1];W=P.parent;src=next(W.glob('*LNDEA7HF1SH024388*'))
for d in ['evidence','preview','validation','template_compatible','scripts','reference']:(P/d).mkdir(exist_ok=True)
shutil.copy2(W/'environment_reconstruction_024388/LuoboTurn024388.xodr',P/'LuoboTurn024388.xodr')
shutil.copy2(W/'dynamic_replay_014346/validation/OpenSCENARIO.xsd',P/'validation/OpenSCENARIO.xsd')
template=Path(r'C:\Users\Administrator\Desktop\模板\scenario - 2026-09-08T142648.948.xosc')
t=E.parse(str(template));(P/'reference/template.pretty.xml').write_bytes(E.tostring(t,pretty_print=True,encoding='utf-8',xml_declaration=True))
analysis={'header':dict(t.find('FileHeader').attrib),'tag_counts':dict(collections.Counter(e.tag for e in t.iter())),'controllers':list(set(t.xpath('//Controller/@name'))),'parameters':[dict(x.attrib) for x in t.findall('ParameterDeclarations/ParameterDeclaration')],'environment_xml':E.tostring(t.find('.//Environment'),encoding='unicode'),'init_private_actions':len(t.findall('Storyboard/Init/Actions/Private')),'heading_examples':t.xpath('//TeleportAction//WorldPosition/@h')[:12]}
(P/'reference/template_analysis.json').write_text(json.dumps(analysis,indent=2,ensure_ascii=False),encoding='utf-8')
for path in ['srunner/tools/openscenario_parser.py','srunner/scenarioconfigs/openscenario_configuration.py','Docs/openscenario_support.md','srunner/scenariomanager/scenarioatomics/atomic_behaviors.py']:
 try:
  url='https://raw.githubusercontent.com/carla-simulator/scenario_runner/v0.9.15/'+path
  data=urllib.request.urlopen(url,timeout=25).read();(P/'reference'/('sr015_'+Path(path).name)).write_bytes(data)
 except Exception as e:print('Reference download:',e)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
groups=[list(range(0,46,5)),list(range(45,81,4)),list(range(80,101,2)),list(range(102,119,2)),list(range(120,150,3)),list(range(150,180,3))]
for cam in ['front','rear','left','right']:
 c=cv2.VideoCapture(str(src/(cam+'.mp4')))
 for gi,times in enumerate(groups):
  sheet=Image.new('RGB',(1280,390*((len(times)+1)//2)),(22,27,34));d=ImageDraw.Draw(sheet)
  for i,s in enumerate(times):
   c.set(cv2.CAP_PROP_POS_MSEC,s*1000);ok,f=c.read()
   if not ok:continue
   raw=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));raw.save(P/'evidence'/f'{cam}_{s:03d}.jpg')
   # Gamma-only analysis view; original frame is saved separately. Not a generated image.
   lut=bytes(round(255*(v/255)**.63) for v in range(256));bright=raw.point(list(lut)*3)
   x=i%2*640;y=i//2*390;sheet.paste(bright.resize((640,360)),(x,y+28));d.text((x+8,y+3),f'{cam}  视频 {s}s / 提亮分析视图',font=font,fill='white')
  sheet.save(P/'evidence'/f'{cam}_audit_{gi}.jpg',quality=94)
 c.release()
print(json.dumps(analysis,ensure_ascii=False,indent=2))
