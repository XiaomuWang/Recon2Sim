"""Reimport the generated FBX, audit its geometry/textures and render explicit offline evidence."""
import bpy
import csv
import json
import math
import sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

out=Path(sys.argv[sys.argv.index('--')+1]).resolve()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
cfg=read(out/'scene_config.json');mapping=read(out/'entity_mapping.json');name=cfg['map_name']
folder=out/'validation/fbx';folder.mkdir(parents=True,exist_ok=True)

def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]

bpy.ops.wm.open_mainfile(filepath=str(out/'map'/(name+'.blend')))
before={o.name:bounds(o) for o in bpy.context.scene.objects if o.type=='MESH'}
# Retain the reconstructed world/lights (especially rainy/night scenes).
for obj in list(bpy.context.scene.objects):
    if obj.type=='MESH':bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.import_scene.fbx(filepath=str(out/'map'/(name+'.fbx')),use_anim=False)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];after={o.name:bounds(o) for o in meshes}
missing=[n for n in before if n not in after]
max_error=max((max(abs(v[i][j]-after[n][i][j]) for i in range(2) for j in range(3)) for n,v in before.items() if n in after),default=0)
missing_textures=[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()]

def bvh(objects):
    vertices=[];polys=[]
    for o in objects:
        n=len(vertices);vertices.extend(o.matrix_world@v.co for v in o.data.vertices)
        polys.extend(tuple(n+i for i in p.vertices) for p in o.data.polygons)
    return BVHTree.FromPolygons(vertices,polys) if vertices else None

surface=bvh([o for o in meshes if any(token in o.name.lower() for token in ['_road_','_terrain_','_sidewalk_'])])
roads=bvh([o for o in meshes if '_road_road_' in o.name.lower()])
structures=bvh([o for o in meshes if any(token in o.name.lower() for token in ['_wall_','_fence_','_building_'])])
data={}
with (out/'trajectories.csv').open(encoding='utf-8-sig',newline='') as f:
    for r in csv.DictReader(f): data.setdefault(r['actor_id'],[]).append({k:(v if k=='actor_id' else float(v)) for k,v in r.items()})
audit=[]
for e in mapping['actors']:
    misses=0;obstacles=0;checks=0;examples=[];max_dz=0
    length=e['dimensions_m']['length']/2;width=e['dimensions_m']['width']/2
    for r in data[e['actor_id']][::6]:
        h=-math.radians(r['yaw_carla_deg']);co,si=math.cos(h),math.sin(h)
        for dx,dy in [(0,0),(-length,-width),(-length,width),(length,-width),(length,width)]:
            x=r['x']+co*dx-si*dy;y=-r['y']+si*dx+co*dy;z=r['z'];checks+=1
            hit=surface.ray_cast(Vector((x,y,z+1)),Vector((0,0,-1)),2) if surface else (None,)
            if hit[0] is None:
                misses+=1
                if len(examples)<5: examples.append(dict(t=r['replay_time_s'],x=x,y=y))
            else: max_dz=max(max_dz,abs(hit[0].z-z))
            hit=structures.ray_cast(Vector((x,y,z+e['dimensions_m']['height'])),Vector((0,0,-1)),max(.1,e['dimensions_m']['height']-.1)) if structures else (None,)
            if hit[0] is not None: obstacles+=1
    audit.append(dict(actor_id=e['actor_id'],checks=checks,surface_missing=misses,structure_ray_hits=obstacles,max_surface_height_error_m=max_dz,examples=examples))
wps=read(out/'validation/waypoints.json');waypoint_misses=0;waypoint_max_dz=0
for w in wps:
    hit=roads.ray_cast(Vector((w['x'],-w['y'],w['z']+1)),Vector((0,0,-1)),2) if roads else (None,)
    if hit[0] is None: waypoint_misses+=1
    else: waypoint_max_dz=max(waypoint_max_dz,abs(hit[0].z-w['z']))
from io_scene_fbx import parse_fbx
fbx,version=parse_fbx.parse(str(out/'map'/(name+'.fbx')))
objects=next(e for e in fbx.elems if e.id==b'Objects')
embedded=sum(e.id==b'Video' and any(c.id==b'Content' and c.props and len(c.props[0])>100 for c in e.elems) for e in objects.elems)
report=dict(roundtrip_pass=not missing and max_error<.002,missing_objects=missing,max_bounds_error_m=max_error,
            mesh_count=len(meshes),missing_textures=missing_textures,embedded_texture_count=embedded,fbx_version=version,
            xodr_waypoint_checks=len(wps),xodr_waypoint_surface_misses=waypoint_misses,max_xodr_surface_height_error_m=waypoint_max_dz,
            footprint_checks=audit,carla_runtime_verified=False,
            method='Generated FBX reimport; CARLA waypoint rays; actor center+4 estimated footprint corners every sixth sample. Not swept-volume collision.')
