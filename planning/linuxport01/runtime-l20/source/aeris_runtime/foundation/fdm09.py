"""Lossless physical tokens for EXACT canonical logical journal-v2 rows.

FDM09 reuses Compact10's bounded typed-frame/CRC/stream-chain pattern. Context
and previous logical head are already committed by the segment/chain; they are
reconstructed, never guessed. Physical segment SHA/seals cover stored bytes.
No float parsing, sensor regeneration, rounding or arbitrary field omission.
"""
import base64,hashlib,json,re,struct,zlib,math
HEADER=struct.Struct('>4sBBHQqI');MAGIC=b'FDM9';CODEC='FDM09_CANONICAL_V2_LOSSLESS';MAX_LOGICAL=2048
STAGE_KEYS=tuple(sorted(('clockPublicationAtReceive','clockPublicationCompleteAtReceiveSinceOriginNs','receiveSinceOriginNs','wireFrame','rateHz','clockCheckAtReceiveSinceOriginNs','clockIDAtReceive','clockAgeAtReceiveNs','computeBeginSinceOriginNs','computeEndSinceOriginNs','sensorBytes','clockPublicationAtSend','clockPublicationCompleteAtSendSinceOriginNs','clockIDBeforeSend','clockCheckBeforeSendSinceOriginNs','clockAgeBeforeSendNs','sendBeginSinceOriginNs','clockAtomicPermitSinceOriginNs','clockAtomicPermitAgeNs','sendEndSinceOriginNs','frameGroupEndSinceOriginNs','clockPublicationAtAdmission','clockPublicationCompleteAtAdmissionSinceOriginNs','clockCheckAtAdmissionSinceOriginNs','clockIDAtAdmission','clockAgeAtAdmissionNs','clockAdmissionScopeVersion','originalReceiveSinceOriginNs','originalReceiveKind','clockAtOriginalReceiptStatus','clockAdmissionSinceOriginNs','unadmittedClockWaitNs','clockWaitPriorID')))
def need(ok,why):
 if not ok:raise ValueError('FDM09_'+why)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def uint(v,maximum=2**63-1):return type(v)is int and 0<=v<=maximum
def unique(pairs):
 result={}
 for k,v in pairs:need(k not in result,'DUPLICATE_FIELD');result[k]=v
 return result
def load(raw):return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in()).throw(ValueError('FDM09_NONFINITE')))
def logical(body):
 raw=canonical(body);head=hashlib.sha256(bytes.fromhex(body['previous'])+raw).hexdigest();return canonical({'body':body,'crc32':format(zlib.crc32(raw),'08x'),'sha256':head})+b'\n'
def varint(value):
 need(type(value)is int and 0<=value<2**64,'VARINT_UINT64');out=bytearray()
 while value>=128:out.append((value&127)|128);value>>=7
 out.append(value);return bytes(out)
def read_varint(data,at):
 value=0;start=at
 for i in range(10):
  need(at<len(data),'PARTIAL_VARINT');b=data[at];at+=1;value|=(b&127)<<(7*i)
  if not b&128:
   need(value<2**64 and data[start:at]==varint(value),'OVERLONG_OR_OVERFLOW_VARINT');return value,at
 need(False,'VARINT10_BOUND')
# Integer-only bijection. Missing bases mean literal zero, never an equality
# assumption: a nonzero residual is encoded just as exactly as zero. Dependency
# graph is acyclic; bounded to the original <=32 actually present fields.
STAGE_BASES={
 'originalReceiveSinceOriginNs':'receiveSinceOriginNs',
 'clockAdmissionSinceOriginNs':'receiveSinceOriginNs',
 'clockCheckAtAdmissionSinceOriginNs':'clockAdmissionSinceOriginNs',
 'clockCheckAtReceiveSinceOriginNs':'receiveSinceOriginNs',
 'computeBeginSinceOriginNs':'receiveSinceOriginNs',
 'computeEndSinceOriginNs':'computeBeginSinceOriginNs',
 'clockCheckBeforeSendSinceOriginNs':'computeEndSinceOriginNs',
 'sendBeginSinceOriginNs':'clockCheckBeforeSendSinceOriginNs',
 'clockAtomicPermitSinceOriginNs':'sendBeginSinceOriginNs',
 'sendEndSinceOriginNs':'sendBeginSinceOriginNs',
 'frameGroupEndSinceOriginNs':'sendEndSinceOriginNs',
 'clockPublicationCompleteAtReceiveSinceOriginNs':'receiveSinceOriginNs',
 'clockPublicationCompleteAtAdmissionSinceOriginNs':'receiveSinceOriginNs',
 'clockPublicationCompleteAtSendSinceOriginNs':'receiveSinceOriginNs',
 'clockAgeAtReceiveNs':'clockCheckAtReceiveSinceOriginNs',
 'clockAgeAtAdmissionNs':'clockCheckAtAdmissionSinceOriginNs',
 'clockAgeBeforeSendNs':'clockCheckBeforeSendSinceOriginNs',
 'clockAtomicPermitAgeNs':'clockAtomicPermitSinceOriginNs',
}
def stage_basis(fields):
 result={}
 for k,v in fields.items():
  n=v-fields.get(STAGE_BASES.get(k),0);result[k]=(n<<1)if n>=0 else((-n<<1)-1)
  need(0<=result[k]<2**64,'BASIS_UINT64')
 return result
