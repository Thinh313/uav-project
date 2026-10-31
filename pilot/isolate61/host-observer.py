"""Read-only host context, fixed2s cadence, bounded180s. No process intervention."""
import datetime,json,os,shutil,subprocess,sys,time,signal
from pathlib import Path
R=Path(__file__).resolve().parents[2];run=sys.argv[1];assert run.isalnum();out=R/'evidence/isolate61/runs'/run;stop=False
def end(*_):
 global stop;stop=True
signal.signal(signal.SIGTERM,end);signal.signal(signal.SIGINT,end)
with(out/'host-observer.jsonl').open('x')as f:
 started=time.monotonic();lastPower=0;power=None
 while not stop and time.monotonic()-started<180 and not(out/'closure.json').exists():
  t=time.monotonic_ns();processes=[]
  result=subprocess.run(['ps','-A','-o','pid=,pcpu=,pmem=,comm='],capture_output=True,text=True,timeout=2)
  for line in result.stdout.splitlines():
   parts=line.split(None,3)
   if len(parts)==4:
    try:processes.append({'pid':int(parts[0]),'cpuPercent':float(parts[1]),'memoryPercent':float(parts[2]),'executable':parts[3]})
    except ValueError:pass
  if time.monotonic()-lastPower>=10:
   power={k:subprocess.run(a,capture_output=True,text=True,timeout=2).stdout for k,a in {'battery':['pmset','-g','batt'],'thermal':['pmset','-g','therm']}.items()};lastPower=time.monotonic()
  row={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostMonotonicNs':t,'freeBytes':shutil.disk_usage(R).free,'loadAverage':os.getloadavg(),'processes':sorted(processes,key=lambda p:p['cpuPercent'],reverse=True)[:12],'psExitCode':result.returncode,'power':power,'vmStat':subprocess.run(['vm_stat'],capture_output=True,text=True,timeout=2).stdout,'iostat':subprocess.run(['iostat','-I','-d'],capture_output=True,text=True,timeout=2).stdout,'scope':'Point samples; CPU percentages are OS averages, not instantaneous causal attribution'}
  f.write(json.dumps(row,separators=(',',':'))+'\n');f.flush()
  for _ in range(20):
   if stop or(out/'closure.json').exists():break
   time.sleep(.1)
 f.flush();os.fsync(f.fileno())
