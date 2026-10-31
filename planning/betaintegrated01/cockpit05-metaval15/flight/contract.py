"""Metadata-only native14 reuse contract, new explicit15 host selection and immutable14 ancestry."""
from pathlib import Path
from importlib import import_module
from functools import lru_cache
import json,hashlib,time,datetime,math,re
IDENTITY=import_module('planning.betaintegrated01.cockpit05-metaval15.native_identity')
ROOT=IDENTITY.ROOT;PACKAGE=IDENTITY.PACKAGE;ACTIVITY=IDENTITY.ACTIVITY;BUILD=IDENTITY.BUILD;PROVIDERS='planning/betaintegrated01/m1cockpit04/native/expected-providers01.json';ARTIFACT_RESERVE=4*2**20
NAMESPACE='planning.betaintegrated01.cockpit05-metaval15.flight';COMPUTATIONAL=NAMESPACE;FROZEN_COMPUTATIONAL='planning.betaintegrated01.cockpit05-compact10.flight';OBSERVER='planning.betaintegrated01.cockpit05-metaval15.adapter';POLICY='planning.betaintegrated01.cockpit05-metaval15.runtime.policy';RUNTIME='planning.betaintegrated01.cockpit05-metaval15.runtime.backend';SUPERVISOR=OBSERVER+'.ap_supervisor'
EVIDENCE='evidence/betaintegrated01-cockpit05-metaval15';E=ROOT/EVIDENCE;TASK_PLANNING=ROOT/'planning/betaintegrated01/cockpit05-metaval15'
MANIFEST=E/'host/input-contract01.json';PRIOR_MANIFEST=ROOT/'evidence/betaintegrated01-cockpit05-clockterm14/host/input-contract01.json';PRIOR_SHA='2fbb5675da63d95eba863773dac89e1afa94d9536d5abc4166daf99feea21f62';PRIOR_SEAL=ROOT/'evidence/betaintegrated01-cockpit05-clockterm14/handoff-final.json';PRIOR_SEAL_SHA='aeac6cdc717f65b22ae716eb9254cf151990bebe19fcbc3b502ef0f30145d717'
GUARDIAN=E/'emulator01';GUARDIAN_SOURCE=Path(__file__).parent/'android_guardian.py';SETUP=E/'android-setup01';FIRST_PRELAUNCH=E/'task-start01.json'
EXPECTED_BUILD_RECEIPT_SHA256=IDENTITY.EXPECTED_BUILD_RECEIPT_SHA256;PROTOCOL=IDENTITY.PROTOCOL;IOPROTOCOL=IDENTITY.IOPROTOCOL;TERMINAL_PROTOCOL=IDENTITY.TERMINAL_PROTOCOL;CERT_SHA256=IDENTITY.CERT_SHA256
CASES={'short':{'directory':'actual-short01','run':'cockpit05-metaval15-short-01','maximumSeconds':180,'holdSeconds':5},'long':{'directory':'actual-combined01','run':'cockpit05-metaval15-combined-01','maximumSeconds':1960,'holdSeconds':1802}}
sha=IDENTITY.sha

def policy():return import_module(POLICY)
def observer():return import_module(OBSERVER+'.policy')
def build_config(*a,**kw):
 v=policy().build_config(*a,**kw);v['externalNativeClientSelection']=native_selection();validate_native_selection(v);return v
def verify_observer_capture(*a,**kw):return import_module(OBSERVER+'.cold').verify_observer_capture(*a,**kw)
def case_budget(free_bytes=None,maximum_seconds=1960):
 b=json.loads(json.dumps(policy().case_budget(free_bytes,maximum_seconds)));b['categories']['newIsolatedAPKAndArchiveReserve']=ARTIFACT_RESERVE;b['taskHardPeakBytes']+=ARTIFACT_RESERVE;b['requiredFreeBytes']+=ARTIFACT_RESERVE;b['admitted']=None if b['actualFreeBytes']is None else b['actualFreeBytes']>=b['requiredFreeBytes'];b['nativeDiagnosticExportPerCaseBytes']=256*1024;b['nativeExportCapBytes']-=256*1024;return b
def task_budget(free_bytes=None,maximum_seconds=1960):return case_budget(free_bytes,maximum_seconds)
def campaign_budget(free_bytes=None):
 v=policy().campaign_budget(free_bytes);v['taskHardPeakBytes']+=ARTIFACT_RESERVE;v['newIsolatedAPKAndArchiveReserve']=ARTIFACT_RESERVE;v['nativeOriginalParts']={'shortJournalAndDiagnostic':160*2**20+256*1024,'longJournalAndDiagnostic':160*2**20+256*1024,'system':int(191.5*2**20)};v['resourceCampaign']='FRESH_METAVAL15';return v
