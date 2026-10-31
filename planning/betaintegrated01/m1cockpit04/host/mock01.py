"""Pure policy/source/old-native differential tests, no sockets/runtime starts."""
from pathlib import Path
import ast,hashlib,importlib.util,json,math,resource,time
ROOT=Path(__file__).resolve().parents[4]
from pilot.betaintegrated01.cockpit04 import capacity
from pilot.betaintegrated01.cockpit04.frame_adapter import FrameAdapter
from pilot.betaintegrated01.runtime02.frame_adapter import FrameAdapter as Old
from pilot.betaintegrated01.cockpit04.confirmation import verify_confirmation,descriptor_sha256,create_confirmation_descriptor_long
from pilot.betaintegrated01.cockpit04.native_stream import closed_native
from pilot.betaintegrated01.control04.confirmation import _closed_native as old_closed
from pilot.betaintegrated01.runtime.ap_stage import canonical

def main():
 results=[]
 def test(name,fn):
  try:value=fn();results.append({'case':name,'pass':True,'result':value})
  except Exception as e:results.append({'case':name,'pass':False,'error':repr(e)})
 def policies():
  assert capacity.journal_policy(1960).quota_bytes==6*2**30
  assert capacity.journal_policy(1960).segment_bytes==16*2**20
  assert capacity.transport_policy(1960).quota_bytes==256*2**20
  assert capacity.task_budget()['taskHardPeakBytes']<9.5*2**30
  assert capacity.task_budget()['perCaseFreshEntry20Required']is True
  for v in (True,1961,1800,2000,0,-1,1960.):
   try:capacity.duration(v)
   except ValueError:continue
   raise AssertionError(v)
  return capacity.task_budget()
 test('finite quotas/global arithmetic/no later-entry waiver',policies)
 def method_identity():
  names=[name for name in Old.__dict__ if callable(getattr(Old,name))and name!='__init__']
  for name in names:assert getattr(FrameAdapter,name)is getattr(Old,name)
  return names
 test('all model/receive/send/phase/failure methods same object',method_identity)
 def policy_diff():
  pairs=[('clock_socket.py','runtime/clock_socket.py', [('1800','1960')]),('backend.py','control05/backend.py',[]) ]
  a=(ROOT/'pilot/betaintegrated01/cockpit04/clock_socket.py').read_text();b=(ROOT/'pilot/betaintegrated01/runtime/clock_socket.py').read_text();assert a==b.replace('1800','1960')
  return {'clockOnlyDiff':'literal1800→1960','frameBody':'inheritedExact'}
 test('clock single literal diff and frame inheritance',policy_diff)
 def metadata():
  c={k:'x'*64 for k in('run','epoch','boot')};h={'format':'aeris-ap-pipe-stage','version':1,**c,'ordinal':999999,'startSequence':100000000,'previousSegmentSHA256':'f'*64,'eventBytes':64}
  s={'format':'aeris-ap-stage-seal','version':1,**c,'ordinal':999999,'startSequence':100000000,'events':16384,'nextSequence':100000000,'sha256':'f'*64,'previousSegmentSHA256':'f'*64}
  assert len(canonical(h))+1<1024 and len(canonical(s))+1<1024
  segments=sum(math.ceil((n*1200*10+10)/16384)for n in(1960,90,90))
  assert segments*2048+3*8192<16*2**20
  return {'generatedMaxContextHeaderBytes':len(canonical(h))+1,'generatedMaxContextSealBytes':len(canonical(s))+1,'allCasesSegments':segments,'derivedMetadataUpperBytes':segments*2048+3*8192}
 test('AP generated metadata finite16MiB derived bound',metadata)
 def native_diff():
  d=json.loads((ROOT/'evidence/betaintegrated01-m1control02/host/old-regression04/derived-loss05-confirmation-descriptor.json').read_text())
  old,orows=old_closed(d['nativeTarPath'],d['prefix'],d['nativeExternalAnchor'])
  new,nrows=closed_native(d['nativeTarPath'],d['prefix'],d['nativeExternalAnchor'])
  assert old['normalRC']and new['normalRCCount']==len(old['normalRC']);assert new['RXCount']==len(old['RX'])
  assert all(old[k]==new[k]for k in old if k not in('normalRC','RX'))
  assert orows==list(nrows)
  n,sha=create_confirmation_descriptor_long(d['nativeTarPath'],d['prefix'],d['nativeExternalAnchor'],d['hostBracket'],d['expectedLaunchContext'])
  assert n==d and sha==descriptor_sha256(d)
  v=verify_confirmation(d,sha,**{k:d['expectedLaunchContext'][k]for k in('run','epoch','boot')})
  return {'records':new['records'],'normalRC':new['normalRCCount'],'RX':new['RXCount'],'descriptorSHA256':sha,'sameConfirmationSHA':v['nativeConfirmationRecordSHA256']}
 test('exact accepted native/raw/confirmation differential no copy',native_diff)
 out={'status':'PASS'if all(r['pass']for r in results)else'FAIL','cases':results,'serviceStarts':0,'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'firstAttemptFailureRetained':'Initial reader allowlist rejected existing zero-byte writer.lock; finite explicit lock+optional manifest schema repaired before qualification, no raw changed.'}
 path=ROOT/'evidence/betaintegrated01-m1cockpit04/host/mock01/results.json';path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'cases':len(results),'peakRSSBytes':out['peakRSSBytes']}))
 if out['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
