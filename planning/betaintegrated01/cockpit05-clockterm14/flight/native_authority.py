"""QA-owned bounded native authority/CRC pass over every root-anchored native row.

Reuse the unchanged accepted chain receiver through the new indexed archive.
Keep only64 recent input/binding frames and bounded discrete operator witnesses;
never retain a full long raw row/input table in this independent pass.
"""
from pathlib import Path
import base64,hashlib,json,math,sys
from collections import OrderedDict
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from .native_stream import closed_native
from .rx_group import RXAudit
from pilot.betaintegrated01.control01.mavlink import Framer
TTL=200_000_000

def audit(path,prefix,anchor,context,*,scenario='nominal'):
 proof,rows=closed_native(path,prefix,anchor)
 if proof.get('expiryRevocations'):raise ValueError('EXPIRY_DEESCALATION_NOT_UNINTERRUPTED_SUCCESSFUL_AUTHORITY')
 if proof.get('inputAdmissionRejections'):raise ValueError('ADMISSION_REJECTION_NOT_UNINTERRUPTED_SUCCESSFUL_AUTHORITY')
 if proof.get('preSocketRefusals'):raise ValueError('REFUSAL_IS_NOT_SUCCESSFUL_FLIGHT_AUTHORITY')
 from .transactions import resolve_rows
 sampler={};commitProof={};rawRecords=proof['records'];originalRows=rows
 def resolved():
  yield from resolve_rows(originalRows,context,commitProof)
  proof['rawRecords']=rawRecords;proof['records']=commitProof['logicalRecords'];proof['commitTransactions']=commitProof
 rows=validate_sampler_rows(resolved(),context,sampler)
 result=audit_rows(proof,rows,context,scenario=scenario);result['dedicatedSampler']=sampler;return result

