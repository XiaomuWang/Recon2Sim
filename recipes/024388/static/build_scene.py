import sys,math,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from scene_lib import *
from tree_lib import *
from mathutils import Matrix
material('PlasterGrey',(.49,.51,.51),texture='facade',normal=.13)
material('PlasterWarm',(.64,.6,.49),.85)
material('TileIvory',(.69,.71,.69),.58)
material('DarkCladding',(.11,.135,.145),.48,.3)
material('Bronze',(.30,.21,.11),.4,.65)
material('FrameAluminum',(.34,.39,.41),.35,.72)
material('GreenFence',(.045,.19,.12),.72)
material('RedSign',(.55,.035,.025),.48)
material('ShopGreen',(.12,.35,.08),.52)
material('ShopYellow',(.72,.46,.075),.6)
material('WindowWarm',(.4,.27,.11),.4)
material('WindowCool',(.22,.30,.31),.38)
material('CeramicPot',(.34,.17,.09),.78)
material('TactilePaving',(.6,.45,.17),.85)
M['Patch'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.035,.039,.041,1)
emissions={}
def emissive(name,col,strength):
 m=material(name,col,.4);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=strength;emissions[name]={'color':col,'strength':strength}
emissive('NeonBlue',(.03,.12,1),4)
emissive('NeonWhite',(.8,.9,1),2)
emissive('WarmLight',(1,.67,.32),3)
emissive('ShopLight',(.8,1,.83),2)
emissive('NeonRed',(1,.05,.025),2.5)
emissive('WindowLit',(1,.72,.4),.7)
emissive('ShopInterior',(.32,.36,.28),.55)
LIGHTS=[]
def point_light(name,loc,energy=150,col=(1,.79,.54),radius=.3):
 d=bpy.data.lights.new(name,'POINT');d.energy=energy;d.color=col;d.shadow_soft_size=radius;o=bpy.data.objects.new(name,d);link(o,'Lighting');o.location=loc
 LIGHTS.append({'name':name,'type':'POINT','xyz_m':list(loc),'energy_w':energy,'color':col,'radius_m':radius})
 return o
def area_light(name,loc,target,power,size,col):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=col;o=bpy.data.objects.new(name,d);link(o,'Lighting');o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 LIGHTS.append({'name':name,'type':'AREA','xyz_m':list(loc),'target_m':list(target),'energy_w':power,'color':col,'size_m':size});return o
def strip(m,pts,width,mat,z=.014):
 for p,q in zip(pts,pts[1:]):
  dx,dy=q[0]-p[0],q[1]-p[1];L=math.hypot(dx,dy)
  if L<1e-6:continue
  nx,ny=-dy/L*width/2,dx/L*width/2
  m.face([(p[0]+nx,p[1]+ny,z),(p[0]-nx,p[1]-ny,z),(q[0]-nx,q[1]-ny,z),(q[0]+nx,q[1]+ny,z)],mat)
def rect(m,x0,x1,y0,y1,z,mat):m.face([(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)],mat)
def cylball(m,c,r,mat):
 # UV sphere geometry for stone bollards, no shading-dependent modifiers.
 for i in range(9):
  a=-math.pi/2+i*math.pi/9;b=-math.pi/2+(i+1)*math.pi/9
  for j in range(16):
   u=j*math.tau/16;v=(j+1)*math.tau/16
   pts=[(c[0]+r*math.cos(t)*math.cos(p),c[1]+r*math.cos(t)*math.sin(p),c[2]+r*math.sin(t)) for t,p in [(a,u),(a,v),(b,v),(b,u)]]
   if i==0:pts=pts[1:]
   if i==8:pts=pts[:3]
   m.face(pts,mat)
font=bpy.data.fonts.load('C:/Windows/Fonts/msyh.ttc')
def text_mesh(body,center,width,mat,normal=(-1,0,0),name='SignText',max_height=.55):
 c=bpy.data.curves.new(name,'FONT');c.body=body;c.font=font;c.align_x='CENTER';c.align_y='CENTER';c.size=1;c.extrude=.004;c.resolution_u=3
 o=bpy.data.objects.new(NAME+'_Props_'+name,c);link(o,'Props');o.location=center
 # Local Y is vertical; local Z faces the sidewalk.
 n=Vector(normal);up=Vector((0,0,1));right=up.cross(n);rot=Matrix((right,up,n)).transposed();o.rotation_euler=rot.to_euler();bpy.context.view_layer.update();scale=min(width/max(o.dimensions.x,.001),max_height/max(o.dimensions.y,.001));o.scale=(scale,scale,scale)
 c.materials.append(M[mat]);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');return bpy.context.object
