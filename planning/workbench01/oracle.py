"""Separate brute-force formulation, standard library only, no imports from JS planner."""
import json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2]
cases=json.loads((R/'evidence/workbench01/oracle-input.json').read_text());out=[]
def inside(x,y,poly):
 # Independent winding number at grid centers, handles tested non-boundary points.
 winding=0
 for a,b in zip(poly,poly[1:]+poly[:1]):
  cross=(b['x']-a['x'])*(y-a['y'])-(b['y']-a['y'])*(x-a['x'])
  if a['y']<=y<b['y'] and cross>0:winding+=1
  elif b['y']<=y<a['y'] and cross<0:winding-=1
 return winding!=0
for c in cases:
 p=c['plan'];st=c['stepM'];ps=sum(p['regions'],[]);xmin=math.floor(min(q['x'] for q in ps)/st)*st;ymin=math.floor(min(q['y'] for q in ps)/st)*st
 nx=math.ceil((max(q['x'] for q in ps)-xmin)/st);ny=math.ceil((max(q['y'] for q in ps)-ymin)/st);n=hit=0
 for j in range(ny):
  for i in range(nx):
   x=xmin+(i+.5)*st;y=ymin+(j+.5)*st
   if not any(inside(x,y,r) for r in p['regions']):continue
   n+=1;covered=False
   for f in p['shots']:
    angle=math.atan2(f['uy'],f['ux']);dx=x-f['x'];dy=y-f['y'];along=dx*math.cos(angle)+dy*math.sin(angle);across=-dx*math.sin(angle)+dy*math.cos(angle)
    covered|=abs(along)<=f['alongM']/2+1e-8 and abs(across)<=f['acrossM']/2+1e-8
   hit+=covered
 assert n==len(c['result']['cells']),c['name']
 assert abs(100*hit/n-c['result']['plannedPct'])<1e-9,c['name']
 out.append({'case':c['name'],'status':'PASS','cells':n,'plannedPct':100*hit/n})
result={'status':'PASS','method':'Python winding number plus trigonometric rectangle projection, brute force, independently formulated code by same assistant','cases':out,'externalGroundTruth':False}
(R/'evidence/workbench01/math-oracle01.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
