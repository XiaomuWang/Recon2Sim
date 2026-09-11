"""Run with Blender 4.2. Environment only; shared road_layout.py aligns FBX/XODR."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scene_lib import *
material('GlassGreen',(.18,.31,.28),.27,.42)
material('MintTile',(.61,.67,.59),.82)
material('WarmTile',(.63,.48,.35),.87)
material('CreamTile',(.72,.67,.53),.83)
material('RoseTile',(.56,.36,.28),.84)
material('Plinth',(.24,.26,.25),.9)
material('WindowFrame',(.68,.72,.7),.42,.4)
material('LeafTrunkWhite',(.72,.71,.62),.96)
material('SignalUnlit',(.023,.03,.028),.6)
material('SignalLens',(.08,.19,.13),.35)
material('Brick',(.49,.35,.28),.9)
material('Tactile',(.62,.52,.31),.96)
def graphic(name,file):
 m=material(name,(1,1,1),.78);tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'textures'/file));m.node_tree.links.new(tex.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
for i in range(13):graphic('Sign'+str(i),f'sign_{i:02d}.png')
for i in range(4):graphic('Civic'+str(i),f'civic_{i}.png')
def strip(m,x1,x2,y1,y2,z,mat):ribbon(m,x1,x2,y1,y2,z,mat,step=3)
def line(m,p,q,w,mat='PaintWhite',z=.013):
 dx=q[0]-p[0];dy=q[1]-p[1];l=math.hypot(dx,dy)
 if l<.0001:return
 nx=-dy/l*w/2;ny=dx/l*w/2
 m.face([(p[0]+nx,p[1]+ny,z),(p[0]-nx,p[1]-ny,z),(q[0]-nx,q[1]-ny,z),(q[0]+nx,q[1]+ny,z)],mat)
def frontface(m,x,y,z,w,h,mat,side=-1):
 v=[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)]
 if side==1:v.reverse()
 m.face(v,mat,[(0,0),(1,0),(1,1),(0,1)] if side==-1 else [(1,1),(0,1),(0,0),(1,0)])
print('Roads, curbs and street furniture',flush=True)
for a in range(int(XMIN),int(XMAX),25):
 m=Mesh('Asphalt_%d'%a,'Road')
 cuts=sorted(set([a,min(a+25,XMAX)]+[v for v in [JX-JHALF,JX+JHALF] if a<v<min(a+25,XMAX)]))
 for u,v in zip(cuts,cuts[1:]):
  if not in_junction((u+v)/2):strip(m,u,v,-PAVED_HALF,PAVED_HALF,0,'Asphalt')
 m.done()
for sg in [-1,1]:
 m=Mesh('CrossStreet_'+str(sg),'Road');y1,y2=sorted([sg*10,sg*SIDE_END]);m.box((JX,(y1+y2)/2,-.10),(SIDE_W*2+2.5,y2-y1,.20),'Asphalt');m.done()
 # Junction corners: extended apron to accommodate turning lane sweeps.
m=Mesh('Junction_Asphalt_Apron','Road');m.box((JX,0,-.10),(24,20,.20),'Asphalt');m.done()
side=Mesh('Curbs_And_Paving','Sidewalk');joints=Mesh('Sidewalk_Seams','Sidewalk')
for x in range(int(XMIN),int(XMAX)):
 for sg in [-1,1]:
  if in_junction(x+.5):continue
  access=in_access(x+.5);height=.03 if access else .18
  side.box((x+.5,sg*9.15,height/2),(1,.3,height),'Concrete')
  strip(side,x,x+1,sg*9.3,sg*14,height,'Paving') if sg>0 else strip(side,x,x+1,-14,-9.3,height,'Paving')
  if not access:
   side.box((x+.5,sg*10.7,.19),(1,.36,.025),'Tactile')
   for j in range(3):side.box((x+.5,sg*10.7+(j-1)*.105,.208),(1,.024,.015),'Tactile')
  for yy in [9.8,10.3,11.3,11.8,12.3,12.8,13.3,13.8]:
   joints.box((x+.5,sg*yy,height+.002),(1,.008,.004),'Joint')
  joints.box((x,sg*11.65,height+.002),(.008,4.7,.004),'Joint')
for sg in [-1,1]:
 for sx in [-1,1]:
  y1,y2=sorted([sg*10,sg*65]);side.box((JX+sx*4.65,(y1+y2)/2,.09),(.3,y2-y1,.18),'Concrete');side.box((JX+sx*6.3,(y1+y2)/2,.08),(3,y2-y1,.16),'Paving')
for sx in [-1,1]:
 for sg in [-1,1]:side.box((JX+sx*9.9,sg*12,.08),(4.2,4,.16),'Paving')
side.done();joints.done()
marks=Mesh('Lane_Markings','RoadLines')
for x in range(int(XMIN),int(XMAX),9):
 if abs(x-JX)<20:continue
 for y in [-LANE,LANE]:strip(marks,x,x+3.5,y-.06,y+.06,.013,'PaintWhite')
for a,b in [(XMIN,JX-15),(JX+15,XMAX)]:
 for y in [-.26,.26]:strip(marks,a,b,y-.05,y+.05,.014,'PaintYellow')
 for y in [-6.6,6.6]:strip(marks,a,b,y-.06,y+.06,.013,'PaintWhite')
for x in range(int(XMIN),int(XMAX),6):
 if in_access(x):continue
 # Worn yellow road-side restriction marks, visible near the right corridor.
 strip(marks,x,x+2,-6.78,-6.68,.016,'PaintYellow')
for xc in [JX-16,JX+16,-340,-230]:
 for y in [i*.95-8.6 for i in range(19)]:strip(marks,xc-2,xc+2,y,y+.45,.018,'PaintWhite')
for sg in [-1,1]:
 y=sg*13.5
 for x in [JX-3.9+i*.85 for i in range(10)]:strip(marks,x,x+.42,y-2,y+2,.019,'PaintWhite')
 strip(marks,JX-21,JX-20.65,-6.5,0,.018,'PaintWhite');strip(marks,JX+20.65,JX+21,0,6.5,.018,'PaintWhite')
for xc in [-365,-260,-167,-80,40]:
 for sg in [-1,1]:
  for ln in [1,2]:
   y=sg*(ln-.5)*LANE;direction=-sg
   line(marks,(xc-direction*1.8,y),(xc+direction*1,y),.19)
   marks.face([(xc+direction*2.5,y,.018),(xc+direction*.65,y-.65,.018),(xc+direction*.65,y+.65,.018)],'PaintWhite')
# Yellow keep-clear boxes in observed minor shop accesses.
for xc,w in ACCESSES:
 for sg in [-1,1]:
  yl,yh=sorted([sg*.45,sg*8.75]);xl,xh=xc-w,xc+w
  for yy in [yl,yh]:line(marks,(xl,yy),(xh,yy),.10,'PaintYellow')
  for xx in [xl,xh]:line(marks,(xx,yl),(xx,yh),.10,'PaintYellow')
  for slope in [-1,1]:
   for k in range(-8,9):
    off=k*2.2;pts=[]
    for xx in [xl,xh]:
     yy=slope*(xx-xc)+off+(yl+yh)/2
     if yl<=yy<=yh:pts.append((xx,yy))
    for yy in [yl,yh]:
     xx=(yy-off-(yl+yh)/2)/slope+xc
     if xl<=xx<=xh:pts.append((xx,yy))
    if len(pts)==2:line(marks,*pts,.075,'PaintYellow')
marks.done()
wear=Mesh('Road_Repairs_And_Drains','Props')
for x in range(-392,99,19):
 for sg in [-1,1]:
  if in_access(x):continue
  wear.box((x,sg*8.7,.01),(.65,.40,.016),'DarkSteel')
  for j in range(9):wear.box((x-.27+j*.066,sg*8.7,.026),(.025,.37,.025),'Galvanized')
for x,y in [(-4,-2.1),(-51,-5.2),(-199,2.4),(-285,-3.9),(-153,4)]:
 wear.cyl((x,y,.003),(x,y,.012),.36,.36,'DarkSteel',32)
 for j in range(-4,5):line(wear,(x-.21,y+j*.05),(x+.21,y+j*.05),.009,'Galvanized',.016)
wear.done()
patch=Mesh('Asphalt_Weathering','RoadLines')
for i in range(80):
 x=random.uniform(XMIN+1,XMAX-1);y=random.uniform(-8.8,8.8);r=random.uniform(.15,.7)
 patch.face([(x+math.cos(a*math.tau/9)*r,y+math.sin(a*math.tau/9)*r*.38,.004) for a in range(9)],'Patch')
patch.done()
# White arched median fence with yellow weighted feet. Geometry has actual open arches.
for a in range(int(XMIN),int(XMAX),40):
 f=Mesh('Median_Arches_%d'%a,'Fence')
 for i in range(a,min(a+40,int(XMAX))):
  if in_access(i+.5):continue
  for x in [i+.25,i+.75]:
   r=.20;top=1.02
   f.cyl((x-r,0,.13),(x-r,0,top),.018,.018,'WhiteMetal',6);f.cyl((x+r,0,.13),(x+r,0,top),.018,.018,'WhiteMetal',6)
   for j in range(10):
    u=j*math.pi/10;v=(j+1)*math.pi/10
    f.cyl((x+r*math.cos(u),0,top+r*math.sin(u)),(x+r*math.cos(v),0,top+r*math.sin(v)),.019,.019,'WhiteMetal',6)
  for z in [.18,.60]:f.cyl((i,0,z),(i+1,0,z),.016,.016,'WhiteMetal',6)
  if i%3==0:
   f.box((i,0,.047),(.42,.48,.094),'CurbYellow');f.box((i,0,.67),(.055,.055,1.2),'WhiteMetal')
 f.done()
# Near-side civic safety panels at the incident; independent panels with metal framing.
for sg in [-1,1]:
 for a in range(-400,100,30):
  f=Mesh('CivicPanels_%d_%d'%(sg,a),'Fence')
  for x in range(a,min(a+30,100),3):
   if in_access(x+1.5):continue
   y=sg*6.95;h=1.12
   f.box((x+1.5,y,.74),(2.92,.045,h),'WhiteMetal')
   frontface(f,x+1.5,y-sg*.027,.74,2.88,h-.04,'Civic'+str((x//3)%4),-sg)
   frontface(f,x+1.5,y+sg*.027,.74,2.88,h-.04,'Civic'+str((x//3)%4),sg)
   for xx in [x,x+3]:
    f.box((xx,y,.70),(.055,.075,1.32),'Galvanized');f.box((xx,y,.07),(.30,.36,.10),'Concrete')
   for z in [.17,1.31]:f.box((x+1.5,y,z),(3,.075,.04),'Galvanized')
  f.done()
props=Mesh('Bollards_Lamps_Signs','Props')
for xc,w in ACCESSES+[(JX,12)]:
 for sg in [-1,1]:
  for dx in [-w-.7,w+.7]:
   props.cyl((xc+dx,sg*9.8,.18),(xc+dx,sg*9.8,.82),.14,.11,'Concrete',12)
for sx in [-1,1]:
 for sg in [-1,1]:
  for dy in range(11,25,2):props.cyl((JX+sx*7.7,sg*dy,.16),(JX+sx*7.7,sg*dy,.79),.13,.11,'Concrete',12)
for x in range(-385,99,34):
 if in_access(x):continue
 for sg in [-1,1]:
  y=sg*9.9;props.cyl((x,y,.15),(x,y,8.2),.09,.052,'Galvanized',10);props.cyl((x,y,7.9),(x+1,sg*7.6,8.55),.05,.037,'Galvanized',8);props.box((x+1,sg*7.3,8.52),(.4,.9,.15),'WhiteMetal')
for x in [-360,-248,-167,-54,49]:
 for sg in [-1,1]:
  y=sg*8.85;props.cyl((x,y,.10),(x,y,3.3),.045,.037,'Galvanized',8);props.box((x,y,3.0),(.07,.65,.72),'SignBlue')
  # Physical generic parking / direction pictogram: no invented street names.
  props.box((x-sg*.041,y,3.05),(.015,.08,.43),'PaintWhite');props.box((x-sg*.041,y+.10,3.23),(.015,.25,.07),'PaintWhite');props.box((x-sg*.041,y+.20,3.10),(.015,.07,.24),'PaintWhite');props.box((x-sg*.041,y+.10,3.0),(.015,.25,.07),'PaintWhite')
props.done()
signal=Mesh('Signal_Furniture_Unconfigured','Props')
for xx,sg in [(JX+17,-1),(JX-17,1)]:
 y=sg*9.5;signal.cyl((xx,y,.15),(xx,y,6.5),.11,.075,'Galvanized',12);signal.cyl((xx,y,6.3),(xx,sg*.9,6.3),.085,.075,'Galvanized',10)
 for yy in [sg*1.9,sg*5.1]:
  signal.box((xx,yy,6.0),(.28,1.18,.41),'DarkSteel')
  for k in [-1,0,1]:signal.cyl((xx+sg*.17,yy+k*.34,6.0),(xx+sg*.20,yy+k*.34,6.0),.115,.115,'SignalLens' if k==1 else 'SignalUnlit',16)
 signal.box((xx,sg*9.4,.22),(.9,.9,.44),'Concrete')
signal.done()
print('Shopfronts and residential facades',flush=True)
def building(x,sg,w,d,h,style=0,yfront=14.5):
 y=sg*(yfront+d/2);face=sg*yfront;m=Mesh('Block_%d_%d'%(x,sg),'Building');col=['MintTile','CreamTile','WarmTile','RoseTile','BuildingIvory'][style%5]
 m.box((x,y,h/2+.18),(w,d,h),col);m.box((x,y,.4),(w+.05,d+.05,.5),'Plinth')
 # Ground floor arcade, doors and separate colorful fascia boards.
 shops=max(1,int(w/5.2));sw=w/shops
 for j in range(shops):
  xx=x-w/2+sw*(j+.5);m.box((xx,face-sg*.045,1.95),(sw-.35,.12,3.1),'GlassDark')
  for k in [-1,0,1]:m.box((xx+k*(sw-.5)/2,face-sg*.16,1.88),(.065,.18,3.05),'WindowFrame')
  m.box((xx,face-sg*.22,.28),(sw-.2,.9,.15),'Concrete')
  m.box((xx,face-sg*.22,3.82),(sw-.13,.3,1.12),'WhiteMetal')
  frontface(m,xx,face-sg*.383,3.82,sw-.2,1.05,'Sign'+str(12 if sg==-1 and x==20 and j==0 else (j+int(abs(x)/8)+style)%12),-sg)
  m.box((xx,face-sg*.8,4.46),(sw-.12,1.7,.11),'Concrete')
  if j%2==0:
   m.box((xx,face-sg*.18,2.9),(sw-.6,.06,.55),'Balcony')
   for k in range(8):m.box((xx-(sw-.6)/2+(sw-.6)*k/8,face-sg*.225,2.9),(.015,.035,.53),'Galvanized')
 for xx in [x-w/2+.13,x+w/2-.13]:m.box((xx,face-sg*.25,2.15),(.26,.65,4.0),col)
 # Windows with recessed glass, sills, rain hoods, grille cages and AC compressors.
 floors=max(1,int((h-4.8)/3.0));cols=max(2,int(w/3.2));cw=(w-.9)/cols
 for f in range(floors):
  z=6.05+f*3.0
  if z+1.3>h:continue
  m.box((x,face-sg*.07,z-1.15),(w,.18,.13),'Concrete')
  for j in range(cols):
   xx=x-(w-.9)/2+(j+.5)*cw;ww=min(1.65,cw-.45)
   m.box((xx,face-sg*.055,z),(ww+.16,.12,1.89),'WindowFrame');m.box((xx,face-sg*.122,z),(ww,.025,1.72),('GlassGreen' if style==0 else 'GlassBlue') if (f+j)%5 else 'GlassDark')
   m.box((xx,face-sg*.15,z),(.047,.065,1.72),'WindowFrame');m.box((xx,face-sg*.15,z+.07),(ww,.065,.045),'WindowFrame')
   m.box((xx,face-sg*.27,z-.96),(ww+.28,.56,.12),'Concrete');m.box((xx,face-sg*.20,z+1.0),(ww+.32,.42,.1),'Concrete')
   if (j+f)%3!=0:
    m.box((xx+ww*.4,face-sg*.49,z-1.24),(.68,.45,.43),'WhiteMetal')
    for k in range(6):m.box((xx+ww*.4-.27+k*.1,face-sg*.725,z-1.24),(.025,.018,.32),'Galvanized')
   if (j+f+style)%4==0:
    for k in range(6):m.box((xx-ww/2+k*ww/5,face-sg*.39,z),(.025,.03,1.78),'Galvanized')
    for dz in [-.8,.8]:m.box((xx,face-sg*.39,z+dz),(ww,.03,.03),'Galvanized')
 # Side walls carry actual window geometry, useful to the rear and cross-street cameras.
 for sx in [-1,1]:
  xf=x+sx*w/2
  for f in range(floors):
   z=6+f*3
   if z+1>h:continue
   for k in range(max(2,int(d/3.3))):
    yy=y-d/2+1.8+k*3.1
    if yy>y+d/2-1:continue
    m.box((xf+sx*.05,yy,z),(.12,1.4,1.8),'WindowFrame');m.box((xf+sx*.116,yy,z),(.022,1.25,1.62),'GlassDark');m.box((xf+sx*.25,yy,z-.96),(.5,1.6,.11),'Concrete')
 m.box((x,y,h+.15),(w+.35,d+.35,.3),'Concrete');m.box((x,y,h+.45),(w,.16,.65),col)
 for sx in [-1,1]:m.box((x+sx*(w/2-.15),y,h+.45),(.24,d,.65),col)
 for ss in [-1,1]:m.box((x,y+ss*(d/2-.15),h+.45),(w,.24,.65),col)
 m.box((x-w*.23,y,h+1.15),(w*.27,d*.38,1.9),'Concrete')
 for j in range(2):m.cyl((x+w*.21+j*1.8,y,h+.3),(x+w*.21+j*1.8,y,h+1.9),.65,.65,'WhiteMetal',16)
 # External drain pipe down facade edge.
 m.cyl((x+w/2-.32,face-sg*.18,4.6),(x+w/2-.32,face-sg*.18,h),.045,.045,'WhiteMetal',6)
 return m.done()
# Distinctive blocks around the incident, matching four-view massing and pale-green frontage.
for vals in [(-53,-1,22,18,25,4),(-15,-1,32,18,25,0),(20,-1,34,19,25,0),(57,-1,32,17,23,1),(88,-1,26,18,22,4),(-85,1,24,18,27,0),(-55,1,28,18,23,1),(-17,1,28,17,26,2),(15,1,32,18,25,1),(50,1,29,18,26,3),(84,1,32,18,22,1),(-151,1,28,20,29,2),(-150,-1,26,20,29,0)]:building(*vals)
for sg in [-1,1]:
 for idx,(x,w) in enumerate([(-383,31),(-354,22),(-316,34),(-279,34),(-248,20),(-210,28),(-179,28)]):building(x,sg,w,random.uniform(16,22),random.choice([20,23,26,29]),(idx+(1 if sg>0 else 0))%5)
# Dark glazed commercial corner seen right at the signalized intersection.
m=Mesh('Corner_Glass_Commercial_Podium','Building');x=-91;y=-24.6;w=29;d=19;h=15.5
m.box((x,y,h/2),(w,d,h),'BuildingBeige')
for z in [2.2,6.0,9.3,12.6]:
 m.box((x,-14.92,z),(w-.4,.12,2.8),'GlassBlue');m.box((-105.57,y,z),(.12,d-.4,2.8),'GlassBlue')
 for xx in range(-105,-77,3):m.box((xx,-14.80,z),(.11,.16,2.8),'Galvanized')
 for yy in range(-33,-15,3):m.box((-105.7,yy,z),(.16,.11,2.8),'Galvanized')
 m.box((x,-14.66,z-1.51),(w+.3,.50,.23),'Concrete');m.box((-105.8,y,z-1.51),(.5,d,.23),'Concrete')
m.box((x,-14.5,4.05),(w+.4,.6,.7),'WhiteMetal');frontface(m,x,-14.18,4.05,w-.2,.6,'Sign11',1)
m.box((x,y,15.65),(w+.8,d+.8,.3),'Concrete');m.done()
# Tall apartment mass set back above the glazed podium.
building(-92,-1,22,19,73,1,yfront=32)
building(-154,1,24,23,62,1,yfront=40)
building(-185,-1,22,20,58,2,yfront=43)
# Cross-street background blocks remain visible through the junction.
for x in [-141,-99]:
 for sg in [-1,1]:building(x,sg,15,18,random.choice([23,26,29]),2,yfront=48)
terrain=Mesh('Urban_Ground','Terrain');terrain.box((-150,0,-.38),(530,180,.6),'Earth');terrain.done()
print('Building tree canopy and palms',flush=True)
tree_protos=[]
for variant in range(5):
 m=Mesh('Tree_Prototype_%d'%variant,'Vegetation');height=random.uniform(8.5,10.3)
 m.cyl((0,0,0),(.1,-.08,height*.67),.28,.095,'Bark',12);m.cyl((0,0,0),(.017,-.014,1.35),.284,.251,'LeafTrunkWhite',12)
 clusters=[]
 for b in range(17):
  ang=b*2.4;z=height*random.uniform(.50,.85);r=random.uniform(1.3,2.7);end=(math.cos(ang)*r,math.sin(ang)*r,z+random.uniform(.6,1.6))
  m.cyl((.08,0,z*.63),end,.085,.018,'Bark',7);clusters.append(end)
 for c in clusters:
  for j in range(540):
   theta=random.random()*math.tau;zz=random.uniform(-1,1);rr=random.random()**(1/3);rd=math.sqrt(1-zz*zz)
   pos=(c[0]+1.75*rr*rd*math.cos(theta),c[1]+1.75*rr*rd*math.sin(theta),c[2]+1.4*rr*zz)
   m.leaf(pos,random.uniform(.12,.23),'Leaf'+str(random.randrange(6)))
 o=m.done();o.hide_render=True;o.hide_viewport=True;tree_protos.append(o)
def tree(x,y,z=.18,scale=1):
 p=random.choice(tree_protos);o=bpy.data.objects.new(NAME+'_Vegetation_StreetTree',p.data);link(o,'Vegetation');o.location=(x,y,z);o.scale=(scale,scale,scale);o.rotation_euler.z=random.uniform(0,math.tau);return o
wells=Mesh('Tree_Pits_Grates','Sidewalk')
for x in range(-394,100,10):
 if in_access(x):continue
 for sg in [-1,1]:
  yy=sg*9.98;tree(x+random.uniform(-.4,.4),yy,.18,random.uniform(.91,1.13))
  wells.box((x,yy,.191),(1.6,1.4,.025),'Earth')
  for dx in [-.85,.85]:wells.box((x+dx,yy,.22),(.12,1.7,.09),'Concrete')
  for dy in [-.8,.8]:wells.box((x,yy+dy,.22),(1.8,.12,.09),'Concrete')
for sg in [-1,1]:
 for yy in range(26,66,11):
  for sx in [-1,1]:tree(JX+sx*6.5,sg*yy,.18,.85)
wells.done()
palms=Mesh('Corner_Palms','Vegetation')
for x,y,base,h in [(-103,-15.3,.18,10),(-91,-15.3,.18,10.8),(-79,-15.3,.18,10.4),(-100,-23,15.8,6.8),(-88,-23,15.8,7.3),(-79,-23,15.8,6.4)]:
 palms.cyl((x,y,base),(x+.12,y,base+h),.18,.105,'Bark',10)
 for j in range(int(h/.25)):palms.cyl((x,y,base+j*.25),(x,y,base+j*.25+.055),.19-j*.0019,.19-j*.0019,'Bark',8)
 for f in range(14):
  ang=f*math.tau/14;co=math.cos(ang);si=math.sin(ang);prev=(x,y,base+h)
  for j in range(1,19):
   u=j/18;r=u*3.4;z=base+h+1.7*math.sin(u*math.pi)-1.1*u;pt=(x+r*co,y+r*si,z);palms.cyl(prev,pt,.014,.009,'Leaf1',5)
   for side in [-1,1]:
    le=(1-u)*.65+.12;tip=(pt[0]-si*side*le-co*.15,pt[1]+co*side*le-si*.15,z-.28)
    palms.face([pt,(tip[0]-.03*co,tip[1]-.03*si,tip[2]),(tip[0]+.03*co,tip[1]+.03*si,tip[2]),(pt[0]+.09*co,pt[1]+.09*si,pt[2])],'Leaf'+str(f%4))
   prev=pt
palms.done()

# Beyond-video continuation only: keeps the observed vanishing point from ending in empty sky.
context=Mesh('Far_Context_Road_NON_NAVIGABLE','Terrain');context.box((215,0,-.10),(230,18,.2),'Asphalt');context.done()
for sg in [-1,1]:
 for idx,x in enumerate([125,162,202,244,288,324]):
  building(x,sg,32,18,random.choice([20,23,26]),idx%5)
 for x in range(108,331,12):tree(x,sg*10,.18,random.uniform(.85,1.0))
context=Mesh('Far_Context_Pavement_NON_NAVIGABLE','Terrain')
for sg in [-1,1]:context.box((215,sg*11.5,.08),(230,5,.16),'Paving')
context.done()
context=Mesh('Far_Context_Markings_NON_NAVIGABLE','RoadLines')
for x in range(101,329,9):
 for yy in [-3.3,3.3]:strip(context,x,x+3.5,yy-.05,yy+.05,.012,'PaintWhite')
for yy in [-.2,.2]:strip(context,100,330,yy-.05,yy+.05,.012,'PaintYellow')
context.done()

def camera(name,loc,target,lens=25):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);link(o,'Cameras');o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=1600;return o
cams={
 '00_aerial':camera('VIEW_Aerial',(-47,-38,88),(-22,-1,1),36),
 '01_forward':camera('VIEW_Forward_Incident',(0,-4.95,1.68),(58,-4.5,2.0),23),
 '02_rear':camera('VIEW_Rear_Incident',(0,-4.95,1.68),(-93,-2,2.5),23),
 '03_left':camera('VIEW_Left_Incident',(0,-4.95,1.68),(-3,17,5),22),
 '04_right':camera('VIEW_Right_Incident',(0,-4.95,1.68),(-1,-17,3.3),18),
 '05_junction':camera('VIEW_Junction_Approach',(-151,-4.95,1.7),(-102,-3.2,3.2),23),
 '06_junction_aerial':camera('VIEW_Junction_Aerial',(-141,-45,133),(-120,0,0),38),
 '07_full_corridor':camera('VIEW_Full_Corridor',(-325,-305,265),(-155,0,0),39)}
ld=bpy.data.lights.new('Sun','SUN');lo=bpy.data.objects.new('Sun',ld);link(lo,'Lighting');lo.rotation_euler=Vector((25,-45,-100)).to_track_quat('-Z','Y').to_euler();ld.energy=2.8;ld.angle=.055
world=bpy.data.worlds.new('Summer_Daylight');world.use_nodes=True;scene.world=world;ns=world.node_tree.nodes;lk=world.node_tree.links;bg=ns.get('Background');bg.inputs['Strength'].default_value=.42
sky=ns.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_disc=False;sky.sun_elevation=1.0;sky.sun_rotation=2.5;sky.air_density=1.15;sky.dust_density=1.5;lk.new(sky.outputs['Color'],bg.inputs['Color'])
# Camera-only clear summer sky; physical Nishita illumination retained.
path=ns.new('ShaderNodeLightPath');mix=ns.new('ShaderNodeMixShader');skybg=ns.new('ShaderNodeBackground');skybg.inputs['Color'].default_value=(.27,.46,.78,1);skybg.inputs['Strength'].default_value=.75;lk.new(path.outputs['Is Camera Ray'],mix.inputs[0]);lk.new(bg.outputs[0],mix.inputs[1]);lk.new(skybg.outputs[0],mix.inputs[2]);lk.new(mix.outputs[0],ns.get('World Output').inputs['Surface'])
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for dev in prefs.devices:dev.use=dev.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception as e:print('GPU setup',e)
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.25;scene.render.image_settings.file_format='PNG';scene.camera=cams['01_forward']
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH' and not o.hide_render:o.select_set(True)
exported=[o for o in scene.objects if o.select_get()]
stats={'objects':len(exported),'mesh_vertices_instances':sum(len(o.data.vertices) for o in exported),'polygons_instances':sum(len(o.data.polygons) for o in exported),'materials':len(bpy.data.materials),'coordinate_system':'RH metres +X forward, +Y left, +Z up; CARLA y=-Y','excluded':'vehicles, people, light actors, cameras, hidden prototypes','coverage':'500m visually estimated street; 110m cross street; 1 navigable crossroad; minor accesses visual only'}
for o in exported:o['source']='four-view parameterized visual reconstruction';o['metric_accuracy']='estimated, not surveyed'
print('Export FBX',stats,flush=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/(NAME+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False)
for o in tree_protos:bpy.data.objects.remove(o,do_unlink=True)
for img in bpy.data.images:
 if img.source=='FILE':img.filepath='//textures/'+Path(img.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(NAME+'.blend')))
(ROOT/'validation/mesh_statistics.json').write_text(json.dumps(stats,indent=2))
for name,cam in cams.items():
 scene.camera=cam;scene.render.filepath=str(ROOT/'renders'/(name+'.png'));print('RENDER',name,flush=True);bpy.ops.render.render(write_still=True)
print('FINISHED',flush=True)