print('Building observed T junction and curved curbs',flush=True)
# The driveable mesh boundary is shared by curbs and markings.
low=[(-180,-3.3),(-8.3,-3.3)]+[(-8.3+5*math.cos(a),-8.3+5*math.sin(a)) for a in [math.pi/2-i*math.pi/2/32 for i in range(1,33)]]+[(-3.3,-100)]
up=[(-3.3,85),(-3.3,8.3)]+[(-8.3+5*math.cos(a),8.3+5*math.sin(a)) for a in [-i*math.pi/2/32 for i in range(1,33)]]+[(-180,3.3)]
boundary=low+[(3.3,-100),(3.3,85)]+up
road=Mesh('Street_Surface','Road');road.face([(x,y,0) for x,y in boundary],'Asphalt');road.done()
side=Mesh('Sidewalk_Forecourts','Sidewalk')
# Arc-shaped near corner sidewalks, bounded by the observed road edge.
side.face([(x,y,.16) for x,y in [(-180,-26),(-3.3,-26)]+list(reversed(low[:-1]))],'Paving')
side.face([(x,y,.16) for x,y in [(-180,26),(-180,3.3)]+list(reversed(up[1:-1]))+[(-3.3,26)]],'Paving')
rect(side,-10,-3.3,-100,-26,.16,'Paving');rect(side,-10,-3.3,26,85,.16,'Paving');rect(side,3.3,9,-100,85,.16,'Paving');side.done()
curb=Mesh('Segmented_Granite_Curb','Sidewalk');mark=Mesh('Painted_Lines','RoadLines')
for pts in [low,up,[(3.3,-100),(3.3,85)]]:
 for p,q in zip(pts,pts[1:]):
  length=math.dist(p,q);n=max(1,math.ceil(length/.8))
  for j in range(n):
   a=tuple(p[i]+(q[i]-p[i])*j/n for i in [0,1]);b=tuple(p[i]+(q[i]-p[i])*(j+1)/n for i in [0,1]);h=math.atan2(b[1]-a[1],b[0]-a[0]);curb.box(((a[0]+b[0])/2,(a[1]+b[1])/2,.065),(length/n-.014,.23,.19),'Concrete',h)
curb.done()
for y in [-.12,.12]:strip(mark,[(-180,y),(-15,y)],.10,'PaintYellow')
for y in [-3.03,3.03]:strip(mark,[(-180,y),(-12,y)],.11,'PaintYellow')
for x in [-3.04,3.04]:
 for a,b in [(-100,-13),(13,85)]:strip(mark,[(x,a),(x,b)],.10,'PaintYellow')
# Cross-street centerline is inferred and only continued beyond the main crossing.
for a,b in [(-100,-18),(18,85)]:
 for x in [-.1,.1]:strip(mark,[(x,a),(x,b)],.10,'PaintYellow')
# 3 zebra crossings, approach and both arms, confirmed by side/rear videos.
for y in [-2.85,-1.9,-.95,0,.95,1.9,2.85]:rect(mark,-12.7,-9.3,y-.22,y+.22,.018,'PaintWhite')
for y in [-9.4,9.4]:
 for x in [-2.85,-1.9,-.95,0,.95,1.9,2.85]:rect(mark,x-.22,x+.22,y-1.7,y+1.7,.018,'PaintWhite')
strip(mark,[(-14.2,-3.05),(-14.2,-.3)],.32,'PaintWhite')
def arrow(x,y,h=0,split=False):
 # White approach arrows; lateral branches at terminal T junction.
 shape=[(-2,-.10),(.6,-.10),(.6,-.40),(1.55,0),(.6,.4),(.6,.10),(-2,.10)]
 if split:shape=[(-2,-.1),(.05,-.1),(.05,-.72),(-.3,-.72),(.15,-1.35),(.6,-.72),(.25,-.72),(.25,.72),(.6,.72),(.15,1.35),(-.3,.72),(.05,.72),(.05,.1),(-2,.1)]
 mark.face([(x+a*math.cos(h)-b*math.sin(h),y+a*math.sin(h)+b*math.cos(h),.017) for a,b in shape],'PaintWhite')
arrow(-24,-1.65,0,True);arrow(-62,-1.65);arrow(-103,-1.65);arrow(-48,1.65,math.pi);arrow(-118,1.65,math.pi)
mark.done()
wear=Mesh('Road_Repairs_Drains','RoadLines')
for x,y in [(-17,-.9),(-39,1.5),(-78,-1.4),(-124,.9),(1.1,-17),(1.5,28),(-1,-61)]:
 wear.cyl((x,y,.006),(x,y,.011),.32,.32,'DarkSteel',32)
 for u in [-.2,-.1,0,.1,.2]:strip(wear,[(x-.22,y+u),(x+.22,y+u)],.012,'Galvanized',.016)
