"""Independent exact IEEE/scaffold inverse, no model or actors."""
from pathlib import Path
import base64,hashlib,json,math,os,struct,sys,zlib
R=Path(__file__).resolve().parents[3];T=R/'planning/betasim-integrated01/runtime';sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.foundation.fdm09 import compact_sensor,restore_sensor,compact_line,decode_line,original_lines,HEADER
from aeris_runtime.metadata_budget import encoded
import io
checks=[]
def deny(fn):
 try:fn()
 except Exception:return
 raise AssertionError('negative unexpectedly admitted')
def test(name,fn):fn();checks.append(name)
def sensors(v):return b'\n'+json.dumps({'timestamp':v[0],'imu':{'gyro':v[1:4],'accel_body':v[4:7]},'position':v[7:10],'velocity':v[10:13],'quaternion':v[13:17],'battery':{'voltage':v[17],'current':v[18]},'velocity_wind':v[19:22]},separators=(',',':'),allow_nan=False).encode()+b'\n'
def logical(raw,n=1,previous='0'*64):
 body={'v':2,'run':'qa-sensor09','epoch':'e'*32,'segment':0,'seq':n,'previous':previous,'kind':'INTENT','frame':n-1,'payload':{'base64':base64.b64encode(raw).decode()}};b=json.dumps(body,sort_keys=True,separators=(',',':')).encode();head=hashlib.sha256(bytes.fromhex(previous)+b).hexdigest();original=json.dumps({'body':body,'crc32':f'{zlib.crc32(b)&0xffffffff:08x}','sha256':head},sort_keys=True,separators=(',',':')).encode()+b'\n';return body,original,head
def token(stored):return base64.b64decode(json.loads(stored)['fdm09'])
def inverse():
 values=[0,0.0,-0.0,5e-324,-5e-324,sys.float_info.max,-sys.float_info.max,sys.float_info.min,-sys.float_info.min,1.0,-1.0,1e-100,1e100];head='0'*64;physical=[];originals=[]
 for i in range(66):
  v=[values[(j+i)%len(values)]for j in range(22)];source=sensors(v);data=compact_sensor(source);assert data is not None and len(data)<=180 and restore_sensor(data)==source
  expected_mask=sum(1<<j for j,x in enumerate(v)if type(x)is float);expected=struct.pack('>I',expected_mask)+b''.join(struct.pack('>d',x)for x in v if type(x)is float);assert data==expected
  b,raw,newhead=logical(source,i+1,head);stored=compact_line(b,raw);assert token(stored)[5]==5 and decode_line(stored,b['run'],b['epoch'],head)==raw;physical.append(stored);originals.append(raw);head=newhead
 assert list(original_lines(io.BytesIO(b''.join(physical)),'qa-sensor09','e'*32,previous='0'*64))==originals
def exact_zero_types():
 rows=[]
 for value in[0,0.0,-0.0]:
  raw=sensors([value]*22);stored=compact_sensor(raw);assert restore_sensor(stored)==raw;rows.append(stored)
 assert len(set(rows))==3 and rows[0]==bytes(4)and len(rows[1])==180 and rows[1]!=rows[2]
def opaque_fallback():
 raw=sensors([0.0]*22);base=json.loads(raw);q={**base,'unknown':5};reversed_top=dict(reversed(list(base.items())));nested={**base,'battery':dict(reversed(list(base['battery'].items())))}
 candidates=[raw.replace(b'"timestamp":0.0',b'"timestamp":1'),raw.replace(b'"timestamp":0.0',b'"timestamp":true'),raw.replace(b'"timestamp"',b'"unknownTimestamp"'),raw.replace(b',"imu"',b', "imu"'),raw[1:],json.dumps(q,separators=(',',':')).encode(),b'\n'+json.dumps(reversed_top,separators=(',',':')).encode()+b'\n',b'\n'+json.dumps(nested,separators=(',',':')).encode()+b'\n',raw.replace(b'"gyro":[0.0,0.0,0.0]',b'"gyro":[0.0]'),raw.replace(b'"timestamp":0.0',b'"timestamp":0e0')]
 for source in candidates:
  assert compact_sensor(source)is None;b,original,_=logical(source);stored=compact_line(b,original);assert token(stored)[5]==2 and decode_line(stored,b['run'],b['epoch'],b['previous'])==original
def semantic_bad_after_recrc():
 valid=compact_sensor(sensors([0.0]*22));b,original,_=logical(sensors([0.0]*22));old=token(compact_line(b,original));head=bytearray(old[:HEADER.size]);data=old[HEADER.size:]
 for bad in[struct.pack('>I',1<<31),struct.pack('>I',1),struct.pack('>I',0)+b'x',struct.pack('>I',1)+struct.pack('>d',float('nan')),struct.pack('>I',1)+struct.pack('>d',float('inf')),struct.pack('>I',1)+struct.pack('>d',-float('inf')),valid[:-1],valid+b'\x00']:
  deny(lambda:restore_sensor(bad));prefix=bytes(head[:-4]);blob=prefix+struct.pack('>I',zlib.crc32(prefix+bad)&0xffffffff)+bad;stored=encoded({'fdm09':base64.b64encode(blob).decode()});deny(lambda:decode_line(stored,b['run'],b['epoch'],b['previous']))
def original_mismatch():
 b,raw,_=logical(sensors([0.0]*22));deny(lambda:compact_line(b,raw.replace(b'"crc32":"',b'"crc32":"f')));changed={**b,'frame':10};deny(lambda:compact_line(changed,raw))
test('66_exact_scaffold_typed22_IEEE64_extreme_subnormal_full_logicalCRC_SHA_prefix_inverse',inverse)
test('literal_int0_float0_negativefloat0_distinct_mask_and_original_bytes',exact_zero_types)
test('unknown_scaffold_spacing_order_nonzeroInt_bool_listlength_keep_opaqueRAW_exact',opaque_fallback)
test('highmask_truncated_extra_NaN_Inf_rejected_even_with_recomputed_physicalCRC',semantic_bad_after_recrc)
test('original_logical_tamper_or_frame_mismatch_denied_before_optimization',original_mismatch)
p=T/'source/aeris_runtime/foundation/fdm09.py';out=R/(sys.argv[1]if len(sys.argv)>1 else'evidence/betasim-integrated01/qa/fdm09-sensor01.json');assert not out.exists();out.write_bytes(encoded({'format':'aeris-independent-fdm09-absolute-sensor-source-qa','status':'PASS_EXACT_BYTES_AND_TYPED_NEGATIVES_NOT_ACTUAL_FDM_OR_EXPORT','checks':checks,'sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'fixtureSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'actorsStarted':False,'modelNotRun':True,'maximumTypedPayloadBytes':180,'futureCompressionRatioAccepted':False}));print(json.dumps({'path':str(out.relative_to(R)),'checks':len(checks),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
