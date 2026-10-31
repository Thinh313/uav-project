"""One explicit release selection. Revision01 inputs preserved, not executed as operators."""
from pathlib import Path
from importlib import import_module
import hashlib,json,time,datetime,math
from functools import lru_cache
OLD=import_module('planning.betaintegrated01.cockpit05-compact10.flight.contract')
ROOT=OLD.ROOT;PACKAGE=OLD.PACKAGE;ACTIVITY=OLD.ACTIVITY;BUILD=OLD.BUILD;PROVIDERS=OLD.PROVIDERS;EVIDENCE=OLD.EVIDENCE;CASES=OLD.CASES;RUNTIME=OLD.RUNTIME;POLICY=OLD.POLICY;OBSERVER=OLD.OBSERVER;ARTIFACT_RESERVE=OLD.ARTIFACT_RESERVE
NAMESPACE='planning.betaintegrated01.cockpit05-compact10.release02';COMPUTATIONAL='planning.betaintegrated01.cockpit05-compact10.flight';TASK_PLANNING=ROOT/'planning/betaintegrated01/cockpit05-compact10';E=ROOT/EVIDENCE
MANIFEST=E/'host/input-contract02.json';PRIOR_MANIFEST=E/'host/input-contract01.json';GUARDIAN=E/'emulator02';GUARDIAN_SOURCE=Path(__file__).parent/'android_guardian.py';SETUP=E/'android-setup02';FIRST_PRELAUNCH=E/'root-prelaunch01.json'
EXPECTED_APK='8c1f9d0ba1216a1d0d51effe8c0c5542a5cacaf1dbec9d630b510fc5c6b9176a';EXPECTED_SOURCE='b98c36b7692e121873947ec171348e06d23c8ffe251ff0d43c7d29f521083feb';PRIOR_SHA='6fc7707ec2e499aae5e56bafd203a6cf238caede167e142487964d7bdde2ea8a'
sha=OLD.sha;case_budget=OLD.case_budget;task_budget=OLD.task_budget;campaign_budget=OLD.campaign_budget;policy=OLD.policy;observer=OLD.observer;build_config=OLD.build_config;expected_context=OLD.expected_context

def build_receipt():return json.loads((ROOT/BUILD).read_text())
def __getattr__(name):
 if name=='APK_SHA256':return build_receipt()['sha256']
 if name=='SOURCE_SHA256':return build_receipt()['sourceSHA256']
 raise AttributeError(name)
@lru_cache(maxsize=1)
def first_task_clocks():
 v=json.loads(FIRST_PRELAUNCH.read_text());at=v.get('hostNs')
 if type(at)is not int or at<0 or v.get('manifestSHA256')!=PRIOR_SHA:raise ValueError('ORIGINAL_FIRST_PRELAUNCH_BINDING')
 wall=datetime.datetime.fromisoformat(v['atUTC']).timestamp()
 if not math.isfinite(wall):raise ValueError('ORIGINAL_WALL_CLOCK')
 return at,wall

def absolute_task_deadline():return first_task_clocks()[0]+5400*10**9

@lru_cache(maxsize=1)
def first_wall_ns():
 value=datetime.datetime.fromisoformat(json.loads(FIRST_PRELAUNCH.read_text())['atUTC']);return int(value.timestamp())*10**9+value.microsecond*1000

def remaining_task_ns(now_ns=None,wall_seconds=None,wall_ns=None):
 now=time.monotonic_ns()if now_ns is None else now_ns;first,_=first_task_clocks();initialWall=first_wall_ns()
 if wall_ns is not None:wall=wall_ns
 elif wall_seconds is not None:
  if type(wall_seconds)not in(int,float)or not math.isfinite(wall_seconds):raise ValueError('ORIGINAL_WALL_CLOCK_TYPE')
  wall=round(wall_seconds*10**9)
 else:wall=time.time_ns()
 if type(now)is not int or now<first or type(wall)is not int or wall<initialWall:raise ValueError('ORIGINAL_TASK_CLOCK_REGRESSION')
 if abs((wall-initialWall)-(now-first))>2*10**9:raise ValueError('ORIGINAL_TASK_WALL_MONOTONIC_GAP')
 return min(absolute_task_deadline()-now,initialWall+5400*10**9-wall)
def selected_plan():
 r=build_receipt()
 return dict(package=PACKAGE,build=BUILD,apk=r['apk'],apkSHA256=r['sha256'],sourceSHA256=r['sourceSHA256'],sourceInputs=len(r['sourcePins']),manifest=str(MANIFEST),guardian=str(GUARDIAN),guardianSource=str(GUARDIAN_SOURCE),setup=str(SETUP),runtime=RUNTIME,policy=POLICY,absoluteTaskDeadlineNs=absolute_task_deadline(),AVDBaseline=str(E/'avd-baseline.json'),originalPrelaunch=str(FIRST_PRELAUNCH))
