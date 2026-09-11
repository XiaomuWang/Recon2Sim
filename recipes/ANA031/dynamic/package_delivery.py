"""Build the reviewed ANA031 dynamic package and an explicit event-condition table."""
import ast
import csv
import hashlib
import json
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

P = Path(__file__).resolve().parents[1]
root = ET.parse(P / 'RainJunctionANA031_Timeline.xosc').getroot()
rows = []
for group in root.findall('.//ManeuverGroup'):
    entity = group.find('Actors/EntityRef').get('entityRef')
    for event in group.findall('Maneuver/Event'):
        conditions = event.findall('StartTrigger/ConditionGroup/Condition')
        time = event.find('.//SimulationTimeCondition')
        guard = event.find('.//StoryboardElementStateCondition')
        speed = event.find('.//AbsoluteTargetSpeed')
        rows.append(dict(entity=entity, event=event.get('name'),
            time_s=time.get('value'), time_rule=time.get('rule'),
            condition_edges=';'.join(c.get('conditionEdge') for c in conditions),
            condition_combination='AND within ConditionGroup',
            own_activation_dependency=guard.get('storyboardElementRef') if guard is not None else '',
            dependency_state=guard.get('state') if guard is not None else '',
            maximum_execution_count=event.get('maximumExecutionCount'),
            teleport=event.find('.//TeleportAction') is not None,
            route_waypoints=len(event.findall('.//Waypoint')),
            speed_mps=speed.get('value') if speed is not None else ''))
assert len(rows) == 1826
with (P / 'trigger_conditions.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

static_map = P.parent / 'environment_reconstruction_ANA031/RainJunctionANA031.xodr'
assert sha(static_map) == sha(P / static_map.name)
template = Path('C:/Users/Administrator/Desktop/模板/scenario - 2026-09-08T142648.948.xosc')
assert sha(template) == sha(P / 'evidence/source_template.xosc')
reports = json.loads((P / 'validation/xosc_validation.json').read_text())
assert len(reports) == 3 and all(r['xsd_pass'] and r['time_order_pass'] and r['entity_reference_pass'] for r in reports)
delivery = json.loads((P / 'validation/delivery_validation.json').read_text())
assert not delivery['runtime_verified'] and not delivery['off_driving_surface']
assert all(t['pass'] and t['events_reached'] == len(rows) for t in delivery['trigger_schedule_tests'])
assert json.loads((P / 'validation/protocol_tests.json').read_text())['pass']
assert not json.loads((P / 'validation/trajectory_validation.json').read_text())['estimated_bbox_overlaps']
for path in P.rglob('*.py'):
    ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))

excluded = {'protocol_run.json', 'delivery_manifest.json'}
files = sorted(p for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts
               and p.suffix not in {'.log', '.zip', '.pyc'} and p.name not in excluded)
manifest = dict(map_sha256=sha(static_map), source_template_sha256=sha(template),
    entities=12, vehicles_including_ego=11, pedestrians=1, event_count=len(rows),
    video_reconstruction_duration_s=63.7, xosc_timeout_s=64.1,
    target_carla_version='0.9.15', runtime_verified=False,
    files=[dict(path=p.relative_to(P).as_posix(), bytes=p.stat().st_size, sha256=sha(p)) for p in files])
manifest_path = P / 'delivery_manifest.json'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
files.append(manifest_path)
dest = P.parent / 'RainJunctionANA031_Dynamic_CARLA0915.zip'
with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for path in files:
        z.write(path, (Path(P.name) / path.relative_to(P)).as_posix())
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    for item in manifest['files']:
        assert hashlib.sha256(z.read(P.name + '/' + item['path'])).hexdigest() == item['sha256']
print(json.dumps(dict(package=str(dest), bytes=dest.stat().st_size, files=len(files),
    events=len(rows), sha256=sha(dest), zip_crc_and_file_hashes_pass=True), indent=2))
