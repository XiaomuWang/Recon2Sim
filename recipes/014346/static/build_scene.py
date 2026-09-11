"""Four-view-informed environment. Run with Blender 4.2 --background --python."""
import bpy,math,random,sys,json,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from road_layout import pose,LENGTH,WIDTH
random.seed(14346)
NAME='NanshanGate014346'
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
print('Building road and architecture...',flush=True)
for a in range(0,210,30):
 m=Mesh('Road_Concrete_%03d'%a,'Road');ribbon(m,-.05 if a==0 else a,min(a+30,210.05) if a<180 else 210.05,-2.9,2.9,0,'RoadConcrete');m.done()
marks=Mesh('RoadLine_EdgeAndCenter','RoadLines')
for a,b in [(0,93.9),(106.1,210)]:ribbon(marks,a,b,-2.65,-2.55,.012,'PaintWhite')
ribbon(marks,0,210,2.55,2.65,.012,'PaintWhite')
for a,b,col in [(0,92,'PaintWhite'),(108,210,'PaintYellow')]:ribbon(marks,a,b,-.055,.055,.013,col)
# Construction road concrete slabs, irregular repair patches and fine cracks.
details=Mesh('Slab_Joints_Repairs','RoadLines')
for s in range(3,210,5):ribbon(details,s,s+.018,-2.88,2.88,.008,'Joint')
for k in range(90):
 s=random.uniform(2,208);t=random.uniform(-2.45,2.45);size=random.uniform(.1,.5)
 vv=[sp(s+math.cos(i*math.tau/9)*size,t+math.sin(i*math.tau/9)*size*.5,.009) for i in range(9)]
 details.face(vv,'Patch')
for k in range(38):
 s=random.uniform(2,206);t=random.uniform(-2.6,2.6)
 for j in range(random.randint(3,8)):
  sn=s+random.uniform(.1,.35);tn=t+random.uniform(-.16,.16)
  details.face([sp(s,t,.01),sp(sn,tn,.01),sp(sn,tn+.008,.01),sp(s,t+.008,.01)],'Joint');s,t=sn,tn
for s in [121,139,160]:
 for d in [0,.45,.9]:ribbon(marks,s+d,s+d+.15,-2.45,-.15,.016,'PaintYellow')
# Entry zebra crossing, visible at 52s.
for t in [-2.45,-1.55,-.65,.25,1.15,2.05]:ribbon(marks,2,5,t,t+.45,.016,'PaintWhite')
marks.done();details.done()
side=Mesh('Sidewalk_Curbs','Sidewalk')
for a in range(210):
 boxat(side,a+.5,3.05,.09,(1,.3,.18),'Concrete')
 ribbon(side,a,a+1,3.2,4.15,.14,'Paving')
 if not 94<=a<=105:
  boxat(side,a+.5,-3.05,.1,(1,.3,.2),'Concrete');ribbon(side,a,a+1,-4.05,-3.2,.17,'Paving')
  if a>106:boxat(side,a+.5,-3.72,.31,(.95,.34,.38),'CurbYellow' if a%2==0 else 'CurbBlack')
side.done()
pave=Mesh('Paving_Joints','Sidewalk')
for a in range(0,210):
 ribbon(pave,a,a+.013,3.2,4.15,.145,'Joint')
 if not 94<=a<=106:ribbon(pave,a,a+.013,-4.05,-3.2,.175,'Joint')
for t in [3.48,3.76,4.04]:ribbon(pave,0,210,t,t+.008,.146,'Joint')
pave.done()
# Authentic W-beam profiles, continuous except at observed gate.
guard=Mesh('GuardRail_WBeam','Fence');posts=Mesh('GuardRail_PostsBolts','Fence')
profile=[(-.09,.00),(-.045,.04),(.0,.085),(.055,.09),(.09,.02),(.13,.00),(.17,.02),(.205,.09),(.26,.085),(.305,.04),(.34,.00)]
for side_sign,intervals in [(1,[(5,210)]),(-1,[(106.1,210)])]:
 for a,b in intervals:
  for k in range(math.ceil((b-a)/1)):
   u=a+k;v=min(b,u+1)
   for (z1,dy1),(z2,dy2) in zip(profile,profile[1:]):
    guard.face([sp(u,side_sign*(3.3-dy1),.69+z1),sp(v,side_sign*(3.3-dy1),.69+z1),sp(v,side_sign*(3.3-dy2),.69+z2),sp(u,side_sign*(3.3-dy2),.69+z2)],'Galvanized')
  for k in range(math.ceil((b-a)/2)):
   s=a+k*2;boxat(posts,s,side_sign*3.38,.58,(.12,.14,.94),'Galvanized')
   posts.cyl(sp(s,side_sign*3.17,.82),sp(s,side_sign*3.12,.82),.019,.019,'DarkSteel',8)
