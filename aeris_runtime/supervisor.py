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
 def __init__(self,context,source,root,native,resources,*,admission,verify_evidence,now=time.monotonic_ns,journal=None,campaign=None,mock_mode=False,scenario='nominal',check_live=None):
  if not mock_mode:
   from .audit.receiver import FixedReceiver
   if type(verify_evidence) is not FixedReceiver:raise ValueError('FIXED_PRODUCTION_RECEIVER_REQUIRED')
  need(scenario in ('nominal','loss'),'VALIDATED_PRODUCT_SCENARIO');self.scenario=scenario;self.loss_request=None;self.mock_mode=mock_mode;self.home_confirmation=None;self.provider=None;self.assisted_window=None;self.context=context;self.check_live=check_live;self.raw_lock=threading.RLock();self.watch_stop=threading.Event();self.watch_thread=None;self.watch_failure=None;self.root=Path(root);self.source=source;self.native=native;self.resources=resources;self.admission=admission;self.verify_evidence=verify_evidence;self.now=now;self.campaign=campaign;self.life=Lifecycle(self.root,context,source,journal=journal,now=now);self.reader=None;self.incident_cursor=0;self.seal=None;self.ground=None
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
   resource_receipt=launch(self.resources,self._deadline());resource_receipt['nativePreparation']=native_preparation
   need(resource_receipt.get('backendReady') is True and resource_receipt.get('APReady') is True and resource_receipt.get('actualAPExecutableSHA256')==provider.get('binarySHA256'),'OWNED_RESOURCES_READY_ACTUAL_PROVIDER_AP')
   self.attach_transport(Path(launch.config['evidence'])/'transport-journal');self.start_raw_watch()
   self.life.transition('RESOURCES_READY',resource_receipt);self.life.transition('BOOTSTRAPPING',{'publicDeadlineNs':10_000_000_000,'wholeColdStartClaimed10s':False})
   # Independent resource boot/prime gates have already completed; this10s is only
   # coherent public-native readiness and stage. No stale files supplement it.
   deadline=min(self.now()+10_000_000_000,self._deadline());status=self.native.status(deadline_ns=deadline)
   while not (status['state'].get('viewReady') is True and status['state'].get('presentedView')==status['state'].get('chosenView') and status['state'].get('checkpoint',{}).get('phase') in ('READY','RECOVERED_NOT_LIVE_ACK')):
    need(self.now()<deadline,'PUBLIC_NATIVE10S');status=self.native.status(deadline_ns=deadline)
   staged=self.native.stage(status,self.context.value(),provider,survey=survey,expected_draft_sha=expected_draft_sha,deadline_ns=deadline)
   self.life.transition('READY',{'snapshotSHA256':self.native.trace[-1]['snapshotSHA256'],'revision':staged['revision'],'processEpoch':staged['processEpoch'],'publicHostReceivedNs':self.native.trace[-1]['hostReceivedNs'],'preparationElapsedNs':self.now()-started,'nativeAuthorityGranted':False})
   return self.snapshot()
  except BaseException as e:
   self.life.fail(e)
   try:self.cleanup_failed_preparation()
   except BaseException as cleanup_error:self.life.note_failure_detail('PREPARATION_CLEANUP_BLOCKED',{'reason':str(cleanup_error)[:512],'APNotDeclaredGround':True})
   raise
 def cleanup_failed_preparation(self):
  need(self.life.phase=='FAILED','FAILED_PREPARATION_ONLY')
  deadline=min(self.now()+60_000_000_000,self._deadline())
  if 'ap' not in self.resources.children:
   return self.resources.abort_preparation({'APNeverDispatched':True,'flightAcceptance':False},deadline_ns=deadline)
  s=self.native.status(deadline_ns=min(deadline,self.now()+10_000_000_000));n=s['state'].get('native',{})
  need(s['state'].get('ownerActive') is False and n.get('phase')=='NO_SESSION' and n.get('authorityRestorable') is False,'GENUINE_INITIAL_NATIVE_NO_SESSION')
  rawroot=Path(self.resources.children['backend'].argv[-1]).parent
  reader=CommittedTransportReader(rawroot/'transport-journal',self.context.value());reader.witness.begin_landing(self.resources.children['ap'].started_ns)
  while self.now()<deadline:
   projection=json.loads((rawroot/'transport-state.json').read_bytes());reader.advance(projection)
   need(not reader.native_connection_seen and not reader.native_bytes_seen,'NO_NATIVE_CONNECTION_IN_INITIAL_RAW')
   if len(reader.witness.groups)==2:
    ground=reader.witness.proof(self.now());proof={'noNativeSessionSourceBound':True,'noNativeConnectionInOriginalCommittedRaw':True,'nativeSnapshotRevision':s['revision'],'processEpoch':s['processEpoch'],'ground':ground,'originalStartupFailureStillFailed':True};return self.resources.abort_preparation(proof,deadline_ns=deadline)
   time.sleep(.05)
  raise TimeoutError('INITIAL_RAW_GROUND_NOT_PROVEN_KEEP_AP_ALIVE')
 def observe_native(self):
  """Operator CONNECT/consent/mode actions are independently observed, never sent here."""
  self._deadline();self.check_watch();s=self.native.status(context=self.context.value());n=s['state'].get('native',{});flight=n.get('flight',{})
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
  self.assisted_window={'startHostNs':self.now(),'endHostNs':None,'sourceRevision':s['revision'],'minimumObservedNs':1800_000_000_000 if self.verify_evidence.config['maximumSeconds']==1960 else 5_000_000_000,'dwellTargetNs':1802_000_000_000 if self.verify_evidence.config['maximumSeconds']==1960 else 5_000_000_000};self.life._record('ASSISTED_WINDOW_STARTED',self.assisted_window);return dict(self.assisted_window)
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
   need(terminal is not None,'BOUNDED_REVIEW_DURABLE_REQUIRED');proof=evidence_durable(terminal,self.context.value());verified=self.verify_evidence(self,terminal,closure)
   need(verified.get('status')=='PASS' and verified.get('allOriginalRawVerified') is True and verified.get('allFramesRetained') is True,'INDEPENDENT_COMPLETE_EVIDENCE')
   self.life.transition('EVIDENCE_DURABLE',{'checkpoint':proof,'receiver':verified,'ownedDrain':closure});self.life.transition('REVIEW_READY',proof);return self.snapshot()
  except BaseException as e:
   self.life.fail(e)
   try:self.close_watch()
   except BaseException as cleanup:self.life.note_failure_detail('RAW_WATCH_CLOSE_FAILED',{'reason':str(cleanup)[:512]})
   raise
 def verify_restart(self,restart):
  need(self.life.phase=='REVIEW_READY','REVIEW_BEFORE_RESTART');old_process=self.native.latest['processEpoch'];restart();s=self.native.status();need(s['processEpoch']!=old_process,'GENUINE_NEW_PROCESS_EPOCH');state=s['state'];cp=state.get('checkpoint',{})
  need(s.get('context') is None and state.get('ownerActive') is False and state.get('authorityRestorable') is False and cp.get('phase')=='RECOVERED_NOT_LIVE_ACK','RESTART_NO_AUTHORITY_NO_ACK_RESTORE')
  persistence=self.verify_evidence.persistence_after_restart(self,s)
  need(persistence.get('status')=='PASS' and persistence.get('allDeclaredHistoryFilesByteExact')is True,'FULL_PERSISTENCE_INDEPENDENT_BYTES')
  self.life.transition('CLOSED',{'persistence':persistence,'processEpoch':s['processEpoch'],'revision':s['revision'],'historicalEvidenceRetained':True,'authorityRestored':False});return self.life.finish()
 def snapshot(self):return self.life.snapshot()
