"""Rebuild the supplied reviewed reconstruction recipes in an isolated workspace.

Raw videos provide visual evidence. Metric anchors and object identities come from
the supplied research recipes; these are not calibrated automatic 3D tracking.
"""
import argparse
import csv
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from .common import PROJECT, WORKSPACE, IDS, VIEWS, read, write, sha, wrap

ROLES = {
    '014346': ['gate_truck', 'worker_orange', 'cargo_tricycle'],
    '019742': ['wrongway_orange_rider', 'wrongway_white_rider'],
    '016955': ['sweeper', 'cross_scooter_a', 'cross_scooter_b', 'coach'],
    '024388': ['box_truck', 'cross_person_1', 'cross_person_2', 'late_pair_1', 'late_pair_2'],
    '0512189': ['green_delivery_van', 'silver_minivan', 'white_box_truck', 'bus_teal', 'bus_yellow_ad'],
    '0508656': ['white_following_car', 'blue_box_courier', 'silver_suv_late'],
    'ANA031': ['lead_silver', 'driver_gray', 'rear_dark'],
}


def init():
    configs = []
    for sid in IDS:
        static = WORKSPACE / 'static_data' / ('environment_reconstruction_' + sid)
        dynamic = WORKSPACE / 'dynamic_data' / ('dynamic_replay_' + sid)
        video = [p for p in (WORKSPACE / 'data').iterdir() if sid in p.name]
        if len(video) != 1:
            raise ValueError('Ambiguous video scene: ' + sid)
        source = read(dynamic / 'scenario.json')
        cfg = PROJECT / 'configs' / (sid + '.json')
        offsets = source.get('camera_file_time_offsets_s', dict.fromkeys(VIEWS, 0.0))
        if sid == '016955':
            offsets['left'] = 1 / 15
        config = dict(scene_id=sid, name=source['map_name'], video_dir=str(video[0].relative_to(WORKSPACE)),
                      ego_actor_id='ego', accident_actor_ids=ROLES[sid],
                      role_basis='Proposed from supplied event/identity anchors; editable, not legal fault attribution',
                      camera_file_time_offsets_s=offsets,
                      camera_sync_status='estimated from supplied evidence; not hardware synchronized',
                      road_margin_m=0.5, carla_host='localhost', carla_port=2000)
        if not cfg.exists():
            write(cfg, config)
        configs.append(read(cfg))
        for kind, source_dir in [('static', static), ('dynamic', dynamic)]:
            dest = PROJECT / 'recipes' / sid / kind
            dest.mkdir(parents=True, exist_ok=True)
            for p in (source_dir / 'scripts').glob('*.py'):
                if not (dest / p.name).exists():
                    shutil.copy2(p, dest / p.name)
    write(PROJECT / 'configs' / 'index.json', configs)


def stage(sid):
    """Only staged/generated files are changed. Inputs stay read-only."""
    root = PROJECT / 'work'
    for kind, prefix in [('static', 'environment_reconstruction_'), ('dynamic', 'dynamic_replay_')]:
        src = WORKSPACE / (kind + '_data') / (prefix + sid)
        dest = root / (prefix + sid)
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copytree(PROJECT / 'recipes' / sid / kind, dest / 'scripts', dirs_exist_ok=True)
        for directory in (['textures'] if kind == 'static' else ['evidence']):
            if (src / directory).exists():
                shutil.copytree(src / directory, dest / directory, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns('*.mp4', '*.jpg', '*.png', '*.jpeg') if kind == 'dynamic' else None)
        for d in ['validation', 'renders', 'evidence', 'preview']:
            (dest / d).mkdir(exist_ok=True)
        # Schema is needed by some historical writers; validation results are never copied.
        if (src / 'validation' / 'schema').exists():
            shutil.copytree(src / 'validation' / 'schema', dest / 'validation' / 'schema', dirs_exist_ok=True)
        for p in src.glob('*.json'):
            if p.name != 'scenario.json':
                shutil.copy2(p, dest / p.name)
        if kind == 'dynamic':
            # Some historical generators read their own map, generated in the previous stage.
            cfg = read(PROJECT / 'configs' / (sid + '.json'))
            xodr = root / ('environment_reconstruction_' + sid) / (cfg['name'] + '.xodr')
            if xodr.exists():
                shutil.copy2(xodr, dest / xodr.name)
    return root


