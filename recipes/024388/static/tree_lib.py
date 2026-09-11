from scene_lib import *
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
