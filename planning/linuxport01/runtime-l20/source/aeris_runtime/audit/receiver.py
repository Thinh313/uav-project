"""Fixed production full-raw receiver. Product completion never accepts caller PASS."""
from pathlib import Path
import hashlib,json,re,tarfile
from .oracles import verify_case
from .native_authority import audit as native_audit
from .confirmation import create_confirmation_descriptor
from . import checkpoint
from .window import assisted_window
from .native_chain_json import strict_json
from ..candidate import load,sha,put
from ..identity import validate_native_selection
from ..proofs import need
from ..dependencies import loaded_leaf_origins
from pilot.betaintegrated01.runtime.ap_stage import canonical

def metadata_table(path):
 table={};total=0
 with tarfile.open(path,'r:') as t:
  for ordinal,m in enumerate(t,1):
   need(ordinal<=2048 and not m.issym() and not m.islnk(),'EXPORT_METADATA_MEMBER_BOUND')
   if m.isdir():continue
   need(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts,'EXPORT_METADATA_PATH')
   if m.name.startswith('files/control-runs/'):continue
   need(m.name not in table and m.size<=131072,'EXPORT_METADATA_DUPLICATE_OR_SIZE');raw=t.extractfile(m).read(m.size+1);total+=len(raw);need(len(raw)==m.size and total<=64*2**20,'EXPORT_METADATA64MiB');table[m.name]=raw
 return table

def parent_receipt(path):
 raw=Path(path).read_bytes();need(len(raw)<=8*2**20,'PARENT_LOG8MiB');matches=[]
 for line in raw.splitlines():
  try:v=json.loads(line)
  except(ValueError,UnicodeError):continue
  if type(v)is dict and 'commitAnchor' in v and 'clockCommitAnchor' in v:matches.append(v)
 need(len(matches)==1,'ONE_ORIGINAL_HOST_PARENT_CLOSURE');return matches[0]
def ap_receipt(path):
 raw=Path(path).read_bytes();need(len(raw)<=8*2**20,'AP_PARENT_LOG8MiB');matches=[]
 for line in raw.splitlines():
  try:v=json.loads(line)
  except(ValueError,UnicodeError):continue
  if type(v)is dict and 'terminalSHA256' in v:matches.append(v)
 need(len(matches)==1,'ONE_ORIGINAL_AP_PARENT_CLOSURE');return matches[0]

