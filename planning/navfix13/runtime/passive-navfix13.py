#!/usr/bin/env python3
"""Root-only20s source probe; no Android, AP, authority or candidate identity."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,sys,time
R=Path(__file__).resolve().parents[3];S=Path(__file__).resolve().parent/'source'
os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(S),str(R)]
from aeris_runtime.darwin_disk11 import HostDiskObserver,fixed_paths,decode,FILE_MAX
p=argparse.ArgumentParser();p.add_argument('--spec',required=True);p.add_argument('--output',required=True);p.add_argument('--seconds',type=int,choices=(20,),default=20);a=p.parse_args()
target=Path(a.output).absolute();expected=R/'evidence/navfix13/passive/host-disk-attribution.bin'
if target!=expected or target.exists()or target.parent.exists()or any(x.is_symlink()for x in[target,*target.parents]):raise ValueError('HOSTDIAG11_PASSIVE_ONE_FIXED_OUTPUT')
if shutil.disk_usage(R).free<10*2**30+256*2**20+80*1024:raise ValueError('HOSTDIAG11_PASSIVE_ORIGINAL_FLOOR')
spec=json.loads(Path(a.spec).read_bytes());source=S/'aeris_runtime/darwin_disk11.py';digest=hashlib.sha256(source.read_bytes()).hexdigest();observer=HostDiskObserver(R,fixed_paths(spec),candidate='0'*64,source=digest,scope='PASSIVE_SOURCE_PROBE');start=time.monotonic_ns();primary=None;observer.start()
try:
 until=start+20_000_000_000
 while time.monotonic_ns()<until:
  if observer.failure:raise RuntimeError('HOSTDIAG11_PASSIVE_CAPTURE_FAILED:'+observer.failure)
  time.sleep(max(0,min(.1,(until-time.monotonic_ns())/1e9)))
except BaseException as e:primary=e
finally:observer.retire();observer.stop()
raw=observer.export();value=decode(raw,candidate='0'*64,source=digest)
if len(raw)>FILE_MAX or shutil.disk_usage(R).free-len(raw)<10*2**30+256*2**20:raise ValueError('HOSTDIAG11_PASSIVE_FINAL_FLOOR')
target.parent.mkdir()
with target.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
receipt={'format':'aeris-hostdiag11-passive-source-probe','status':'CAPTURE_FAILED_PRESERVED_NOT_ACCEPTANCE'if primary is not None or observer.failure else'CAPTURED_NON_AUTHORIZING_NOT_RUNTIME_ACCEPTANCE','scope':'PASSIVE_SOURCE_PROBE','candidateIdentity':None,'sourceSHA256':digest,'startedHostNs':start,'endedHostNs':time.monotonic_ns(),'rawBytes':len(raw),'rawSHA256':hashlib.sha256(raw).hexdigest(),'maximumRawBytes':FILE_MAX,'samplesRetained':len(value['rows']),'threadCPUObservedNs':sum(row['threadCPU']for row in value['rows']),'sampleMaximumObservedNs':max((row['end']-row['begin']for row in value['rows']),default=None),'observerFailure':observer.failure,'primaryFailure':None if primary is None else type(primary).__name__+':'+str(primary)[:192],'causalProcess':'UNKNOWN_UNLESS_COLD_EVIDENCE_SUPPORTS_MORE','AndroidOrAPStarted':False}
body=(json.dumps(receipt,sort_keys=True,separators=(',',':'))+'\n').encode()
if len(body)>4096:raise ValueError('HOSTDIAG11_PASSIVE_RECEIPT4096')
with(target.parent/'receipt.json').open('xb')as f:f.write(body);f.flush();os.fsync(f.fileno())
print(body.decode(),end='')
if primary is not None:raise primary
if observer.failure:raise RuntimeError('HOSTDIAG11_PASSIVE_CAPTURE_FAILED:'+observer.failure)
