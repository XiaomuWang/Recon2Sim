"""Create a portable FBX/XODR/BLEND delivery; exclude runtime caches and source videos."""
from pathlib import Path
import hashlib,json,zipfile
P=Path(__file__).resolve().parents[1];name='UrbanBrake019742Package';out=P/(name+'.zip')
def eligible(p):
 rel=p.relative_to(P)
 return p.is_file() and p.suffix not in ['.zip','.blend1','.pyc','.log'] and '__pycache__' not in rel.parts and not any(q.endswith('.fbm') for q in rel.parts) and p.name!='delivery_manifest.json'
files=sorted(p for p in P.rglob('*') if eligible(p))
manifest={'package':name,'files':[{'path':p.relative_to(P).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(P/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
files.append(P/'delivery_manifest.json')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,name+'/'+p.relative_to(P).as_posix())
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for rec in manifest['files']:
  assert hashlib.sha256(z.read(name+'/'+rec['path'])).hexdigest()==rec['sha256']
print(json.dumps({'zip':str(out),'bytes':out.stat().st_size,'files':len(files),'zip_crc_and_sha256_pass':True},indent=2))
