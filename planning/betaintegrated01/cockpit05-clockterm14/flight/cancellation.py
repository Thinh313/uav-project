"""Strict CLOCKTERM14 causal cancellation audit. Raw rows stay byte-identical.
The CAS receipt describes a local dispatch-entry permit, never kernel/remote execution.
"""
import base64,hashlib,json,math,re,struct
from collections import OrderedDict
from .rx_group import RXAudit
from pilot.betaintegrated01.control01.mavlink import Framer
CTX={'run','epoch','boot','operator','generation','profileId'};TTL=200_000_000
NOTICE={'format','version','context','source','inputProvenance','viewEpoch','oldFence','newFence','releaseId','observedAtNs','permitSerialAtRelease','uiThreadId','touchRevision','releaseRevision','motionRawSHA256','motionContext','axes','pointers','foreground','focused','presentedFly'}
MOTION={'action','side','eventSource','deviceId','flags','eventUptimeMs','downUptimeMs','receiptElapsedNs','viewWidthPx','viewHeightPx'}
DETAIL={'format','version','context','phase','source','inputSequence','viewEpoch','oldFence','newFence','notices','dispatchPermitEntered','decisionNs'}
REF={'recordN','payloadSHA256','releaseId','oldFence','newFence','motionRecordN','motionPayloadSHA256'}
RAW={'source','kind','side','eventSource','deviceId','flags','action','eventUptimeMs','downUptimeMs','receiptElapsedNs','viewWidthPx','viewHeightPx','radiusPx','points','history'}
PHASES={'PRE_COMMIT','AUTHORITY_OR_PRE_SOCKET','DISPATCH_ENTRY'}
def fail(s):raise ValueError('CLOCKTERM14:'+s)
def need(v,s):
 if not v:fail(s)
def integer(v,minimum=0):need(type(v)is int and minimum<=v<2**63,'INTEGER');return v
def sha(v):return hashlib.sha256(v).hexdigest()
def digest(v):need(type(v)is str and re.fullmatch('[a-f0-9]{64}',v)is not None,'SHA');return v
def equal(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False)
def strict(raw):return __import__('importlib').import_module('planning.betaintegrated01.cockpit05-compact10.flight.native_chain').strict_json(raw)
def context(v,expected=None):
 need(type(v)is dict and set(v)==CTX and all(type(v[k])is str and 1<=len(v[k])<=128 for k in CTX),'CONTEXT')
 if expected is not None:need(all(v[k]==expected[k]for k in CTX),'FOREIGN_CONTEXT')
 return v
def schema(v,keys,fmt):need(type(v)is dict and set(v)==keys and v.get('format')==fmt and type(v.get('version'))is int and v['version']==1,'SCHEMA')
def exact_member_bytes(raw,name):
 """Extract the exact original JSON lexeme, preserving -0, exponent and escape spelling."""
 strict(raw);text=raw.decode('utf8');d=json.JSONDecoder();p=0
 def ws(i):
  while i<len(text)and text[i].isspace():i+=1
  return i
 p=ws(p);need(text[p]=='{','OBJECT');p=ws(p+1)
 while p<len(text)and text[p]!='}':
  key,end=d.raw_decode(text,p);need(type(key)is str,'OBJECT_KEY');p=ws(end);need(text[p]==':','OBJECT_COLON');start=ws(p+1);_,end=d.raw_decode(text,start)
  if key==name:return text[start:end].encode('utf8')
  p=ws(end)
  if text[p]==',':p=ws(p+1)
  else:break
 fail('OBJECT_MEMBER_MISSING')

def full_input(i,expected):
 from .transactions import input_schema
 input_schema(i,expected);return i