guard.done();posts.done()
# Retaining wall with joints, top coping, stepped tall supports and upper railing.
def wh(s):return 1.15+min(3.8,max(0,(s-32)*.035))
wall=Mesh('RetainingWall_StainedConcrete','Wall');cap=Mesh('RetainingWall_Coping','Wall');fence=Mesh('RetainingWall_TopRailing','Fence');ground=Mesh('Left_Bank','Terrain')
for s in range(210):
 h1=wh(s);h2=wh(s+1)
 wall.face([sp(s,4.2,.14),sp(s+1,4.2,.14),sp(s+1,4.2,h2),sp(s,4.2,h1)],'Concrete',[(s/4,0),((s+1)/4,0),((s+1)/4,h2/4),(s/4,h1/4)])
 ground.face([sp(s,4.4,h1-.1),sp(s+1,4.4,h2-.1),sp(s+1,19,5.1),sp(s,19,5.1)],'Grass')
 boxat(cap,s+.5,4.3,(h1+h2)/2,(1,.5,.14),'Concrete')
 if s%5==0:boxat(cap,s,4.09,wh(s)/2,(.2,.23,wh(s)),'Concrete')
 if s>82:
  fence.cyl(sp(s,4.4,wh(s)+.1),sp(s,4.4,wh(s)+1.1),.025,.025,'DarkSteel')
  fence.cyl(sp(s,4.4,wh(s)+1.1),sp(s+1,4.4,wh(s+1)+1.1),.03,.03,'DarkSteel')
  for off in [.25,.5,.75]:fence.cyl(sp(s+off,4.4,wh(s+off)+.15),sp(s+off,4.4,wh(s+off)+1.02),.012,.012,'DarkSteel',5)
wall.done();cap.done();ground.done();fence.done()
# Green turf-faced temporary panels with light gray uprights.
hoard=Mesh('Hoarding_GreenPanels','Fence');trim=Mesh('Hoarding_Frame','Fence')
for a,b in [(0,94),(106,210)]:
 for k in range(math.ceil((b-a)/2.5)):
  s=a+k*2.5;e=min(b,s+2.5)
  for t1,t2 in [(-4.08,-3.96)]:
   hoard.face([sp(s,t2,.2),sp(s,t2,3.4),sp(e,t2,3.4),sp(e,t2,.2)],'GreenHoarding',[(s/2,0),(s/2,1.6),(e/2,1.6),(e/2,0)])
   hoard.face([sp(e,t1,.2),sp(e,t1,3.4),sp(s,t1,3.4),sp(s,t1,.2)],'GreenHoarding')
  boxat(trim,s,-4.02,1.78,(.07,.17,3.4),'WhiteMetal')
  boxat(trim,(s+e)/2,-4.02,3.42,(e-s,.18,.07),'Galvanized')
  if k%4==0:boxat(trim,s,-4.02,3.5,(.08,.08,.1),'WarningRed')
# Gate return walls define an opening rather than a false green surface.
for x in [-6,6]:
 hoard.box((x,-13,1.7),(.13,18,3.4),'GreenHoarding')
 for y in [-4,-7,-10,-13,-16,-19,-22]:trim.box((x,y,1.75),(.15,.12,3.5),'WhiteMetal')
