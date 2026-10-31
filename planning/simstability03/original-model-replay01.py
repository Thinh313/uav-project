#!/usr/bin/env python3
"""Independent immutable pure-Python model replay, explicitly cold and bounded.

Run only after Contractor confirms no AP remains active:
python3 -B planning/simstability03/original-model-replay01.py --ack-runtimes-closed
No native code is loaded and no simulator or old helper CLI is executed.
Exact byte comparison has no tolerance. Numerical drift is reported separately.
"""
import argparse,collections,datetime,hashlib,importlib.util,json,math,pathlib,struct,subprocess,sys,time,zlib
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];REC=ROOT/'.local/simstability03/receiver03';RUN='rc8f9c0bfcc3a4563b492';R=REC/'evidence/simhand01/runs'/RUN
MODEL=REC/'evidence/sim32/source-final/pilot/sim32/physics.py';OUT=ROOT/'evidence/simstability03/original-model-replay01.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def compare_numeric(expected,actual,path,drift,structural):
 if isinstance(expected,bool)or isinstance(actual,bool):
  if expected!=actual:structural[path]+=1
 elif isinstance(expected,(int,float))and isinstance(actual,(int,float)):
  assert math.isfinite(expected)and math.isfinite(actual),'NONFINITE_REPLAY'
  drift[path]=max(drift.get(path,0),abs(expected-actual))
 elif isinstance(expected,dict)and isinstance(actual,dict):
  if set(expected)!=set(actual):structural[path+'.keys']+=1
  for k in expected.keys()&actual.keys():compare_numeric(expected[k],actual[k],path+'.'+k,drift,structural)
 elif isinstance(expected,list)and isinstance(actual,list):
  if len(expected)!=len(actual):structural[path+'.length']+=1
  for i,(a,b)in enumerate(zip(expected,actual)):compare_numeric(a,b,path+'['+str(i)+']',drift,structural)
 elif expected!=actual:structural[path]+=1

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--ack-runtimes-closed',action='store_true');args=parser.parse_args()
 if not args.ack_runtimes_closed:parser.error('Explicit cold-runtime acknowledgement required; do not run during an AP test.')
 active=subprocess.run(['docker','ps','--filter','label=aeris.task=simhand01','--format','{{.ID}}'],capture_output=True,text=True,timeout=5,check=True).stdout.strip()
 assert not active,'ACTIVE_SIMHAND_AP_DEFER_REPLAY'
 assert not OUT.exists(),'EXCLUSIVE_NEW_RECEIPT_REQUIRED'
 before={n:sha(R/n)for n in ['frames.wal','request.json','backend-result.json']};modelSHA=sha(MODEL);pins=json.loads((ROOT/'evidence/simstability03/source-pins03.json').read_text());assert modelSHA==pins['files'][str(MODEL.relative_to(REC))]['sha256']
 config=json.loads((R/'request.json').read_text());backend=json.loads((R/'backend-result.json').read_text());spec=importlib.util.spec_from_file_location('original_pure_python_model',MODEL);original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original);model=original.Model(original.profile(config['load'],config['wind'],config['seed']))
 started=time.monotonic();chain=bytes(32);sequence=0;frames=0;prev=None;pwm=None;rxRaw=None;phase='HEADER';mismatches={'sensorUtf8':0,'modelAux':0};firstDiff=None;drift={};structural=collections.Counter();groupMax={};stop=None;close=0
 try:
  with(R/'frames.wal').open('rb')as f:
   assert f.read(8)==b'AERISJ04'
   while True:
    if time.monotonic()-started>300:stop='REPLAY_DEADLINE300';break
    header=f.read(28)
    if not header:break
    assert len(header)==28
    kind,flags,reserved,frame,size,index,stamp=struct.unpack('<BBHIIQQ',header);assert flags==reserved==0 and index==sequence and size<=16384
    body=f.read(size);tail=f.read(36);assert len(body)==size and len(tail)==36
    digest=hashlib.sha256(chain+header+body).digest();assert tail[4:]==digest and int.from_bytes(tail[:4],'little')==zlib.crc32(header+body);chain=digest;sequence+=1
    if kind==1:assert phase=='HEADER';phase='RX'
    elif kind==2:
     assert phase=='RX';rx=json.loads(body);rxRaw=bytes.fromhex(rx['rawHex']);magic,rate,servoFrame,*pwm=struct.unpack('<HHI16H',rxRaw);assert magic==18458 and rate==1200 and servoFrame==frame and(prev is None or frame==prev+1);phase='INTENT'
    elif kind==3:
     assert phase=='INTENT';n,snap=struct.unpack_from('<II',body);assert snap==0 and len(body)==n+8;captured=json.loads(body[8:]);assert captured['frame']==frame and captured['rate']==1200 and captured['servoHex']==rxRaw.hex() and captured['epoch']==backend['epoch']
     sensors=model.step(pwm,1/1200);aux=model.snapshot();expected='\n'+json.dumps(sensors,separators=(',',':'),allow_nan=False)+'\n';auxJSON=json.dumps(aux,separators=(',',':'),allow_nan=False);sensorMismatch=expected!=captured['sensorUtf8'];auxMismatch=auxJSON!=json.dumps(captured['modelAux'],separators=(',',':'),allow_nan=False);mismatches['sensorUtf8']+=sensorMismatch;mismatches['modelAux']+=auxMismatch
     if(sensorMismatch or auxMismatch)and firstDiff is None:firstDiff={'frame':frame,'admittedOrdinal':frames,'sensorBytesDiffer':sensorMismatch,'modelAuxBytesDiffer':auxMismatch,'expectedSensorSHA256':hashlib.sha256(expected.encode()).hexdigest(),'capturedSensorSHA256':hashlib.sha256(captured['sensorUtf8'].encode()).hexdigest(),'expectedSensorBytes':len(expected.encode()),'capturedSensorBytes':len(captured['sensorUtf8'].encode())}
     observed=json.loads(captured['sensorUtf8']);compare_numeric(sensors,observed,'sensor',drift,structural);compare_numeric(aux,captured['modelAux'],'modelAux',drift,structural)
     for key in ['position','velocity','quaternion','velocity_wind']:
      norm=math.sqrt(sum((a-b)**2 for a,b in zip(sensors[key],observed[key])));groupMax[key]=max(groupMax.get(key,0),norm)
     frames+=1;prev=frame;phase='SENT'
     if frames%20000==0:print(json.dumps({'progressFrames':frames,'elapsedSeconds':time.monotonic()-started,'sensorMismatch':mismatches['sensorUtf8']}),flush=True)
    elif kind==4:assert phase=='SENT';sent=json.loads(body);assert sent['returnedBytes']==sent['expectedBytes'];phase='RX'
    elif kind==6:assert phase=='RX';close+=1;assert json.loads(body)['intentAndSentFrames']==frames;phase='CLOSED'
    else:raise AssertionError('WAL_KIND')
 except Exception as e:stop=type(e).__name__+':'+str(e)
 after={n:sha(R/n)for n in before};unchanged=before==after and sha(MODEL)==modelSHA;complete=stop is None and frames==backend['frames']and phase=='CLOSED'and close==1 and unchanged;exact=complete and not any(mismatches.values())and not structural
 report={'format':'aeris-simstability03-original-model-byte-replay','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run':RUN,'status':'EXACT_ORIGINAL_MODEL_BYTES_PASS'if exact else 'EXACT_BYTES_NOT_ESTABLISHED','completeReplay':complete,'stopReason':stop,'framesCompared':frames,'expectedFrames':backend['frames'],'phaseAtEnd':phase,'closeRecords':close,'mismatchFrames':mismatches,'firstDifference':firstDiff,'maxNumericAbsoluteDriftByPath':dict(sorted(drift.items(),key=lambda q:q[1],reverse=True)),'maxVectorL2Drift':groupMax,'structuralOrNonNumericMismatch':dict(structural),'toleranceUsedForExactVerdict':None,'inputsUnchanged':unchanged,'inputSha256':before,'modelPath':str(MODEL),'modelSha256':modelSHA,'modelType':'IMMUTABLE_ORIGINAL_PURE_PYTHON_NO_NATIVE_KERNEL','scriptSha256':sha(pathlib.Path(__file__)),'elapsedSeconds':time.monotonic()-started,'scope':'SAME_CAPTURED_AP_PWM_OFFLINE_DETERMINISTIC_ORACLE_ONLY_NOT_HERA_CALIBRATION_OR_REALTIME_PERFORMANCE','priorFailedAP03':'NOT_REPLAYED_OR_PROMOTED'}
 with OUT.open('x')as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({'status':report['status'],'frames':frames,'mismatches':mismatches,'complete':complete,'elapsedSeconds':report['elapsedSeconds'],'out':str(OUT)}))
 if not exact:sys.exit(2)
if __name__=='__main__':main()
