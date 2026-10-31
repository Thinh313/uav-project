"""Root-only one-shot preservation export. No flight/UI/restart/install operation."""
from pathlib import Path
import hashlib,json,math,os,re,selectors,subprocess,sys,tarfile,time
from importlib import import_module
R=Path(__file__).resolve().parents[4]
OLD=R/'evidence/betaintegrated01-cockpit05-nativeio04'
E=OLD; C=None
G=OLD/'emulator01'; GS=R/'planning/betaintegrated01/cockpit05-nativeio04/flight/android_guardian.py'
ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
SERIAL='emulator-5582'; PACKAGE='vn.rtr.aeris.cockpitio04'; MIB=2**20
FLOOR=10*2**30+256*MIB; SINGLE=168*MIB; GLOBAL=192*MIB; CHUNK=256*1024

def require(ok,why):
 if not ok:raise RuntimeError(why)
def read(p,bound=262144):
 p=Path(p);require(p.is_file()and not p.is_symlink()and p.stat().st_size<=bound,'BOUNDED_REGULAR_METADATA_REQUIRED');return json.loads(p.read_bytes())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def allocated(p):
 p=Path(p)
 return sum(x.lstat().st_blocks*512 for x in p.rglob('*')if x.is_file()and not x.is_symlink())
def inventory_parse(raw,run):
 roots=('files/control-runs/'+run+'/', 'files/workspace03/', 'files/review-links/')
 out={}
 for line in raw.decode('utf-8').splitlines():
  digest,name=line.split(None,1);name=name.strip()
  require(re.fullmatch('[0-9a-f]{64}',digest)and name.startswith(roots)and '..'not in Path(name).parts and name not in out,'PRIVATE_INVENTORY_INVALID');out[name]=digest
 require(0<len(out)<=1024,'PRIVATE_INVENTORY_BOUND');return out

def exports():
 # Actual retained bytes, including every incomplete attempt; ledger is not proof of absence.
 return sorted({p.resolve()for root in(E,)for p in root.rglob('native-private*.tar')if p.is_file()and not p.is_symlink()})

class Guard:
 def __init__(self):
  self.launch=read(G/'launch.json');self.admission=read(G/'admission.json');self.lastFull=0
  require(self.launch['serial']==SERIAL and self.launch['scope']=='ANDROID_SITL_TEST'and self.launch['maximumSeconds']==5400,'OWNED_FULL_GUARDIAN_SCOPE')
  prime=self.admission['actualPrime'];budget=self.admission['fullBudget']
  require(prime.get('primed')is True and type(prime.get('historySpanNs'))is int and prime['historySpanNs']>=15_000_000_000 and type(prime.get('elapsedRealMonotonicNs'))is int and prime['elapsedRealMonotonicNs']>=15_000_000_000 and prime.get('floorAndReserveBytes')==FLOOR and prime.get('source')=='ACTUAL_HOST_15S_PRIME_NO_SYNTHETIC_SEED','REAL_PRIOR_15S_PRIME_REQUIRED')
  require(budget.get('admitted')is True and budget.get('floorBytes')==10*2**30 and budget.get('reserveBytes')==256*MIB,'ORIGINAL_WHOLE_BUDGET_ADMISSION_REQUIRED')
  self.source=self.launch['guardianSourceSHA256'];self.full()
 def full(self):
  require(sha(GS)==self.source==self.admission['sourceSHA256'],'GUARD_SOURCE_CHANGED')
  for pid,key in((self.launch['guardianPID'],'guardianProcessStart'),(self.launch['pid'],'processStart')):
   actual=subprocess.check_output(['ps','-p',str(pid),'-o','lstart='],text=True,timeout=2).strip()
   require(actual==self.launch[key],'GUARD_PID_START_CHANGED')
  require(os.getpgid(self.launch['pid'])==self.launch['processGroup'],'EMULATOR_PROCESS_GROUP_CHANGED')
  avd=read(OLD/'avd-baseline.json');growth=max(0,allocated(avd['path'])-avd['allocatedBytes'])
  require(growth<=512*MIB,'AVD_GROWTH_CAP')
  planning=R/'planning/betaintegrated01/cockpit05-nativeio04/flight'
  # Count entire retained current campaign + closure artifacts; no old raw exclusions here.
  whole=allocated(E)+allocated(planning)+growth
  require(whole<=self.admission['campaignHardBudget']['taskHardPeakBytes'],'WHOLE_ALLOCATED_HARD_CAP')
  self.lastFull=time.monotonic()
 def check(self,n=0):
  require(not(G/'closure.json').exists()and not(G/'failure.json').exists(),'GUARD_CLOSED_OR_FAILED')
  for pid in(self.launch['guardianPID'],self.launch['pid']):os.kill(pid,0)
  with(G/'guard.jsonl').open('rb')as f:
   f.seek(0,2);size=f.tell();f.seek(max(0,size-65536));lines=f.read().splitlines()
  # Incomplete append is never parsed as a fresh observation.
  rows=[]
  for line in lines[-3:]:
   try:rows.append(json.loads(line))
   except(ValueError,UnicodeError):pass
  require(rows,'NO_REAL_GUARD_OBSERVATION');row=rows[-1];now=time.monotonic_ns()
  require(type(row.get('hostNs'))is int and 0<=now-row['hostNs']<=2_000_000_000,'GUARD_OBSERVATION_STALE')
  for key in('freeBytes','forecastFreeBytes'):
   v=row.get(key);require(type(v)in(int,float)and math.isfinite(v)and v>=FLOOR+n,'GUARD_FLOOR_OR_FORECAST')
  require(row.get('AC')is True or(type(row.get('batteryPercent'))is int and row['batteryPercent']>20),'GUARD_POWER_STOP')
  s=os.statvfs(R);require(s.f_bavail*s.f_frsize>=FLOOR+n,'LIVE_FLOOR_RESERVE')
  if time.monotonic()-self.lastFull>=.5:self.full()
  return row