for i in range(125):
 if i<80:x=random.uniform(-177,-16);y=random.uniform(-2.7,2.7)
 else:x=random.uniform(-2.7,2.7);y=random.choice([-1,1])*random.uniform(14,90)
 r=random.uniform(.10,.7);pts=[(x+math.cos(j*math.tau/9)*r,y+math.sin(j*math.tau/9)*r*.5,.003) for j in range(9)];wear.face(pts,'Patch')
for i in range(45):
 x=random.uniform(-175,-16);y=random.uniform(-2.7,2.7);pts=[(x,y)]
 for j in range(6):x+=random.uniform(.06,.24);y+=random.uniform(-.1,.1);pts.append((x,y))
 strip(wear,pts,.01,'Joint',.008)
wear.done()
drain=Mesh('Curb_Drain_Gratings','Props')
for x in range(-170,-15,9):
 for y in [-3.08,3.08]:
  drain.box((x,y,.012),(.55,.3,.025),'DarkSteel')
  for j in range(9):drain.box((x-.24+j*.06,y,.027),(.016,.29,.009),'Galvanized')
for y in range(-93,82,12):
 if abs(y)>14:
  drain.box((-3.07,y,.012),(.30,.55,.025),'DarkSteel')
  for j in range(9):drain.box((-3.07,y-.24+j*.06,.027),(.29,.016,.009),'Galvanized')
drain.done()
# Sidewalk tactile routes with raised bars and paving joints at the corners.
walk=Mesh('Corner_Tactile_And_Tile_Joints','Sidewalk')
for x in range(-178,-13):
 for sgn in [-1,1]:
  rect(walk,x,x+.97,sgn*4.25-.15,sgn*4.25+.15,.168,'TactilePaving')
  for k in range(3):walk.box((x+.48,sgn*4.25-.09+k*.09,.176),(.9,.018,.014),'TactilePaving')
for y in range(-99,84):
 if abs(y)>12:
  rect(walk,-5.2,-4.9,y,y+.97,.168,'TactilePaving')
  for k in range(3):walk.box((-5.17+k*.09,y+.48,.176),(.018,.9,.014),'TactilePaving')
for x in range(-32,-9):
 for y in [-6,-7,-8,6,7,8]:strip(walk,[(x,y),(x+.95,y)],.012,'Joint',.17)
walk.done()
print('Building hotel, commercial frontage, opposite housing and construction gate',flush=True)
# Geometry in local facade coordinates: u horizontal, v inward, z vertical.
def facade_point(origin,u,v,z,h):
 return (origin[0]+u*math.cos(h)-v*math.sin(h),origin[1]+u*math.sin(h)+v*math.cos(h),z)
def facade_box(m,origin,u,v,z,du,dv,dz,mat,h):m.box(facade_point(origin,u,v,z,h),(du,dv,dz),mat,h)
def building(name,x,y,w,d,h,style=0):
 m=Mesh(name,'Building');mat=['PlasterGrey','PlasterWarm','TileIvory'][style%3]
 m.box((x,y,h/2+.18),(w,d,h),mat);m.box((x,y,.36),(w+.3,d+.3,.4),'DarkCladding')
 for z in [4.2]+[7.4+i*3.2 for i in range(int((h-7)/3.2))]:
  m.box((x,y,z),(w+.12,d+.12,.16),'TileIvory')
 # Windows on all four elevations; facade module details are inferred.
 for origin,L,rot in [((x,y-d/2),w,0),((x+w/2,y),d,math.pi/2),((x,y+d/2),w,math.pi),((x-w/2,y),d,-math.pi/2)]:
  for z in [5.9+i*3.2 for i in range(max(1,int((h-5)/3.2)))]:
   for j in range(max(1,int(L/3.4))):
    u=-L/2+1.7+j*3.4
    facade_box(m,origin,u,-.025,z,1.65,.12,1.9,'FrameAluminum',rot)
    wm=random.choices(['GlassDark','WindowCool','WindowWarm','WindowLit'],[62,19,14,5])[0]
    facade_box(m,origin,u,-.095,z,1.45,.025,1.7,wm,rot)
    facade_box(m,origin,u,-.12,z,.045,.05,1.72,'WhiteMetal',rot)
    facade_box(m,origin,u,-.12,z-.25,1.5,.05,.045,'WhiteMetal',rot)
    facade_box(m,origin,u,-.16,z-1.01,1.85,.35,.12,'TileIvory',rot)
    if style==1 and j%2==0:
     facade_box(m,origin,u,-.55,z-1,2.6,1.05,.18,'TileIvory',rot)
     facade_box(m,origin,u,-1.04,z-.5,2.6,.08,.85,'DarkSteel',rot)
     for k in range(8):facade_box(m,origin,u-1.15+k*.32,-1.06,z-.46,.028,.025,.85,'WhiteMetal',rot)
    if j%3==0 and int(z)%2==0:
     facade_box(m,origin,u+1.1,-.25,z-.55,.67,.48,.43,'Concrete',rot)
     for k in range(6):facade_box(m,origin,u+1.1,-.5,z-.71+k*.06,.53,.02,.025,'DarkSteel',rot)
  # Coping, downpipes and pilasters separate the elevations.
  for u in [-L/2+.18,L/2-.18]:
   facade_box(m,origin,u,-.04,h/2,.2,.18,h,'TileIvory',rot)
   a=facade_point(origin,u+.25,-.18,.4,rot);b=facade_point(origin,u+.25,-.18,h-.2,rot);m.cyl(a,b,.045,.045,'DarkSteel',8)
 m.box((x,y,h+.25),(w+.5,d+.5,.5),'TileIvory');m.box((x,y,h+.53),(w-.6,d-.6,.06),'DarkCladding')
 for xx in [-w*.25,w*.25]:
  m.box((x+xx,y,h+1.15),(2.5,2,1.2),'Concrete')
  for j in [-.6,.6]:m.cyl((x+xx+j,y,h+1.75),(x+xx+j,y,h+1.79),.42,.42,'DarkSteel',16)
 return m.done()
