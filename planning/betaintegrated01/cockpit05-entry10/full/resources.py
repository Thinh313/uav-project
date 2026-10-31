"""Root-only continuous campaign resource observation, not a source-runtime waiver."""
from pathlib import Path
import hashlib,json,os,re,shutil,signal,subprocess,threading,time,selectors
from ..host.admission import DiskGuard
from ..host.policy02 import task_budget
MIB=2**20
from .metadata import allocated_metadata
R=Path(__file__).resolve().parents[4]
E=R/'evidence/betaintegrated01-cockpit05-entry10-flight'
AVD=R/'.local/betaintegrated01/android/avd/aeris-beta-m1.avd'
def put(p,v):
 with Path(p).open('x')as f:json.dump(v,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def allocated(root):
 return sum(p.lstat().st_blocks*512 for p in Path(root).rglob('*')if p.is_file()and not p.is_symlink())
def power():
 raw=subprocess.check_output(['pmset','-g','batt'],text=True);ac="'AC Power'"in raw;m=re.search(r'(\d+)%',raw);n=int(m.group(1))if m else None
 if not ac and n is None:raise RuntimeError('UNKNOWN_POWER')
 return dict(raw=raw,AC=ac,batteryPercent=n,userAuthorizedBattery=True)
class ResourceGuard:
 def __init__(self,control,maximum_seconds):
  self.control=Path(control);self.maximum=maximum_seconds;self.started=time.monotonic();self.stopped=threading.Event();self.fault=[];self.lock=threading.Lock();self.disk=DiskGuard(R);self.thread=None
 def start(self):
  b=task_budget(shutil.disk_usage(R).free);assert b['admitted'],'CAMPAIGN_ENTRY_CAPACITY'
  p=power();assert p['AC']or p['batteryPercent']>=30,'POWER_ENTRY30_OR_AC'
  baseline=json.loads((E/'avd-baseline.json').read_text());self.avd_baseline=baseline['allocatedBytes'];assert baseline['path']==str(AVD)
  self.native05baseline=allocated(R/'native/betaintegrated01/cockpit05');prime=self.disk.prime();assert task_budget(shutil.disk_usage(R).free)['admitted'],'ROOT_RESOURCE_WHOLE_BUDGET_AFTER_REAL_PRIME';put(self.control/'root-guard-entry.json',dict(capacity=b,power=p,actualPrime=prime,AVDbaseline=baseline))
  self.thread=threading.Thread(target=self._run,name='cockpit05-soak-root-resource-guard');self.thread.start()
 def check(self,n=0):
  if self.fault:raise RuntimeError(self.fault[0])
  if self.thread and not self.thread.is_alive()and not self.stopped.is_set():raise RuntimeError('ROOT_GUARD_DEAD')
  with self.lock:self.disk.check(n)
 def _run(self):
  last=time.monotonic();wall=time.time();tick=0
  try:
   with(self.control/'guard.jsonl').open('x')as f:
    while not self.stopped.wait(.5):
     with self.lock:self.disk.check()
     now=time.monotonic();utc=time.time();p=power();gap=(utc-wall)-(now-last);last,wall=now,utc;tick+=1
     delta=allocated(AVD)-self.avd_baseline
     row=dict(hostNs=time.monotonic_ns(),freeBytes=shutil.disk_usage(R).free,forecast15s=self.disk.diagnostic().get('forecastFreeBytes'),AVDpositiveAllocatedDelta=max(0,delta),AC=p['AC'],batteryPercent=p['batteryPercent'],wallMonoGapSeconds=gap,elapsedSeconds=now-self.started)
     f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
     if tick%10==0:
      if allocated_metadata(E)+allocated(R/'planning/betaintegrated01/cockpit05-entry10/full')>64*MIB:raise RuntimeError('FULL_METADATA64MiB_CAP')
      task_allocated=allocated(E)+allocated(R/'planning/betaintegrated01/cockpit05-entry10/full')+max(0,allocated(R/'native/betaintegrated01/cockpit05')-self.native05baseline)+max(0,delta)
      if task_allocated>task_budget()['taskHardPeakBytes']:raise RuntimeError('WHOLE_TASK_ALLOCATED_HARD_BUDGET')
     if max(0,delta)>512*MIB:raise RuntimeError('AVD_ALLOCATED_GROWTH512MiB')
     if not p['AC']and p['batteryPercent']<=20:raise RuntimeError('BATTERY_STOP20')
     if abs(gap)>2:raise RuntimeError('SUSPEND_OR_WALL_JUMP')
     if now-self.started>self.maximum:raise RuntimeError('ROOT_WALL_LIMIT')
     if(E/'emulator01/closure.json').exists():raise RuntimeError('OWNED_EMULATOR_CLOSED')
  except BaseException as x:self.fault.append(type(x).__name__+':'+str(x));put(self.control/'root-guard-failure.json',dict(error=self.fault[-1],diagnostic=self.disk.diagnostic()))
 def close(self):
  self.stopped.set()
  if self.thread:self.thread.join(timeout=8)
  put(self.control/'root-guard-closure.json',dict(faults=self.fault,elapsedSeconds=time.monotonic()-self.started,lastDisk=self.disk.diagnostic()))

def capture_native(op,control,run,kind,guard):
 """One current-run stream; no wholehistory tar and no duplicate extraction."""
 from importlib import import_module
 import sys
 sys.path.insert(0,str(R/'planning/betaintegrated01/cockpit05-soak/android'))
 from cockpit05_android_operator import ADB,SERIAL,PACKAGE
 assert re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}',run)and kind in ('smoke','loss','long')
 cap={'smoke':28,'loss':28,'long':168}[kind]*MIB;ledger=E/'native-export-ledger.jsonl';previous=[json.loads(x)for x in ledger.read_text().splitlines()]if ledger.exists()else[]
 assert all(x['case']!=run for x in previous),'NATIVE_EXPORT_ONCE_ONLY';used=sum(x['bytes']for x in previous)
 target=Path(control)/'native-private.tar';args=[ADB,'-s',SERIAL,'exec-out','run-as',PACKAGE,'tar','-cf','-','--','files/control-runs/'+run,'files/workspace03','files/review-links']
 err=(Path(control)/'native-export-stderr.bin').open('xb');child=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=err);total=0;h=hashlib.sha256();error=None
 try:
  deadline=time.monotonic()+120;poll=selectors.DefaultSelector();poll.register(child.stdout,selectors.EVENT_READ);os.set_blocking(child.stdout.fileno(),False)
  with target.open('xb')as sink:
   while True:
    guard.check(65536)
    if time.monotonic()>deadline:raise RuntimeError('NATIVE_EXPORT120S_DEADLINE')
    if not poll.select(.5):continue
    chunk=os.read(child.stdout.fileno(),65536)
    if not chunk:break
    total+=len(chunk)
    if total>cap or used+total>192*MIB:raise RuntimeError('NATIVE_EXPORT_HARD_CAP')
    sink.write(chunk);h.update(chunk)
   sink.flush();os.fsync(sink.fileno())
  code=child.wait(timeout=15)
  if code:raise RuntimeError('NATIVE_EXPORT_EXIT:'+str(code))
 except BaseException as x:
  error=repr(x)
  if child.poll()is None:child.terminate()
  try:child.wait(timeout=5)
  except subprocess.TimeoutExpired:child.kill();child.wait(timeout=3)
  raise
 finally:
  if 'poll'in locals():poll.close()
  err.close();child.stdout.close();put(Path(control)/'native-export-receipt.json',dict(argv=args,PID=child.pid,exit=child.poll(),bytes=total,capBytes=cap,previousExportBytes=used,sha256=h.hexdigest(),error=error,noRetry=True))
 row=dict(case=run,kind=kind,path=str(target),sha256=h.hexdigest(),bytes=total)
 with ledger.open('a')as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
 put(Path(control)/'native-export-location.json',dict(path=str(target),sha256=h.hexdigest()));return row