def stage_unbasis(values):
 result={};visiting=set()
 def restore(k):
  if k in result:return result[k]
  need(k not in visiting,'BASIS_DEPENDENCY');visiting.add(k);zz=values[k];n=(zz>>1)^-(zz&1);base=STAGE_BASES.get(k);value=n+(restore(base)if base in values else 0);need(uint(value),'BASIS_RESTORED_UINT63');result[k]=value;visiting.remove(k);return value
 for k in values:restore(k)
 return result
def sensor_object(v):
 need(type(v)is list and len(v)==22,'SENSOR22')
 return {'timestamp':v[0],'imu':{'gyro':v[1:4],'accel_body':v[4:7]},'position':v[7:10],'velocity':v[10:13],'quaternion':v[13:17],'battery':{'voltage':v[17],'current':v[18]},'velocity_wind':v[19:22]}
def sensor_bytes(v):return b'\n'+json.dumps(sensor_object(v),separators=(',',':'),allow_nan=False).encode()+b'\n'
def compact_sensor(raw):
 # Unknown valid opaque INTENTs retain the existing RAW mode. This optimizer
 # has no authority to normalize keys/order/number types or JSON spelling.
 try:
  q=load(raw);need(type(q)is dict and list(q)==['timestamp','imu','position','velocity','quaternion','battery','velocity_wind'],'SENSOR_KEYS_ORDER')
  need(type(q['imu'])is dict and list(q['imu'])==['gyro','accel_body']and type(q['battery'])is dict and list(q['battery'])==['voltage','current'],'SENSOR_NESTED_KEYS_ORDER')
  arrays=[q['imu']['gyro'],q['imu']['accel_body'],q['position'],q['velocity'],q['quaternion'],q['velocity_wind']]
  need(all(type(a)is list and len(a)==n for a,n in zip(arrays,(3,3,3,3,4,3))),'SENSOR_LIST_LENGTHS')
  v=[q['timestamp'],*arrays[0],*arrays[1],*arrays[2],*arrays[3],*arrays[4],q['battery']['voltage'],q['battery']['current'],*arrays[5]];mask=0;parts=[]
  for i,value in enumerate(v):
   if type(value)is float and math.isfinite(value):mask|=1<<i;parts.append(struct.pack('>d',value))
   else:need(type(value)is int and value==0,'SENSOR_LITERAL_ZERO_OR_FINITE_FLOAT')
  need(sensor_bytes(v)==raw,'SENSOR_FULL_ORIGINAL_BYTE_EQUALITY');return struct.pack('>I',mask)+b''.join(parts)
 except (ValueError,TypeError,KeyError,OverflowError,struct.error):return None
def restore_sensor(data):
 need(type(data)is bytes and len(data)>=4,'SENSOR_MASK');mask=struct.unpack_from('>I',data)[0];need(mask>>22==0 and len(data)==4+8*mask.bit_count(),'SENSOR_MASK_LENGTH');v=[];at=4
 for i in range(22):
  if mask&(1<<i):value=struct.unpack_from('>d',data,at)[0];at+=8;need(math.isfinite(value),'SENSOR_NONFINITE_IEEE');v.append(value)
  else:v.append(0)
 raw=sensor_bytes(v);need(0<len(raw)<=768 and compact_sensor(raw)==data,'SENSOR_CANONICAL_INVERSE');return raw