hoard.done();trim.done()
drive=Mesh('Road_GateApron','Road');drive.box((0,-17.45,-.065),(12,29.1,.13),'RoadConcrete');drive.done()
yard=Mesh('Worksite_Ground','Terrain');yard.box((6,-39,-.25),(62,32,.3),'Earth');yard.done()
# Observed road hoarding text as mesh, not a photograph containing vehicle artifacts.
try:font=bpy.data.fonts.load('C:/Windows/Fonts/msyhbd.ttc')
except:font=None
for s,text in [(78,'南山永不止步'),(119,'南山永不止步'),(151,'生态南山  山海连城'),(188,'山海连城')]:
 cu=bpy.data.curves.new('Observed_Lettering','FONT');cu.body=text;cu.size=.42;cu.extrude=.001;cu.align_x='CENTER'
 if font:cu.font=font
 o=bpy.data.objects.new(NAME+'_Fence_Lettering',cu);link(o,'Fence');o.location=sp(s,-3.947,2.5);o.rotation_euler=(math.pi/2,0,math.pi+pose(s)[3]);cu.materials.append(M['PaintWhite'])
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
# Simplified observed white city silhouettes near the base of green hoarding.
logos=Mesh('Hoarding_WhiteSkyline','Fence')
for s in [14,43,86,115,172,204]:
 for j in range(5):
  u=s+j*.17;z=random.uniform(.3,.9)
  logos.face([sp(u,-3.94,.25),sp(u,-3.94,z),sp(u+.12,-3.94,z+.06),sp(u+.12,-3.94,.25)],'PaintWhite')
logos.done()
props=Mesh('Site_SafetyAndDrainage','Props')
for s in [5,20,36,52,68,86,93.5,106.5]:
 p=sp(s,-3.4,.17);props.cyl(p,(p[0],p[1],p[2]+.75),.26,.22,'PaintWhite',16)
 for row in range(3):
  for j in range(8):
   if (row+j)%2:
    a=j*math.tau/8;b=(j+1)*math.tau/8;r=.265-row*.0107
    props.face([(p[0]+r*math.cos(a),p[1]+r*math.sin(a),p[2]+.05+row*.2),(p[0]+r*math.cos(b),p[1]+r*math.sin(b),p[2]+.05+row*.2),(p[0]+(r-.013)*math.cos(b),p[1]+(r-.013)*math.sin(b),p[2]+.25+row*.2),(p[0]+(r-.013)*math.cos(a),p[1]+(r-.013)*math.sin(a),p[2]+.25+row*.2)],'WarningRed')
 props.cyl((p[0],p[1],p[2]+.68),(p[0],p[1],p[2]+.78),.24,.24,'CurbYellow',16)
for s in range(8,210,16):
 boxat(props,s,2.78,.013,(.65,.25,.024),'DarkSteel')
 for j in range(8):boxat(props,s-.28+j*.08,2.78,.031,(.025,.25,.019),'Galvanized')
for x,y in [(-.3,-23),(2,-24),(3,-26)]:
 for j in range(10):props.box((x+j*.1,y,.18+j%3*.05),(.065,3,.07),'Balcony')
props.done()
print('Building detailed vegetation...',flush=True)
# Leaf-based broadleaf prototypes: branches and thousands of individual leaves, no billboard trees.
tree_protos=[]
for variant in range(5):
 m=Mesh('Tree_Prototype_%d'%variant,'Vegetation');height=random.uniform(7.5,10.5)
 m.cyl((0,0,0),(.1,-.08,height*.66),.22,.09,'Bark',10)
 clusters=[]
 for b in range(15):
  ang=b*2.4;z=height*random.uniform(.5,.85);r=random.uniform(1.7,3.2);end=(math.cos(ang)*r,math.sin(ang)*r,z+random.uniform(.6,1.8))
  m.cyl((.08,0,z*.65),end,.075,.015,'Bark',7);clusters.append(end)
 for c in clusters:
  for j in range(330):
   u=random.random();v=random.random();theta=u*math.tau;zz=2*v-1;rr=random.random()**(1/3);rd=math.sqrt(1-zz*zz)
   pos=(c[0]+1.7*rr*rd*math.cos(theta),c[1]+1.7*rr*rd*math.sin(theta),c[2]+1.2*rr*zz)
   m.leaf(pos,random.uniform(.09,.19),'Leaf'+str(random.randrange(6)))
 o=m.done();tree_protos.append(o);o.hide_render=True;o.hide_viewport=True
def tree(x,y,z,scale=1,i=None):
 proto=tree_protos[i if i is not None else random.randrange(5)];o=bpy.data.objects.new(NAME+'_Vegetation_Tree',proto.data);link(o,'Vegetation');o.location=(x,y,z);o.scale=(scale,scale,scale);o.rotation_euler.z=random.uniform(0,math.tau);return o
