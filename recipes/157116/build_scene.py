"""Detailed v2: original 0508656 mesh/PBR/architecture and 019742 fencing methods."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scene_lib import *
from architecture import building
out=ROOT.parent
p=json.loads((ROOT/'road_parameters.json').read_text());END=p['incident_station_m'];L=p['end_station_m'];random.seed(157116)
for n,c in [('MintTile',(.62,.70,.65)),('WarmTile',(.65,.52,.41)),('CreamTile',(.72,.66,.54)),('RoseTile',(.53,.36,.30)),('Plinth',(.23,.26,.25)),('WindowFrame',(.70,.73,.71)),('LeafTrunkWhite',(.73,.73,.65)),('Tactile',(.71,.60,.35)),('HedgeLight',(.29,.43,.065)),('HedgeDark',(.12,.26,.04)),('GlassGreen',(.18,.34,.31))]:material(n,c,.35 if 'Glass' in n else .85)
# Generic fascia colours, without unrelated business names from other cases.
for i,c in enumerate([(.36,.10,.07),(.16,.23,.20),(.28,.30,.29),(.68,.64,.53)]*3):material('Sign'+str(i),c,.8)
def strip(m,a,b,y1,y2,z,mat):
 y1,y2=sorted([y1,y2]);m.face([(a,y1,z),(b,y1,z),(b,y2,z),(a,y2,z)],mat)
def tube(m,p,q,r,mat='Galvanized',n=8):m.cyl(p,q,r,r,mat,n)
def line(m,p,q,w,mat='PaintWhite',z=.018):
 dx=q[0]-p[0];dy=q[1]-p[1];le=math.hypot(dx,dy)
 if le<1e-6:return
 nx=-dy/le*w/2;ny=dx/le*w/2;m.face([(p[0]+nx,p[1]+ny,z),(p[0]-nx,p[1]-ny,z),(q[0]-nx,q[1]-ny,z),(q[0]+nx,q[1]+ny,z)],mat)
print('Textured roads, kerbs and pavement',flush=True)
m=Mesh('Boulevard_Main','Road');strip(m,-8,L+8,-10.65,10.65,0,'Asphalt');m.done()
m=Mesh('Surrounding_Ground','Terrain');m.box((L/2,0,-.38),(L+90,160,.60),'Earth');m.done()
side=Mesh('Kerbs_Paving_Tactile','Sidewalk');seams=Mesh('Pavement_Joints','Props')
for x in range(-7,int(L)+7):
 for sg in [-1,1]:
  access=abs(x-(END-25))<7
  side.box((x+.5,sg*10.77,.08 if access else .11),(1,.24,.16 if access else .22),'Concrete')
  strip(side,x,x+1,sg*10.90,sg*13.2,.18,'Paving' if access else 'Grass');strip(side,x,x+1,sg*13.2,sg*20.2,.18,'Paving')
  if not access:
   side.box((x+.5,sg*14,.195),(1,.38,.03),'Tactile')
   for off in [-.11,0,.11]:side.box((x+.5,sg*14+off,.216),(1,.024,.014),'Tactile')
  seams.box((x,sg*16.7,.184),(.012,7,.006),'Joint')
  for yy in [13.7,14.7,15.7,16.7,17.7,18.7,19.7]:seams.box((x+.5,sg*yy,.184),(1,.009,.006),'Joint')
side.done();seams.done()
m=Mesh('Dashed_Lanes_Double_Yellow_Arrows','RoadLines')
for sg in [-1,1]:
 for x in range(-5,int(L),9):
  for yy in [3.5,7]:strip(m,x,x+3.5,sg*yy-.06,sg*yy+.06,.018,'PaintWhite')
 for yy in [.30,10.43]:strip(m,-7,L+7,sg*yy-.06,sg*yy+.06,.018,'PaintYellow')
 for x in [45,100,END-13,END+42]:
  for lane in [1,2,3]:
   yy=sg*(lane-.5)*3.5;dd=-sg;line(m,(x-dd*1.7,yy),(x+dd*1.1,yy),.18)
   m.face([(x+dd*2.5,yy,.021),(x+dd*.8,yy-.6,.021),(x+dd*.8,yy+.6,.021)],'PaintWhite')
for yy in [-.75,.75]:strip(m,END-21,END-3,yy-.06,yy+.06,.018,'PaintYellow')
m.done()
print('Original arched median and street furniture',flush=True)
for start in range(0,int(L),35):
 m=Mesh('Median_Arched_Rail_%03d'%start,'Fence')
 for x in range(start,min(start+35,int(L))):
  if x<45 or END-22<x<END-3:continue
  for xc in [x+.25,x+.75]:
   rr=.20;top=.96
   for xx in [xc-rr,xc+rr]:tube(m,(xx,0,.13),(xx,0,top),.017,'WhiteMetal',6)
   for k in range(8):
    a=k*math.pi/8;b=(k+1)*math.pi/8;tube(m,(xc+rr*math.cos(a),0,top+rr*math.sin(a)),(xc+rr*math.cos(b),0,top+rr*math.sin(b)),.018,'WhiteMetal',6)
  for z in [.19,.62]:tube(m,(x,0,z),(x+1,0,z),.018,'WhiteMetal',6)
  if x%3==0:m.box((x,0,.05),(.48,.44,.1),'CurbYellow');m.box((x,0,.65),(.055,.055,1.22),'WhiteMetal')
 m.done()
m=Mesh('Drainage_Poles_Streetlights','Props')
for x in [45,END-23,END-2]:
 m.cyl((x,0,.08),(x,0,1.3),.085,.075,'CurbYellow',12);m.cyl((x,0,.85),(x,0,1.05),.088,.08,'WhiteMetal',12)
for x in range(8,int(L),21):
 for sg in [-1,1]:
  m.box((x,sg*10.2,.013),(.60,.36,.026),'DarkSteel')
  for j in range(8):m.box((x-.25+j*.07,sg*10.2,.032),(.022,.34,.02),'Galvanized')
for x in range(15,int(L),32):
 for sg in [-1,1]:
  y=sg*11.6;tube(m,(x,y,.2),(x,y,9.7),.068);tube(m,(x,y,9.1),(x+1.1,y-sg*1.9,10.2),.045)
  m.box((x+1.1,y-sg*2.1,10.2),(.35,.85,.15),'WhiteMetal');m.box((x,sg*13.5,.67),(.52,.44,.95),'DarkSteel')
for x in [END-5,END-23]:
 tube(m,(x,.20,0),(x,.20,4.8),.045);m.box((x,.20,4.55),(.035,.72,.78),'SignBlue')
 for z in [4.37,4.43,4.49,4.55,4.61]:m.box((x-.025,.35,z),(.012,.065,.07),'PaintWhite')
 m.box((x-.025,.19,4.65),(.012,.35,.07),'PaintWhite');m.box((x-.025,.04,4.57),(.012,.065,.17),'PaintWhite')
m.done()
m=Mesh('Subtle_Road_Repairs','RoadLines')
for x,y in [(27,-2),(72,-5),(119,2),(END-8,-7.8),(END+35,4)]:
 m.cyl((x,y,.001),(x,y,.011),.32,.32,'DarkSteel',24)
 for yy in [-.12,0,.12]:line(m,(x-.19,y+yy),(x+.19,y+yy),.012,'Galvanized',.015)
for i in range(50):
 x=random.uniform(0,L);y=random.uniform(-10,10);r=random.uniform(.18,.50);m.face([(x+math.cos(a*math.tau/9)*r,y+math.sin(a*math.tau/9)*r*.4,.004) for a in range(9)],'Patch')
m.done()
print('Original detailed architectural helper',flush=True)
for v in [(25,1,28,21,23,1,36),(69,1,22,20,42,0,42),(END-45,1,19,19,20,3,33),(END+51,1,24,21,24,1,26),(END+83,1,30,20,27,2,27),(END+6,-1,29,22,43,2,28),(END+40,-1,27,24,48,1,29),(END+74,-1,26,23,46,3,29),(END-49,-1,24,24,67,0,56),(END-17,-1,25,25,73,1,60),(END+23,-1,24,24,72,0,62)]:
 x,sg,w,d,h,sty,f=v;building(x,sg,w,d,h,sty,yfront=f)
def steps(a,b,d):return [a+i*d for i in range(max(0,int((b-a)/d)+1))]
def office(label,x,sg,w,d,h,front,mint=False):
 m=Mesh(label,'Building');y=sg*(front+d/2);face=sg*front;base='MintTile' if mint else 'BuildingIvory';glass='GlassGreen' if mint else 'GlassBlue';m.box((x,y,h/2),(w,d,h),base)
 for z in [2+i*3.3 for i in range(int(h/3.3))]:
  m.box((x,face-sg*.06,z),(w-.5,.12,2.65),glass);m.box((x,face-sg*.21,z-1.45),(w+.3,.42,.28),base)
  for xx in steps(x-w/2+.2,x+w/2,1.45):m.box((xx,face-sg*.15,z),(.075,.16,2.68),'WindowFrame')
  for sx in [-1,1]:
   m.box((x+sx*(w/2+.05),y,z),(.12,d-.5,2.65),glass)
   for yy in steps(y-d/2+.3,y+d/2,1.6):m.box((x+sx*(w/2+.14),yy,z),(.17,.075,2.65),'WindowFrame')
 m.box((x,y,h+.15),(w+.5,d+.5,.3),'Concrete');m.box((x,y+sg*2,h+1.2),(w*.55,d*.5,2.2),base);m.box((x,face-sg*2,3.8),(w*.55,4.5,.20),'Galvanized')
 for dx in [-w*.24,w*.24]:tube(m,(x+dx,face-sg*3.5,.2),(x+dx,face-sg*3.5,3.7),.12,'WhiteMetal',12)
 m.done()
office('Right_Office_Frontage',61,-1,53,25,28,29);office('Right_Office_Back_Tower',58,-1,28,27,64,63);office('Right_Office_Second_Wing',111,-1,35,25,34,33)
# Rectilinear stepped masses: fisheye curvature is NOT assumed to be physical facade curvature.
office('Left_Mint_Landmark',END+1,1,30,28,34,25,True);office('Left_Mint_Rear_Wing',END-12,1,21,23,45,54,True);office('Distant_Office_End',END+72,1,28,28,53,64)
print('Original individual-leaf foliage method',flush=True)
protos=[]
for variant in range(3):
 m=Mesh('TREE_PROTO_%d'%variant,'Vegetation');height=7.6+variant*.6;m.cyl((0,0,0),(.13,0,height*.68),.24,.085,'Bark',10);m.cyl((0,0,0),(.02,0,1.15),.245,.215,'LeafTrunkWhite',10)
 for b in range(14):
  ang=b*2.4;rr=random.uniform(1.4,2.3);zz=height*random.uniform(.56,.86);c=(rr*math.cos(ang),rr*math.sin(ang),zz);m.cyl((.1,0,zz*.6),c,.072,.015,'Bark',6)
  for j in range(420):
   az=random.random()*math.tau;z=random.uniform(-1,1);rd=random.random()**(1/3);rad=math.sqrt(1-z*z);pt=(c[0]+1.45*rd*rad*math.cos(az),c[1]+1.45*rd*rad*math.sin(az),c[2]+1.25*rd*z);m.leaf(pt,random.uniform(.14,.24),'Leaf'+str(random.randrange(6)))
 protos.append(m.done())
for x in range(4,int(L),11):
 for sg in [-1,1]:
  if abs(x-(END-25))<7:continue
  p=random.choice(protos);o=bpy.data.objects.new(NAME+'_Vegetation_StreetTree',p.data);link(o,'Vegetation');o.location=(x,sg*12,.18);o.rotation_euler.z=random.random()*math.tau;o.scale=(random.uniform(.8,1.08),)*3
for x in range(5,115,13):
 p=random.choice(protos);o=bpy.data.objects.new(NAME+'_Vegetation_Left_GardenTree',p.data);link(o,'Vegetation');o.location=(x,23,.2);o.scale=(1.05,)*3
m=Mesh('HEDGE_PROTO','Vegetation');m.box((0,0,.45),(3.8,.7,.40),'HedgeDark')
for k in range(2500):
 x=random.uniform(-2,2);y=random.uniform(-.52,.52);z=random.uniform(.28,.77)
 if k%2==0:z=random.uniform(.73,.83)
 m.leaf((x,y,z),random.uniform(.05,.08),'HedgeLight' if random.random()<.65 else 'HedgeDark')
hp=m.done()
for x in range(4,int(L)-2,4):
 for sg in [-1,1]:
  if abs(x-(END-25))<8:continue
  o=bpy.data.objects.new(NAME+'_Vegetation_VergeHedge',hp.data);link(o,'Vegetation');o.location=(x,sg*11.2,.18)
for p in protos+[hp]:bpy.data.objects.remove(p,do_unlink=True)
m=Mesh('Landmark_Palms','Vegetation')
for x in [END-16,END-6,END+4]:
 y=20.7;height=9;m.cyl((x,y,.2),(x+.18,y,height),.16,.105,'Bark',12)
 for a in range(11):
  ang=a*math.tau/11;last=(x+.18,y,height)
  for j in range(1,9):
   rr=j*.38;pt=(x+.18+rr*math.cos(ang),y+rr*math.sin(ang),height+.7*math.sin(j*math.pi/8)-.14*j);tube(m,last,pt,.018,'Leaf1',5)
   for sg in [-1,1]:
    tip=(pt[0]-sg*.5*math.sin(ang)-.15*math.cos(ang),pt[1]+sg*.5*math.cos(ang)-.15*math.sin(ang),pt[2]-.18);m.face([last,pt,tip],'Leaf2')
   last=pt
m.done()
print('Export detailed scene',flush=True)
ld=bpy.data.lights.new('Sun','SUN');lo=bpy.data.objects.new('Sun',ld);link(lo,'Lighting');lo.rotation_euler=Vector((26,32,-90)).to_track_quat('-Z','Y').to_euler();ld.energy=2.3;ld.angle=.12
world=bpy.data.worlds.new('Cloudy_Daylight');world.use_nodes=True;scene.world=world;ns=world.node_tree.nodes;lk=world.node_tree.links;bg=ns.get('Background');bg.inputs['Strength'].default_value=.45
sky=ns.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_disc=False;sky.sun_elevation=.6;sky.sun_rotation=2.4;lk.new(sky.outputs['Color'],bg.inputs['Color'])
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
bpy.ops.object.select_all(action='DESELECT');meshes=[o for o in scene.objects if o.type=='MESH']
for o in meshes:o.select_set(True)
for im in bpy.data.images:
 if im.source=='FILE':im.pack()
stats=dict(mesh_count=len(meshes),polygons_instances=sum(len(o.data.polygons) for o in meshes),material_count=len(M),method='Original 0508656 mesh/PBR/architecture + 019742 arched median; layout adapted to four fisheye videos',camera_model='Four fisheye inputs; metric calibration unavailable',source_static_revision='detailed_v2')
(out/'validation/static_detail_statistics.json').write_text(json.dumps(stats,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(NAME+'.blend')))
bpy.ops.export_scene.fbx(filepath=str(ROOT/(NAME+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False)
print('DETAILED_STATIC_COMPLETE',stats,flush=True)
