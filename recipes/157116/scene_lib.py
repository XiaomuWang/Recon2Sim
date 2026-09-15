"""Four-view-informed environment. Run with Blender 4.2 --background --python."""
import bpy,math,random,sys,json,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve()/'map'
random.seed(508656)
NAME='PonyFourView157116'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
 if c.name!='Collection' and c.users==0:bpy.data.collections.remove(c)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.0
scene.world.color=(.3,.35,.4)
collections={}
for n in ['Road','RoadLines','Sidewalk','Wall','Fence','Vegetation','Building','Props','Terrain','Lighting','Cameras']:
 c=bpy.data.collections.new(n);scene.collection.children.link(c);collections[n]=c
def link(o,cat):collections[cat].objects.link(o)
M={}
def material(name,color,rough=.8,metal=0,texture=None,normal=.3):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Specular IOR Level'].default_value=.25
 if texture:
  ns=m.node_tree.nodes;lk=m.node_tree.links
  for suf,slot in [('basecolor','Base Color'),('roughness','Roughness'),('normal','Normal')]:
   tex=ns.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'textures'/(texture+'_'+suf+'.png')),check_existing=True);tex.label=suf
   if suf!='basecolor':tex.image.colorspace_settings.name='Non-Color'
   if suf=='normal':
    nm=ns.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=normal;lk.new(tex.outputs['Color'],nm.inputs['Color']);lk.new(nm.outputs['Normal'],p.inputs[slot])
   else:lk.new(tex.outputs['Color'],p.inputs[slot])
 M[name]=m;return m
material('Concrete',(.44,.43,.39),texture='concrete',normal=.4)
material('RoadConcrete',(.4,.39,.35),texture='road',normal=.3)
material('Asphalt',(.2,.21,.2),texture='asphalt',normal=.45)
material('GreenHoarding',(.18,.29,.11),texture='hoarding',normal=.65)
material('Paving',(.43,.42,.38),texture='paving')
material('Earth',(.3,.26,.18),texture='soil')
material('Bark',(.24,.2,.14),texture='bark')
material('Galvanized',(.47,.5,.5),.38,.72)
material('DarkSteel',(.10,.13,.14),.48,.65)
material('PaintWhite',(.81,.8,.69),.92)
material('PaintYellow',(.75,.49,.07),.9)
material('CurbYellow',(.79,.57,.12),.85)
material('CurbBlack',(.038,.043,.043),.87)
material('Joint',(.055,.052,.046),1)
material('Patch',(.23,.235,.216),.96)
material('WhiteMetal',(.7,.74,.72),.42,.3)
material('WarningRed',(.62,.08,.07),.7)
material('SignBlue',(.025,.13,.38),.5,.1)
material('BuildingBeige',(.55,.49,.38),.86)
material('BuildingIvory',(.69,.69,.61),.8)
material('GlassBlue',(.15,.27,.3),.22,.62)
material('GlassDark',(.07,.14,.16),.25,.5)
material('Balcony',(.32,.32,.28),.72)
for i,col in enumerate([(.09,.17,.035),(.13,.23,.055),(.18,.29,.07),(.22,.34,.09),(.12,.25,.085),(.28,.36,.10)]):
 m=material('Leaf'+str(i),col,.88);m.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=.04
material('Grass',(.16,.25,.065),.97)
class Mesh:
 def __init__(self,name,cat):self.name=name;self.cat=cat;self.v=[];self.f=[];self.mi=[];self.uv=[];self.mats=[]
 def face(self,verts,mat,uv=None):
  if mat not in self.mats:self.mats.append(mat)
  j=len(self.v);self.v.extend(verts);self.f.append(tuple(range(j,j+len(verts))));self.mi.append(self.mats.index(mat))
  if uv is None:
   nor=(Vector(verts[1])-Vector(verts[0])).cross(Vector(verts[2])-Vector(verts[0]));axis=max(range(3),key=lambda i:abs(nor[i]));ax=[i for i in range(3) if i!=axis];uv=[(v[ax[0]]/3,v[ax[1]]/3) for v in verts]
  self.uv.extend(uv)
 def box(self,c,d,mat,h=0):
  x,y,z=c;dx,dy,dz=[v/2 for v in d];co=math.cos(h);si=math.sin(h)
  pts=[(x+a*co-b*si,y+a*si+b*co,z+cc) for a,b,cc in [(-dx,-dy,-dz),(dx,-dy,-dz),(dx,dy,-dz),(-dx,dy,-dz),(-dx,-dy,dz),(dx,-dy,dz),(dx,dy,dz),(-dx,dy,dz)]]
  for inds in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:self.face([pts[i] for i in inds],mat)
 def cyl(self,p,q,r1,r2,mat,n=8):
  p=Vector(p);q=Vector(q);w=(q-p).normalized();u=w.cross(Vector((0,1,0)) if abs(w.y)<.9 else Vector((1,0,0))).normalized();v=w.cross(u)
  a=[p+(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))*r1 for i in range(n)];b=[q+(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))*r2 for i in range(n)]
  for i in range(n):j=(i+1)%n;self.face([a[i],a[j],b[j],b[i]],mat)
  self.face(list(reversed(a)),mat);self.face(b,mat)
 def leaf(self,c,size,mat):
  c=Vector(c);phi=random.random()*math.tau;tilt=random.uniform(-.6,.6);u=Vector((math.cos(phi),math.sin(phi),tilt)).normalized()*size;v=Vector((-math.sin(phi),math.cos(phi),random.uniform(-1,1))).normalized()*size*.42
  self.face([c-u,c-v,c+u,c+v],mat,[(0,.5),(.5,0),(1,.5),(.5,1)])
 def done(self):
  if not self.f:return None
  me=bpy.data.meshes.new(self.name);me.from_pydata(self.v,[],self.f);me.update()
  for m in self.mats:me.materials.append(M[m])
  for p,i in zip(me.polygons,self.mi):p.material_index=i
  uv=me.uv_layers.new(name='UVMap')
  for x,u in zip(uv.data,self.uv):x.uv=u
  tag={'Road':'Road_Road','RoadLines':'Road_Marking','Sidewalk':'Road_Sidewalk'}.get(self.cat,self.cat)
  o=bpy.data.objects.new(NAME+'_'+tag+'_'+self.name,me);link(o,self.cat);return o
def sp(s,t,z=0):return pose(s,t,z)[:3]
def ribbon(m,a,b,t1,t2,z,mat,step=.7):
 n=max(1,math.ceil((b-a)/step))
 for i in range(n):
  u=a+(b-a)*i/n;v=a+(b-a)*(i+1)/n
  m.face([sp(u,t1,z),sp(v,t1,z),sp(v,t2,z),sp(u,t2,z)],mat,[(u/4,t1/4),(v/4,t1/4),(v/4,t2/4),(u/4,t2/4)])
def boxat(m,s,t,z,d,mat):m.box(sp(s,t,z),d,mat,pose(s)[3])
