"""Independent strict physical-v2 decoder. Exact09logicalbytes, no persisted conversion."""
import base64,hashlib,json,re,struct,zlib
HEADER=512;FIXED=112;PHYSICAL_SEGMENT=2**20;DECODED_SEGMENT=8*2**20;PAYLOAD=8192;MAX_LONG=2**63-1
NAME=re.compile(r'[A-Za-z0-9_.:-]{1,128}');KIND=re.compile(r'[A-Z][A-Z0-9_]{0,47}')
def need(v,why):
 if not v:raise ValueError('COMPACT10:'+why)
def encoded(v):return json.dumps(v,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def crc(v):return zlib.crc32(v)&0xffffffff
def header(raw,run,epoch,segment,previous_physical,previous_logical):
 need(type(raw)is bytes and len(raw)==HEADER,'HEADER_LENGTH');need(raw[:8]==b'AERISC10','HEADER_MAGIC');version,length,seg,rn,en,logical,flags=struct.unpack_from('>HHIHHHH',raw,8)
 need(version==2 and length==HEADER and seg==segment and 0<=seg<256 and logical==1 and flags==0 and 1<=rn<=128 and 1<=en<=128,'HEADER_SCHEMA')
 try:r=raw[88:88+rn].decode('ascii');e=raw[216:216+en].decode('ascii')
 except UnicodeError:need(False,'CONTEXT_ASCII')
 need(NAME.fullmatch(r)is not None and NAME.fullmatch(e)is not None and r==run and e==epoch,'CONTEXT')
 need(not any(raw[88+rn:216])and not any(raw[216+en:344])and not any(raw[376:508]),'PADDING_RESERVED')
 need(crc(raw[:508])==struct.unpack_from('>I',raw,508)[0],'HEADER_CRC');need(raw[344:376].hex()==sha(encoded(dict(run=run,epoch=epoch))),'HEADER_CONTEXT_SHA')
 need(raw[24:56]==(bytes(32)if segment==0 else bytes.fromhex(previous_physical))and raw[56:88]==(bytes(32)if segment==0 else bytes.fromhex(previous_logical)),'HEADER_PREVIOUS_SEALS')
 if segment==0:need(previous_physical==previous_logical=='','FIRST_PREVIOUS_SEALS')
 return dict(run=r,epoch=e,segment=seg)
def decode_segment(raw,run,epoch,segment,previous_physical,previous_logical,first_n,previous_head,last_time=-1):
 need(type(raw)is bytes and HEADER<len(raw)<=PHYSICAL_SEGMENT,'PHYSICAL_SEGMENT_BOUND');header(raw[:HEADER],run,epoch,segment,previous_physical,previous_logical);offset=HEADER;n=first_n;head=previous_head;total=0;count=0
 while offset<len(raw):
  need(len(raw)-offset>=FIXED,'PARTIAL_FRAME');f=raw[offset:offset+FIXED];need(f[:4]==b'R10\0','FRAME_MAGIC');length,flags,decoded,stored,ordinal,at,seg,kn,codec,reserved,row_crc,data_crc=struct.unpack_from('>HHIIQQIBBHII',f,4)
  need(length==FIXED and flags in(0,1)and decoded<=PAYLOAD and stored<=PAYLOAD and 1<=kn<=48 and reserved==0 and seg==segment and ordinal==n and 1<=n<=MAX_LONG and 0<=at<=MAX_LONG and at>=last_time,'FRAME_DOMAIN_ORDER')
  need(codec==0 and stored==decoded or codec==1 and stored<decoded,'CODEC_LENGTH')
  end=offset+FIXED+kn+stored;need(end<=len(raw),'TRUNCATED_PAYLOAD')
  try:kind=raw[offset+FIXED:offset+FIXED+kn].decode('ascii')
  except UnicodeError:need(False,'KIND_ASCII')
  need(KIND.fullmatch(kind)is not None and(count==0)==(kind=='HEADER'),'KIND_HEADER_ORDER')
  previous=''if flags==1 else f[48:80].hex();need(previous==head,'LOGICAL_PREVIOUS_CHAIN')
  if flags:need(n==1 and segment==0 and kind=='HEADER'and not any(f[48:80]),'EMPTY_PREVIOUS_DOMAIN')
  data=raw[offset+FIXED+kn:end];need(crc(data)==data_crc,'ENCODED_CRC')
  if codec==0:payload=data
  else:
   decoder=zlib.decompressobj(-15)
   try:payload=decoder.decompress(data,decoded+1)
   except zlib.error as e:raise ValueError('COMPACT10:RAW_DEFLATE_FORMAT')from e
   need(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,'DEFLATE_FINISH_TRAILING_DICTIONARY_OR_BOMB')
  need(len(payload)==decoded,'DECODED_LENGTH')
  body=encoded(dict(format='aeris-native-record',version=1,run=run,epoch=epoch,segment=segment,n=n,previous=previous,monotonicNs=at,kind=kind,base64=base64.b64encode(payload).decode()))
  logical_sha=sha(body);need(f[80:112].hex()==logical_sha,'LOGICAL_ROW_SHA');line=body[:-1]+b',"sha256":"'+logical_sha.encode()+b'"}\n';need(len(line)<=32768 and crc(line)==row_crc,'LOGICAL_ROW_CRC_BOUND')
  total+=len(line);need(total<=DECODED_SEGMENT,'DECODED_SEGMENT8MiB');count+=1
  yield dict(line=line,n=n,monotonicNs=at,head=logical_sha,physicalFrameBytes=end-offset,codec=codec,encodedPayloadBytes=stored,decodedPayloadBytes=decoded)
  offset=end;n+=1;head=logical_sha;last_time=at
 need(count>0 and offset==len(raw),'EMPTY_OR_PARTIAL_SEGMENT')
