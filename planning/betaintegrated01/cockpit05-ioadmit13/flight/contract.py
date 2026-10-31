"""IOAdmit13 pinned native client selection on unchanged Observer11 host/AP policy."""
from pathlib import Path
from importlib import import_module
from functools import lru_cache
import json,hashlib,time,datetime,math
OLD=import_module('planning.betaintegrated01.cockpit05-observer11.flight.contract')
ROOT=OLD.ROOT;PACKAGE='vn.rtr.aeris.cockpitio13';ACTIVITY=PACKAGE+'/.CockpitActivity';BUILD='evidence/betaintegrated01-cockpit05-ioadmit13/native/build-01.json';PROVIDERS=OLD.PROVIDERS;ARTIFACT_RESERVE=OLD.ARTIFACT_RESERVE
NAMESPACE='planning.betaintegrated01.cockpit05-ioadmit13.flight';COMPUTATIONAL=NAMESPACE;FROZEN_COMPUTATIONAL='planning.betaintegrated01.cockpit05-compact10.flight';OBSERVER='planning.betaintegrated01.cockpit05-observer11.adapter';POLICY='planning.betaintegrated01.cockpit05-observer11.runtime.policy';RUNTIME='planning.betaintegrated01.cockpit05-observer11.runtime.backend';SUPERVISOR=OBSERVER+'.ap_supervisor'
EVIDENCE='evidence/betaintegrated01-cockpit05-ioadmit13';E=ROOT/EVIDENCE;TASK_PLANNING=ROOT/'planning/betaintegrated01/cockpit05-ioadmit13'
MANIFEST=E/'host/input-contract01.json';PRIOR_MANIFEST=ROOT/'evidence/betaintegrated01-cockpit05-release12/host/input-contract01.json';PRIOR_SHA='612813ce4cea5724a2e3ca881158e3ea33fe1aaf3d91ba688d02c422a80d312e';PRIOR_SEAL=ROOT/'evidence/betaintegrated01-cockpit05-release12/handoff-final.json';PRIOR_SEAL_SHA='0a1db05549dbd636d031f0482c859a4348c36c6e4b59af3234653cdd0f263897'
GUARDIAN=E/'emulator01';GUARDIAN_SOURCE=Path(__file__).parent/'android_guardian.py';SETUP=E/'android-setup01';FIRST_PRELAUNCH=E/'task-start01.json'
EXPECTED_BUILD_RECEIPT_SHA256='b5474f51d80db87074fac712bab4b5157c9e2c85fa57865fccb783297d04d4f4';PROTOCOL=ROOT/'evidence/betaintegrated01-cockpit05-release12/native/RELEASE-PROTOCOL01.json';IOPROTOCOL=E/'native/IOADMIT-PROTOCOL01.json';CERT_SHA256='3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'
CASES={k:{**v,'run':v['run'].replace('cockpit05-observer11','cockpit05-ioadmit13')}for k,v in OLD.CASES.items()}
sha=OLD.sha

def policy():return import_module(POLICY)
def observer():return import_module(OBSERVER+'.policy')
def build_config(*a,**kw):
 v=policy().build_config(*a,**kw);v['externalNativeClientSelection']=native_selection();validate_native_selection(v);return v
def verify_observer_capture(*a,**kw):return import_module(OBSERVER+'.cold').verify_observer_capture(*a,**kw)
def case_budget(free_bytes=None,maximum_seconds=1960):
 helper=import_module('planning.betaintegrated01.cockpit05-compact10.flight.contract');return helper.with_artifact_budget(policy().case_budget(free_bytes,maximum_seconds))
def task_budget(free_bytes=None,maximum_seconds=1960):return case_budget(free_bytes,maximum_seconds)
def campaign_budget(free_bytes=None):
 v=policy().campaign_budget(free_bytes);v['taskHardPeakBytes']+=ARTIFACT_RESERVE;v['newIsolatedAPKAndArchiveReserve']=ARTIFACT_RESERVE;v['nativeOriginalParts']={'shortJournalAndDiagnostic':160*2**20+256*1024,'longJournalAndDiagnostic':160*2**20+256*1024,'system':int(191.5*2**20)};v['resourceCampaign']='FRESH_IOADMIT13';return v
