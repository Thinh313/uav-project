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

class FixedReceiver:
 def __init__(self,candidate_dir,digest,config,device):
  loaded_leaf_origins()
  self.candidate=Path(candidate_dir);self.digest=digest;self.manifest=load(candidate_dir,digest);self.config=config;self.device=device;self.scenario=config.get('controlScenario')
  need(self.scenario in ('nominal','loss'),'EXPLICIT_SUPPORTED_FAULT_SCENARIO_REQUIRED')
  self.source_pins={k:v for k,v in self.manifest['sourceSHA256'].items() if k.startswith('aeris_runtime/audit/')}
  need(bool(self.source_pins),'IMMUTABLE_SELECTED_AUDIT_REQUIRED')
 def __call__(self,supervisor,terminal,closure):
  load(self.candidate,self.digest);validate_native_selection(self.config,self.candidate);loaded_leaf_origins();context=supervisor.context.value();cfg=self.config
  need(all(cfg[k]==context[k] for k in ('run','epoch','boot')) and supervisor.source==self.manifest['native']['sourceSHA256'],'AUDIT_SELECTED_SOURCE_CONTEXT')
  for name,h in self.source_pins.items():
   p=Path(__file__).resolve().parents[2]/name
   need(p.is_file() and sha(p)==h,'ACTUAL_SELECTED_RECEIVER_CODE')
  root=supervisor.root;export=self.device.export_private(context['run'],root/'native-closed.tar',deadline_ns=supervisor._deadline());table=metadata_table(export['path']);self.before_restart={k:hashlib.sha256(v).hexdigest()for k,v in table.items() if not k.startswith('files/runtime/')};cp=terminal['state']['checkpoint'];observed=checkpoint.verify_live_carrier(terminal['state'],context,supervisor.source,terminal['viewEpoch'])
  proof=checkpoint.verify(cp,table['files/latest-state.json'],table['files/checkpoint14/status.json'],table[cp['archivePath']],context,supervisor.source,observed_ns=observed);history=checkpoint.verify_history(table,table['files/checkpoint14/status.json']);review_link=verify_review_links(table,context,supervisor.source,cp['reviewSHA256'])
  need(supervisor.home_confirmation is not None,'PRODUCT_ORIGINAL_HOME_BRACKET_REQUIRED');binding=supervisor.provider;launch={k:binding[k] for k in ('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')};descriptor,descriptor_anchor=create_confirmation_descriptor(export['path'],'files/control-runs/'+context['run']+'/',cp['terminalAnchor'],supervisor.home_confirmation,launch)
  rawroot=Path(cfg['evidence']);host=parent_receipt(closure['children']['backend']['stdout']);ap=ap_receipt(closure['children']['ap']['stdout']);need(host.get('run')==ap.get('run')==context['run'] and host.get('epoch')==ap.get('epoch')==context['epoch'] and host.get('boot')==ap.get('boot')==context['boot'],'ORIGINAL_PARENT_CLOSURE_CONTEXT')
  base=verify_case(rawroot,context['run'],context['epoch'],context['boot'],host_anchor=host['commitAnchor'],AP_anchor=ap['terminalSHA256'],transport_anchor=host['transportCommitAnchor'],scenario=self.scenario,native_confirmation=descriptor,confirmedHomeReceiptAnchor=descriptor_anchor,clock_anchor=host['clockCommitAnchor'],source_amendment=cfg['externalRecordingPolicy']['amendmentSHA256'],maximum_seconds=cfg['maximumSeconds'])
  native=native_audit(export['path'],'files/control-runs/'+context['run']+'/',cp['terminalAnchor'],{**binding,'expectedViewEpoch':terminal['viewEpoch']},scenario=self.scenario)
  need(base['status']=='CONTROL_OBSERVATIONS_PASS' and native['status']==('PASS_STREAMED_NATIVE_AUTHORITY_CRC' if self.scenario=='nominal' else 'PASS_LOSS_FAILURE_RETAINED_NATIVE_AUTHORITY_REVOKED'),'FULL_RAW_SEMANTIC_RECEIVERS_PASS')
  window=None
  if self.scenario=='nominal':
   spec=supervisor.assisted_window;need(type(spec)is dict and type(spec.get('startHostNs'))is int and type(spec.get('endHostNs'))is int,'PRODUCT_ORIGINAL_ASSISTED_WINDOW_BOUNDARIES')
   minimum=1800_000_000_000 if cfg['maximumSeconds']==1960 else 5_000_000_000;need(spec.get('minimumObservedNs')==minimum and type(spec.get('minimumObservedNs'))is int,'FIXED_ASSISTED_MINIMUM');window=assisted_window(base['wireAudit']['passiveTimeline'],spec['startHostNs'],spec['endHostNs']);need(window['status']=='PASS' and window['hostWindowNs']>=minimum and window['APBootWindowNs']>=minimum and native['secondLeaseProducerWindowNs']>=minimum and native['secondLeaseUptimeWindowNs']>=minimum,'CONTINUOUS_HOST_NATIVE_AND_AP_CLOCKS')
  need(base['fullFrameModelAP']['frames']==host['frames'] and base['fullFrameModelAP']['APCoveredFrames']==host['frames'] and base['fullFrameModelAP']['status']=='EXACT_ADMITTED_FRAME_AND_ORIGINAL_MODEL_BYTES_PASS','EVERY_ORIGINAL_ADMITTED_FRAME')
  lifecycle_proofs=supervisor.life.verify_proofs()
  result={'lifecycleProofAudit':lifecycle_proofs,'status':'PASS','scenario':self.scenario,'allOriginalRawVerified':True,'allFramesRetained':True,'candidateSHA256':self.digest,'base':base,'assistedWindow':window,'native':native,'checkpoint':proof,'history':history,'originalReviewLink':review_link,'originalExport':export,'descriptor':descriptor,'descriptorAnchor':descriptor_anchor,'oldFailsafeVetoPreserved':True,'betaOrPhysicalHeraClaimed':False}

  result['actualLeafModuleOrigins']=loaded_leaf_origins()
  encoded=canonical(result)+b'\n';need(len(encoded)<=64*2**20,'AUDIT_METADATA64MiB_BOUND');path=root/'full-raw-audit.json';put(path,encoded)
  return {'status':'PASS','allOriginalRawVerified':True,'allFramesRetained':True,'scenario':self.scenario,'auditPath':str(path),'auditSHA256':hashlib.sha256(encoded).hexdigest(),'auditBytes':len(encoded),'candidateSHA256':self.digest,'nativeTerminalAnchor':cp['terminalAnchor']}

 def persistence_after_restart(self,supervisor,snapshot):
  need(hasattr(self,'before_restart'),'ORIGINAL_DURABLE_PRE_RESTART_INVENTORY')
  existing=(supervisor.root/'native-closed.tar').stat().st_size;remaining=192*2**20-existing;need(remaining>0,'EXPORT192MiB_REMAINING')
  export=self.device.export_private(supervisor.context.run,supervisor.root/'native-restart-metadata.tar',deadline_ns=supervisor._deadline(),metadata_only=True,maximum_bytes=min(64*2**20,remaining));table=metadata_table(export['path']);after={k:hashlib.sha256(v).hexdigest()for k,v in table.items() if not k.startswith('files/runtime/')}
  need(after==self.before_restart,'ORIGINAL_ALL_CANONICAL_ARCHIVE_STATUS_REVIEW_WORKSPACE_BYTES_AFTER_RESTART')
  cp=snapshot['state']['checkpoint'];need(cp.get('phase')=='RECOVERED_NOT_LIVE_ACK' and cp.get('authorityRestorable') is False,'RECOVERY_NEVER_RESTORES_LIVE_ACK')
  return {'status':'PASS','retainedFileSHA256':after,'originalPreRestartFileSHA256':self.before_restart,'metadataExport':export,'allDeclaredHistoryFilesByteExact':True,'rawFullTarDuplicated':False}
