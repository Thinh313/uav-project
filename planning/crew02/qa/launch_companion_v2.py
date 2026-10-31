"""Owned independent operatorB runtime. Never sends aircraft commands or auto reconnects."""
from pathlib import Path
import os,sys,json,time,datetime,hashlib,subprocess,shutil,socket,signal
R=Path(__file__).resolve().parents[3];tag=sys.argv[1];assert tag.isdigit() and len(tag)==2;E=R/'evidence/crew02-runtime'/('companion'+tag);assert shutil.disk_usage(R).free>=26*2**30;E.mkdir()
with socket.socket() as probe:probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);probe.bind(('127.0.0.1',8850))
script=R/'native/crew02/host/companion.mjs';native=R/'evidence/crew02-runtime/native-public-identity02.json';assert native.is_file()
cmd=['node','--max-old-space-size=128',str(script),'--identity-dir',str(R/'.local/crew02/identity'),'--native-public',str(native),'--evidence-root',str(E)];f=(E/'console.txt').open('x');p=subprocess.Popen(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT);start=time.monotonic();samples=[];error=None
l={'at':datetime.datetime.now().astimezone().isoformat(),'hostMonoNs':str(time.monotonic_ns()),'pid':p.pid,'controllerPid':os.getpid(),'scriptSHA256':hashlib.sha256(script.read_bytes()).hexdigest(),'nativePublicSHA256':hashlib.sha256(native.read_bytes()).hexdigest(),'command':cmd,'UIOrigin':'http://127.0.0.1:8850','identity':'engineering-mTLS payload-b, privatekey excluded from evidence','automaticConnect':False,'automaticJoin':False,'automaticAuthority':False};(E/'launch.json').open('x').write(json.dumps(l,indent=2)+'\n');print(json.dumps(l),flush=True)
try:
 while not(E/'stop-request.json').exists():
  samples.append(shutil.disk_usage(R).free);assert samples[-1]>=int(20.5*2**30),'HOST_FLOOR_STOP';assert time.monotonic()-start<1200,'COMPANION_BOUND';assert p.poll() is None,'COMPANION_EXIT';assert sum(x.stat().st_size for x in E.rglob('*') if x.is_file())<24*2**20,'COMPANION_EVIDENCE_BOUND';time.sleep(.5)
except BaseException as ex:error=str(ex)
finally:
 if p.poll() is None:
  os.kill(p.pid,signal.SIGCONT);p.terminate()
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5);error=error or 'TERM_TIMEOUT_FORCED_OWNED_CHILD_STOP'
 f.close();q={'at':datetime.datetime.now().astimezone().isoformat(),'hostMonoNs':str(time.monotonic_ns()),'pid':p.pid,'exit':p.returncode,'error':error,'minFreeBytes':min(samples) if samples else shutil.disk_usage(R).free,'finalFreeBytes':shutil.disk_usage(R).free,'elapsedS':time.monotonic()-start};(E/'closure.json').open('x').write(json.dumps(q,indent=2)+'\n');print(json.dumps(q),flush=True)
