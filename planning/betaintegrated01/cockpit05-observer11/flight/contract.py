"""One Observer11 selection from unchanged installed Compact10 APK to new host/observer."""
from pathlib import Path
from importlib import import_module
from functools import lru_cache
import json,hashlib,time,datetime,math
OLD=import_module('planning.betaintegrated01.cockpit05-compact10.release02.contract')
ROOT=OLD.ROOT;PACKAGE=OLD.PACKAGE;ACTIVITY=OLD.ACTIVITY;BUILD=OLD.BUILD;PROVIDERS=OLD.PROVIDERS;ARTIFACT_RESERVE=OLD.ARTIFACT_RESERVE
NAMESPACE='planning.betaintegrated01.cockpit05-observer11.flight';COMPUTATIONAL='planning.betaintegrated01.cockpit05-compact10.flight';OBSERVER='planning.betaintegrated01.cockpit05-observer11.adapter';POLICY='planning.betaintegrated01.cockpit05-observer11.runtime.policy';RUNTIME='planning.betaintegrated01.cockpit05-observer11.runtime.backend';SUPERVISOR=OBSERVER+'.ap_supervisor'
EVIDENCE='evidence/betaintegrated01-cockpit05-observer11';E=ROOT/EVIDENCE;TASK_PLANNING=ROOT/'planning/betaintegrated01/cockpit05-observer11'
MANIFEST=E/'host/input-contract01.json';PRIOR_MANIFEST=ROOT/'evidence/betaintegrated01-cockpit05-compact10/host/input-contract02.json';PRIOR_SHA='c290ba8bc92a8db1c6029a19c9e6e0eb019dcc6a7894e358614447ef22d3a5ce';PRIOR_SEAL=ROOT/'evidence/betaintegrated01-cockpit05-compact10/handoff-final.json';PRIOR_SEAL_SHA='fa0a9d5c8d3f7f2721f22a118f3250785cec0e4004099cb46f9ca891302b4c4b'
GUARDIAN=E/'emulator01';GUARDIAN_SOURCE=Path(__file__).parent/'android_guardian.py';SETUP=E/'android-setup01';FIRST_PRELAUNCH=E/'task-start01.json'
EXPECTED_APK=OLD.EXPECTED_APK;EXPECTED_SOURCE=OLD.EXPECTED_SOURCE
CASES={k:{**v,'run':v['run'].replace('cockpit05-compact10','cockpit05-observer11')}for k,v in OLD.CASES.items()}
sha=OLD.sha

def policy():return import_module(POLICY)
def observer():return import_module(OBSERVER+'.policy')
def build_config(*a,**kw):return policy().build_config(*a,**kw)
def verify_observer_capture(*a,**kw):return import_module(OBSERVER+'.cold').verify_observer_capture(*a,**kw)
def case_budget(*a,**kw):return policy().case_budget(*a,**kw)
def task_budget(*a,**kw):return policy().task_budget(*a,**kw)
def campaign_budget(*a,**kw):return policy().campaign_budget(*a,**kw)
def expected_context(*a,**kw):return OLD.expected_context(*a,**kw)
def build_receipt():return json.loads((ROOT/BUILD).read_bytes())
def __getattr__(name):
 if name=='APK_SHA256':return build_receipt()['sha256']
 if name=='SOURCE_SHA256':return build_receipt()['sourceSHA256']
 raise AttributeError(name)
@lru_cache(maxsize=1)
def first_task_clocks():
 v=json.loads(FIRST_PRELAUNCH.read_bytes());n=v.get('hostNs');utc=datetime.datetime.fromisoformat(v['atUTC'])
 if type(n)is not int or n<0 or v.get('maximumSeconds')!=5400 or type(v.get('maximumSeconds'))is not int or v.get('scope')!='OBSERVER11_FRESH_TASK' or utc.utcoffset()!=datetime.timedelta(0):raise ValueError('FRESH11_ROOT_TASK_START_BINDING')
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
 if type(now)is not int or now<first or type(wall)is not int or wall<initialWall:raise ValueError('FRESH11_TASK_CLOCK_REGRESSION')
 if abs((wall-initialWall)-(now-first))>2*10**9:raise ValueError('FRESH11_TASK_WALL_MONOTONIC_GAP')
 return min(absolute_task_deadline()-now,initialWall+5400*10**9-wall)