def run_log(args, log, cwd=None):
    log.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    with log.open('w', encoding='utf-8') as f:
        p = subprocess.run([str(x) for x in args], cwd=cwd, stdout=f, stderr=subprocess.STDOUT, env=env)
    if p.returncode:
        raise RuntimeError('Command failed, see ' + str(log))


def blender_exe():
    p = os.environ.get('BLENDER_EXE') or shutil.which('blender')
    if p:
        return Path(p)
    choices = list((WORKSPACE / 'static_data').glob('*/runtime/blender-*/blender.exe'))
    if not choices:
        raise RuntimeError('Set BLENDER_EXE to Blender 4.2 executable')
    return choices[0]


def build_static(sid, mesh=True):
    cfg = read(PROJECT / 'configs' / (sid + '.json'))
    stage(sid)
    root = PROJECT / 'work' / ('environment_reconstruction_' + sid)
    logs = PROJECT / 'outputs' / sid / 'validation'
    run_log([sys.executable, PROJECT / 'scripts' / 'run_recipe.py', root / 'scripts' / 'make_opendrive.py'], logs / 'static_xodr_build.log', root / 'scripts')
    if mesh:
        run_log([blender_exe(), '--background', '--python-exit-code', '1', '--python', PROJECT / 'scripts' / 'blender_build.py', '--', root / 'scripts' / 'build_scene.py'],
                logs / 'static_fbx_build.log', root)
    out = PROJECT / 'outputs' / sid / 'map'
    out.mkdir(parents=True, exist_ok=True)
    for ext in ['.xodr', '.fbx', '.blend']:
        p = root / (cfg['name'] + ext)
        if p.exists():
            shutil.copy2(p, out / p.name)
    shutil.copytree(root / 'textures', out / 'textures', dirs_exist_ok=True)
    write(out / (cfg['name'] + 'Package.json'), {'maps': [{'name': cfg['name'], 'source': cfg['name'] + '.fbx',
          'xodr': cfg['name'] + '.xodr', 'use_carla_materials': False}], 'props': []})
    write(out / 'coordinate_contract.json', dict(source_frame='right-handed X,Y,Z in meters; same origin as XODR',
          carla_frame='x=X,y=-Y,z=Z; yaw_carla_deg=-degrees(heading_rh_rad)',
          fbx_export=dict(axis_forward='Y', axis_up='Z', apply_unit_scale=True, embed_textures=True),
          unreal_import='Use supplied Unreal importer with scene axis conversion; centimeters are engine-only, CSV stays meters',
          precision='estimated from video; no calibration or survey'))


def entity_type(a):
    category = a.get('category', 'unknown')
    bp = ' '.join(a.get('blueprint_candidates', []))
    if category == 'pedestrian' or 'walker.' in bp:
        return 'pedestrian'
    if any(x in bp for x in ['diamondback', 'gazelle', 'bh.crossbike']):
        return 'bicycle'
    if category == 'tricycle':
        return 'tricycle'
    if category == 'motorcycle' or any(x in bp for x in ['vespa', 'yamaha', 'kawasaki', 'harley']):
        return 'motorbike'
    if category in ['truck', 'gate_truck'] or 'carlamotors' in bp and category != 'bus':
        return 'truck'
    if category in ['bus', 'van', 'sweeper']:
        return category
    if category in ['car', 'suv', 'mpv', 'parked', 'parked_car', 'parked_vehicle']:
        return 'car'
    return category


