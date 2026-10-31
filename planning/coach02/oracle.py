"""Second numerical implementation, not physical calibration or human assessment."""
from pathlib import Path
import math,json,subprocess,random
R=Path(__file__).resolve().parents[2];folder=R/'evidence/coach02/tests02/reference'
js="import fs from'node:fs';import{makePackage}from'./pilot/coach02/journal.mjs';const root='evidence/coach02/tests02/reference';console.log(JSON.stringify(fs.readdirSync(root).map(id=>{const p=makePackage(root,id);return {id,sha256:p.sha256,review:{within:p.review.withinReferenceFraction,horizontal:p.review.horizontalErrorP95M,altitude:p.review.altitudeErrorP95M,heading:p.review.headingErrorP95Deg,steps:p.review.observedSteps,verdict:p.review.verdict}}})));"
summaries=json.loads(subprocess.run(['node','--input-type=module','-e',js],cwd=R,capture_output=True,text=True,check=True).stdout)
base=json.loads((R/'evidence/coach02/tests02/reference-package.json').read_text());assert summaries[0]['sha256']==base['sha256']
def smooth(t,a,b):
 u=max(0,min(1,(t-a)/(b-a)));return u*u*(3-2*u)
def target(kind,t):return(0,12*smooth(t,3,13)if kind=='straight'else 0,10,90*smooth(t,4,12)if kind=='turn'else 0)
def wrap(x):return math.degrees(math.atan2(math.sin(math.radians(x)),math.cos(math.radians(x))))
def pct(xs):return sorted(xs)[math.ceil(len(xs)*.95)-1]
frames=0;max_error=0;max_clock_error=0
for info in summaries:
 rows=[json.loads(l)for l in(folder/info['id']/'journal.jsonl').read_text().splitlines()];start=rows[0]['data'];profile=start['profile'];kind=start['context']['exerciseId'];m={'x':0.,'y':0.,'z':10.,'vx':0.,'vy':0.,'vz':0.,'yaw':0.,'yawRate':0.};errs=[];clock=None;count=0
 for row in rows[1:]:
  d=row['data'];a=d['action']
  if not d['outcome']['accepted']:continue
  if a['kind']=='sync':clock=(start['challenge']['t2']-a['t3'],start['challenge']['t1']-a['t0'],a['sourceTimeMs'])
  if a['kind']!='tick':continue
  count+=1;frames+=1;axes=a['axes'];r=math.radians(m['yaw']);wanted={'vx':profile['speedMS']*(axes['roll']*math.cos(r)+axes['pitch']*math.sin(r))+profile['windEastMS'],'vy':profile['speedMS']*(axes['pitch']*math.cos(r)-axes['roll']*math.sin(r))+profile['windNorthMS'],'vz':profile['climbMS']*axes['throttle'],'yawRate':profile['yawRateDegS']*axes['yaw']};decay=math.exp(-.05/profile['tauS']);new={k:wanted[k]+(m[k]-wanted[k])*decay for k in wanted}
  for pos,vel in [('x','vx'),('y','vy'),('z','vz')]:m[pos]+=.025*(m[vel]+new[vel])
  m['yaw']=wrap(m['yaw']+.025*(m['yawRate']+new['yawRate']));m.update(new)
  for k,v in m.items():error=abs(v-d['state']['model'][k]);max_error=max(max_error,error);assert error<1e-9,(kind,k,error)
  t=count*.05;tx,ty,tz,heading=target(kind,t);errs.append((math.hypot(m['x']-tx,m['y']-ty),abs(m['z']-tz),abs(wrap(m['yaw']-heading))))
  lo,hi,anchor=clock;drift=abs(a['sourceTimeMs']-anchor)*100/1e6;lower=a['sourceTimeMs']+lo-drift;upper=min(a['sourceTimeMs']+hi+drift,d['hostMs']);reported=d['outcome']['bounds'];max_clock_error=max(max_clock_error,abs(lower-reported['lowerHostMs']),abs(upper-reported['upperHostMs']));assert abs(lower-reported['lowerHostMs'])<1e-9 and abs(upper-reported['upperHostMs'])<1e-9
 for key,i in [('horizontal',0),('altitude',1),('heading',2)]:assert abs(info['review'][key]-pct([e[i]for e in errs]))<1e-9
 assert count==info['review']['steps']and info['review']['verdict']=='PASS_REFERENCE_EXERCISE'
rng=random.Random(20261025);cases=[]
for i in range(100):
 t0=rng.uniform(1000,2000);offset=rng.uniform(-400,400);one=rng.uniform(0,20);process=rng.uniform(0,5);two=rng.uniform(0,20);t1=t0+offset+one;t2=t1+process;t3=t0+one+process+two
 cases.append(dict(t0=t0,t1=t1,t2=t2,t3=t3,offset=offset,now=t3+offset+one,i=i))
js="import{createState,apply}from'./pilot/coach02/engine.mjs';let s='';for await(const c of process.stdin)s+=c;console.log(JSON.stringify(JSON.parse(s).map(c=>{const ctx={sessionId:'m'+String(c.i).padStart(32,'0'),hostBoot:'host',operatorId:'operator',sourceClockId:'source',sourceKind:'SCRIPTED_MOCK',profileId:'unloaded',exerciseId:'hover'},a=createState(ctx,{nonce:'q',t1:c.t1,t2:c.t2},c.t2);const r=apply(a,{...ctx,kind:'sync',seq:1,sourceTimeMs:c.t3,nonce:'q',t0:c.t0,t3:c.t3},c.now);return{accepted:r.outcome.accepted,clock:r.state.clock};})));"
got=json.loads(subprocess.run(['node','--input-type=module','-e',js],cwd=R,input=json.dumps(cases),text=True,capture_output=True,check=True).stdout)
for a,b in zip(cases,got):assert b['accepted']and b['clock']['offsetLowerMs']<=a['offset']+1e-9 and b['clock']['offsetUpperMs']>=a['offset']-1e-9
out={'status':'PASS','referenceCases':len(summaries),'modelFramesRecomputed':frames,'maximumModelComponentError':max_error,'maximumClockBoundsErrorMs':max_clock_error,'asymmetricClockPropertyCases':len(cases),'seed':20261025,'method':'PYTHON_CLOSED_FORM_VELOCITY_RESPONSE_ROTATION_TARGET_AND_CLOCK_INTERVAL_CONTAINMENT','source':'SYNTHETIC_SCRIPTED_REFERENCE_NOT_HERA_OR_UNSEEN_REAL_FLIGHTS','independentHumanQA':False}
(R/'evidence/coach02/oracle01.json').open('x').write(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