def expected_context(run,epoch,boot,generation,operator,variant='nominal',repository=ROOT):
 if variant not in('nominal','loss'):raise ValueError('PROFILE_VARIANT')
 p=json.loads((Path(repository)/PROVIDERS).read_text())['profiles']['M1-COCKPIT04-'+variant.upper()]
 c={'run':run,'epoch':epoch,'boot':boot,'generation':generation,'operator':operator,'profileId':p['profileId'],'binarySHA256':p['binarySHA256'],'configSHA256':p['configSHA256']}
 for key in('run','epoch','boot','generation'):
  if type(c[key])is not str or re.fullmatch(r'[A-Za-z0-9_-]{1,64}',c[key])is None:raise ValueError('LAUNCH_CONTEXT_IDENTIFIER')
 for key in('operator','profileId'):
  if type(c[key])is not str or not 1<=len(c[key])<=128 or any(ord(ch)<32 for ch in c[key]):raise ValueError('LAUNCH_CONTEXT_LABEL')
 for key in('binarySHA256','configSHA256'):
  if type(c[key])is not str or re.fullmatch('[0-9a-f]{64}',c[key])is None:raise ValueError('LAUNCH_CONTEXT_SHA256')
 return c
build_receipt=IDENTITY.build_receipt
native_selection=IDENTITY.native_selection
validate_native_selection=IDENTITY.validate_native_selection
def __getattr__(name):
 if name=='APK_SHA256':return build_receipt()['sha256']
 if name=='SOURCE_SHA256':return build_receipt()['sourceSHA256']
 raise AttributeError(name)
@lru_cache(maxsize=1)
def first_task_clocks():
 v=json.loads(FIRST_PRELAUNCH.read_bytes());n=v.get('hostNs');utc=datetime.datetime.fromisoformat(v['atUTC'])
 if type(n)is not int or n<0 or v.get('maximumSeconds')!=5400 or type(v.get('maximumSeconds'))is not int or v.get('scope')!='METAVAL15_FRESH_TASK' or utc.utcoffset()!=datetime.timedelta(0):raise ValueError('FRESH15_ROOT_TASK_START_BINDING')
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
 if type(now)is not int or now<first or type(wall)is not int or wall<initialWall:raise ValueError('FRESH15_TASK_CLOCK_REGRESSION')
 if abs((wall-initialWall)-(now-first))>2*10**9:raise ValueError('FRESH15_TASK_WALL_MONOTONIC_GAP')
 return min(absolute_task_deadline()-now,initialWall+5400*10**9-wall)
def selected_plan():
 r=build_receipt()
 return dict(package=PACKAGE,build=BUILD,apk=r['apk'],apkSHA256=r['sha256'],sourceSHA256=r['sourceSHA256'],sourceInputs=len(r['sourcePins']),manifest=str(MANIFEST),guardian=str(GUARDIAN),guardianSource=str(GUARDIAN_SOURCE),setup=str(SETUP),runtime=RUNTIME,policy=POLICY,observer=OBSERVER,supervisor=SUPERVISOR,absoluteTaskDeadlineNs=absolute_task_deadline(),AVDBaseline=str(E/'avd-baseline.json'),originalPrelaunch=str(FIRST_PRELAUNCH))
def validate_plan(p,*,maximum_seconds=None,now_ns=None,wall_seconds=None,wall_ns=None,live=False):
 r=build_receipt()
 expected={'package':PACKAGE,'build':BUILD,'apk':r['apk'],'apkSHA256':r['sha256'],'sourceSHA256':r['sourceSHA256'],'sourceInputs':len(r['sourcePins']),'manifest':str(MANIFEST),'guardian':str(GUARDIAN),'guardianSource':str(GUARDIAN_SOURCE),'setup':str(SETUP),'runtime':RUNTIME,'policy':POLICY,'observer':OBSERVER,'supervisor':SUPERVISOR,'AVDBaseline':str(E/'avd-baseline.json'),'originalPrelaunch':str(FIRST_PRELAUNCH)}
 if type(p)is not dict or set(p)!=set(expected)|{'absoluteTaskDeadlineNs'}or any(type(p[k])is not type(v)or p[k]!=v for k,v in expected.items())or type(p['absoluteTaskDeadlineNs'])is not int or p['absoluteTaskDeadlineNs']!=absolute_task_deadline():raise ValueError('METAVAL15_CROSS_SELECTOR_MISMATCH')
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
def validate_linux_gate():
 p=E/'linux-gate01.json'
 if p.is_symlink()or not p.is_file()or not 1<=p.stat().st_size<=262144:raise ValueError('METAVAL15_ORIGINAL_LINUX_GATE_METADATA_REQUIRED')
 g=json.loads(p.read_bytes())
 if g.get('status')!='PASS_EXACT_LINUX_METADATA_GATE_NOT_AP_FLIGHT'or type(g.get('APOrClockprobeStarted'))is not bool or g['APOrClockprobeStarted']is not False or type(g.get('networkOrSocketCreated'))is not bool or g['networkOrSocketCreated']is not False or type(g.get('prohibitedEffectAttempts'))is not list or g['prohibitedEffectAttempts']!=[]:raise ValueError('METAVAL15_LINUX_GATE_NOT_EXACT_METADATA_PASS')
 if g.get('hostPolicySHA256')!=policy().amendment()['amendmentSHA256']or g.get('nativeBuildReceiptSHA256')!=EXPECTED_BUILD_RECEIPT_SHA256 or g.get('probeSHA256')!=sha(TASK_PLANNING/'linux_probe.py'):raise ValueError('METAVAL15_LINUX_GATE_ACTUAL_SOURCE_BINDING')
 return g
