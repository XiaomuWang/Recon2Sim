from pathlib import Path
from lxml import etree as E
from collections import Counter
import json,copy
P=Path(__file__).resolve().parents[1];out=P/'template_compatible';out.mkdir(exist_ok=True)
schema=E.XMLSchema(E.parse(str(P/'validation/OpenSCENARIO.xsd')))
rows=[]
for p in Path(r'C:\Users\Administrator\Desktop\模板').glob('scenario - 2026-09-08T1426*.xosc'):
 root=E.parse(str(p));tags=Counter(e.tag for e in root.iter());samples=[]
 for action in root.findall('.//Action'):
  tag=next((e.tag for e in action.iter() if e.tag.endswith('Action') and e.tag not in ['Action','PrivateAction','GlobalAction','RoutingAction','LongitudinalAction']),None)
  if tag and tag not in [r['type'] for r in samples]:samples.append({'type':tag,'xml':E.tostring(action,encoding='unicode')[:3500]})
 row={'file':p.name,'header':dict(root.find('FileHeader').attrib),'counts':dict(tags),'schema_pass':schema.validate(root),'schema_errors':str(schema.error_log),'action_examples':samples,'headings_sample':[e.get('h') for e in root.findall('.//TeleportAction/Position/WorldPosition')[:20]],'controllers':list(set(root.xpath('//Controller/@name')))}
 rows.append(row)
 print(json.dumps({k:v for k,v in row.items() if k not in ['counts','action_examples']},ensure_ascii=False,indent=2))
 print('Actions:',{k:v for k,v in tags.items() if k.endswith('Action') or k=='Event'})
 (out/(p.stem+'.pretty.xml')).write_bytes(E.tostring(root,encoding='utf-8',pretty_print=True,xml_declaration=True))
(out/'template_analysis.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