for s in range(5,205,10):
 p=sp(s,7,wh(s)+.2);tree(*p,random.uniform(.85,1.2))
 if s<88:tree(*sp(s,13,5.2),random.uniform(.8,1.15))
for s in [9,30,54,78,118,145,175,204]:tree(*sp(s,-9,0),random.uniform(.9,1.1))
# Hanging vines track the wall's top edge and reveal concrete in irregular gaps.
for a in range(0,210,15):
 ivy=Mesh('Ivy_%03d'%a,'Vegetation')
 for k in range(85):
  s=random.uniform(a,min(a+15,210));h=wh(s);length=random.uniform(.25,min(h,2.5));t=4.12-random.uniform(.04,.18)
  for j in range(max(2,int(length/.14))):
   z=h-j*.14;ss=s+math.sin(j*.8+k)*.065
   if j:
    ivy.cyl(sp(ss,t,z),sp(ss+.03,t,z+.14),.007,.006,'Bark',4)
   for l in range(3):ivy.leaf(sp(ss+random.uniform(-.14,.14),t-random.uniform(0,.12),z+random.uniform(-.1,.1)),random.uniform(.065,.13),'Leaf'+str(random.randrange(6)))
 for k in range(400):
  s=random.uniform(a,min(a+15,210));t=random.uniform(4.5,8);z=wh(s)+(t-4.5)/14*(5.1-wh(s))
  ivy.leaf(sp(s,t,z+random.uniform(.02,.18)),.15,'Leaf'+str(random.randrange(6)))
 ivy.done()
# Boulevard context seen in initial/front/back views. Visual context is outside the precision road network.
bl=Mesh('Boulevard_Context','Terrain');bl.box((-230,29,4.39),(410,17,.22),'Asphalt');bl.box((-230,41,4.45),(410,5,.3),'Grass');bl.box((-230,47,4.39),(410,7,.22),'Asphalt')
bl.box((-230,17.2,4.5),(410,4.2,.42),'Grass');bl.done()
bm=Mesh('Boulevard_ContextMarking','RoadLines')
for x in range(-429,-27,9):
 for y in [25.5,29,32.5]:bm.box((x,y,4.515),(4,.12,.014),'PaintWhite')
for y in [20.65,37.25,43.7,50.3]:bm.box((-230,y,4.515),(407,.13,.014),'PaintWhite')
bm.done()
hedge=Mesh('Boulevard_Hedge','Vegetation')
for x in range(-430,-24,4):
 hedge.box((x,17.1,4.88),(4,1.5,.55),'Leaf2')
 for j in range(55):hedge.leaf((x+random.uniform(-2,2),17.1+random.uniform(-.9,.9),5.15+random.uniform(-.15,.18)),.18,'Leaf'+str(random.randrange(6)))
hedge.done()
for x in range(-415,-20,20):
 tree(x,42,4.65,.9);tree(x,54,4.65,1.0)
# Slender palms are a distinctive feature in left/front 18-50 seconds.
palms=Mesh('Boulevard_Palms','Vegetation')
for x in range(-416,-35,15):
 y=40.1;base=4.6;h=random.uniform(9,12)
 palms.cyl((x,y,base),(x+.18,y,base+h),.19,.12,'Bark',10)
 for j in range(int(h/.28)):
  palms.cyl((x,y,base+j*.28),(x,y,base+j*.28+.06),.202,.198,'Bark',10)
 for f in range(12):
  ang=f*math.tau/12+random.uniform(-.12,.12);co=math.cos(ang);si=math.sin(ang)
  prev=(x,y,base+h)
  for j in range(1,19):
   u=j/18;r=u*3.8;z=base+h+1.9*math.sin(u*math.pi)-1.2*u;pt=(x+r*co,y+r*si,z)
   palms.cyl(prev,pt,.018*(1-u)+.004,.016*(1-u)+.003,'Leaf1',5)
   for side in [-1,1]:
    length=(1-u)*.7+.13;tip=(pt[0]-si*side*length-co*.15,pt[1]+co*side*length-si*.15,z-.35)
    palms.face([pt,(tip[0]-.025*co,tip[1]-.025*si,tip[2]),(tip[0]+.025*co,tip[1]+.025*si,tip[2]),(pt[0]+.07*co,pt[1]+.07*si,pt[2])],'Leaf'+str(f%4))
   prev=pt