building('Hotel_Main_Block',-32,-20,43,19,25,0)
building('Hotel_Turn_Street_Wing',-15.8,-46,11,33,22,0)
building('Opposite_Corner_Apartments',-17,23,14,26,30,1)
building('Left_Street_Housing',-18,55,16,29,27,1)
building('Right_Exit_MixedUse',-17,-83,14,25,24,1)
building('Approach_Left_Shops',-59,16,55,18,23,1)
building('Approach_Right_ServiceBlock',-81,-15,42,13,15,0)
building('Early_Right_BlankWall',-136,-13,51,12,20,0)
building('Early_Left_Residential',-130,17,57,18,26,2)
# Infill plain wall and long strip windows on early right side, strongly visible in right 0-25 sec.
early=Mesh('Early_Right_Masonry_Front','Building');early.box((-136,-6.91,2.6),(51,.24,5),'PlasterGrey')
for x in range(-158,-112,4):
 early.box((x,-6.74,3.55),(2.4,.05,1.65),'GlassDark')
 for dx in [-1.2,-.4,.4,1.2]:early.box((x+dx,-6.67,3.55),(.06,.12,1.75),'WhiteMetal')
 early.box((x,-6.68,3.55),(2.45,.1,.055),'WhiteMetal')
early.done()
hotel=Mesh('Hotel_Entrance_Articulation','Building')
# Hotel entrance faces approach, at the near right corner, alongside convenience store.
hotel.box((-15.0,-9.7,2.25),(8.7,.35,4.2),'DarkCladding')
hotel.box((-15.1,-9.46,2.2),(5.3,.10,3.5),'GlassDark')
for x in [-17.55,-16.25,-13.8,-12.55]:hotel.box((x,-9.3,2.2),(.09,.16,3.5),'Bronze')
hotel.box((-15,-8.9,4.4),(10.2,2.0,.32),'DarkCladding')
for j in range(25):hotel.box((-19.9+j*.41,-8.9,4.16),(.075,1.85,.08),'Bronze')
for j in range(8):hotel.box((-19.55+j*.17,-9.25,2.2),(.06,.28,3.65),'Bronze')
for i in range(3):hotel.box((-15,-8.75+i*.28,.20+i*.07),(8.2,1.9-i*.3,.08),'Concrete')
hotel.box((-15,-9.42,5.2),(10,.3,1.15),'DarkCladding')
hotel.done()
text_mesh('美豪丽致酒店',(-15,-9.20,5.37),8.6,'NeonWhite',(0,1,0),'Hotel_Title')
text_mesh('MEHOOD LESTIE',(-15,-9.18,4.92),5.8,'NeonWhite',(0,1,0),'Hotel_English')
text_mesh('欢迎光临',(-15,-9.16,3.87),2.4,'WarmLight',(0,1,0),'Hotel_Welcome')
area_light('Hotel_Entrance_Warm',(-15,-8.4,3.8),(-14,-5,.3),260,4,(1,.69,.40))
point_light('Hotel_Sign_Cool',(-15,-8.4,5),65,(.24,.35,1),1.4)
# Corner convenience shop, transparent-looking glazing with modeled interior shelves.
shop=Mesh('Corner_Convenience_Store','Building');shop.box((-9.75,-17.7,3.9),(.65,13.8,.7),'DarkCladding')
shop.box((-10.06,-17.7,2.05),(.10,13.5,3.1),'ShopInterior')
for y in [-23.9,-21,-18,-15,-12]:shop.box((-9.92,y,2.05),(.15,.09,3.3),'WhiteMetal')
shop.box((-9.86,-17.7,.5),(.17,13.6,.38),'TileIvory')
shop.box((-10.1,-17.7,3.43),(.4,13.8,.20),'ShopLight')
shop.box((-10.5,-17.7,3.15),(1.2,13.4,.08),'TileIvory')
for yy in [-23,-19,-15]:
 for zz in [.55,1.15,1.75,2.35]:
  shop.box((-9.94,yy,zz),(.20,2.2,.06),'WhiteMetal')
  for j in range(8):shop.box((-9.89,yy-.9+j*.26,zz+.18),(.16,.19,.30),['ShopGreen','ShopYellow','RedSign','PaintWhite'][j%4])