def sensor_state(data):
 mask=struct.unpack_from('>I',data)[0];at=4;bits=[]
 for i in range(22):
  if mask&(1<<i):bits.append(struct.unpack_from('>Q',data,at)[0]);at+=8
  else:bits.append(0)
 return mask,tuple(bits)
def compact_sensor_delta(absolute,prior):
 current=sensor_state(absolute);mask,bits=current;changed=sum(1<<i for i in range(22)if mask&(1<<i)and bits[i]!=(prior[1][i]if prior[0]&(1<<i)else 0));return struct.pack('>II',mask,changed)+b''.join(varint(bits[i]^(prior[1][i]if prior[0]&(1<<i)else 0))for i in range(22)if changed&(1<<i))
def restore_sensor_delta(data,prior):
 need(type(prior)is tuple and len(prior)==2 and type(prior[0])is int and prior[0]>>22==0 and type(prior[1])is tuple and len(prior[1])==22 and all(type(n)is int and 0<=n<2**64 for n in prior[1]),'SENSOR_DELTA_PREVIOUS_STATE')
 need(type(data)is bytes and len(data)>=8,'SENSOR_DELTA_HEADER');mask,changed=struct.unpack_from('>II',data);need(mask>>22==0 and changed&~mask==0,'SENSOR_DELTA_MASK');at=8;values=[]
 for i in range(22):
  if mask&(1<<i):
   old=prior[1][i]if prior[0]&(1<<i)else 0
   if changed&(1<<i):xor,at=read_varint(data,at);need(xor!=0,'SENSOR_DELTA_NONZERO_CANONICAL');old^=xor
   values.append(struct.pack('>Q',old))
 need(at==len(data),'SENSOR_DELTA_TRAILING');absolute=struct.pack('>I',mask)+b''.join(values);raw=restore_sensor(absolute);need(compact_sensor_delta(absolute,prior)==data,'SENSOR_DELTA_CANONICAL');return raw,sensor_state(absolute)
