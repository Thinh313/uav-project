"""One Root-owned Workbench simulator DAG and bounded physical failure closure.
The product UI/client supplies intents; this owner creates no flight messages.
"""
from pathlib import Path
import hashlib,json,os,secrets,signal,sys,time,threading
from .candidate import load,sha
from .campaign import Campaign
from .inventory import Inventory,capture_avd_baseline
from .metadata_budget import MetadataBudget,encoded
from .diagnostic_job import DiagnosticJob
from .identity import build_config
from .lifecycle import Context
from .monitor import ResourceMonitor,host_power
from .commands import HostCommands
from .resources import OwnedResources,OwnedChild
from .launch import SimulationLauncher
from .android import AndroidDevice
from .product_writer import ProductWriter
from .telemetry import CommittedTransportReader
from .paths import repository
from .policy import case_budget
from .disposal import dispose_resources,stop_owned

def bounded_text(value,maximum):return str(value).encode('utf-8',errors='replace')[:maximum].decode('utf-8',errors='ignore')

def need(v,name):
 if not v:raise RuntimeError('PRODUCT_RUNTIME_'+name)

def event_original_files(root,candidate_sha):
 """Cold source references for the exact committed pre-export event prefix."""
 root=Path(root);journal=root/'reports/runtime-events.jsonl';need(journal.is_file()and not journal.is_symlink(),'EVENT_ORIGINAL_JOURNAL_REQUIRED');need(0<journal.stat().st_size<=128*8192,'EVENT_ORIGINAL_PREFIX_BOUND');raw=journal.read_bytes();need(0<len(raw)<=128*8192 and raw.endswith(b'\n'),'EVENT_ORIGINAL_PREFIX_BOUND');files=[journal];detail_bytes=0;last_host=0
 for ordinal,line in enumerate(raw.splitlines(),1):
  row=json.loads(line);need(encoded(row)==line+b'\n'and set(row)=={'format','version','sequence','hostNs','kind','detailRef','context','candidateSHA256','flightAcceptance'}and row['format']=='aeris-product-runtime-event'and type(row['version'])is int and row['version']==2 and type(row['sequence'])is int and row['sequence']==ordinal and ordinal<=128 and type(row['hostNs'])is int and row['hostNs']>=last_host and type(row['kind'])is str and 0<len(row['kind'])<=64 and row['candidateSHA256']==candidate_sha and row['flightAcceptance']is False,'EVENT_ORIGINAL_ROW_SOURCE');last_host=row['hostNs'];context=row['context'];need(context is None or(type(context)is dict and Context(**context).value()==context),'EVENT_ORIGINAL_CONTEXT');ref=row['detailRef'];expected='reports/runtime-event-%03d-detail.json'%ordinal
  need(type(ref)is dict and set(ref)=={'path','offset','bytes','sha256','writeSequence'}and ref['path']==expected and type(ref['offset'])is int and ref['offset']==0 and type(ref['bytes'])is int and 0<ref['bytes']<=32768 and type(ref['writeSequence'])is int and ref['writeSequence']>0,'EVENT_ORIGINAL_EXACT_DETAIL_REF');path=root/expected;need(path.is_file()and not any(p.is_symlink()for p in[path,*path.parents]),'EVENT_ORIGINAL_DETAIL_REGULAR');need(path.stat().st_size==ref['bytes'],'EVENT_ORIGINAL_DETAIL_SHA_OR_AGGREGATE');body=path.read_bytes();detail_bytes+=len(body);need(len(body)==ref['bytes']and hashlib.sha256(body).hexdigest()==ref['sha256']and detail_bytes<=64*1024,'EVENT_ORIGINAL_DETAIL_SHA_OR_AGGREGATE');payload=json.loads(body);need(encoded(payload)==body and set(payload)=={'format','version','sequence','kind','hostNs','context','candidateSHA256','detail'}and payload['format']=='aeris-product-runtime-event-detail'and type(payload['version'])is int and payload['version']==1 and type(payload['sequence'])is int and type(payload['hostNs'])is int and all(payload[k]==row[k]for k in('sequence','kind','hostNs','context','candidateSHA256')),'EVENT_ORIGINAL_DETAIL_IDENTITY');files.append(path)
 need(set((root/'reports').glob('runtime-event-*-detail.json'))==set(files[1:]),'EVENT_ORIGINAL_UNREFERENCED_DETAIL')
 return files

