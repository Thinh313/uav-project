"""Source integer-basis bijection and malformed wire negatives, no actors."""
from pathlib import Path
import base64,hashlib,json,random,struct,sys,zlib
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.foundation.fdm09 import *
from aeris_runtime.metadata_budget import encoded

def deny(fn):
 try:fn()
 except ValueError:return
 raise AssertionError('expected invalid source wire')
def wire(data):
 prefix=HEADER.pack(MAGIC,1,0x85,0,2,1,0);raw=prefix[:-4]+struct.pack('>I',zlib.crc32(prefix[:-4]+data)&0xffffffff)+data;return canonical({'fdm09':base64.b64encode(raw).decode()})+b'\n'
def run():
 pin=hashlib.sha256((T/'source/aeris_runtime/foundation/fdm09.py').read_bytes()).hexdigest();rng=random.Random(938);state={};cold={};head='0'*64;codes=set()
 for n in range(2000):
  if n<1000:
   t=10_000_000_000+n*833333;fields={'receiveSinceOriginNs':t,'originalReceiveSinceOriginNs':t+(n%3),'clockAdmissionSinceOriginNs':t+17,'computeBeginSinceOriginNs':t+31,'computeEndSinceOriginNs':t+53,'clockCheckBeforeSendSinceOriginNs':t+61,'sendBeginSinceOriginNs':t+67,'sendEndSinceOriginNs':t+79,'frameGroupEndSinceOriginNs':t+83,'clockAtomicPermitSinceOriginNs':t+71,'clockCheckAtAdmissionSinceOriginNs':t+19,'clockAgeAtAdmissionNs':t-(n//120)*100_000_000,'clockAdmissionScopeVersion':9,'clockAtOriginalReceiptStatus':0,'clockIDAtAdmission':n//120,'originalReceiveKind':1}
  else:fields={k:rng.randrange(2**63)for k in rng.sample(list(STAGE_KEYS),rng.randrange(1,33))}
  assert stage_unbasis(stage_basis(fields))==fields
  b={'v':2,'run':'fdm-basis','epoch':'e'*32,'segment':0,'seq':n,'previous':head,'kind':'EVENT','frame':None,'payload':{'eventKind':'STAGE','data':{'frame':n,'fields':fields}}};original=logical(b);stored=compact_line(b,original,stage_state=state);codes.add(HEADER.unpack_from(base64.b64decode(load(stored)['fdm09']))[2]);assert decode_line(stored,'fdm-basis','e'*32,head,stage_state=cold)==original;head=load(original)['sha256'];assert len(stored)<=frame_capacity()['parts']['STAGE32']
 assert 0x85 in codes and 4 in codes
 k='computeBeginSinceOriginNs';mask=1<<STAGE_KEYS.index(k);prior={'fields':{k:0}}
 for payload in(struct.pack('>QQ',mask,mask)+varint(1),struct.pack('>QQ',mask,mask)+varint(2**64-1),struct.pack('>QQ',mask,1<<63)+varint(0),struct.pack('>QQ',mask,mask)+b'\x81\x00'):
  deny(lambda:decode_line(wire(payload),'fdm-basis','e'*32,'0'*64,stage_state=prior.copy()))
 assert pin==hashlib.sha256((T/'source/aeris_runtime/foundation/fdm09.py').read_bytes()).hexdigest();out=R/'evidence/betasim-integrated01/runtime/fdm09-basis-mock01.json';assert not out.exists();report={'format':'aeris-fdm09-integer-time-basis-causal-mock','status':'PASS_SOURCE_CODEC_NOT_ACTUAL_FLIGHT_OR_EXPORT','groups':['exact-bijection-current-scope9-nonzero-residuals-changed-clock-IDs-and1000-random-valid-subsets','actual-delta-wire-full-original-canonicalCRC-SHA-byte-roundtrip-both-basis-and-ABS-selected','malformed-basis-negative-overflow-mask-and-overlong-varint-rejected','source-pins-stable-and-ABS-hard1644B-frame-bound-unchanged'],'seed':938,'sourceSHA256':pin,'codesObserved':sorted(codes),'actorsStarted':False,'scratchCreated':False};out.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':run()
