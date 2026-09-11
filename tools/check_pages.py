"""Verify the exported site's asset integrity using only the Python standard library."""
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1] / 'docs'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(v for k, v in attrs if k in ['href', 'src'] and v)


def check():
    manifest = json.loads((ROOT / 'site_manifest.json').read_text(encoding='utf-8'))
    expected = {entry['path'] for entry in manifest['files']} | {'site_manifest.json'}
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}
    if actual != expected:
        raise RuntimeError('Unexpected or missing site files: ' + str(actual ^ expected))
    total = 0
    for entry in manifest['files']:
        file = ROOT / entry['path']
        file.resolve().relative_to(ROOT.resolve())
        if file.is_symlink() or file.stat().st_size > 100 * 1024 ** 2:
            raise RuntimeError('Symlink or oversized Git asset: ' + entry['path'])
        digest = hashlib.sha256()
        with file.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != entry['sha256'] or file.stat().st_size != entry['bytes']:
            raise RuntimeError('Asset hash/size mismatch: ' + entry['path'])
        total += entry['bytes']
    if total >= 1024 ** 3:
        raise RuntimeError('Site exceeds 1 GiB')
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    scenes = json.loads(re.search(r'const scenes=(.*?);\s*const el=', html, re.S).group(1))
    if [s['id'] for s in scenes] != manifest['scene_order']:
        raise RuntimeError('Scene order mismatch')
    for name in ['index.html', 'csv_viewer.html']:
        links = Links()
        links.feed((ROOT / name).read_text(encoding='utf-8'))
        for url in links.links:
            parsed = urlsplit(url)
            if parsed.scheme or not parsed.path:
                continue
            if parsed.path.startswith('/') or not (ROOT / unquote(parsed.path)).is_file():
                raise RuntimeError('Broken/project-prefix-unsafe link: ' + url)
    for scene in scenes:
        for file in ['presentation/report.mp4', 'presentation/report_poster.png',
                     'analysis/ego_analysis.png', 'analysis/ego_metrics.csv', 'entity_mapping.json',
                     'validation/carla_imported/ego_telemetry.csv', 'validation/carla_imported/runtime_report.json']:
            if not (ROOT / scene['id'] / file).is_file():
                raise RuntimeError('Missing dynamic page link: ' + scene['id'] + '/' + file)
    print('PAGES_CHECK_OK', len(expected), 'files;', len(scenes), 'scenes;', round(total / 1048576, 2), 'MiB')


if __name__ == '__main__':
    check()