shop.box((-9.7,-12.2,3.03),(.25,.8,1.45),'ShopGreen');shop.done()
text_mesh('生活超市',(-9.34,-17.8,3.95),8.4,'NeonWhite',(1,0,0),'Convenience_Title')
text_mesh('便利',(-9.51,-12.2,3.15),.64,'ShopLight',(1,0,0),'Shop_Vertical')
for y in [-22,-18,-14]:area_light('Shop_Front_'+str(y),(-9.1,y,3.0),(-4,y,.4),140,2.5,(.73,1,.81))
# Low shopfront modules on the left and along the approach; generic unreadable signage is labelled in README.
def shopfront(origin,L,h,index):
 m=Mesh('Shopfront_%02d'%index,'Building');colors=['ShopGreen','RedSign','ShopYellow','DarkCladding'];normal=(math.sin(h),-math.cos(h),0)
 facade_box(m,origin,0,-.05,2,L,.18,3.4,'GlassDark',h);facade_box(m,origin,0,-.15,3.78,L+.12,.30,.78,colors[index%4],h)
 for u in [-L/2+.06,0,L/2-.06]:facade_box(m,origin,u,-.20,2,.10,.2,3.3,'WhiteMetal',h)
 facade_box(m,origin,0,-.6,3.22,L+.2,1.5,.08,'ShopYellow' if index%2 else 'DarkCladding',h)
 for z in [.5,.85,1.2,1.55,1.9,2.25,2.6]:
  if index%3==1:facade_box(m,origin,-L*.25,-.24,z,L*.43,.1,.28,'FrameAluminum',h)
 m.done();loc=facade_point(origin,0,-.34,3.8,h);titles=['生活便利','社区商店','家常小吃','美食坊','百货商店','便民服务']
 text_mesh(titles[index%len(titles)],loc,L*.8,'WarmLight' if index%2 else 'NeonWhite',normal,'Store_%02d'%index)
 a=facade_point(origin,0,-.8,3,h);target=facade_point(origin,0,-3,.2,h);area_light('Store_Light_'+str(index),a,target,80,L*.6,(1,.78,.55))
for i,y in enumerate([15,21,27,33,43,49,55,61,67]):shopfront((-9.91,y),5,math.pi/2,i)
for i,x in enumerate([-33,-40,-47,-54,-61,-68,-75,-83]):shopfront((x,6.96),5.7,0,10+i)
for i,x in enumerate([-63,-69,-77,-85,-93]):shopfront((x,-8.4),5,math.pi,20+i)
# Chinese construction company gate at opposite side of T.
gate=Mesh('Construction_Gate_Portico','Building');gate.box((9,0,5.25),(.9,14.6,1.25),'TileIvory')
for y in [-6.65,6.65]:gate.box((9,y,2.75),(.9,1.15,5.4),'TileIvory')
gate.box((9.02,0,5.99),(.96,14.9,.2),'DarkCladding')
gate.box((8.65,0,6.65),(.24,10.3,1.05),'DarkCladding')
gate.box((11.4,3.5,1.55),(3.6,4.7,2.8),'PlasterGrey');gate.box((9.52,3.5,1.82),(.07,3.6,1.45),'GlassBlue')
gate.box((11.4,3.5,3.1),(4,5.1,.24),'TileIvory');gate.done()
text_mesh('中国建筑一局',(8.49,0,6.67),8.8,'NeonBlue',(-1,0,0),'Gate_Corporate_Title',.72)
text_mesh('中国建筑  品质保障',(8.49,0,5.24),11.3,'SignBlue',(-1,0,0),'Gate_Header',.32)
for y in [-6.65,6.65]:
 for i,ch in enumerate('安全施工文明建设'):text_mesh(ch,(8.49,y,4.55-i*.45),.34,'SignBlue',(-1,0,0),'Gate_Pillar')
