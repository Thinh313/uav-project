"""Independent byte/CRC/typed-bound checks. No AP, pipe actor or large copy."""
from pathlib import Path
import hashlib,io,json,os,random,shutil,struct,sys,zlib
R=Path(__file__).resolve().parents[3];T=R/'planning/betasim-integrated01/runtime';sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.foundation import ap_stage09 as A
from aeris_runtime.metadata_budget import encoded
checks=[]
def deny(fn):
 try:fn()
 except Exception:return
 raise AssertionError('negative unexpectedly admitted')
def test(name,fn):fn();checks.append(name)
def event(seq=0,frame=0,kind=10,tid=1,begin=100,end=101,arg=2,extra=3,result=-1):return struct.pack('<QQIIQQQQq',seq,frame,kind,tid,begin,end,arg,extra,result)
def pack_many(rows):
 out=bytearray();prior=None
 for row in rows:out.extend(A.packed_event(row,prior));prior=struct.unpack('<QQIIQQQQq',row)
 return bytes(out)
def inverse_bound():
 rng=random.Random(9412);rows=[event(i,i//10,10+i%5,7,100+i,101+i,rng.randrange(2**64),rng.randrange(2**64),rng.randrange(-2**63,2**63))for i in range(128)]
 stored=A.block_bytes(pack_many(rows),len(rows),b''.join(rows));decoded=list(A.records(io.BytesIO(stored)))
 assert [r for r,p in decoded]==rows and b''.join(p for r,p in decoded)==stored and len(stored)<=128*64
def extremes():
 rows=[event(seq=0,frame=2**64-1,begin=0,end=2**64-1,arg=2**64-1,extra=0,result=-2**63),event(seq=1,frame=0,begin=2**64-1,end=2**64-1,arg=0,extra=2**64-1,result=2**63-1)]
 prior=None
 for raw in rows:
  stored=A.packed_event(raw,prior);assert len(stored)==64;assert A.read_event(io.BytesIO(stored),prior)[0]==raw;prior=struct.unpack('<QQIIQQQQq',raw)
 for raw in[event(seq=100000000),event(seq=2**64-1),event(kind=9),event(tid=0),event(begin=102,end=101)]:deny(lambda:A.packed_event(raw,None))
def mixed_and_basis():
 rows=[event(i,i//10)for i in range(128)];original=b''.join(rows);plain=A.block_bytes(original,128,original);assert plain==original and len(plain)==8192
 later=[event(128,13),event(129,13)];packed=A.block_bytes(pack_many(later),2,b''.join(later));assert packed.startswith(b'APS9')
 assert b''.join(r for r,_ in A.records(io.BytesIO(plain+packed)))==original+b''.join(later)
 a=event(0,0,10,1,10**15,10**15+10,2**64-1,2**64-2,-1);b=event(1,1,10,1,10**15+100,10**15+110,0,0,0);stored=A.packed_event(b,struct.unpack('<QQIIQQQQq',a));assert stored.startswith(A.ESCAPE)and stored[8]&128;assert A.read_event(io.BytesIO(stored),struct.unpack('<QQIIQQQQq',a))[0]==b
def state_and_crc():
 a,b=event(),event(1);delta=A.packed_event(b,struct.unpack('<QQIIQQQQq',a));assert delta.startswith(A.ESCAPE)
 deny(lambda:A.read_event(io.BytesIO(delta),None))
 stored=A.block_bytes(a+delta,2,a+b);assert stored.startswith(b'APS9')
 for where in[0,5,8,len(stored)-1]:
  bad=bytearray(stored);bad[where]^=1;it=A.records(io.BytesIO(bad));deny(lambda:next(it))
 for n in[1,7,11,len(stored)-1]:deny(lambda:list(A.records(io.BytesIO(stored[:n]))))
 # A fresh independently encoded segment starts ABS, not last segment delta.
 assert A.packed_event(b,None)==b
def varint_negatives():
 prior=struct.unpack('<QQIIQQQQq',event())
 def delta(data):return A.ESCAPE+bytes([len(data)])+data
 for data in[b'\x80\x00'+bytes(8),b'\x80'*10+bytes(8),bytes(8),bytes(10),b'\xff'*9+b'\x02'+bytes(8)]:deny(lambda:A.read_event(io.BytesIO(delta(data)),prior))
 # Canonical delta -1 from an unsigned zero must refuse typed underflow.
 deny(lambda:A.read_event(io.BytesIO(delta(b'\x01'+bytes(8))),prior))
 deny(lambda:A.read_event(io.BytesIO(A.ESCAPE+b'\x09'+bytes(7)),prior))
def cold_disk():
 scratch=R/'planning/betasim-integrated01/qa/.apstage09-fixture';assert not scratch.exists()
 try:
  d=A.StageDrainer(scratch,'qa-ap09','e'*32,'b'*32,events_per_chunk=13,max_events=200)
  original=b''.join(event(i,i//10,10+i%5,7,100+i,101+i,i,i*3,-i)for i in range(140))
  for at in range(0,len(original),17):d.feed(original[at:at+17])
  terminal=d.finish(ap_exit=0,eof=True);result=A.verify_stage(scratch,'qa-ap09','e'*32,'b'*32,terminal_sha256=terminal['terminalSHA256']);assert result['events']==140 and result['segments']==11 and result['APExecutionAccepted']is False
  restored=b''
  for p in sorted(scratch.glob('stage-*.bin')):
   with p.open('rb')as f:f.readline();restored+=b''.join(r for r,_ in A.records(f))
  assert restored==original
  deny(lambda:A.verify_stage(scratch,'qa-ap09','f'*32,'b'*32))
  # Cold reader must reject malformed original chronology even after an attacker
  # recomputes physical CRC/hash and seal/logical SHA. External anchor is omitted
  # deliberately: this probes semantics rather than relying on a trusted digest.
  p=scratch/'stage-000000.bin';head,payload=p.read_bytes().split(b'\n',1);badrows=[event(i,i//10,10+i%5,7,100+i,101+i,i,i*3,-i)for i in range(13)];badrows[0]=event(0,0,9,7)
  malformed=A.block_bytes(b''.join(badrows),13,b''.join(badrows));p.write_bytes(head+b'\n'+malformed)
  sealp=scratch/'stage-000000.seal.json';seal=json.loads(sealp.read_bytes());seal['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();seal['logicalEventSHA256']=hashlib.sha256(b''.join(badrows)).hexdigest();sealp.write_bytes(encoded(seal));deny(lambda:A.verify_stage(scratch,'qa-ap09','e'*32,'b'*32))
 finally:
  if scratch.exists():shutil.rmtree(scratch)
def version_scope():
 ctx={'run':'qa-ap09','epoch':'e'*32,'boot':'b'*32};header={'format':'aeris-ap-pipe-stage','version':2,'physicalCodec':A.PHYSICAL_CODEC,**ctx,'ordinal':0,'startSequence':0,'previousSegmentSHA256':'0'*64,'eventBytes':64}
 A._schema(header,'header',ctx)
 for key,value in[('version',1),('version',True),('physicalCodec','APSTAGE_PLAIN_V1'),('eventBytes',True),('ordinal',False)]:deny(lambda:A._schema({**header,key:value},'header',ctx))
 # Frozen original reader source has explicit version1 requirement; it is not
 # modified/reused as an implicit version2 decoder.
 old=R/'pilot/betaintegrated01/runtime/ap_stage.py';assert old.exists();assert "obj['version'] != 1"in old.read_text()
test('128_exact64_inverse_with_block_or_original_plain_fallback_never_over8192bytes',inverse_bound)
test('unsigned_signed_extremes_exact_absolute_fallback_and_escape_domain',extremes)
test('allABS_8192byte_fallback_mixed_blocks_and_exact_uint64_signed_time_basis',mixed_and_basis)
test('full_block_crc_before_first_yield_partial_eof_and_segment_reset',state_and_crc)
test('noncanonical_overflow_underflow_trailing_partial_delta_refused',varint_negatives)
test('real_small_segmented_files_cold_anchor_context_original_chronology',cold_disk)
test('version2_explicit_codec_schema_and_old_reader_unchanged',version_scope)
p=T/'source/aeris_runtime/foundation/ap_stage09.py';old=R/'pilot/betaintegrated01/runtime/ap_stage.py';out=R/(sys.argv[1]if len(sys.argv)>1 else'evidence/betasim-integrated01/qa/ap-stage09-01.json');assert not out.exists();out.write_bytes(encoded({'format':'aeris-independent-apstage09-source-qa','status':'PASS_LOCAL_SMALL_FILES_NOT_ACTUAL_AP_OR_DURABILITY','checks':checks,'sourcePins':{str(q.relative_to(R)):hashlib.sha256(q.read_bytes()).hexdigest()for q in[p,old]},'actorsStarted':False,'scratchRemoved':['planning/betasim-integrated01/qa/.apstage09-fixture'],'actualAP':False,'exportCapacityAccepted':False}));print(json.dumps({'status':'PASS','checks':len(checks),'path':str(out.relative_to(R)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
