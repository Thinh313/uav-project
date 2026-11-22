"""09-only audit projection from immutable candidate+delayed durable receipts.

Never serialized as native raw. Original chain/seal verification precedes this
pass. Actual decision clock is the logical authority boundary, not row entry.
"""
import base64,hashlib,json,math,re
from .native_chain import strict_json
TTL=200_000_000
CTX={'run','epoch','boot','operator','generation','profileId'}
PROVENANCE='SOURCE_BOUND_DELAYED_COMMIT_RECEIPT'
def fail(why):raise ValueError('COMMIT09:'+why)
def integer(x,minimum=0):
 if type(x)is not int or x<minimum:fail('INTEGER_DOMAIN')
 return x
def same(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False)
def payload(row):return strict_json(base64.b64decode(row['base64'],validate=True))
def context(v,expected):
 if type(v)is not dict or set(v)!=CTX or any(type(v[k])is not str or not 1<=len(v[k])<=128 for k in CTX):fail('CONTEXT_SCHEMA')
 if expected is not None and any(v[k]!=expected[k]for k in CTX):fail('CONTEXT_MISMATCH')

def input_schema(i,ctx):
 keys=CTX|{'source','clockDomain','provenance','sequence','uptimeNs','elapsedNs','lastMotionUptimeNs','axes','pointers','motionAction','release','inputObservation'}
 if type(i)is not dict or set(i)!=keys or any(i[k]!=ctx[k]for k in CTX):fail('INPUT_SCHEMA_CONTEXT')
 for k in('sequence','uptimeNs','elapsedNs','lastMotionUptimeNs'):integer(i[k])
 if type(i['source'])is not str or not i['source']or i['clockDomain']!='ANDROID_UPTIME_NS_SAMPLER'or i['provenance']not in('ROOT_INJECTED_ANDROID_TOUCH','LOCAL_ANDROID_TOUCH_NOT_HID_ATTESTED'):fail('INPUT_SOURCE_CLOCK')
 if not i['lastMotionUptimeNs']<=i['uptimeNs']<=i['elapsedNs']or type(i['pointers'])is not int or not 0<=i['pointers']<=2 or type(i['motionAction'])is not int or i['motionAction']not in(-1,0,1,2,3,5,6)or type(i['release'])is not bool:fail('INPUT_TYPES_CLOCK_MOTION')
 if type(i['axes'])is not list or len(i['axes'])!=4 or any(type(x)not in(int,float)or not math.isfinite(x)or not -1<=x<=1 for x in i['axes']):fail('INPUT_AXES')
 o=i['inputObservation'];keys={'kind','uiHeartbeatElapsedNs','touchRevision','samplerThreadId','uiThreadId','viewEpoch','releaseFence'}
 if type(o)is not dict or set(o)!=keys or o['kind']!='IMMUTABLE_UI_TOUCH_STATE_SAMPLE_NOT_NEW_MOTION_EVENT':fail('INPUT_OBSERVATION_SCHEMA')
 for k in keys-{'kind'}:integer(o[k])
 if o['uiHeartbeatElapsedNs']>i['elapsedNs']or o['samplerThreadId']<=0 or o['uiThreadId']<=0 or o['samplerThreadId']==o['uiThreadId']or o['viewEpoch']<=0:fail('INPUT_OBSERVATION_CONTEXT_CLOCK')

