"""Public Android Intent bridge. No private baseline, binding push, or input authority."""
import base64,json,secrets,time,re,hashlib
from pathlib import Path
from collections import deque
from .candidate import put
from pilot.betaintegrated01.runtime.ap_stage import canonical
from .proofs import validate_native_ack,need,workspace_projection
PACKAGE='vn.rtr.aeris.mission'
COMPONENT=PACKAGE+'/.CockpitActivity'
class NativeBridge:
 """Injected bounded command/log adapter; only the product supervisor invokes it."""
 def __init__(self,device,source,*,now=time.monotonic_ns,receipt_root=None,apk_sha=None):
  self.device=device;self.source=source;self.apk_sha=apk_sha;self.now=now;self.latest=None;self.trace=deque(maxlen=8);self.receipt_root=Path(receipt_root) if receipt_root is not None else None;self.requests=0;self.process_epoch=None;self.last_receipt_ref=None;self.stage_attempted=False;self.bootstrap_attempted=False;self.unselected_identity=None;self._unselected_pin_bytes=None;self._latest_validated_raw=None;self._latest_receipt_bytes=None;self.stage_committed=False;self.staged_context=None;self.stage_receipt_ref=None;self.last_timing=None;self.planned_transition=None;self.transition_attempted=False
 def prepare_normal(self,*,deadline_ns):
  need(type(self.apk_sha) is str and len(self.apk_sha)==64,'INSTALLED_APK_EXPECTATION_REQUIRED')
  return self.device.prepare_normal(self.apk_sha,deadline_ns=min(deadline_ns,self.now()+60_000_000_000))
 def request(self,action,body=None,*,context=None,deadline_ns=None):
  timing=None
  if action=='STATUS'and getattr(self.device,'status_socket',None)is not None:
   from .status15_timing import StatusTiming
   timing=StatusTiming(now=self.now)
  if action=='BOOTSTRAP':self.bootstrap_attempted=True
  self.device._check_budget_actor()
  need(context is None or type(context)is dict and len(canonical(context))<=256,'OBSERVER_PROFILE_CONTEXT256_BEFORE_DISPATCH')
  need(action in ('STATUS','BOOTSTRAP'),'PUBLIC_ACTION');need(getattr(self.device,'store',None)is not None,'DURABLE_ONCE_STORE_REQUIRED')
  if action=='STATUS'and getattr(self.device,'status_socket',None)is not None:
   need(self.device.status_socket.active and not self.device.status_socket.closed and self.device.status_socket.failure is None,'STATUS15_SELECTED_CHANNEL_FAILURE_NO_LEGACY_FALLBACK')
   timing.point('validated')
   try:
    with self.device.budget.trace_stages(timing):
     with self.device.budget.operation({'requests':2048+8192,'commands':32768,'dto':16384+8192,'barriers':8192,'command_receipts':8192}):result=self._socket_request(body,context=context,deadline_ns=deadline_ns,timing=timing)
   finally:
    timing.point('returnReady');self.last_timing=timing.projection(final=True)
   return result
  with self.device.budget.operation({'requests':(16384 if action=='BOOTSTRAP'else 2048)+8192}):return self._request(action,body,context=context,deadline_ns=deadline_ns)
 def _request(self,action,body=None,*,context=None,deadline_ns=None):
  need(self.requests<2048,'PUBLIC_REQUEST2048_METADATA_BOUND_NO_DROPS')
  need(self.requests<900,'DECLARED_CAMPAIGN900_REQUEST_ENVELOPE')
  need(getattr(self.device,'store',None) is not None,'DURABLE_ONCE_STORE_REQUIRED')
  self.device.budget.ensure('requests',(16384 if action=='BOOTSTRAP'else 2048)+8192);self.device.budget.tick('requests')
  if action=='BOOTSTRAP':self.device.budget.tick('bootstraps')
  need(action in ('STATUS','BOOTSTRAP'),'PUBLIC_ACTION');request=dict(body or {});request.setdefault('version',1);request.setdefault('requestNonce',secrets.token_hex(16))
  raw=json.dumps(request,separators=(',',':'),ensure_ascii=False).encode();need(len(raw)<=(512 if action=='STATUS' else 32768),'INTENT_BOUNDED')
  sent=self.now();deadline=min(sent+10_000_000_000,deadline_ns or sent+10_000_000_000)
  # Subscription is active before Intent. It must retain its original matching live row.
  with self.device.live_log('AERIS_MISSION',deadline_ns=deadline) as stream:
   intent_host_ns=self.now()
   self.device.intent(COMPONENT,{'missionAction':action,'missionRequestBase64':base64.urlsafe_b64encode(raw).decode()},deadline_ns=deadline)
   ack=None
   for row in stream:
    need(self.now()<=deadline,'PUBLIC_NATIVE10S')
    if row.get('requestNonce')!=request['requestNonce']:continue
    ack=row;break
   need(ack is not None,'LIVE_ACK_REQUIRED')
   pid=self.device.pid(PACKAGE,deadline_ns=deadline)
   snapshot=self.device.read_private(PACKAGE,ack.get('snapshotPath'),maximum_bytes=131072,deadline_ns=deadline)
   received=self.now();need(received<=deadline,'PUBLIC_NATIVE10S')
   result=validate_native_ack(request,ack,snapshot,pid=pid,source=self.source,expected_context=context,host_sent_ns=sent,host_received_ns=received)
   need(self.process_epoch is None or result['processEpoch']==self.process_epoch,'PROCESS_RESTART_REQUIRES_NEW_DEVICE_LIFECYCLE')
   self.process_epoch=result['processEpoch']
   receipt={'format':'aeris-public-request','version':3,'sequence':self.requests+1,'request':request,'action':action,'hostSentNs':sent,'hostReceivedNs':received,'sourceSHA256':self.source,'context':ack['context'],'expectedContext':context,'intentHostNs':intent_host_ns,'actualPID':pid,'barrierRef':self.device.last_barrier_ref,'barrierObservedHostNs':self.device.last_barrier_ns,'ackRef':self.device.observer.last_ref,'snapshotRef':self.device.last_snapshot_ref,'snapshotSHA256':ack['snapshotSHA256'],'snapshotBytes':len(snapshot),'rawSnapshotSHA256':ack['snapshotSHA256']}
   self.requests+=1
   if self.requests>2048:raise ValueError('PUBLIC_REQUEST2048_METADATA_BOUND_NO_DROPS')
   encoded=canonical(receipt)+b'\n'
   need(len(encoded)<=(16384 if action=='BOOTSTRAP'else 2048),'PUBLIC_COMPACT_RECEIPT_METADATA_BOUND')
   self.last_receipt_ref=self.device.store.receipt('request-%05d.json'%self.requests,receipt,owner='requests')
   self.trace.append(receipt)
   self.device.include_quarantine=result.get('state',{}).get('recovery',{}).get('phase')=='COMPLETE'
   self._latest_validated_raw=bytes(snapshot);self._latest_receipt_bytes=canonical(receipt);self.latest=result;return result
 def enable_status_socket(self,*,deadline_ns):
  need(self.latest is not None and self.trace and self.trace[-1]['action']=='STATUS'and self.last_receipt_ref is not None,'STATUS15_ORIGINAL_LEGACY_ENROLLMENT_REQUIRED')
  need(self.trace[-1]['version']==3 and 0<=self.now()-self.trace[-1]['hostReceivedNs']<=10_000_000_000,'STATUS15_FRESH_LEGACY_ENROLLMENT')
  need(self.latest.get('context')is None and self.latest['state'].get('ownerActive')is False and self.latest['state'].get('authorityRestorable')is False and self.latest['state'].get('native',{}).get('flight',{}).get('armed')is not True,'STATUS15_ENROLL_ONLY_UNARMED_UNSELECTED')
  return self.device.open_status_socket(self.latest,self.last_receipt_ref,self.source,self.apk_sha,deadline_ns=deadline_ns)
 def _begin_bootstrap_transport(self,status):
  """A declared lifecycle boundary, never an unexpected-EOF reconnect."""
  channel=getattr(self.device,'status_socket',None)
  if channel is None:return None
  need(not self.transition_attempted and self.planned_transition is None,'STATUS_TRANSITION_ONE_BOOTSTRAP_ATTEMPT')
  need(channel.active is True and channel.closed is False and channel.failure is None,'STATUS_TRANSITION_HEALTHY_OLD_CHANNEL')
  need(status is self.latest and self.trace[-1]['action']=='STATUS'and self.trace[-1].get('version')==4,'STATUS_TRANSITION_ORIGINAL_CURRENT_STATUS')
  need(type(self._latest_validated_raw)is bytes and canonical(status)==canonical(json.loads(self._latest_validated_raw)),'STATUS_TRANSITION_IMMUTABLE_OLD_SNAPSHOT')
  self.transition_attempted=True
  closed=self.device.close_status_socket(deadline_ns=min(self.now()+5_000_000_000,self._stage_deadline))
  proof=closed.get('receipt',{})if type(closed)is dict else{}
  need(proof.get('captureComplete')is True and proof.get('drainComplete')is True and proof.get('failure')is None and closed.get('receiptRef')is not None,'STATUS_TRANSITION_OLD_CHANNEL_DURABLY_DRAINED')
  return {'oldChannelOpenRef':channel.open_ref,'oldChannelCloseRef':closed['receiptRef'],'beforeIdentity':{k:status[k]for k in('sourceSHA256','pid','processEpoch','viewEpoch')},'oldBaselineRequestRef':self.last_receipt_ref}
 def _finish_bootstrap_transport(self,boundary,ready,context,deadline):
  if boundary is None:return ready
  need(self.planned_transition is None and self.transition_attempted and self.trace[-1]['action']=='BOOTSTRAP','STATUS_TRANSITION_DIRECT_READY_TRANSACTION')
  bootstrap_ref=self.last_receipt_ref;bootstrap_nonce=self.trace[-1]['request']['requestNonce']
  self._transition_inert(ready,context,boundary['beforeIdentity'])
  need(type(ready.get('bootstrapSHA256'))is str and re.fullmatch('[a-f0-9]{64}',ready['bootstrapSHA256'])is not None,'STATUS_TRANSITION_ORIGINAL_BOOTSTRAP_HASH')
  # This single legacy observation is explicitly planned before BOOTSTRAP was
  # sent. A previously failed channel never reaches this transaction.
  baseline=self._request('STATUS',context=context,deadline_ns=deadline)
  self._transition_inert(baseline,context,boundary['beforeIdentity'])
  need(baseline['bootstrapSHA256']==ready['bootstrapSHA256']and baseline.get('lifecycle',{}).get('phase')=='READY','STATUS_TRANSITION_SAME_READY_BOOTSTRAP')
  need(0<=self.now()-self.trace[-1]['hostReceivedNs']<=10_000_000_000,'STATUS_TRANSITION_FRESH_ORIGINAL_STATUS')
  value={'format':'aeris-planned-bootstrap-status-transition','version':1,**boundary,'bootstrapRequestRef':bootstrap_ref,'bootstrapRequestNonce':bootstrap_nonce,'bootstrapSHA256':ready['bootstrapSHA256'],'baselineRequestRef':self.last_receipt_ref,'context':dict(context),'sourceSHA256':self.source,'authorityRestored':False,'unexpectedEOFReconnect':False}
  ref=self.device.store.receipt('status15-planned-bootstrap-transition.json',value)
  self.planned_transition={'proof':value,'receiptRef':ref}
  self.device.open_status_socket(baseline,self.last_receipt_ref,self.source,self.apk_sha,deadline_ns=deadline,planned_transition=self.planned_transition)
  return baseline
 def _transition_inert(self,snapshot,context,identity):
  need(snapshot.get('context')==context and snapshot.get('sourceSHA256')==self.source and all(snapshot.get(k)==v for k,v in identity.items()),'STATUS_TRANSITION_SAME_ORIGINAL_CONTEXT_IDENTITY')
  state=snapshot.get('state',{});native=state.get('native',{});input_state=native.get('input',{})
  need(state.get('ownerActive')is False and state.get('connectPending')is False and state.get('authorityRestorable')is False and native.get('phase')=='NO_SESSION'and native.get('authorityRestorable')is False,'STATUS_TRANSITION_NO_NATIVE_OWNER')
  need(native.get('flight',{}).get('armed')is not True and input_state.get('consent')is not True and input_state.get('leaseId')is None and native.get('rcOverrideActiveLocally')is not True,'STATUS_TRANSITION_NO_ARM_OR_INPUT')
 def _socket_request(self,body=None,*,context=None,deadline_ns=None,timing):
  from .status15_wire import request_bytes
  from .once_reader import read_ref,unique
  need(self.requests<900,'DECLARED_CAMPAIGN900_REQUEST_ENVELOPE');self.device.budget.tick('requests');timing.point('reserved')
  request=dict(body or{});request.setdefault('version',1);request.setdefault('requestNonce',secrets.token_hex(16));wire=request_bytes(request);sent=self.now();deadline=min(sent+10_000_000_000,deadline_ns or sent+10_000_000_000);channel=self.device.status_socket;observer=self.device.observer;frame=None;result=None
  need(observer is not None and observer.busy.acquire(blocking=False),'ONE_ACK_REQUEST_AT_A_TIME')
  channel.sent_prefix=bytearray();channel.last_prefix=b'';exchange_attempted=False
  try:
   marker=observer.expect_native_marker(request['requestNonce']);exchange_attempted=True;frame=channel.exchange(request,deadline,timing)
   barrier_ref,barrier_ns=observer.join_native_marker(marker,deadline);ack=None
   for row in observer.rows_until(deadline):
    if row.get('requestNonce')==request['requestNonce']:ack=row;break
   need(ack is not None,'STATUS15_MATCHING_ORIGINAL_LIVE_ACK');ack_ref=observer.last_ref;original_ack=read_ref(self.device.store.root,ack_ref)
   need(original_ack==frame['ack'],'STATUS15_SOCKET_ACK_EQUALS_ORIGINAL_LOG_ACK');timing.point('ackJoined');received=self.now();timing.point('validateStart')
   result=validate_native_ack(request,ack,frame['dto'],pid=channel.enrollment['pid'],source=self.source,expected_context=context,host_sent_ns=sent,host_received_ns=received)
   need(result['processEpoch']==channel.enrollment['processEpoch']and result['viewEpoch']==channel.enrollment['viewEpoch'],'STATUS15_SAME_ENROLLED_PROCESS_VIEW')
   need(self.process_epoch is None or result['processEpoch']==self.process_epoch,'PROCESS_RESTART_REQUIRES_NEW_DEVICE_LIFECYCLE');timing.point('validateEnd');timing.point('persistStart')
   need(bytes(channel.sent_prefix)==wire,'STATUS15_COMPLETE_KERNEL_ACCEPTED_REQUEST_BYTES')
   snapshot_ref=self.device.store.blob(frame['dto'],owner='dto');request_wire_ref=self.device.store.command_bytes(wire);ack_header_ref=self.device.store.command_bytes(frame['ackHeader']);socket_ack_ref=self.device.store.command_bytes(frame['ack']);dto_header_ref=self.device.store.command_bytes(frame['dtoHeader']);timing.point('payloadPersisted')
   proof={'format':'aeris-status15-exchange','version':1,'channelOpenRef':channel.open_ref,'sequence':channel.sequence,'requestWireRef':request_wire_ref,'ackHeaderRef':ack_header_ref,'socketACKRef':socket_ack_ref,'DTOHeaderRef':dto_header_ref,'snapshotRef':snapshot_ref,'timing':timing.projection(),'frameCompleteBeforeOwnPersistence':True,'socketExchangeNotADBCommand':True}
   socket_ref=self.device.store.status15_proof(proof)
   receipt={'format':'aeris-public-request','version':4,'sequence':self.requests+1,'request':request,'action':'STATUS','hostSentNs':sent,'hostReceivedNs':received,'sourceSHA256':self.source,'context':ack['context'],'expectedContext':context,'actualPID':channel.enrollment['pid'],'barrierRef':barrier_ref,'barrierObservedHostNs':barrier_ns,'ackRef':ack_ref,'snapshotRef':snapshot_ref,'snapshotSHA256':ack['snapshotSHA256'],'snapshotBytes':len(frame['dto']),'rawSnapshotSHA256':ack['snapshotSHA256'],'socketRef':socket_ref}
   need(len(canonical(receipt))+1<=2048,'PUBLIC_STATUS2048_RECEIPT_BOUND');self.last_receipt_ref=self.device.store.receipt('request-%05d.json'%(self.requests+1),receipt,owner='requests');timing.point('requestPersisted');self.requests+=1;self.trace.append(receipt);self._latest_validated_raw=bytes(frame['dto']);self._latest_receipt_bytes=canonical(receipt);self.process_epoch=result['processEpoch'];self.latest=result;self.device.last_snapshot_ref=snapshot_ref;self.device.include_quarantine=result.get('state',{}).get('recovery',{}).get('phase')=='COMPLETE';return result
  except BaseException as error:
   channel.failure=error
   try:
    closing=self.device.budget.snapshot().get('failed')is not None
    request_ref=self.device.store.command_bytes(bytes(channel.sent_prefix),closing=closing);prefix_ref=self.device.store.command_bytes(channel.last_prefix,closing=closing)
    if closing:self.device.store.receipt('status15-failed-prefix.json',{'format':'aeris-status15-failed-prefix','version':1,'channelOpenRef':channel.open_ref,'requestNonce':request['requestNonce'],'requestWireRef':request_ref,'intendedRequestBytes':len(wire),'requestWasFullySent':bytes(channel.sent_prefix)==wire,'exchangeAttempted':exchange_attempted,'channelSequence':channel.sequence,'sendEvidence':'KERNEL_ACCEPTED_BYTES_NOT_REMOTE_RECEIPT','prefixRef':prefix_ref,'failure':str(error)[:256],'uncertainPhysicalDuplicate':frame is not None,'acceptanceEvidence':False},closing=True)
    else:self.device.store.status15_proof({'format':'aeris-status15-failed-prefix','version':1,'channelOpenRef':channel.open_ref,'requestNonce':request['requestNonce'],'requestWireRef':request_ref,'intendedRequestBytes':len(wire),'requestWasFullySent':bytes(channel.sent_prefix)==wire,'exchangeAttempted':exchange_attempted,'channelSequence':channel.sequence,'sendEvidence':'KERNEL_ACCEPTED_BYTES_NOT_REMOTE_RECEIPT','prefixRef':prefix_ref,'failure':str(error)[:256],'uncertainPhysicalDuplicate':frame is not None,'acceptanceEvidence':False})
   except BaseException as preserve:error.add_note('STATUS15_CAPTURE_PREFIX_UNDURABLE:'+str(preserve)[:256]);channel.prefix_undurable=True
   try:self.device.budget.failure(error)
   except BaseException as preserve:error.add_note('STATUS15_FAILURE_RECORD_UNDURABLE:'+str(preserve)[:256])
   raise
  finally:
   observer.busy.release()
 def status(self,*,context=None,deadline_ns=None):return self.request('STATUS',context=context,deadline_ns=deadline_ns)
 def observe_unselected(self,snapshot):
  """Exact inert startup identity; None is never a selected-context waiver."""
  need(not self.stage_attempted and not self.bootstrap_attempted,'UNSELECTED_NO_STAGE_OR_BOOTSTRAP_ATTEMPT')
  need(snapshot is self.latest and self.last_receipt_ref is not None and self.trace and self.trace[-1].get('action')=='STATUS','UNSELECTED_ORIGINAL_FRESH_STATUS_RECEIPT')
  need(type(self._latest_validated_raw)is bytes and type(self._latest_receipt_bytes)is bytes,'UNSELECTED_IMMUTABLE_ORIGINAL_RECEIPT')
  original=json.loads(self._latest_receipt_bytes);need(original['action']=='STATUS'and hashlib.sha256(self._latest_validated_raw).hexdigest()==original['snapshotSHA256']and canonical(snapshot)==canonical(json.loads(self._latest_validated_raw)),'UNSELECTED_EXACT_ORIGINAL_SNAPSHOT_BYTES')
  need(0<=self.now()-original['hostReceivedNs']<=10_000_000_000,'UNSELECTED_FRESH_REQUEST_ACK')
  need('context'in snapshot and 'bootstrapSHA256'in snapshot,'UNSELECTED_EXPLICIT_NULL_CARRIERS')
  need(snapshot.get('sourceSHA256')==self.source and snapshot.get('context')is None and snapshot.get('bootstrapSHA256')is None,'UNSELECTED_SOURCE_NULL_CONTEXT_DESCRIPTOR')
  state=snapshot.get('state',{});n=state.get('native',{})
  need(state.get('connectPending')is False and state.get('ownerActive')is False and state.get('authorityRestorable')is False and n.get('phase')=='NO_SESSION' and n.get('authorityRestorable')is False,'UNSELECTED_ORIGINAL_NO_SESSION_OWNER')
  need(n.get('flight',{}).get('armed')is not True and n.get('input',{}).get('consent')is not True and n.get('input',{}).get('leaseId')is None and n.get('rcOverrideActiveLocally')is not True,'UNSELECTED_NO_ARM_INPUT_OR_LOCAL_RC')
  identity={k:snapshot.get(k)for k in('sourceSHA256','pid','processEpoch','viewEpoch')}
  need(type(identity['pid'])is int and identity['pid']>0 and type(identity['viewEpoch'])is int and identity['viewEpoch']>0 and type(identity['processEpoch'])is str and re.fullmatch('[a-f0-9]{32}',identity['processEpoch'])is not None,'UNSELECTED_TYPED_ORIGINAL_PROCESS_IDENTITY')
  if self._unselected_pin_bytes is None:self._unselected_pin_bytes=canonical(identity);self.unselected_identity=dict(identity)
  need(canonical(identity)==self._unselected_pin_bytes and canonical(self.unselected_identity)==self._unselected_pin_bytes,'UNSELECTED_SAME_ORIGINAL_PID_EPOCH_SOURCE_VIEW')
  return {'identity':dict(identity),'snapshotRevision':snapshot['revision'],'requestReceiptRef':self.last_receipt_ref,'context':None,'bootstrapAttempted':False,'authorityRestored':False}
 def stage(self,status,context,provider,*,survey=None,expected_draft_sha=None,deadline_ns=None):
  self.stage_attempted=True
  need(status['sourceSHA256']==self.source and status['state'].get('ownerActive') is False,'INERT_CURRENT_STATUS')
  need(status['state'].get('viewReady') is True and status['state'].get('presentedView')==status['state'].get('chosenView'),'VISIBLE_CURRENT_VIEW')
  need(status['state'].get('checkpoint',{}).get('phase') in ('READY','RECOVERED_NOT_LIVE_ACK'),'CHECKPOINT_CAN_BIND')
  need((survey is None)!=(expected_draft_sha is None),'NEW_SURVEY_XOR_EXISTING_HASH')
  workspace_projection(status,ready=True)
  body={'version':1,'requestNonce':secrets.token_hex(16),'processEpoch':status['processEpoch'],'viewEpoch':status['viewEpoch'],'baseRevision':status['revision'],'sourceSHA256':self.source,'context':context,'provider':provider,'survey':survey,'expectedDraftSHA256':expected_draft_sha}
  self._stage_deadline=min(deadline_ns or self.now()+10_000_000_000,self.now()+10_000_000_000)
  boundary=self._begin_bootstrap_transport(status)
  result=self.request('BOOTSTRAP',body,context=context,deadline_ns=self._stage_deadline)
  need(result.get('lifecycle',{}).get('phase')=='READY' and result['state'].get('ownerActive') is False,'READY_IS_STAGED_NOT_CONNECTED')
  workspace=result['state']['workspace'];draft=workspace.get('draft');need(type(draft)is dict and type(workspace.get('draftSHA256'))is str and len(workspace['draftSHA256'])==64,'READY_ACTUAL_SAVED_DRAFT')
  if expected_draft_sha is not None:need(workspace['draftSHA256']==expected_draft_sha,'READY_EXACT_EXISTING_DRAFT_SHA')
  else:
   need(type(draft.get('revision'))is int and draft['revision']==1 and draft.get('trainingOnly')is True and draft.get('name')==survey['name'].strip(' '),'READY_NEW_DRAFT_REVISION_NAME')
   for key in ('kind','datum','altitudeDatum','units','geometry','altitudeM','corridorWidthM'):need(draft.get(key)==survey[key] and not isinstance(draft.get(key),bool),'READY_NEW_SURVEY_SEMANTICS_'+key)
  self.stage_committed=True;self.staged_context=dict(context);self.stage_receipt_ref=self.last_receipt_ref
  return self._finish_bootstrap_transport(boundary,result,context,self._stage_deadline)
