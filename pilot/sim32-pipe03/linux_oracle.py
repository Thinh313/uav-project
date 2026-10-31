"""Offline platform admission only; no SITL or command socket."""
from pathlib import Path
import sys,gzip,struct,json,hashlib,platform,time
R=Path('/project');sys.path[:0]=[str(R/'runtime/sim32-pipe03-build/native'),str(R/'pilot/sim32')]
from physics import Model
report={'platform':platform.platform(),'python':sys.version,'kernelSha256':hashlib.sha256(next((R/'runtime/sim32-pipe03-build/native').glob('*.so')).read_bytes()).hexdigest(),'cases':[],'status':'PASS'}
for namespace,rid in [('sim32-pipe03','ui1791946639928')]:
 e=R/'evidence'/namespace/'runs'/rid;m=Model(json.loads((e/'profile.json').read_text()));n=0
 with gzip.open(e/'physics-raw.jsonl.gz','rt')as f:
  for line in f:
   row=json.loads(line);_,rate,frame,*pwm=struct.unpack('<HHI16H',bytes.fromhex(row['servoHex']));result=m.step(pwm,1/rate);encoded='\n'+json.dumps(result,separators=(',',':'),allow_nan=False)+'\n'
   if encoded!=row['sensorUtf8']:
    report['status']='REJECT_PLATFORM_BYTE_DIFFERENCE';report['cases'].append({'run':rid,'exactPrefixFrames':n,'firstDifferenceFrame':frame,'expected':row['sensorUtf8'],'actual':encoded});break
   n+=1
  else:report['cases'].append({'run':rid,'exactFrames':n})
print(json.dumps(report,indent=2))
