import bisect
import hashlib
import json
import math
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent
IDS = ['014346', '019742', '016955', '024388', '0512189', '0508656', 'ANA031']
VIEWS = ['front', 'rear', 'left', 'right']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def wrap(yaw):
    return (yaw + 180) % 360 - 180


def interpolate(rows, t):
    """No extrapolation: disappearing actors are not held forever."""
    if not rows or t < rows[0]['replay_time_s'] - 1e-6 or t > rows[-1]['replay_time_s'] + 1e-6:
        return None
    i = bisect.bisect_right([r['replay_time_s'] for r in rows], t)
    if i == 0:
        return dict(rows[0])
    if i == len(rows):
        return dict(rows[-1])
    a, b = rows[i-1], rows[i]
    u = (t-a['replay_time_s']) / (b['replay_time_s']-a['replay_time_s'])
    out = dict(a)
    for k in ['x', 'y', 'z', 'speed']:
        out[k] = a[k] + u * (b[k]-a[k])
    out['yaw_carla_deg'] = wrap(a['yaw_carla_deg'] + u * wrap(b['yaw_carla_deg']-a['yaw_carla_deg']))
    return out


def tracks(path):
    import csv
    result = {}
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            result.setdefault(r['actor_id'], []).append({k: (v if k == 'actor_id' else float(v)) for k, v in r.items()})
    return result