palms.done()
lights=Mesh('Boulevard_Lights','Props')
for x in range(-410,0,38):
 lights.cyl((x,39,4.6),(x,39,15.6),.12,.065,'WhiteMetal',10)
 for sgn in [-1,1]:
  lights.cyl((x,39,15),(x,39+sgn*3.7,15.7),.06,.04,'WhiteMetal',8);lights.box((x,39+sgn*3.7,15.72),(.4,1,.15),'WhiteMetal')
lights.done()
# Residential towers ahead: articulated balconies, muted beige piers, recessed glass.
def tower(x,y,w,d,h,style=0):
 m=Mesh('Tower_%d_%d'%(x,y),'Building');z0=1.5
 m.box((x,y,.67),(w+.2,d+.2,1.66),'BuildingBeige')
 m.box((x,y,z0+h/2),(w,d,h),'BuildingBeige' if style==0 else 'BuildingIvory')
 floors=int(h/3.2)
 for floor in range(2,floors):
  z=z0+floor*3.2
  for sy in [-1,1]:
   m.box((x,y+sy*(d/2+.08),z),(w-.7,.12,2.25),'GlassDark' if floor%4 else 'GlassBlue')
   m.box((x,y+sy*(d/2+.55),z-1.1),(w+.4,1.2,.21),'BuildingIvory')
   m.box((x,y+sy*(d/2+1.03),z-.6),(w+.3,.08,.8),'Balcony')
  for sx in [-1,1]:
   m.box((x+sx*(w/2+.04),y,z),(.11,d-.8,2.2),'GlassDark')
   m.box((x+sx*(w/2+.25),y,z-1.1),(.6,d,.2),'BuildingIvory')
   if style==0:
    for yy in [-d*.30,d*.30]:
     m.box((x+sx*(w/2+.65),y+yy,z-1.07),(1.35,4.0,.23),'BuildingBeige')
     m.box((x+sx*(w/2+1.2),y+yy,z-.59),(.08,4.0,.82),'Balcony')
    for yy in [-d*.46,-d*.12,d*.12,d*.46]:m.box((x+sx*(w/2+.18),y+yy,z),(.4,.9,3.2),'BuildingBeige')
 for xx in [-w*.42,-w*.2,0,w*.2,w*.42]:
  for sy in [-1,1]:m.box((x+xx,y+sy*(d/2+.25),z0+h/2),(.55,.6,h),'BuildingBeige')
 for yy in [-d*.38,0,d*.38]:
  for sx in [-1,1]:m.box((x+sx*(w/2+.14),y+yy,z0+h/2),(.4,.65,h),'BuildingBeige')
 m.box((x,y,z0+h+.5),(w+1,d+1,1),'BuildingIvory');m.box((x,y,z0+h+2),(w*.6,d*.65,2),'BuildingBeige');m.done()
for vals in [(128,10,20,20,91),(150,-19,21,18,108),(116,45,20,18,96),(158,49,19,20,111),(174,11,22,18,104)]:tower(*vals)
pod=Mesh('Residential_Podium','Building');pod.box((127,17,5.5),(26,65,11),'BuildingIvory')
for z in [3,6,9]:
 pod.box((113.91,17,z),(.13,62,2.2),'GlassBlue');pod.box((113.5,17,z-1.2),(1.1,65,.3),'BuildingIvory')