def selected_plan():
 r=build_receipt()
 return dict(package=PACKAGE,build=BUILD,apk=r['apk'],apkSHA256=r['sha256'],sourceSHA256=r['sourceSHA256'],sourceInputs=len(r['sourcePins']),manifest=str(MANIFEST),guardian=str(GUARDIAN),guardianSource=str(GUARDIAN_SOURCE),setup=str(SETUP),runtime=RUNTIME,policy=POLICY,observer=OBSERVER,supervisor=SUPERVISOR,absoluteTaskDeadlineNs=absolute_task_deadline(),AVDBaseline=str(E/'avd-baseline.json'),originalPrelaunch=str(FIRST_PRELAUNCH))
def validate_plan(p,*,maximum_seconds=None,now_ns=None,wall_seconds=None,wall_ns=None,live=False):
 expected={'package':PACKAGE,'build':'evidence/betaintegrated01-cockpit05-compact10/native/build-02.json','apk':'native/betaintegrated01/cockpitio10/dist/aeris-cockpitio10-development-02.apk','apkSHA256':EXPECTED_APK,'sourceSHA256':EXPECTED_SOURCE,'sourceInputs':40,'manifest':str(MANIFEST),'guardian':str(GUARDIAN),'guardianSource':str(GUARDIAN_SOURCE),'setup':str(SETUP),'runtime':RUNTIME,'policy':POLICY,'observer':OBSERVER,'supervisor':SUPERVISOR,'AVDBaseline':str(E/'avd-baseline.json'),'originalPrelaunch':str(FIRST_PRELAUNCH)}
 if type(p)is not dict or set(p)!=set(expected)|{'absoluteTaskDeadlineNs'}or any(type(p[k])is not type(v)or p[k]!=v for k,v in expected.items())or type(p['absoluteTaskDeadlineNs'])is not int or p['absoluteTaskDeadlineNs']!=absolute_task_deadline():raise ValueError('OBSERVER11_CROSS_SELECTOR_MISMATCH')
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
 for n,h in {**prior['sourceSHA256'],**prior['metadataSHA256']}.items():
  if sha(ROOT/n)!=h:raise ValueError('FROZEN496_57_DRIFT:'+n)
 v=json.loads(json.dumps(prior));v['sourceSHA256'].update(policy().source_binding());v['sourceSHA256'].update(selected_sources())
 meta=[PRIOR_MANIFEST,PRIOR_SEAL,FIRST_PRELAUNCH,E/'avd-baseline.json',E/'power-policy01.json',TASK_PLANNING/'TIP.md',TASK_PLANNING/'ADR.md',E/'work-start01.json',Path(__file__).parent/'RUNNER.md',ROOT/'evidence/betaintegrated01-cockpit05-compact10/root-device-closeout01/after-restart.json']
 for p in meta:v['metadataSHA256'][str(p.relative_to(ROOT))]=sha(p)
 v.update(format='aeris-observer11-selection-closure',releaseSelection=selected_plan(),releaseRevision=1,originalInputManifestSHA256=PRIOR_SHA,absoluteTaskDeadlineNs=absolute_task_deadline(),frozen496_57Preserved=True,runtimeEntryModule=RUNTIME,externalRecordingPolicy=policy().amendment(),externalObserverRecordingPolicy=observer().amendment(),existingPackage10R1Unchanged=True,newEvidenceRoot=EVIDENCE,newCasePolicies=CASES,capacity=task_budget(),priorDraftRevisions=[1],newActualDraftRevision=None,baselinePolicy='ACTUAL_EXISTING_PACKAGE10_R1_PRESERVED_WITH307_OLD_FILES_AND_FOUR_DIAGNOSTICS_NO_NEW_SAVE',freshTaskResourceCampaign='OBSERVER11_DISTINCT_FROM_CLOSED_COMPACT10',old496_57MetadataHistorical=True)
 return v
make_manifest=build_input_contract
def verify_full_inputs():
 validate_release();v=json.loads(MANIFEST.read_bytes())
 if v.get('releaseSelection')!=selected_plan()or v.get('runtimeEntryModule')!=RUNTIME or v.get('externalRecordingPolicy')!=policy().amendment()or v.get('externalObserverRecordingPolicy')!=observer().amendment():raise ValueError('OBSERVER11_MANIFEST_SELECTION')
 for n,h in {**v['sourceSHA256'],**v['metadataSHA256']}.items():
  if sha(ROOT/n)!=h:raise ValueError('SELECTED_SOURCE_DRIFT:'+n)
 return v
if __name__=='__main__':
 v=make_manifest();MANIFEST.open('x').write(json.dumps(v,indent=2)+'\n');print(json.dumps(dict(path=str(MANIFEST),sha256=sha(MANIFEST))))