def verify_review_links(table,context,source,review_sha):
 path='files/review-links/'+context['run']+'.json';need(path in table,'ORIGINAL_DURABLE_PREFLIGHT_REVIEW_LINK_REQUIRED');raw=table[path];need(0<len(raw)<=131072,'REVIEW_LINK128KiB');link=strict_json(raw)
 need(type(link)is dict and all(link.get(k)==context[k] for k in ('run','epoch','boot','operator','generation','profileId')),'REVIEW_LINK_CURRENT_CONTEXT')
 need(link.get('sourceSHA256')==source==link.get('sourceIdentity',{}).get('sourceSHA256') and link.get('authorityRestorable')is False,'REVIEW_LINK_SOURCE_NO_AUTHORITY')
 review_path='files/workspace03/review-'+context['run']+'-'+review_sha+'.json';need(review_path in table,'DECLARED_REVIEW_FOR_ORIGINAL_LINK');review=strict_json(table[review_path])
 need(canonical(link)==canonical(review.get('preflightContext')),'REVIEW_EXACT_ORIGINAL_PREFLIGHT_LINK')
 return {'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'reviewPath':review_path,'linkMatchesStrictReviewPreflightContext':True}


def verify_public_review_context(snapshot,table,context):
 """Current review reference is checked against full immutable TAR metadata."""
 from ..proofs import workspace_projection,preflight_context_canonical
 p=workspace_projection(snapshot)
 if p.get('format')!='aeris-public-workspace-projection':return None
 matches=[r for r in snapshot['state']['workspace']['reviews']if r['run']==context['run']]
 need(len(matches)<=1,'ONE_PUBLIC_CURRENT_REVIEW_REFERENCE')
 if not matches:return {'currentReviewReferencePublished':False,'fullPrivateReviewStillIndependentlyVerified':True,'fullSourceCacheBytesReconstructed':False}
 ref=matches[0];link_name='files/review-links/'+context['run']+'.json';need(link_name in table,'ORIGINAL_FULL_LINK_FOR_PUBLIC_REF');link=strict_json(table[link_name])
 if ref['status']=='PENDING_NATIVE_TERMINAL_OR_VERIFICATION':
  # This earlier cache entry refers to the original unresolved link summary,
  # never to the later full review and never constitutes acceptance evidence.
  original={'id':context['run'],'run':context['run'],'surveyRevision':link['surveyRevision'],'surveySHA256':link['surveySHA256'],'status':'PENDING_NATIVE_TERMINAL_OR_VERIFICATION','durableLinkSHA256':hashlib.sha256(table[link_name]).hexdigest(),'completionClaim':False,'authorityRestorable':False,'actualImages':0};path=link_name
 else:
  names=[n for n in table if n.startswith('files/workspace03/review-'+context['run']+'-')and n.endswith('.json')];need(len(names)==1,'ONE_FULL_CURRENT_REVIEW_FOR_PUBLIC_REF');path=names[0];original=strict_json(table[path]);original.pop('trajectory',None)
  need(preflight_context_canonical(original.get('preflightContext'))==preflight_context_canonical(link),'PUBLIC_REVIEW_ORIGINAL_FULL_PREFLIGHT_LINK')
 raw=preflight_context_canonical(original)
 need(ref['id']==original['id']and ref['run']==original['run']and ref['status']==original['status']and ref['reviewCacheSHA256']==hashlib.sha256(raw).hexdigest()and ref['reviewCacheBytes']==len(raw),'PUBLIC_REVIEW_REF_EXACT_COMPLETE_CACHED_METADATA')
 return {'currentReviewReferencePublished':True,'referenceSHA256':ref['reviewCacheSHA256'],'referenceBytes':len(raw),'originalMetadataPath':path,'pendingReferenceIsAcceptance':False,'fullSourceCacheBytesReconstructed':False}

class FixedReceiver:
 def __init__(self,candidate_dir,digest,config,device,*,budget=None,health_monitor=None):
  loaded_leaf_origins()
  self.health_monitor=health_monitor
  self.budget=budget or device.budget;self.candidate=Path(candidate_dir);self.digest=digest;self.manifest=load(candidate_dir,digest);self.config=config;self.device=device;self.scenario=config.get('controlScenario')
  need(self.scenario in ('nominal','loss'),'EXPLICIT_SUPPORTED_FAULT_SCENARIO_REQUIRED')
  self.source_pins={k:v for k,v in self.manifest['sourceSHA256'].items() if k.startswith('aeris_runtime/audit/')}
  need(bool(self.source_pins),'IMMUTABLE_SELECTED_AUDIT_REQUIRED')
 def __call__(self,supervisor,terminal,closure):
  load(self.candidate,self.digest);validate_native_selection(self.config,self.candidate);loaded_leaf_origins();context=supervisor.context.value();cfg=self.config
  need(all(cfg[k]==context[k] for k in ('run','epoch','boot')) and supervisor.source==self.manifest['native']['sourceSHA256'],'AUDIT_SELECTED_SOURCE_CONTEXT')
  for name,h in self.source_pins.items():
   p=Path(__file__).resolve().parents[2]/name
   need(p.is_file() and sha(p)==h,'ACTUAL_SELECTED_RECEIVER_CODE')
  from ..once_reader import verify_store
  need(self.device.store is not None,'V3_ONCE_STORE_REQUIRED_FOR_PRODUCT_PASS')
  public_proof=verify_store(self.device.store,source=supervisor.source,expected_context=context,expected_apk=self.manifest['native']['APK_SHA256'])
  need(public_proof['requests']==supervisor.native.requests,'COMPLETE_PUBLIC_REQUEST_RECEIPTS')
  need(public_proof['navigationViews'][:2]==['preflight','fly'],'COLD_ORIGINAL_PREFLIGHT_FLY_NAVIGATION')
  root=supervisor.root;export=self.device.export_private(context['run'],root/'native-closed.tar',deadline_ns=supervisor._deadline());table=metadata_table(export['path']);self.before_restart={k:hashlib.sha256(v).hexdigest()for k,v in table.items() if not k.startswith('files/runtime/')};cp=terminal['state']['checkpoint'];observed=checkpoint.verify_live_carrier(terminal['state'],context,supervisor.source,terminal['viewEpoch'])
  proof=checkpoint.verify(cp,table['files/latest-state.json'],table['files/checkpoint14/status.json'],table[cp['archivePath']],context,supervisor.source,observed_ns=observed);history=checkpoint.verify_history(table,table['files/checkpoint14/status.json']);review_link=verify_review_links(table,context,supervisor.source,cp['reviewSHA256']);public_review_ref=verify_public_review_context(terminal,table,context)
  need(supervisor.home_confirmation is not None,'PRODUCT_ORIGINAL_HOME_BRACKET_REQUIRED');binding=supervisor.provider;launch={k:binding[k] for k in ('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')};descriptor,descriptor_anchor=create_confirmation_descriptor(export['path'],'files/control-runs/'+context['run']+'/',cp['terminalAnchor'],supervisor.home_confirmation,launch)
  rawroot=Path(cfg['evidence']);host=parent_receipt(closure['children']['backend']['stdout']);ap=ap_receipt(closure['children']['ap']['stdout']);need(host.get('run')==ap.get('run')==context['run'] and host.get('epoch')==ap.get('epoch')==context['epoch'] and host.get('boot')==ap.get('boot')==context['boot'],'ORIGINAL_PARENT_CLOSURE_CONTEXT')
  base=verify_case(rawroot,context['run'],context['epoch'],context['boot'],host_anchor=host['commitAnchor'],AP_anchor=ap['terminalSHA256'],transport_anchor=host['transportCommitAnchor'],scenario=self.scenario,native_confirmation=descriptor,confirmedHomeReceiptAnchor=descriptor_anchor,clock_anchor=host['clockCommitAnchor'],source_amendment=cfg['externalRecordingPolicy']['amendmentSHA256'],maximum_seconds=cfg['maximumSeconds'])
  native=native_audit(export['path'],'files/control-runs/'+context['run']+'/',cp['terminalAnchor'],{**binding,'expectedViewEpoch':terminal['viewEpoch']},scenario=self.scenario)
  need(base['status']=='CONTROL_OBSERVATIONS_PASS' and native['status']==('PASS_STREAMED_NATIVE_AUTHORITY_CRC' if self.scenario=='nominal' else 'PASS_LOSS_FAILURE_RETAINED_NATIVE_AUTHORITY_REVOKED'),'FULL_RAW_SEMANTIC_RECEIVERS_PASS')
  window=None
  if self.scenario=='nominal':
   spec=supervisor.assisted_window;need(type(spec)is dict and type(spec.get('startHostNs'))is int and type(spec.get('endHostNs'))is int,'PRODUCT_ORIGINAL_ASSISTED_WINDOW_BOUNDARIES')
   minimum=600_000_000_000 if cfg['maximumSeconds']==760 else(1800_000_000_000 if cfg['maximumSeconds']==1960 else 5_000_000_000);need(spec.get('minimumObservedNs')==minimum and type(spec.get('minimumObservedNs'))is int,'FIXED_ASSISTED_MINIMUM');window=assisted_window(base['wireAudit']['passiveTimeline'],spec['startHostNs'],spec['endHostNs']);need(window['status']=='PASS' and window['hostWindowNs']>=minimum and window['APBootWindowNs']>=minimum and native['secondLeaseProducerWindowNs']>=minimum and native['secondLeaseUptimeWindowNs']>=minimum,'CONTINUOUS_HOST_NATIVE_AND_AP_CLOCKS')
  need(base['fullFrameModelAP']['frames']==host['frames'] and base['fullFrameModelAP']['APCoveredFrames']==host['frames'] and base['fullFrameModelAP']['status']=='EXACT_ADMITTED_FRAME_AND_ORIGINAL_MODEL_BYTES_PASS','EVERY_ORIGINAL_ADMITTED_FRAME')
  lifecycle_proofs=supervisor.life.verify_proofs()
  # Full validators above still replay every original frame/clock/native byte.
  # Keep their bounded certificate and immutable raw references; do not serialize
  # duplicate full timelines/model arrays into a64MiB metadata payload.
  actual_leaf_origins=loaded_leaf_origins()
  def file_ref(path):
   path=Path(path);return {'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size}
  from ..monitor import ResourceMonitor
  need(type(self.health_monitor)is ResourceMonitor,'SOURCE_REAL_RESOURCE_HEALTH_BARRIER_REQUIRED');health_barrier=self.health_monitor.barrier()
  result={'hostHealthBarrier':health_barrier,'format':'aeris-full-raw-audit-summary','version':3,'status':'PASS','scenario':self.scenario,'candidateSHA256':self.digest,'allOriginalRawVerified':True,'allFramesRetained':True,
   'sourceAmendmentSHA256':cfg['externalRecordingPolicy']['amendmentSHA256'],'nativeSourceSHA256':supervisor.source,
   'independentValidation':{'baseStatus':base['status'],'nativeStatus':native['status'],'fullFrameModelAPStatus':base['fullFrameModelAP']['status'],'frames':host['frames'],'APCoveredFrames':base['fullFrameModelAP']['APCoveredFrames'],'lifecycleProofStatus':lifecycle_proofs.get('status'),'originalHistoryVerified':True,'originalReviewLinkVerified':True,'originalCheckpointVerified':True},
   'originalRawRefs':{'rawRoot':str(rawroot),'config':file_ref(rawroot/'run-config.json'),'hostParent':file_ref(closure['children']['backend']['stdout']),'APParent':file_ref(closure['children']['ap']['stdout']),'hostAnchor':host['commitAnchor'],'transportAnchor':host['transportCommitAnchor'],'clockAnchor':host['clockCommitAnchor'],'APAnchor':ap['terminalSHA256'],'nativeExport':export,'nativeTerminalAnchor':cp['terminalAnchor'],'checkpointStatusSHA256':cp['statusSHA256'],'reviewSHA256':cp['reviewSHA256'],'reviewLink':review_link,'lifecycleRoot':str(supervisor.life.root),'lifecycleHead':supervisor.life.journal.head},
   'publicReviewContextReference':public_review_ref,'publicOriginalByteProof':public_proof,'publicStoreRoot':str(self.device.store.root),'assistedWindow':window,'nativeSecondLeaseProducerWindowNs':native.get('secondLeaseProducerWindowNs'),'nativeSecondLeaseUptimeWindowNs':native.get('secondLeaseUptimeWindowNs'),
   'loadedLeafOriginsSHA256':hashlib.sha256(canonical(actual_leaf_origins)).hexdigest(),'oldFailsafeVetoPreserved':True,'betaOrPhysicalHeraClaimed':False}
  encoded=canonical(result)+b'\n';need(len(encoded)<=32768,'AUDIT_COMPACT32KiB_SOURCE_BOUND');path=root/'full-raw-audit.json';self.budget.tick('auditRecords');self.budget.write('audit',path,encoded)
  return {'status':'PASS','allOriginalRawVerified':True,'allFramesRetained':True,'scenario':self.scenario,'auditPath':str(path),'auditSHA256':hashlib.sha256(encoded).hexdigest(),'auditBytes':len(encoded),'candidateSHA256':self.digest,'nativeTerminalAnchor':cp['terminalAnchor']}

 def persistence_after_restart(self,supervisor,snapshot):
  need(hasattr(self,'before_restart'),'ORIGINAL_DURABLE_PRE_RESTART_INVENTORY')
  existing=(supervisor.root/'native-closed.tar').stat().st_size;remaining=192*2**20-existing;need(remaining>0,'EXPORT192MiB_REMAINING')
  export=supervisor.native.device.export_private(supervisor.context.run,supervisor.root/'native-restart-metadata.tar',deadline_ns=supervisor._deadline(),metadata_only=True,maximum_bytes=min(64*2**20,remaining));table=metadata_table(export['path']);after={k:hashlib.sha256(v).hexdigest()for k,v in table.items() if not k.startswith('files/runtime/')}
  need(after==self.before_restart,'ORIGINAL_ALL_CANONICAL_ARCHIVE_STATUS_REVIEW_WORKSPACE_BYTES_AFTER_RESTART')
  public_review_ref=verify_public_review_context(snapshot,table,supervisor.context.value())
  cp=snapshot['state']['checkpoint'];need(cp.get('phase')=='RECOVERED_NOT_LIVE_ACK' and cp.get('authorityRestorable') is False,'RECOVERY_NEVER_RESTORES_LIVE_ACK')
  from ..once_reader import verify_store
  old_cold=verify_store(self.device.store,source=supervisor.source,expected_context=supervisor.context.value(),expected_apk=self.manifest['native']['APK_SHA256'])
  need(old_cold['navigationViews'][:3]==['preflight','fly','review'],'COLD_ORIGINAL_PREFLIGHT_FLY_REVIEW_NAVIGATION')
  cold=verify_store(supervisor.native.device.store,source=supervisor.source,expected_context=None,expected_apk=self.manifest['native']['APK_SHA256'])
  from ..monitor import ResourceMonitor
  need(type(self.health_monitor)is ResourceMonitor,'RESTART_SOURCE_REAL_HEALTH_BARRIER_REQUIRED');health_barrier=self.health_monitor.barrier()
  result={'hostHealthBarrier':health_barrier,'format':'aeris-restart-persistence-summary','version':3,'status':'PASS','retainedFileCount':len(after),'retainedFileSHA256Digest':hashlib.sha256(canonical(after)).hexdigest(),'originalPreRestartFileSHA256Digest':hashlib.sha256(canonical(self.before_restart)).hexdigest(),'metadataExport':export,'allDeclaredHistoryFilesByteExact':True,'rawFullTarDuplicated':False,'publicReviewContextReference':public_review_ref,'newObserverColdProof':cold,'oldObserverPostRestartCommandsColdProof':old_cold,'oldStoreRetained':str(self.device.store.root),'newStoreRoot':str(supervisor.native.device.store.root)}
  raw=canonical(result)+b'\n';need(len(raw)<=16384,'PERSISTENCE_SUMMARY16KiB');self.budget.tick('auditRecords');self.budget.write('audit',supervisor.root/'restart-persistence-proof.json',raw);return result
