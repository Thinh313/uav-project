"""Bounded streaming exact-model/raw replay. Integrity is not physical calibration."""
from pathlib import Path
import sys,json,gzip,hashlib,struct,time,importlib.util
from physics import Model
R=Path(__file__).resolve().parents[2]
def verify(rid):
 out=R/'evidence/sim32/runs'/rid
 launch=json.loads((out/'launch.json').read_text())
 model_class=Model;model_hash=launch['modulePins']['pilot/sim32/physics.py']
 if hashlib.sha256((R/'pilot/sim32/physics.py').read_bytes()).hexdigest()!=model_hash:
  candidates=[p for p in (R/'evidence/sim32/source-iterations').glob('*/physics.py') if hashlib.sha256(p.read_bytes()).hexdigest()==model_hash]
  if not candidates:raise ValueError('Pinned model version unavailable')
  spec=importlib.util.spec_from_file_location('sim32_pinned_model',candidates[0]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);model_class=module.Model
 model=model_class(json.loads((out/'profile.json').read_text()));count=0;digest=hashlib.sha256();first=last=None;frame=None;rates=set();peak=0;air_energy=[];hover=[]
 with gzip.open(out/'physics-raw.jsonl.gz','rb') as f:
  for line in f:
   if len(line)>8192:raise ValueError('Raw line bound')
   row=json.loads(line);magic,rate,seq,*pwm=struct.unpack('<HHI16H',bytes.fromhex(row['servoHex']))
   assert magic==18458 and seq==row['frame'] and rate==row['rate'] and (frame is None or seq==frame+1)
   observed=json.loads(row['sensorUtf8']);expected=model.step(pwm,1/rate);assert expected==observed,'Sensor/model byte-value mismatch'
   aux=row.get('modelAux',row.get('model'));snapshot=model.snapshot()
   for key in ['rpmEstimated','energyWhEstimated','ground']:assert aux[key]==snapshot[key],key
   frame=seq;count+=1;digest.update(line);rates.add(rate);peak=max(peak,-observed['position'][2]);last=row['hostMonotonicNs'];first=last if first is None else first
   if not model.ground and abs(observed['velocity'][2])<.1 and -observed['position'][2]>4:
    hover.append(sum(snapshot['rpmEstimated'])/4)
 summary=json.loads((out/'backend-summary.json').read_text());assert count==summary['frames'] and digest.hexdigest()==summary['rawSha256']
 wall=(last-first)/1e9 if count>1 else 0
 return {'run':rid,'exactFrames':count,'rawSha256':digest.hexdigest(),'shaMatch':True,'ratesHz':sorted(rates),'modelSeconds':model.t,'activeWireWallSeconds':wall,'activeRealTimeFactor':model.t/wall if wall else None,'peakAltitudeM':peak,'energyWhEstimated':model.energyWh,'meanStableFlightRpmEstimated':sum(hover)/len(hover) if hover else None,'backendStatus':summary['status'],'scope':'Exact-model/raw integrity; not independent aerodynamic reference or Hera calibration'}
if __name__=='__main__':
 rid=sys.argv[1]
 if not rid.isalnum() or len(rid)>32:raise ValueError('Run ID')
 receipt=verify(rid);out=R/'evidence/sim32/runs'/rid/'raw-replay.json'
 with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt))
