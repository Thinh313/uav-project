"""Product mission FSM and owned simulation lifecycle; UI/tests are only clients.

Physical autopilot shutdown is deliberately outside this simulation-only DAG.
Input authority remains exclusively inside the native control owner.
"""
from pathlib import Path
import json,time,threading,re
from contextlib import contextmanager
from .lifecycle import Lifecycle,Context
from .telemetry import CommittedTransportReader
from .proofs import need,native_sealed,evidence_durable
class MissionSupervisor:
 def __init__(self,context,source,root,native,resources,*,admission,verify_evidence,now=time.monotonic_ns,journal=None,campaign=None,mock_mode=False,scenario='nominal',check_live=None,budget=None):
  if not mock_mode:
   from .audit.receiver import FixedReceiver
   if type(verify_evidence) is not FixedReceiver:raise ValueError('FIXED_PRODUCTION_RECEIVER_REQUIRED')
  need(scenario in ('nominal','loss'),'VALIDATED_PRODUCT_SCENARIO');self.scenario=scenario;self.loss_request=None;self.mock_mode=mock_mode;self.home_confirmation=None;self.provider=None;self.assisted_window=None;self.context=context;self.check_live=check_live;self.raw_lock=threading.RLock();self.watch_stop=threading.Event();self.watch_thread=None;self.watch_failure=None;self.root=Path(root);self.source=source;self.native=native;self.resources=resources;self.admission=admission;self.verify_evidence=verify_evidence;self.now=now;self.campaign=campaign;self.life=Lifecycle(self.root,context,source,journal=journal,now=now,budget=budget);self.reader=None;self.incident_cursor=0;self.seal=None;self.ground=None;self.connected_lifetime=False;self.restart_evidence=None;self.prelaunch_native=None;self.stage_attempted=False
 @contextmanager
 def raw_section(self):
  if not self.raw_lock.acquire(timeout=2):raise TimeoutError('ORIGINAL_RAW_WATCH_LOCK2S')
  try:yield
  finally:self.raw_lock.release()
 def _deadline(self):
  self.life.check_guard_observer()
  if self.campaign is None:raise ValueError('ORIGINAL_CAMPAIGN_DEADLINE_REQUIRED')
  self.campaign.check();return self.campaign.deadline_ns
 def prepare(self,launch,provider,*,survey=None,expected_draft_sha=None):
  """Returns PREPARING timings separately from the public native10s handshake."""
  try:
   self.provider=dict(provider)
   self.life.transition('ADMITTING',{'candidateSHA256':self.resources.digest});started=self.now();receipt=self.admission()
   need(receipt.get('admitted') is True and receipt.get('realPriming') is True,'ORIGINAL_RESOURCE_ADMISSION')
   self.life.transition('STARTING',{'admission':receipt,'startedNs':started})
   native_preparation=self.native.prepare_normal(deadline_ns=self._deadline())
   initial=self._await_inert_native_ready(min(self.now()+10_000_000_000,self._deadline()));self.prelaunch_native=self.native.observe_unselected(initial)
   from .proofs import workspace_projection,navigation_measurement,H
   workspace_projection(initial,ready=True)
   need(survey is None and type(expected_draft_sha)is str and H.fullmatch(expected_draft_sha)is not None and initial['state']['workspace'].get('draftSHA256')==expected_draft_sha and initial['state']['checkpoint'].get('bindAvailable')is True,'CURRENT_EXISTING_DRAFT_BEFORE_RESOURCE_DISPATCH')
   navigation_measurement(initial,action='nav-preflight',receipt=self.native.trace[-1],before_tap_ns=self.now())
   self.life._record('INERT_NATIVE_READY_BEFORE_RESOURCE_DISPATCH',self.prelaunch_native)
   resource_receipt=launch(self.resources,self._deadline());resource_receipt['nativePreparation']=native_preparation
   need(resource_receipt.get('backendReady') is True and resource_receipt.get('APReady') is True and resource_receipt.get('actualAPExecutableSHA256')==provider.get('binarySHA256'),'OWNED_RESOURCES_READY_ACTUAL_PROVIDER_AP')
   self.attach_transport(Path(launch.config['evidence'])/'transport-journal');self.start_raw_watch()
   self.life.transition('RESOURCES_READY',resource_receipt);self.life.transition('BOOTSTRAPPING',{'publicDeadlineNs':10_000_000_000,'wholeColdStartClaimed10s':False})
   # Independent resource boot/prime gates have already completed; this10s is only
   # coherent public-native readiness and stage. No stale files supplement it.
   deadline=min(self.now()+10_000_000_000,self._deadline());status=self._await_inert_native_ready(deadline)
   self.stage_attempted=True
   staged=self.native.stage(status,self.context.value(),provider,survey=survey,expected_draft_sha=expected_draft_sha,deadline_ns=deadline)
   self.life.transition('READY',{'snapshotSHA256':self.native.trace[-1]['snapshotSHA256'],'revision':staged['revision'],'processEpoch':staged['processEpoch'],'publicHostReceivedNs':self.native.trace[-1]['hostReceivedNs'],'preparationElapsedNs':self.now()-started,'nativeAuthorityGranted':False})
   return self.snapshot()
  except BaseException as e:
   self.life.fail(e)
   raise
 def _await_inert_native_ready(self,deadline):
  while True:
   status=self.native.status(context=None,deadline_ns=deadline);self.native.observe_unselected(status);state=status['state'];cp=state.get('checkpoint',{})
   if cp.get('phase')in('FAILED','REVIEW_FAILED'):
    reason=cp.get('failure');need(type(reason)is str and 0<len(reason)<=1024,'NATIVE_CHECKPOINT_FAILURE_TYPED')
    raise RuntimeError('NATIVE_CHECKPOINT_FAILED:'+reason)
   if status.get('lifecycle',{}).get('phase')=='FAILED':
    cause=status['lifecycle'].get('failure');raise RuntimeError('NATIVE_INERT_STARTUP_FAILED:'+str(cause))
   if cp.get('phase')in('READY','RECOVERED_NOT_LIVE_ACK')and cp.get('bindAvailable')is False:raise RuntimeError('NATIVE_CHECKPOINT_RETAINED_CAPACITY_EXHAUSTED')
   if state.get('viewReady')is True and state.get('presentedView')==state.get('chosenView') and cp.get('phase')in('READY','RECOVERED_NOT_LIVE_ACK'):return status
   need(self.now()<deadline,'PUBLIC_NATIVE10S');time.sleep(min(.5,max(0,(deadline-self.now())/1e9)))
 def cleanup_failed_preparation(self):
  """Failure-only irreversible ingress fence; never an airborne recovery path."""
  need(self.life.phase=='FAILED','FAILED_PREPARATION_ONLY');need(not self.has_connected_lifetime(),'CONNECTED_LIFETIME_FORBIDS_PREOWNER_ABORT')
  deadline=min(self.now()+60_000_000_000,self._deadline())
  if 'ap' not in self.resources.children:
   return self.resources.abort_preparation({'APNeverDispatched':True,'flightAcceptance':False},deadline_ns=deadline)
  unselected=not self.stage_attempted and not self.native.stage_attempted and not self.native.bootstrap_attempted
  if unselected:need(self.prelaunch_native is not None,'PREBOOTSTRAP_ORIGINAL_UNSELECTED_PRELAUNCH_IDENTITY_REQUIRED')
  else:need(self.native.stage_committed is True and self.native.staged_context==self.context.value(),'UNKNOWN_OR_INCOMPLETE_SELECTION_RETAINS_OWNERSHIP')
  def no_session():
   s=self.native.status(context=None if unselected else self.context.value(),deadline_ns=min(deadline,self.now()+10_000_000_000))
   if unselected:
    identity=self.native.observe_unselected(s);need(identity['identity']==self.prelaunch_native['identity'],'PREBOOTSTRAP_SAME_ORIGINAL_PROCESS_SOURCE')
   state=s['state'];n=state.get('native',{})
   need(state.get('connectPending')is False and state.get('ownerActive')is False and n.get('phase')=='NO_SESSION' and n.get('authorityRestorable')is False and state.get('authorityRestorable')is False,'GENUINE_INITIAL_NATIVE_NO_SESSION')
   need(n.get('flight',{}).get('armed')is not True and n.get('input',{}).get('consent')is not True and n.get('input',{}).get('leaseId')is None,'INITIAL_NATIVE_NO_ARM_OR_AUTHORITY')
   return s
  before=no_session();rawroot=Path(self.resources.children['backend'].argv[-1]).parent
  if self.reader is None:self.attach_transport(rawroot/'transport-journal')
  if self.watch_thread is None:self.start_raw_watch()
  def cleanup_observers():
   self.check_watch();need(not self.watch_stop.is_set(),'FAILURE_CLEANUP_RAW_WATCH_MUST_REMAIN_AVAILABLE')
   if self.check_live is not None:self.check_live()
  def advance():
   raw=(rawroot/'transport-state.json').read_bytes();need(len(raw)<=65536,'TRANSPORT_PROJECTION64KiB')
   complete=self.reader.advance(json.loads(raw));need(not self.reader.native_connection_seen and not self.reader.native_bytes_seen and not self.reader.pending_forward_seen,'NO_NATIVE_CONNECTION_BYTES_PENDING_IN_LIFETIME_RAW');return complete
  cleanup_observers()
  with self.raw_section():
   need(advance(),'COMPLETE_PRE_FENCE_COMMITTED_PREFIX');need(self.reader.cut_requested is None,'NO_PREEXISTING_CUT_FOR_FAILURE_ABORT')
  from .candidate import put
  from pilot.betaintegrated01.runtime.ap_stage import canonical
  import secrets
  n=self.now();request={'run':self.context.run,'epoch':self.context.epoch,'boot':self.context.boot,'action':'CUT_NATIVE_LINK','nonce':secrets.token_hex(16),'hostNs':n}
  self.life.note_failure_detail('FAILURE_ABORT_INGRESS_FENCE',{'purpose':'FAILED_PREOWNER_CLEANUP_NOT_LOSS_ACCEPTANCE','request':request,'beforeSnapshotRevision':before['revision']})
  put(rawroot/'cut-request.json',canonical(request)+b'\n')
  after=None
  while self.now()<deadline:
   self._deadline();cleanup_observers()
   with self.raw_section():
    complete=advance()
    if complete and self.reader.cut_closed_ref is not None:
     fence=self.reader.preowner_fence(request);self.reader.witness.begin_landing(fence['closedRef']['closedHostNs'])
    else:fence=None
   if fence is not None and len(self.reader.witness.groups)==2:
    after=no_session();proof=None
    with self.raw_section():
     if advance() and len(self.reader.witness.groups)==2:
      fence=self.reader.preowner_fence(request);ground=self.reader.witness.proof(self.now())
      need(ground['afterHostNs']==fence['closedRef']['closedHostNs'] and ground['committedPrefix']==fence['committedPrefix'],'SAME_POST_FENCE_PREFIX_AND_FRESH_GROUND')
      proof={'noNativeSessionSourceBound':True,'noNativeConnectionInOriginalCommittedRaw':True,'nativeSnapshotRevision':after['revision'],'processEpoch':after['processEpoch'],'startupSelection':{'unselectedPrebootstrap':unselected,'originalIdentity':self.prelaunch_native['identity']if unselected else None,'beforeRevision':before['revision'],'afterRevision':after['revision'],'context':None if unselected else self.context.value(),'stageAttempted':self.stage_attempted,'bootstrapAttempted':self.native.bootstrap_attempted},'ingressFence':fence,'ground':ground,'originalStartupFailureStillFailed':True}
    if proof is not None:
     cleanup_observers();return self.resources.abort_preparation(proof,deadline_ns=deadline)
   time.sleep(.05)
  raise TimeoutError('INITIAL_RAW_FENCED_GROUND_NOT_PROVEN_KEEP_AP_ALIVE')
 def has_connected_lifetime(self):
  """A host phase failure never erases an original native/raw connection."""
  n=(self.native.latest or {}).get('state',{}).get('native',{})
  original=self.reader is not None and (self.reader.native_connection_seen or self.reader.native_bytes_seen or self.reader.pending_forward_seen)
  return self.connected_lifetime or bool(original) or n.get('run')==self.context.run and n.get('phase')!='NO_SESSION'
 def failed_native_seal(self,snapshot):
  """Failure-only closure proof from exact native50 terminal fields, never PASS.

  ControlSession.fail can durably finish its journal while MissionLifecycle
  reports FAILED. The nominal seal predicate deliberately remains unchanged.
  """
  context=self.context.value();state=snapshot.get('state',{});n=state.get('native',{});j=n.get('journal',{});a=n.get('input',{});lc=n.get('lifecycle',{});mission=snapshot.get('lifecycle',{})
  failure=n.get('firstFailure') or mission.get('failure')
  need(snapshot.get('context')==context and snapshot.get('sourceSHA256')==self.source,'FAILED_SEAL_ORIGINAL_SOURCE_CONTEXT')
  need(mission.get('phase')=='FAILED' and type(failure)is str and 0<len(failure)<=1024,'FAILED_SEAL_TYPED_ORIGINAL_FAILURE')
  need(state.get('ownerActive')is False and state.get('authorityRestorable')is False and n.get('closed')is True and n.get('authorityRestorable')is False,'FAILED_SEAL_OWNER_CLOSED_NO_AUTHORITY')
  need(all(n.get(k)==context[k]for k in('run','epoch','boot','generation')),'FAILED_SEAL_NATIVE_CONTEXT')
  need(j.get('closed')is True and j.get('failed')is False and type(j.get('commitAnchor'))is str and re.fullmatch('[a-f0-9]{64}',j['commitAnchor'])is not None and j.get('run')==context['run'] and j.get('epoch')==context['epoch'],'FAILED_SEAL_ORIGINAL_JOURNAL_CLOSED')
  need(a.get('consent')is False and a.get('leaseId')is None and a.get('authorityRestorable')is False and n.get('rcOverrideActiveLocally')is False,'FAILED_SEAL_REVOKED_NOT_QUEUED')
  closed=lc.get('resourcesClosedNs');observed=snapshot.get('observedElapsedNs')
  need(type(closed)is int and type(observed)is int and 0<=closed<=observed and lc.get('run')==context['run'] and lc.get('generation')==context['generation'] and lc.get('leaseActive')is False and lc.get('leaseId')is None,'FAILED_SEAL_RESOURCES_ORIGINAL_CLOCK_CONTEXT')
  need(type(snapshot.get('pid'))is int and snapshot['pid']>0 and type(snapshot.get('revision'))is int and snapshot['revision']>0 and re.fullmatch('[a-f0-9]{32}',str(snapshot.get('processEpoch')))is not None,'FAILED_SEAL_ORIGINAL_PID_REVISION_EPOCH')
  return {'format':'aeris-failure-only-native-seal','version':1,'nativeJournalAnchor':j['commitAnchor'],'snapshotRevision':snapshot['revision'],'processEpoch':snapshot['processEpoch'],'resourcesClosedNs':closed,'originalFailure':failure,'flightAcceptance':False,'checkpointOrReviewUsedAsSeal':False,'nominalNativeSealClaimed':False}
 def cleanup_failed_connected(self):
  """Only original post-loss ground plus a source-real terminal seal may drain."""
  need(self.life.phase=='FAILED' and self.has_connected_lifetime(),'FAILED_CONNECTED_LIFETIME_REQUIRED')
  need(self.reader is not None,'FAILED_CONNECTED_ORIGINAL_READER_REQUIRED')
  deadline=min(self.now()+60_000_000_000,self._deadline())
  self.check_watch()
  with self.raw_section():
   if not self.mock_mode:need(self.refresh_raw(),'FAILED_CONNECTED_COMPLETE_COMMITTED_PREFIX')
   r=self.reader;failure_fence=getattr(r,'failure_closed_ref',None)
   if failure_fence is not None:
    fence=failure_fence;loss={'kind':'SPONTANEOUS_SOURCE_POST_CLOSE_FENCE','closedRef':fence,'eofRef':fence['eofRef']}
   else:
    need(r.cut_requested is not None and r.cut_accepted is True and r.cut_request_ref is not None and r.cut_accepted_ref is not None and r.cut_closed_ref is not None,'FAILED_CONNECTED_ORIGINAL_CRC_LOSS_CLOSURE_REQUIRED')
    pending=getattr(r,'cut_pending',None);need(type(pending)is dict and pending.get('toAPBytes')==0,'FAILED_CONNECTED_NO_PENDING_NATIVE_TO_AP')
    fence=r.cut_closed_ref;loss={'kind':'EXPLICIT_SOURCE_POST_CLOSE_CUT','request':r.cut_requested,'requestRef':r.cut_request_ref,'acceptedRef':r.cut_accepted_ref,'closedRef':fence}
   need(r.native_connection_seen and r.seq>=fence['sequence'] and r.witness.prefix=={'sequence':r.seq,'sha256':r.head},'FAILED_CONNECTED_LIFETIME_AND_COMPLETE_RAW_PREFIX')
   need(getattr(r,'forward_intent',None)is None and getattr(r,'forward_unknown',False)is False,'FAILED_CONNECTED_NO_UNRESOLVED_SEND')
   boundary=fence['closedHostNs'];r.witness.begin_landing(boundary)
  while True:
   self.check_watch()
   with self.raw_section():
    if not self.mock_mode:need(self.refresh_raw(),'FAILED_CONNECTED_FRESH_GROUND_PREFIX')
    try:
     need(all(v['hostNs']>=boundary for g in r.witness.groups for v in g.values()),'FAILED_CONNECTED_GROUND_AFTER_ORIGINAL_LOSS');self.ground=r.witness.proof(self.now());break
    except ValueError:
     if self.mock_mode or self.now()>=deadline:raise
   self._deadline();time.sleep(.05)
  s=self.native.status(context=self.context.value(),deadline_ns=min(deadline,self.now()+10_000_000_000))
  if s.get('lifecycle',{}).get('phase')=='FAILED':seal=self.failed_native_seal(s)
  else:seal=native_sealed(s,self.context.value())
  need(s.get('sourceSHA256')==self.source,'CONNECTED_ABORT_SOURCE_BOUND_NATIVE_SEAL')
  detail={'originalGround':self.ground,'originalNativeSeal':seal,'originalLossFence':loss,'nativeRequestReceipt':dict(self.native.trace[-1]),'originalStartupOrMissionFailureStillFailed':True,'flightAcceptance':False}
  need(self.life.note_failure_detail('FAILED_CONNECTED_SAFE_DRAIN_PROOF',detail)is not None,'FAILED_CONNECTED_DURABLE_PROOF_BEFORE_DRAIN')
  with self.raw_section():
   if not self.mock_mode:need(self.refresh_raw(),'FAILED_CONNECTED_DRAIN_CURRENT_RAW_PREFIX')
   self.check_watch();self.ground=self.reader.witness.proof(self.now());need(all(v['hostNs']>=boundary for g in self.ground['groups']for v in g.values()),'FAILED_CONNECTED_DRAIN_POST_LOSS_GROUND')
   closure=self.resources.drain(self.ground,seal,deadline_ns=min(deadline,self.now()+20_000_000_000))
  original=self.resources.completed_closure();need(original is closure,'EXACT_COMPLETED_CONNECTED_FAILURE_DRAIN');self.seal=seal;self.close_watch();return closure
 def observe_native(self):
  """Operator CONNECT/consent/mode actions are independently observed, never sent here."""
  self._deadline();self.check_watch();s=self.native.status(context=self.context.value());n=s['state'].get('native',{});flight=n.get('flight',{})
  if s['state'].get('ownerActive')is True or n.get('run')==self.context.run and n.get('phase')!='NO_SESSION':self.connected_lifetime=True
  mission=s.get('lifecycle',{})
  if mission.get('phase')=='FAILED':
   cause=mission.get('failure');error=RuntimeError(cause if type(cause)is str and 0<len(cause)<=1024 else'VERIFIED_NATIVE_MISSION_FAILED_WITHOUT_TYPED_CAUSE')
   self.life.fail(error);self.life.note_failure_detail('NATIVE_MISSION_FAILURE_OBSERVED',{'failure':str(error),'snapshotRevision':s['revision'],'processEpoch':s['processEpoch'],'sourceSHA256':s['sourceSHA256'],'nativeAuthorityInferred':False});raise error
  if self.life.phase=='READY' and s['state'].get('ownerActive') is True:self.life.transition('CONNECTED',{'revision':s['revision'],'processEpoch':s['processEpoch'],'operatorConnected':True})
  if self.life.phase=='CONNECTED' and flight.get('armed') is True:self.life.transition('ARMED',{'revision':s['revision'],'nativeSource':self.source})
  if self.life.phase=='ARMED':
   lease=self.observed_native_lease(s)
   if lease is not None:self.life.transition('ACTIVE',{'revision':s['revision'],'processEpoch':s['processEpoch'],'leaseObservedAtOriginalSnapshot':lease,'hostOrFutureAuthorityGranted':False})
  return s
 def observed_native_lease(self,s):
  state=s.get('state',{});n=state.get('native',{});a=n.get('input',{});f=n.get('flight',{});observed=s.get('observedElapsedNs')
  if state.get('ownerActive')is not True or f.get('armed')is not True or a.get('consent')is not True or a.get('leaseId') is None or a.get('failed')is not False or n.get('firstFailure')is not None:return None
  need(all(n.get(k)==self.context.value()[k] for k in ('run','epoch','boot','generation')),'OBSERVED_LEASE_NATIVE_CONTEXT');need(type(a.get('leaseId'))is str and 0<len(a['leaseId'])<=128 and type(a.get('leaseExpiresNs'))is int and type(observed)is int,'OBSERVED_LEASE_TYPED_CLOCK')
  expires=a['leaseExpiresNs']
  if expires<=observed:return None
  need(expires-observed<=200_000_000,'ORIGINAL_NATIVE_INPUT_LEASE200MS');need(type(a.get('source'))is str and re.fullmatch(r'touch-[a-f0-9-]{36}',a['source'])is not None and self.provider is not None and a.get('provenance')==self.provider['inputProvenance'],'OBSERVED_LEASE_SELECTED_LOCAL_TOUCH_SOURCE')
  return {'leaseId':a['leaseId'],'leaseExpiresNs':expires,'snapshotObservedElapsedNs':observed,'source':a['source'],'inputProvenance':a['provenance'],'currentOrFutureHostAuthorityClaim':False,'nativeInputGuardRemainsAuthoritative':True}
 def begin_assisted_window(self):
  need(self.life.phase=='ACTIVE' and self.assisted_window is None,'ACTIVE_ONE_ASSISTED_WINDOW');s=self.native.status(context=self.context.value());n=s['state']['native'];f=n['flight'];a=n['input']
  need(f.get('armed')is True and f.get('mode')==17 and f.get('landedState')==2 and type(a.get('grants'))is int and a['grants']==2 and a.get('consent')is True and a.get('leaseId')is not None,'EXPLICIT_SECOND_GRANT_AIRBORNE_BRAKE')
  from .acceptance_profile import assisted_contract
  contract=assisted_contract(self.verify_evidence.config['maximumSeconds']);self.assisted_window={'startHostNs':self.now(),'endHostNs':None,'sourceRevision':s['revision'],'minimumObservedNs':contract['minimumObservedNs'],'dwellTargetNs':contract['dwellTargetNs']};self.life._record('ASSISTED_WINDOW_STARTED',self.assisted_window);return dict(self.assisted_window)
 def finish_assisted_window(self):
  need(self.assisted_window is not None and self.assisted_window['endHostNs'] is None,'OPEN_ASSISTED_WINDOW');n=self.now();need(n-self.assisted_window['startHostNs']>=self.assisted_window['dwellTargetNs'],'CONTINUOUS_ASSISTED_DWELL_TARGET');self.assisted_window['endHostNs']=n;self.life._record('ASSISTED_WINDOW_FINISHED',self.assisted_window);return dict(self.assisted_window)
 def progress(self):
  self.check_watch();self._deadline()
  with self.raw_section():
   w=self.reader.witness if self.reader is not None else None
   return {'lifecycle':self.life.snapshot(),'originalPassiveCRCPosition':None if w is None else w.p,'originalPassiveCRCHeartbeat':None if w is None else w.h,'originalPassiveCRCLanded':None if w is None else w.l,'committedPrefix':None if w is None else w.prefix,'assistedWindow':self.assisted_window,'hostObservedNs':self.now(),'authorityMintedOrRenewed':False}
 def begin_home_confirmation(self,displayed_home_hash):
  need(self.life.phase in ('ARMED','ACTIVE') and type(displayed_home_hash) is str and len(displayed_home_hash)==64,'POST_ARM_DISPLAYED_HOME_REQUIRED')
  return {'beforeActionHostNs':self.now(),'run':self.context.run,'epoch':self.context.epoch,'boot':self.context.boot,'generation':self.context.generation,'displayedHomeHash':displayed_home_hash}
 def observed_home_confirmation(self,before):
  need(self.home_confirmation is None,'ONE_EXPLICIT_HOME_CONFIRMATION');s=self.native.status(context=self.context.value());flight=s['state'].get('native',{}).get('flight',{})
  need(flight.get('homeConfirmed') is True and flight.get('postArmHomePending') is False and flight.get('homeHash')==before.get('displayedHomeHash'),'ACTUAL_POST_ARM_HOME_CONFIRMED')
  self.home_confirmation={**before,'afterObservedConfirmedHostNs':self.now()};self.life._record('EXPLICIT_HOME_CONFIRMATION_OBSERVED',self.home_confirmation);return self.home_confirmation
 def landing_requested(self,original_host_ns):
  """Public operator request boundary, not an invented AP command receipt."""
  self._deadline();need(type(original_host_ns) is int and original_host_ns<=self.now(),'ORIGINAL_LAND_REQUEST_CLOCK')
  if self.reader is None:raise ValueError('ORIGINAL_RAW_READER_NOT_ATTACHED')
  self.reader.witness.begin_landing(original_host_ns)
  self.life.transition('LANDING',{'operatorRequestHostNs':original_host_ns,'APCommandExecutionClaimed':False})
 def request_link_loss(self):
  from .candidate import put
  from pilot.betaintegrated01.runtime.ap_stage import canonical
  import secrets
  need(self.scenario=='loss' and self.life.phase=='ACTIVE' and self.reader is not None and self.loss_request is None,'EXPLICIT_LOSS_SCENARIO_ACTIVE_ONCE')
  n=self.now();self.loss_request={k:self.context.value()[k] for k in ('run','epoch','boot')};self.loss_request.update(action='CUT_NATIVE_LINK',nonce=secrets.token_hex(16),hostNs=n)
  self.life._record('INTENTIONAL_LINK_LOSS_REQUEST',self.loss_request);put(self.reader.root.parent/'cut-request.json',canonical(self.loss_request)+b'\n');self.reader.witness.begin_landing(n);self.life.transition('LANDING',{'intentionalLossHostNs':n,'APCommandExecutionClaimed':False,'APKeptAliveUntilOriginalGround':True});return self.loss_request
 def attach_transport(self,journal_root):
  need(self.reader is None,'ONE_ORIGINAL_TRANSPORT_READER');self.reader=CommittedTransportReader(journal_root,self.context.value())
 def inspect_committed_transport(self,projection):
  with self.raw_section():
   self._deadline();need(self.reader is not None,'RAW_READER_REQUIRED');complete=self.reader.advance(projection)
   for incident in self.reader.witness.incidents[self.incident_cursor:]:self.life.incident(incident)
   self.incident_cursor=len(self.reader.witness.incidents);return complete
 def refresh_raw(self):
  raw=(self.reader.root.parent/'transport-state.json').read_bytes();need(len(raw)<=65536,'TRANSPORT_PROJECTION64KiB');return self.inspect_committed_transport(json.loads(raw))
 def start_raw_watch(self):
  need(self.watch_thread is None and self.reader is not None,'ONE_PRODUCT_RAW_WATCH')
  def loop():
   try:
    while not self.watch_stop.wait(.1):
     if self.check_live is not None:self.check_live()
     self.refresh_raw()
   except BaseException as e:self.watch_failure=type(e).__name__+':'+str(e);self.life.fail(self.watch_failure)
  self.watch_thread=threading.Thread(target=loop,name='aeris-original-raw-lifecycle-watch');self.watch_thread.start()
 def check_watch(self):
  self.life.check_guard_observer()
  if self.watch_failure:raise RuntimeError(self.watch_failure)
  if self.watch_thread is not None and not self.watch_thread.is_alive() and not self.watch_stop.is_set():raise RuntimeError('OWNED_RAW_WATCH_DEAD')
 def close_watch(self):
  self.watch_stop.set()
  if self.watch_thread is not None:self.watch_thread.join(timeout=8)
  if self.watch_thread is not None and self.watch_thread.is_alive():raise RuntimeError('OWNED_RAW_WATCH_DID_NOT_CLOSE')
 def await_ground(self):
  need(self.life.phase=='LANDING' and self.reader is not None,'DECLARED_LANDING_OR_INTENTIONAL_LOSS');deadline=min(self.now()+60_000_000_000,self._deadline())
  while self.now()<=deadline:
   self.check_watch()
   with self.raw_section():
    if not self.mock_mode:self.refresh_raw()
    if len(self.reader.witness.groups)==2:
     return self.reader.witness.proof(self.now())
   time.sleep(.05)
  raise TimeoutError('ORIGINAL_TWO_GROUND_GROUPS_NOT_OBSERVED')
 def finalize_nominal(self,*,closure_seconds=60):
  """Drain occurs after grounded+native raw seal, before slow checkpoint/review IO."""
  try:
   self._deadline();need(self.life.phase=='LANDING','LANDING_REQUIRED');need(not self.life.incidents or self.scenario=='loss' and self.loss_request is not None and self.reader.cut_requested==self.loss_request and self.reader.cut_accepted is True,'FAILSAFE_CAUSAL_PHASE_UNKNOWN_BLOCKS_NOMINAL')
   self.ground=self.await_ground();self.life.transition('GROUNDED',self.ground)
   seal_deadline=min(self.now()+60_000_000_000,self._deadline())
   while self.now()<=seal_deadline:
    s=self.native.status(context=self.context.value(),deadline_ns=min(seal_deadline,self.now()+10_000_000_000))
    native=s['state'].get('native',{})
    if (self.scenario=='nominal' and native.get('firstFailure') is not None) or native.get('journal',{}).get('failed') is True:raise RuntimeError('NATIVE_FAILED_BEFORE_SEAL')
    if native.get('closed') is True and native.get('journal',{}).get('closed') is True and s['state'].get('ownerActive')is False and s.get('lifecycle',{}).get('phase')in('NATIVE_SEALED','TERMINAL_DURABLE','REVIEW_READY'):
     self.seal=native_sealed(s,self.context.value());break
    time.sleep(min(.5,max(0,(seal_deadline-self.now())/1e9)))
   need(self.seal is not None,'BOUNDED_ORIGINAL_NATIVE_SEAL_REQUIRED')
   self.life.transition('REVOKED',{'snapshotRevision':s['revision'],'consent':False,'leaseId':None,'authorityRestorable':False})
   self.life.transition('NATIVE_SEALED',self.seal);self.life.transition('DRAINING',{'rawNativeSeal':self.seal,'reviewWaitBeforeAPDrain':False})
   with self.raw_section():
    if not self.mock_mode:need(self.refresh_raw(),'CURRENT_COMMITTED_RAW_PREFIX_REQUIRED')
    self.check_watch();need(not self.life.incidents or self.scenario=='loss','LATE_FAILSAFE_INCIDENT_BLOCKS_NOMINAL');self.ground=self.reader.witness.proof(self.now())
   drain_deadline=min(self.now()+20_000_000_000,self._deadline());closure=self.resources.drain(self.ground,self.seal,deadline_ns=drain_deadline);self.close_watch()
   # Independent strict receivers must replay full AP/model/clock/native chains.
   # Product phase never promotes ACK/file visibility into evidence acceptance.
   deadline=min(self.now()+int(closure_seconds*1e9),self._deadline());terminal=None
   while self.now()<=deadline:
    s=self.native.status(context=self.context.value(),deadline_ns=min(deadline,self.now()+10_000_000_000))
    if s['state'].get('checkpoint',{}).get('reviewStatus')=='FAILED':raise RuntimeError('NATIVE_REVIEW_FAILED')
    state=s['state'];projection=state.get('workspaceProjection',{})
    if state.get('checkpoint',{}).get('reviewStatus')=='DURABLE' and state.get('viewReady')is True and state.get('chosenView')==state.get('presentedView') and projection.get('initialized')is True and projection.get('pendingRefresh')is False and state.get('renderedWorkspaceVersion')==projection.get('version'):terminal=s;break
    time.sleep(min(.5,max(0,(deadline-self.now())/1e9)))
   need(terminal is not None,'BOUNDED_REVIEW_DURABLE_REQUIRED');proof=evidence_durable(terminal,self.context.value());verified=self.verify_evidence(self,terminal,closure)
   need(verified.get('status')=='PASS' and verified.get('allOriginalRawVerified') is True and verified.get('allFramesRetained') is True,'INDEPENDENT_COMPLETE_EVIDENCE')
   self.life.transition('EVIDENCE_DURABLE',{'checkpoint':proof,'receiver':verified,'ownedDrain':closure});self.life.transition('REVIEW_READY',proof);return self.snapshot()
  except BaseException as e:
   self.life.fail(e)
   raise
 def verify_restart_operation(self,device,operation,old_pid):
  """Cold-read original stop/absence command bytes, not callback assertions."""
  from .once_reader import read_ref,unique
  import shlex
  rows=[]
  for key in('stopReceiptRef','absenceReceiptRef'):
   row=json.loads(read_ref(device.store.root,operation[key]),object_pairs_hook=unique)
   need(row.get('format')=='aeris-command' and row.get('captureComplete')is True and row.get('exit')==0 and row.get('failure')is None,'RESTART_ORIGINAL_STOP_ABSENCE_COMMAND_SUCCESS')
   argv=json.loads(read_ref(device.store.root,row['argvRef']),object_pairs_hook=unique)
   need(type(argv)is list and len(argv)==5 and argv[:4]==[device.adb,'-s',device.serial,'shell'],'RESTART_ORIGINAL_COMMAND_OWNER')
   rows.append((row,shlex.split(argv[4]),read_ref(device.store.root,row['stdoutRef'])))
  stop,absent=rows
  expected='if pidof vn.rtr.aeris.mission >/dev/null || kill -0 '+str(old_pid)+' 2>/dev/null; then echo RUNNING; else echo ABSENT; fi'
  need(stop[1]==['am','force-stop','vn.rtr.aeris.mission'] and absent[1]==['sh','-c',expected] and absent[2].strip()==b'ABSENT','ORIGINAL_EXACT_PID_ABSENCE_AFTER_STOP')
  need(all(type(row[0].get(k))is int for row in rows for k in('startedHostNs','endedHostNs')) and stop[0]['startedHostNs']<=stop[0]['endedHostNs']<=absent[0]['startedHostNs']<=absent[0]['endedHostNs'],'RESTART_ORIGINAL_STOP_THEN_ABSENCE_CLOCKS')
  return {'oldPID':old_pid,'originalStopAndAbsenceBytesVerified':True,'absenceCommandEndedHostNs':absent[0]['endedHostNs']}
 def verify_restart(self,restart):
  need(self.life.phase=='REVIEW_READY','REVIEW_BEFORE_RESTART');old=self.native
  need(old.latest is not None and old.trace,'ORIGINAL_REVIEW_REQUEST_BEFORE_RESTART')
  before=old.latest;old_receipt=dict(old.trace[-1]);self.restart_evidence={'format':'aeris-fresh-observer-restart','version':1,'beforeProcessEpoch':before['processEpoch'],'beforePID':before['pid'],'sourceSHA256':self.source,'APKSHA256':old.apk_sha,'beforeStoreRoot':str(old.device.store.root),'beforeRequestReceipt':old_receipt,'authorityRestored':False}
  try:
   closed=old.device.close_observer();receipt=closed.get('receipt',{})if type(closed)is dict else{}
   need(receipt.get('captureComplete')is True and receipt.get('closeErrors')==[] and receipt.get('error')is None and type(closed.get('receiptRef'))is dict,'ORIGINAL_ACK_OBSERVER_DURABLE_EOF_JOIN_REQUIRED')
   from .once_reader import read_ref,unique
   need(json.loads(read_ref(old.device.store.root,closed['receiptRef']),object_pairs_hook=unique)==receipt,'ORIGINAL_DURABLE_OLD_OBSERVER_CLOSE_BYTES')
   self.restart_evidence['oldObserverClosure']=closed;self.life._record('OLD_OBSERVER_CLOSED_BEFORE_RESTART',dict(self.restart_evidence))
   new,operation=restart(old);need(new is not old and new.device is not old.device and new.device.store is not old.device.store and new.device.observer is not old.device.observer,'GENUINE_NEW_DEVICE_STORE_OBSERVER_BRIDGE')
   need(new.latest is None and new.requests==0 and new.process_epoch is None and new.device.sequence>0,'FRESH_BRIDGE_COUNTERS_BEFORE_FIRST_STATUS')
   need(new.device.store.root!=old.device.store.root and new.device.budget is old.device.budget,'NEW_OBSERVER_PATH_SAME_CAMPAIGN_BUDGET')
   self.native=new;self.restart_evidence['restartOperation']=operation
   need(operation.get('oldPID')==before['pid'] and operation.get('oldPIDAbsent')is True and operation.get('absenceReceiptRef')is not None,'ORIGINAL_OLD_PID_ABSENCE_RECEIPT')
   self.restart_evidence['originalRestartCommandProof']=self.verify_restart_operation(new.device,operation,before['pid'])
   s=new.status();need(s['processEpoch']!=before['processEpoch'],'GENUINE_NEW_PROCESS_EPOCH');state=s['state'];cp=state.get('checkpoint',{})
   need(s.get('sourceSHA256')==self.source and new.apk_sha==old.apk_sha,'RESTART_SAME_SOURCE_APK')
   need(s.get('context')is None and state.get('ownerActive')is False and state.get('authorityRestorable')is False and state.get('connectPending')is False and cp.get('phase')=='RECOVERED_NOT_LIVE_ACK','RESTART_NO_AUTHORITY_NO_ACK_RESTORE')
   new_receipt=dict(new.trace[-1]);need(new_receipt['request']['requestNonce']!=old_receipt['request']['requestNonce'] and new_receipt['barrierRef']!=old_receipt['barrierRef'],'NEW_NONCE_AND_ORIGINAL_STREAM_MARKER')
   from .once_reader import reconstruct_requests,verify_store
   cold=verify_store(new.device.store,source=self.source,expected_apk=new.apk_sha);need(cold.get('allOriginalCommandBytesVerified')is True and cold.get('allOriginalRequestAndSnapshotBytesVerified')is True and cold.get('processEpoch')==s['processEpoch'],'INDEPENDENT_FRESH_COMMAND_AND_REQUEST_CHAIN')
   self.restart_evidence['freshObserverColdProof']=cold
   reconstructed=reconstruct_requests(new.device.store.root,[new_receipt],source=self.source,expected_apk=new.apk_sha)
   need(len(reconstructed)==1 and reconstructed[0]==s,'INDEPENDENT_NEW_OBSERVER_ORIGINAL_BYTES')
   self.restart_evidence.update(afterProcessEpoch=s['processEpoch'],afterPID=s['pid'],afterStoreRoot=str(new.device.store.root),afterRequestReceipt=new_receipt)
   persistence=self.verify_evidence.persistence_after_restart(self,s)
   need(persistence.get('status')=='PASS' and persistence.get('allDeclaredHistoryFilesByteExact')is True,'FULL_PERSISTENCE_INDEPENDENT_BYTES')
   self.life.transition('CLOSED',{'persistence':persistence,'freshObserverRestart':dict(self.restart_evidence),'processEpoch':s['processEpoch'],'revision':s['revision'],'historicalEvidenceRetained':True,'authorityRestored':False});return self.life.finish()
  except BaseException as primary:
   self.life.fail(primary);self.life.note_failure_detail('FRESH_OBSERVER_RESTART_FAILED',{'originalAndNewEvidence':self.restart_evidence,'failure':type(primary).__name__+':'+str(primary)[:1024],'authorityRestored':False});raise
 def snapshot(self):return self.life.snapshot()
