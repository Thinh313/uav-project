"""Same-host fused kernel admission. Expected bytes are immutable-oracle-proven raw."""
from pathlib import Path
import sys,gzip,json,struct,time,hashlib,statistics
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'runtime/sim32-pipe03-build/host-native'),str(R/'pilot/sim32'),str(R/'pilot/sim32-pipe03')]
from fast_physics import Model
from physics import Model as Baseline
E=R/'evidence/sim32-pipe03'
cases=[]
for ns,rid in [('sim32-pipe03','ui1791946639928')]+[('sim32-pacing02',p.name)for p in sorted((R/'evidence/sim32-pacing02/runs').iterdir())if p.is_dir()and(p/'model-replay.json').exists()]:
 p=R/'evidence'/ns/'runs'/rid;proof=json.loads((p/'model-replay.json').read_text());assert proof['status']=='PASS'
 m=Model(json.loads((p/'profile.json').read_text()));n=0;h=hashlib.sha256();started=time.perf_counter()
 with gzip.open(p/'physics-raw.jsonl.gz','rb')as f:
  for line in f:
   h.update(line);row=json.loads(line);_,rate,frame,*pwm=struct.unpack('<HHI16H',bytes.fromhex(row['servoHex']));result=m.step(pwm,1/rate)
   assert '\n'+json.dumps(result,separators=(',',':'),allow_nan=False)+'\n'==row['sensorUtf8'],(ns,rid,frame,'byte difference')
   snap=m.snapshot();assert all(snap[k]==row['modelAux'][k]for k in ['rpmEstimated','energyWhEstimated','ground']);n+=1
 assert h.hexdigest()==proof['rawSha256']
 cases.append({'namespace':ns,'run':rid,'exactFrames':n,'rawSha256':h.hexdigest(),'wallSeconds':time.perf_counter()-started});print(rid,n,'EXACT_FUSED_SENSOR_BYTES_AUX',flush=True)
 with(E/'integrator-oracle-progress.json').open('w')as f:json.dump({'status':'RUNNING_NOT_FINAL','cases':cases},f,indent=2)
benchmark=[]
for load,wind in [('empty','calm'),('central','crosswind'),('offset','gust')]:
 from physics import profile
 for rep in range(3):
  for cls,name in [(Baseline,'guarded-native-derivative'),(Model,'fused-RK4')][::1 if rep%2==0 else -1]:
   m=cls(profile(load,wind));start=time.perf_counter_ns()
   for n in range(6000):m.step([1050,1050,1050,1050],1/1200)
   benchmark.append({'profile':load+'-'+wind,'rep':rep,'engine':name,'steps':6000,'meanStepUs':(time.perf_counter_ns()-start)/6000/1000})
write={'status':'PASS_EXACT_BYTES_ALL_INPUTS','cases':cases,'totalExactFrames':sum(c['exactFrames']for c in cases),'microbenchmark':benchmark,'limitations':'Offline mean step cost, not closed-loop RTF; no physical calibration','sourcePins':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [R/'pilot/sim32-pipe03/integrator.c',R/'pilot/sim32-pipe03/fast_physics.py',next((R/'runtime/sim32-pipe03-build/host-native').glob('*.so'))]}}
with(E/'integrator-oracle.json').open('x')as f:json.dump(write,f,indent=2);f.write('\n')
