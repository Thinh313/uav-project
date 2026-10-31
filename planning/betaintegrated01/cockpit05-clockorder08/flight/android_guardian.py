"""Root-owned cached Android UI test only. No AP, transport or aircraft commands."""
from pathlib import Path
import datetime,hashlib,json,os,re,signal,socket,subprocess,time,sys
from importlib import import_module
from . import ledger
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
H='planning.betaintegrated01.cockpit05-clockowner02'
DiskGuard=import_module(H+'.admission').DiskGuard
policy=import_module(H+'.policy')
contract=import_module('planning.betaintegrated01.cockpit05-clockorder08.flight.contract')
metadata_allocated=import_module('planning.betaintegrated01.cockpit05-clockorder08.flight.metadata').allocated_metadata
R=Path(__file__).resolve().parents[4]
E=R/'evidence/betaintegrated01-cockpit05-clockorder08/emulator01'
W=R/'.local/betaintegrated01/android'
SDK=R/'.local/native86-android/sdk'
ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
STOP=False
def halt(*_):
 global STOP
 STOP=True
def put(name,value):
 with(E/name).open('x')as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def power():
 raw=subprocess.check_output(['pmset','-g','batt'],text=True,timeout=2);m=re.search(r'(\d+)%',raw);n=int(m[1])if m else None;ac="'AC Power'"in raw
 if not ac and n is None:raise RuntimeError('UNKNOWN_POWER')
 return dict(raw=raw,AC=ac,batteryPercent=n,userAuthorizedBattery=True)
