"""Bounded Root-operated read-only host diagnostic; no runtime launch or cleanup."""
from pathlib import Path
import ctypes,datetime,hashlib,json,os,plistlib,re,shutil,subprocess,time

R=Path(__file__).resolve().parents[2]
E=R/'evidence/hostdiag08'
E.mkdir(parents=True,exist_ok=True)
HEADER=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/sys/resource.h')
src=HEADER.read_text();body=re.search(r'struct rusage_info_v4\s*\{(.*?)\};',src,re.S).group(1)
names=re.findall(r'uint64_t\s+(ri_\w+);',body)
assert len(names)==35,('SDK_LAYOUT_CHANGED',len(names))
class Usage(ctypes.Structure):
 _fields_=[('ri_uuid',ctypes.c_uint8*16)]+[(n,ctypes.c_uint64)for n in names]
assert ctypes.sizeof(Usage)==296
lib=ctypes.CDLL('/usr/lib/libproc.dylib',use_errno=True)
lib.proc_listallpids.argtypes=[ctypes.c_void_p,ctypes.c_int];lib.proc_listallpids.restype=ctypes.c_int
lib.proc_name.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_uint32];lib.proc_name.restype=ctypes.c_int
lib.proc_pid_rusage.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_void_p];lib.proc_pid_rusage.restype=ctypes.c_int

def command(argv,limit=2**20):
 p=subprocess.run(argv,capture_output=True,timeout=5)
 assert len(p.stdout)<=limit and len(p.stderr)<=8192,'COMMAND_OUTPUT_BOUND'
 return p.returncode,p.stdout,p.stderr.decode(errors='replace')

def processes():
 pids=(ctypes.c_int*32768)();n=lib.proc_listallpids(pids,ctypes.sizeof(pids));assert 0<=n<32768
 rows=[];errors={}
 for pid in pids[:n]:
  if pid<=0:continue
  u=Usage();ctypes.set_errno(0)
  if lib.proc_pid_rusage(pid,4,ctypes.byref(u))!=0:
   err=str(ctypes.get_errno());errors[err]=errors.get(err,0)+1;continue
  b=ctypes.create_string_buffer(256);lib.proc_name(pid,b,len(b))
  rows.append({'pid':pid,'name':b.value.decode(errors='replace'),'start':str(u.ri_proc_start_abstime),'written':u.ri_diskio_byteswritten,'read':u.ri_diskio_bytesread,'logicalWrites':u.ri_logical_writes,'footprint':u.ri_phys_footprint})
 return {'processes':rows,'deniedOrGoneByErrno':errors}

def apfs():
 code,raw,err=command(['diskutil','apfs','list','-plist'])
 if code:return {'error':err,'exit':code}
 data=plistlib.loads(raw)
 for c in data['Containers']:
  if any('Data'in v.get('Roles',[])for v in c.get('Volumes',[])):
   return {'container':c['ContainerReference'],'free':c['CapacityFree'],'volumes':[{'device':v['DeviceIdentifier'],'roles':v.get('Roles',[]),'allocated':v['CapacityInUse']}for v in c['Volumes']]}
 return {'error':'DATA_CONTAINER_NOT_FOUND'}

def stat(path):
 v=os.statvfs(path);return {'bavailBytes':v.f_bavail*v.f_frsize,'bfreeBytes':v.f_bfree*v.f_frsize,'device':os.stat(path).st_dev}

limit=16*2**20;used=0;rows=[];head='0'*64
def emit(f,row):
 global used,head
 payload=json.dumps(row,separators=(',',':'),allow_nan=False).encode();h=hashlib.sha256(payload).hexdigest()
 line=json.dumps({'previousSha256':head,'body':row,'sha256':h},separators=(',',':')).encode()+b'\n'
 assert used+len(line)<=limit,'DIAGNOSTIC16MIB_BOUND'
 f.write(line);f.flush();used+=len(line);head=h

start=time.monotonic();failure=None
with(E/'samples01.jsonl').open('xb')as f:
 try:
  for i in range(181):
   delay=start+i-time.monotonic()
   if delay>0:time.sleep(delay)
   now=time.monotonic();free=shutil.disk_usage(R).free
   assert free>=20*2**30,'READONLY_DIAGNOSTIC_STOP_BELOW20GIB'
   row={'index':i,'mono':now,'elapsedS':now-start,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'free':free,'stat':{n:stat(p)for n,p in [('repo',R),('root','/'),('data','/System/Volumes/Data')]}}
   if i%5==0:
    row.update(processes());code,raw,err=command(['sysctl','vm.swapusage']);row['swap']={'exit':code,'text':raw.decode(errors='replace').strip(),'error':err}
    code,raw,err=command(['vm_stat']);row['vmStat']={'exit':code,'text':raw.decode(errors='replace'),'error':err}
   if i%10==0:row['apfs']=apfs()
   row['observationFinishedMono']=time.monotonic();emit(f,row);rows.append({'mono':now,'free':free,'index':i})
   if i%30==0:print(json.dumps({'index':i,'freeGiB':free/2**30,'elapsedS':now-start}),flush=True)
 except BaseException as e:failure=type(e).__name__+':'+str(e);raise
 finally:
  os.fsync(f.fileno())
  receipt={'classification':'HOST_OBSERVATION_NOT_CAMPAIGN_ADMISSION','startedMono':start,'endedMono':time.monotonic(),'samples':len(rows),'minimumFreeBytes':min((r['free']for r in rows),default=None),'maximumFreeBytes':max((r['free']for r in rows),default=None),'bytes':used,'head':head,'failure':failure,'SDKHeaderSha256':hashlib.sha256(HEADER.read_bytes()).hexdigest(),'rusageVersion':4,'rusageSize':ctypes.sizeof(Usage),'rusageU64Fields':names,'noRuntimeLaunched':True,'noSystemOrUserDataChanges':True}
  with(E/'collection01.json').open('x')as out:json.dump(receipt,out,indent=2)
