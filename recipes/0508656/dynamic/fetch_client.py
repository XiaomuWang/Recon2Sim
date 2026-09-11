"""Optional download of official cp38 CARLA 0.9.15 wheel; use Python 3.11 TLS."""
import pathlib,urllib.request,json,hashlib,zipfile
P=pathlib.Path(__file__).resolve().parents[1];dest=P/'runtime';dest.mkdir(exist_ok=True)
meta=json.load(urllib.request.urlopen('https://pypi.org/pypi/carla/0.9.15/json',timeout=30))
row=next(x for x in meta['urls'] if x['filename']=='carla-0.9.15-cp38-cp38-win_amd64.whl')
wheel=dest/row['filename'];urllib.request.urlretrieve(row['url'],wheel)
assert hashlib.sha256(wheel.read_bytes()).hexdigest()==row['digests']['sha256']
with zipfile.ZipFile(wheel) as z:z.extractall(dest)
(P/'validation/client_provenance.json').write_text(json.dumps({'url':row['url'],'sha256':row['digests']['sha256'],'version':'0.9.15','python_abi':'cp38-win_amd64','purpose':'offline API/OpenDRIVE compatibility check, not CARLA server runtime'},indent=2))
print('Verified official CARLA 0.9.15 cp38 wheel; extracted locally')
