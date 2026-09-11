from scene_lib import *
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
def frontface(m,x,y,z,w,h,mat,side=-1):
 v=[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)]
 if side==1:v.reverse()
 m.face(v,mat,[(0,0),(1,0),(1,1),(0,1)] if side==-1 else [(1,1),(0,1),(0,0),(1,0)])
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
  frontface(m,xx,face-sg*.383,3.82,sw-.2,1.05,'Sign'+str((j+int(abs(x)/8)+style)%12),-sg)
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
   m.box((xx,face-sg*.055,z),(ww+.16,.12,1.89),'WindowFrame');m.box((xx,face-sg*.122,z),(ww,.025,1.72),'GlassBlue' if (f+j)%5 else 'GlassDark')
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
tree_protos=[]
for variant in range(5):
 m=Mesh('Tree_Prototype_%d'%variant,'Vegetation');height=random.uniform(8.5,10.3)
 m.cyl((0,0,0),(.1,-.08,height*.67),.28,.095,'Bark',12);m.cyl((0,0,0),(.017,-.014,1.35),.284,.251,'LeafTrunkWhite',12)
 clusters=[]
 for b in range(17):
  ang=b*2.4;z=height*random.uniform(.50,.85);r=random.uniform(1.3,2.7);end=(math.cos(ang)*r,math.sin(ang)*r,z+random.uniform(.6,1.6))
  m.cyl((.08,0,z*.63),end,.085,.018,'Bark',7);clusters.append(end)
 for c in clusters:
  for j in range(350):
   theta=random.random()*math.tau;zz=random.uniform(-1,1);rr=random.random()**(1/3);rd=math.sqrt(1-zz*zz)
   pos=(c[0]+1.75*rr*rd*math.cos(theta),c[1]+1.75*rr*rd*math.sin(theta),c[2]+1.4*rr*zz)
   m.leaf(pos,random.uniform(.12,.23),'Leaf'+str(random.randrange(6)))
 o=m.done();o.hide_render=True;o.hide_viewport=True;tree_protos.append(o)
def tree(x,y,z=.18,scale=1):
 p=random.choice(tree_protos);o=bpy.data.objects.new(NAME+'_Vegetation_StreetTree',p.data);link(o,'Vegetation');o.location=(x,y,z);o.scale=(scale,scale,scale);o.rotation_euler.z=random.uniform(0,math.tau);return o