class WorkbenchRuntime:
 def __init__(self,candidate,digest,*,evidence,planning,spec,seconds=180):
  self.repo=repository();self.candidate=Path(candidate).resolve();self.digest=digest;self.manifest=load(self.candidate,digest)
  need(self.manifest['native'].get('productKind')=='BETASIM_INTEGRATED','SELECTED_NEW_PRODUCT_NOT_LEGACY_M1')
  self.root=Path(evidence).resolve();self.planning=Path(planning).resolve();self.artifacts=self.candidate.parent
  need(self.root.parent==self.repo/'evidence/betarc01'and self.root.name in __import__('aeris_runtime.mission16',fromlist=['SLOTS']).SLOTS and self.planning==self.repo/'planning/betarc01'and self.artifacts==self.repo/'evidence/nativejournal17/candidates','EXPLICIT_SCOPE')
  from .mission16 import nominal_duration
  self.planned_seconds=nominal_duration(self.root.name,seconds)
  self.spec_path=Path(spec).resolve();self.spec_raw=self.spec_path.read_bytes();self.specSHA256=hashlib.sha256(self.spec_raw).hexdigest();self.spec=json.loads(self.spec_raw);self.budget=None;self.campaign=None;self.guardian=None;self.attempt=None;self.case=None;self.parent=os.getppid();self.started=time.monotonic_ns();self.owner_deadline=self.started+1800_000_000_000;self.failure=None;self.events=0;self.closed=False;self.disk_observer=None
 def write(self,name,value,*,closing=False):
  raw=encoded(value);need(len(raw)<=(4096 if closing else 32768),'REPORT_SOURCE_BOUND');need(not closing or name=='owner-terminal.json','ONLY_OWNER_TERMINAL_CLOSURE_REPORT');return self.budget.write('closure'if closing else'external_task',self.root/'reports'/name,raw,closing=closing)
 def event(self,kind,detail=None):
  self.events+=1;need(self.events<=128,'EVENT128_BOUND');host_ns=time.monotonic_ns();name='runtime-event-%03d-detail.json'%self.events;context=None if getattr(self,'case',None)is None else dict(self.case['context'])
  payload={'format':'aeris-product-runtime-event-detail','version':1,'sequence':self.events,'kind':kind,'hostNs':host_ns,'context':context,'candidateSHA256':self.digest,'detail':detail};committed=self.write(name,payload)
  ref={'path':'reports/'+name,'offset':0,'bytes':committed['bytes'],'sha256':committed['sha256'],'writeSequence':committed['writeSequence']}
  row={'format':'aeris-product-runtime-event','version':2,'sequence':self.events,'hostNs':host_ns,'kind':kind,'detailRef':ref,'context':context,'candidateSHA256':self.digest,'flightAcceptance':False}
  return self.budget.append_json('external_task',self.root/'reports/runtime-events.jsonl',row,maximum=8192)
 def check_deadline(self):
  need(os.getppid()==self.parent,'ROOT_PARENT_DIED_REVOKE_ADMISSION');need(time.monotonic_ns()<self.owner_deadline,'AUTONOMOUS_OWNER1800S_CLOSE_BEFORE_ROW_EXHAUSTION')
  if self.campaign:self.campaign.check()
 def bootstrap(self):
  from .pipeline_contract import require_closed_contract,artifact_cap_contract
  need(self.budget is None and not(self.root/'campaign-clock.json').exists(),'ONE_CAMPAIGN_NO_RESET');self.check_deadline();require_closed_contract();artifact_cap_contract(self.manifest)
  need(case_budget(__import__('shutil').disk_usage(self.repo).free,self.planned_seconds)['admitted']is True,'LIVE_SHORT_ADMISSION')
  from .input_roles10 import inputs
  inputs(verify_hashes=True)
  capture_avd_baseline(self.spec['AVD'],self.root/'avd-baseline.json',evidence=self.root,planning=self.planning,artifact_root=self.artifacts)
  inventory=Inventory(self.root,self.planning,self.spec['AVD'],self.root/'avd-baseline.json',artifact_root=self.artifacts);self.budget=MetadataBudget(self.root/'metadata-budget',inventory);admission=self.budget.admit();self.campaign=Campaign.create(self.root/'campaign-clock.json',self.budget);self.attempt=self.campaign.attempt(self.candidate,self.digest)
  from .darwin_disk11 import HostDiskObserver,fixed_paths
  self.disk_observer=HostDiskObserver(self.repo,fixed_paths(self.spec),candidate=self.digest,source=self.manifest['sourceSHA256']['aeris_runtime/darwin_disk11.py']);self.disk_observer.start()
  os.environ.update(AERIS_METADATA_BUDGET=str(self.budget.root),AERIS_RUNTIME_OWNER_PID=str(os.getpid()),AERIS_CANDIDATE_DIR=str(self.candidate),AERIS_CANDIDATE_SHA256=self.digest,AERIS_REPOSITORY_ROOT=str(self.repo),PYTHONPATH=str(self.candidate/'source')+os.pathsep+str(self.repo))
  need(hashlib.sha256(self.spec_path.read_bytes()).hexdigest()==self.specSHA256,'DECLARED_SPEC_BYTES_DRIFT_BEFORE_GUARDIAN')
  self.guardian=DiagnosticJob(self.budget,self.root/'diagnostics/guardian-process');argv=[sys.executable,'-P','-B','-m','aeris_runtime.emulator','--spec',str(self.spec_path),'--root',str(self.root/'guardian'),'--campaign',str(self.root/'campaign-clock.json'),'--evidence',str(self.root),'--planning',str(self.planning),'--avd-baseline',str(self.root/'avd-baseline.json'),'--artifact-root',str(self.artifacts),'--seconds',str(self.planned_seconds)];self.guardian.start(argv)
  end=time.monotonic_ns()+60_000_000_000
  while not(self.root/'guardian/health.sock').exists():
   self.check_deadline();need(self.guardian.process.poll()is None,'GUARDIAN_DIED_BEFORE_ENDPOINT');need(time.monotonic_ns()<end,'GUARDIAN_START60S');time.sleep(.05)
  self.health();self.event('GUARDIAN_READY',{'PID':self.guardian.process.pid,'admission':admission});return admission
 def health(self):
  from .emulator import observe_guardian
  return observe_guardian(self.root/'guardian',self.manifest['sourceSHA256']['aeris_runtime/emulator.py'],budget=self.budget)
 def create_case(self,run,*,seconds):
  self.check_deadline();need(self.case is None,'HOSTISOLATE14_ONE_CASE_DIAGNOSTIC_CHILDREN4');need(type(seconds)is int and seconds==self.planned_seconds,'MISSION16_EXACT_ADMITTED_DURATION');need(case_budget(__import__('shutil').disk_usage(self.repo).free,seconds)['admitted']is True,'LIVE_WHOLE_CASE_ADMISSION')
  context=Context(run,secrets.token_hex(16),secrets.token_hex(16),'ROOT-LAB',secrets.token_hex(16),'WORKBENCH_SIM_V1').value();self.campaign.case(self.attempt['path'],self.digest,context);root=self.root/'sessions'/run
  cfg=build_config(self.candidate,'workbench',run,context['epoch'],context['boot'],root/'raw','nominal',seconds)
  from .product_types import selected_types
  Device,Probe=selected_types(self.manifest)
  device=Device(self.spec['ADB'],'emulator-5582',root/'android-api',budget=self.budget,observer_tag='AERIS_PRODUCT_STATUS');probe=Probe(device,self.manifest)
  resources=OwnedResources(self.candidate,self.digest,root/'processes',budget=self.budget);inventory=Inventory(self.root,self.planning,self.spec['AVD'],self.root/'avd-baseline.json',native=probe,artifact_root=self.artifacts)
  from .host_health import GuardianClient
  guardian=GuardianClient(self.root/'guardian',self.manifest['sourceSHA256']['aeris_runtime/emulator.py'],budget=self.budget);queries=HostCommands(root/'host-queries',self.campaign,budget=self.budget);device.host_query=queries
  monitor=ResourceMonitor(root/'resources',seconds,self.campaign,inventory=inventory,power=host_power,guardian=guardian,budget=self.budget);writer=ProductWriter(self.budget,context);scene=resources.enable_scene(context,root/'raw',self.scene_binding(cfg));writer.scene_source=scene
  self.case={'context':context,'root':root,'config':cfg,'plannedSeconds':seconds,'device':device,'native':probe,'resources':resources,'monitor':monitor,'writer':writer,'companion':None,'launcher':None,'scene':scene,'closed':False,'admissionRevoked':False,'APStarted':False,'monitorClosed':False,'deliveryStartedNs':None,'deliveryDeadlineNs':None,'phase':'CREATED'}
  self.event('CASE_CREATED',{'context':context,'maximumSeconds':seconds});return self.case
 def scene_binding(self,cfg):
  return {'backendSourceSHA256':self.manifest['sourceSHA256']['aeris_runtime/backend.py'],'modelSourceSHA256':cfg['modelSHA256'],'profileSHA256':cfg['expectedConfigSHA256'],'journalPolicySHA256':cfg['externalRecordingPolicy']['amendmentSHA256']}
 def descriptor(self):
  c=self.case;context=c['context'];from_profile=__import__('aeris_runtime.tar_profile_h7',fromlist=['profile']).profile();value= {'format':'aeris-root-workbench-provider','version':1,'context':{k:context[k]for k in('run','epoch','boot','operator','generation')},'runtimeContext':context,'profileId':'WORKBENCH_SIM_V1','nativeTarTransportProfile':from_profile,'candidateSHA256':self.digest,'evidenceRoot':str(self.root),'native':self.manifest['native'],'nativeOnlyScope17':{'format':'aeris-native17-unused-lifecycle-scope','version':1,'APStarted':False,'flightAcceptance':False,'expectedGenerations':2,'expectedInputRecords':0},'journalLifecycle17':{'archiveVerifierSHA256':self.manifest['productInputClosure']['pins']['planning/nativejournal17/archive_verifier17.py'],'tarVerifierSHA256':self.manifest['productInputClosure']['pins']['planning/betarc01/tar_profile_h7/reader.py']},'APSHA256':c['config']['APSHA256'],'modelSHA256':c['config']['modelSHA256'],'configSHA256':c['config']['expectedConfigSHA256'],'endpoint':{'host':'127.0.0.1','port':5961},'rawRoot':str(c['root']/'raw'),'writer':c['writer'].descriptor(),'soleMAVLinkWriter':'WORKBENCH_SIM_SINGLE_FLIGHT_OWNER','rootProxyCreatesMAVLinkMessages':False,'fsyncBeforeForward':True,'rootTransportRelativePath':str((c['root']/'raw/transport-journal').relative_to(self.root)),'sourceContractRef':{'candidateSHA256':self.digest,'sourcePath':'aeris_runtime/foundation/transport.py','sourceSHA256':self.manifest['sourceSHA256']['aeris_runtime/foundation/transport.py'],'proofKind':'SOURCE_FSYNC_BEFORE_FORWARD_COLD_RAW_JOIN_REQUIRED'},'typedParameters':json.loads((self.candidate/'source/aeris_runtime/assets/workbench-profiles/nominal/typed-profile.json').read_bytes())['parameters'],'sceneSourceBinding':self.scene_binding(c['config']),'sceneEnabled':True,'engineeringSelection':c['engineeringSelection'],'inputFreshnessNs':250000000,'inputLeaseNs':200000000,'simulationOnly':True,'authorityRestorable':False}
  if not self.root.name.startswith('g1'):
   value.pop('nativeOnlyScope17');value['journalLifecycle17']['archiveVerifierSHA256']=self.manifest['productInputClosure']['pins']['planning/betarc01/archive/archive_rc01.py']
  return value
 def start_writer(self):
  c=self.case;policy_path=self.candidate/'source/aeris_runtime/assets/media-engineering-selection.json';media_policy=json.loads(policy_path.read_bytes());need(media_policy=={'format':'aeris-explicit-media-profile-policy','version':1,'profileId':'VP8-720P30-V1','decision':'ROOT_L2_ENGINEERING_PROFILE_EXPLICIT_NOT_FALLBACK','requiredVideoForArm':True,'noAutomaticFallback':True},'SOURCE_EXPLICIT_MEDIA_ENGINEERING_POLICY')
  selected={**media_policy,'format':'aeris-explicit-media-profile-selection','context':dict(c['context']),'candidateSHA256':self.digest,'policySHA256':self.manifest['sourceSHA256']['aeris_runtime/assets/media-engineering-selection.json']};name='media-engineering-selection-%02d.json'%self.budget.snapshot()['counters']['cases'];committed=self.write(name,selected);c['engineeringSelection']={k:v for k,v in selected.items()if k not in('candidateSHA256','policySHA256')};c['engineeringSelection']['decisionRef']={'path':'reports/'+name,'sha256':committed['sha256']};c['writer'].start();value=self.descriptor();self.write('product-descriptor-%02d.json'%self.budget.snapshot()['counters']['cases'],value);return value
 def start_companion(self,argv):
  c=self.case;need(c['companion']is None,'ONE_COMPANION_PER_CASE');job=DiagnosticJob(self.budget,self.root/'diagnostics'/('product-'+c['context']['run']));c['companion']=job;job.start(argv);self.event('COMPANION_STARTED',{'pid':job.process.pid});return job
 def planned_native_rollover(self,*,deadline_ns):
  """After scenario's public force-stop, enroll once; never restore any grant."""
  self.check();c=self.case;need(c['phase']in('NATIVE_UI_READY','ROOT_AP_READY')and not c['admissionRevoked'],'ACTIVE_CASE_PLANNED_NATIVE_RESTART');transition=c['native'].prepare_rollover(deadline_ns=deadline_ns);snapshot=c['native'].start(deadline_ns=deadline_ns);registration=c['writer'].register_native_probe(c['native']);self.event('NATIVE_PLANNED_NEW_GENERATION_OBSERVED',{'processEpoch':snapshot['processEpoch'],'keyId':snapshot['input']['producerKeyId'],'rolloverSourceRef':transition['sourceReceiptRef'],'authorityRestored':False});return {'transition':transition,'registration':registration,'requiresPrivateCompanionCommand':'NATIVE_ROLLOVER','authorityRestored':False}
 def start_resources(self,image):
  need(not self.root.name.startswith('g1'),'RC01_NATIVE_GATE_NO_AP')
  c=self.case;need(c['native'].latest is not None and c['native'].latest['sourceSHA256']==self.manifest['native']['sourceSHA256'],'SOURCE_NATIVE_OBSERVATION_BEFORE_ADMISSION');self.check_deadline();c['monitor'].start()
  launcher=SimulationLauncher(c['config'],c['root']/'simulation',image=image,query=c['device'].host_query,check_live=self.check, budget=self.budget);c['launcher']=launcher;receipt=launcher(c['resources'],self.campaign.deadline_ns);c['APStarted']=True;c['phase']='ROOT_AP_READY';
  from .flight_interval import FlightIntervalTracker
  c['flightInterval']=FlightIntervalTracker(c['context']);c['reader']=CommittedTransportReader(c['root']/'raw/transport-journal',c['context'],event_observer=c['flightInterval'].event);c['intervalJob']=None;c['intervalProof']=None;c['intervalError']=None
  def interval_ready(mission):
   need(c['intervalError']is None,'SOURCE_INTERVAL_COLD_JOIN_FAILED:'+str(c['intervalError']));need(c['intervalProof']is not None and c['intervalProof']['missionSHA256']==mission,'SOURCE_INTERVAL_NOT_READY_NO_RETRY');return dict(c['intervalProof'])
  c['writer'].flight_interval_source=interval_ready;
  self.event('ROOT_AP_READY',receipt);return receipt
 def check(self):
  self.check_deadline();c=self.case
  if c is None:return
  need(not c['admissionRevoked'],'COMMAND_ADMISSION_REVOKED')
  c['writer'].check()
  if c['companion']is not None:
   need(c['companion'].process.poll()is None,'PRODUCT_COMPANION_EXIT');c['companion'].output.check()
  if c['monitor']._never_started():self.budget.require_real_actor();self.health();need(self.guardian.process.poll()is None,'GUARDIAN_PREPARATION_EXIT');self.guardian.output.check()
  elif not c['monitorClosed']:c['monitor'].check()
  if c['phase']=='RAW_DRAINED_EXPORT_ALLOWED':self.delivery_check()
  if c['APStarted']and c['phase']!='RAW_DRAINED_EXPORT_ALLOWED':
   state=c['root']/'raw/transport-state.json'
   if state.exists():
    raw=state.read_bytes();need(len(raw)<=65536,'TRANSPORT_PROJECTION64K');c['reader'].advance(json.loads(raw))
   if not(c.get('faultRC01')or{}).get('dispatched'):self.prepare_interval()
  if c['phase']!='RAW_DRAINED_EXPORT_ALLOWED':
   for name in c['resources'].children:c['resources'].require_alive(name)
 def prepare_interval(self):
  c=self.case
  if c.get('intervalJob')is not None or c['flightInterval'].end is None:return
  if c['reader'].witness.prefix!={'sequence':c['reader'].seq,'sha256':c['reader'].head}:return
  path=c['root']/'product/journal/workspace.jsonl'
  if not path.exists()or path.stat().st_size>8*2**20:return
  # Immutable accepted review appears only after the Node flight capture closed.
  # Read-only cold join is off the actor/control thread and never in 200ms RPC.
  from .product_seal import original_rows
  committed=c['writer'].committed_prefix('journal/workspace.jsonl')
  if committed is None:return
  workspace_original,workspace_commit=committed
  _,rows,_=original_rows(workspace_original,'hash','previousHash','seq');reviews=[r['data']for r in rows if r['kind']=='BETA_FLIGHT_REVIEW'and r['data'].get('accepted')is True]
  if not reviews:return
  mission=reviews[-1]['missionSHA256'];prefix=dict(c['reader'].witness.prefix)
  from types import SimpleNamespace
  frozen=SimpleNamespace(root=c['reader'].root,seq=prefix['sequence'],head=prefix['sha256'],witness=SimpleNamespace(prefix=prefix))
  def cold():
   try:c['intervalProof']=c['flightInterval'].proof(frozen,c['root']/'product',mission,workspace_original=workspace_original)
   except BaseException as error:c['intervalError']=type(error).__name__+':'+str(error)[:512]
  c['intervalJob']=threading.Thread(target=cold,name='aeris-cold-flight-interval',daemon=True);c['intervalJob'].start()
 def close_interval(self):
  job=self.case.get('intervalJob')if self.case else None
  if job is not None:job.join(timeout=2);need(not job.is_alive(),'COLD_INTERVAL_THREAD_STILL_ALIVE')
 def await_ground(self,*,seconds=20):
  c=self.case;reader=c['reader'];reader.witness.begin_landing(time.monotonic_ns());end=min(time.monotonic_ns()+int(seconds*1e9),self.campaign.deadline_ns)
  while time.monotonic_ns()<end:
   self.check();raw=(c['root']/'raw/transport-state.json').read_bytes();need(len(raw)<=65536,'TRANSPORT_PROJECTION64K');complete=reader.advance(json.loads(raw))
   if complete and len(reader.witness.groups)==2:return reader.witness.proof(time.monotonic_ns())
   time.sleep(.05)
  raise TimeoutError('ROOT_TWO_FRESH_CRC_GROUND_GROUPS_REQUIRED')
 def drain_flight(self,product_seal):
  c=self.case;need(c['phase']=='ROOT_AP_READY','ONE_DRAIN_AFTER_PRODUCT_SEAL');ground=self.await_ground();normal=c['resources'].drain_workbench(ground,product_seal,deadline_ns=time.monotonic_ns()+60_000_000_000);c['managedDrain']=normal;c['nativeExport']=c['native'].closed_export or c['native'].export_closed(c['resources'],deadline_ns=time.monotonic_ns()+60_000_000_000)
  inp=c['native'].latest['input'];need(inp['closed']is True and inp['configured']is False and inp['pending']is False and inp['journal']['durablyDrained']is True,'SOURCE_NATIVE_NO_INPUT_BEFORE_FLIGHT_MONITOR_CLOSE');monitor=c['monitor'].close();need(monitor.get('durablyDrained')is True,'GENUINE_FLIGHT_MONITOR_DRAIN');c['monitorClosed']=True;c['flightMonitorClosure']=monitor;c['deliveryStartedNs']=time.monotonic_ns();c['deliveryDeadlineNs']=min(self.owner_deadline,self.campaign.deadline_ns,c['deliveryStartedNs']+300_000_000_000);c['phase']='RAW_DRAINED_EXPORT_ALLOWED';c['writer'].delivery_check=self.delivery_check;self.event('FLIGHT_DRAINED_DELIVERY_PHASE_STARTED',{'startedHostNs':c['deliveryStartedNs'],'deadlineHostNs':c['deliveryDeadlineNs'],'originalFlightSeconds':c['plannedSeconds'],'monitorDurablyDrained':True,'deliveryIsNotFlightDuration':True});c['rawExport']=c['writer'].register_closed_raw(c['resources'],c['native']);c['native'].raw_export_reference=c['rawExport'];self.event('SOURCE_RAW_DRAINED_EXPORT_ALLOWED',c['rawExport']);return c['rawExport']
 def delivery_check(self):
  c=self.case;self.check_deadline();need(c is not None and c['phase']=='RAW_DRAINED_EXPORT_ALLOWED'and c['monitorClosed']and c['managedDrain']and c['deliveryDeadlineNs']is not None and time.monotonic_ns()<c['deliveryDeadlineNs'],'SOURCE_BOUNDED_DELIVERY_PHASE300S');self.budget.require_real_actor();self.health();inp=c['native'].latest['input'];need(inp['closed']is True and inp['configured']is False and inp['pending']is False,'SOURCE_DELIVERY_NATIVE_INPUT_REMAINS_CLOSED');need(c['companion']is not None and c['companion'].process.poll()is None,'DELIVERY_COMPANION_ALIVE');c['companion'].output.check();return {'phase':'CLOSED_FLIGHT_BOUNDED_DELIVERY','flightAcceptance':False,'originalFlightGuardUnchanged':True}

 def close_case(self,product_seal):
  c=self.case
  if c['phase']!='RAW_DRAINED_EXPORT_ALLOWED':self.drain_flight(product_seal)
  normal=c['managedDrain'];c['admissionRevoked']=True;c['writer'].begin_close()
  if c['companion']is not None:
   job=c['companion'];child=OwnedChild('product',job.process,list(job.process.args),job.started,'','');stop_owned(child,deadline_ns=time.monotonic_ns()+25_000_000_000);job.wait(time.monotonic_ns()+5_000_000_000)
  self.close_interval();writer=c['writer'].close();native=c['native'].close();monitor=c.get('flightMonitorClosure')or c['monitor'].close();c['closed']=True;c['phase']='DRAINED';result={'status':'CASE_MANAGED_CLOSED_AWAITING_INDEPENDENT_ACCEPTANCE','resources':normal,'writer':writer,'native':native,'monitor':monitor,'flightAcceptance':False};self.write('case-'+c['context']['run']+'-closure.json',result);return result
 def close_native_only(self):
  """No AP exists: positive native/source closure, never a flight drain."""
  c=self.case;need(c is not None and not c['APStarted']and not c['resources'].children and c['phase']=='NATIVE_UI_READY','NATIVE_ONLY_NO_AP_DAG')
  need(c.get('archiveProofRef17')is not None and c.get('nativeCryptoProof')is not None,'FULL_NATIVE_COLD_PROOFS_BEFORE_CLOSE')
  inp=c['native'].latest['input'];need(inp['closed']is True and inp['configured']is False and inp['pending']is False and inp['failed']is False and inp['workerTerminated']is True and inp['journal']['durablyDrained']is True,'ORIGINAL_UNUSED_ACTOR_CLOSED')
  job=c['companion'];need(job is not None,'OWNED_NATIVE_UI_HOST')
  physical=stop_owned(OwnedChild('product',job.process,list(job.process.args),job.started,'',''),deadline_ns=time.monotonic_ns()+25_000_000_000);job.wait(time.monotonic_ns()+5_000_000_000)
  c['companion']=None;writer=c['writer'].close();scene=c['resources'].close_scene();native=c['native'].close();monitor=c['monitor'].close();c['monitorClosed']=True
  need(monitor.get('durablyDrained')is True,'NATIVE_MONITOR_NORMAL_DRAIN');c['closed']=True;c['phase']='NATIVE_MANAGED_CLOSED';c['admissionRevoked']=True
  result={'status':'NATIVE_ONLY_MANAGED_CLOSED_AWAITING_INDEPENDENT_ACCEPTANCE','companion':physical,'writer':writer,'scene':scene,'native':native,'monitor':monitor,'APStarted':False,'APGroundProven':False,'flightAcceptance':False,'authorityRestored':False}
  self.write('native17-case-closure.json',result);return result
 def close_maintenance(self):
  """Cold administration accepts positive no-monitor-actor closure only.
  This is not a normal monitor drain, AP ground proof or flight acceptance.
  """
  c=self.case;need(c is not None and self.root.name in('m101','m102','m201','m202','m303','m401','m402','m501','m502','m601','m602')and not c['APStarted']and not c['resources'].children and c['companion']is None,'MAINTENANCE_EXACT_OWNED_COLD_SCOPE')
  proof=c.get('maintenanceRC01')
  if self.root.name in('m601','m602'):
   from .reconcile_h7 import verify_sdk
   verify_sdk(self,proof)
  elif self.root.name in('m401','m402'):
   from .sdk_only_h5 import verify
   verify(self,proof)
  else:need(type(proof)is dict and proof.get('originalPrivateBytesConserved')is True and proof.get('pendingTransactions')==0 and proof.get('activityStarted')is False,'MAINTENANCE_COLD_ORIGINAL_PROOF')
  need(c['device'].observer.process is None or c['device'].observer.process.poll()is not None,'MAINTENANCE_NO_LIVE_NATIVE_OBSERVER')
  writer=c['writer'].close();scene=c['resources'].close_scene();native=c['native'].close();monitor=c['monitor'].close();m=c['monitor'];p=monitor.get('noActorProof');state=self.budget.snapshot()
  need(monitor.get('format')=='aeris-resource-monitor-closure'and type(monitor.get('version'))is int and monitor['version']==2 and monitor.get('status')=='CLOSED_NO_ACTOR_NOT_ACCEPTANCE'and monitor.get('disposition')=='NOT_STARTED_NO_ACTOR'and monitor.get('failure')is None and monitor.get('durablyDrained')is False and monitor.get('health')is None and monitor.get('guardianOriginalPrefix')is None and monitor.get('APGroundProven')is False and monitor.get('flightAcceptance')is False and monitor.get('authorityRestored')is False,'MAINTENANCE_EXACT_NO_ACTOR_DISPOSITION')
  need(type(p)is dict and p.get('startAttempted')is False and type(p.get('startAttempts'))is int and p['startAttempts']==0 and p.get('startPhase')=='NEVER_ATTEMPTED'and all(p.get(k)is True for k in('healthObjectAbsent','threadObjectAbsent','entryAbsent'))and type(p.get('monitorLeaseClaims'))is int and p['monitorLeaseClaims']==0,'MAINTENANCE_POSITIVE_NO_ACTOR_FIELDS')
  need(m._start_attempted is False and type(m._start_attempts)is int and m._start_attempts==0 and m._start_phase=='NEVER_ATTEMPTED'and m.health is None and m.thread is None and m.entry is None and m.failure is None and m.close_failure is None and m.failure_closure is None and m.done.is_set()and m.closure==monitor,'MAINTENANCE_ORIGINAL_MONITOR_NEVER_STARTED_CLOSED')
  need(p.get('originalBudgetRoot')==str(self.budget.root)and p.get('originalLedgerSourceIdentity')==state['sourceIdentity']and p.get('monitorSourceSHA256')==self.manifest['sourceSHA256']['aeris_runtime/monitor.py']and type(p.get('originalLedgerWrites'))is int and p['originalLedgerWrites']>=0 and type(state.get('writes'))is int and state['writes']>=p['originalLedgerWrites']+1 and type(p.get('constructedHostNs'))is int and type(p.get('observedHostNs'))is int and 0<=p['constructedHostNs']<=p['observedHostNs']<=time.monotonic_ns(),'MAINTENANCE_ORIGINAL_NO_ACTOR_LEDGER_SOURCE_BINDING')
  c['monitorClosed']=True;c['closed']=True;c['phase']='NATIVE_MAINTENANCE_CLOSED';c['admissionRevoked']=True
  result={'status':'SDK_ONLY_ADMINISTRATIVE_CLOSED_AWAITING_ROOT_ACCEPTANCE'if self.root.name in('m401','m402','m501','m502','m601','m602')else'NATIVE_MAINTENANCE_CLOSED_AWAITING_INDEPENDENT_ACCEPTANCE','writer':writer,'scene':scene,'native':native,'monitor':monitor,'monitorStarted':False,'monitorDurableDrainClaimed':False,'monitorDisposition':'NOT_STARTED_NO_ACTOR','activityStarted':False,'APStarted':False,'originalPrivateBytesConserved':True,'flightAcceptance':False,'authorityRestored':False};
  if self.root.name in('m401','m402','m501','m502','m601','m602'):result.update(pendingTransactions='NOT_CLAIMED_SDK_ONLY',noTransactionsCreatedByThisSDKDiagnostic=True)
  self.write('native-maintenance-case-closure.json',result);return result
 def close_sdk_only(self):
  need(self.root.name in('m401','m402','m501','m502','m601','m602'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')
  return self.close_maintenance()
 def persist_ui_failure(self,value):
  raw=encoded(value);need(len(raw)<=32768,'FINAL_UI_FAILURE32KiB');path=self.root/'reports/ui-failure-final.json';receipt=self.budget.write('closure',path,raw,closing=True);self.ui_failure_ref={'path':'reports/ui-failure-final.json','bytes':len(raw),'sha256':receipt['sha256']};return self.ui_failure_ref
 def persist_owner_error(self,trace):
  raw=trace.encode('utf-8');prefix=raw[:16384];path=self.root/'reports/owner-error.txt';ref=self.budget.write('closure',path,prefix,closing=True);self.owner_error_ref={'path':'reports/owner-error.txt','bytes':len(prefix),'sha256':ref['sha256'],'captureComplete':len(raw)<=16384,'originalBytes':len(raw),'truncatedPrefixNotFullTrace':len(raw)>16384};return self.owner_error_ref
 def revoke_failure_ingress(self):
  if getattr(self,'disk_observer',None)is not None:self.disk_observer.retire()
  c=self.case
  if c is not None:
   c['admissionRevoked']=True;c['phase']='FAILED';c['writer'].begin_close()
  return {'admissionRevoked':True,'persistentIO':False,'flightAcceptance':False}
 def fail_case(self,primary):
  """Never blocks waiting for a person after failure. No flight command is sent."""
  self.revoke_failure_ingress();self.failure=str(primary)[:2048];c=self.case;errors=[];results={}
  def step(name,fn):
   try:results[name]=fn()
   except BaseException as error:errors.append({'step':name,'error':type(error).__name__+':'+str(error)[:512]})
  if c is not None:
   c['admissionRevoked']=True;c['phase']='FAILED';step('writer-revoke-ingress',c['writer'].begin_close)
   if c.get('uiDriver')is not None:step('preserve-final-original-ui',lambda:c['uiDriver'].persist_failure(primary))
   if c['companion']is not None and c['companion'].process is not None:
    job=c['companion'];step('stop-command-producer',lambda:stop_owned(OwnedChild('product',job.process,list(job.process.args),job.started,'',''),deadline_ns=time.monotonic_ns()+25_000_000_000));step('command-producer-EOF',lambda:job.wait(time.monotonic_ns()+5_000_000_000))
   step('interval-close',self.close_interval);step('writer-close',c['writer'].close)
   step('simulator-physical-disposal',lambda:dispose_resources(c['resources'],primary_failure=self.failure,admission_revoked=True,deadline_ns=time.monotonic_ns()+30_000_000_000))
   step('native-observer-close',c['native'].close);step('resource-monitor-close',lambda:c['monitor'].close_failed(primary))
  step('guardian-exceptional-disposal',lambda:self.close_guardian(failed=True))
  from .ipc_trace10 import flush_clients
  step('preserve-hosthealth-ipc-client',lambda:flush_clients(self.budget,self.root/'reports/hosthealth-ipc-client.bin'))
  if getattr(self,'disk_observer',None)is not None:
   step('host-disk-observer-stop',self.disk_observer.stop);step('preserve-host-disk-attribution',lambda:self.disk_observer.flush(self.budget,self.root/'reports/host-disk-attribution.bin'))
  from .guardian_cause11 import diagnostic
  guardian_cause=diagnostic(primary)
  result={'status':'FAILED_PHYSICAL_DISPOSAL_RECORDED_NOT_ACCEPTANCE','primaryFailure':self.failure,'results':results,'secondaryErrors':errors,'APGroundProven':False,'flightAcceptance':False,'normalCompletedClosureClaimed':False,'automaticRetry':False}
  terminal={'format':'aeris-product-owner-terminal','version':2,'status':result['status'],'candidateSHA256':self.digest,'primaryFailure':bounded_text(self.failure,768),'guardianCause':guardian_cause,'secondaryErrors':[{'step':e['step'],'error':bounded_text(e['error'],160)}for e in errors[:8]],'APGroundProven':False,'APStarted':False if c is None else c['APStarted'],'normalCompletedClosureClaimed':False,'flightAcceptance':False,'automaticRetry':False,'writerTraceRef':results.get('writer-close',{}).get('traceRef'),'ownerErrorRef':getattr(self,'owner_error_ref',None),'finalOriginalUIRef':getattr(self,'ui_failure_ref',None),'lastCommandRef':None if c is None else c['device'].last_command_ref,'commandRoot':None if c is None else str(c['device'].root.relative_to(self.root)),'guardianClosurePath':'guardian/closure.json','guardianProcessClosurePath':'diagnostics/guardian-process/close.json','cleanupSteps':[{'name':name,'returned':True}for name in results]}
  try:self.write('owner-terminal.json',terminal,closing=True)
  except BaseException as storage:primary.add_note('OWNER_TERMINAL_UNDURABLE:'+type(storage).__name__+':'+str(storage)[:256])
  try:self.budget.failure(primary,detail={'workbenchFailure':result['status'],'secondaryErrors':errors,'APGroundProven':False})
  except BaseException:pass
  return result
 def close_guardian(self,*,failed=False):
  if self.guardian is None:return None
  p=self.guardian.process;need(p is not None,'GUARDIAN_START_UNKNOWN')
  if getattr(self,'disk_observer',None)is not None:self.disk_observer.retire()
  if not failed:
   need(self.case is None or self.case['closed']is True,'CASE_MUST_MANAGED_CLOSE');self.health()
  if p.poll()is None:p.send_signal(signal.SIGUSR1 if failed else signal.SIGTERM)
  result=self.guardian.wait(time.monotonic_ns()+55_000_000_000);self.closed=True
  if not failed:
   from .ipc_trace10 import flush_clients
   flush_clients(self.budget,self.root/'reports/hosthealth-ipc-client.bin')
   if getattr(self,'disk_observer',None)is not None:self.disk_observer.stop();self.disk_observer.flush(self.budget,self.root/'reports/host-disk-attribution.bin')
  return {'physicalClose':result,'exceptional':failed,'flightAcceptance':False}
