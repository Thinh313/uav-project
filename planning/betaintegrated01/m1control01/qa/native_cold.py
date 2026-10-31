"""Independent bounded reader for CLOSED native control raw, external anchor required.

This checks bytes and local input/wire causality. It does not turn ACK or local
write into flight execution, ground or physical controller attestation.
"""
from pathlib import Path
import base64,hashlib,json,struct

def sha(b):return hashlib.sha256(b).hexdigest()
def load(p,bound=2**20):
 b=p.read_bytes()
 if len(b)>bound:raise ValueError('BOUND:'+str(p))
 return b,json.loads(b)
def native_cold(root,external_anchor):
 root=Path(root)if isinstance(root,(str,Path))else root;raw,terminal=load(root/'session.json');assert sha(raw)==external_anchor
 assert terminal['publicationAllowed']is False and terminal['authorityRestorable']is False
 previous='';previous_seal='';n=0;last=-1;events={};inputs={};bindings={};pending=None;normal=[];rx=[];unknown=0
 for segment in range(terminal['segments']):
  path=root/f'segment-{segment:06}.jsonl';body=path.read_bytes();assert len(body)<=8*2**20
  sealraw,seal=load(root/f'seal-{segment:06}.json');assert seal['sha256']==sha(body)and seal['bytes']==len(body)and seal['previousSeal']==previous_seal
  first=n+1
  for line in body.splitlines(keepends=True):
   assert line.endswith(b'\n')and len(line)<=16384
   row=json.loads(line);stored=row['sha256'];assert line.endswith(b',"sha256":"'+stored.encode()+b'"}\n')
   plain=line[:-(len(stored)+len(',"sha256":""}\n'))]+b'}'
   assert sha(plain)==stored
   assert row['n']==n+1 and row['previous']==previous and row['segment']==segment and row['run']==terminal['run']and row['epoch']==terminal['epoch']and type(row['monotonicNs'])is int and row['monotonicNs']>=last
   n+=1;last=row['monotonicNs'];previous=stored;kind=row['kind'];payload=base64.b64decode(row['base64'],validate=True);events[kind]=events.get(kind,0)+1
   if kind=='HEADER':
    h=json.loads(payload);assert h['segment']==segment and h['previousSeal']==previous_seal
   elif kind=='CONTROL_INPUT':
    v=json.loads(payload);assert v['run']==terminal['run']and v['epoch']==terminal['epoch']and len(v['axes'])==4 and all(type(x)in(int,float)and -1<=x<=1 for x in v['axes'])
    assert v['elapsedNs']<=row['monotonicNs']and row['monotonicNs']-v['elapsedNs']<=200_000_000
    assert v['sequence']not in inputs;inputs[v['sequence']]=v
   elif kind=='CONTROL_INPUT_WIRE_BINDING':
    v=json.loads(payload);i=inputs[v['inputSequence']];assert i['source']==v['source']and v['producerElapsedNs']==i['elapsedNs']and 0<=v['sendCheckNs']-i['elapsedNs']<=200_000_000
    bindings[v['wireSHA256']]=(v,i)
   elif kind=='TX_INTENT':
    assert pending is None;pending=payload
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
   elif kind=='TX_UNKNOWN':
    assert pending is not None;v=json.loads(payload);assert v['wireSHA256']==sha(pending);pending=None;unknown+=1
   elif kind=='RX':rx.append({'n':n,'monotonicNs':row['monotonicNs'],'bytes':len(payload),'sha256':sha(payload)})
  assert seal['first']==first and seal['last']==n and seal['head']==previous
  previous_seal=sha(sealraw)
 assert terminal['records']==n and terminal['head']==previous and terminal['lastSeal']==previous_seal
 assert pending is None and events.get('SESSION_CLOSE')==1
 return {'format':'aeris-independent-native-control-cold','integrity':'PASS_EXTERNAL_ANCHOR','run':terminal['run'],'epoch':terminal['epoch'],'records':n,'events':events,'inputs':len(inputs),'normalRC':normal,'RX':rx,'unknownSends':unknown,'executionAcceptance':False,'physicalInputAttested':False,'remoteNetworkAge':'NOT_MEASURED','scope':'Closed native integrity + local input-to-wire mapping; actual AP motion/modes/failsafe/ground require independent raw oracle'}

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