def allocated(root):return sum(p.stat().st_blocks*512 for p in root.rglob('*')if p.is_file()and not p.is_symlink())
def main():
 os.chdir(R);assert contract.case_budget(__import__('shutil').disk_usage(R).free,180)['admitted'],'EMULATOR_ENTRY10_UI_WHOLEBUDGET_BEFORE_PRIME';E.mkdir(exist_ok=False);guard=DiskGuard(R);child=None;log=None;reason='OWNER_STOP';failure=None;stamp=None;start=time.monotonic()
 try:
  contract.verify_full_inputs();ledger.assert_shared_caps(allocated(W/'avd/aeris-beta-m1.avd'));p=power();assert p['AC']or p['batteryPercent']>=30,'POWER_ENTRY'
  assert 'emulator-5582'not in subprocess.check_output([ADB,'devices'],text=True)
  for port in(5582,5583):
   with socket.socket()as s:s.bind(('127.0.0.1',port))
  old=json.loads((R/'evidence/betaintegrated01-m1cockpit04/emulator01/prelaunch.json').read_text())
  for n,d in old['verifiedPrerequisites'].items():assert sha(d['path'])==d['sha256'],n
  avd=W/'avd/aeris-beta-m1.avd';assert sha(avd/'config.ini')==old['AVDConfigSHA256'];baseline=allocated(avd);native05=R/'native/betaintegrated01/cockpitio08';native05baseline=allocated(native05)
  argv=old['argv'];assert argv[0]==str(SDK/'emulator/emulator')and argv[1:5]==['-avd','aeris-beta-m1','-port','5582']
  admission=guard.prime();contract.verify_full_inputs();ledger.assert_shared_caps(allocated(W/'avd/aeris-beta-m1.avd'));p=power();assert p['AC']or p['batteryPercent']>=30,'POWER_ENTRY'
  put('admission.json',dict(fullBudget=contract.case_budget(__import__('shutil').disk_usage(R).free,180),campaignHardBudget=contract.campaign_budget(),selectedAPK_SHA256=contract.APK_SHA256,selectedAPK_SourceSHA256=contract.SOURCE_SHA256,selectedAPKInputs=39,actualPrime=admission,power=p,sourceSHA256=sha(__file__),verifiedPrerequisites=old['verifiedPrerequisites'],AVDAllocatedBaseline=baseline,cumulativeAVDOriginalBaseline=ledger.prior()['cumulativeAVDOriginalBaseline'],prior07LedgerSHA256=sha(ledger.LEDGER),AVDConfigSHA256=old['AVDConfigSHA256'],scope='ANDROID_SITL_TEST',maximumSeconds=5400,metadataBudgetBytes=64*2**20,AVDGrowthBudgetBytes=512*2**20))
  guard.check();assert contract.case_budget(__import__('shutil').disk_usage(R).free,180)['admitted'],'EMULATOR_ENTRY10_UI_WHOLEBUDGET_AFTER_REAL_PRIME';log=(E/'console.txt').open('xb');env=dict(os.environ,ANDROID_AVD_HOME=str(avd.parent),ANDROID_USER_HOME=str(W/'user'),ANDROID_HOME=str(SDK),ANDROID_SDK_ROOT=str(SDK))
  child=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);stamp=subprocess.check_output(['ps','-p',str(child.pid),'-o','lstart='],text=True).strip()
  put('launch.json',dict(pid=child.pid,processStart=stamp,processGroup=child.pid,argv=argv,serial='emulator-5582',guardianPID=os.getpid(),guardianProcessStart=subprocess.check_output(['ps','-p',str(os.getpid()),'-o','lstart='],text=True).strip(),guardianSourceSHA256=sha(__file__),maximumSeconds=5400,scope='ANDROID_SITL_TEST',atUTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
  last=time.monotonic();wall=time.time();tick=0
  with(E/'guard.jsonl').open('x')as f:
   while not STOP and child.poll()is None:
    guard.check();now=time.monotonic();utc=time.time();p=power();gap=(utc-wall)-(now-last);last,wall=now,utc;tick+=1
    if abs(gap)>2:raise RuntimeError('SUSPEND_OR_WALL_JUMP')
    if not p['AC']and p['batteryPercent']<=20:raise RuntimeError('BATTERY_LOW20')
    if now-start>5400:raise RuntimeError('UI_TEST_WALL_BUDGET')
    if (E/'console.txt').stat().st_size>16*2**20:raise RuntimeError('EMULATOR_CONSOLE16MiB_CAP')
    if tick%10==0:
     if allocated(E)>32*2**20:raise RuntimeError('OWN_EMULATOR_METADATA32MiB_CAP')
     if allocated(E.parent)+allocated(R/'planning/betaintegrated01/cockpit05-clockorder08/flight')+max(0,allocated(avd)-baseline)+max(0,allocated(native05)-native05baseline)>contract.campaign_budget()['taskHardPeakBytes']:raise RuntimeError('FULL_TASK_HARD_QUOTA')
     ledger.assert_shared_caps(allocated(avd))
     if ledger.metadata_total()>64*2**20:raise RuntimeError('CUMULATIVE_METADATA64MiB_CAP')
     if max(0,allocated(native05)-native05baseline)>512*2**20:raise RuntimeError('NEW_NATIVE05_POSITIVE_GROWTH_OTHER_BUDGET')
    f.write(json.dumps(dict(hostNs=time.monotonic_ns(),freeBytes=guard.diagnostic()['currentFreeBytes'],forecastFreeBytes=guard.diagnostic()['forecastFreeBytes'],AC=p['AC'],batteryPercent=p['batteryPercent'],wallMonoGapSeconds=gap,cumulative07_08AVDpositiveAllocatedDelta=ledger.avd_growth(allocated(avd))))+'\n');f.flush();os.fsync(f.fileno());time.sleep(.5)
   if child.poll()is not None:reason='EMULATOR_EXIT'
 except BaseException as exc:
  failure=type(exc).__name__+':'+str(exc);reason='GUARD_OR_ADMISSION_FAILURE';put('failure.json',dict(error=failure,diagnostic=guard.diagnostic(),APStarted=False))
 finally:
  if child is not None and child.poll()is None:
   actual=subprocess.check_output(['ps','-p',str(child.pid),'-o','lstart='],text=True).strip()
   assert actual==stamp and os.getpgid(child.pid)==child.pid
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=25)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)
  if log:log.close()
  put('closure.json',dict(reason=reason,failure=failure,exit=None if child is None else child.poll(),APStarted=False,flightCommands=0,elapsedSeconds=time.monotonic()-start,lastDisk=guard.diagnostic()))
if __name__=='__main__':
 attempt=sys.argv[1]if len(sys.argv)>1 else'01';assert attempt=='01'
 E=E.parent/('emulator'+attempt)
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt);main()
