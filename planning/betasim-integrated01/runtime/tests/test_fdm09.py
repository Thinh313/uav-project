"""Byte-exact physical compaction, bounded adversarial decode, real journal IO."""
from pathlib import Path
from types import SimpleNamespace
import base64,hashlib,io,json,os,shutil,struct,sys,time,zlib
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.foundation.fdm09 import *
from aeris_runtime.foundation.frame_adapter import FrameAdapter,SERVO
from aeris_runtime.foundation.journal_base import verify_journal
from aeris_runtime.scene_channel import ScenePublisher,ScenePipeReader
from aeris_runtime.metadata_budget import encoded
from pilot.betaintegrated01.runtime.physics import Model,profile
LAB=R/'evidence/betasim-integrated01/runtime/.fdm09'
def deny(fn):
 try:fn()
 except(Exception):return
 raise AssertionError('expected rejection')
def body(kind,payload,n=1,frame=0):return{'v':2,'run':'fdm09','epoch':'e'*32,'segment':0,'seq':n,'previous':'a'*64,'kind':kind,'frame':frame,'payload':payload}
class Clock:
 def dispatch(self,bracket,fn):return fn(time.monotonic_ns())
def fresh():
 t=time.monotonic_ns();return{'id':1,'hostReceiveNs':t,'offsetLowNs':0,'offsetHighNs':0,'clockPublicationSequence':1,'publicationCompleteHostNs':t}
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);groups=[];adapter=None;publisher=reader=None;paths=[T/'source/aeris_runtime/foundation'/n for n in('fdm09.py','journal.py','frame_adapter.py','journal_base/receiver.py')]+[T/'source/aeris_runtime/scene_channel.py'];start_pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}
 try:
  rows=[body('RX',{'base64':base64.b64encode(SERVO.pack(18458,1200,0,*([1000]*16))).decode()}),body('INTENT',{'base64':base64.b64encode(bytes(range(256))*3).decode()}),body('SENT',{'expectedBytes':768,'returnedBytes':768,'scope':'LOCAL_CALLBACK_RETURN_NOT_AP_EXECUTION'}),body('EVENT',{'eventKind':'STAGE','data':{'frame':0,'fields':{k:1 for k in STAGE_KEYS[:32]}}},frame=None)]
  for row in rows:
   original=logical(row);stored=compact_line(row,original);assert decode_line(stored,'fdm09','e'*32,row['previous'])==original and len(stored)<=2048
  cap=frame_capacity();assert cap['physicalMaximumBytesPerAcceptedFrame']==1644;assert sum(len(compact_line(row,logical(row)))for row in rows)<=1644;groups.append('RX40-INTENT768-SENT-STAGE32-canonical-v2-all-byte-SHA-CRC-exact-roundtrip-max1644Bframe')
  for value in(True,None,1.5,float('inf'),float('nan'),-1,2**63):
   row=body('EVENT',{'eventKind':'STAGE','data':{'frame':0,'fields':{STAGE_KEYS[0]:value}}},frame=None);deny(lambda:compact_line(row,logical(row)))
  row=body('EVENT',{'eventKind':'STAGE','data':{'frame':0,'fields':{'unknown-field':1}}},frame=None);deny(lambda:compact_line(row,logical(row)));groups.append('unknown-bool-None-float-nonfinite-negative-overflow-not-coerced-or-omitted')
  for bad in({**rows[0],'unknownFutureField':1},{**rows[0],'v':True},{**rows[0],'v':3}):deny(lambda:compact_line(bad,logical(bad)))
  deny(lambda:compact_line(rows[0],logical(rows[0]).replace(b'"v":2',b'"v":1')));groups.append('unknown-body-key-wrong-v-bool-version-and-original-bytes-mismatch-refused-without-loss')
  stored=compact_line(rows[0],logical(rows[0]));wire=json.loads(stored);raw=bytearray(base64.b64decode(wire['fdm09']));raw[-1]^=1;deny(lambda:decode_line(canonical({'fdm09':base64.b64encode(raw).decode()})+b'\n','fdm09','e'*32,'a'*64));deny(lambda:decode_line(stored[:-1],'fdm09','e'*32,'a'*64));deny(lambda:decode_line(stored,'fdm09','e'*32,None));deny(lambda:list(original_lines(io.BytesIO(b'x'*10000000),'fdm09','e'*32)));groups.append('physicalCRC-partial-no-previoushead-and-oversized-streamfail-before-unbounded-restore')
  state={};decoded={};stages=[]
  for n in range(3):
   b=body('EVENT',{'eventKind':'STAGE','data':{'frame':n,'fields':{k:100000+n for k in STAGE_KEYS[:12]}}},n=n,frame=None);raw=logical(b);stored=compact_line(b,raw,stage_state=state);assert decode_line(stored,'fdm09','e'*32,b['previous'],stage_state=decoded)==raw;stages.append((stored,b))
  delta,b=stages[1];assert base64.b64decode(json.loads(delta)['fdm09'])[5]in(0x84,0x85);deny(lambda:decode_line(delta,'fdm09','e'*32,b['previous']));absolute=compact_line(b,logical(b),stage_state=state,force_absolute_stage=True);assert base64.b64decode(json.loads(absolute)['fdm09'])[5]==4;assert decode_line(absolute,'fdm09','e'*32,b['previous'])==logical(b)
  header=body('SEGMENT',{'ordinal':0,'startSequence':0,'previousSegmentSHA256':'0'*64},n=0,frame=None);compact_line(header,logical(header),stage_state=state);assert not state;reset=compact_line(b,logical(b),stage_state=state);assert base64.b64decode(json.loads(reset)['fdm09'])[5]==4;groups.append('changed-mask-signedvarint-delta-byteexact-firststage-resetABS-singleprefix-refusesdelta-privateABS-checkpoint')
  blob=bytearray(base64.b64decode(json.loads(delta)['fdm09']));struct.pack_into('>Q',blob,HEADER.size,1<<63);struct.pack_into('>I',blob,HEADER.size-4,zlib.crc32(blob[:HEADER.size-4]+blob[HEADER.size:])&0xffffffff);deny(lambda:decode_line(canonical({'fdm09':base64.b64encode(blob).decode()})+b'\n','fdm09','e'*32,b['previous'],stage_state=decoded));deny(lambda:read_varint(b'\x81\x00',0));deny(lambda:read_varint(b'\xff'*11,0));groups.append('unknown-delta-mask-overlong-overflow-varints-refused-no-implicit-state-or-cast')
  # Real existing disk prime, original journal state machine and original
  # write/fsync barriers, no fake 15-second priming claim or AP/Android actor.
  root=LAB/'source';root.mkdir();origin=time.monotonic_ns();adapter=FrameAdapter(root/'journal','fdm09','e'*32,Model(profile('empty','calm',32)),max_frames=12,maximum_seconds=180,clock_owner=Clock(),origin_ns=origin);sent=[]
  rd,wr=os.pipe();pins={k:'a'*64 for k in('backendSourceSHA256','modelSourceSHA256','profileSHA256','journalPolicySHA256')};context={'run':'fdm09','epoch':'e'*32,'boot':'b','profileId':'WORKBENCH_SIM_V1'};at=[time.monotonic_ns()];reader=ScenePipeReader(rd,context,root,pins);reader.start();publisher=ScenePublisher(wr,context,lambda:{'latest':{'HEARTBEAT':{'armed':False,'observedHostNs':at[0]}}},pins);publisher.start();adapter.scene=publisher
  for frame in range(12):
   if frame==6:time.sleep(.06)
   at[0]=time.monotonic_ns()
   receipt=time.monotonic_ns();adapter.receive(SERVO.pack(18458,1200,frame,*([1000]*16)),('127.0.0.1',9000),lambda b:sent.append(b)or len(b),clock_read=fresh,original_receive_ns=receipt,admission_deadline_ns=receipt+100_000_000)
  result=adapter.close();proof=verify_journal(root/'journal','fdm09','e'*32,expected_commit=result['commitAnchor'],expected_physical_codec=CODEC);assert proof['frames']==12 and proof['stageRows']==12 and len(sent)==12;manifest=json.loads((root/'journal/manifest.json').read_bytes());assert manifest['physicalCodec']==CODEC
  deny(lambda:verify_journal(root/'journal','fdm09','e'*32,expected_commit=result['commitAnchor']));groups.append('clock-transport-defaultplain-role-refuses-FDM09-manifest-no-auto-codec-from-input')
  physical=(root/'journal/segment-000000.jsonl').read_bytes();restored=list(original_lines(io.BytesIO(physical),'fdm09','e'*32));assert any('fdm09'in json.loads(x)for x in physical.splitlines());assert all('body'in json.loads(x)for x in restored);groups.append('real-original15s-diskprime-12frames-fsync-beforeSensor-original-seals-cold-chain-anchor-complete')
  publisher.close();end=time.monotonic()+1
  while reader.received<1 and time.monotonic()<end:time.sleep(.005)
  assert reader.received>=1 and reader.failure is None,(reader.received,reader.failure);stage_rows=[json.loads(x)for x in restored if json.loads(x)['body']['kind']=='EVENT'and json.loads(x)['body']['payload']['eventKind']=='STAGE'];assert len(stage_rows)==12;groups.append('source-reserves20Hz-ABS-before-stagefsync-real-pipe-SingleStage-prefix-and-logicalhead-proof')
  segment=root/'journal/segment-000000.jsonl';changed=bytearray(physical);where=physical.find(b'fdm09');changed[where]=ord('x');segment.write_bytes(changed);deny(lambda:verify_journal(root/'journal','fdm09','e'*32,expected_commit=result['commitAnchor'],expected_physical_codec=CODEC));segment.write_bytes(physical);groups.append('cold-receiver-refuses-tampered-physicalprefix-or-seal-no-converted-file-fallback')
  assert start_pins=={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths};report={'format':'aeris-fdm09-lossless-source-mock','status':'PASS_REAL_SOURCE_JOURNAL_DISK_PRIME_AND_IO_NO_SIMULATOR_ACTORS','groups':groups,'capacity':cap,'sourcePins':start_pins,'sourceChangedDuringMock':False,'logicalRowsExactNotSummaryOnly':True,'physicalQuotasUnchanged':True,'actorsStarted':False,'scratchRemoved':str(LAB.relative_to(R))}
 finally:
  if adapter is not None and not adapter.closed:adapter.journal.abort('MOCK_TERMINAL')
  if publisher is not None:publisher.close()
  if reader is not None:reader.close()
  shutil.rmtree(LAB)
 out=R/'evidence/betasim-integrated01/runtime/fdm09-causal-mock04.json';assert not out.exists();out.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