def put(p,value,guard):
 raw=(json.dumps(value,indent=2)+'\n').encode();require(len(raw)<=262144,'METADATA_BOUND');guard.check(len(raw))
 with Path(p).open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())

def tar_check(path,expected,run):
 actual={};dirs=0
 with tarfile.open(path,mode='r|')as t:
  for item in t:
   name=item.name.rstrip('/')
   require(not name.startswith('/')and '..'not in Path(name).parts,'TAR_UNSAFE_PATH')
   if item.isdir():
    require(name in('files/control-runs/'+run,'files/workspace03','files/review-links')or name.startswith('files/control-runs/'+run+'/'),'TAR_UNKNOWN_DIRECTORY');dirs+=1;require(dirs<=1024,'TAR_DIRECTORY_BOUND');continue
   require(item.isfile()and name in expected and name not in actual,'TAR_UNKNOWN_DUPLICATE_NONREGULAR')
   f=t.extractfile(item);h=hashlib.sha256()
   for b in iter(lambda:f.read(CHUNK),b''):h.update(b)
   actual[name]=h.hexdigest();require(actual[name]==expected[name],'TAR_MEMBER_SHA_MISMATCH')
   terminal=t.offset
 require(actual==expected,'TAR_PRIVATE_MAP_INCOMPLETE')
 require(path.stat().st_size%512==0 and path.stat().st_size>=1024,'TAR_BLOCK_SIZE')
 require(path.stat().st_size-terminal>=1024,'TAR_TERMINAL_ZERO_BLOCKS')
 with path.open('rb')as f:
  f.seek(terminal)
  for b in iter(lambda:f.read(CHUNK),b''):require(not any(b),'TAR_TRAILING_NONZERO_BYTES')
 return {'members':len(actual),'directories':dirs,'allMemberSHA256':actual,'extractedFiles':0}