point_light('Gate_Blue_Glow',(7.7,0,5.9),145,(.07,.16,1),2.3)
fence=Mesh('Gate_Closed_Metal_Barrier','Fence')
for z in [.45,1.3,2.15]:fence.box((8.6,-.8,z),(.08,10.3,.07),'Galvanized')
for j in range(57):
 y=-5.85+j*.18;fence.cyl((8.6,y,.24),(8.6,y,2.23),.021,.021,'Galvanized',6)
for y in [-5.8,-3.6,-1.4,.8,2.8,4.2]:fence.cyl((8.5,y,.15),(8.5,y,2.35),.044,.044,'WhiteMetal',8)
fence.done()
wall=Mesh('Green_Site_Perimeter','Fence')
for a,b in [(-100,-7.3),(7.3,85)]:
 wall.box((9.05,(a+b)/2,1.8),(.15,b-a,3.3),'GreenFence')
 wall.box((9.03,(a+b)/2,.43),(.38,b-a,.53),'PlasterGrey')
 for y in range(math.ceil(a),int(b),3):
  wall.box((8.88,y,1.9),(.16,.12,3.5),'WhiteMetal')
 for z in [1,2.1,3.4]:wall.box((8.91,(a+b)/2,z),(.08,b-a,.06),'Galvanized')
wall.done()
# A gate forecourt and set-back work compound, inferred behind visible closed gate.
site=Mesh('Site_Setback_Ground','Terrain');site.box((28,0,-.08),(38,174,.12),'Earth');site.box((16,0,.06),(13,13,.12),'RoadConcrete');site.done()
building('Setback_Construction_Mass',45,21,21,35,34,0)
# Decorative ground-level street furniture.
props=Mesh('Bollards_Street_Furniture','Props')
for x in [float(i) for i in range(-95,-20,2)]:
 y=-4.25;props.cyl((x,y,.16),(x,y,1.0),.065,.065,'CurbBlack',12)
 for z in [.43,.77]:props.cyl((x,y,z),(x,y,z+.14),.069,.069,'CurbYellow',12)
 props.cyl((x,y,.16),(x,y,.20),.14,.14,'DarkSteel',12)
for y in list(range(-97,-11,4))+list(range(13,81,4)):
 x=-4.3;props.cyl((x,y,.16),(x,y,1.02),.063,.063,'CurbYellow',12);props.cyl((x,y,.7),(x,y,.93),.067,.067,'CurbBlack',12)
for x,y in [(-9,-7),(-11,-7.8),(-17,-7.7),(-5.0,-10.6)]:
 cylball(props,(x,y,.40),.27,'Concrete');props.cyl((x,y,.16),(x,y,.20),.32,.32,'Concrete',24)
for x,y in [(-31,4.8),(-87,4.8),(-126,-4.7),(-5.4,21),(-5.4,-29)]:
 props.box((x,y,.6),(.65,.55,.85),'DarkSteel');props.box((x,y,1.05),(.69,.58,.10),'Galvanized');props.box((x+.33,y,.81),(.02,.38,.14),'Joint')
props.done()
pots=Mesh('Hotel_Corner_Planters','Props');leaves=Mesh('Corner_Planter_Foliage','Vegetation')
for x,y in [(-13,-6.1),(-17,-6.1),(-21,-6.1),(-9.2,-7.3)]:
 pots.box((x,y,.59),(.9,.9,.86),'CeramicPot');pots.box((x,y,1.02),(1,.99,.08),'PlasterWarm');pots.box((x,y,1.06),(.82,.82,.04),'Earth')
 for j in range(650):
  a=random.uniform(0,math.tau);z=random.uniform(-.65,.65);r=random.random()**(1/3);q=math.sqrt(1-z*z)
  leaves.leaf((x+r*q*math.cos(a)*.67,y+r*q*math.sin(a)*.67,1.66+r*z),random.uniform(.07,.14),'Leaf'+str(random.randrange(6)))
pots.done();leaves.done()
# Trees are located by the four-view curb relationships, with multi-stem banyan at the gate.
print('Building trees and street lighting',flush=True)
for x in range(-171,-19,14):
 tree(x,4.85,.17,random.uniform(.90,1.18));tree(x,-5.6,.17,random.uniform(.8,1.08))
for y in list(range(-95,-13,14))+list(range(17,85,14)):
 tree(6.3,y,.17,random.uniform(1.0,1.28));tree(-5.95,y,.17,random.uniform(.78,1.02))