def audit_rows(proof,rows,context,*,scenario='nominal'):
 recent=OrderedDict();bindings=OrderedDict();actions={};consents=[];revokes=[];failures=[];up=[];lease=None;expires=None;latest=None;pending=None;last_input=-1;last_uptime=-1;last_offset=None;source=None;opened=provider=False;first_ns=last_ns=None;first_input=last_input_ns=None;accepted_inputs=0;max_lease2_gap=0;max_gap=0;max_age=0;max_bind_age=0;renewals=0;wire_written=unknown=RX=tx_count=rx_frames=normal_rc=0;last_failure=None;normal_after_failure=0;max_recent=0;max_bind=0;last_written=None;close=None;operator_close=[];rx=Framer();tx=Framer();lifecycle=[];lease2first=lease2last=lease2uptimefirst=lease2uptimelast=None;neutral_hold=True;neutral_at_failure=False;first_pointer_release=None;pilot_after_release=0;rxGroups=RXAudit()
 for row in rows:
  n,now,k=row['n'],row['monotonicNs'],row['kind'];first_ns=now if first_ns is None else first_ns;last_ns=now;raw=base64.b64decode(row['base64'],validate=True)
  received=rxGroups.feed(row)
  if received is not None:rx_frames+=len(rx.feed(received['raw'],received['receiptElapsedNs']))
  v=json.loads(raw)if k in('HEADER','LIFECYCLE','CONTROL_PROVIDER','CONTROL_INPUT','OPERATOR_TOUCH_ACTION','CONTROL_CONSENT','CONTROL_LEASE_RENEWED','CONTROL_REVOKED','CONTROL_INPUT_WIRE_BINDING','TX_UNKNOWN','TX_REFUSED','CONTROL_FAILURE','OPERATOR_CLOSE_REQUEST','SESSION_CLOSE')else None
  if k=='LIFECYCLE':
   if len(lifecycle)>=32:raise ValueError('LIFECYCLE_COUNT_BOUND')
   lifecycle.append(dict(record=n,kind=v['kind'],guestNs=now))
   if v['kind']=='OPENED':
    assert not opened
    for key in('run','epoch','boot','generation','operator','profileId'):assert v[key]==context[key]
    assert v['binarySHA256']==context['binarySHA256'];opened=True
  elif k=='CONTROL_PROVIDER':
   assert not provider
   for key in('run','epoch','boot','generation'):assert v[key]==context[key]
   assert v['binarySHA256']==context['binarySHA256']and v['configSHA256']==context['configSHA256'];source=v['source'];provider=True
  elif k=='CONTROL_INPUT':
   if lease is not None:assert now<=expires,'INPUT_DURABLE_EVENT_AFTER_PRIOR_LEASE_EXPIRY'
   accepted_inputs+=1
   for key in('run','epoch','boot','generation','operator','profileId'):assert v[key]==context[key]
   assert v['source']==source and v['clockDomain']=='ANDROID_UPTIME_NS_SAMPLER'and v['provenance']==context['inputProvenance'];seq=v['sequence'];assert type(seq)is int and seq>last_input;assert type(v['elapsedNs'])is int and type(v['uptimeNs'])is int and last_uptime<=v['uptimeNs']<=v['elapsedNs']<=now and 0<=now-v['elapsedNs']<=TTL
   assert type(v['lastMotionUptimeNs'])is int and 0<=v['lastMotionUptimeNs']<=v['uptimeNs'];a=v['axes'];assert len(a)==4 and all(type(x)in(int,float)and math.isfinite(x)and -1<=x<=1 for x in a);assert type(v['pointers'])is int and 0<=v['pointers']<=2 and type(v['release'])is bool and v['motionAction']in(-1,0,1,2,3,5,6)
   if v['pointers']==0:assert all(x==0 for x in a)
   if v['release']:assert v['motionAction']in(1,3,6)and v['pointers']==0;up.append(dict(record=n,input=v))
   if len(consents)==2 and lease==consents[1]['event']['leaseId']:neutral_hold=neutral_hold and v['pointers']==0 and not v['release']and all(x==0 for x in a)
   offset=v['elapsedNs']-v['uptimeNs'];assert last_offset is None or abs(offset-last_offset)<=5_000_000
   if last_input_ns is not None:max_gap=max(max_gap,v['elapsedNs']-last_input_ns)
   first_input=v['elapsedNs']if first_input is None else first_input;last_input_ns=v['elapsedNs'];max_age=max(max_age,now-v['elapsedNs']);last_input=seq;last_uptime=v['uptimeNs'];last_offset=offset;latest=(row,v);recent[seq]=latest
   while len(recent)>64:recent.popitem(last=False)
   max_recent=max(max_recent,len(recent))
  elif k=='OPERATOR_TOUCH_ACTION':
   assert v['actionId']not in actions and len(actions)<256;assert type(v['producerElapsedNs'])is int and v['producerElapsedNs']<=v['receiptElapsedNs']<=now and now-v['producerElapsedNs']<=TTL;actions[v['actionId']]=(row,v)
  elif k=='CONTROL_CONSENT':
   ir,iv=recent[v['neutralInputSequence']];assert latest[1]['sequence']==iv['sequence']and not iv['release']and iv['pointers']==0 and all(x==0 for x in iv['axes']);assert 0<=now-iv['elapsedNs']<=TTL and v['expiresNs']==iv['elapsedNs']+TTL;ar,av=actions[v['actionId']];assert av['action']=='CONSENT'and ar['n']<n and lease is None;lease=v['leaseId'];expires=v['expiresNs'];consents.append(dict(record=n,guestNs=now,event=v,input=iv,operatorAction=av))
   assert len(consents)<=4
   if len(consents)==2:lease2first=iv['elapsedNs'];lease2last=iv['elapsedNs'];lease2uptimefirst=iv['uptimeNs'];lease2uptimelast=iv['uptimeNs']
  elif k=='CONTROL_LEASE_RENEWED':
   assert expires is not None and now<=expires,'RENEWED_DURABLE_EVENT_AFTER_PRIOR_LEASE_EXPIRY'
   assert lease==v['leaseId']and latest[1]['sequence']==v['inputSequence']and v['expiresNs']==latest[1]['elapsedNs']+TTL;expires=v['expiresNs'];renewals+=1
   if len(consents)==2:max_lease2_gap=max(max_lease2_gap,latest[1]['elapsedNs']-lease2last);lease2last=latest[1]['elapsedNs'];lease2uptimelast=latest[1]['uptimeNs']
  elif k=='CONTROL_REVOKED':
   if len(revokes)>=32:raise ValueError('REVOKE_COUNT_BOUND')
   revokes.append(dict(record=n,guestNs=now,event=v));lease=None;expires=None
   if v['reason']in('TRUSTED_TOUCH_RELEASE','EXPECTED_RELEASE_CANCELLATION'):
    assert any(x['record']==row.get('rawRecordN',n)for x in proof['release12']['causalReleases']);first_pointer_release=n
  elif k=='CONTROL_INPUT_WIRE_BINDING':
   ir,iv=recent[v['inputSequence']];assert v['leaseId']==lease and v['source']==iv['source']and v['producerElapsedNs']==iv['elapsedNs'];age=v['sendCheckNs']-iv['elapsedNs'];assert 0<=age<=TTL and v['sendCheckNs']<=now and expires is not None and v['sendCheckNs']<=expires;max_bind_age=max(max_bind_age,age);bindings[v['wireSHA256']]=(row,v,iv)
   if first_pointer_release is not None and v['purpose']=='RC_LOITER_PILOT':pilot_after_release+=1
   while len(bindings)>64:bindings.popitem(last=False)
   max_bind=max(max_bind,len(bindings))
  elif k=='TX_INTENT':
   assert pending is None;pending=(raw,n,now,row.get('rawRecordN',n))
   if last_failure is not None:normal_after_failure+=1
  elif k=='TX_WRITTEN':
   assert pending and pending[0]==raw;wire_written+=1;last_written=n
   for frame in tx.feed(raw,now):
    assert(frame['system'],frame['component'])==(255,190);tx_count+=1
    if frame['id']==70:
     b=bindings.get(hashlib.sha256(raw).hexdigest())
     if b and b[1]['purpose']=='RC_LOITER_PILOT':
      import struct
      p=frame['payload'];a=b[2]['axes'];expected=[math.floor(1500+125*x+.5)for x in(a[0],-a[1],a[2],a[3])];assert list(struct.unpack_from('<4H',p))==expected and p[16:18]==bytes([42,1]);normal_rc+=1
   pending=None
  elif k=='TX_REFUSED':
   assert 'expectedCancellation'in v and pending
   assert pending and type(v['intentRecordN'])is int and v['intentRecordN']==pending[3]and v['wireSHA256']==hashlib.sha256(pending[0]).hexdigest()and v['socketCallbackEntered']is False
   pending=None
  elif k=='TX_UNKNOWN':assert pending and v['wireSHA256']==hashlib.sha256(pending[0]).hexdigest();pending=None;unknown+=1
  elif k=='RX':
   RX+=1
   # CRC is consumed only after its adjacent strict group completion above.
  elif k=='CONTROL_FAILURE':
   neutral_at_failure=bool(latest and latest[1]['pointers']==0 and not latest[1]['release']and all(x==0 for x in latest[1]['axes'])and len(consents)==2 and lease==consents[1]['event']['leaseId']);failures.append(dict(record=n,guestNs=now,event=v));assert len(failures)<=16;last_failure=n;lease=None;expires=None
  elif k=='OPERATOR_CLOSE_REQUEST':operator_close.append(dict(record=n,event=v));assert len(operator_close)<=4
  elif k=='SESSION_CLOSE':assert close is None;close=dict(record=n,guestNs=now,event=v)
 rxGroups.finish()
 assert opened and provider and close and close['record']==proof['records']and pending is None and not rx.pending and not tx.pending and lease is None and normal_after_failure==0
 releaseProof=proof.get('release12');assert releaseProof is not None and not releaseProof.get('incompleteExpectedEpisodes')
 causalIds={x['releaseId']for x in releaseProof['causalReleases']};noticeIds={x['releaseId']for x in releaseProof['noticeProofs']};assert len(causalIds)==1 and causalIds==noticeIds and len(up)<=1,'ONE_CAUSAL_RAW_TOUCH_RELEASE_REQUIRED'
 if scenario=='nominal':assert len(consents)==2 and consents[0]['event']['leaseId']!=consents[1]['event']['leaseId']and len(causalIds)==1 and not failures and unknown==0 and close['event']['reason']=='CONTROL_OWNED_RESOURCES_CLOSED'
 if scenario=='assisted-hold-loss':assert len(consents)==2 and len(causalIds)==1 and failures and close['event']['reason']=='CONTROL_FAILED_RESOURCES_CLOSED'
 if scenario=='loss':assert len(consents)==1 and failures and close['event']['reason']=='CONTROL_FAILED_RESOURCES_CLOSED'
 return dict(release12=releaseProof,acceptedUPSamples=up,rawTouchReleaseIds=sorted(causalIds),status='PASS_STREAMED_NATIVE_AUTHORITY_CRC'if scenario=='nominal'else'PASS_LOSS_FAILURE_RETAINED_NATIVE_AUTHORITY_REVOKED',chain=proof,scenario=scenario,records=proof['records'],nativeObservedWindowNs=last_ns-first_ns,inputObservedWindowNs=None if first_input is None else last_input_ns-first_input,secondLeaseProducerWindowNs=None if lease2first is None else lease2last-lease2first,secondLeaseUptimeWindowNs=None if lease2uptimefirst is None else lease2uptimelast-lease2uptimefirst,lease2NeutralThroughout=neutral_hold,neutralAtFailure=neutral_at_failure,pilotBindingsAfterFirstRelease=pilot_after_release,inputs=accepted_inputs,maxLease2ProducerGapNs=max_lease2_gap,normalRCPackets=normal_rc,rawRXRecords=RX,allCRC_RXFrames=rx_frames,allCRC_TXFrames=tx_count,written=wire_written,unknownSends=unknown,maxInputObservedGapNs=max_gap,maxInputJournalAgeNs=max_age,maxBindingAgeNs=max_bind_age,boundedRecentInputs=max_recent,boundedWireBindings=max_bind,consents=consents,revokes=revokes,UP=up,failures=failures,operatorClose=operator_close,terminal=close,postFailureTXIntents=normal_after_failure,authorityRestored=False,physicalHIDAttested=False,actualThirtyMinuteAccepted=False,scope='Allrows+CRC/input/lease mapping fromrootanchorednative; conservative durable-event lease-expiry checks required for uninterrupted qualification; actual duration/flight/ground requirehost/AP and rootpower clocks, not mock timestamps.')