def compact_line(body,original,*,stage_state=None,force_absolute_stage=False):
 need(type(body)is dict and set(body)=={'v','run','epoch','segment','seq','previous','kind','frame','payload'}and type(body['v'])is int and body['v']==2,'EXACT_V2_BODY_SCHEMA')
 need(all(type(body[k])is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',body[k])for k in('run','epoch'))and type(body['previous'])is str and re.fullmatch('[a-f0-9]{64}',body['previous'])is not None,'BODY_CONTEXT_HEAD')
 need(type(original)is bytes and 0<len(original)<=MAX_LOGICAL and original==logical(body),'ORIGINAL_CANONICAL_BYTES')
 kind=body['kind'];payload=body['payload'];frame=body['frame'];code=0;data=None
 if kind=='SEGMENT'and stage_state is not None:stage_state.clear()
 if kind in('RX','INTENT'):
  need(type(payload)is dict and set(payload)=={'base64'}and type(payload['base64'])is str,'RAW_PAYLOAD_SCHEMA');data=base64.b64decode(payload['base64'],validate=True);need(base64.b64encode(data).decode()==payload['base64'],'CANONICAL_BASE64');need(len(data)==40 if kind=='RX'else 0<len(data)<=768,'RAW_PAYLOAD_BOUND');code=1 if kind=='RX'else 2
  if kind=='INTENT':
   sensor=compact_sensor(data)
   if sensor is not None and len(sensor)<len(data):
    original_sensor=data;data=sensor;code=5;prior=None if stage_state is None else stage_state.get('sensor')
    if prior is not None:
     delta=compact_sensor_delta(sensor,prior)
     if len(delta)<len(data):
      restored,_=restore_sensor_delta(delta,prior);need(restored==original_sensor,'SENSOR_DELTA_ORIGINAL_BYTES');data=delta;code=6
    if stage_state is not None:stage_state['sensor']=sensor_state(sensor)
   elif stage_state is not None:stage_state.pop('sensor',None)
 elif kind=='SENT':
  need(type(payload)is dict and set(payload)=={'expectedBytes','returnedBytes','scope'}and payload['scope']=='LOCAL_CALLBACK_RETURN_NOT_AP_EXECUTION','SENT_SCHEMA');need(uint(payload['expectedBytes'],768)and payload['expectedBytes']>0 and type(payload['returnedBytes'])is int and payload['returnedBytes']==payload['expectedBytes'],'SENT_LENGTH');data=struct.pack('>HH',payload['expectedBytes'],payload['returnedBytes']);code=3
 elif kind=='EVENT'and payload.get('eventKind')=='STAGE':
  need(set(payload)=={'eventKind','data'}and type(payload['data'])is dict and set(payload['data'])=={'frame','fields'}and frame is None,'STAGE_SCHEMA');frame=payload['data']['frame'];fields=payload['data']['fields'];need(type(fields)is dict and len(fields)<=32 and all(k in STAGE_KEYS and uint(v)for k,v in fields.items()),'STAGE_TYPED_FIELDS');mask=sum(1<<i for i,k in enumerate(STAGE_KEYS)if k in fields);data=struct.pack('>Q',mask)+b''.join(struct.pack('>Q',fields[k])for k in STAGE_KEYS if k in fields);code=4
  prior=None if stage_state is None else stage_state.get('fields')
  if prior is not None and not force_absolute_stage:
   changed=[(i,k)for i,k in enumerate(STAGE_KEYS)if k in fields and(k not in prior or fields[k]!=prior[k])];change_mask=sum(1<<i for i,k in changed);deltas=[]
   for _,k in changed:
    n=fields[k]-prior.get(k,0);deltas.append(varint((n<<1)if n>=0 else((-n<<1)-1)))
   candidate=struct.pack('>QQ',mask,change_mask)+b''.join(deltas)
   if len(candidate)<len(data):data=candidate;code=0x84
   # Alternative time-basis delta is chosen only if strictly smaller. ABS
   # remains the hard maximum; extreme valid residual jumps simply use ABS.
   basis=stage_basis(fields);old_basis=stage_basis(prior);changed_basis=[(i,k)for i,k in enumerate(STAGE_KEYS)if k in basis and(k not in old_basis or basis[k]!=old_basis[k])];basis_mask=sum(1<<i for i,k in changed_basis);values=[];fits=True
   for _,k in changed_basis:
    n=basis[k]-old_basis.get(k,0);zz=(n<<1)if n>=0 else((-n<<1)-1)
    if zz>=2**64:fits=False;break
    values.append(varint(zz))
   if fits:
    candidate=struct.pack('>QQ',mask,basis_mask)+b''.join(values)
    if len(candidate)<len(data):data=candidate;code=0x85
  if stage_state is not None:stage_state['fields']=dict(fields);stage_state['lastStageAbsolute']=code==4
 else:return original
 need(uint(frame)and uint(body['seq'])and uint(body['segment'],4095),'HEADER_NUMERIC');prefix=HEADER.pack(MAGIC,1,code,body['segment'],body['seq'],frame,0);blob=prefix[:-4]+struct.pack('>I',zlib.crc32(prefix[:-4]+data)&0xffffffff)+data;stored=canonical({'fdm09':base64.b64encode(blob).decode()})+b'\n';need(len(original)<=MAX_LOGICAL and len(stored)<=MAX_LOGICAL,'RECORD2048');return stored
def decode_line(stored,run,epoch,previous,*,stage_state=None):
 need(type(stored)is bytes and 0<len(stored)<=MAX_LOGICAL and stored.endswith(b'\n'),'PHYSICAL_BOUND_OR_PARTIAL');row=load(stored)
 if type(row)is not dict or 'fdm09'not in row:
  if stage_state is not None and type(row)is dict and type(row.get('body'))is dict and row['body'].get('kind')=='SEGMENT':stage_state.clear()
  return stored
 need(set(row)=={'fdm09'}and type(row['fdm09'])is str,'WRAPPER_SCHEMA');raw=base64.b64decode(row['fdm09'],validate=True);need(len(raw)>=HEADER.size and base64.b64encode(raw).decode()==row['fdm09'],'BINARY_BOUND');magic,version,code,segment,seq,frame,crc=HEADER.unpack_from(raw);data=raw[HEADER.size:];need(magic==MAGIC and version==1 and code in(1,2,3,4,5,6,0x84,0x85)and uint(segment,4095)and uint(seq)and uint(frame),'HEADER_SCHEMA');need(crc==(zlib.crc32(raw[:HEADER.size-4]+data)&0xffffffff),'PHYSICAL_CRC');need(type(previous)is str and re.fullmatch('[a-f0-9]{64}',previous)is not None,'PREVIOUS_HEAD_REQUIRED')
 if code in(1,2,5,6):
  if code==6:
   need(stage_state is not None,'SENSOR_DELTA_PREVIOUS_STATE');data,current=restore_sensor_delta(data,stage_state.get('sensor'));stage_state['sensor']=current
  elif code==5:
   absolute=data;data=restore_sensor(data)
   if stage_state is not None:stage_state['sensor']=sensor_state(absolute)
  elif code==2 and stage_state is not None:stage_state.pop('sensor',None)
  need(len(data)==40 if code==1 else 0<len(data)<=768,'RAW_PAYLOAD_BOUND');kind='RX'if code==1 else'INTENT';payload={'base64':base64.b64encode(data).decode()};body_frame=frame
 elif code==3:
  need(len(data)==4,'SENT_LENGTH');expected,returned=struct.unpack('>HH',data);need(0<expected<=768 and returned==expected,'SENT_LENGTH');kind='SENT';payload={'expectedBytes':expected,'returnedBytes':returned,'scope':'LOCAL_CALLBACK_RETURN_NOT_AP_EXECUTION'};body_frame=frame
 else:
  need(len(data)>=8,'STAGE_MASK');mask=struct.unpack_from('>Q',data)[0];need(mask>>len(STAGE_KEYS)==0 and mask.bit_count()<=32,'STAGE_MASK_LENGTH');fields={};at=8
  if code==4:
   need(len(data)==8+8*mask.bit_count(),'STAGE_MASK_LENGTH')
   for i,k in enumerate(STAGE_KEYS):
    if mask&(1<<i):value=struct.unpack_from('>Q',data,at)[0];need(uint(value),'STAGE_UINT63');fields[k]=value;at+=8
  else:
   prior=None if stage_state is None else stage_state.get('fields');need(type(prior)is dict and len(prior)<=32 and all(k in STAGE_KEYS and uint(v)for k,v in prior.items()),'DELTA_PREVIOUS_STATE_REQUIRED');need(len(data)>=16,'DELTA_MASK');changed=struct.unpack_from('>Q',data,8)[0];need(changed&~mask==0,'DELTA_CHANGED_NOT_PRESENT');at=16
   previous_values=stage_basis(prior)if code==0x85 else prior
   for i,k in enumerate(STAGE_KEYS):
    if mask&(1<<i):
     if changed&(1<<i):zz,at=read_varint(data,at);n=(zz>>1)^-(zz&1);value=previous_values.get(k,0)+n
     else:need(k in previous_values,'DELTA_NEW_FIELD_UNCHANGED');value=previous_values[k]
     need(0<=value<2**64 if code==0x85 else uint(value),'DELTA_UINT63');fields[k]=value
   need(at==len(data),'DELTA_TRAILING_BYTES')
   if code==0x85:fields=stage_unbasis(fields)
  if stage_state is not None:stage_state['fields']=dict(fields);stage_state['lastStageAbsolute']=code==4
  kind='EVENT';payload={'eventKind':'STAGE','data':{'frame':frame,'fields':fields}};body_frame=None
 body={'v':2,'run':run,'epoch':epoch,'segment':segment,'seq':seq,'previous':previous,'kind':kind,'frame':body_frame,'payload':payload};expanded=logical(body);need(len(expanded)<=MAX_LOGICAL,'LOGICAL2048');return expanded
def original_lines(file,run,epoch,*,previous=None):
 """One bounded row restored at a time, no converted file or whole-stream RAM."""
 stage_state={}
 while True:
  stored=file.readline(MAX_LOGICAL+1)
  if not stored:return
  need(len(stored)<=MAX_LOGICAL,'PHYSICAL2048');expanded=decode_line(stored,run,epoch,previous,stage_state=stage_state);row=load(expanded);previous=row['sha256'];yield expanded
def frame_capacity():
 wrapped=lambda payload:13+4*((HEADER.size+payload+2)//3)
 parts={'RX':wrapped(40),'INTENT':wrapped(768),'SENT':wrapped(4),'STAGE32':wrapped(8+32*8)}
 return {'physicalMaximumBytesPerAcceptedFrame':sum(parts.values()),'parts':parts,'headerBytes':HEADER.size,'logicalMaximumBytesPerRecord':MAX_LOGICAL,'STAGEActualFieldsMaximum':32,'maskBits':64}
