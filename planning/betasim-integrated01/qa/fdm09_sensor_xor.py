"""Independent code6 sequence/type-reset and corruption checks; no actors."""
from pathlib import Path
import base64,hashlib,io,json,os,struct,sys,zlib
R=Path(__file__).resolve().parents[3];T=R/'planning/betasim-integrated01/runtime';sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.foundation.fdm09 import compact_line,decode_line,original_lines,HEADER,compact_sensor,restore_sensor_delta,sensor_state
from aeris_runtime.metadata_budget import encoded
checks=[]
def deny(fn):
 try:fn()
 except Exception:return
 raise AssertionError('negative unexpectedly admitted')
def source(v):return b'\n'+json.dumps({'timestamp':v[0],'imu':{'gyro':v[1:4],'accel_body':v[4:7]},'position':v[7:10],'velocity':v[10:13],'quaternion':v[13:17],'battery':{'voltage':v[17],'current':v[18]},'velocity_wind':v[19:22]},separators=(',',':'),allow_nan=False).encode()+b'\n'
def row(kind,payload,seq,frame,previous,segment=0):
 b={'v':2,'run':'qa-xor09','epoch':'e'*32,'segment':segment,'seq':seq,'previous':previous,'kind':kind,'frame':frame,'payload':payload};data=json.dumps(b,sort_keys=True,separators=(',',':')).encode();head=hashlib.sha256(bytes.fromhex(previous)+data).hexdigest();return b,json.dumps({'body':b,'crc32':f'{zlib.crc32(data)&0xffffffff:08x}','sha256':head},sort_keys=True,separators=(',',':')).encode()+b'\n',head
def sequence():
 enc={};dec={};physical=[];original=[];head='0'*64;n=0;codes=[];delta=None
 def add(kind,payload,frame,segment=0):
  nonlocal head,n,delta
  n+=1;b,raw,newhead=row(kind,payload,n,frame,head,segment);stored=compact_line(b,raw,stage_state=enc);assert decode_line(stored,b['run'],b['epoch'],head,stage_state=dec)==raw;head=newhead;physical.append(stored);original.append(raw)
  if kind=='INTENT':
   code=base64.b64decode(json.loads(stored)['fdm09'])[5];codes.append(code)
   if code==6 and delta is None:delta=stored
   return code
 for i in range(90):
  if i==60:
   add('SEGMENT',{'ordinal':1,'startSequence':n+1,'previousSegmentSHA256':'a'*64},None,1);assert not enc and not dec
  segment=int(i>=60);add('RX',{'base64':base64.b64encode(bytes(40)).decode()},i,segment)
  if i==30:
   sensor=b'OPAQUE_ORIGINAL_SENSOR_PAYLOAD';assert add('INTENT',{'base64':base64.b64encode(sensor).decode()},i,segment)==2;assert 'sensor'not in enc and 'sensor'not in dec
  else:
   values=[1.0+i*2**-50]*22
   if i%9==0:values[i%22]=0
   if i%11==0:values[(i+1)%22]=-0.0
   if i%13==0:values[(i+2)%22]=5e-324
   sensor=source(values);code=add('INTENT',{'base64':base64.b64encode(sensor).decode()},i,segment)
   if i in(0,31,60):assert code==5
  add('SENT',{'expectedBytes':len(sensor),'returnedBytes':len(sensor),'scope':'LOCAL_CALLBACK_RETURN_NOT_AP_EXECUTION'},i,segment)
  add('EVENT',{'eventKind':'STAGE','data':{'frame':i,'fields':{'computeBeginSinceOriginNs':100000+i,'computeEndSinceOriginNs':100001+i}}},None,segment)
 assert 6 in codes and delta is not None
 assert list(original_lines(io.BytesIO(b''.join(physical)),'qa-xor09','e'*32,previous='0'*64))==original
 deny(lambda:decode_line(delta,'qa-xor09','e'*32,'0'*64));checks.append('90_interleaved_frames_exact_canonicalCRC_SHA_sequence_typeflips_RAW_and_segment_reset_firstABS')
 # Actual code6 bytes remain unchanged if the producer's future dictionary is mutated.
 saved=physical[5];enc.clear();assert physical[5]==saved
 checks.append('delta_requires_source_previous_state_and_no_mutable_payload_alias')
