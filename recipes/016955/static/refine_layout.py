from pathlib import Path
P=Path(__file__).resolve().parent
p=P/'build_scene.py';s=p.read_text(encoding='utf-8')
changes={
"trans=lambda seq:[(cx+mirror*x,y) for x,y in seq]":"trans=lambda seq:[(cx+mirror*x,y) if jid==1 else (-y,x) for x,y in seq]",
"zebra(0,15.2,7)":"zebra(15.7,0,7,math.pi/2)",
"'leftright' if x==-30":"'both' if x==-30",
"range(-188,65,18)":"range(-188,-20,18)",
"range(-152,-13,3)":"range(-152,70,3)",
"[(8,-205),(8,-28),(10.5,-23),(10.5,75)]":"[(8,-205),(8,-28),(10.5,-23),(10.5,-15),(14,-12.2),(75,-12.2)]",
"hoarding('North_BranchBoundary',[(-10,24),(-10,75)])":"# Continuous north compound wall established from rear 114-150 sec.",
"for y in [-17,-14,-11,-8,-5,0,5,10,15,18]:bollard(4.6,y)":"for x,y in [(4.4,-18),(4.4,-16),(4.6,-14),(5.1,-11),(6,-9),(7.3,-7),(9,-5.5),(11,-4.7),(14,-4.25),(17,-4.25)]:bollard(x,y)",
"[-182,-151,-112,-76,-44,-15,18,49]":"[-182,-151,-112,-76,-44,-15]",
"range(-149,-17,27)":"range(-149,70,27)",
"range(-190,68,28)":"range(-190,-20,28)",
"range(-194,65,11)":"range(-194,-22,11)",
"for y in range(-188,110,23):tree(-180,y,.28,.65)":"for y in range(-188,110,23):\n if abs(y)>23:tree(-180,y,.28,.65)",
}
for a,b in changes.items():
 assert a in s,a;s=s.replace(a,b)
p.write_text(s,encoding='utf-8')
