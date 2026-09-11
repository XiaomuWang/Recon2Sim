import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];NAME='LuoboTurn024388'
sys.path.insert(0,str(ROOT/'scripts'))
from road_layout import path_pose
bpy.ops.wm.open_mainfile(filepath=str(ROOT/(NAME+'.blend')))
def bounds(o):
 vs=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
before={o.name:bounds(o) for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(ROOT/(NAME+'.fbx')),use_anim=False)
after={o.name:bounds(o) for o in bpy.context.scene.objects if o.type=='MESH'}
errs=[];maxerr=0
for n,b in before.items():
 if n not in after:errs.append('missing '+n);continue
 err=max(abs(b[i][j]-after[n][i][j]) for i in range(2) for j in range(3));maxerr=max(maxerr,err)
 if err>.002:errs.append([n,err])
verts=[];polys=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH' and '_Road_Road_' in o.name:
  start=len(verts);verts.extend([o.matrix_world@v.co for v in o.data.vertices]);polys.extend([tuple(start+i for i in p.vertices) for p in o.data.polygons])
bvh=BVHTree.FromPolygons(verts,polys)
misses=[];zerr=0;points=json.loads((ROOT/'validation/carla_waypoints.json').read_text())
for p in points:
 x,y,z=p['xyz_rh'];hit=bvh.ray_cast(Vector((x,y,z+1)),Vector((0,0,-1)),2)
 if hit[0] is None:misses.append(p)
 else:zerr=max(zerr,abs(hit[0].z-z))
report={'fbx_reimport_pass':not errs,'source_mesh_objects':len(before),'imported_mesh_objects':len(after),'maximum_bounds_error_m':maxerr,'mesh_errors':errs,'carla_waypoints_tested':len(points),'road_surface_missing_hits':misses,'max_waypoint_to_mesh_height_m':zerr,'textures_missing':[i.filepath for i in bpy.data.images if i.source=='FILE' and not Path(bpy.path.abspath(i.filepath)).exists() and not i.packed_file],'runtime_tested':False}
from io_scene_fbx import parse_fbx
fbx,version=parse_fbx.parse(str(ROOT/(NAME+'.fbx')))
settings=next(e for e in fbx.elems if e.id==b'GlobalSettings');props=next(e for e in settings.elems if e.id==b'Properties70')
header={e.props[0].decode():e.props[-1] for e in props.elems if e.id==b'P' and e.props[0] in [b'UpAxis',b'UpAxisSign',b'FrontAxis',b'FrontAxisSign',b'CoordAxis',b'CoordAxisSign',b'UnitScaleFactor']}
objects=next(e for e in fbx.elems if e.id==b'Objects');embedded=[e for e in objects.elems if e.id==b'Video' and any(c.id==b'Content' and c.props and len(c.props[0])>100 for c in e.elems)]
report['fbx_version']=version;report['fbx_axis_units']=header;report['embedded_texture_count']=len(embedded)
edge_misses=[];edge_tests=0
for path in json.loads((ROOT/'validation/junction_paths.json').read_text()):
 for i in range(1,161):
  s=path['length']*i/162
  for t in [-1.60,0,1.60]:
   x,y,z,h=path_pose(path,s,t);edge_tests+=1;hit=bvh.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),2)
   if hit[0] is None:edge_misses.append({'road':path['id'],'s':s,'lateral_offset':t,'point':[x,y]})
report['junction_lane_band_samples']=edge_tests;report['junction_lane_band_missing_hits']=edge_misses
(ROOT/'validation/fbx_validation.json').write_text(json.dumps(report,indent=2));print('VALIDATION',json.dumps(report),flush=True)
assert not errs and not misses and not edge_misses and zerr<.01 and len(embedded)>=21
assert header['UpAxis']==2 and header['FrontAxis']==1 and header['FrontAxisSign']==-1 and header['CoordAxis']==0 and header['CoordAxisSign']==1 and header['UnitScaleFactor']==100
