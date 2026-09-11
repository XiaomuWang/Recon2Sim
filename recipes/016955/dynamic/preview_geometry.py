"""Road surface outlines matching the existing static build_scene.py."""
import math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'environment_reconstruction_016955/scripts'))
from road_layout import ROADS,pose
def road_polygons():
 result=[]
 for rid,r in ROADS.items():
  hw=r['n']*3.5+r['median'];result.append([(p[0],p[1]) for p in [pose(rid,0,-hw),pose(rid,r['length'],-hw),pose(rid,r['length'],hw),pose(rid,0,hw)]])
 def arc(cx,cy,r,a,b):return [(cx+r*math.cos(a+(b-a)*i/32),cy+r*math.sin(a+(b-a)*i/32)) for i in range(33)]
 for jid,cx,hw,mirror in [(1,-180,11.7,-1),(2,0,3.5,1)]:
  r=4.5 if jid==1 else 7.;b=3.5
  lower=[(-20,-b),(-hw-r,-b)]+arc(-hw-r,-b-r,r,math.pi/2,0)+[(-hw,-20)]
  upper=[(-hw,20),(-hw,b+r)]+arc(-hw-r,b+r,r,0,-math.pi/2)+[(-20,b)]
  pts=lower+[(hw,-20),(hw,20)]+upper
  result.append([(cx+mirror*x,y) if jid==1 else (-y,x) for x,y in pts])
 return result