class Export:
 def __init__(self,control):
  self.control=Path(control)
  require(self.control.resolve()in[(E/name/'control').resolve()for name in('actual-short01','actual-combined01')],'SELECTED_NEW_CASE_ONLY')
  self.guard=Guard();self.guard.check();self.binding=read(self.control/'launch-binding.json');self.run=self.binding['run'];self.single=(24 if self.control.parent.name=='actual-short01'else 168)*MIB
  require(self.run==('cockpit05-nativeio04-short-01'if self.control.parent.name=='actual-short01'else'cockpit05-nativeio04-combined-01'),'EXACT_CASE_RUN_REQUIRED')
  self.expected=read(self.control/'private-before-restart-SHA.json');self.logs=0
  require(inventory_parse(('\n'.join(h+'  '+n for n,h in self.expected.items())+'\n').encode(),self.run)==self.expected,'EXPECTED_MAP_INVALID')
 def command(self,args,timeout=20):
  self.guard.check();argv=[ADB,'-s',SERIAL,*args];started=time.monotonic_ns();output=b'';error=b'';code=None;failure=None;p=None
  try:
   p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   try:output,error=p.communicate(timeout=timeout)
   except subprocess.TimeoutExpired:
    p.kill();output,error=p.communicate(timeout=3);raise
   code=p.returncode
   require(len(output)<=262144 and len(error)<=262144,'COMMAND_OUTPUT_BOUND');require(code==0,'READONLY_ADB_COMMAND_FAILED');return output
  except BaseException as x:failure=repr(x);raise
  finally:
   self.logs+=1;put(self.control/('export-command-%02d.json'%self.logs),dict(argv=argv,PID=None if p is None else p.pid,startedNs=started,endedNs=time.monotonic_ns(),exit=code,stdout=output.decode('utf-8','replace'),stderr=error.decode('utf-8','replace'),error=failure,noRetry=True),self.guard)
 def inventory(self):return inventory_parse(self.command(['exec-out','run-as',PACKAGE,'find','files/control-runs/'+self.run,'files/workspace03','files/review-links','-type','f','-exec','sha256sum','{}','+']),self.run)
 def main(self):
  target=self.control/'native-private.tar';require(not target.exists()and not(self.control/'export-attempt-start.json').exists(),'EXPORT_ONCE_ONLY')
  prior=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))for p in exports()];used=sum(p['bytes']for p in prior)
  require(used<GLOBAL,'PRIOR_EXPORT_GLOBAL_CAP');put(self.control/'export-attempt-start.json',dict(priorExports=prior,priorBytes=used,run=self.run,guardSourceSHA256=self.guard.source,sourceSHA256=sha(__file__),deadlineSeconds=120,chunkBytes=CHUNK,noRetry=True),self.guard)
  require(self.inventory()==self.expected,'DEVICE_CHANGED_BEFORE_EXPORT')
  state=json.loads(self.command(['exec-out','run-as',PACKAGE,'cat','files/workspace-state.json']))
  require(state.get('ownerActive')is False and state.get('native',{}).get('phase')=='NO_SESSION','RESTART_NOT_INERT')
  args=[ADB,'-s',SERIAL,'exec-out','run-as',PACKAGE,'tar','-cf','-','--','files/control-runs/'+self.run,'files/workspace03','files/review-links']
  self.guard.check(CHUNK);err=(self.control/'native-export-stderr.bin').open('xb');child=None;total=0;h=hashlib.sha256();eof=False;error=None;start=time.monotonic_ns();poll=None
  try:
   child=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=err);deadline=time.monotonic()+120;poll=selectors.DefaultSelector();poll.register(child.stdout,selectors.EVENT_READ);os.set_blocking(child.stdout.fileno(),False)
   with target.open('xb',buffering=CHUNK)as sink:
    while True:
     require(time.monotonic()<=deadline,'NATIVE_EXPORT120S_DEADLINE');self.guard.check(CHUNK)
     require((self.control/'native-export-stderr.bin').stat().st_size<=MIB,'EXPORT_STDERR1MiB_CAP')
     if not poll.select(.1):continue
     chunk=os.read(child.stdout.fileno(),CHUNK)
     if not chunk:eof=True;break
     require(total+len(chunk)<=self.single and used+total+len(chunk)<=GLOBAL,'EXPORT_SINGLE_OR_GLOBAL_CAP')
     sink.write(chunk);h.update(chunk);total+=len(chunk)
    sink.flush();os.fsync(sink.fileno())
   code=child.wait(timeout=max(.01,deadline-time.monotonic()));require(code==0,'NATIVE_EXPORT_EXIT')
   require(self.inventory()==self.expected,'DEVICE_CHANGED_AFTER_EXPORT')
   cold=tar_check(target,self.expected,self.run);put(self.control/'tar-cold.json',cold,self.guard)
  except BaseException as x:
   error=repr(x)
   if child is not None and child.poll()is None:
    child.terminate()
    try:child.wait(timeout=3)
    except subprocess.TimeoutExpired:child.kill();child.wait(timeout=2)
   raise
  finally:
   if poll:poll.close()
   if child is not None:child.stdout.close()
   err.close()
   # File size is authoritative for retained failed-prefix accounting.
   retained=target.stat().st_size if target.exists()else 0
   try:
    put(self.control/'native-export-receipt.json',dict(argv=args,PID=None if child is None else child.pid,exit=None if child is None else child.poll(),startedNs=start,endedNs=time.monotonic_ns(),bytes=retained,streamBytes=total,sha256=sha(target)if target.exists()else None,streamSHA256=h.hexdigest(),EOF=eof,error=error,capBytes=self.single,previousExportBytes=used,globalRetainedBytes=used+retained,priorExports=prior,noRetry=True,publishable=error is None and eof),self.guard)
   except BaseException as receiptError:
    print(json.dumps({'receiptWriteError':repr(receiptError),'originalError':error,'retainedPath':str(target),'retainedBytes':retained,'noRetry':True}),file=sys.stderr)
    if error is None:raise
  put(self.control/'native-export-location.json',{'path':str(target),'sha256':h.hexdigest()},self.guard)
  return {'status':'CLOSED_PRIVATE_BYTES_PRESERVED_NOT_FLIGHT_ACCEPTANCE','path':str(target),'bytes':total,'sha256':h.hexdigest(),'members':len(self.expected)}
def capture(control):return Export(control).main()
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('case',choices=['actual-short01','actual-combined01']);a=p.parse_args();print(json.dumps(capture(E/a.case/'control')))
