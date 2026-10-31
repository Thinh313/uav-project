from pathlib import Path
import base64,collections,datetime,hashlib,json,struct,sys
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.runtime02.journal import verify_journal
from pilot.betaintegrated01.runtime.physics_reference import Model
from pilot.betaintegrated01.runtime.physics import profile
from pilot.betaintegrated01.control01.mavlink import Framer
from pilot.betaintegrated01.control01.oracles03 import events,critical_fields,native_fields,control_outcome
B=R/'evidence/betaintegrated01-m1control01/actual-loss03';O=R/'evidence/betaintegrated01-m1control01/qa/actual-loss03';c=json.loads((B/'raw/run-config.json').read_bytes());run,epoch=c['run'],c['epoch']
host=verify_journal(B/'raw/journal',run,epoch);transport=verify_journal(B/'raw/transport-journal',run,epoch)
model=Model(profile(c['load'],c['wind'],c['seed']));count=0;phase='RX';stages=0;sensor=None
for p in sorted((B/'raw/journal').glob('segment-*.jsonl')):
 for line in p.open('rb'):
  v=json.loads(line)['body'];kind,payload=v['kind'],v['payload']
  if kind=='RX':
   assert phase=='RX'and v['frame']==count
   wire=base64.b64decode(payload['base64']);magic,rate,frame,*pwm=struct.unpack('<HHI16H',wire);assert magic==18458 and rate==1200 and frame==count
   sensor=('\n'+json.dumps(model.step(pwm,1/rate),separators=(',',':'),allow_nan=False)+'\n').encode();phase='INTENT'
  if kind=='INTENT':assert phase=='INTENT'and base64.b64decode(payload['base64'])==sensor;phase='SENT'
  if kind=='SENT':assert phase=='SENT';count+=1;phase='RX'
  if kind=='EVENT'and payload['eventKind']=='STAGE':stages+=1
passive,native=Framer(),Framer();timeline=[];commands=[];decoded=collections.deque();sequence=None;intent=None;cut=None
for kind,data in events(B/'raw/transport-journal'):
 if kind=='PASSIVE_RX':decoded.extend(passive.feed(bytes.fromhex(data['rawHex']),data['hostNs']))
 if kind=='PASSIVE_FRAME':
  f=decoded.popleft();assert f['wireHex']==data['wireHex'];delta=1 if sequence is None else(f['wireSequence']-sequence)&255
  if f['system']==42 and f['component']==1 and 0<delta<128:
   sequence=f['wireSequence'];v=critical_fields(f)
   if v:timeline.append({'hostNs':f['monotonicNs'],**v})
 if kind=='FORWARD_INTENT':intent=(data['direction'],bytes.fromhex(data['rawHex']))
 if kind in('FORWARD_LOCAL_RETURN','FORWARD_NOT_READY'):
  assert intent is not None and intent[0]==data['direction'];direction,raw=intent;n=data['sentBytes'];assert 0<=n<=len(raw)
  if direction=='toAP':
   for f in native.feed(raw[:n],data['_observedHostNs']):
    v=native_fields(f)
    if v:commands.append({'hostNs':data['_observedHostNs'],**v})
  intent=None
 if kind=='CUT_CONNECTIONS_CLOSED':cut=data['closedHostNs']
unlogged_decoded=len(decoded) # A quota failure may occur after raw RX, before its FRAME metadata.
audit={'passiveTimeline':timeline,'nativeForwardedTimeline':commands,'cutClosedHostNs':cut,'passiveApplicationTXBytes':0};outcome=control_outcome(audit,'loss')
r={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FAILED_QUOTA_RETAINED_PREFIX_PARTIAL_FLIGHT_ONLY','hostPrefix':host,'transportPrefix':transport,'modelPrefix':{'exactPureModelCompletedFrames':count,'stageRows':stages,'lastPhase':phase,'completeAnchoredRecording':False},'unloggedDecodedPassiveFramesAtQuota':unlogged_decoded,'unresolvedForwardIntentAtQuota':intent is not None,'partialFlightOutcome':outcome,'lastObservedHeartbeat':next((x for x in reversed(timeline)if x['kind']=='heartbeat'),None),'lastObservedPosition':next((x for x in reversed(timeline)if x['kind']=='position'),None),'lastObservedLandedState':next((x for x in reversed(timeline)if x['kind']=='landed'),None),'timelinesDerivedFromFailedPrefix':True,'passiveTimeline':timeline,'nativeTimeline':commands,'noCompleteCaptureOrGroundAcceptance':True}
(O/'host-prefix01.json').open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'frames':count,'stages':stages,'host':host['state'],'transport':transport['state'],'partialCriteria':outcome['criteria'],'lastHB':r['lastObservedHeartbeat']}))
