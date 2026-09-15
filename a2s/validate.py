"""Offline CARLA parser and trajectory audit; never claims server execution."""
import csv
import math
from pathlib import Path
import cv2
import carla
from lxml import etree
from .common import PROJECT, WORKSPACE, VIEWS, read, write, tracks, sha


def validate(sid):
    out=PROJECT/'outputs'/sid
    scene=read(out/'scene_config.json'); config=read(PROJECT/'configs'/(sid+'.json'))
    entities=read(out/'entity_mapping.json')['actors']; data=tracks(out/'trajectories.csv')
    road=out/'map'/(scene['map_name']+'.xodr')
    m=carla.Map(scene['map_name'],road.read_text(encoding='utf-8'))
    wps=m.generate_waypoints(1.0)
    write(out/'validation'/'waypoints.json',[dict(x=w.transform.location.x,y=w.transform.location.y,z=w.transform.location.z,
          yaw=w.transform.rotation.yaw,width=w.lane_width,road_id=w.road_id,lane_id=w.lane_id,s=w.s) for w in wps])
    schema=PROJECT/'work'/('environment_reconstruction_'+sid)/'validation/schema/opendrive_17_core.xsd'
    xsd_ok=None; xsd_error=None
    if schema.exists():
        try:
            etree.XMLSchema(etree.parse(str(schema))).assertValid(etree.parse(str(road))); xsd_ok=True
        except etree.Error as e: xsd_ok=False; xsd_error=str(e)
    audits=[]; exceptions=[]; associations=[]
    for e in entities:
        rows=data[e['actor_id']]; outside=[]; max_dist=0; height_error=0
        for r in rows:
            loc=carla.Location(x=r['x'],y=r['y'],z=r['z'])
            nearest=m.get_waypoint(loc,project_to_road=True,lane_type=carla.LaneType.Any)
            if nearest is None:
                excess=1e6
            else:
                p=nearest.transform.location
                distance=math.hypot(r['x']-p.x,r['y']-p.y)
                excess=max(0,distance-nearest.lane_width/2)
                max_dist=max(max_dist,excess)
                if excess<=config['road_margin_m']: height_error=max(height_error,abs(r['z']-p.z))
            associations.append(dict(actor_id=e['actor_id'],replay_time_s=r['replay_time_s'],
                road_id=nearest.road_id if nearest else '',lane_id=nearest.lane_id if nearest else '',s=nearest.s if nearest else '',
                xodr_margin_excess_m=excess,classification='lane_area' if excess<=config['road_margin_m'] else 'check_fbx_scene_area',
                xodr_sha256=scene['provenance']['xodr_sha256']))
            if excess>config['road_margin_m']:
                outside.append(r)
                if len(outside)<=15:
                    exceptions.append(dict(actor_id=e['actor_id'],t=r['replay_time_s'],x=r['x'],y=r['y'],excess_m=excess,
                                           disposition='REVIEW: may be sidewalk/driveway/parking; must check FBX surface, never auto-snap'))
        audits.append(dict(actor_id=e['actor_id'],role=e['role'],samples=len(rows),start_s=rows[0]['replay_time_s'],end_s=rows[-1]['replay_time_s'],
              off_xodr_sample_count=len(outside),max_distance_beyond_lane_halfwidth_m=max_dist,max_lane_height_difference_m=height_error,
              max_speed_m_s=max(r['speed'] for r in rows), stationary=e['stationary']))
    video={}
    for v in VIEWS:
        path=WORKSPACE/scene['source_recording'] if scene.get('source_recording') else WORKSPACE/scene['video_dir']/scene.get('video_files',{}).get(v,v+'.mp4'); cap=cv2.VideoCapture(str(path))
        fps=cap.get(cv2.CAP_PROP_FPS); frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration=frames/fps if fps else 0
        start=scene['source_video_start_s']+scene['camera_file_time_offsets_s'][v]
        end=scene['source_video_end_s']+scene['camera_file_time_offsets_s'][v]
        video[v]=dict(path=str(path),fps=fps,frames=frames,duration_s=duration,width=int(cap.get(3)),height=int(cap.get(4)),
                      reconstruction_file_start_s=start,reconstruction_file_end_s=end,
                      missing_head_s=max(0,-start),missing_tail_s=max(0,end-duration),
                      unmodeled_video_head_s=max(0,start),unmodeled_video_tail_s=max(0,duration-end))
        cap.release()
    write(out/'validation'/'video_metadata.json',video)
    write(out/'validation'/'road_exceptions.json',exceptions)
    with (out/'road_associations.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(associations[0]));writer.writeheader();writer.writerows(associations)
    result=dict(scene_id=sid,carla_client_version=carla.Client('localhost',2000).get_client_version(),
          xodr_parser_pass=len(wps)>0,xodr_schema_pass=xsd_ok,xodr_schema_error=xsd_error,waypoint_count=len(wps),
          static_map_hash_matches=sha(road)==scene['provenance']['xodr_sha256'],actors=len(entities),total_samples=sum(len(r) for r in data.values()),
          all_actor_ids_preserved=set(data)=={e['actor_id'] for e in entities},trajectory_audit=audits,
          trajectory_centers_within_xodr_margin=all(a['off_xodr_sample_count']==0 for a in audits),
          all_raw_video_actors_verified=False,metric_accuracy_verified=False,carla_runtime_verified=False,
          validation_scope='CARLA client parser + every trajectory center, lane halfwidth with 0.5m tolerance; not swept-volume/legal-road test',
          acceptance='REVIEW_REQUIRED: video completeness, off-road FBX coverage and engine recording are separate gates')
    write(out/'validation'/'offline_validation.json',result)
    print(sid, 'actors',len(entities),'off-XODR samples',sum(a['off_xodr_sample_count'] for a in audits),flush=True)
    return result