tree(6.2,-9.5,.17,1.58,2);tree(6.5,11,.17,1.45,4)
roots=Mesh('Banyan_Trunk_Buttress_Roots','Vegetation')
for x,y in [(6.2,-9.5),(6.5,11)]:
 for j in range(12):
  a=j*math.tau/12;r=random.uniform(.18,.5);roots.cyl((x+math.cos(a)*r,y+math.sin(a)*r,.18),(x+.12,y,6+random.uniform(-1,1)),.16,.045,'Bark',9)
  roots.cyl((x,y,.55),(x+math.cos(a)*random.uniform(.8,1.6),y+math.sin(a)*random.uniform(.8,1.6),.2),.17,.03,'Bark',8)
 for j in range(15):
  a=random.random()*math.tau;rr=random.uniform(.5,2);xx=x+rr*math.cos(a);yy=y+rr*math.sin(a);roots.cyl((xx,yy,2.3),(xx+.05,yy,6.7),.017,.012,'Bark',5)
roots.done()
trp=Mesh('Tree_Beds_and_Supports','Props')
for x in range(-171,-19,14):
 for y in [4.85,-5.6]:
  trp.box((x,y,.173),(1.3,1.3,.03),'Earth')
  for sgn in [-1,1]:trp.box((x+sgn*.7,y,.20),(.12,1.5,.13),'Concrete');trp.box((x,y+sgn*.7,.20),(1.5,.12,.13),'Concrete')
trp.done()
lamps=Mesh('Street_Lamps','Props')
for x,y in [(-164,4),(-136,-4),(-108,4),(-80,-4),(-51,4),(-23,-4),(5.2,-11),(5.2,19),(5.2,-43),(5.2,-76),(5.2,51),(5.2,79)]:
 lamps.cyl((x,y,.16),(x,y,7.8),.08,.047,'Galvanized',12)
 if x<0:tip=(x,y-math.copysign(1.2,y),8)
 else:tip=(x-1.2,y,8)
 lamps.cyl((x,y,7.7),tip,.045,.03,'Galvanized',10);lamps.box(tip,(.75,.28,.10),'DarkSteel');lamps.box((tip[0],tip[1],tip[2]-.06),(.62,.24,.025),'WarmLight')
 point_light('Road_Lamp_%d_%d'%(x,y),(tip[0],tip[1],tip[2]-.2),260,(1,.83,.61),.30)
lamps.done()
# Pedestrian signs and mirror; static props only, no invented signal controller.
sign=Mesh('Pedestrian_Signs_And_Corner_Mirror','Props')
for x,y,normal in [(-7,-8.8,(-1,0,0)),(5,-10,(0,-1,0)),(-7,8.8,(-1,0,0))]:
 sign.cyl((x,y,.16),(x,y,2.9),.031,.031,'Galvanized',10)
 n=Vector(normal);u=Vector((0,0,1)).cross(n);c=Vector((x,y,2.75))
 sign.face([c-u*.36+Vector((0,0,-.36)),c+u*.36+Vector((0,0,-.36)),c+u*.36+Vector((0,0,.36)),c-u*.36+Vector((0,0,.36))],'SignBlue')
 c+=n*.008;sign.face([c-u*.30+Vector((0,0,-.25)),c+u*.30+Vector((0,0,-.25)),c+Vector((0,0,.29))],'PaintWhite')
 # Walking figure silhouette, built as short bars, kept clear at game-camera distance.
 a=c+n*.014;sign.cyl(a+Vector((0,0,.14)),a+Vector((0,0,.16)),.043,.043,'DarkSteel',10)
 for p,q in [(a+Vector((0,0,.08)),a+Vector((0,0,-.08))),(a+Vector((0,0,-.06)),a-u*.09+Vector((0,0,-.20))),(a+Vector((0,0,-.06)),a+u*.11+Vector((0,0,-.18)))]:sign.cyl(p,q,.024,.024,'DarkSteel',6)
