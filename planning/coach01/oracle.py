"""Second implementation, no JavaScript verifier import; same author, not human QA."""
from pathlib import Path
import json,base64,struct,math,hashlib,random,subprocess
R=Path(__file__).resolve().parents[2]
b=json.loads((R/'evidence/betaworkbench05/android-saf-package01.json').read_bytes());report=json.loads((R/'evidence/coach01/tests01/actual-report.json').read_text());rows=[json.loads(l)for l in base64.b64decode(b['files']['flight/raw.jsonl']['base64']).decode().splitlines()]
extra={0:50,33:104};buf=b'';known=0;hb=None;trace=[]
phi=math.radians(report['plan']['origin']['lat']);lam=math.radians(report['plan']['origin']['lon']);A=6378137;F=1/298.257223563;E2=F*(2-F)
def ecef(lat,lon):
 p=math.radians(lat);l=math.radians(lon);n=A/math.sqrt(1-E2*math.sin(p)**2);return(n*math.cos(p)*math.cos(l),n*math.cos(p)*math.sin(l),n*(1-E2)*math.sin(p))
base=ecef(report['plan']['origin']['lat'],report['plan']['origin']['lon']);east=(-math.sin(lam),math.cos(lam),0);north=(-math.sin(phi)*math.cos(lam),-math.sin(phi)*math.sin(lam),math.cos(phi))
def xy(lat,lon):
 q=[a-b for a,b in zip(ecef(lat,lon),base)];return(sum(a*b for a,b in zip(q,east)),sum(a*b for a,b in zip(q,north)))
for row in rows:
 if row['kind']!='RX_RAW':continue
 t=int(row['hostNs'])/1e6;buf+=bytes.fromhex(row['data']['rawHex'])
 while buf:
  if buf[0]not in(253,254):buf=buf[1:];continue
  v2=buf[0]==253;h=10 if v2 else 6
  if len(buf)<h:break
  n=buf[1];signed=v2 and(buf[2]&1);total=h+n+2+(13 if signed else 0)
  if len(buf)<total:break
  frame=buf[:total];buf=buf[total:];mid=int.from_bytes(frame[7:10],'little')if v2 else frame[5]
  if mid not in extra:continue
  c=65535
  for v in frame[1:h+n]+bytes([extra[mid]]):
   z=v^(c&255);z^=(z<<4)&255;c=((c>>8)^(z<<8)^(z<<3)^(z>>4))&65535
  assert c==int.from_bytes(frame[h+n:h+n+2],'little')
  known+=1
  if(frame[5 if v2 else 3],frame[6 if v2 else 4])!=(42,1):continue
  p=frame[h:h+n]+bytes(32)
  if mid==0:hb={'host':t,'mode':struct.unpack_from('<I',p)[0],'armed':bool(p[6]&128),'record':row['n']}
  else:
   boot,lat,lon,msl,rel,vx,vy,vz,heading=struct.unpack_from('<IiiiihhhH',p);x,y=xy(lat/1e7,lon/1e7);fresh=hb is not None and t-hb['host']<=1500
   trace.append({'record':row['n'],'hostMs':t,'bootMs':boot,'latitudeDeg':lat/1e7,'longitudeDeg':lon/1e7,'relativeHomeM':rel/1000,'vx':vx/100,'vy':vy/100,'groundSpeedMS':math.hypot(vx,vy)/100,'headingDeg':None if heading==65535 else heading/100,'x':x,'y':y,'mode':hb['mode']if fresh else None,'armed':hb['armed']if fresh else None})
assert not buf and len(trace)==len(report['telemetry']['trace'])
for a,b in zip(trace,report['telemetry']['trace']):
 for k,v in a.items():
  if v is None or type(v)is bool:assert v==b[k],k
  else:assert abs(v-b[k])<1e-6,(k,v,b[k])
