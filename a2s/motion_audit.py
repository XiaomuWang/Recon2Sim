"""Audit the original seven cases without changing reconstructed trajectories."""
import argparse
import math
import numpy as np
from .common import PROJECT, read, write, tracks, wrap
from .motion import ORIGINAL_SCENES, motion_kind, reference


def audit():
    result=dict(source='original seven reconstructed trajectories',
        limits_status='engineering screening assumptions, not measured vehicle capabilities',
        limits=dict(walker_speed_mps=3.,rider_accel_mps2=3.,rider_lateral_accel_mps2=3.),scenes={})
    for sid in ORIGINAL_SCENES:
        root=PROJECT/'outputs'/sid; data=tracks(root/'trajectories.csv'); actors=[]
        for e in read(root/'entity_mapping.json')['actors']:
            kind=motion_kind(e)
            if kind=='recorded': continue
            rows=data[e['actor_id']];times=np.arange(rows[0]['replay_time_s'],rows[-1]['replay_time_s'],.1)
            samples=[reference(rows,float(t)) for t in times]
            if len(samples)<3: continue
            speeds=np.array([r['motion_speed'] for r in samples])
            acc=np.diff(speeds)/.1
            yawrate=np.array([math.radians(wrap(b['motion_yaw']-a['motion_yaw']))/.1 for a,b in zip(samples,samples[1:])])
            lateral=abs(yawrate*speeds[1:])
            issues=[]
            if kind.startswith('unsupported'): issues.append('requires matching actor model; stock substitute is not physical equivalence')
            if kind=='walker' and max(speeds)>3.: issues.append('reference exceeds configured walk/run speed limit')
            if kind=='two_wheeler' and max(abs(acc))>3.: issues.append('reference acceleration exceeds screening limit')
            if kind=='two_wheeler' and max(lateral)>3.: issues.append('reference lateral acceleration exceeds screening limit')
            actors.append(dict(actor_id=e['actor_id'],role=e['role'],kind=kind,source_type=e['type'],
                max_speed_mps=float(max(speeds)),max_abs_accel_mps2=float(max(abs(acc))),
                max_lateral_accel_mps2=float(max(lateral)),issues=issues))
        result['scenes'][sid]=actors
    write(PROJECT/'outputs/motion_review/reference_audit.json',result)
    print('Audited',sum(len(v) for v in result['scenes'].values()),'actors across',len(result['scenes']),'scenes')
    return result


if __name__=='__main__': audit()
