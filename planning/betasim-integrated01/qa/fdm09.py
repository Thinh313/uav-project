"""Independent FDM09 byte/state/capacity checks. No AP, SDK or large copy."""
from pathlib import Path
import base64,hashlib,io,json,os,random,struct,sys,zlib
R=Path(__file__).resolve().parents[3];T=R/'planning/betasim-integrated01/runtime';sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.foundation.fdm09 import compact_line,decode_line,original_lines,STAGE_KEYS,HEADER,CODEC,frame_capacity,read_varint
from aeris_runtime.foundation.journal_base.receiver import verify_journal
from aeris_runtime.metadata_budget import encoded
checks=[];run='qa-fdm09';epoch='e'*32
def raw(body):
 b=json.dumps(body,sort_keys=True,separators=(',',':'),allow_nan=False).encode();h=hashlib.sha256(bytes.fromhex(body['previous'])+b).hexdigest();return json.dumps({'body':body,'crc32':f'{zlib.crc32(b)&0xffffffff:08x}','sha256':h},sort_keys=True,separators=(',',':')).encode()+b'\n'
def body(kind,payload,seq=1,frame=0,segment=0,previous='0'*64):return{'v':2,'run':run,'epoch':epoch,'segment':segment,'seq':seq,'previous':previous,'kind':kind,'frame':frame,'payload':payload}
def stage(fields,seq=1,frame=0,**kw):return body('EVENT',{'eventKind':'STAGE','data':{'frame':frame,'fields':fields}},seq,frame=None,**kw)
def deny(fn):
 try:fn()
 except Exception:return
 raise AssertionError('negative unexpectedly admitted')
def test(name,fn):fn();checks.append(name)
def basic():
 rows=[body('RX',{'base64':base64.b64encode(bytes(range(40))).decode()}),body('INTENT',{'base64':base64.b64encode(bytes(range(256))*3).decode()}),body('SENT',{'expectedBytes':768,'returnedBytes':768,'scope':'LOCAL_CALLBACK_RETURN_NOT_AP_EXECUTION'}),stage({k:1 for k in STAGE_KEYS[:32]})]
 sizes=[]
 for row in rows:
  original=raw(row);stored=compact_line(row,original);assert decode_line(stored,run,epoch,row['previous'])==original;sizes.append(len(stored));assert hashlib.sha256(stored).hexdigest()!=json.loads(original)['sha256']
 assert sum(sizes)==1644 and frame_capacity()['physicalMaximumBytesPerAcceptedFrame']==1644
def body_unknown():
 base=body('RX',{'base64':base64.b64encode(bytes(40)).decode()})
 for key,value in[('unknown',1),('v',True),('v',3),('seq',True),('segment',False),('frame',None)]:
  q={**base,key:value};deny(lambda:compact_line(q,raw(q)))
 deny(lambda:compact_line(base,raw(base)+b' '))
def typed_stage():
 for v in[None,True,False,1.0,float('inf'),float('nan'),-1,2**63]:
  q=stage({STAGE_KEYS[0]:v});deny(lambda:compact_line(q,raw(q)))
 q=stage({'not-a-supported-field':1});deny(lambda:compact_line(q,raw(q)))
 q=stage({STAGE_KEYS[0]:2**63-1});assert decode_line(compact_line(q,raw(q)),run,epoch,q['previous'])==raw(q)
def delta_series():
 enc={};dec={};head='0'*64;rng=random.Random(9052);physical=[];original=[];codes=[]
 for i in range(150):
  fields={k:10000000+i*100+j for j,k in enumerate(STAGE_KEYS[:12])if not(i%9==0 and j==3)}
  if i%11==0:fields[STAGE_KEYS[1]]=max(0,10000000-i*100)
  q=stage(fields,i+1,i,previous=head);expected=raw(q);stored=compact_line(q,expected,stage_state=enc,force_absolute_stage=i%5==0);code=base64.b64decode(json.loads(stored)['fdm09'])[5];codes.append(code)
  if i%5==0:assert code==4
  assert decode_line(stored,run,epoch,head,stage_state=dec)==expected
  physical.append(stored);original.append(expected);head=json.loads(expected)['sha256']
 assert any(c in(0x84,0x85)for c in codes)and list(original_lines(io.BytesIO(b''.join(physical)),run,epoch,previous='0'*64))==original
 delta=physical[next(i for i,c in enumerate(codes)if c in(0x84,0x85))];deny(lambda:decode_line(delta,run,epoch,'0'*64))
