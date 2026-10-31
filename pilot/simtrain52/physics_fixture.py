"""Offline open-loop model comparison, not ArduPilot, flight/control or RTF acceptance."""
from pathlib import Path
import sys,importlib.util,json,hashlib,time,shutil,math
R=Path(__file__).resolve().parents[2];E=R/'evidence/simtrain52';sys.path[:0]=[str(R/'pilot/sim32'),str(R/'pilot/sim32-pipe03'),str(R/'runtime/sim32-pipe03-build/host-native')]
from fast_physics import Model,profile
spec=importlib.util.spec_from_file_location('immutable_sim32_reference52',R/'evidence/sim32/source-final/pilot/sim32/physics.py');ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
def enc(x):return json.dumps(x,separators=(',',':'),allow_nan=False)
def main():
 assert shutil.disk_usage(R).free>20*2**30+64*2**20
 root=E/'model1';root.mkdir();tests=[];cases=[];frame_count=2400
 for load,wind in [('empty','calm'),('central','calm'),('empty','gust')]:
  p=profile(load,wind);a=Model(p);b=ref.Model(p);name=load+'-'+wind;samples=[{'frame':-1,**a.snapshot()}];chain=hashlib.sha256();start=time.monotonic();before=shutil.disk_usage(R).free
  with(root/(name+'.jsonl')).open('x')as f:
   f.write(enc({'type':'HEADER','scope':'OFFLINE_OPEN_LOOP_MODEL_NO_AUTOPILOT_NO_FLIGHT','profile':p,'rateHz':1200,'frames':frame_count,'renderDecimation':20,'rawAllFramesRetained':True})+'\n')
   for i in range(frame_count):
    if i%400==0:assert shutil.disk_usage(R).free>20*2**30+32*2**20
    pwm=[1000]*16;pwm[:4]=[1000 if i<120 else 1800]*4
    s=a.step(pwm,1/1200);r=b.step(pwm,1/1200);actual=enc(s);expected=enc(r)
    assert actual==expected,('ORACLE_BYTES',name,i)
    raw=enc({'frame':i,'pwm':pwm,'sensorUtf8':actual,'aux':a.snapshot()})+'\n';f.write(raw);chain.update(raw.encode())
    if (i+1)%20==0:samples.append({'frame':i,**a.snapshot()})
  tests.append({'name':name,'pass':True,'exactSensorFrameComparisons':frame_count,'scope':'same-platform exact original implementation oracle; not physical/Hera validation','rawFrameSha256':chain.hexdigest(),'offlineElapsedSeconds':time.monotonic()-start})
  cases.append({'id':name,'profile':p,'samples':samples,'rawFrames':frame_count,'source':'OFFLINE_REFERENCE_MODEL_NO_SITL','durationSeconds':frame_count/1200,'renderRateHz':60,'rawRateHz':1200,'rawSha256':hashlib.sha256((root/(name+'.jsonl')).read_bytes()).hexdigest()})
 out={'format':'simtrain52-offline-reference-v1','scope':'RECORDED_OPEN_LOOP_PHYSICS_NOT_LIVE_NOT_HERA_NOT_SITL','modelFrameComparisons':len(cases)*frame_count,'dt':1/1200,'cases':cases,'sourcePins':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[R/'pilot/sim32-pipe03/fast_physics.py',R/'evidence/sim32/source-final/pilot/sim32/physics.py']}}
 (E/'model-fixture.json').write_text(enc(out)+'\n');(root/'receipt.json').write_text(json.dumps({'status':'PASS_OFFLINE_MODEL_ORACLE','cases':tests,'exactFrameComparisons':frame_count*len(cases),'physicsStepsSkipped':0,'sensorBytesMatched':True,'physicalValidation':False,'autopilotStarted':False,'realTimeFactorClaim':False},indent=2)+'\n');print(json.dumps({'status':'PASS_OFFLINE_MODEL_ORACLE','exactFrameComparisons':frame_count*len(cases),'sampleEndPositions':{c['id']:c['samples'][-1]['position']for c in cases}}))
if __name__=='__main__':main()
