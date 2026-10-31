"""Root-only continuous campaign resource observation, not a source-runtime waiver."""
from pathlib import Path
import hashlib,json,os,re,shutil,signal,subprocess,threading,time,selectors
from importlib import import_module
DiskGuard=import_module('planning.betaintegrated01.cockpit05-clockowner02.admission').DiskGuard
from . import contract
from .contract import task_budget,campaign_budget,case_budget
MIB=2**20
from ..flight.metadata import allocated_metadata
from . import ledger
R=Path(__file__).resolve().parents[4]
E=R/'evidence/betaintegrated01-cockpit05-compact10'
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
 def __init__(self,control,maximum_seconds,recording_seconds=1960):
  self.control=Path(control);self.maximum=maximum_seconds;self.recording_seconds=recording_seconds;self.started=time.monotonic();self.stopped=threading.Event();self.fault=[];self.lock=threading.Lock();self.disk=DiskGuard(R);self.thread=None
 def start(self):
  contract.validate_release(maximum_seconds=self.recording_seconds)
  b=case_budget(shutil.disk_usage(R).free,self.recording_seconds);assert b['admitted'],'CAMPAIGN_ENTRY_CAPACITY'
  p=power();assert p['AC']or p['batteryPercent']>=30,'POWER_ENTRY30_OR_AC'
  ledger.assert_shared_caps(allocated(AVD));baseline=json.loads((E/'avd-baseline.json').read_text());self.avd_baseline=baseline['allocatedBytes'];assert baseline['path']==str(AVD)
  self.native05baseline=allocated(R/'native/betaintegrated01/cockpitio10');prime=self.disk.prime();assert case_budget(shutil.disk_usage(R).free,self.recording_seconds)['admitted'],'ROOT_RESOURCE_WHOLE_BUDGET_AFTER_REAL_PRIME';put(self.control/'root-guard-entry.json',dict(capacity=b,power=p,actualPrime=prime,AVDbaseline=baseline))
  self.thread=threading.Thread(target=self._run,name='cockpit05-soak-root-resource-guard');self.thread.start()
 def check(self,n=0):
  if self.fault:raise RuntimeError(self.fault[0])
  g=contract.GUARDIAN
  if(g/'failure.json').exists()or(g/'closure.json').exists():raise RuntimeError('OWNED_GUARDIAN_FAILED_OR_CLOSED')
  with(g/'guard.jsonl').open('rb')as stream:
   stream.seek(0,2);size=stream.tell();stream.seek(max(0,size-65536));lines=stream.read().splitlines()
  rows=[]
  for line in lines[-3:]:
   try:rows.append(json.loads(line))
   except(ValueError,UnicodeError):pass
  if not rows or type(rows[-1].get('hostNs'))is not int or not 0<=time.monotonic_ns()-rows[-1]['hostNs']<=2_000_000_000:raise RuntimeError('OWNED_GUARDIAN_OBSERVATION_STALE')
  if self.thread and not self.thread.is_alive()and not self.stopped.is_set():raise RuntimeError('ROOT_GUARD_DEAD')
  with self.lock:self.disk.check(n)
 def _run(self):
  last=time.monotonic();wall=time.time();tick=0
  try:
   with(self.control/'guard.jsonl').open('x')as f:
    while not self.stopped.wait(.5):
     with self.lock:self.disk.check()
     contract.validate_release(live=True)
     now=time.monotonic();utc=time.time();p=power();gap=(utc-wall)-(now-last);last,wall=now,utc;tick+=1
     delta=allocated(AVD)-self.avd_baseline
     row=dict(hostNs=time.monotonic_ns(),freeBytes=shutil.disk_usage(R).free,forecast15s=self.disk.diagnostic().get('forecastFreeBytes'),AVDpositiveAllocatedDelta=max(0,delta),task10AVDpositiveAllocatedDelta=ledger.avd_growth(allocated(AVD)),AC=p['AC'],batteryPercent=p['batteryPercent'],wallMonoGapSeconds=gap,elapsedSeconds=now-self.started)
     f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
     if tick%10==0:
      ledger.assert_shared_caps(allocated(AVD))
      if ledger.metadata_total()>64*MIB:raise RuntimeError('FULL_METADATA64MiB_CAP')
      task_allocated=allocated(E)+allocated(contract.TASK_PLANNING)+max(0,allocated(R/'native/betaintegrated01/cockpitio10')-self.native05baseline)+max(0,delta)
      if task_allocated>campaign_budget()['taskHardPeakBytes']:raise RuntimeError('WHOLE_TASK_ALLOCATED_HARD_BUDGET')
     if ledger.avd_growth(allocated(AVD))>512*MIB:raise RuntimeError('AVD_ALLOCATED_GROWTH512MiB')
     if not p['AC']and p['batteryPercent']<=20:raise RuntimeError('BATTERY_STOP20')
     if abs(gap)>2:raise RuntimeError('SUSPEND_OR_WALL_JUMP')
     if now-self.started>self.maximum:raise RuntimeError('ROOT_WALL_LIMIT')
     if(contract.GUARDIAN/'closure.json').exists():raise RuntimeError('OWNED_EMULATOR_CLOSED')
  except BaseException as x:self.fault.append(type(x).__name__+':'+str(x));put(self.control/'root-guard-failure.json',dict(error=self.fault[-1],diagnostic=self.disk.diagnostic()))
 def close(self):
  self.stopped.set()
  if self.thread:self.thread.join(timeout=8)
  put(self.control/'root-guard-closure.json',dict(faults=self.fault,elapsedSeconds=time.monotonic()-self.started,lastDisk=self.disk.diagnostic()))

def capture_native(op,control,run,kind,guard):
 """Selected current run only; every failed prefix counts against new campaign192MiB."""
 from .export_native import capture
 from .contract import CASES
 expected='short'if Path(control).parent.name=='actual-short01'else'long'
 if kind!=expected or run!=CASES[expected]['run']:raise ValueError('EXPORT_EXACT_CASE_RUN_KIND_REQUIRED')
 guard.check();return capture(control)