def resolve_rows(rows,expected=None,summary=None):
 from .cancellation import ReleaseAudit
 from .rx_group import RXAudit
 rxProof={};rows=RXAudit().wrap(rows,rxProof)
 releaseProof={};releaseState=ReleaseAudit(expected);rows=releaseState.wrap(rows,releaseProof)
 cancelled=0
 pending=None;buffer=[];lease=None;expiry=-1;latest=None;lastDecision=-1;lastSequence=-1;logical=0;accepted=refused=candidates=0;maxBarrier=0;grants=0;failed=False;failureSeen=False;openedSeen=False;providerSource=None;providerProvenance=None;lastRejected=-1;admissionPending=None;admissionRejected=0;admissionExpired=0;admissionFatal=False
 def derive(raw,kind,value,decision,proof):
  return {**raw,'kind':kind,'monotonicNs':decision,'base64':base64.b64encode(json.dumps(value,separators=(',',':'),allow_nan=False).encode()).decode(),'rawRecordN':raw['n'],'commitEvidence':proof}
 def output(row):
  nonlocal logical
  logical+=1;return {**row,'rawRecordN':row.get('rawRecordN',row['n']),'rawRecordSHA256':row['sha256'],'n':logical,'logicalIndex':logical,'auditProjectionOnly':True}
 for row in rows:
  k=row['kind'];v=payload(row)if k.startswith('CONTROL_')or k=='LIFECYCLE'else None
  if k=='LIFECYCLE'and v.get('kind')=='OPENED':
   if openedSeen:fail('DUPLICATE_OPENED_CONTEXT')
   openedSeen=True
   observed={key:v[key]for key in CTX};context(observed,expected);expected={**(expected or {}),**observed}
  if k in('CONTROL_INPUT_TX','CONTROL_CONSENT_TX')and expected is None:fail('CHAIN_OPENED_CONTEXT_REQUIRED')
  if k in('CONTROL_INPUT','CONTROL_CONSENT','CONTROL_LEASE_RENEWED'):fail('LEGACY_AUTHORITY_EVENT_NOT_SELECTED09')
  candidate=k in('CONTROL_INPUT_TX','CONTROL_CONSENT_TX')
  if candidate and failed:fail('CANDIDATE_AFTER_FAILED_AUTHORITY')
  receipt=v.get('priorCommitReceipt')if candidate else(v.get('commitReceipt')if type(v)is dict else None)
  if receipt is not None:
   if not candidate and k not in('CONTROL_INPUT_WIRE_BINDING','CONTROL_REVOKED','CONTROL_LOCAL_SEND_RETURNED','CONTROL_COMMIT_RECEIPT','CONTROL_COMMIT_REFUSED','CONTROL_INPUT_REJECTED','CONTROL_COMMIT_CANCELLED','CONTROL_INPUT_CANCELLED_BEFORE_COMMIT','CONTROL_INPUT_ADMISSION_REJECTED'):fail('UNDECLARED_RECEIPT_CARRIER')
   if pending is None:fail('ORPHAN_OR_DUPLICATE_RECEIPT')
   cr,cv,raw= pending;r=receipt
   if type(r)is not dict or set(r)!=({'format','version','context','operation','txRecordN','txPayloadSHA256','groupDurableNs','decisionNs','disposition','proposal','reason','authorityRestorable'}|({'expectedCancellation'}if r.get('disposition')=='CANCELLED'else set()))or r['format']!='aeris-authority-commit-receipt'or type(r['version'])is not int or r['version']!=1:fail('RECEIPT_SCHEMA')
   context(r['context'],expected)
   if not same(r['context'],cv['context'])or r['operation']!=cv['operation']or type(r['txRecordN'])is not int or r['txRecordN']!=cr['n']or r['txPayloadSHA256']!=hashlib.sha256(raw).hexdigest()or not same(r['proposal'],cv['proposal'])or r['authorityRestorable']is not False:fail('RECEIPT_CANDIDATE_BINDING')
   durable=integer(r['groupDurableNs']);decision=integer(r['decisionNs']);pre=integer(cv['preWriteNs'])
   if not pre<=cr['monotonicNs']<=durable<=decision<=row['monotonicNs']or decision<lastDecision:fail('COMMIT_CLOCK_ORDER')
   if any(x['monotonicNs']<decision for x in buffer):fail('INTERVENING_EVENT_PRECEDES_RESOLVED_DECISION')
   p=cv['proposal'];i=cv['input']if cv['operation']=='INPUT'else cv['neutralInput'];kind=p['kind']
   if r['disposition']not in('ACCEPTED','REFUSED','CANCELLED')or(r['disposition']=='ACCEPTED'and r['reason']is not None)or(r['disposition']=='REFUSED'and(type(r['reason'])is not str or not 1<=len(r['reason'])<=512))or(r['disposition']=='CANCELLED'and r['reason']!='EXPECTED_RELEASE_CANCELLATION'):fail('DISPOSITION_REASON')
   if p['priorLeaseId']!=lease or p['priorExpiryNs']!=expiry:fail('PRIOR_LEASE_NOT_RESOLVED_STATE')
   proof={'provenance':PROVENANCE,'candidateRecordN':cr['n'],'candidateRecordSHA256':cr['sha256'],'candidatePayloadSHA256':hashlib.sha256(raw).hexdigest(),'carrierRecordN':row['n'],'carrierRecordSHA256':row['sha256'],'carrierMonotonicNs':row['monotonicNs'],'groupDurableNs':durable,'decisionNs':decision,'disposition':r['disposition']}
   maxBarrier=max(maxBarrier,durable-pre);lastDecision=decision
   if r['disposition']in('ACCEPTED','CANCELLED'):
    if any(i.get(key)!=cv['context'][key]for key in CTX):fail('INPUT_CONTEXT')
    seq=integer(i['sequence']);sample=integer(i['elapsedNs']);uptime=integer(i['uptimeNs']);o=i.get('inputObservation')
    if not uptime<=sample<=pre or any(not 0<=t-sample<=TTL for t in(durable,decision)):fail('INPUT_AGE_AT_ACTUAL_COMMIT')
    if type(o)is not dict or type(o.get('uiHeartbeatElapsedNs'))is not int or any(not 0<=t-o['uiHeartbeatElapsedNs']<=TTL for t in(durable,decision))or o['uiHeartbeatElapsedNs']>sample:fail('ATTACHED_UI_AT_ACTUAL_COMMIT')
    if lease is not None and (durable>expiry or decision>expiry):fail('PRIOR_LEASE_EXPIRED_AT_ACTUAL_COMMIT')
    if p['inputSequence']!=seq:fail('PROPOSAL_INPUT')
    if r['disposition']=='CANCELLED':
     if k!='CONTROL_COMMIT_CANCELLED'or r['expectedCancellation']['decisionNs']>decision:fail('CANCELLED_CARRIER_CLOCK')
     if p['inputSequence']!=seq:fail('CANCELLED_PROPOSAL_INPUT')
     if cv['operation']=='INPUT':
      if seq<=lastSequence or kind!=('RELEASE'if i['release']else'RENEW'if lease is not None else'OBSERVE')or p['proposedLeaseId']!=(None if i['release']else lease)or p['proposedExpiryNs']!=(-1 if i['release']or lease is None else sample+TTL):fail('CANCELLED_PROPOSAL')
     elif kind!='CONSENT'or lease is not None or latest is None or not same(latest,i)or i['release']or i['pointers']!=0 or any(x!=0 for x in i['axes'])or p['proposedLeaseId']!=f"lease-{grants+1}-{p['actionId']}"or p['proposedExpiryNs']!=sample+TTL:fail('CANCELLED_CONSENT')
     cancelled+=1;lease=None;expiry=-1
     yield output(derive(cr,'CONTROL_INPUT_COMMIT_CANCELLED',{'input':i,'expectedCancellation':r['expectedCancellation'],'operation':cv['operation']},decision,proof))
    elif cv['operation']=='INPUT':
     if seq<=lastSequence:fail('INPUT_SEQUENCE')
     if kind!=('RELEASE'if i['release']else'RENEW'if lease is not None else'OBSERVE'):fail('PROPOSAL_KIND')
     if p['proposedLeaseId']!=(None if i['release']else lease)or p['proposedExpiryNs']!=(-1 if i['release']or lease is None else sample+TTL):fail('PROPOSED_LEASE')
     lastSequence=seq;latest=i;accepted+=1
     yield output(derive(cr,'CONTROL_INPUT',i,decision,proof))
     if kind=='RENEW':
      expiry=p['proposedExpiryNs'];yield output(derive(cr,'CONTROL_LEASE_RENEWED',{'leaseId':lease,'inputSequence':seq,'expiresNs':expiry},decision,proof))
     if kind=='RELEASE':lease=None;expiry=-1
    else:
     if kind!='CONSENT'or p['proposedLeaseId']!=f"lease-{grants+1}-{p['actionId']}"or lease is not None or latest is None or not same(latest,i)or i['release']or i['pointers']!=0 or any(x!=0 for x in i['axes'])or p['proposedExpiryNs']!=sample+TTL or type(p['proposedLeaseId'])is not str:fail('CONSENT_PROPOSAL_OR_INPUT')
     lease=p['proposedLeaseId'];expiry=p['proposedExpiryNs'];accepted+=1;grants+=1
     event={'actionId':p['actionId'],'leaseId':lease,'neutralInputSequence':seq,'source':i['source'],'clockDomain':i['clockDomain'],'provenance':i['provenance'],'expiresNs':expiry}
     yield output(derive(cr,'CONTROL_CONSENT',event,decision,proof))
   else:
    if k!='CONTROL_COMMIT_REFUSED':fail('REFUSAL_CARRIER_NOT_DECLARED')
    refused+=1;lease=None;expiry=-1;failed=True
   for held in buffer:yield output(held)
   buffer=[];pending=None
  if candidate:
   if v['operation']=='INPUT'and v['input']['sequence']<=lastRejected:fail('REJECTED_INPUT_REPLAYED_AS_CANDIDATE')
   if admissionFatal:fail('CANDIDATE_AFTER_FATAL_ADMISSION')
   if pending is not None:fail('PENDING_RECEIPT_NOT_CARRIED_BY_NEXT_CANDIDATE')
   required={'format','version','context','operation','preWriteNs','proposal','priorCommitReceipt','input'if k=='CONTROL_INPUT_TX'else'neutralInput'}
   if type(v)is not dict or set(v)!=required or v['format']!='aeris-authority-transaction'or type(v['version'])is not int or v['version']!=1 or v['operation']!=('INPUT'if k=='CONTROL_INPUT_TX'else'CONSENT'):fail('CANDIDATE_SCHEMA')
   context(v['context'],expected);input_schema(v['input']if v['operation']=='INPUT'else v['neutralInput'],v['context']);integer(v['preWriteNs']);p=v['proposal'];keys={'kind','priorLeaseId','priorExpiryNs','proposedLeaseId','proposedExpiryNs','inputSequence'}|({'actionId'}if v['operation']=='CONSENT'else set())
   if type(p)is not dict or set(p)!=keys or type(p['priorExpiryNs'])is not int or type(p['proposedExpiryNs'])is not int or type(p['inputSequence'])is not int:fail('PROPOSAL_SCHEMA')
   if v['operation']=='CONSENT'and(type(p['actionId'])is not str or re.fullmatch('[A-Za-z0-9_.:-]{1,128}',p['actionId'])is None):fail('CONSENT_ACTION_ID')
   pending=(row,v,base64.b64decode(row['base64'],validate=True));candidates+=1
   continue
  if pending is not None:
   if k in('CONTROL_REVOKED','CONTROL_FAILURE','CONTROL_COMMIT_REFUSED','CONTROL_COMMIT_CANCELLED','OPERATOR_TOUCH_ACTION'):fail('UNRESOLVED_BEFORE_AUTHORITY_OR_DISCRETE_EVENT')
   buffer.append(row)
   if len(buffer)>256 or sum(len(x['base64'])for x in buffer)>4*2**20:fail('DELAYED_CARRIER_BUFFER_BOUND')
   if k in('TX_INTENT','SESSION_CLOSE'):fail('UNRESOLVED_BEFORE_WIRE_OR_TERMINAL')
   continue
  if k=='CONTROL_PROVIDER':
   epoch=v.get('selectedUIEpoch')
   if providerSource is not None or type(epoch)is not int or epoch<=0 or type(v.get('source'))is not str or re.fullmatch(r'touch-[a-f0-9-]{36}',v['source'])is None or v.get('inputProvenance')not in('ROOT_INJECTED_ANDROID_TOUCH','LOCAL_ANDROID_TOUCH_NOT_HID_ATTESTED'):fail('SELECTED_PROVIDER_SOURCE_OR_UI_EPOCH')
   if expected.get('expectedViewEpoch')is not None and expected['expectedViewEpoch']!=epoch:fail('ROOT_PROVIDER_UI_EPOCH_MISMATCH')
   expected={**expected,'expectedViewEpoch':epoch};providerSource=v['source'];providerProvenance=v['inputProvenance']
  if admissionPending is not None and k!='HEADER':
   if k!='CONTROL_REVOKED'or v.get('reason')!=admissionPending['reason']or v.get('previousLeaseId')!=admissionPending['priorLeaseId']or v.get('atNs',-1)<admissionPending['atNs']or v.get('authorityRestorable')is not False:fail('ADMISSION_REJECTION_MUST_IMMEDIATELY_REVOKE')
   admissionPending=None
  if k=='CONTROL_INPUT_ADMISSION_REJECTED':
   from .input_admission import validate as admission_validate
   if expected is None or providerSource is None:fail('ADMISSION_PROVIDER_CONTEXT_REQUIRED')
   retained=admission_validate(v,row['monotonicNs'],expected,providerSource,providerProvenance,lease,expiry,max(lastSequence,lastRejected),latest,lastDecision,failed,releaseState.lastFence or 0,releaseState.notices.values())
   if retained is not None:lastRejected=max(lastRejected,retained['sequence'])
   admissionRejected+=1;isExpiry=v['disposition']=='EXPIRED_NO_AUTHORITY';admissionExpired+=int(isExpiry);admissionFatal=admissionFatal or not isExpiry
   admissionPending={'reason':'INPUT_ADMISSION_EXPIRED'if isExpiry else'INVALID_INPUT','priorLeaseId':lease,'atNs':v['atNs']}
  if k=='CONTROL_INPUT_CANCELLED_BEFORE_COMMIT':
   if lease is not None and v['expectedCancellation']['decisionNs']>expiry:fail('PRIOR_LEASE_EXPIRED_BEFORE_PREQUEUE_CANCELLATION')
  if k in('CONTROL_COMMIT_REFUSED','CONTROL_COMMIT_CANCELLED')and receipt is None:fail('COMMIT_REFUSED_WITHOUT_RECEIPT')
  if k=='CONTROL_FAILURE':failed=True;failureSeen=True
  if k=='SESSION_CLOSE':
   close=payload(row)
   if failed and(not failureSeen or close.get('reason')!='CONTROL_FAILED_RESOURCES_CLOSED'):fail('FAILED_AUTHORITY_REQUIRES_FAILED_TERMINAL')
  if k=='CONTROL_REVOKED'and v.get('reason')in('UI_LIVENESS_EXPIRED','INPUT_LEASE_EXPIRED'):
   at=integer(v.get('atNs'));ui=None if latest is None else latest['inputObservation']['uiHeartbeatElapsedNs']
   if not(lease is not None and latest is not None and v.get('previousLeaseId')==lease and v.get('previouslyActive')is True and at<=row['monotonicNs']and at>=lastDecision):fail('TICK_EXPIRY_PRIOR_AUTHORITY')
   if v['reason']=='UI_LIVENESS_EXPIRED'and not at-ui>TTL:fail('TICK_UI_EXPIRY_PREDICATE')
   if v['reason']=='INPUT_LEASE_EXPIRED'and not(at>expiry and 0<=at-ui<=TTL):fail('TICK_LEASE_EXPIRY_PREDICATE_OR_ORDER')
  if k in('CONTROL_REVOKED','CONTROL_FAILURE','CONTROL_COMMIT_REFUSED'):lease=None;expiry=-1
  yield output(row)
 if admissionPending is not None:fail('ADMISSION_REJECTION_REVOKE_MISSING')
 if admissionFatal and not failureSeen:fail('FATAL_ADMISSION_FAILED_TERMINAL_REQUIRED')
 if pending is not None or buffer:fail('UNKNOWN_UNWITNESSED_COMMIT_TAIL')
 if candidates==0:fail('NO_SELECTED09_TRANSACTIONS')
 if summary is not None:summary.update(format='aeris-09-resolved-commit-audit-view',provenance=PROVENANCE,candidates=candidates,accepted=accepted,refused=refused,cancelled=cancelled,rxGroup13=rxProof,inputAdmission13=dict(rejected=admissionRejected,expired=admissionExpired,fatal=admissionFatal,fullOriginalInputRetained=True,qualifiedUninterruptedControl=admissionRejected==0,unverifiableFatalContextCausesRejected=True),release12=releaseProof,logicalRecords=logical,maxBarrierWallNs=maxBarrier,actualDecisionClockRequired=True,rawMutated=False)