def build_input_contract(repository=ROOT):
 if Path(repository)!=ROOT:raise ValueError('REPOSITORY')
 validate_linux_gate();validate_release();prior=json.loads(PRIOR_MANIFEST.read_bytes())
 if sha(PRIOR_MANIFEST)!=PRIOR_SHA or sha(PRIOR_SEAL)!=PRIOR_SEAL_SHA:raise ValueError('FROZEN_COMPACT10_MANIFEST_OR_SEAL_DRIFT')
 for group in('sourceSHA256','metadataSHA256'):
  for n,h in prior[group].items():
   if sha(ROOT/n)!=h:raise ValueError('FROZEN675_108_DRIFT:'+n)
 v=json.loads(json.dumps(prior));v['sourceSHA256'].update(policy().source_binding());v['sourceSHA256'].update(build_receipt()['sourcePins']);v['sourceSHA256'].update(selected_sources());v['sourceSHA256'].update({str(p.relative_to(ROOT)):sha(p)for p in TASK_PLANNING.glob('*.py')})
 meta=[PRIOR_MANIFEST,PRIOR_SEAL,FIRST_PRELAUNCH,E/'avd-baseline.json',E/'power-policy01.json',TASK_PLANNING/'TIP.md',TASK_PLANNING/'ADR.md',E/'work-start01.json',Path(__file__).parent/'RUNNER.md',ROOT/'evidence/betaintegrated01-cockpit05-clockterm14/actual-short01/control/all-private-before-case-SHA.json',ROOT/'evidence/betaintegrated01-cockpit05-ioadmit13/root-diagnostic-recovery01.json',ROOT/BUILD,PROTOCOL,IOPROTOCOL,TERMINAL_PROTOCOL,E/'linux-gate01.json',E/'native/native-reuse01.json']
 meta.extend(sorted(TASK_PLANNING.glob('ADR-AMENDMENT*.md')))
 for p in meta:v['metadataSHA256'][str(p.relative_to(ROOT))]=sha(p)
 for group in('sourceSHA256','metadataSHA256'):
  for n,h in v[group].items():
   if sha(ROOT/n)!=h:raise ValueError('SELECTED_SOURCE_OR_METADATA_DRIFT:'+n)
 v.update(format='aeris-metaval15-selection-closure',releaseSelection=selected_plan(),releaseRevision=1,originalInputManifestSHA256=PRIOR_SHA,absoluteTaskDeadlineNs=absolute_task_deadline(),frozen675_108Preserved=True,runtimeEntryModule=RUNTIME,externalRecordingPolicy=policy().amendment(),externalObserverRecordingPolicy=observer().amendment(),existingPackage13SixFilesUnchanged=True,reusedNative14APKUnchanged=True,reusedNative14R1WithoutNewSave=True,newAPKBuilt=False,externalNativeClientSelection=native_selection(),APKSourceSHA256=build_receipt()['sourceSHA256'],apk=build_receipt()['apk'],apkSHA256=build_receipt()['sha256'],package=PACKAGE,activity=ACTIVITY,selectedAPKInputs=len(build_receipt()['sourcePins']),newEvidenceRoot=EVIDENCE,newCasePolicies=CASES,capacity=task_budget(),priorDraftRevisions=[1],reusedActualDraftRevision=1,newActualDraftRevision=None,baselinePolicy='REUSE_INSTALLED_EXACT14_R1_NO_INSTALL_CLEAR_IMPORT_OR_SAVE_PRESERVE331_OLD_FILES_SEVEN_DIAGNOSTICS_PLUS_EXISTING14_PRIVATE',freshTaskResourceCampaign='METAVAL15_DISTINCT_FROM_FAILED14_NO_INTERVAL_CREDIT',old675_108MetadataHistorical=True)
 return v
make_manifest=build_input_contract
def verify_full_inputs():
 validate_linux_gate();validate_release();v=json.loads(MANIFEST.read_bytes())
 if v.get('releaseSelection')!=selected_plan()or v.get('runtimeEntryModule')!=RUNTIME or v.get('externalRecordingPolicy')!=policy().amendment()or v.get('externalObserverRecordingPolicy')!=observer().amendment()or v.get('externalNativeClientSelection')!=native_selection():raise ValueError('METAVAL15_MANIFEST_SELECTION')
 for group in('sourceSHA256','metadataSHA256'):
  for n,h in v[group].items():
   if sha(ROOT/n)!=h:raise ValueError('SELECTED_SOURCE_DRIFT:'+n)
 return v
if __name__=='__main__':
 v=make_manifest();MANIFEST.open('x').write(json.dumps(v,indent=2)+'\n');print(json.dumps(dict(path=str(MANIFEST),sha256=sha(MANIFEST))))