def expected_context(*a,**kw):return OLD.expected_context(*a,**kw)
def build_receipt():
 p=ROOT/BUILD
 if len(EXPECTED_BUILD_RECEIPT_SHA256)!=64 or sha(p)!=EXPECTED_BUILD_RECEIPT_SHA256:raise ValueError('IOADMIT13_PINNED_NATIVE_BUILD_REQUIRED')
 v=json.loads(p.read_bytes())
 if type(v.get('sourcePins'))is not dict or not v['sourcePins']or not v['apk'].startswith('native/betaintegrated01/cockpitio13/dist/')or v.get('productionSigning')is not False or CERT_SHA256 not in v.get('signature','').lower():raise ValueError('IOADMIT13_BUILD_SHAPE')
 return v
def native_selection():
 r=build_receipt();protocolSHA=sha(PROTOCOL);ioProtocolSHA=sha(IOPROTOCOL)
 if r['sourcePins'].get(str(PROTOCOL.relative_to(ROOT)))!=protocolSHA:raise ValueError('PACKAGED_NATIVE_PROTOCOL_SOURCE_PIN')
 if r['sourcePins'].get(str(IOPROTOCOL.relative_to(ROOT)))!=ioProtocolSHA:raise ValueError('PACKAGED_NATIVE_IOADMISSION_PROTOCOL_SOURCE_PIN')
 return dict(format='aeris-external-native-client-selection',version=1,package=PACKAGE,buildReceipt=BUILD,buildReceiptSHA256=EXPECTED_BUILD_RECEIPT_SHA256,APK_SHA256=r['sha256'],sourceSHA256=r['sourceSHA256'],devCertificateSHA256=CERT_SHA256,selectedNativeSourceSHA256=r['sourcePins'],cancellationProtocolPath=str(PROTOCOL.relative_to(ROOT)),cancellationProtocolSHA256=protocolSHA,inputAdmissionProtocolPath=str(IOPROTOCOL.relative_to(ROOT)),inputAdmissionProtocolSHA256=ioProtocolSHA,inheritedHostPolicySHA256=policy().amendment()['amendmentSHA256'],supersedesOnlyHistoricalNativeAPKChangedLabel=True,historicalNativePinsRemainHistorical=True)
def validate_native_selection(config):
 from pilot.betaintegrated01.runtime.ap_stage import canonical
 policy().validate_recording_policy(config)
 if canonical(config.get('externalNativeClientSelection'))!=canonical(native_selection()):raise ValueError('IOADMIT13_EXACT_NATIVE_CLIENT_SELECTION_REQUIRED')
 return native_selection()
def __getattr__(name):
 if name=='APK_SHA256':return build_receipt()['sha256']
 if name=='SOURCE_SHA256':return build_receipt()['sourceSHA256']
 raise AttributeError(name)
@lru_cache(maxsize=1)
def first_task_clocks():
 v=json.loads(FIRST_PRELAUNCH.read_bytes());n=v.get('hostNs');utc=datetime.datetime.fromisoformat(v['atUTC'])
 if type(n)is not int or n<0 or v.get('maximumSeconds')!=5400 or type(v.get('maximumSeconds'))is not int or v.get('scope')!='IOADMIT13_FRESH_TASK' or utc.utcoffset()!=datetime.timedelta(0):raise ValueError('FRESH13_ROOT_TASK_START_BINDING')
 wall=int(utc.timestamp())*10**9+utc.microsecond*1000
 return n,wall

