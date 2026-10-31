from pathlib import Path
import subprocess,sys,time,json,socket
R=Path(__file__).resolve().parents[2];E=R/'evidence/alloc60';sys.path.insert(0,str(R/'pilot/sim32-journal04'))
from wal_journal import read_wal
checks=[]
for phase in ['before','after','normal']:
 out=E/'mock'/('crash02-'+phase);out.mkdir();log=(out/'console.txt').open('x')
 with socket.socket(socket.AF_INET,socket.SOCK_DGRAM)as s:
  s.bind(('127.0.0.1',0));s.settimeout(.05)
  p=subprocess.Popen([sys.executable,'-B','pilot/alloc60/crash-worker.py',str(out),phase,str(s.getsockname()[1])],cwd=R,stdout=log,stderr=subprocess.STDOUT)
  try:
   deadline=time.monotonic()+4;marker=out/('barrier-pending'if phase=='before'else'barrier-durable')
   while not marker.exists():assert p.poll()is None;assert time.monotonic()<deadline;time.sleep(.01)
   try:wire=s.recv(8192)
   except socket.timeout:wire=None
   ok=wire is None;checks.append({'name':phase+' no UDP sensor before permitted publication','pass':ok});assert ok
   if phase=='normal':
    (out/'release').write_text('explicit mock barrier release');s.settimeout(2);assert s.recv(8192)==b'sensor';p.wait(timeout=3)
   else:p.kill();p.wait(timeout=3)
  finally:
   if p.poll()is None:p.kill();p.wait(timeout=3)
   log.close()
 parsed=read_wal(out/'frames.wal');expected=['HEADER','RX','INTENT']+(['SENT','CLOSE']if phase=='normal'else[])
 ok=parsed['error']is None and [r['kind']for r in parsed['records']]==expected;checks.append({'name':phase+' exact reopen records/EOF after process closure, no repair','pass':ok});assert ok
with(E/'qa-crash02.json').open('x')as f:json.dump({'status':'PASS_PROCESS_CRASH_AND_OBSERVED_UDP_BARRIER','checks':checks,'scope':'SIGKILL before/after fsync and normal publication; process-crash readability is not power-loss durability'},f,indent=2)
print(json.dumps({'status':'PASS','checks':len(checks)}))
