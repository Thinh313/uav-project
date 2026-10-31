from pathlib import Path
from importlib import import_module
import hashlib,json,sys,tarfile,time
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[6];sys.path.insert(0,str(R));E=R/'evidence/betaintegrated01-cockpit05-entry10-flight';C=E/'actual-combined01/control';A=R/'evidence/betaintegrated01-cockpit05-closure01/native-private02.tar';P='files/control-runs/cockpit05-entry10-combined-01/';O=E/'qa/actual-prefix01';began=time.monotonic()
receipt=json.loads((A.parent/'native-export02-receipt.json').read_text());source=import_module('pilot.betaintegrated01.cockpit04.revision02.native_stream').IndexedNative(A,P);binding=json.loads((C/'launch-binding.json').read_text());auth=import_module('planning.betaintegrated01.m1cockpit04.qa.native_authority02')
command=C/'android/0710-adb-72ad8f9e';readback=C/'android/0711-adb-46b42c3e'
def command_bytes(directory,expected):
 r=json.loads((directory/'receipt.json').read_text());assert r['argv']==expected and type(r['exit'])is int and r['exit']==0 and r['timedOut']is False
 for label in('stdout','stderr'):
  b=(directory/(label+'.bin')).read_bytes();assert len(b)==r[label+'Bytes']and hashlib.sha256(b).hexdigest()==r[label+'SHA256']
 return(directory/'stdout.bin').read_bytes(),r
adb=['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','-s','emulator-5582']
raw,cr=command_bytes(command,adb+['exec-out','run-as','vn.rtr.aeris.cockpit05','find','files/control-runs/'+binding['run'],'files/workspace03','files/review-links','-type','f','-exec','sha256sum','{}','+'])
mp={}
for line in raw.decode().splitlines():
 h,name=line.split(None,1);assert name not in mp;mp[name]=h
assert mp==json.loads((C/'private-before-restart-SHA.json').read_text());anchor=mp[P+'session.json'];assert anchor==hashlib.sha256(source.read('session.json')).hexdigest()
rawstate,sr=command_bytes(readback,adb+['shell','run-as','vn.rtr.aeris.cockpit05','cat','files/workspace-state.json']);state=json.loads(rawstate);n=state['native'];assert all(n[k]==binding[k]for k in('run','epoch','boot','generation'));assert n['closed']is True and n['journal']['closed']is True and n['journal']['commitAnchor']==anchor and n['journal']['records']==109128 and n['input']['consent']is False and n['input']['leaseId']is None
assert cr['atUTC']<=sr['atUTC'];assert source.tar_sha==receipt['sha256']
provenance={'deviceSHACommandReceiptSHA256':hashlib.sha256((command/'receipt.json').read_bytes()).hexdigest(),'deviceSHAStdoutSHA256':cr['stdoutSHA256'],'closedSnapshotReceiptSHA256':hashlib.sha256((readback/'receipt.json').read_bytes()).hexdigest(),'closedSnapshotStdoutSHA256':sr['stdoutSHA256'],'deviceSHAObservedUTC':cr['atUTC'],'closedSnapshotObservedUTC':sr['atUTC'],'privateMapFiles':len(mp)}

try:
 result=auth.audit(str(A),P,anchor,binding,scenario='INCOMPLETE_HOST_CASE_NO_INTENTIONAL_CUT')
 result.update(status='NATIVE_CHAIN_AUTHORITY_EXTERNALLY_MATCHED_ROOT_DEVICE_BYTES_PREFIX_ONLY',anchorProvenance='OUTSIDE_ARCHIVE_ROOT_DEVICE_SHA_OBSERVATION_WITH_MATCHING_CLOSED_SNAPSHOT_NOT_POWERLOSS_OR_SOURCE_AUTH',derivedSessionSHA256=anchor,archiveSHA256=source.tar_sha,archiveBytes=A.stat().st_size,archiveReceiptSHA256=hashlib.sha256((A.parent/'native-export02-receipt.json').read_bytes()).hexdigest(),coldAllRows=result['records'],externallyClosedNativeAnchorObserved=True,externalObservation=provenance,actualThirtyMinuteAccepted=False,wholeBetaAccepted=False,durationSeconds=time.monotonic()-began)
 (O/'native-external02.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in['status','records','inputs','secondLeaseProducerWindowNs','secondLeaseUptimeWindowNs','maxLease2ProducerGapNs','durationSeconds']}))
except BaseException as e:
 (O/'native-external02-failure.json').open('x').write(json.dumps({'status':'NATIVE_COLD_FAILURE_RETAINED_NO_ACCEPTANCE','error':repr(e),'derivedSessionSHA256':anchor,'anchorDerivedNotExternal':True,'archiveSHA256':source.tar_sha,'durationSeconds':time.monotonic()-began},indent=2)+'\n');raise