def validate_sampler_rows(rows,context,summary=None):
 expected=context.get('expectedViewEpoch')
 if type(expected)is not int or expected<=0:raise ValueError('ROOT_OBSERVED_UI_EPOCH_REQUIRED')
 latest={};thread_pair=None;touch=-1;fence=-1;last_ui=-1;inputs=0;maximumUIAge=0
 for row in rows:
  kind=row['kind'];now=row['monotonicNs']
  if kind=='TX_REFUSED':
   v=json.loads(base64.b64decode(row['base64'],validate=True))
   if 'expectedCancellation'not in v:raise ValueError('TX_REFUSED_FORENSIC_NOT_SUCCESS')
  if kind=='CONTROL_INPUT':
   v=json.loads(base64.b64decode(row['base64'],validate=True));o=v.get('inputObservation')
   if type(o)is not dict or set(o)!={'kind','uiHeartbeatElapsedNs','touchRevision','samplerThreadId','uiThreadId','viewEpoch','releaseFence'}or o['kind']!='IMMUTABLE_UI_TOUCH_STATE_SAMPLE_NOT_NEW_MOTION_EVENT':raise ValueError('DEDICATED_SAMPLER_DECLARATION_REQUIRED')
   if any(type(o[k])is not int or o[k]<0 for k in('uiHeartbeatElapsedNs','touchRevision','samplerThreadId','uiThreadId','viewEpoch','releaseFence')):raise ValueError('SAMPLER_TYPES')
   if o['viewEpoch']!=expected or not 0<=now-o['uiHeartbeatElapsedNs']<=TTL or o['uiHeartbeatElapsedNs']>v['elapsedNs']or o['samplerThreadId']<=0 or o['uiThreadId']<=0 or o['samplerThreadId']==o['uiThreadId']or o['touchRevision']<touch or o['releaseFence']<fence or o['uiHeartbeatElapsedNs']<last_ui:raise ValueError('SAMPLER_UI_FRESHNESS_CONTEXT_THREADS_OR_REGRESSION')
   inputs+=1;maximumUIAge=max(maximumUIAge,now-o['uiHeartbeatElapsedNs'])
   pair=(o['samplerThreadId'],o['uiThreadId'])
   if thread_pair is not None and pair!=thread_pair:raise ValueError('SAMPLER_THREAD_IDENTITY_CHANGED')
   thread_pair=pair;touch=o['touchRevision'];fence=o['releaseFence'];last_ui=o['uiHeartbeatElapsedNs'];latest[v['sequence']]=o
   while len(latest)>64:del latest[next(iter(latest))]
  elif kind=='CONTROL_CONSENT':
   v=json.loads(base64.b64decode(row['base64'],validate=True));o=latest.get(v['neutralInputSequence'])
   if o is None or not 0<=now-o['uiHeartbeatElapsedNs']<=TTL:raise ValueError('SAMPLER_UI_NOT_FRESH_AT_CONSENT')
  elif kind=='CONTROL_INPUT_WIRE_BINDING':
   v=json.loads(base64.b64decode(row['base64'],validate=True));o=latest.get(v['inputSequence'])
   if o is None or not 0<=v['sendCheckNs']-o['uiHeartbeatElapsedNs']<=TTL:raise ValueError('SAMPLER_UI_NOT_FRESH_AT_WIRE_BINDING')
  yield row
 if summary is not None:summary.update({'inputs':inputs,'samplerThreadId':None if thread_pair is None else thread_pair[0],'uiThreadId':None if thread_pair is None else thread_pair[1],'viewEpoch':expected,'maximumUIHeartbeatAgeAtInputRecordNs':maximumUIAge,'lastTouchRevision':touch,'lastReleaseFence':fence,'provenance':'IMMUTABLE_UI_TOUCH_STATE_SAMPLE_NOT_NEW_MOTION_EVENT','authorityOrPhysicalMotionAttestation':False})
