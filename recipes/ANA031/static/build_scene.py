"""Evidence-informed static environment. Blender 4.2, metres, no vehicles/people."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scene_lib import *
random.seed(310827)
material('IvoryFacade',(.54,.53,.45),.73,texture='concrete')
material('WarmFacade',(.35,.29,.25),.78)
material('CoolFacade',(.25,.29,.29),.78)
material('WindowFrame',(.48,.53,.52),.38,.5)
material('TrunkWhite',(.65,.67,.58),.85)
material('Tactile',(.60,.46,.20),.64)
material('Puddle',(.075,.087,.09),.10)
material('SignalBlack',(.012,.018,.017),.40)
material('Roof',(.39,.43,.39),.32,.45)
material('Hedge',(.045,.12,.037),.85)
for name,color,strength in [('LampWhite',(.90,.98,.77),7),('WindowWarm',(.64,.47,.24),.65),('WindowCool',(.42,.60,.65),.45),('SignalRed',(1,.015,.008),9),('SignalGreen',(.015,1,.34),7),('PanelLight',(.46,.68,.8),1.7)]:
 m=material(name,color,.35);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=strength
# Wet asphalt is texture based in FBX; roughness export stays independently accessible.
m=M['Asphalt'];p=m.node_tree.nodes.get('Principled BSDF')
for lk in list(m.node_tree.links):
 if lk.to_socket==p.inputs['Roughness']:m.node_tree.links.remove(lk)
p.inputs['Roughness'].default_value=.23;p.inputs['Coat Weight'].default_value=.28;p.inputs['Coat Roughness'].default_value=.15
for n in m.node_tree.nodes:
 if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=.24
for name in ['PaintWhite','PaintYellow']:M[name].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.32
lights=[]
def light(name,loc,power,color=(.88,.95,.77),radius=.3,typ='POINT',size=3):
 d=bpy.data.lights.new(name,typ);o=bpy.data.objects.new(name,d);link(o,'Lighting');o.location=loc;d.energy=power;d.color=color
 if typ=='POINT':d.shadow_soft_size=radius
 else:d.shape='DISK';d.size=size
 lights.append({'name':name,'type':typ,'xyz_rh_m':list(loc),'color_linear':list(color),'blender_watts':power,'unreal_intensity_lumens_estimate':power*65,'source_radius_m':radius,'area_size_m':size})
 return o
def strip(m,x1,x2,y1,y2,z,mat):
 if x2<x1:x1,x2=x2,x1
 if y2<y1:y1,y2=y2,y1
 ribbon(m,x1,x2,y1,y2,z,mat,step=4)
def line(m,p,q,w,mat='PaintWhite',z=.012):
 dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy)
 if length<1e-6:return
 nx=-dy/length*w/2;ny=dx/length*w/2
 m.face([(p[0]+nx,p[1]+ny,z),(p[0]-nx,p[1]-ny,z),(q[0]-nx,q[1]-ny,z),(q[0]+nx,q[1]+ny,z)],mat)
print('Road and sidewalk geometry',flush=True)
for a in range(int(XMIN),int(XMAX),30):
 m=Mesh('WetAsphalt_%d'%a,'Road');strip(m,a,min(a+30,XMAX),-PAVED_HALF,PAVED_HALF,0,'Asphalt');m.done()
m=Mesh('Junction_And_CrossStreet','Road')
# Slightly wider junction apron encloses all turn paths without colliding with corners.
for sg in [-1,1]:
 strip(m,JX-12,JX+12,*sorted([sg*SIDE_JOIN,sg*SIDE_END]),0,'Asphalt')
 strip(m,JX-JHALF,JX+JHALF,*sorted([sg*PAVED_HALF,sg*SIDE_JOIN]),0,'Asphalt')
m.done()
m=Mesh('Paving_Curbs_And_Tactile','Sidewalk')
for x in range(int(XMIN),int(XMAX)):
 if in_junction(x+.5):continue
 for sg in [-1,1]:
  m.box((x+.5,sg*CURB,.09),(1,.3,.18),'Concrete')
  strip(m,x,x+1,sg*15,sg*20.5,.18,'Paving')
  m.box((x+.5,sg*16.25,.192),(1,.35,.025),'Tactile')
  for k in [-1,0,1]:m.box((x+.5,sg*16.25+k*.1,.21),(1,.024,.02),'Tactile')
for sg in [-1,1]:
 for sx in [-1,1]:
  lo,hi=sorted([sg*16,sg*SIDE_END]);m.box((JX+sx*12.15,(lo+hi)/2,.09),(.3,hi-lo,.18),'Concrete');m.box((JX+sx*14.5,(lo+hi)/2,.08),(4.4,hi-lo,.16),'Paving')
  # Corner plaza outside junction envelope, lowered pedestrian access.
  m.box((JX+sx*18,sg*18.4,.07),(7.7,4.8,.14),'Paving')
m.done()
m=Mesh('Markings_StopBars_Crosswalks','RoadLines')
for a,b in [(XMIN,JX-JHALF),(JX+JHALF,XMAX)]:
 for sg in [-1,1]:
  for ln in range(1,4):
   y=sg*ln*LANE
   for x in range(math.ceil(a),math.floor(b),9):strip(m,x,min(x+4,b),y-.07,y+.07,.012,'PaintWhite')
  strip(m,a,b,sg*14-.075,sg*14+.075,.013,'PaintWhite')
  strip(m,a,b,sg*.22-.055,sg*.22+.055,.013,'PaintYellow')
 # Solid approach lane separations.
 for ln in range(1,4):
  if b==JX-JHALF:strip(m,b-38,b,-ln*LANE-.075,-ln*LANE+.075,.014,'PaintWhite')
  else:strip(m,a,a+38,ln*LANE-.075,ln*LANE+.075,.014,'PaintWhite')
for x in [JX-18,JX+18]:
 for y in [i*.95-14 for i in range(30)]:strip(m,x-2,x+2,y,y+.48,.015,'PaintWhite')
strip(m,JX-24,JX-23.55,-14,-.4,.016,'PaintWhite');strip(m,JX+23.55,JX+24,.4,14,.016,'PaintWhite')
for sg in [-1,1]:
 for x in [JX-10.5+i*.95 for i in range(23)]:strip(m,x,x+.48,sg*13.8,sg*17.8,.015,'PaintWhite')
 for ln in [-2,-1,1,2]:
  xx=JX+ln*SIDE_W
  for y in range(23,98,9):line(m,(xx,sg*y),(xx,sg*(y+4)),.13)
for xc in [-130,-70,-15,108,145]:
 for sg in [-1,1]:
  for ln in range(1,5):
   y=sg*(ln-.5)*LANE;di=-sg
   line(m,(xc-di*2,y),(xc+di*.8,y),.22)
   m.face([(xc+di*2.7,y,.015),(xc+di*.6,y-di*.62,.015),(xc+di*.6,y+di*.62,.015)],'PaintWhite')
# Yellow paired transverse markings beside the observed shelter.
for x in [-6,9]:
 for dx in [-.7,0,.7]:
  for yy in [-13.1,-12.2,-11.3]:strip(m,x+dx,x+dx+.27,yy,yy+.64,.018,'PaintYellow')
m.done()
m=Mesh('RainPatches_And_Repairs','RoadLines')
for i in range(170):
 x=random.uniform(XMIN,XMAX);y=random.uniform(-13.8,13.8);rx=random.uniform(.4,2.8);ry=random.uniform(.12,.8)
 m.face([(x+math.cos(j*math.tau/13)*rx*random.uniform(.8,1.1),y+math.sin(j*math.tau/13)*ry,.004) for j in range(13)],'Puddle' if i%4 else 'Patch')
m.done()
m=Mesh('Drains_Manholes','Props')
for x in range(-163,158,16):
 if in_junction(x):continue
 for sg in [-1,1]:
  m.box((x,sg*14.4,.005),(.66,.43,.01),'DarkSteel')
  for j in range(8):m.box((x-.27+j*.078,sg*14.4,.014),(.025,.39,.016),'Galvanized')
for x,y in [(-3,-7.5),(7,-6.8),(-50,-9),(90,5),(-100,3)]:m.cyl((x,y,.003),(x,y,.015),.34,.34,'DarkSteel',24)
m.done()
print('White median railings and pedestrian fences',flush=True)
for sg in [0,-1,1]:
 for start in range(-168,160,40):
  m=Mesh('White_Rail_%d_%d'%(sg,start),'Fence');y=0 if sg==0 else sg*15.05
  for x in range(start,min(start+40,160),2):
   if abs(x-JX)<26:continue
   m.box((x,y,.07),(.38,.44,.14),'CurbYellow' if sg==0 else 'Concrete');m.box((x,y,.65),(.065,.065,1.2),'WhiteMetal')
   for z in [.23,1.12]:m.box((x+1,y,z),(2,.04,.04),'WhiteMetal')
   for k in range(7):
    xx=x+.18+k*.26;m.cyl((xx,y,.25),(xx,y,1.10),.014,.014,'WhiteMetal',6)
  m.done()
# Shelter: three stepped cantilever roofs read in right fisheye, no guessed signage.
m=Mesh('RightSide_Tiered_Shelter','Building')
for j in range(3):
 x=-11+j*7.7;y=-19.3;h=3.7+(1-abs(j-1))*.8
 for xx in [x-2.7,x+2.7]:
  m.box((xx,y,h/2),(.20,.24,h),'WhiteMetal');m.box((xx,y,.14),(.52,.58,.28),'Concrete')
  m.cyl((xx,y,h-1.1),(xx,y+2.3,h-.1),.085,.07,'WhiteMetal',8)
 m.box((x,y+.5,h),(7.5,4.6,.16),'Roof');m.box((x,y+.5,h+.18),(4.8,2.65,.14),'WhiteMetal')
 for xx in [x-3.5,x+3.5]:m.box((xx,y+.5,h+.04),(.13,4.8,.25),'WhiteMetal')
 m.box((x,y-1,1.45),(6.0,.08,2.45),'GlassBlue');m.box((x,y-.2,.5),(4.8,.48,.10),'WhiteMetal')
 for dx in [-1.8,1.8]:m.box((x+dx,y-.2,.25),(.1,.38,.5),'DarkSteel')
 m.box((x,y+.2,h-.13),(4.5,.15,.045),'LampWhite');light('Shelter_%d'%j,(x,y+.3,h-.25),45,(.7,.9,1),typ='AREA',size=4)
m.done()
print('Observed building massing and detailed facades',flush=True)
def building(x,sg,w,d,h,front=23,style=0):
 y=sg*(front+d/2);face=sg*front;col=['IvoryFacade','WarmFacade','CoolFacade'][style%3];m=Mesh('Block_%s_%s'%(x,sg),'Building')
 m.box((x,y,h/2),(w,d,h),col)
 for z in [1.0,3.8,h-.4]:m.box((x,face-sg*.08,z),(w+.15,.2,.20),'Concrete')
 n=max(2,int(w/3.3));nf=int((h-2)/3.2)
 for f in range(nf):
  z=2.8+f*3.2
  for j in range(n):
   xx=x-w/2+(j+.5)*w/n;ww=min(1.55,w/n-.6);mat='GlassDark'
   if random.random()<.10:mat=random.choice(['WindowWarm','WindowCool'])
   m.box((xx,face-sg*.07,z),(ww+.15,.16,1.85),'WindowFrame');m.box((xx,face-sg*.16,z),(ww,.025,1.66),mat)
   m.box((xx,face-sg*.20,z),(.045,.06,1.7),'WindowFrame');m.box((xx,face-sg*.24,z-.97),(ww+.26,.45,.12),'Concrete')
   if f<7 and (j+f)%3==0:
    m.box((xx+ww*.45,face-sg*.39,z-1.25),(.65,.43,.42),'WhiteMetal')
    for k in range(5):m.box((xx+ww*.45-.25+k*.12,face-sg*.61,z-1.25),(.018,.02,.29),'DarkSteel')
 for sx in [-1,1]:
  for f in range(nf):
   for yy in range(int(d/3.5)):
    py=y-d/2+1.9+yy*3.5;z=2.8+f*3.2
    m.box((x+sx*(w/2+.04),py,z),(.10,1.4,1.8),'WindowFrame');m.box((x+sx*(w/2+.10),py,z),(.025,1.25,1.62),'GlassDark')
 m.box((x,y,h+.13),(w+.5,d+.5,.26),'Concrete')
 for sx in [-1,1]:m.box((x+sx*(w/2-.14),y,h+.5),(.2,d,.7),col)
 for sy in [-1,1]:m.box((x,y+sy*(d/2-.14),h+.5),(w,.2,.7),col)
 m.box((x-w*.2,y,h+.85),(w*.26,d*.4,1.6),'Concrete')
 m.cyl((x+w*.24,face-sg*.22,.2),(x+w*.24,face-sg*.22,h),.04,.04,'WhiteMetal',6)
 return m.done()
# Low ivory slab and narrow taller building directly on the left; set-back towers on right.
for args in [(-12,1,28,12,7,23,0),(9,1,12,15,24,26,0),(-66,1,22,17,27,24,2),(-110,1,27,18,34,26,2),(88,1,26,20,23,25,1),(127,1,22,17,28,26,0),(-90,-1,30,18,24,26,2),(-139,-1,25,19,33,27,0),(7,-1,28,20,61,43,2),(100,-1,25,24,72,34,1),(136,-1,24,20,55,38,2)]:building(*args)
for args in [(-50,1,24,20,56,55,2),(-5,1,21,24,65,68,2),(95,1,24,22,47,63,2),(-48,-1,30,24,43,54,2),(-120,1,28,23,45,63,1)]:building(*args)
m=Mesh('Left_LowWall_Gates','Wall')
for a,b in [(-160,-130),(-110,-78),(-47,19),(76,150)]:
 m.box(((a+b)/2,21.8,1.05),(b-a,.35,2.1),'IvoryFacade');m.box(((a+b)/2,21.8,2.14),(b-a+.2,.55,.15),'Concrete')
m.done()
m=Mesh('Rear_Illuminated_Panels','Props')
for x in range(-144,-97,8):
 m.box((x,-21.2,1.5),(5.6,.23,2.2),'DarkSteel');m.box((x,-21.05,1.5),(5.2,.035,1.8),'PanelLight')
 # Neutral information panel layout because video text cannot be read reliably.
 for z in [1.0,1.25,1.5]:m.box((x,-21.02,z),(4,.02,.04),'WhiteMetal')
 m.box((x-1.4,-21.02,1.94),(1.1,.02,.25),'SignBlue')
m.done()
print('Trees and planting',flush=True)
protos=[]
for variant in range(4):
 m=Mesh('TreeProto%d'%variant,'Vegetation');h=7.5+variant*.6
 m.cyl((0,0,0),(.1,0,h*.64),.22,.07,'Bark',10);m.cyl((0,0,0),(.025,0,1.2),.225,.19,'TrunkWhite',10)
 for b in range(13):
  ang=b*2.4;r=random.uniform(.8,2.0);z=random.uniform(h*.57,h*.9);end=(math.cos(ang)*r,math.sin(ang)*r,z)
  m.cyl((.06,0,z*.65),end,.062,.015,'Bark',6)
  for j in range(350):
   th=random.random()*math.tau;zz=random.uniform(-1,1);rr=random.random()**(1/3);rad=math.sqrt(1-zz*zz)
   m.leaf((end[0]+1.45*rr*rad*math.cos(th),end[1]+1.45*rr*rad*math.sin(th),end[2]+1.2*rr*zz),random.uniform(.12,.24),'Leaf'+str(random.randrange(6)))
 o=m.done();o.hide_render=True;o.hide_viewport=True;protos.append(o)
def tree(x,y,scale=1):
 pr=random.choice(protos);o=bpy.data.objects.new(NAME+'_Vegetation_StreetTree',pr.data);link(o,'Vegetation');o.location=(x,y,.18);o.rotation_euler.z=random.random()*math.tau;o.scale=(scale,)*3
m=Mesh('TreePits_Planters','Sidewalk')
for x in range(-163,159,11):
 if abs(x-JX)<25:continue
 for sg in [-1,1]:
  yy=sg*17.9
  if sg==-1 and -17<x<13:continue
  tree(x,yy,random.uniform(.85,1.12));m.box((x,yy,.195),(1.8,1.6,.035),'Earth')
  for dx in [-.94,.94]:m.box((x+dx,yy,.22),(.13,1.85,.09),'Concrete')
for sg in [-1,1]:
 for y in range(26,96,12):
  for sx in [-1,1]:tree(JX+sx*15,sg*y,.9)
m.done()
terrain=Mesh('GroundAndPlantedSetbacks','Terrain');terrain.box((-5,0,-.35),(380,235,.5),'Earth');terrain.done()
print('Decorative lamps, signals, monitoring gantries',flush=True)
def streetlamp(x,y,decorative=False):
 m=Mesh('StreetLamp_%s_%s'%(x,y),'Props');h=10 if decorative else 9
 m.cyl((x,y,.15),(x,y,h),.15,.08,'WhiteMetal',12);m.box((x,y,.25),(.55,.55,.5),'Concrete')
 if decorative:
  for k in range(6):
   a=k*math.tau/6;px=x+math.cos(a)*1.25;py=y+math.sin(a)*1.25;pz=h+.35*math.sin(a*2)
   m.cyl((x,y,h-.7),(px,py,pz),.035,.025,'WhiteMetal',8);m.cyl((px,py,pz),(px,py,pz+.20),.15,.10,'LampWhite',10)
  light('CrownLight_%s_%s'%(x,y),(x,y,h-.2),280,radius=.7)
 else:
  sg=1 if y<0 else -1;m.cyl((x,y,h-.4),(x,y+sg*1.6,h),.048,.035,'WhiteMetal',8);m.box((x,y+sg*1.6,h),(.75,.35,.12),'WhiteMetal');m.box((x,y+sg*1.6,h-.08),(.62,.28,.04),'LampWhite');light('RoadLight_%s_%s'%(x,y),(x,y+sg*1.6,h-.16),170,radius=.35)
 m.done()
for x in [-152,-116,-80,-44,-8,24,73,109,145]:
 for sg in [-1,1]:streetlamp(x,sg*15.8,decorative=x in [-8,24,73])
for y in [-84,-48,47,83]:
 for sx in [-1,1]:streetlamp(JX+sx*12.8,y)
signal_records=[]
def signal(x,y,facing,red=True):
 m=Mesh('Signal_%s_%s'%(x,y),'Props');co=math.cos(facing);si=math.sin(facing)
 m.cyl((x,y,0),(x,y,6.8),.12,.075,'WhiteMetal',10)
 # Heads face along direction towards approaching traffic.
 for j in range(3):
  z=5.5-j*.39;m.box((x,y,z),(.30,.22,.37),'SignalBlack',facing)
  p=(x+co*.17,y+si*.17,z);q=(x+co*.20,y+si*.20,z)
  mat=('SignalRed' if red else 'SignalGreen') if j==(0 if red else 2) else 'SignalBlack'
  m.cyl(p,q,.11,.11,mat,16)
  m.box((x+co*.12,y+si*.12,z+.17),(.47,.42,.045),'SignalBlack',facing)
 light('SignalGlow_%s_%s'%(x,y),(x+co*.4,y+si*.4,5.5 if red else 4.72),12,(1,.015,.005) if red else (.005,1,.25),radius=.12)
 m.done();signal_records.append({'xyz_rh_m':[x,y,0],'facing_yaw_rad':facing,'visual_state':'red' if red else 'green','functional_actor':False})
signal(JX+21,-13.5,math.pi,True);signal(JX-21,13.5,0,True);signal(JX-11,-18,-math.pi/2,False);signal(JX+11,18,math.pi/2,False)
m=Mesh('Forward_Signal_Cantilever','Props');m.cyl((JX+22,-14.4,0),(JX+22,-14.4,6.6),.14,.10,'WhiteMetal',12);m.cyl((JX+22,-14.4,6.6),(JX+22,-1.8,6.6),.09,.065,'WhiteMetal',10)
for yy in [-3.0,-6.5,-10.0]:
 m.box((JX+22,yy,6.15),(.25,1.10,.40),'SignalBlack')
 for j in range(3):m.cyl((JX+21.85,yy+(j-1)*.32,6.15),(JX+21.80,yy+(j-1)*.32,6.15),.12,.12,'SignalRed' if j==0 else 'SignalBlack',16)
 light('ForwardRed_%s'%yy,(JX+21.7,yy-.32,6.15),12,(1,.012,.008),radius=.14)
m.done()
for x,sg in [(JX-26,-1),(JX+26,1)]:
 m=Mesh('MonitoringGantry_%s'%x,'Props');y=sg*15.8;m.cyl((x,y,0),(x,y,7.1),.15,.11,'WhiteMetal',12);m.cyl((x,y,7.1),(x,sg*.8,7.1),.10,.065,'WhiteMetal',10)
 for ln in range(1,5):
  yy=sg*(ln-.5)*LANE;m.box((x,yy,7.25),(.50,.27,.23),'WhiteMetal');m.box((x-.26,yy,7.25),(.025,.13,.12),'GlassDark')
 m.done()
def camera(name,loc,target,lens=25):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);link(o,'Cameras');o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=1000;return o
cams={'00_night_aerial':camera('Night_Aerial',(-26,-24,86),(37,0,0),32),'01_front':camera('Front',(0,-5.25,2.0),(62,-5.25,2.4),20),'02_rear':camera('Rear',(0,-5.25,1.0),(-90,-5.25,2.0),22),'03_left_rectilinear':camera('Left_Rectilinear',(0,-5.25,1.7),(-3,30,5),20),'04_right_rectilinear':camera('Right_Rectilinear',(0,-5.25,1.7),(-1,-25,3),20),'05_shelter_detail':camera('Shelter_Detail',(18,-7,5),(-4,-20,2),31),'06_day_overview':camera('Day_Overview',(-30,-25,112),(36,0,0),32)}
world=bpy.data.worlds.new('RainNight');world.use_nodes=True;scene.world=world;world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.055,.07,.105,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.20
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for dev in prefs.devices:dev.use=dev.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.max_bounces=7
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=1.5
scene.render.image_settings.file_format='PNG';scene.camera=cams['01_front']
scene.use_nodes=True;nt=scene.node_tree;nt.nodes.clear();rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=2;gl.mix=-.92;comp=nt.nodes.new('CompositorNodeComposite');nt.links.new(rl.outputs['Image'],gl.inputs['Image']);nt.links.new(gl.outputs['Image'],comp.inputs['Image'])
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH' and not o.hide_render:o.select_set(True)
exported=[o for o in scene.objects if o.select_get()]
stats={'objects':len(exported),'vertices_with_instances':sum(len(o.data.vertices) for o in exported),'polygons_with_instances':sum(len(o.data.polygons) for o in exported),'materials':len(bpy.data.materials),'source':'Four-view parameterized visual reconstruction; side fisheye interpreted using uncalibrated projection sensitivity views','metric_accuracy':'estimated, not surveyed','vehicles':0,'people':0,'main_extent_m':330,'lights_in_separate_json':len(lights)}
for o in exported:o['reconstruction_accuracy']='visual estimate, not calibrated photogrammetry'
print('Export',stats,flush=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/(NAME+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False)
for o in protos:bpy.data.objects.remove(o,do_unlink=True)
for img in bpy.data.images:
 if img.source=='FILE':img.filepath='//textures/'+Path(img.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(NAME+'.blend')))
(ROOT/'validation/mesh_statistics.json').write_text(json.dumps(stats,indent=2));(ROOT/'lighting.json').write_text(json.dumps({'lights':lights,'traffic_signals':signal_records,'note':'Visual fixed lenses only; configure functional CARLA traffic-light actors/phases separately. Unreal brightness estimates require tuning, not photometry.'},indent=2))
for name,cam in cams.items():
 scene.camera=cam
 if name.startswith('06'):
  world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.55,.65,.8,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.6
  d=bpy.data.lights.new('DaySun','SUN');o=bpy.data.objects.new('DaySun',d);link(o,'Lighting');o.rotation_euler=(.4,-.5,-.3);d.energy=2;d.angle=.15;scene.view_settings.exposure=.2
 scene.render.filepath=str(ROOT/'renders'/(name+'.png'));print('RENDER',name,flush=True);bpy.ops.render.render(write_still=True)
print('FINISHED',flush=True)