for y in range(-14,49,5):pod.box((113.4,y,6),(.7,.5,11),'BuildingIvory')
pod.done()
modern=Mesh('Left_ModernCampus','Building');modern.box((-11,39,12),(85,22,14),'BuildingIvory');modern.box((-11,27.9,12),(82,.13,11.5),'GlassBlue')
modern.box((-11,39,4.7),(85,22,.6),'BuildingIvory')
for x in range(-52,32,3):modern.box((x,27.5,12),(.2,.6,12),'WhiteMetal')
for z in [8,11.3,14.6,18]:modern.box((-11,27.45,z),(85,.65,.22),'WhiteMetal')
modern.box((-11,27.0,19.15),(89,4,.25),'WhiteMetal')
for x in range(-49,30,8):modern.cyl((x,28,18),(x,25,20),.065,.065,'Galvanized')
modern.done()
# Rear skyline visible above entrance tree line, low detail because video pixels cannot resolve facade.
for vals in [(-174,74,22,20,88),(-252,80,25,22,107),(-355,78,22,25,76),(-95,-43,19,19,82)]:tower(*vals,style=1)
terrain=Mesh('Terrain_Perimeter','Terrain');terrain.box((10,-5,-.65),(380,165,1),'Earth');terrain.box((-240,68,4.35),(410,38,.3),'Grass');terrain.box((-230,40,2.1),(410,50,4.5),'Earth');terrain.box((-11,39,2.2),(85,22,4.4),'Earth');terrain.done()
# Rear / forward closure context with site fence behind far curve; no invented traversable continuation.
end=Mesh('SiteBackground','Fence');end.box((121,-8,1.7),(.13,32,3.4),'GreenHoarding');end.done()
# Four-view inspection cameras; matching qualitative video landmarks, uncalibrated intrinsics.
def camera(name,loc,target,lens=25):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);link(o,'Cameras');o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=2000;return o
cam_front=camera('VIEW_01_Forward',sp(109,-1.45,1.65),sp(143,-1.0,2.3),22)
cam_rear=camera('VIEW_02_Rear',sp(112,-1.4,1.65),sp(80,-.5,2.8),23)
cam_right=camera('VIEW_03_Gate',(-9,1,2.0),(1,-10,1.8),21)
cam_left=camera('VIEW_04_LeftWall',sp(130,-1.3,1.7),sp(134,4.2,2.8),22)
cam_hero=camera('VIEW_00_Aerial',(-38,-49,37),(32,1,1),34)
cam_site=camera('VIEW_05_Context',(-100,-120,115),(0,12,0),33)
ld=bpy.data.lights.new('Sun','SUN');lo=bpy.data.objects.new('Sun',ld);link(lo,'Lighting');lo.rotation_euler=Vector((70,45,-100)).to_track_quat('-Z','Y').to_euler();ld.energy=2.5;ld.angle=.15
world=bpy.data.worlds.new('Daylight_Haze');world.use_nodes=True;scene.world=world;ns=world.node_tree.nodes;lk=world.node_tree.links;bg=ns.get('Background');bg.inputs['Strength'].default_value=.5
sky=ns.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_disc=False;sky.sun_elevation=.9;sky.sun_rotation=2.3;sky.altitude=.05;sky.air_density=1.25;sky.dust_density=1.8;lk.new(sky.outputs['Color'],bg.inputs['Color'])
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for dev in prefs.devices:dev.use=dev.type=='OPTIX'
 scene.cycles.device='GPU'
except:pass
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.2
scene.render.image_settings.file_format='PNG';scene.camera=cam_front
scene.render.film_transparent=False
# Export contains only real mesh objects; prototype sources are not exported.
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH' and not o.hide_render:o.select_set(True)
# Preserve source geometry in metric X forward / Z up; FBX stores unit metadata for UE conversion.
exported=[o for o in scene.objects if o.select_get()]
stats={'objects':len(exported),'mesh_vertices_instances':sum(len(o.data.vertices) for o in exported),'polygons_instances':sum(len(o.data.polygons) for o in exported),'materials':len(bpy.data.materials),'coordinate_system':'metric right-handed X along gate road; +Y left; +Z up','excluded':'vehicles, people, cameras, lighting, hidden prototypes','coverage':'210m detailed access road and visual boulevard / skyline context'}
for o in exported:
 o['source']='four-view visual reconstruction';o['metric_accuracy']='estimated, not surveyed'
print('Exporting FBX...',stats,flush=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/(NAME+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',global_scale=1.0,axis_forward='Y',axis_up='Z',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False)
# Remove runtime-only prototype source objects from the saved project; linked tree meshes remain.
for o in tree_protos:bpy.data.objects.remove(o,do_unlink=True)
for img in bpy.data.images:
 if img.source=='FILE':img.filepath='//textures/'+Path(img.filepath).name
scene.camera=cam_front
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(NAME+'.blend')))
(ROOT/'validation'/'mesh_statistics.json').write_text(json.dumps(stats,indent=2))
for name,cam in [('01_forward',cam_front),('02_rear',cam_rear),('03_gate',cam_right),('04_left',cam_left),('00_aerial',cam_hero),('05_context',cam_site)]:
 scene.camera=cam;scene.render.filepath=str(ROOT/'renders'/(name+'.png'));print('RENDER',name,flush=True);bpy.ops.render.render(write_still=True)
print('FINISHED',flush=True)
