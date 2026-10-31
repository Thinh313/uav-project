"""Immutable export via container mount namespace; fail closed before tmpfs teardown."""
from pathlib import Path
import subprocess,json,hashlib,os

def digest(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def source_digest(cid,source):
 code="import hashlib,json,sys,os;h=hashlib.sha256();f=open(sys.argv[1],'rb');n=0\nfor b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)\nprint(json.dumps({'sha256':h.hexdigest(),'bytes':n}))"
 return json.loads(subprocess.check_output(['docker','exec',cid,'python3','-B','-c',code,source],text=True,timeout=30))
def export(cid,source,dest):
 assert not dest.exists();proc=subprocess.Popen(['docker','exec',cid,'/bin/cat',source],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  with dest.open('xb')as f:
   for b in iter(lambda:proc.stdout.read(1048576),b''):f.write(b)
   f.flush();os.fsync(f.fileno())
  proc.stdout.close();code=proc.wait(timeout=20);error=proc.stderr.read().decode();assert code==0,error
  original=source_digest(cid,source)
  assert original['bytes']==dest.stat().st_size and original['sha256']==digest(dest),'IMMUTABLE_SOURCE_COPY_SHA'
 finally:
  if proc.poll()is None:proc.kill();proc.wait()
 return {'source':source,'destination':dest.name,**original,'sameImmutableSourceBytes':True,'transfer':'DOCKER_EXEC_CAT_STDOUT_FSYNCED_HOST_COPY'}
def archive(cid,out,trace_mode):
 subprocess.run(['docker','exec',cid,'/bin/sh','/diagnostics/stop-ap.sh'],check=True,timeout=10,capture_output=True)
 state=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0];assert state['Id']==cid and state['State']['Running']
 source='/evidence/ap-timing.bin'if trace_mode=='bind'else'/ap-trace/ap-timing.bin'
 subprocess.run(['docker','exec',cid,'/instrument/traceflush',source],check=True,timeout=10,capture_output=True)
 files=[]
 if trace_mode=='tmpfs':files.append(export(cid,source,out/'ap-timing.bin'))
 else:
  original=source_digest(cid,source);assert original['sha256']==digest(out/'ap-timing.bin') and original['bytes']==(out/'ap-timing.bin').stat().st_size
  files.append({'source':source,'destination':'ap-timing.bin',**original,'sameImmutableSourceBytes':True,'transfer':'BIND_MOUNT_SAME_SOURCE_BYTE_VERIFIED'})
 for source,name in [('/probe/guest-scheduler.jsonl','guest-scheduler.jsonl'),('/probe/guest-result.json','guest-result.json'),('/state/ap-exit-code','ap-exit-code'),('/state/observer-exit-code','observer-exit-code')]:files.append(export(cid,source,out/name))
 assert(out/'observer-exit-code').read_text().strip()=='0';assert json.loads((out/'guest-result.json').read_text())['error']is None
 with(out/'guest-archive.json').open('x')as f:json.dump({'status':'PASS_IMMUTABLE_SOURCE_SHA_EXPORT_BEFORE_CONTAINER_STOP','containerId':cid,'traceMode':trace_mode,'apWriterReaped':True,'files':files},f,indent=2)
 return files