class ReleaseAudit:
 def __init__(self,expected=None):
  self.expectedView=None if expected is None else expected.get('expectedViewEpoch');self.viewEpoch=None;self.threadPair=None;self.latestNovelSequence=-1;self.latestUptime=-1;self.latestUI=-1;self.candidates=OrderedDict();self.acceptedPublicationChecks=0;self.acceptedFences={};self.context=None if expected is None else {k:expected[k]for k in CTX};self.provider=None;self.inputs=OrderedDict();self.motions=OrderedDict();self.notices=OrderedDict();self.pending=None;self.bindings=OrderedDict();self.lastWritten=None;self.permitSerial=0;self.lastFence=None;self.lastReleaseRevision=-1;self.lastTouch=-1;self.outcomes=OrderedDict();self.wireOutcomes={};self.handled=[];self.trusted=[];self.opened=False;self.closed=False;self.failed=False;self.failedTerminal=False;self.cleanupPending=False;self.cleanupCompletionNs=None;self.cleanupRevocationN=None;self.lastReleaseWritten=None;self.noticeProofs=[];self.cleanupMarkerNs=None;self.consentActions={};self.noticesSeen=0;self.cancelledSequences=set();self.revocations={};self.pendingAdmissionExpiry=None;self.expiryEpisodeActive=False;self.expiryCleanupEpisodes=[];self.cleanupOrigin=None;self.cleanupRX=RXAudit();self.cleanupParser=Framer();self.cleanupAPSequence=None;self.cleanupAPMode=-1;self.cleanupAPHBNs=-1;self.cleanupCRCActive=False;self.cleanupStage=0;self.brakeWrittenNs=-1;self.brakeObserved=False
 def input(self,i):
  full_input(i,self.context);seq=i['sequence'];o=i['inputObservation']
  need(self.provider is not None and i['source']==self.provider['source']and i['provenance']==self.provider['inputProvenance'],'INPUT_PROVIDER_SOURCE')
  need(self.expectedView is None or o['viewEpoch']==self.expectedView,'ROOT_UI_EPOCH')
  pair=(o['samplerThreadId'],o['uiThreadId']);need(self.viewEpoch is None or self.viewEpoch==o['viewEpoch'],'INPUT_VIEW_CHANGED');need(self.threadPair is None or self.threadPair==pair,'INPUT_THREADS_CHANGED');self.viewEpoch=o['viewEpoch'];self.threadPair=pair
  if seq not in self.inputs:
   need(seq>self.latestNovelSequence and i['uptimeNs']>=self.latestUptime and o['uiHeartbeatElapsedNs']>=self.latestUI,'INPUT_CLOCK_OR_SEQUENCE_REGRESSION');self.latestNovelSequence=seq;self.latestUptime=i['uptimeNs'];self.latestUI=o['uiHeartbeatElapsedNs']
  if seq in self.inputs:need(equal(self.inputs[seq],i),'INPUT_SEQUENCE_MUTATED')
  self.inputs[seq]=i
  while len(self.inputs)>64:self.inputs.popitem(last=False)
 def cleanup_packet(self,raw,now):
  parser=Framer();frames=parser.feed(raw,now);need(len(frames)==1 and not parser.pending,'CLEANUP_ONE_CRC_PACKET');f=frames[0];need((f['system'],f['component'])==(255,190),'CLEANUP_WRITER');p=f['payload'];ident=f['id']
  if ident in(0,20)or ident==76 and struct.unpack_from('<H',p,28)[0]in(511,512):return
  if ident==76 and struct.unpack_from('<H',p,28)[0]==176 and struct.unpack_from('<ff',p)==(1.0,17.0)and p[30:32]==bytes([42,1]):
   need(self.cleanupStage==0,'CLEANUP_DUPLICATE_BRAKE');self.cleanupStage=1;self.brakeWrittenNs=now;return
  if ident==70:
   need(self.brakeObserved and self.cleanupAPMode==17 and 0<=now-self.cleanupAPHBNs<=1_500_000_000,'CLEANUP_RC_REQUIRES_FRESH_CRC17')
   channels=list(struct.unpack_from('<8H',p))+list(struct.unpack_from('<10H',p,18));target=p[16:18]==bytes([42,1])
   if self.cleanupStage==1 and target and channels[:4]==[1500]*4 and channels[4:]==[65535]*14:self.cleanupStage=2;return
   if self.cleanupStage==2 and target and channels[:8]==[0]*8 and channels[8:]==[65534]*10:self.cleanupStage=3;return
  fail('CLEANUP_PACKET_SHAPE_OR_ORDER')
 def detail(self,v,i,now,phase=None):
  schema(v,DETAIL,'aeris-release12-cancellation');context(v['context'],self.context);full_input(i,self.context)
  need(v['phase']in PHASES and(phase is None or v['phase']in phase)and v['dispatchPermitEntered']is False,'CANCELLATION_PHASE')
  for k in('inputSequence','viewEpoch','oldFence','newFence','decisionNs'):integer(v[k])
  o=i['inputObservation'];at=v['decisionNs'];need(v['source']==i['source']and v['inputSequence']==i['sequence']and v['viewEpoch']==o['viewEpoch']and v['oldFence']==o['releaseFence']and v['oldFence']<v['newFence']and at<=now,'CANCELLATION_INPUT_CONTEXT')
  need(0<=at-i['elapsedNs']<=TTL and 0<=at-o['uiHeartbeatElapsedNs']<=TTL,'CANCELLATION_INPUT_UI_AGE')
  refs=v['notices'];need(type(refs)is list and 1<=len(refs)<=16 and len(refs)==v['newFence']-v['oldFence'],'NOTICE_CHAIN_LENGTH');fence=v['oldFence'];ids=[]
  for ref in refs:
   need(type(ref)is dict and set(ref)==REF,'NOTICE_REF_SCHEMA')
   for k in('recordN','motionRecordN'):integer(ref[k],1)
   for k in('oldFence','newFence'):integer(ref[k])
   digest(ref['payloadSHA256']);digest(ref['motionPayloadSHA256']);n=self.notices.get(ref['recordN']);need(n is not None,'MISSING_NOTICE_REF');notice=n['value'];m=n['motion']
   need(ref['payloadSHA256']==n['sha']and ref['motionRecordN']==m['record']and ref['motionPayloadSHA256']==m['sha']and ref['releaseId']==notice['releaseId']and ref['oldFence']==fence==notice['oldFence']and ref['newFence']==notice['newFence']==fence+1,'NOTICE_REF_BINDING')
   need(notice['source']==i['source']and notice['inputProvenance']==i['provenance']and notice['viewEpoch']==o['viewEpoch']and notice['uiThreadId']==o['uiThreadId']and notice['touchRevision']>o['touchRevision'],'NOTICE_INPUT_SOURCE_VIEW_THREAD_REVISION')
   need(o['uiHeartbeatElapsedNs']<=notice['motionContext']['receiptElapsedNs']<=notice['observedAtNs']<=at and at-notice['observedAtNs']<=TTL,'NOTICE_CAUSE_CLOCK')
   ids.append(notice['releaseId']);fence=notice['newFence']
  need(fence==v['newFence']and len(set(ids))==len(ids),'NOTICE_CHAIN_END');return ids
 def outcome(self,v,i,row,kind,phase):
  ids=self.detail(v,i,row['monotonicNs'],phase);key=(kind,row['n']);need(key not in self.outcomes,'DUPLICATE_OUTCOME');self.outcomes[key]=dict(detail=v,input=i,row=row,ids=ids,handled=False)
  need(i['sequence']not in self.cancelledSequences,'CANCELLED_INPUT_REPLAY');self.cancelledSequences.add(i['sequence']);need(len(self.outcomes)<=128,'UNHANDLED_OUTCOME_BOUND');return key
 def feed(self,row):
  need(not self.closed,'AFTER_TERMINAL');k=row['kind'];raw=base64.b64decode(row['base64'],validate=True);v=strict(raw)if k.startswith('CONTROL_')or k in('LIFECYCLE','TX_REFUSED','RC_NEUTRAL_AND_RELEASE_WRITTEN','BRAKE_HOLD_NO_RC_RELEASE_NEEDED','RC_RELEASE_NOT_NEEDED')else None;now=row['monotonicNs']
  received=self.cleanupRX.feed(row)
  if received is not None:
   for frame in self.cleanupParser.feed(received['raw'],received['receiptElapsedNs']):
    if(frame['system'],frame['component'])!=(42,1):continue
    delta=None if self.cleanupAPSequence is None else(frame['wireSequence']-self.cleanupAPSequence)&255
    if delta==0 or delta is not None and delta>=128:continue
    self.cleanupAPSequence=frame['wireSequence']
    if frame['id']==0:self.cleanupAPMode=struct.unpack_from('<I',frame['payload'])[0];self.cleanupAPHBNs=received['receiptElapsedNs']
  if k=='SAFETY_RELEASE_REQUESTED':
   safety=strict(raw);need(self.cleanupPending and not self.cleanupCRCActive and type(safety.get('cleanupPacketBudget'))is int and safety['cleanupPacketBudget']==3 and safety.get('requiresObservedBrake17BeforeNeutralRelease')is True,'SAFETY_RELEASE_CRC_PROTOCOL_START');self.cleanupCRCActive=True;self.cleanupStage=0;self.brakeWrittenNs=-1;self.brakeObserved=False
  if k=='SAFETY_BRAKE17_OBSERVED':
   brake=strict(raw);need(self.cleanupCRCActive and self.cleanupStage==1 and type(brake.get('mode'))is int and brake['mode']==17 and type(brake.get('atNs'))is int and brake['atNs']<=now and self.cleanupAPMode==17 and self.cleanupAPHBNs>=self.brakeWrittenNs and 0<=now-self.cleanupAPHBNs<=1_500_000_000,'BRAKE_MARKER_REQUIRES_FRESH_ORIGINAL_CRC17');self.brakeObserved=True
  if k=='TX_WRITTEN'and self.cleanupCRCActive:self.cleanup_packet(raw,now)
  receipt=v.get('priorCommitReceipt')if k in('CONTROL_INPUT_TX','CONTROL_CONSENT_TX')else(v.get('commitReceipt')if type(v)is dict else None)
  if type(receipt)is dict and receipt.get('disposition')=='ACCEPTED':
   candidate=self.candidates.get(receipt.get('txRecordN'))
   if candidate is not None:
    cr,ci=candidate;decision=receipt.get('decisionNs');integer(decision)
    for observed in self.notices.values():
     notice=observed['value'];definitelyBefore=observed['record']<cr or observed['rowNs']<decision or notice['observedAtNs']<decision
     if definitelyBefore and notice['newFence']>ci['inputObservation']['releaseFence']and notice['source']==ci['source']and notice['viewEpoch']==ci['inputObservation']['viewEpoch']:fail('ACCEPTED_OLD_FENCE_AFTER_PROVABLY_PUBLISHED_RELEASE')
    
    if receipt.get('operation')=='CONSENT':self.expiryEpisodeActive=False
    self.acceptedPublicationChecks+=1;fence=ci['inputObservation']['releaseFence'];prior=self.acceptedFences.get(fence)
    if prior is None or decision>=prior['decisionNs']:self.acceptedFences[fence]=dict(decisionNs=decision,candidateRecordN=cr,source=ci['source'],viewEpoch=ci['inputObservation']['viewEpoch'])
    need(len(self.acceptedFences)<=128,'ACCEPTED_FENCE_BOUND')
  if k=='LIFECYCLE'and v.get('kind')=='OPENED':
   need(not self.opened,'DUPLICATE_OPENED');ctx={x:v[x]for x in CTX};context(ctx,self.context);self.context=ctx;self.opened=True
  elif k=='CONTROL_PROVIDER':
   need(self.opened and self.provider is None,'PROVIDER_ORDER');need(all(v[x]==self.context[x]for x in('run','epoch','boot','generation')),'PROVIDER_CONTEXT');self.provider=v;epoch=v.get('selectedUIEpoch');integer(epoch,1);need(self.expectedView is None or epoch==self.expectedView,'PROVIDER_SELECTED_UI_EPOCH');self.expectedView=epoch
  elif k in('CONTROL_INPUT_TX','CONTROL_CONSENT_TX'):
   need(not any(not o['handled']for o in self.outcomes.values()),'CANDIDATE_BEFORE_CANCEL_HANDLED')
   if k=='CONTROL_CONSENT_TX':
    need(not self.cleanupPending,'CONSENT_BEFORE_RELEASE_CLEANUP');a=self.consentActions.get(v['proposal']['actionId']);need(a is not None,'CONSENT_ACTION_REQUIRED');done=a['releaseCompletedNs']
    if self.cleanupMarkerNs is None:need(done==-1,'FIRST_CONSENT_COMPLETION_MINUS1')
    else:need(done>=self.cleanupMarkerNs and a['producerElapsedNs']>done,'CONSENT_CLICK_BEFORE_ACTUAL_CLEANUP_COMPLETION');self.cleanupCompletionNs=done
   i=v['input']if k=='CONTROL_INPUT_TX'else v['neutralInput'];need(i['sequence']not in self.cancelledSequences,'CANDIDATE_AFTER_INPUT_CANCELLED');self.input(i);self.candidates[row['n']]=(row['n'],i)
   while len(self.candidates)>64:self.candidates.popitem(last=False)
  elif k=='CONTROL_RELEASE_MOTION':
   need(self.opened and self.provider is not None and type(v)is dict and set(v)==CTX|{'inputProvenance','releaseId','raw'},'MOTION_ENVELOPE_SCHEMA');context({x:v[x]for x in CTX},self.context);need(v['inputProvenance']==self.provider['inputProvenance'],'MOTION_PROVENANCE');m=v['raw'];need(type(m)is dict and set(m)==RAW and m.get('kind')=='ANDROID_MOTION_EVENT'and m.get('source')==self.provider['source'],'MOTION_SOURCE');
   need(type(m['radiusPx'])in(int,float)and math.isfinite(m['radiusPx'])and m['radiusPx']>0 and type(m['points'])is list and len(m['points'])<=2 and type(m['history'])is list and len(m['history'])<=32,'RAW_MOTION_BOUNDS')
   groups=[m['points']]
   for h in m['history']:
    need(type(h)is dict and set(h)=={'eventUptimeMs','points'}and type(h['eventUptimeMs'])is int and 0<=h['eventUptimeMs']<=m['eventUptimeMs']and type(h['points'])is list and len(h['points'])==len(m['points']),'RAW_MOTION_HISTORY');groups.append(h['points'])
   for points in groups:
    ids=[]
    for point in points:
     need(type(point)is dict and set(point)=={'id','xPx','yPx'}and type(point['id'])is int and point['id']>=0 and all(type(point[x])in(int,float)and math.isfinite(point[x])for x in('xPx','yPx')),'RAW_MOTION_POINT');ids.append(point['id'])
    need(len(ids)==len(set(ids)),'RAW_MOTION_POINTER_DUPLICATE')
   self.motions[v['releaseId']]=dict(value=v,raw=m,rawBytes=exact_member_bytes(raw,'raw'),record=row['n'],sha=sha(raw))
   while len(self.motions)>32:self.motions.popitem(last=False)
  elif k=='CONTROL_RELEASE_NOTICE':
   schema(v,NOTICE,'aeris-release12-notice');context(v['context'],self.context);need(self.provider is not None and v['source']==self.provider['source']and v['inputProvenance']==self.provider['inputProvenance'],'NOTICE_SOURCE')
   for x in('viewEpoch','oldFence','newFence','observedAtNs','permitSerialAtRelease','uiThreadId','touchRevision','releaseRevision','pointers'):integer(v[x])
   need(v['viewEpoch']>0 and v['uiThreadId']>0 and v['touchRevision']>self.lastTouch and v['releaseRevision']>self.lastReleaseRevision and v['newFence']==v['oldFence']+1 and v['oldFence']==(0 if self.lastFence is None else self.lastFence),'NOTICE_FENCE_REVISION')
   need(v['releaseId']==self.context['run']+':'+str(v['newFence'])and v['observedAtNs']<=now and v['permitSerialAtRelease']==self.permitSerial,'NOTICE_ID_CLOCK_PERMIT')
   need(v['foreground']is True and v['focused']is True and v['presentedFly']is True and v['pointers']==0 and type(v['axes'])is list and len(v['axes'])==4 and all(type(x)in(int,float)and math.isfinite(x)and x==0 for x in v['axes']),'NOTICE_LIVE_NEUTRAL')
   mc=v['motionContext'];need(type(mc)is dict and set(mc)==MOTION,'MOTION_CONTEXT_SCHEMA');need(type(mc['side'])is int and mc['side']in(0,1),'MOTION_SIDE')
   for x in MOTION-{'deviceId'}:integer(mc[x])
   need(type(mc['deviceId'])is int and -2**31<=mc['deviceId']<2**31,'MOTION_DEVICE');need(mc['action']in(1,3,6)and mc['eventSource']&4098==4098 and 0<=mc['downUptimeMs']<=mc['eventUptimeMs']<=mc['receiptElapsedNs']//1000000 and 0<=v['observedAtNs']-mc['receiptElapsedNs']<=TTL and mc['viewWidthPx']>0 and mc['viewHeightPx']>0,'MOTION_ACTION_CLOCK')
   digest(v['motionRawSHA256']);m=self.motions.get(v['releaseId']);need(m is not None and m['record']<row['n']and sha(m['rawBytes'])==v['motionRawSHA256']and all(equal(m['raw'].get(x),mc[x])for x in MOTION),'EXACT_DURABLE_RAW_MOTION_BINDING')
   for oldFence,accepted in self.acceptedFences.items():
    knownBefore=v['observedAtNs']<accepted['decisionNs']or row['n']<accepted['candidateRecordN']or now<accepted['decisionNs']
    if oldFence<v['newFence']and knownBefore and accepted['source']==v['source']and accepted['viewEpoch']==v['viewEpoch']:fail('DELAYED_RELEASE_PROVES_OLD_FENCE_ACCEPTED_AFTER_PUBLICATION')
   self.notices[row['n']]=dict(value=v,motion=m,sha=sha(raw),record=row['n'],rowNs=now);self.noticesSeen+=1;self.noticeProofs.append(dict(record=row['n'],releaseId=v['releaseId'],oldFence=v['oldFence'],newFence=v['newFence'],source=v['source'],viewEpoch=v['viewEpoch'],motionRecordN=m['record'],observedAtNs=v['observedAtNs']));need(len(self.noticeProofs)<=64,'NOTICE_CASE_BOUND');self.lastFence=v['newFence'];self.lastTouch=v['touchRevision'];self.lastReleaseRevision=v['releaseRevision']
   while len(self.notices)>32:self.notices.popitem(last=False)
  elif k=='CONTROL_INPUT_CANCELLED_BEFORE_COMMIT':
   need(type(v)is dict and set(v)in({'input','expectedCancellation','atNs'},{'input','expectedCancellation','atNs','commitReceipt'}),'PRECOMMIT_SCHEMA');integer(v['atNs']);need(v['atNs']<=now,'PRECOMMIT_CLOCK');self.input(v['input']);self.outcome(v['expectedCancellation'],v['input'],row,'PRE_COMMIT',{'PRE_COMMIT','AUTHORITY_OR_PRE_SOCKET'})
  elif k=='CONTROL_COMMIT_CANCELLED':
   need(type(v)is dict and set(v)=={'reason','atNs','noAutomaticRegrant','commitReceipt'}and v['reason']=='EXPECTED_RELEASE_CANCELLATION'and v['noAutomaticRegrant']is True,'COMMIT_CANCELLED_CARRIER');r=v['commitReceipt'];detail=r['expectedCancellation'];i=self.inputs.get(detail['inputSequence']);need(i is not None,'COMMIT_CANCELLED_INPUT');self.outcome(detail,i,row,'COMMIT',{'AUTHORITY_OR_PRE_SOCKET'})
  elif k=='CONTROL_INPUT_ADMISSION_REJECTED':
   from .input_admission import FIELDS as ADMISSION_FIELDS
   need(type(v)is dict and set(v)in(ADMISSION_FIELDS,ADMISSION_FIELDS|{'commitReceipt'})and v['fullInvalidInputRetained']is True and v['phase']=='PRE_CANDIDATE'and v['authorityRestorable']is False,'ADMISSION_ENVELOPE_REQUIRED')
   if v['disposition']=='EXPIRED_NO_AUTHORITY':
    need(v['reasonClass']=='AdmissionExpiry'and v['reason']in('INPUT_SAMPLE_EXPIRED','UI_OBSERVATION_EXPIRED','PRIOR_LEASE_EXPIRED_BEFORE_CANCEL_CHECK'),'TYPED_ADMISSION_EXPIRY_CAUSE')
    need(self.pendingAdmissionExpiry is None,'ADMISSION_EXPIRY_REVOKE_MISSING');self.pendingAdmissionExpiry=(row,v)
  elif k=='CONTROL_REVOKED'and v.get('reason')=='INPUT_ADMISSION_EXPIRED':
   need(self.pendingAdmissionExpiry is not None,'ADMISSION_EXPIRY_WITHOUT_RETAINED_CAUSE');rejected,detail=self.pendingAdmissionExpiry
   need(rejected['n']<row['n']and detail['atNs']<=v['atNs']<=now and v['previousLeaseId']==detail['priorLeaseId']and v['authorityRestorable']is False,'ADMISSION_EXPIRY_REVOKE_BINDING');self.pendingAdmissionExpiry=None
   if not self.expiryEpisodeActive:
    need(not self.cleanupPending,'EXPIRY_REVOKE_DURING_UNRESOLVED_TOUCH_CLEANUP');self.cleanupPending=True;self.cleanupOrigin='ADMISSION_EXPIRY';self.cleanupRevocationN=row['n'];self.cleanupCompletionNs=None;self.expiryEpisodeActive=True;self.expiryCleanupEpisodes.append(dict(rejectionRecordN=rejected['n'],revokeRecordN=row['n'],inputSequence=detail['sequence'],reason=detail['reason'],fullSemanticsRequireTransactionResolver=True))
    need(len(self.expiryCleanupEpisodes)<=64,'EXPIRY_EPISODE_BOUND')
  elif k=='CONTROL_REVOKED'and v.get('reason')in('UI_LIVENESS_EXPIRED','INPUT_LEASE_EXPIRED'):
   need(v.get('previouslyActive')is True and type(v.get('previousLeaseId'))is str and type(v.get('atNs'))is int and v['atNs']<=now,'TICK_EXPIRY_REVOKE_ENVELOPE')
   if not self.expiryEpisodeActive:
    need(not self.cleanupPending,'TICK_EXPIRY_DURING_UNRESOLVED_TOUCH_CLEANUP');self.cleanupPending=True;self.cleanupOrigin='TICK_EXPIRY';self.cleanupRevocationN=row['n'];self.cleanupCompletionNs=None;self.expiryEpisodeActive=True;self.expiryCleanupEpisodes.append(dict(revokeRecordN=row['n'],reason=v['reason'],fullSemanticsRequireTransactionResolver=True));need(len(self.expiryCleanupEpisodes)<=64,'EXPIRY_EPISODE_BOUND')
  elif k=='CONTROL_INPUT_WIRE_BINDING':
   need(v['inputSequence']in self.inputs,'BINDING_INPUT_REQUIRED');i=self.inputs[v['inputSequence']]
   if self.lastFence is not None:need(i['inputObservation']['releaseFence']>=self.lastFence,'OLD_FENCE_BINDING_AFTER_DURABLE_RELEASE')
   self.bindings[v['wireSHA256']]=i
   while len(self.bindings)>64:self.bindings.popitem(last=False)
  elif k=='TX_INTENT':need(not any(not o['handled']for o in self.outcomes.values()),'WIRE_BEFORE_CANCEL_HANDLED');need(self.pending is None,'OVERLAPPING_INTENT');self.pending=(row,raw)
  elif k=='TX_WRITTEN':
   need(self.pending is not None and self.pending[1]==raw,'WRITTEN_INTENT');self.lastWritten=(row,raw);self.pending=None
   if len(raw)>=50 and raw[0]==253 and int.from_bytes(raw[7:10],'little')==70:
    padded=raw[10:-2]+bytes(38-len(raw[10:-2]));channels=list(struct.unpack_from('<8H',padded))+list(struct.unpack_from('<10H',padded,18))
    if channels[:8]==[0]*8 and channels[8:]==[65534]*10 and padded[16:18]==bytes([42,1]):self.lastReleaseWritten=row
  elif k=='TX_UNKNOWN':self.pending=None
  elif k=='TX_REFUSED':
   if 'expectedCancellation'in v:
    need(self.pending is not None,'CANCEL_INTENT_REQUIRED');ir,wire=self.pending;need(set(v)=={'wireSHA256','intentRecordN','reasonClass','reason','disposition','socketCallbackEntered','run','epoch','expectedCancellation'}and type(v['intentRecordN'])is int and v['intentRecordN']==ir['n']and v['wireSHA256']==sha(wire)and v['run']==self.context['run']and v['epoch']==self.context['epoch']and v['reasonClass']=='Cancel'and v['reason']=='EXPECTED_RELEASE_CANCELLATION'and v['disposition']=='PRE_SOCKET_REFUSED'and v['socketCallbackEntered']is False,'EXPECTED_WIRE_CANCEL_SCHEMA_PHASE')
    detail=v['expectedCancellation'];i=self.bindings.get(v['wireSHA256']);need(i is not None,'EXPECTED_CANCEL_PILOT_BINDING_REQUIRED');self.outcome(detail,i,row,'WIRE',{'AUTHORITY_OR_PRE_SOCKET','DISPATCH_ENTRY'});self.wireOutcomes[row['n']]=dict(intentRecordN=ir['n'],wireSHA256=sha(wire),detail=detail)
   self.pending=None
  elif k=='CONTROL_LOCAL_SEND_RETURNED':
   need(type(v)is dict and set(v)in({'inputSequence','dispatchPermit','atNs','executionAccepted'},{'inputSequence','dispatchPermit','atNs','executionAccepted','commitReceipt'})and v['executionAccepted']is False,'PERMIT_SCHEMA');p=v['dispatchPermit'];need(type(p)is dict and set(p)=={'serial','releaseFence','claimObservedNs','meaning'}and p['meaning']=='LOCAL_DISPATCH_ENTRY_PERMIT_NOT_KERNEL_OR_REMOTE_ATTESTATION','PERMIT_MEANING')
   for x in('serial','releaseFence','claimObservedNs'):integer(p[x])
   integer(v['inputSequence']);integer(v['atNs']);i=self.inputs.get(v['inputSequence']);need(i is not None and p['serial']==self.permitSerial+1 and p['releaseFence']==i['inputObservation']['releaseFence']and self.lastWritten is not None and self.bindings.get(sha(self.lastWritten[1]))is i and p['claimObservedNs']<=self.lastWritten[0]['monotonicNs']<=v['atNs']<=now,'PERMIT_WIRE_ORDER');need(0<=p['claimObservedNs']-i['elapsedNs']<=TTL and 0<=p['claimObservedNs']-i['inputObservation']['uiHeartbeatElapsedNs']<=TTL,'PERMIT_INPUT_UI_AGE');self.permitSerial=p['serial']
  elif k=='CONTROL_EXPECTED_INPUT_CANCELLED':
   need(type(v)is dict and set(v)=={'expectedCancellation','causePhase','intentRecordN','outcomeRecordN','wireSHA256','atNs','userAuthorityRestored'}and v['userAuthorityRestored']is False,'HANDLED_SCHEMA');need(v['causePhase']==v['expectedCancellation']['phase']and type(v['atNs'])is int and v['atNs']<=now,'HANDLED_CLOCK')
   hits=[(key,o)for key,o in self.outcomes.items()if not o['handled']and equal(o['detail'],v['expectedCancellation'])];need(len(hits)==1,'HANDLED_OUTCOME_UNIQUE');key,o=hits[0]
   if key[0]=='WIRE':need(type(v['intentRecordN'])is int and type(v['outcomeRecordN'])is int and v['intentRecordN']==self.wireOutcomes[key[1]]['intentRecordN']and v['outcomeRecordN']==key[1]and v['wireSHA256']==self.wireOutcomes[key[1]]['wireSHA256'],'HANDLED_WIRE_BINDING')
   else:need(type(v['intentRecordN'])is int and v['intentRecordN']==-1 and type(v['outcomeRecordN'])is int and v['outcomeRecordN']==-1 and v['wireSHA256']is None,'HANDLED_NONWIRE_BINDING')
   need(v['expectedCancellation']['newFence']in self.revocations and self.revocations[v['expectedCancellation']['newFence']]['record']<row['n'],'EXPECTED_CANCEL_REVOKE_REQUIRED');o['handled']=True;self.handled.append(dict(record=row['n'],outcomeRecord=key[1],phase=v['causePhase'],releaseIds=o['ids'],inputSequence=o['input']['sequence']));self.cancelledSequences.add(o['input']['sequence']);need(len(self.handled)<=64,'CANCELLED_EPISODE_BOUND')
  elif k=='CONTROL_REVOKED'and v.get('reason')in('TRUSTED_TOUCH_RELEASE','EXPECTED_RELEASE_CANCELLATION'):
   cause=v.get('releaseCause');need(type(cause)is dict,'EXPLICIT_RELEASE_CAUSE_REQUIRED')
   if v['reason']=='TRUSTED_TOUCH_RELEASE':
    need(set(cause)==REF,'TRUSTED_RELEASE_REF_SCHEMA');n=self.notices.get(cause['recordN']);need(n is not None,'TRUSTED_RELEASE_REF_MISSING');m=n['motion'];notice=n['value']
    need(all(type(cause[x])is int for x in('recordN','oldFence','newFence','motionRecordN'))and cause['payloadSHA256']==n['sha']and cause['releaseId']==notice['releaseId']and cause['oldFence']==notice['oldFence']and cause['newFence']==notice['newFence']and cause['motionRecordN']==m['record']and cause['motionPayloadSHA256']==m['sha'],'TRUSTED_RELEASE_CAUSE_BINDING')
   else:
    i=self.inputs.get(cause.get('inputSequence'));need(i is not None,'EXPECTED_REVOKE_INPUT');self.detail(cause,i,now);n=self.notices[cause['notices'][-1]['recordN']]
   integer(v['atNs']);need(n['record']<row['n']and n['value']['observedAtNs']<=v['atNs']<=now,'TRUSTED_RELEASE_ORDER');self.cleanupPending=True;self.cleanupOrigin='TOUCH_RELEASE';self.cleanupCompletionNs=None;self.cleanupRevocationN=row['n'];proof=dict(record=row['n'],releaseId=n['value']['releaseId'],noticeRecordN=n['record'],newFence=n['value']['newFence'],reason=v['reason']);self.revocations[n['value']['newFence']]=proof
   if v['reason']=='TRUSTED_TOUCH_RELEASE':self.trusted.append(proof)
   need(len(self.trusted)<=64,'TRUSTED_RELEASE_BOUND')
  elif k in('RC_NEUTRAL_AND_RELEASE_WRITTEN','BRAKE_HOLD_NO_RC_RELEASE_NEEDED','RC_RELEASE_NOT_NEEDED'):
   need(self.cleanupPending,'CLEANUP_WITHOUT_CAUSAL_RELEASE');integer(v.get('atNs',now));completion=v.get('atNs',now);need(completion<=now,'CLEANUP_COMPLETION_CLOCK')
   if k=='RC_NEUTRAL_AND_RELEASE_WRITTEN':need(self.lastReleaseWritten is not None and self.cleanupRevocationN<self.lastReleaseWritten['n']and self.lastReleaseWritten['monotonicNs']<=completion and v.get('neutralAndReleaseWritten')is True and type(v.get('cleanupPacketsWritten'))is int and v['cleanupPacketsWritten']==3 and v.get('localWriteOnly')is True and v.get('userAuthorityRestored')is False,'ACTUAL_RELEASE_WRITTEN_BEFORE_CLEANUP')
   if k!='RC_RELEASE_NOT_NEEDED':need(self.cleanupCRCActive and self.brakeObserved and self.cleanupStage==(3 if k=='RC_NEUTRAL_AND_RELEASE_WRITTEN'else 1),'CLEANUP_CRC_SEQUENCE_INCOMPLETE')
   else:need(not self.cleanupCRCActive,'GROUND_CLEANUP_DURING_AIRBORNE_SEQUENCE')
   self.cleanupCRCActive=False;self.cleanupPending=False;self.cleanupMarkerNs=now;self.cleanupCompletionNs=completion
  elif k=='OPERATOR_TOUCH_ACTION':
   action=strict(raw)
   if action.get('action')=='CONSENT':
    need(type(action)is dict and set(action)=={'action','actionId','producerElapsedNs','receiptElapsedNs','displayedHomeHash','source','releaseCompletedNs'}and action['source']=='ANDROID_BUTTON_CLICK_NOT_NETWORK_RETIMESTAMPED'and type(action['releaseCompletedNs'])is int and action['releaseCompletedNs']>=-1,'CONSENT_COMPLETION_FIELD_SCHEMA')
    integer(action['producerElapsedNs']);integer(action['receiptElapsedNs']);need(action['producerElapsedNs']<=action['receiptElapsedNs']<=now and action['releaseCompletedNs']<=action['receiptElapsedNs'],'CONSENT_ACTION_CLOCK');need(action['actionId']not in self.consentActions and len(self.consentActions)<256,'CONSENT_ACTION_UNIQUE');self.consentActions[action['actionId']]=action
  elif k=='CONTROL_FAILURE':self.failed=True
  elif k=='SESSION_CLOSE':
   close=strict(raw);self.failedTerminal=close.get('reason')=='CONTROL_FAILED_RESOURCES_CLOSED';self.closed=True
 def finish(self):
  self.cleanupRX.finish();need(not self.cleanupCRCActive or self.failed and self.failedTerminal,'INCOMPLETE_CRC_CLEANUP_WITHOUT_FAILED_TERMINAL');need(self.pendingAdmissionExpiry is None,'ADMISSION_EXPIRY_REVOKE_MISSING');incomplete=[key[1]for key,o in self.outcomes.items()if not o['handled']];need(not incomplete or self.failed and self.failedTerminal,'UNHANDLED_EXPECTED_CANCEL_OUTCOME');return dict(incompleteExpectedEpisodes=incomplete,forensicOnly=bool(incomplete),format='aeris-release12-causal-cancellation-audit',notices=self.noticesSeen,noticeProofs=self.noticeProofs,causalReleases=list(self.revocations.values()),expiryCleanupEpisodes=self.expiryCleanupEpisodes,expirySemanticsRequireMandatoryTransactionResolver=True,cleanupCompletionNs=self.cleanupCompletionNs,cleanupMarkerNs=self.cleanupMarkerNs,expectedCancellations=self.handled,expectedWireOutcomes=list(self.wireOutcomes),trustedTouchReleases=self.trusted,dispatchPermits=self.permitSerial,acceptedPublicationChecks=self.acceptedPublicationChecks,releasePublicationOrder='OBSERVED_AT_FIRST_POST_CAS_OBSERVATION_UPPER_BOUND_ONLY_STRICT_LESS_THAN_DECISION_EQUALITY_AMBIGUOUS_NOT_CAS_INSTANT',sourceBoundLocalDispatchEntryOnly=True,rawRewritten=False)
 def wrap(self,rows,summary=None):
  for row in rows:self.feed(row);yield row
  v=self.finish()
  if summary is not None:summary.update(v)