def pct(xs):return sorted(xs)[math.ceil(len(xs)*.95)-1]if xs else None
acc=[];turn=[];eligible=[]
for i,t in enumerate(trace):
 if t['mode']==3 and t['armed']and t['relativeHomeM']>2:
  if i and trace[i-1]['mode']==3 and trace[i-1]['armed']and trace[i-1]['relativeHomeM']>2:
   a=trace[i-1];g=t['bootMs']-a['bootMs'];h=t['hostMs']-a['hostMs']
   if 0<g<=1000 and 0<=h<=2000:
    acc.append(math.sqrt((t['vx']-a['vx'])**2+(t['vy']-a['vy'])**2)/(g/1000))
    if t['headingDeg']is not None and a['headingDeg']is not None:turn.append(abs((t['headingDeg']-a['headingDeg']+180)%360-180)/(g/1000))
 if t['mode']==3 and t['armed']and abs(t['relativeHomeM']-report['plan']['plannedAltitudeRelativeHomeM'])<=2:
  ds=[]
  for l in report['plan']['legs']:
   a=l['start'];b=l['end'];u=(b['x']-a['x'],b['y']-a['y']);v=(t['x']-a['x'],t['y']-a['y']);dot=sum(x*y for x,y in zip(u,v));length=sum(x*x for x in u);f=max(0,min(1,dot/length))if length else 0;ds.append(math.sqrt((v[0]-f*u[0])**2+(v[1]-f*u[1])**2))
  eligible.append(min(ds))
for key,value in [('accelerationP95MS2',pct(acc)),('headingRateP95DegS',pct(turn))]:assert abs(value-report['telemetry']['motion'][key])<1e-8
assert abs(pct(eligible)-report['telemetry']['metrics']['nearestStripP95M'])<1e-6
# Analytic holdout geometry/angles: generated after engine, seed fixed; not unseen real flight data.
rng=random.Random(20261025);cases=[]
for _ in range(120):
 a=[rng.uniform(-100,100)for _ in range(2)];b=[rng.uniform(-100,100)for _ in range(2)];p=[rng.uniform(-100,100)for _ in range(2)];first=rng.uniform(0,360);second=rng.uniform(0,360)
 # Second path: ternary search of squared distance on a closed segment.
 lo=0;hi=1
 def d(t):return sum((p[i]-a[i]-(b[i]-a[i])*t)**2 for i in range(2))
 for _ in range(100):
  u=lo+(hi-lo)/3;v=hi-(hi-lo)/3
  if d(u)<d(v):hi=v
  else:lo=u
 expected=math.sqrt(min(d(0),d(1),d((lo+hi)/2)));signed=math.degrees(math.atan2(math.sin(math.radians(second-first)),math.cos(math.radians(second-first))))
 cases.append({'a':dict(zip(['x','y'],a)),'b':dict(zip(['x','y'],b)),'p':dict(zip(['x','y'],p)),'first':first,'second':second,'distance':expected,'angle':signed})
js="import{segmentDistance,angleDelta}from'./pilot/coach01/core.mjs';let t='';for await(const c of process.stdin)t+=c;console.log(JSON.stringify(JSON.parse(t).map(c=>({distance:segmentDistance(c.p,c.a,c.b),angle:angleDelta(c.first,c.second)}))));"
r=subprocess.run(['node','--input-type=module','-e',js],input=json.dumps(cases),text=True,capture_output=True,cwd=R,check=True);got=json.loads(r.stdout)
for a,b in zip(cases,got):assert abs(a['distance']-b['distance'])<1e-7 and abs(a['angle']-b['angle'])<1e-8
result={'status':'PASS','implementation':'PYTHON_STRUCT_CRC_ECEF_DIFFERENCES_AND_TERNARY_SEGMENT_ORACLE','actualWireKnownMessages':known,'positionSamples':len(trace),'accelerationP95MS2':pct(acc),'headingRateP95DegS':pct(turn),'nearestStripP95M':pct(eligible),'analyticHoldoutCases':len(cases),'holdoutScope':'ASSISTANT_AUTHORED_SEEDED_MATH_NOT_REAL_UNSEEN_FLIGHTS','independentHumanQA':False}
(R/'evidence/coach01/oracle01.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
