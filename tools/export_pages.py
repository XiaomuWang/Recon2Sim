"""Export only the approved report assets; no CARLA/editor dependency required."""
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def export():
    source, target = ROOT / 'outputs', ROOT / 'docs'
    target.mkdir(exist_ok=True)
    html = (source / 'index.html').read_text(encoding='utf-8')
    match = re.search(r'const scenes=(.*?);\s*const el=', html, re.S)
    if not match:
        raise RuntimeError('Report scene metadata missing')
    scenes = json.loads(match.group(1))
    copied = []

    def copy(relative, destination=None):
        src = source / relative
        dst = target / (destination or relative)
        src.resolve().relative_to(source.resolve())
        dst.resolve().relative_to(target.resolve())
        if not src.is_file():
            raise FileNotFoundError(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst)

    for scene in scenes:
        sid = scene['id']
        if not re.fullmatch(r'[A-Za-z0-9]+', sid) or not scene['ready']:
            raise RuntimeError('Unready or invalid scene: ' + sid)
        for suffix in ['presentation/report.mp4', 'presentation/report_poster.png',
                       'analysis/ego_analysis.png', 'analysis/ego_metrics.csv',
                       'validation/carla_imported/ego_telemetry.csv', 'entity_mapping.json']:
            copy(sid + '/' + suffix)
        # Publish useful validation evidence, excluding machine paths and asset inventories.
        report = read(source / sid / 'validation/carla_imported/runtime_report.json')
        keys = ['scene_id', 'success', 'server_version', 'client_version', 'frames',
                'full_duration_capture', 'fbx_runtime_verified', 'imported_geometry_complete',
                'imported_environment_object_count', 'missing_actor_ids', 'activated_actor_ids',
                'max_ego_origin_error_m', 'max_actor_origin_errors_m', 'max_actor_yaw_errors_deg',
                'command_submission', 'chase_camera', 'fresh_world_loaded',
                'hybrid_reconstruction', 'physical_collision_validated', 'recorded_actor_ids',
                'motion_actor_ids', 'motion_tracking_accepted', 'motion']
        public = {key: report[key] for key in keys if key in report}
        surface = report.get('engine_surface_check', {})
        public['road_surface_check'] = {key: surface[key] for key in ['misses', 'max_error_m'] if key in surface}
        public['scope'] = 'Published summary of completed runtime verification; execution consistency is not real-world reconstruction accuracy.'
        path = target / sid / 'validation/carla_imported/runtime_report.json'
        path.write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding='utf-8')
        copied.append(path)

    highlight = read(source / 'presentation/highlights_manifest.json')
    if [c['scene_id'] for c in highlight['clips']] != [s['id'] for s in scenes]:
        raise RuntimeError('Highlight and page scene order differ')
    copy('presentation/' + highlight.get('video_file', 'highlights.mp4'), 'presentation/highlights.mp4')
    # The homepage excludes installation-package and legacy offline-report links.
    html, count = re.subn(r'<div class="actions" style="margin-bottom:20px">.*?</div>',
                         '<div class="actions" style="margin-bottom:20px"><a href="presentation/highlights.mp4" target="_blank">七组事故重点片段 · 84 秒</a></div>', html, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError('Global download section not found')
    html = re.sub(r'<a href="offline\.html"[^>]*>.*?</a>', '', html)
    (target / 'index.html').write_text(html, encoding='utf-8')
    copied.append(target / 'index.html')
    copy('csv_viewer.html')
    (target / '.nojekyll').touch()
    copied.append(target / '.nojekyll')
    manifest = {'scene_order': [s['id'] for s in scenes], 'files': []}
    for file in copied:
        digest = hashlib.sha256()
        with file.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        manifest['files'].append({'path': file.relative_to(target).as_posix(),
                                  'bytes': file.stat().st_size, 'sha256': digest.hexdigest()})
    (target / 'site_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PAGES_EXPORT', len(copied), 'files;', round(sum(x['bytes'] for x in manifest['files']) / 1048576, 2), 'MiB')


if __name__ == '__main__':
    export()
