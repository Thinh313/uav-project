"""Root-owned cached Android UI test only. No AP, transport or aircraft commands."""
from pathlib import Path
import datetime,hashlib,json,os,re,signal,socket,subprocess,time,sys
from pilot.betaintegrated01.runtime02.journal.admission import DiskGuard
R=Path(__file__).resolve().parents[3]
E=R/'evidence/betaintegrated01-cockpit05-native/emulator01'
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
 os.chdir(R);E.mkdir(exist_ok=False);guard=DiskGuard(R);child=None;log=None;reason='OWNER_STOP';failure=None;stamp=None;start=time.monotonic()
 try:
  p=power();assert p['AC']or p['batteryPercent']>=30,'POWER_ENTRY'
  assert 'emulator-5582'not in subprocess.check_output([ADB,'devices'],text=True)
  for port in(5582,5583):
   with socket.socket()as s:s.bind(('127.0.0.1',port))
  old=json.loads((R/'evidence/betaintegrated01-m1cockpit04/emulator01/prelaunch.json').read_text())
  for n,d in old['verifiedPrerequisites'].items():assert sha(d['path'])==d['sha256'],n
  avd=W/'avd/aeris-beta-m1.avd';assert sha(avd/'config.ini')==old['AVDConfigSHA256'];baseline=allocated(avd)
  argv=old['argv'];assert argv[0]==str(SDK/'emulator/emulator')and argv[1:5]==['-avd','aeris-beta-m1','-port','5582']
  admission=guard.prime();p=power();assert p['AC']or p['batteryPercent']>=30,'POWER_ENTRY'
  put('admission.json',dict(actualPrime=admission,power=p,sourceSHA256=sha(__file__),verifiedPrerequisites=old['verifiedPrerequisites'],AVDAllocatedBaseline=baseline,AVDConfigSHA256=old['AVDConfigSHA256'],scope='ANDROID_UI_ONLY_NO_AP',maximumSeconds=1800,metadataBudgetBytes=32*2**20,AVDGrowthBudgetBytes=512*2**20))
  guard.check();log=(E/'console.txt').open('xb');env=dict(os.environ,ANDROID_AVD_HOME=str(avd.parent),ANDROID_USER_HOME=str(W/'user'),ANDROID_HOME=str(SDK),ANDROID_SDK_ROOT=str(SDK))
  child=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);stamp=subprocess.check_output(['ps','-p',str(child.pid),'-o','lstart='],text=True).strip()
  put('launch.json',dict(pid=child.pid,processStart=stamp,processGroup=child.pid,argv=argv,serial='emulator-5582',atUTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
  last=time.monotonic();wall=time.time();tick=0
  with(E/'guard.jsonl').open('x')as f:
   while not STOP and child.poll()is None:
    guard.check();now=time.monotonic();utc=time.time();p=power();gap=(utc-wall)-(now-last);last,wall=now,utc;tick+=1
    if abs(gap)>2:raise RuntimeError('SUSPEND_OR_WALL_JUMP')
    if not p['AC']and p['batteryPercent']<=20:raise RuntimeError('BATTERY_LOW20')
    if now-start>1800:raise RuntimeError('UI_TEST_WALL_BUDGET')
    if tick%10==0:
     if max(0,allocated(avd)-baseline)>512*2**20:raise RuntimeError('AVD_GROWTH_CAP')
     if allocated(E.parent)>32*2**20:raise RuntimeError('UI_EVIDENCE_CAP')
    f.write(json.dumps(dict(hostNs=time.monotonic_ns(),freeBytes=guard.diagnostic()['currentFreeBytes'],forecastFreeBytes=guard.diagnostic()['forecastFreeBytes'],AC=p['AC'],batteryPercent=p['batteryPercent'],wallMonoGapSeconds=gap))+'\n');f.flush();os.fsync(f.fileno());time.sleep(.5)
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
 attempt=sys.argv[1]if len(sys.argv)>1 else'01';assert attempt in('01','02')
 E=E.parent/('emulator'+attempt)
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt);main()
