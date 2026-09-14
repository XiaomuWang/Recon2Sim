"""Verify deployed HTML, motion summaries and seekable video against docs/."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]


def check(base):
    manifest=json.loads((ROOT/'docs/site_manifest.json').read_text(encoding='utf-8'))
    entries=[e for e in manifest['files'] if e['path'].endswith(('.mp4','runtime_report.json')) or e['path'] in ('index.html','csv_viewer.html')]
    def verify(entry):
        path=entry['path'];video=path.endswith('.mp4')
        headers={'User-Agent':'Recon2Sim-motion-verification'}
        if video:headers['Range']='bytes=65536-65567'
        try:
            req=Request(base.rstrip('/')+'/'+path+'?v='+entry['sha256'][:16],headers=headers)
            with urlopen(req,timeout=35) as response:
                body=response.read(32 if video else 1000000)
                if video:
                    with (ROOT/'docs'/path).open('rb') as stream:stream.seek(65536);expected=stream.read(32)
                    valid=response.status==206 and body==expected and response.headers.get('Content-Range')=='bytes 65536-65567/'+str(entry['bytes'])
                else:
                    valid=response.status==200 and hashlib.sha256(body).hexdigest()==entry['sha256']
                    if path.endswith('runtime_report.json'):
                        data=json.loads(body);valid=valid and data.get('motion_tracking_accepted') and data.get('motion',{}).get('version')=='motion_full_v1'
                result=dict(path=path,passed=bool(valid),status=response.status)
        except Exception as error:result=dict(path=path,passed=False,error=str(error))
        print(json.dumps(result),flush=True);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(verify,entries))
    (ROOT/'outputs/motion_pages_verification.json').write_text(json.dumps(dict(base=base,passed=all(r['passed'] for r in results),results=results),indent=2),encoding='utf-8')
    if not all(r['passed'] for r in results):raise SystemExit(1)
    print('MOTION_PAGES_VERIFIED',len(results),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='https://xiaomuwang.github.io/Recon2Sim/')
    check(parser.parse_args().base)
