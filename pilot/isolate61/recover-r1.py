"""Explicit forensic recovery of failed owned R1, never rewrites its closure/status."""
from pathlib import Path
import subprocess,json,time,sys
from archive import export,source_digest,digest
R=Path(__file__).resolve().parents[2];E=R/'evidence/isolate61';d=json.loads((E/'s61R1-driver-result.json').read_text());out=E/'runs'/d['owner']['run'];launch=json.loads((out/'launch.json').read_text());cid=launch['containerId'];info=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
assert info['Config']['Labels']['aeris.task']=='isolate61'and info['Config']['Labels']['aeris.run']==out.name and info['Id']==cid
pid=subprocess.check_output(['docker','exec',cid,'cat','/state/ap.pid'],text=True).strip();assert pid.isdigit();cmd=subprocess.check_output(['docker','exec',cid,'cat',f'/proc/{pid}/cmdline']);assert cmd.startswith(b'/aeris/arducopter\0')
subprocess.run(['docker','exec',cid,'/bin/kill','-KILL',pid],check=True)
for _ in range(60):
 p=subprocess.run(['docker','exec',cid,'cat','/state/observer-exit-code'],capture_output=True,text=True)
 if p.returncode==0:break
 time.sleep(.05)
assert p.returncode==0
subprocess.run(['docker','exec',cid,'/instrument/traceflush','/evidence/ap-timing.bin'],check=True)
a=source_digest(cid,'/evidence/ap-timing.bin');assert a['sha256']==digest(out/'ap-timing.bin')
files=[{'source':'/evidence/ap-timing.bin','destination':'ap-timing.bin',**a,'sameImmutableSourceBytes':True}]
for source,name in [('/probe/guest-scheduler.jsonl','guest-scheduler.jsonl'),('/probe/guest-result.json','guest-result.json'),('/state/ap-exit-code','ap-exit-code'),('/state/observer-exit-code','observer-exit-code')]:files.append(export(cid,source,out/name))
subprocess.run(['docker','stop','-t','2',cid],check=True,capture_output=True)
with(out/'forensic-recovery.json').open('x')as f:json.dump({'status':'FAILED_RUN_FORENSIC_SOURCE_EXPORTED_AND_CONTAINER_STOPPED','containerId':cid,'apChildForcedKill':True,'notFlightCompletion':True,'originalClosureUntouched':True,'guestObserverError':json.loads((out/'guest-result.json').read_text())['error'],'files':files},f,indent=2)
print('R1 failed evidence source verified, owned AP/container closed')
