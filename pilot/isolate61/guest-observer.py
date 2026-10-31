"""Read-only guest scheduler counters; writes only bounded guest tmpfs."""
from pathlib import Path
import os,time,signal,json,sys
out=Path(sys.argv[2]);out.mkdir(exist_ok=True);pid=int(Path(sys.argv[1]).read_text());stopped=False
signal.signal(signal.SIGTERM,lambda *_:globals().__setitem__('stopped',True))
period=20000000;due=time.monotonic_ns();rows=0;error=None;reason=None;lastContext=0;context=None

def read(p):
 try:return Path(p).read_text()
 except OSError:return None
try:
 with(out/'guest-scheduler.jsonl').open('x')as f:
  while not stopped and rows<8000:
   now=time.monotonic_ns()
   if now<due:time.sleep((due-now)/1e9)
   actual=time.monotonic_ns();missed=max(0,(actual-due)//period);tasks=[]
   try:tids=list((Path('/proc')/str(pid)/'task').iterdir())
   except FileNotFoundError:reason='AP_EXIT_OBSERVED';break
   for td in tids:
    raw=read(td/'schedstat');stat=read(td/'stat')
    if raw is None or stat is None:continue
    fields=stat[stat.rfind(')')+2:].split();sched=[int(v)for v in raw.split()]
    if len(sched)!=3:raise RuntimeError('SCHEDSTAT_SHAPE')
    tasks.append({'tid':int(td.name),'schedstat':sched,'state':fields[0],'startTicks':int(fields[19]),'minorFaults':int(fields[7]),'majorFaults':int(fields[9]),'rawStat':stat})
   if actual-lastContext>=1000000000:
    context={p:read(p)for p in ['/proc/sys/kernel/sched_schedstats','/proc/pressure/cpu','/proc/pressure/io','/proc/pressure/memory','/sys/fs/cgroup/cpu.stat','/sys/fs/cgroup/io.stat','/sys/fs/cgroup/memory.current','/sys/fs/cgroup/memory.events']};lastContext=actual
   row={'index':rows,'scheduledNs':due,'guestMonotonicNs':actual,'observerThreadCpuNs':time.thread_time_ns(),'missedDeadlines':missed,'pid':pid,'tasks':tasks,'context':context};line=json.dumps(row,separators=(',',':'))+'\n'
   if f.tell()+len(line)>8*2**20:raise RuntimeError('GUEST_OBSERVER_QUOTA')
   f.write(line);rows+=1;due+=(missed+1)*period
  else:reason='SIGNAL_STOP'if stopped else'ROW_BOUND'
  f.flush();os.fsync(f.fileno())
except BaseException as exc:error=str(exc)
with(out/'guest-result.json').open('x')as f:json.dump({'rows':rows,'error':error,'reason':reason,'pid':pid,'periodNs':period,'scope':'Guest kernel per-task schedstat counters, not host runnable wait; zeros/unavailable are not zero contention proof. Raw stat birth identity retained.'},f,indent=2)
if error:raise SystemExit(1)
