"""Independent bounded reader for CLOSED native control raw, external anchor required.

This checks bytes and local input/wire causality. It does not turn ACK or local
write into flight execution, ground or physical controller attestation.
"""
from pathlib import Path
import base64,hashlib,json,struct,re

def _pairs(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('DUPLICATE_NATIVE_JSON_KEY')
  d[k]=v
 return d
def strict_json(raw):return json.loads(raw,object_pairs_hook=_pairs,parse_constant=lambda v:(_ for _ in()).throw(ValueError('NONFINITE_NATIVE_JSON')))
def schema(v,keys,fmt):
 if type(v)is not dict or set(v)!=set(keys)or v.get('format')!=fmt or type(v.get('version'))is not int or v['version']!=1:raise ValueError('NATIVE_FORMAT_VERSION_SCHEMA')

def sha(b):return hashlib.sha256(b).hexdigest()
def load(p,bound=2**20):
 b=p.read_bytes()
 if len(b)>bound:raise ValueError('BOUND:'+str(p))
 return b,strict_json(b)
def native_cold(root,external_anchor):
 root=Path(root)if isinstance(root,(str,Path))else root;raw,terminal=load(root/'session.json');assert sha(raw)==external_anchor
 schema(terminal,{'format','version','run','epoch','segments','records','head','lastSeal','authorityRestorable','publicationAllowed'},'aeris-native-session')
 assert type(terminal['segments'])is int and 1<=terminal['segments']<=256 and type(terminal['records'])is int and terminal['records']>=2
 assert terminal['publicationAllowed']is False and terminal['authorityRestorable']is False
 previous='';previous_seal='';n=0;last=-1;events={};inputs={};bindings={};pending=None;normal=[];rx=[];unknown=0;refusals=[];pending_n=None;failed_event=False;close_reason=None;closed_seen=False
 for segment in range(terminal['segments']):
  path=root/f'segment-{segment:06}.jsonl';body=path.read_bytes();assert len(body)<=8*2**20
  sealraw,seal=load(root/f'seal-{segment:06}.json');assert seal['sha256']==sha(body)and seal['bytes']==len(body)and seal['previousSeal']==previous_seal
  schema(seal,{'format','version','run','epoch','segment','file','bytes','sha256','first','last','head','previousSeal'},'aeris-native-seal')
  assert seal['run']==terminal['run']and seal['epoch']==terminal['epoch']and type(seal['segment'])is int and seal['segment']==segment and seal['file']==f'segment-{segment:06}.jsonl'
  assert all(type(seal[k])is int for k in('bytes','first','last'))
  first=n+1;segment_row=0
  for line in body.splitlines(keepends=True):
   assert line.endswith(b'\n')and len(line)<=16384
   assert not closed_seen
   row=strict_json(line);schema(row,{'format','version','run','epoch','segment','n','previous','monotonicNs','kind','base64','sha256'},'aeris-native-record')
   assert type(row['n'])is int and type(row['segment'])is int and type(row['kind'])is str and re.fullmatch('[A-Z][A-Z0-9_]{0,47}',row['kind'])
   assert (segment_row==0)==(row['kind']=='HEADER');segment_row+=1
   stored=row['sha256'];assert line.endswith(b',"sha256":"'+stored.encode()+b'"}\n')
   plain=line[:-(len(stored)+len(',"sha256":""}\n'))]+b'}'
   assert sha(plain)==stored
   assert row['n']==n+1 and row['previous']==previous and row['segment']==segment and row['run']==terminal['run']and row['epoch']==terminal['epoch']and type(row['monotonicNs'])is int and row['monotonicNs']>=last
   n+=1;last=row['monotonicNs'];previous=stored;kind=row['kind'];payload=base64.b64decode(row['base64'],validate=True);events[kind]=events.get(kind,0)+1
   if kind=='HEADER':
    h=strict_json(payload);schema(h,{'format','version','segment','previousSeal'},'aeris-native-segments');assert type(h['segment'])is int and h['segment']==segment and h['previousSeal']==previous_seal
   elif kind in('CONTROL_INPUT','CONTROL_CONSENT','CONTROL_LEASE_RENEWED'):raise ValueError('LEGACY_AUTHORITY_EVENT_NOT_SELECTED09')
   elif kind=='TX_INTENT':
    assert pending is None and not refusals;pending=payload;pending_n=n
   elif kind=='TX_WRITTEN':
    assert pending==payload;pending=None
    if payload[0]==253 and int.from_bytes(payload[7:10],'little')==70:
     p=payload[10:-2];values=struct.unpack_from('<8H',p);binding=bindings.get(sha(payload))
     if binding is not None:
      v,i=binding;assert v['purpose']=='RC_LOITER_PILOT'
      # Java Math.round is floor(x+.5), including negative x.
      import math
      a=i['axes'];expected=[math.floor(1500+125*x+.5)for x in (a[0],-a[1],a[2],a[3])]
      assert list(values[:4])==expected and p[16:18]==bytes([42,1])
      assert row['monotonicNs']>=i['elapsedNs'];normal.append({'inputSequence':i['sequence'],'producerElapsedNs':i['elapsedNs'],'localWrittenNs':row['monotonicNs'],'axes':a,'PWM':expected})
   elif kind=='TX_REFUSED':
    v=strict_json(payload);assert pending is not None and type(v.get('intentRecordN'))is int and v['intentRecordN']==pending_n
    assert set(v)=={'wireSHA256','intentRecordN','reasonClass','reason','disposition','socketCallbackEntered','run','epoch'}and v['wireSHA256']==sha(pending)and v['run']==terminal['run']and v['epoch']==terminal['epoch']
    assert v['disposition']=='PRE_SOCKET_REFUSED'and v['socketCallbackEntered']is False and type(v['reasonClass'])is str and 1<=len(v['reasonClass'])<=128 and type(v['reason'])is str and len(v['reason'])<=512
    refusals.append({'record':n,'intentRecordN':pending_n,**v});pending=None;pending_n=None
   elif kind=='CONTROL_FAILURE':failed_event=True
   elif kind=='SESSION_CLOSE':
    v=strict_json(payload);assert set(v)=={'reason','authorityRestorable','aircraftExecutionAccepted'}and n==terminal['records']and segment==terminal['segments']-1
    if refusals:assert failed_event
    closed_seen=True;close_reason=v['reason'];assert v['authorityRestorable']is False and v['aircraftExecutionAccepted']is False
   elif kind.startswith('TX_')and kind not in('TX_INTENT','TX_WRITTEN','TX_UNKNOWN'):raise ValueError('UNKNOWN_TX_OUTCOME')
   elif kind=='TX_UNKNOWN':
    assert pending is not None;v=strict_json(payload);assert v['wireSHA256']==sha(pending);pending=None;unknown+=1
   elif kind=='RX':rx.append({'n':n,'monotonicNs':row['monotonicNs'],'bytes':len(payload),'sha256':sha(payload)})
  assert seal['first']==first and seal['last']==n and seal['head']==previous
  previous_seal=sha(sealraw)
 assert terminal['records']==n and terminal['head']==previous and terminal['lastSeal']==previous_seal
 assert pending is None and events.get('SESSION_CLOSE')==1 and unknown==0
 if refusals:assert failed_event and close_reason=='CONTROL_FAILED_RESOURCES_CLOSED'
 if failed_event:assert close_reason=='CONTROL_FAILED_RESOURCES_CLOSED'
 if close_reason=='CONTROL_FAILED_RESOURCES_CLOSED':assert failed_event
 return {'format':'aeris-independent-native-control-cold','integrity':'PASS_EXTERNAL_ANCHOR','run':terminal['run'],'epoch':terminal['epoch'],'records':n,'events':events,'inputs':len(inputs),'normalRC':normal,'RX':rx,'unknownSends':unknown,'preSocketRefusals':refusals,'forensicOnly':failed_event or bool(refusals),'executionAcceptance':False,'physicalInputAttested':False,'remoteNetworkAge':'NOT_MEASURED','scope':'09 strict original chain only; transaction+local input-to-wire proof required by selected resolver/authority; actual AP motion/modes/failsafe/ground require independent raw oracle'}

def native_cold_tar(path,prefix,external_anchor):
 import tarfile
 class ReadOnlyTarPath:
  def __init__(self,table,name=''):self.table,self.name=table,name
  def __truediv__(self,name):return ReadOnlyTarPath(self.table,self.name+'/'+name if self.name else name)
  def read_bytes(self):return self.table[self.name]
 with tarfile.open(path)as t:
  table={m.name[len(prefix):]:t.extractfile(m).read()for m in t.getmembers()if m.isfile()and m.name.startswith(prefix)}
  assert sum(map(len,table.values()))<=16*2**20
  return native_cold(ReadOnlyTarPath(table),external_anchor)

if __name__=='__main__':
 import sys
 print(json.dumps(native_cold(sys.argv[1],sys.argv[2]),indent=2))