def build_dynamic(sid, regenerate=True):
    cfg = read(PROJECT / 'configs' / (sid + '.json'))
    work = PROJECT / 'work'
    root = work / ('dynamic_replay_' + sid)
    xodr = PROJECT / 'outputs' / sid / 'map' / (cfg['name'] + '.xodr')
    if not xodr.exists():
        raise ValueError('Static stage required first')
    shutil.copy2(xodr, root / xodr.name)
    if regenerate:
        run_log([sys.executable, PROJECT / 'scripts' / 'run_recipe.py', root / 'scripts' / 'generate_scenario.py'], PROJECT / 'outputs' / sid / 'validation' / 'dynamic_build.log', work)
        source_path = root / 'scenario.json'
    else:
        source_path = WORKSPACE / 'dynamic_data' / ('dynamic_replay_' + sid) / 'scenario.json'
    source = read(source_path)
    for aid,spec in cfg.get('route_overrides',{}).items():
        from .routes import sample_route
        actor=next((a for a in source['actors'] if a['id']==aid),None)
        if actor is None: raise ValueError('Unknown route override actor: '+aid)
        actor['samples']=sample_route(xodr,spec,source.get('fps',30))
        actor['notes']='Explicit road/lane route override on generated XODR; review against original video'
    roles = [cfg['ego_actor_id']] + cfg['accident_actor_ids']
    ids = [a['id'] for a in source['actors']]
    if len(set(ids)) != len(ids) or any(x not in ids for x in roles) or cfg['ego_actor_id'] in cfg['accident_actor_ids']:
        raise ValueError('Invalid/duplicate ego or accident role IDs')
    out = PROJECT / 'outputs' / sid
    entities, rows = [], []
    fallback = dict(car='vehicle.tesla.model3', truck='vehicle.carlamotors.carlacola', van='vehicle.mercedes.sprinter',
                    bus='vehicle.carlamotors.carlacola', motorbike='vehicle.yamaha.yzf', bicycle='vehicle.gazelle.omafiets',
                    tricycle='vehicle.vespa.zx125', pedestrian='walker.pedestrian.0001', sweeper='vehicle.bmw.isetta')
    for a in source['actors']:
        samples = a['samples']
        times = np.array([s['t'] for s in samples], dtype=float)
        pos = np.array([[s['x'], -s['y'], s['z']] for s in samples], dtype=float)
        if len(times) < 2 or not np.isfinite(pos).all() or np.any(np.diff(times) <= 0):
            raise ValueError('Invalid times/positions for ' + a['id'])
        # Per-interval metric speed; stationary duplicate positions remain zero.
        segment_speed = np.linalg.norm(np.diff(pos, axis=0), axis=1) / np.diff(times)
        speeds = np.r_[segment_speed, segment_speed[-1]]
        actor_rows = []
        for s, p, speed in zip(samples, pos, speeds):
            r = dict(actor_id=a['id'], replay_time_s=s['t'], source_video_time_s=s.get('video_t', s['t']+source['source_video_start_s']),
                     x=p[0], y=p[1], z=p[2], yaw_carla_deg=wrap(-math.degrees(s['h'])), speed=float(speed))
            actor_rows.append(r)
        rows.extend(actor_rows)
        kind = entity_type(a)
        candidates = a.get('blueprint_candidates', [])
        if not candidates:
            raise ValueError('Missing blueprint: ' + a['id'])
        backup = next((p for p in candidates[1:] if p != candidates[0]), fallback.get(kind))
        entities.append(dict(actor_id=a['id'], entity_name=a.get('label_zh', a['id']), type=kind,
            source_category=a.get('category'), role='ego' if a['id'] == cfg['ego_actor_id'] else 'accident_related' if a['id'] in cfg['accident_actor_ids'] else 'context',
            carla_blueprint=candidates[0], fallback_blueprint=backup, blueprint_candidates=list(dict.fromkeys(candidates+[backup])),
            custom_blueprint=a.get('preferred_custom_blueprint'), color=a.get('color'),
            start_time_s=float(times[0]), end_time_s=float(times[-1]), initial_state=actor_rows[0], dimensions_m=a.get('dimensions_m'),
            stationary=bool(np.max(segment_speed)<0.01), dimensions_status='estimated', confidence=a.get('confidence'), notes=a.get('notes'),
            appearance_limit='Stock fallback approximates appearance; bus/tricycle/sweeper and delivery ego may need supplied custom assets'))
    with (out / 'trajectories.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    write(out / 'entity_mapping.json', {'ego_actor_id': cfg['ego_actor_id'], 'accident_actor_ids': cfg['accident_actor_ids'], 'actors': entities})
    night = sid in ['024388', 'ANA031']
    weather = dict(cloudiness=25, precipitation=0, precipitation_deposits=0, wetness=5,
                   wind_intensity=5, sun_azimuth_angle=160, sun_altitude_angle=-8 if night else 45,
                   fog_density=2, fog_distance=60, fog_falloff=0.2)
    weather.update(source.get('weather', {}))
    scene = dict(scene_id=sid, map_name=cfg['name'], duration_s=source['duration_s'], replay_start_s=0,
          source_video_start_s=source['source_video_start_s'], source_video_end_s=source['source_video_end_s'],
          coordinate_frame='CARLA left-handed meters; trajectory z is bounding-box ground center', yaw_unit='degrees [-180,180)',
          speed_unit='m/s', ego_actor_id=cfg['ego_actor_id'], accident_actor_ids=cfg['accident_actor_ids'],
          weather_type='rainy_night' if sid=='ANA031' else 'night' if night else 'daylight_estimate',
          lighting=dict(time_of_day='night' if night else 'day', clock_time_local=None, clock_time_status='not recovered'),
          weather=weather, weather_units={'cloudiness':'percent','precipitation':'percent','precipitation_deposits':'percent','wetness':'percent',
          'wind_intensity':'percent','sun_azimuth_angle':'degrees','sun_altitude_angle':'degrees','fog_density':'percent','fog_distance':'m (fog start distance, NOT visibility)','fog_falloff':'dimensionless'},
          fog_visibility_distance_m=120 if sid=='ANA031' else 1000,
          friction_coefficient=0.55 if sid=='ANA031' else 0.85, friction_status='assumed dimensionless; not measured',
          weather_status='estimated replay settings, not meteorological measurements',
          preserve_post_collision_state=True, collision_mode='kinematic recorded poses; no physical collision reconstruction',
          video_dir=cfg['video_dir'], camera_file_time_offsets_s=cfg['camera_file_time_offsets_s'], camera_sync_status=cfg['camera_sync_status'],
          events=source.get('events', []), source_limitations=source.get('limitations', []),
          reconstruction_method=source.get('reconstruction_method'), all_video_actors_verified=False,
          raw_video_full_duration_verified=False, carla_runtime_verified=False,
          provenance=dict(mode='regenerated_reviewed_recipes' if regenerate else 'normalized_existing_result',
                          source_scenario_sha256=sha(source_path), xodr_sha256=sha(xodr)))
    write(out / 'scene_config.json', scene)
    write(out / 'source_anchors.json', [{k:v for k,v in a.items() if k!='samples'} for a in source['actors']])
    # Direct comparison to final legacy results exposes refinements absent from the generator.
    legacy = read(WORKSPACE / 'dynamic_data' / ('dynamic_replay_' + sid) / 'scenario.json')
    diffs = {}
    for a, old in zip(source['actors'], legacy['actors']):
        if a['id']==old['id'] and len(a['samples'])==len(old['samples']):
            diffs[a['id']] = max(math.hypot(s['x']-r['x'],s['y']-r['y']) for s,r in zip(a['samples'],old['samples']))
        else:
            diffs[a['id']] = None
    write(out / 'validation' / 'legacy_comparison.json', dict(max_xy_difference_m_by_actor=diffs, identical_actor_ids=ids==[a['id'] for a in legacy['actors']],
          note='Historical post-generation refinements may differ. Regenerated result is audited separately.'))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['init','build','static','dynamic','validate','preview','fbx-review'])
    ap.add_argument('--scene', default='all', choices=['all']+IDS)
    ap.add_argument('--skip-mesh', action='store_true')
    ap.add_argument('--existing-dynamic', action='store_true')
    ap.add_argument('--with-preview', action='store_true',help='Build FBX verification renders and full six-panel comparison')
    args=ap.parse_args()
    init()
    if args.command=='init': return
    for sid in IDS if args.scene=='all' else [args.scene]:
        print(args.command, sid, flush=True)
        if args.command in ['build','static']: build_static(sid, not args.skip_mesh)
        if args.command in ['build','dynamic']: build_dynamic(sid, not args.existing_dynamic)
        if args.command in ['build','validate']:
            from .validate import validate
            validate(sid)
        if args.command=='fbx-review' or args.command=='build' and args.with_preview:
            run_log([blender_exe(),'--background','--python-exit-code','1','--python',PROJECT/'scripts/blender_review.py','--',PROJECT/'outputs'/sid],
                    PROJECT/'outputs'/sid/'validation/fbx_review.log')
        if args.command=='preview' or args.command=='build' and args.with_preview:
            from .preview import preview
            preview(sid)


if __name__=='__main__': main()