def absolute_task_deadline():return first_task_clocks()[0]+5400*10**9
def first_wall_ns():return first_task_clocks()[1]
def remaining_task_ns(now_ns=None,wall_seconds=None,wall_ns=None):
 now=time.monotonic_ns()if now_ns is None else now_ns;first,initialWall=first_task_clocks()
 if wall_ns is not None:wall=wall_ns
 elif wall_seconds is not None:
  if type(wall_seconds)not in(int,float)or not math.isfinite(wall_seconds):raise ValueError('WALL_CLOCK_TYPE')
  wall=round(wall_seconds*10**9)
 else:wall=time.time_ns()
 if type(now)is not int or now<first or type(wall)is not int or wall<initialWall:raise ValueError('FRESH13_TASK_CLOCK_REGRESSION')
 if abs((wall-initialWall)-(now-first))>2*10**9:raise ValueError('FRESH13_TASK_WALL_MONOTONIC_GAP')
 return min(absolute_task_deadline()-now,initialWall+5400*10**9-wall)
def selected_plan():
 r=build_receipt()
 return dict(package=PACKAGE,build=BUILD,apk=r['apk'],apkSHA256=r['sha256'],sourceSHA256=r['sourceSHA256'],sourceInputs=len(r['sourcePins']),manifest=str(MANIFEST),guardian=str(GUARDIAN),guardianSource=str(GUARDIAN_SOURCE),setup=str(SETUP),runtime=RUNTIME,policy=POLICY,observer=OBSERVER,supervisor=SUPERVISOR,absoluteTaskDeadlineNs=absolute_task_deadline(),AVDBaseline=str(E/'avd-baseline.json'),originalPrelaunch=str(FIRST_PRELAUNCH))
def validate_plan(p,*,maximum_seconds=None,now_ns=None,wall_seconds=None,wall_ns=None,live=False):
 r=build_receipt()
 expected={'package':PACKAGE,'build':BUILD,'apk':r['apk'],'apkSHA256':r['sha256'],'sourceSHA256':r['sourceSHA256'],'sourceInputs':len(r['sourcePins']),'manifest':str(MANIFEST),'guardian':str(GUARDIAN),'guardianSource':str(GUARDIAN_SOURCE),'setup':str(SETUP),'runtime':RUNTIME,'policy':POLICY,'observer':OBSERVER,'supervisor':SUPERVISOR,'AVDBaseline':str(E/'avd-baseline.json'),'originalPrelaunch':str(FIRST_PRELAUNCH)}
 if type(p)is not dict or set(p)!=set(expected)|{'absoluteTaskDeadlineNs'}or any(type(p[k])is not type(v)or p[k]!=v for k,v in expected.items())or type(p['absoluteTaskDeadlineNs'])is not int or p['absoluteTaskDeadlineNs']!=absolute_task_deadline():raise ValueError('IOADMIT13_CROSS_SELECTOR_MISMATCH')
 if maximum_seconds is not None:
  if type(maximum_seconds)is not int or maximum_seconds not in(180,1960):raise ValueError('CASE_DURATION')
  if remaining_task_ns(now_ns,wall_seconds,wall_ns)<(maximum_seconds+290)*10**9:raise ValueError('TASK_DEADLINE_CASE_PLUS290_REQUIRED')
 elif live and remaining_task_ns(now_ns,wall_seconds,wall_ns)<=25*10**9:raise ValueError('TASK_DEADLINE25S_HEADROOM')
 return p
def validate_release(**kw):
 p=validate_plan(selected_plan(),**kw)
 if sha(ROOT/p['apk'])!=p['apkSHA256']:raise ValueError('INSTALLED_APPROVED_APK02_BYTES')
 return p

