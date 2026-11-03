"""Bounded STATUS-only observation framing. No operations or authority payload."""
import json,re,struct
MAX_ACK=2048;MAX_DTO=16384;MAX_RESPONSE=8+MAX_ACK+MAX_DTO

def unique(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('STATUS15_DUPLICATE_KEY')
  d[k]=v
 return d

def request_bytes(request):
 if type(request)is not dict or set(request)!={'version','requestNonce'}or type(request['version'])is not int or request['version']!=1 or type(request['requestNonce'])is not str or re.fullmatch('[a-f0-9]{32}',request['requestNonce'])is None:raise ValueError('STATUS15_REQUEST_ONLY_VERSION_NONCE')
 raw=json.dumps({'version':1,'requestNonce':request['requestNonce']},separators=(',',':')).encode('ascii')
 if len(raw)>512:raise ValueError('STATUS15_REQUEST512')
 return struct.pack('!I',len(raw))+raw

class HelloParser:
 def __init__(self):self.raw=bytearray();self.result=None
 def feed(self,part):
  if type(part)is not bytes:raise TypeError('STATUS15_ORIGINAL_BYTES')
  room=max(0,2053-len(self.raw))
  if len(part)>room:self.raw.extend(part[:room]);raise ValueError('STATUS15_HELLO_BOUNDED_PREFIX')
  self.raw.extend(part)
  if self.result is not None and part:raise ValueError('STATUS15_HELLO_TRAILING')
  if len(self.raw)<4:return
  n=struct.unpack('!I',self.raw[:4])[0]
  if not 0<n<=2048:raise ValueError('STATUS15_HELLO_LENGTH_BEFORE_ALLOCATION')
  if len(self.raw)<4+n:return
  if len(self.raw)!=4+n:raise ValueError('STATUS15_HELLO_TRAILING')
  self.result=bytes(self.raw)
 def eof(self):
  if self.result is None:raise ValueError('STATUS15_HELLO_PARTIAL_EOF')
  return self.result

class ResponseParser:
 def __init__(self):self.raw=bytearray();self.result=None
 def feed(self,part):
  if type(part)is not bytes:raise TypeError('STATUS15_ORIGINAL_BYTES')
  room=max(0,MAX_RESPONSE+1-len(self.raw))
  if len(part)>room:self.raw.extend(part[:room]);raise ValueError('STATUS15_RESPONSE_BOUNDED_PREFIX')
  self.raw.extend(part)
  if self.result is not None and part:raise ValueError('STATUS15_UNSOLICITED_TRAILING')
  if len(self.raw)<4:return
  n=struct.unpack('!I',self.raw[:4])[0]
  if not 0<n<=MAX_ACK:raise ValueError('STATUS15_ACK_LENGTH_BEFORE_ALLOCATION')
  if len(self.raw)<8+n:return
  m=struct.unpack('!I',self.raw[4+n:8+n])[0]
  if not 0<m<=MAX_DTO:raise ValueError('STATUS15_DTO_LENGTH_BEFORE_ALLOCATION')
  if len(self.raw)<8+n+m:return
  if len(self.raw)!=8+n+m:raise ValueError('STATUS15_RESPONSE_TRAILING')
  ack=bytes(self.raw[4:4+n])
  if not ack.endswith(b'\n')or b'\n'in ack[:-1]or b'\r'in ack:raise ValueError('STATUS15_ACK_EXACT_ONE_LINE')
  self.result={'ackHeader':bytes(self.raw[:4]),'ack':ack,'dtoHeader':bytes(self.raw[4+n:8+n]),'dto':bytes(self.raw[8+n:])}
 def eof(self):
  if self.result is None:raise ValueError('STATUS15_RESPONSE_PARTIAL_EOF')
  return self.result