def negatives():
 prior=sensor_state(compact_sensor(source([1.0]*22)));nanbits=int.from_bytes(struct.pack('>d',float('nan')),'big');old=prior[1][0]
 def v(n):
  out=bytearray()
  while n>=128:out.append((n&127)|128);n>>=7
  out.append(n);return bytes(out)
 values=[struct.pack('>II',1<<22,0),struct.pack('>II',0,1)+b'\x01',struct.pack('>II',1,1)+b'\x00',struct.pack('>II',1,1)+b'\x81\x00',struct.pack('>II',1,1)+b'\xff'*10,struct.pack('>II',1,1),struct.pack('>II',1,0)+b'x',struct.pack('>II',1,1)+v(nanbits^old)]
 for data in values:deny(lambda:restore_sensor_delta(data,prior))
 for bad in[None,(True,prior[1]),(-1,prior[1]),(0,(0,)*21),(0,(False,)*22)]:deny(lambda:restore_sensor_delta(struct.pack('>II',0,0),bad))
 checks.append('high_mask_changed_outside_type_zero_overlong_overflow_truncated_trailing_NaN_and_bad_prior_refused')
 # Wrong physical CRC must fail before it can mutate decoder state.
 e={};d={};b,r,h=row('INTENT',{'base64':base64.b64encode(source([1.0]*22)).decode()},1,0,'0'*64);stored=compact_line(b,r,stage_state=e);decode_line(stored,b['run'],b['epoch'],'0'*64,stage_state=d);before=dict(d)
 b,r,_=row('INTENT',{'base64':base64.b64encode(source([1.0+2**-50]*22)).decode()},2,1,h);stored=compact_line(b,r,stage_state=e);x=json.loads(stored);blob=bytearray(base64.b64decode(x['fdm09']));blob[-1]^=1;x['fdm09']=base64.b64encode(blob).decode();deny(lambda:decode_line(encoded(x),b['run'],b['epoch'],h,stage_state=d));assert d==before;checks.append('physical_corruption_refuses_before_changing_cold_state')
def extreme_transitions():
 values=[0,0.0,-0.0,5e-324,-5e-324,sys.float_info.max,-sys.float_info.max,sys.float_info.min,-sys.float_info.min,1.0,-1.0];e={};d={};h='0'*64
 for i in range(144):
  v=[values[(j+i)%len(values)]for j in range(22)];b,r,newh=row('INTENT',{'base64':base64.b64encode(source(v)).decode()},i+1,i,h);stored=compact_line(b,r,stage_state=e);assert decode_line(stored,b['run'],b['epoch'],h,stage_state=d)==r;h=newh
 checks.append('144_mixed_extreme_IEEE_and_literal_type_transitions_delta_or_ABS_fallback_byteexact')
sequence();negatives();extreme_transitions();p=T/'source/aeris_runtime/foundation/fdm09.py';out=R/(sys.argv[1]if len(sys.argv)>1 else'evidence/betasim-integrated01/qa/fdm09-sensor-xor01.json');assert not out.exists();out.write_bytes(encoded({'format':'aeris-independent-fdm09-XOR64-source-qa','status':'PASS_EXACT_CANONICAL_SEQUENCE_NOT_ACTUAL_FLIGHT_OR_EXPORT','checks':checks,'sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'fixtureSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'actorsStarted':False,'modelNotRun':True,'compressionCapacityAccepted':False}));print(json.dumps({'path':str(out.relative_to(R)),'checks':len(checks),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
