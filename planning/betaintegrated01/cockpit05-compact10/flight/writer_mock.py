"""Actual old/new writer methods and realFileIO/fsync; TEST guard, no admissionclaim."""
from pathlib import Path
from importlib import import_module
from contextlib import contextmanager
import hashlib,json,shutil,threading,time,random
R=Path(__file__).resolve().parents[4];W=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal.writer');N=import_module('planning.betaintegrated01.cockpit05-compact10.runtime.journal');P=import_module('planning.betaintegrated01.cockpit05-compact10.runtime.profile').Profile
class TestGuard:
 def check(self,*a,**k):pass
class NoProfile:
 @contextmanager
 def measure(self,*a):yield
class MemoryIO(N.D.DiagnosticIO):
 def __init__(self,hook=None):super().__init__(hook);self.buffers={};self.next=1
 def open_exclusive(self,p):fd=self.next;self.next+=1;self.buffers[fd]=bytearray();return fd
 def write(self,fd,data):
  def op():self.hook('write',fd,len(data));self.buffers[fd].extend(data);return len(data)
  return self._timed('write',fd,len(data),op)
 def fsync(self,fd):return self._timed('fsync',fd,0,lambda:self.hook('fsync',fd,0))
 def dirsync(self,path):self.hook('dirsync',None,0)
 def close(self,fd):self.hook('close',fd,0)
class MemoryProfileIO(MemoryIO):
 def __init__(self,profile,hook=None):super().__init__(hook);self.profile=profile
 _timed=N.ProfileIO._timed
def instance(cls,path,io,profile):
 o=cls.__new__(cls);o.profile=profile;o.root=path;o.run='unseen';o.epoch='epoch';o.policy=W.Policy(segment_bytes=32768,quota_bytes=2**20,max_record_bytes=2048,max_segments=64,termination_reserve_bytes=16384);o.io=io;o.guard=TestGuard();o.lock=threading.Lock();o.seq=0;o.head=W.ZERO;o.previous_segment=W.ZERO;o.segment=-1;o.fd=None;o.segment_used=0;o.used=0;o.first_seq=None;o.segment_hash=None;o.next_frame=0;o.frames=0;o.phase='BETWEEN';o.failed=None;o.closed=False;o.send_called=False;o.stage_summary={};o.seal_shas=[];o.manifest_sha=W.ZERO;o._new_segment()
 if cls is N.SegmentedJournal and not isinstance(profile,NoProfile):o.guard=N.MeasuredGuard(o.guard,profile)
 return o
def run(cls,path,profile,frames=32,fault=None,memory=False):
 trace=[];count=0
 def hook(kind,fd,n):
  nonlocal count
  trace.append((kind,n));count+=1
  if count==fault:raise OSError('SYNTHETIC_FAULT_%d'%fault)
 io=(MemoryProfileIO(profile,hook)if cls is N.SegmentedJournal and not isinstance(profile,NoProfile)else MemoryIO(hook))if memory else(N.ProfileIO(profile,hook)if cls is N.SegmentedJournal and not isinstance(profile,NoProfile)else N.D.DiagnosticIO(hook));o=None;error=None;cpu=time.thread_time_ns();wall=time.perf_counter_ns();rng=random.Random(619)
 try:
  o=instance(cls,path,io,profile)
  for frame in range(frames):
   rx=bytes(rng.randrange(256)for _ in range(40));sensor=json.dumps(dict(t=frame/1200,x=rng.random(),text='địa hình \\"/\\n'),separators=(',',':'),ensure_ascii=False).encode();o.record_frame(frame,rx,sensor,lambda body:len(body));o.append_stage(frame,dict(wireFrame=frame,randomInteger=rng.randrange(10**9)))
  o.close()
 except Exception as e:error=repr(e)
 cpu=time.thread_time_ns()-cpu;wall=time.perf_counter_ns()-wall
 if o and o.fd is not None:
  try:io.close(o.fd)
  except OSError:pass
 files={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in path.glob('*')if p.is_file()}if not memory else{str(fd):hashlib.sha256(v).hexdigest()for fd,v in io.buffers.items()}
 return dict(error=error,trace=trace,files=files,threadCPUNs=cpu,wallNs=wall,profile=None if isinstance(profile,NoProfile)else profile.snapshot())
def main():
 E=R/'evidence/betaintegrated01-cockpit05-compact10/host/writer-mock03';E.mkdir(parents=True,exist_ok=False);scratch=E/'scratch';scratch.mkdir();results=[];metrics={}
 try:
  for mode,cls,profile in [('old',W.SegmentedJournal,NoProfile()),('once',N.SegmentedJournal,NoProfile()),('profile',N.SegmentedJournal,P())]:
   p=scratch/mode;p.mkdir();metrics[mode]=run(cls,p,profile,64)
  assert metrics['old']['files']==metrics['once']['files']==metrics['profile']['files'];assert metrics['old']['trace']==metrics['once']['trace']==metrics['profile']['trace'];assert all(v['error']is None for v in metrics.values());results.append(dict(case='realFileIO_fullwriter_rotations_close_byteexact_write_fsync_sequence',pass_=True))
  faultResults=[]
  for f in(1,2,4,8,16,24,32,64,96):
   a=scratch/('old-f%d'%f);b=scratch/('new-f%d'%f);a.mkdir();b.mkdir();x=run(W.SegmentedJournal,a,NoProfile(),16,f);y=run(N.SegmentedJournal,b,P(),16,f)
   assert x['error']==y['error']and x['trace']==y['trace']and x['files']==y['files'];faultResults.append(f)
  results.append(dict(case='injectedIOposition_preserves_exception_prefix_and_syscall_sequence',pass_=True,positions=faultResults))
  memory={}
  for mode,cls,profile in [('old',W.SegmentedJournal,NoProfile()),('once',N.SegmentedJournal,NoProfile()),('profile',N.SegmentedJournal,P())]:memory[mode]=run(cls,scratch,profile,256,memory=True)
  assert memory['old']['files']==memory['once']['files']==memory['profile']['files'];results.append(dict(case='inmemory_fullwriter_CPU_comparison',pass_=True))
  out=dict(status='PASS',cases=results,actualGuardPrime=False,DiskGuard='TESTONLY_NOOP_ON_NEW_FIXTURE_INSTANCES_NO_FROZEN_PATCH',realFileIOAndFsync=True,baselineIO='ACTUAL09_DIAGNOSTICIO_CLOCKS_LAST8_NOT_PLAINFILEIO',realWriterMetrics={k:{x:v[x]for x in('threadCPUNs','wallNs','profile')}for k,v in metrics.items()},inmemoryWriterMetrics={k:{x:v[x]for x in('threadCPUNs','wallNs','profile')}for k,v in memory.items()},framesByteExact=64,sourceOldModified=False,scope='SYNTHETIC_FIELDS_REAL_IO_METHODS_NOT_MODEL_OR_ACTUAL_RUNTIME_PACING')
 finally:
  removed=sum(p.stat().st_size for p in scratch.rglob('*')if p.is_file());shutil.rmtree(scratch)
 out.update(scratchRemoved=True,removedBytes=removed);(E/'results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'realCPUNs':{k:v['threadCPUNs']for k,v in metrics.items()},'memoryCPUNs':{k:v['threadCPUNs']for k,v in memory.items()},'removedBytes':removed}))
if __name__=='__main__':main()