def reset_segment():
 enc={};dec={};q=stage({STAGE_KEYS[0]:100,STAGE_KEYS[1]:100});one=compact_line(q,raw(q),stage_state=enc);decode_line(one,run,epoch,q['previous'],stage_state=dec)
 header=body('SEGMENT',{'ordinal':1,'startSequence':2,'previousSegmentSHA256':'a'*64},seq=2,frame=None,segment=1);compact_line(header,raw(header),stage_state=enc);decode_line(raw(header),run,epoch,'0'*64,stage_state=dec);assert not enc and not dec
 q=stage({STAGE_KEYS[0]:101,STAGE_KEYS[1]:101},seq=3,segment=1);two=compact_line(q,raw(q),stage_state=enc);assert base64.b64decode(json.loads(two)['fdm09'])[5]==4
def physical_negative():
 q=stage({k:1234 for k in STAGE_KEYS[:12]});b=compact_line(q,raw(q));v=json.loads(b);blob=bytearray(base64.b64decode(v['fdm09']));blob[-1]^=1;bad=encoded({'fdm09':base64.b64encode(blob).decode()});deny(lambda:decode_line(bad,run,epoch,'0'*64));deny(lambda:decode_line(b[:-1],run,epoch,'0'*64));deny(lambda:decode_line(b,run,epoch,None));deny(lambda:read_varint(b'\x80\x00',0));deny(lambda:read_varint(b'\xff'*11,0));deny(lambda:list(original_lines(io.BytesIO(b'x'*4096),run,epoch)))
def main_only():
 lab=R/'planning/betasim-integrated01/qa/.fdm09-role-fixture';assert not lab.exists();lab.mkdir()
 try:
  m=json.loads((R/'evidence/betasim-integrated01/r06/sessions/betasim-short06/raw/clock-journal/manifest.json').read_bytes());m['physicalCodec']=CODEC;(lab/'manifest.json').write_bytes(encoded(m))
  try:verify_journal(lab,m['run'],m['epoch'])
  except Exception as e:assert str(e)=='MANIFEST_FORMAT',str(e)
  else:raise AssertionError('default clock/plain role accepted codec')
 finally:(lab/'manifest.json').unlink();lab.rmdir()
def hard_capacity():
 d=json.loads((T/'source/aeris_runtime/assets/resource-policy.json').read_bytes());bound=frame_capacity()['physicalMaximumBytesPerAcceptedFrame'];global margins
 margins={}
 for seconds in[180,760]:
  p=d['cases'][str(seconds)]['mainJournal'];s=p['max_segments'];overhead=(s+1)*p['max_record_bytes']+(s+3)*4096+(2*s+3)*4096+p['termination_reserve_bytes'];needed=seconds*1200*bound+overhead;assert needed<p['quota_bytes'];margins[str(seconds)]={'frames':seconds*1200,'frameBytesUpper':bound,'withHeadersCloseMetadata4KiBAndAllocationRounding':needed,'conservativeOverheadBytes':overhead,'unchangedQuota':p['quota_bytes'],'headroom':p['quota_bytes']-needed}
test('independent_canonical_byte_hash_CRC_roundtrip_40_768_SENT_STAGE32_bound1644',basic)
test('unknown_body_version_type_or_noncanonical_original_refused',body_unknown)
test('None_bool_float_negative_overflow_unknown_stage_refused_uint63_exact',typed_stage)
test('150_varying_missing_signed_delta_rows_exact_forceABS_and_no_state_refusal',delta_series)
test('segment_header_resets_presence_delta_state_and_first_stage_ABS',reset_segment)
test('CRC_partial_missinghead_overlong_varint_and_stream_bounds',physical_negative)
test('default_plain_clock_role_rejects_input_declared_FDM09',main_only)
test('all_frames_fit_original180_760_main_capture_caps_without_RTF_assumption',hard_capacity)
pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[T/'source/aeris_runtime/foundation/fdm09.py',T/'source/aeris_runtime/foundation/journal.py',T/'source/aeris_runtime/foundation/journal_base/receiver.py',T/'source/aeris_runtime/scene_channel.py']};out=R/(sys.argv[1]if len(sys.argv)>1 else'evidence/betasim-integrated01/qa/fdm09-01.json');assert not out.exists();out.write_bytes(encoded({'format':'aeris-independent-fdm09-byte-capacity-source-qa','status':'PASS_SCOPED_CODEC_NOT_ACTUAL_CAPTURE_OR_EXPORT','checks':checks,'sourcePins':pins,'captureBounds':margins,'exactOriginalBytesNotSensorRegeneration':True,'actualActors':False,'actualExport':False,'universal192MiBEntropyGuarantee':False,'scratchRemoved':'planning/betasim-integrated01/qa/.fdm09-role-fixture'}));print(json.dumps({'status':'PASS','checks':len(checks),'path':str(out.relative_to(R)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
