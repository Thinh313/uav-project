"""Independent private scene row verification and public hint removal fixtures."""
from pathlib import Path
from types import SimpleNamespace
from collections import deque
import hashlib,json,os,sys,threading,time
R=Path(__file__).resolve().parents[3];T=R/'planning/betasim-integrated01/runtime';sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.foundation.fdm09 import compact_line
from aeris_runtime.scene_channel import ScenePublisher,ScenePipeReader
from aeris_runtime.metadata_budget import encoded
CTX={'run':'qa-scene09','epoch':'e'*32,'boot':'b'*32,'profileId':'WORKBENCH_SIM_V1'};BIND={k:'1'*64 for k in('backendSourceSHA256','modelSourceSHA256','profileSHA256','journalPolicySHA256')};LAB=R/'planning/betasim-integrated01/qa/.scene-fdm09-fixture';checks=[]
def original(b):
 raw=json.dumps(b,sort_keys=True,separators=(',',':')).encode();h=hashlib.sha256(bytes.fromhex(b['previous'])+raw).hexdigest();return encoded({'body':b,'crc32':f'{__import__("zlib").crc32(raw)&0xffffffff:08x}','sha256':h})
def fixture(*,delta=False):
 fields={'computeEndSinceOriginNs':1000,'wireFrame':0,'rateHz':1200,'clockIDAtAdmission':1,'clockPublicationAtAdmission':3,'clockAgeAtAdmissionNs':100,'sensorBytes':247};b={'v':2,'run':CTX['run'],'epoch':CTX['epoch'],'segment':0,'seq':1,'previous':'a'*64,'kind':'EVENT','frame':None,'payload':{'eventKind':'STAGE','data':{'frame':0,'fields':fields}}};state={};plain=original(b);stored=compact_line(b,plain,stage_state=state);prefix=b''
 if delta:
  prefix=stored;b={**b,'seq':2,'previous':json.loads(plain)['sha256'],'payload':{'eventKind':'STAGE','data':{'frame':1,'fields':{**fields,'wireFrame':1}}}};plain=original(b);stored=compact_line(b,plain,stage_state=state)
 (LAB/'journal/segment-000000.jsonl').write_bytes(prefix+stored);now=time.monotonic_ns();v={'format':'aeris-sim-scene-frame','version':1,'mode':'LIVE','poseSource':'ROOT_DURABLE_FDM_STATE','sourceBinding':BIND,'context':CTX,'frame':1 if delta else 0,'simulationTimeS':0,'sampleHostNs':str(now-1000000),'committedHostNs':str(now-500000),'positionNedM':[0,0,0],'quaternionWxyz':[1,0,0,0],'rpmEstimated':[0,0,0,0],'ap':{'armed':False,'heartbeatHostNs':str(now-1000000)},'rawRef':{'relativePath':'journal/segment-000000.jsonl','throughSequence':b['seq'],'headSHA256':json.loads(plain)['sha256'],'prefixBytes':len(prefix+stored),'frame':1 if delta else 0,'previousLogicalHeadSHA256':b['previous'],'privatePhysicalStageSHA256':hashlib.sha256(stored).hexdigest(),'physicalStageBytes':len(stored)}}
 return v,stored,plain
def reader():
 x=ScenePipeReader.__new__(ScenePipeReader);x.source_binding=BIND;x.context=CTX;x.raw_root=LAB;x.latest=None;x.received=0;return x
def deny(v):
 x=reader()
 try:x._accept(encoded(v))
 except Exception:assert x.latest is None;return
 raise AssertionError('bad private proof published')
assert not LAB.exists();LAB.mkdir();(LAB/'journal').mkdir()
try:
 v,stored,plain=fixture();x=reader();x._accept(encoded(v));q=x.latest;assert q['proofStatus']=='LIVE_ROOT_VALIDATED_COLD_FULL_PREFIX_REQUIRED'and q['rawRef']['physicalByteStart']==0 and q['rawRef']['physicalStageBytes']==len(stored) and q['rawRef']['headSHA256']==json.loads(plain)['sha256'];assert 'previousLogicalHeadSHA256'not in q['rawRef']and'privatePhysicalStageSHA256'not in q['rawRef'];checks.append('actual_stored_line_SHA_then_logical_crc_head_verified_before_private_hints_removed')
 for key,val in[('previousLogicalHeadSHA256','b'*64),('privatePhysicalStageSHA256','c'*64),('physicalStageBytes',len(stored)-1),('headSHA256','d'*64)]:
  bad=json.loads(json.dumps(v));bad['rawRef'][key]=val;deny(bad)
 checks.append('wrong_previous_physical_hash_size_or_logicalhead_publishes_none')
 v,stored,plain=fixture(delta=True);deny(v);checks.append('single_row_scene_decoder_rejects_DELTA_without_full_state_even_with_valid_physical_SHA')
 p=ScenePublisher.__new__(ScenePublisher);p.failure=None;p.stop=threading.Event();p.reserved=None;p.next_due=200;p.pending=deque(maxlen=1);p.selected=0;p.no_fresh_AP=0
 row={'computeEndSinceOriginNs':100};assert p.reserve(0,row,0)is None;p.next_due=0;p.offer(SimpleNamespace(origin_ns=0),0,row,reservation=None);assert p.selected==0 and not p.pending and p.failure is None;checks.append('explicit_no_reservation_cannot_become_new_after_fsync_selection')
 p.reserved=None;p.next_due=0;r=p.reserve(0,row,0);assert r is not None;p.offer(SimpleNamespace(origin_ns=0,journal=SimpleNamespace(last_stage_encoding_absolute=False)),0,row,reservation=r);assert not p.pending and 'SELECTED_STAGE_MUST_BE_ABSOLUTE'in p.failure;checks.append('selected_non_ABS_stage_fails_closed_before_scene_enqueue')
finally:
 (LAB/'journal/segment-000000.jsonl').unlink();(LAB/'journal').rmdir();LAB.rmdir()
out=R/(sys.argv[1]if len(sys.argv)>1 else'evidence/betasim-integrated01/qa/scene-fdm09-01.json');assert not out.exists();out.write_bytes(encoded({'format':'aeris-independent-private-scene-fdm09-source-qa','status':'PASS_SCOPED_SOURCE_FIXTURES_NOT_LIVE_ROOT_PIPE_OR_FULL_CAPTURE','checks':checks,'sourceSHA256':hashlib.sha256((T/'source/aeris_runtime/scene_channel.py').read_bytes()).hexdigest(),'actualActors':False,'physicalPipeProvenanceInjected':True,'fullColdPrefixStillRequired':True,'noPublicPhysicalSHAClaim':True,'scratchRemoved':str(LAB.relative_to(R))}));print(json.dumps({'status':'PASS','checks':len(checks),'path':str(out.relative_to(R)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
