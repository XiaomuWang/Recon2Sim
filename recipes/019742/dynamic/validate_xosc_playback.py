"""Offline checks of actual exported XML interpretation against original estimated trajectories."""
import sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from replay_xosc import compile_scene
from replay_carla import interpolate
d=json.loads((P/'scenario.json').read_text(encoding='utf-8'));mapping=json.loads((P/'template_compatible/entity_mapping.json').read_text(encoding='utf-8'));ids={r['source_id']:('ego' if r['entity']=='ego_vehicle' else r['entity']) for r in mapping};reports=[]
for suffix in ['Timeline','Timeline_Radians']:
 c=compile_scene(P/'template_compatible'/('UrbanBrake019742_'+suffix+'.xosc'),P/'UrbanBrake019742.xodr');byid={a['id']:a for a in c['actors']};errs=[]
 for a in d['actors']:
  b=byid[ids[a['id']]];err=0;he=0
  for s in a['samples'][::6]:
   t=min(b['end_t'],s['t']+.04);q=interpolate(b['samples'],t);err=max(err,math.hypot(s['x']-q['x'],s['y']-q['y']));he=max(he,abs((s['h']-q['h']+math.pi)%(2*math.pi)-math.pi))
  errs.append({'actor':a['id'],'max_xy_error_m':err,'max_heading_error_deg':math.degrees(he)})
 maxerr=max(e['max_xy_error_m'] for e in errs);reports.append({'file':suffix,'max_xy_error_m':maxerr,'per_actor':errs,'pass':maxerr<.35})
report={'method':'Parse generated XOSC routes, integrate time-triggered mean speeds; compare after 0.04s template startup shift at 5 Hz','reports':reports,'runtime_verified':False}
(P/'validation/xosc_playback_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({r['file']:r['max_xy_error_m'] for r in reports},indent=2));assert all(r['pass'] for r in reports)