(folder/'fbx_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if missing or max_error>.002 or missing_textures: raise RuntimeError('FBX roundtrip/material validation failed')

# Offline render contains this actual FBX and estimated-size actor proxies.
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
scene.render.resolution_x=800;scene.render.resolution_y=450;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
colors={'ego':(.98,.63,.05,1),'accident_related':(.9,.10,.08,1),'context':(.03,.5,.7,1)};materials={}
for role,color in colors.items():
    mat=bpy.data.materials.new('Actor_'+role);mat.diffuse_color=color;materials[role]=mat
actors={}
rubber=bpy.data.materials.new('ProxyRubber');rubber.diffuse_color=(.025,.03,.035,1)
glass=bpy.data.materials.new('ProxyGlass');glass.diffuse_color=(.035,.10,.15,1)

def part(parent,position,size,material,shape='cube',rotation=None):
    if shape=='sphere':bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.5)
    elif shape=='cylinder':bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.5,depth=1)
    else:bpy.ops.mesh.primitive_cube_add(size=1)
    obj=bpy.context.object;obj.parent=parent;obj.location=position;obj.dimensions=size
    if rotation:obj.rotation_euler=rotation
    obj.data.materials.append(material)
    return obj

for e in mapping['actors']:
    dims=e['dimensions_m']
    obj=bpy.data.objects.new('Review_'+e['actor_id'],None);scene.collection.objects.link(obj);actors[e['actor_id']]=obj
    l,w,h=dims['length'],dims['width'],dims['height'];mat=materials[e['role']]
    if e['type']=='pedestrian':
        part(obj,(0,0,h*.58),(l*.65,w*.65,h*.48),mat,'cylinder')
        part(obj,(0,0,h*.91),(h*.18,h*.18,h*.18),mat,'sphere')
        for y in [-w*.2,w*.2]:part(obj,(0,y,h*.21),(l*.26,w*.26,h*.42),rubber,'cylinder')
    elif e['type'] in ['motorbike','bicycle','tricycle']:
        part(obj,(0,0,h*.34),(l*.8,w*.7,h*.22),mat)
        part(obj,(0,0,h*.72),(l*.22,w*.6,h*.38),mat,'cylinder')
        part(obj,(0,0,h*.94),(h*.12,h*.12,h*.12),mat,'sphere')
        for x in [-l*.33,l*.33]:part(obj,(x,0,h*.18),(h*.36,w*.2,h*.36),rubber,'cylinder',(math.pi/2,0,0))
    else:
        part(obj,(0,0,h*.36),(l,w,h*.44),mat)
        if e['type'] in ['truck','bus','van','sweeper']:
            part(obj,(-l*.15,0,h*.70),(l*.66,w*.95,h*.60),mat)
            part(obj,(l*.31,0,h*.70),(l*.3,w*.94,h*.50),glass)
        else:
            part(obj,(-l*.05,0,h*.75),(l*.54,w*.85,h*.50),mat)
            part(obj,(l*.23,0,h*.76),(l*.035,w*.78,h*.36),glass)
            for y in [-w*.431,w*.431]:part(obj,(-l*.06,y,h*.78),(l*.46,.015,h*.30),glass)
        for x in [-l*.32,l*.32]:
            for y in [-w*.48,w*.48]:part(obj,(x,y,h*.19),(h*.38,w*.14,h*.38),rubber,'cylinder',(math.pi/2,0,0))
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.lens=24

def pose_at(rows,t):
    if t<rows[0]['replay_time_s'] or t>rows[-1]['replay_time_s']: return None
    return min(rows,key=lambda r:abs(r['replay_time_s']-t))

def aim(position,target):
    camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()

critical={'014346':17,'019742':110,'016955':114,'024388':64,'0512189':85,'0508656':82,'ANA031':26.8}
times=sorted(set([0,max(0,critical[cfg['scene_id']]-3),critical[cfg['scene_id']],min(cfg['duration_s'],critical[cfg['scene_id']]+4)]))
renders=[]
for idx,t in enumerate(times):
    for e in mapping['actors']:
        p=pose_at(data[e['actor_id']],t);obj=actors[e['actor_id']];obj.hide_render=p is None
        for child in obj.children:child.hide_render=p is None
        if p:
            obj.location=(p['x'],-p['y'],p['z']+.04);obj.rotation_euler[2]=-math.radians(p['yaw_carla_deg'])
    p=pose_at(data[mapping['ego_actor_id']],t);h=-math.radians(p['yaw_carla_deg'])
    aim((p['x']-8*math.cos(h)+3*math.sin(h),-p['y']-8*math.sin(h)-3*math.cos(h),p['z']+6),
        (p['x']+7*math.cos(h),-p['y']+7*math.sin(h),p['z']+1))
    path=folder/('ego_%02d.png'%idx);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    renders.append(dict(file=path.name,replay_time_s=t,renderer='Blender reimported FBX + trajectory proxies; NOT CARLA'))
# Top-down view of the complete reconstructed route.
xs=[w['x'] for w in wps];ys=[-w['y'] for w in wps];cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2
camera.data.type='ORTHO';camera.data.ortho_scale=max((max(xs)-min(xs))*1.1,(max(ys)-min(ys))*1.1*800/450)
aim((cx,cy,300),(cx,cy,0));scene.render.filepath=str(folder/'fbx_aerial.png');bpy.ops.render.render(write_still=True)
(folder/'renders.json').write_text(json.dumps(renders,indent=2),encoding='utf-8')
print('FBX_REVIEW_COMPLETE',json.dumps({k:v for k,v in report.items() if k!='footprint_checks'}),flush=True)
