"""Typed AP original bytes lossless physical role, real bounded drainer IO."""
from pathlib import Path
import io,hashlib,json,random,struct,sys,tempfile,shutil
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.foundation.ap_stage09 import *
from aeris_runtime.metadata_budget import encoded
LAB=R/'evidence/betasim-integrated01/runtime/.apstage09'
def deny(fn):
 try:fn()
 except (ValueError,RuntimeError):return
 raise AssertionError('expected invalid stage')
def run():
 assert not LAB.exists();LAB.mkdir();source=Path(sys.modules[StageDrainer.__module__].__file__);pin=hashlib.sha256(source.read_bytes()).hexdigest();groups=[]
 try:
  rng=random.Random(939);prior=None;count=0;small=0
  for seq in range(2000):
   begin=seq*833333+rng.randrange(100);raw=EVENT.pack(seq,seq//8,tuple(sorted(KINDS))[seq%len(KINDS)],1234,begin,begin+rng.randrange(1000),rng.randrange(100000),rng.randrange(1000),rng.randrange(-10,10));stored=packed_event(raw,prior);restored,physical=read_event(io.BytesIO(stored),prior);assert restored==raw and physical==stored and len(stored)<=64;small+=len(stored)<64;prior=EVENT.unpack(raw);count+=1
  assert small>0;groups.append('all-nine-original-typed-integer-fields-exact64bytes-randomchanges-negative-results-delta-only-if-smaller64')
  deny(lambda:packed_event(b'x',None));deny(lambda:packed_event(EVENT.pack(0,0,99,1,1,2,0,0,0),None));deny(lambda:packed_event(EVENT.pack(0,0,10,0,1,2,0,0,0),None));deny(lambda:packed_event(EVENT.pack(0,0,10,1,2,1,0,0,0),None));deny(lambda:read_event(io.BytesIO(stored),None));deny(lambda:read_event(io.BytesIO(stored[:-1]),prior));block=block_bytes(stored,1,raw);assert len(block)<=64;bad=bytearray(block);bad[-1]^=1
  if block.startswith(b'APS9'):deny(lambda:list(records(io.BytesIO(bad))))
  groups.append('unknown-kind-foreign-type-partial-no-state-and-compact-blockCRC-failclosed')
  d=StageDrainer(LAB/'capture','ap09','e'*32,'b'*32,events_per_chunk=16,max_events=100)
  originals=[]
  for seq in range(48):
   t=seq*833333;raw=EVENT.pack(seq,seq//8,(10,11,12,13,14,20,21,24)[seq%8],42,t,t+7,100,200,-1);originals.append(raw);d.feed(raw[:9]);d.feed(raw[9:])
  result=d.finish(ap_exit=0,eof=True);proof=verify_stage(LAB/'capture','ap09','e'*32,'b'*32,terminal_sha256=result['terminalSHA256']);assert proof['events']==48 and proof['segments']==3
  restored=[]
  for path in sorted((LAB/'capture').glob('stage-*.bin')):
   with path.open('rb')as f:
    head=json.loads(f.readline());assert head['version']==2 and head['physicalCodec']==PHYSICAL_CODEC;rows=list(records(f));assert EVENT.unpack(rows[0][0])[0]==head['startSequence'];restored.extend(q[0]for q in rows)
  assert restored==originals;groups.append('real-drainer-fsync-EOF-all-event-counts-exact-original-physicalSHA-seals-logical-eventSHA-three-segment-firstABS-reset')
  first=originals[0];assert block_bytes(first,1,first)==first
  partial=StageDrainer(LAB/'exceptional','ap09','e'*32,'b'*32,events_per_chunk=128,max_events=200);partial.feed(b''.join(originals[:7])+b'abc');deny(lambda:partial.finish(ap_exit=1,eof=False));failure=json.loads((LAB/'exceptional/failure.json').read_bytes());assert failure['pendingTailHex']=='616263'
  with (LAB/'exceptional/stage-000000.bin').open('rb')as f:f.readline();assert[q[0]for q in records(f)]==originals[:7]
  groups.append('normal-partial-block-EOF-and-exceptional-partial-original-events-flushed-no-padding-tail-retained-plain-fallback-nongrowth')
  p=LAB/'capture/stage-000000.bin';old=p.read_bytes();p.write_bytes(old[:-1]);deny(lambda:verify_stage(LAB/'capture','ap09','e'*32,'b'*32,terminal_sha256=result['terminalSHA256']));p.write_bytes(old);h,tail=old.split(b'\n',1);q=json.loads(h);q['version']=1;p.write_bytes(canonical(q)+b'\n'+tail);deny(lambda:verify_stage(LAB/'capture','ap09','e'*32,'b'*32));groups.append('version-physical-file-prefix-and-external-anchor-refuse-no-oldplain-role-fallback')
  assert pin==hashlib.sha256(source.read_bytes()).hexdigest();out=R/'evidence/betasim-integrated01/runtime/apstage09-causal-mock02.json';assert not out.exists();report={'format':'aeris-apstage09-exact64-physical-codec','status':'PASS_REAL_DRAINER_FILE_IO_NO_SIMULATOR_ACTORS','sourceSHA256':pin,'groups':groups,'originalProducerBytesCountUnchanged':True,'maximumStoredBytesPerEvent':64,'mixedPlainFallbackWhenBlockCRCHeaderWouldGrow':True,'actorsStarted':False,'sourceChangedDuringMock':False,'scratchRemoved':str(LAB.relative_to(R))};out.write_bytes(encoded(report));print(json.dumps(report))
 finally:shutil.rmtree(LAB)
if __name__=='__main__':run()
