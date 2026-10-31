"""Read-only independent prefix audit. NEVER promotes the failed actual01 run."""
from pathlib import Path
import base64,collections,datetime,hashlib,json,struct,sys,zlib
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.runtime.physics_reference import Model
from pilot.betaintegrated01.runtime.physics import profile
from pilot.betaintegrated01.runtime.ap_stage import EVENT,verify_stage
from pilot.betaintegrated01.journal import verify_journal
O=R/'evidence/betaintegrated01-m1runtime/actual01';D=O/'raw';C=O/'control'
cfg=json.loads((D/'run-config.json').read_text());run,epoch,boot=(cfg[k]for k in ['run','epoch','boot']);errors=[];canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def check(b,s):
 if not b:raise AssertionError(s)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
try:default=verify_journal(D/'journal',run,epoch)
except Exception as e:default={'state':'REJECTED_METADATA_OR_FORMAT','reason':type(e).__name__+':'+str(e)}
model=Model(profile(cfg['load'],cfg['wind'],cfg['seed']));head='0'*64;previous_file='0'*64;seq=frame=stages=0;phase='BETWEEN';intent=None;segments=[];kinds=collections.Counter();model_mismatches=[]
for ordinal,p in enumerate(sorted((D/'journal').glob('segment-*.jsonl'))):
 h=hashlib.sha256();first=seq;count=0
 with p.open('rb')as stream:
  for line in stream:
   check(line.endswith(b'\n'),'partial row');h.update(line);row=json.loads(line);b=row['body'];raw=canonical(b)
   check(b['v']==1 and b['run']==run and b['epoch']==epoch and b['segment']==ordinal and b['seq']==seq and b['previous']==head,'record context/sequence')
   check(row['crc32']==format(zlib.crc32(raw),'08x')and row['sha256']==hashlib.sha256(bytes.fromhex(head)+raw).hexdigest(),'record CRC/SHA')
   kind,pay=b['kind'],b['payload'];kinds[kind]+=1
   if count==0:check(kind=='SEGMENT'and pay=={'ordinal':ordinal,'startSequence':seq,'previousSegmentSHA256':previous_file},'segment header')
   elif kind=='RX':
    check(phase=='BETWEEN'and b['frame']==frame,'RXorder');servo=base64.b64decode(pay['base64'],validate=True);magic,rate,num,*pwm=struct.unpack('<HHI16H',servo);check(magic==18458 and rate==1200 and num==frame,'servo')
    expected=('\n'+json.dumps(model.step(pwm,1/1200),separators=(',',':'),allow_nan=False)+'\n').encode();phase='RX'
   elif kind=='INTENT':
    check(phase=='RX'and b['frame']==frame,'INTENTorder');intent=base64.b64decode(pay['base64'],validate=True)
    if intent!=expected:model_mismatches.append(frame)
    phase='INTENT'
   elif kind=='SENT':
    check(phase=='INTENT'and b['frame']==frame,'SENTorder');check(pay['returnedBytes']==pay['expectedBytes']==len(intent),'local sendlength');frame+=1;phase='BETWEEN'
   elif kind=='UNKNOWN':phase='UNKNOWN'
   elif kind=='EVENT'and pay['eventKind']=='STAGE':check(pay['data']['frame']==stages,'stageframe');stages+=1
   head=row['sha256'];seq+=1;count+=1
 file_sha=h.hexdigest();seal=p.with_name(p.name.replace('.jsonl','.seal.json'));sealed=seal.is_file()
 if sealed:
  s=json.loads(seal.read_text());check(s['fileBytes']==p.stat().st_size and s['fileSHA256']==file_sha and s['head']==head and s['startSequence']==first and s['endSequence']==seq-1 and s['previousSegmentSHA256']==previous_file,'segment seal')
 segments.append({'path':str(p.relative_to(R)),'records':count,'sealed':sealed,'sha256':file_sha});previous_file=file_sha
parent_channel=[json.loads(line)for line in(C/'container-control-stdout.txt').read_text().splitlines()if line.startswith('{')][-1]
ap=verify_stage(D/'ap-stage',run,epoch,boot,terminal_sha256=parent_channel['terminalSHA256'])
coverage=0;current=None;group=[];last_group=None
def close_group(f,g):
 global coverage,last_group
 if f<frame:
  check(f==coverage and g in ([10,11,12,13,14,20,21,24],[10,11,12,13,14,20,21,22,23,24]),'APgroup');coverage+=1
 else:last_group={'frame':f,'kinds':g}
for p in sorted((D/'ap-stage').glob('stage-*.bin')):
 with p.open('rb')as stream:
  stream.readline(4097)
  while True:
   row=stream.read(EVENT.size)
   if not row:break
   _,f,k,*_=EVENT.unpack(row)
   if current is not None and f!=current:close_group(current,group);group=[]
   current=f;group.append(k)
if current is not None:close_group(current,group)
check(coverage==frame,'AP/host prefix coverage')
check(not model_mismatches,'pure model bytes mismatch')
state_rows=[json.loads(line)for line in(C/'native-live-states.jsonl').read_text().splitlines()];native_errors=collections.Counter(r['state'].get('error','')for r in state_rows)
inputs=json.loads((C/'input-pins.json').read_text())['files'];drift=[p for p,h in inputs.items()if sha(R/p)!=h]
guard_rows=[json.loads(line)for line in(C/'guard.jsonl').read_text().splitlines()]
failure=D/'journal/failure.json'
result={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FAILED_RUN_VALID_EXACT_RETAINED_PREFIX_ONLY','actualRunStatus':'FAILED_NOT_ACCEPTED','defaultColdResult':default,'host':{'records':seq,'completedFrames':frame,'stageRows':stages,'phaseAtEnd':phase,'modelExactBytesFrames':frame,'modelMismatchFrames':model_mismatches,'segments':segments,'sessionManifestPresent':(D/'journal/session.json').exists(),'failureMarkerBytes':failure.stat().st_size if failure.exists()else None,'recordKinds':dict(kinds)},'AP':{'cold':ap,'externalAnchorSource':'Root-owned parent controlstdout outside AP rawtree','coveredCompletedHostFrames':coverage,'lastUnadmittedGroup':last_group},'native':{'checkpointRows':len(state_rows),'errors':dict(native_errors),'connectedSocketOrTelemetryProven':False},'rootGuard':{'samples':len(guard_rows),'lastFreeBytes':guard_rows[-1]['freeBytes'],'lastForecastBytes':guard_rows[-1]['forecastFreeBytes']},'inputPinDrift':drift,'bugAssessment':{'diskSamplingCodeConfirmed':'deque64sampleatper-recordcadence means <15swindow underload; exactfailing64samples notretained so actualmicroburstwindow/rateunknown','foregroundOrdering':'Checkpointrefusal and source immediateonNewIntentaction beforeonResume consistent; controllerflag is intentattempt only'},'APAndroidRuntimeLaunchesByQA':0,'publicationAllowed':False,'APExecutionAccepted':False,'M1Ready':False,'BetaReady':False,'allOldRawUntouched':True}
Path(R/'evidence/betaintegrated01-m1runtime/qa/actual01-prefix-audit.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'hostFrames':frame,'stages':stages,'APcovered':coverage,'APEvents':ap['events'],'pinDrift':drift,'nativeStates':len(state_rows)}))
