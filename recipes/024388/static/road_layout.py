import math
NAME='LuoboTurn024388'
LANE=3.3
ROADS=[
 {'id':10,'name':'Approach_shopping_street','x':-180.,'y':0.,'h':0.,'length':168.,'junction_end':'end','w':LANE},
 {'id':20,'name':'Right_turn_exit','x':0.,'y':-12.,'h':-math.pi/2,'length':88.,'junction_end':'start','w':LANE},
 {'id':30,'name':'Left_cross_street','x':0.,'y':12.,'h':math.pi/2,'length':73.,'junction_end':'start','w':LANE}]
def road_point(r,s,t=0):
 h=r['h'];return (r['x']+s*math.cos(h)-t*math.sin(h),r['y']+s*math.sin(h)+t*math.cos(h),0)
def pose(s,t=0,z=0):return (s,t,z,0)
def path_pose(p,s,t=0):
 if 'segments' in p:
  for part in p['segments']:
   if s<=part['length']+1e-7:return path_pose(part,max(0,min(s,part['length'])),t)
   s-=part['length']
  return path_pose(p['segments'][-1],p['segments'][-1]['length'],t)
 x,y,h,k=p['x'],p['y'],p['h'],p['k']
 if k:x+=(math.sin(h+k*s)-math.sin(h))/k;y-=(math.cos(h+k*s)-math.cos(h))/k
 else:x+=s*math.cos(h);y+=s*math.sin(h)
 h+=k*s;return (x-t*math.sin(h),y+t*math.cos(h),0,h)