def validate_plan(p,*,maximum_seconds=None,now_ns=None,wall_seconds=None,wall_ns=None,live=False):
 expected={'package':PACKAGE,'build':'evidence/betaintegrated01-cockpit05-compact10/native/build-02.json','apk':'native/betaintegrated01/cockpitio10/dist/aeris-cockpitio10-development-02.apk','apkSHA256':EXPECTED_APK,'sourceSHA256':EXPECTED_SOURCE,'sourceInputs':40,'manifest':str(MANIFEST),'guardian':str(GUARDIAN),'guardianSource':str(GUARDIAN_SOURCE),'setup':str(SETUP),'runtime':RUNTIME,'policy':POLICY,'AVDBaseline':str(E/'avd-baseline.json'),'originalPrelaunch':str(FIRST_PRELAUNCH)}
 if type(p)is not dict or set(p)!=set(expected)|{'absoluteTaskDeadlineNs'}or any(type(p[k])is not type(v)or p[k]!=v for k,v in expected.items())or type(p['absoluteTaskDeadlineNs'])is not int or p['absoluteTaskDeadlineNs']!=absolute_task_deadline():raise ValueError('RELEASE02_CROSS_SELECTOR_MISMATCH')
 now=time.monotonic_ns()if now_ns is None else now_ns
 if type(now)is not int or now<0:raise ValueError('HOST_CLOCK_DOMAIN')
 if maximum_seconds is not None:
  if type(maximum_seconds)is not int or maximum_seconds not in(180,1960):raise ValueError('CASE_DURATION')
  if remaining_task_ns(now,wall_seconds,wall_ns)<(maximum_seconds+290)*10**9:raise ValueError('ORIGINAL_TASK_DEADLINE_CASE_PLUS290_REQUIRED')
 elif live and remaining_task_ns(now,wall_seconds,wall_ns)<=25*10**9:raise ValueError('ORIGINAL_TASK_DEADLINE25S_HEADROOM')
 return p
def validate_release(**kwargs):
 p=validate_plan(selected_plan(),**kwargs)
 if sha(ROOT/p['apk'])!=p['apkSHA256']:raise ValueError('SELECTED_APK02_BYTES')
 return p

def selected_sources():return {str(p.relative_to(ROOT)):sha(p)for p in sorted(Path(__file__).parent.glob('*.py'))}
def build_input_contract(repository=ROOT):
 if Path(repository)!=ROOT:raise ValueError('REPOSITORY')
 validate_release();prior=json.loads(PRIOR_MANIFEST.read_text())
 if sha(PRIOR_MANIFEST)!=PRIOR_SHA:raise ValueError('FROZEN_MANIFEST01_DRIFT')
 for n,h in {**prior['sourceSHA256'],**prior['metadataSHA256']}.items():
  if sha(ROOT/n)!=h:raise ValueError('FROZEN479_49_DRIFT:'+n)
 v=json.loads(json.dumps(prior));v['sourceSHA256'].update(selected_sources())
 paths=[PRIOR_MANIFEST,FIRST_PRELAUNCH,E/'root-bootstrap-incident01.json',E/'emulator01/closure.json',E/'host/release-selection-audit02.json',E/'host/release02-before01.tar',TASK_PLANNING/'HELPER-REVISION02-ADR.md',Path(__file__).parent/'RUNNER.md']
 for p in paths:v['metadataSHA256'][str(p.relative_to(ROOT))]=sha(p)
 v.update(format='aeris-compact10-release02-selection-closure',releaseSelection=selected_plan(),releaseRevision=2,originalInputManifestSHA256=PRIOR_SHA,absoluteTaskDeadlineNs=absolute_task_deadline(),frozen479_49Preserved=True)
 return v
make_manifest=build_input_contract
def verify_full_inputs():
 validate_release();v=json.loads(MANIFEST.read_text())
 if v.get('releaseSelection')!=selected_plan()or v.get('releaseRevision')!=2:raise ValueError('RELEASE02_MANIFEST_SELECTION')
 for n,h in {**v['sourceSHA256'],**v['metadataSHA256']}.items():
  if sha(ROOT/n)!=h:raise ValueError('SELECTED_SOURCE_DRIFT:'+n)
 return v
if __name__=='__main__':
 v=make_manifest();MANIFEST.open('x').write(json.dumps(v,indent=2)+'\n');print(json.dumps(dict(path=str(MANIFEST),sha256=sha(MANIFEST))))
