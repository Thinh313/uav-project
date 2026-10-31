"""Real selected AndroidDevice._command transport with fake Popen pipes.
No Android, install, SDK daemon, QEMU or AP actor is created.
"""
from pathlib import Path
from unittest.mock import patch
import hashlib,json,os,shutil,sys,time
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(P.parent),str(T/'source'),str(R)]
from test_android_ready02 import Peer
from aeris_runtime.application09 import AndroidDomain09,PACKAGE,PRESENCE_ARGS,verify_presence_original
from aeris_runtime.metadata_budget import MetadataBudget,encoded
from aeris_runtime.once_reader import read_ref
LAB=R/'evidence/betasim-integrated01/runtime/.app-presence09'
def main():
 assert not LAB.exists();LAB.mkdir();groups=[];case_rows=[]
 try:
  for name,stdout,stderr,exitcode,expected in [('absent',b'',b'',0,'ABSENT'),('present',('package:'+PACKAGE+'\n').encode(),b'',0,'PRESENT'),('exit1-absent',b'',b'',1,'UNKNOWN'),('permission',b'',b'Permission denied\n',1,'UNKNOWN'),('error-zero',b'Error: user not found\n',b'',0,'UNKNOWN'),('substring',('package:'+PACKAGE+'.foreign\n').encode(),b'',0,'UNKNOWN'),('multiple',('package:'+PACKAGE+'\npackage:'+PACKAGE+'.extra\n').encode(),b'',0,'UNKNOWN'),('stderr-zero',b'',b'Warning\n',0,'UNKNOWN')]:
   root=LAB/name;root.mkdir();budget=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);budget.admit();device=AndroidDomain09('/mock/pinned-adb','emulator-5582',root/'sessions/test/android-api',budget=budget,observer_tag='AERIS_PRODUCT_STATUS');peer=Peer([(stdout,stderr,exitcode)]);error=None
   with patch('aeris_runtime.android.subprocess.Popen',peer):
    try:value=device.package_presence(deadline_ns=time.monotonic_ns()+2_000_000_000)
    except BaseException as e:error=e
    original=json.loads(read_ref(device.root,device.last_presence_ref));assert original['classification']==expected and original['exit']==exitcode and read_ref(device.root,original['stdoutRef'])==stdout and read_ref(device.root,original['stderrRef'])==stderr;assert len(peer.argv)==1 and not peer.replies and peer.argv[0][-1]=='pm list packages --user 0 '+PACKAGE
    if expected=='UNKNOWN':assert error is not None
    else:assert error is None and verify_presence_original(device.root,device.last_presence_ref)['classification']==expected
    try:device.package_presence(deadline_ns=time.monotonic_ns()+1_000_000_000)
    except ValueError as e:assert'ONE_PRESENCE_QUERY_NO_RETRY'in str(e)
    else:raise AssertionError('presence retried')
    assert len(peer.argv)==1
   case_rows.append({'case':name,'classification':expected,'processExit':exitcode,'originalArgvStdoutStderrExitRetained':True,'physicalDispatches':1,'installDispatched':False})
  groups.append('actual-base-command-empty-exit0-ABSENT-exactline-PRESENT-nonzero-permission-errors-substring-multiple-stderr-UNKNOWN-no-retry')
  device._presence_attempted=False;peer=Peer([])
  with patch('aeris_runtime.android.subprocess.Popen',peer):
   for args in [list(PRESENCE_ARGS[:5])+['1',PACKAGE],['shell','pm','list','packages','--user','0','foreign']]:
    try:device.command(args,deadline_ns=time.monotonic_ns()+1_000_000_000,maximum_bytes=256)
    except ValueError:pass
    else:raise AssertionError('foreign query admitted')
   assert not peer.argv
  groups.append('wronguser-and-foreign-package-refused-at-exact-source-allowlist-beforePopen')
  out=R/'evidence/betasim-integrated01/runtime/application09-presence-transport-mock01.json';assert not out.exists();report={'format':'aeris-fixed-package-presence-real-command-transport','status':'PASS_REAL_SOURCE_COMMAND_CAPTURE_FAKE_POPEN_PIPES_NOT_ANDROID','groups':groups,'cases':case_rows,'sourcePins':{name:hashlib.sha256((T/'source/aeris_runtime'/name).read_bytes()).hexdigest()for name in('application09.py','android.py')},'actorsStarted':False,'genericNonzeroExitRelaxed':False,'attemptRetried':False,'scratchRemoved':str(LAB.relative_to(R))};out.write_bytes(encoded(report));print(json.dumps(report))
 finally:shutil.rmtree(LAB)
if __name__=='__main__':main()