sign.cyl((7,-7,.16),(7,-7,3.1),.04,.04,'Galvanized',10);sign.cyl((7.01,-7,3),(6.95,-7,3),.31,.31,'ShopYellow',32);sign.cyl((6.94,-7,3),(6.92,-7,3),.285,.285,'GlassBlue',32)
sign.done()
ground=Mesh('Surrounding_Ground','Terrain');ground.box((-53,-5,-.43),(284,220,.6),'Earth');ground.done()
print('Setting cameras and exporting',flush=True)
def camera(name,loc,target,lens=25):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);link(o,'Cameras');o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=1000;return o
cams={
 '01_approach':camera('VIEW_01_Front_88s',(-19,-1.65,1.65),(9,0,2.2),22),
 '02_rear':camera('VIEW_02_Rear_88s',(-14,-1.65,1.65),(-60,0,2.3),22),
 '03_left':camera('VIEW_03_Left_Corner',(-3,-3,1.7),(-12,18,4),23),
 '04_right':camera('VIEW_04_Right_Shop',(0,-9.5,1.7),(-10,-17,2.6),21),
 '05_exit':camera('VIEW_05_Right_Turn_Exit',(-1.65,-15,1.7),(-1.65,-56,2.0),24),
 '00_aerial':camera('VIEW_00_Aerial',(39,-50,50),(-15,0,0),32),
 '06_gate':camera('VIEW_06_Gate',(-10,1,2),(9,0,3.2),28),
 '07_plan':camera('VIEW_07_Top',(-35,-8,180),(-35,-8,0),24)}
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
 for dev in pref.devices:dev.use=dev.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception as e:print(e)
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.7
world=bpy.data.worlds.new('Night_BlueHour');world.use_nodes=True;scene.world=world;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.13,.19,.32,1);bg.inputs['Strength'].default_value=.20
scene.use_nodes=True;nd=scene.node_tree.nodes;nd.clear();rl=nd.new('CompositorNodeRLayers');gl=nd.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=1.4;gl.size=7;comp=nd.new('CompositorNodeComposite');scene.node_tree.links.new(rl.outputs['Image'],gl.inputs['Image']);scene.node_tree.links.new(gl.outputs['Image'],comp.inputs['Image'])
for o in tree_protos:bpy.data.objects.remove(o,do_unlink=True)
# Texture coordinates are explicit and all transforms remain in a shared metric origin.
exported=[o for o in scene.objects if o.type=='MESH']
for o in exported:
 mod=o.modifiers.new('Triangulate_For_FBX_Tangents','TRIANGULATE');mod.quad_method='BEAUTY';mod.ngon_method='BEAUTY'
for o in exported:
 o['source']='four-view video referenced parametric reconstruction';o['metric_accuracy']='estimated, not surveyed'
bpy.ops.object.select_all(action='DESELECT')
for o in exported:o.select_set(True)
stats={'objects':len(exported),'vertices_instances':sum(len(o.data.vertices) for o in exported),'polygons_instances':sum(len(o.data.polygons) for o in exported),'materials':len(bpy.data.materials),'source_videos':['front','rear','left','right'],'vehicles_and_people':0,'coordinate_system':'RH metre, X approach toward gate, Y left, Z up','coverage':'T junction, 180m approach, 100m right arm, 85m left arm; unobserved distal arms simplified'}
bpy.ops.export_scene.fbx(filepath=str(ROOT/(NAME+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='Y',axis_up='Z',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False)
for img in bpy.data.images:
 if img.source=='FILE':img.filepath='//textures/'+Path(img.filepath).name
scene.camera=cams['01_approach'];bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(NAME+'.blend')))
(ROOT/'validation/mesh_statistics.json').write_text(json.dumps(stats,indent=2));(ROOT/'lighting.json').write_text(json.dumps({'lights':LIGHTS,'emissive_materials':emissions,'note':'Blender lighting is in blend and this manifest. FBX contains lamp meshes only. Recreate lights in Unreal; watts are artistic authoring values, not calibrated photometry.'},indent=2))
matlist=[]
for name,m in M.items():
 p=m.node_tree.nodes.get('Principled BSDF');rec={'name':name,'base_color':list(p.inputs['Base Color'].default_value)[:3],'roughness':p.inputs['Roughness'].default_value,'metallic':p.inputs['Metallic'].default_value,'textures':{}}
 for node in m.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image:rec['textures'][node.label]=Path(node.image.filepath).name
 if name in emissions:rec['emission']=emissions[name]
 matlist.append(rec)
(ROOT/'materials.json').write_text(json.dumps(matlist,indent=2))
print('EXPORTED',stats,flush=True)
def render(key,suffix):
 scene.camera=cams[key];scene.render.filepath=str(ROOT/'renders'/(key+'_'+suffix+'.png'));print('RENDER',key,suffix,flush=True);bpy.ops.render.render(write_still=True)
for key in ['01_approach','04_right','00_aerial','05_exit']:render(key,'night')
# Neutral daylight review uses the exact same meshes.
bg.inputs['Color'].default_value=(.63,.75,1,1);bg.inputs['Strength'].default_value=.65
ld=bpy.data.lights.new('Day_Review_Sun','SUN');ld.energy=2.2;ld.angle=.12;lo=bpy.data.objects.new('Day_Review_Sun',ld);link(lo,'Lighting');lo.rotation_euler=Vector((-.5,.7,-1)).to_track_quat('-Z','Y').to_euler()
for o in scene.objects:
 if o.type=='LIGHT' and o!=lo:o.hide_render=True
scene.view_settings.exposure=0
for key in ['00_aerial','01_approach','02_rear','03_left','04_right','05_exit','06_gate','07_plan']:render(key,'day')
print('FINISHED',flush=True)