def selected_sources():return {str(p.relative_to(ROOT)):sha(p)for p in sorted(Path(__file__).parent.glob('*.py'))}
def build_input_contract(repository=ROOT):
 if Path(repository)!=ROOT:raise ValueError('REPOSITORY')
 validate_release();prior=json.loads(PRIOR_MANIFEST.read_bytes())
 if sha(PRIOR_MANIFEST)!=PRIOR_SHA or sha(PRIOR_SEAL)!=PRIOR_SEAL_SHA:raise ValueError('FROZEN_COMPACT10_MANIFEST_OR_SEAL_DRIFT')
 for group in('sourceSHA256','metadataSHA256'):
  for n,h in prior[group].items():
   if sha(ROOT/n)!=h:raise ValueError('FROZEN567_81_DRIFT:'+n)
 v=json.loads(json.dumps(prior));v['sourceSHA256'].update(policy().source_binding());v['sourceSHA256'].update(build_receipt()['sourcePins']);v['sourceSHA256'].update(selected_sources())
 meta=[PRIOR_MANIFEST,PRIOR_SEAL,FIRST_PRELAUNCH,E/'avd-baseline.json',E/'power-policy01.json',TASK_PLANNING/'TIP.md',TASK_PLANNING/'ADR.md',E/'work-start01.json',Path(__file__).parent/'RUNNER.md',ROOT/'evidence/betaintegrated01-cockpit05-release12/actual-short01/control/all-private-after-restart-SHA.json',ROOT/'evidence/betaintegrated01-cockpit05-release12/actual-short01/control/native-io-diagnostic-export.json',ROOT/BUILD,PROTOCOL,IOPROTOCOL]
 meta.extend(sorted(TASK_PLANNING.glob('ADR-AMENDMENT*.md')))
 for p in meta:v['metadataSHA256'][str(p.relative_to(ROOT))]=sha(p)
 for group in('sourceSHA256','metadataSHA256'):
  for n,h in v[group].items():
   if sha(ROOT/n)!=h:raise ValueError('SELECTED_SOURCE_OR_METADATA_DRIFT:'+n)
 v.update(format='aeris-ioadmit13-selection-closure',releaseSelection=selected_plan(),releaseRevision=1,originalInputManifestSHA256=PRIOR_SHA,absoluteTaskDeadlineNs=absolute_task_deadline(),frozen567_81Preserved=True,runtimeEntryModule=RUNTIME,externalRecordingPolicy=policy().amendment(),externalObserverRecordingPolicy=observer().amendment(),existingPackage12NineFilesUnchanged=True,externalNativeClientSelection=native_selection(),APKSourceSHA256=build_receipt()['sourceSHA256'],apk=build_receipt()['apk'],apkSHA256=build_receipt()['sha256'],package=PACKAGE,activity=ACTIVITY,selectedAPKInputs=len(build_receipt()['sourcePins']),newEvidenceRoot=EVIDENCE,newCasePolicies=CASES,capacity=task_budget(),priorDraftRevisions=[],newActualDraftRevision=1,baselinePolicy='NEW_PACKAGE13_GENUINE_EMPTY_REAL_UI_R1_PRESERVE325_OLD_FILES_AND_SIX_DIAGNOSTICS',freshTaskResourceCampaign='IOADMIT13_DISTINCT_FROM_CLOSED_RELEASE12',old567_81MetadataHistorical=True)
 return v
make_manifest=build_input_contract
def verify_full_inputs():
 validate_release();v=json.loads(MANIFEST.read_bytes())
 if v.get('releaseSelection')!=selected_plan()or v.get('runtimeEntryModule')!=RUNTIME or v.get('externalRecordingPolicy')!=policy().amendment()or v.get('externalObserverRecordingPolicy')!=observer().amendment()or v.get('externalNativeClientSelection')!=native_selection():raise ValueError('IOADMIT13_MANIFEST_SELECTION')
 for group in('sourceSHA256','metadataSHA256'):
  for n,h in v[group].items():
   if sha(ROOT/n)!=h:raise ValueError('SELECTED_SOURCE_DRIFT:'+n)
 return v
if __name__=='__main__':
 v=make_manifest();MANIFEST.open('x').write(json.dumps(v,indent=2)+'\n');print(json.dumps(dict(path=str(MANIFEST),sha256=sha(MANIFEST))))
