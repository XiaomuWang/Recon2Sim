import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'environment_reconstruction_0508656/MeituanBrake0508656.blend'))
def bvh(objects):
 vs=[];polys=[]
 for o in objects:
  n=len(vs);vs.extend([o.matrix_world@v.co for v in o.data.vertices]);polys.extend([tuple(n+i for i in p.vertices) for p in o.data.polygons])
 return BVHTree.FromPolygons(vs,polys)
mesh=[o for o in bpy.context.scene.objects if o.type=='MESH']
road=bvh([o for o in mesh if '_Road_Road_' in o.name])
ob=bvh([o for o in mesh if any(t in o.name for t in ['_Building_','_Sidewalk_','_Wall_','_Fence_'])])
d=json.loads((P/'scenario.json').read_text(encoding='utf-8'));rows=[]
for a in d['actors']:
 missing=[];blocked=[];checks=0;l=a['dimensions_m']['length']/2;w=a['dimensions_m']['width']/2
 for s in a['samples'][::6]:
  h=s['h'];co=math.cos(h);si=math.sin(h)
  for k,(xx,yy) in enumerate([(0,0),(-l,-w),(l,-w),(l,w),(-l,w)]):
   x=s['x']+xx*co-yy*si;y=s['y']+xx*si+yy*co;checks+=1
   hit=road.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),1.15)
   if hit[0] is None:missing.append({'t':s['t'],'point':k,'xy':[x,y]})
   hit=ob.ray_cast(Vector((x,y,1.95)),Vector((0,0,-1)),1.90)
   if hit[0] is not None:blocked.append({'t':s['t'],'point':k,'xyz':list(hit[0])})
 rows.append({'id':a['id'],'checks':checks,'road_surface_missing_count':len(missing),'road_surface_missing_examples':missing[:10],'static_structure_ray_hits':len(blocked),'static_structure_examples':blocked[:10]})
report={'method':'Center and four estimated footprint-corner downward rays every 0.2 s against delivered Blender road and structural meshes. Not a swept-volume collision or CARLA engine test.','actors':rows,'runtime_verified':False}
(P/'validation/static_surface_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps([r for r in rows if r['road_surface_missing_count'] or r['static_structure_ray_hits']],indent=2))
