"""Strict physical-v2 indexed tar + exact09logical row view; no extraction/conversion."""
from pathlib import Path
import hashlib,json,re,tarfile
_frozen_compact=__import__('importlib').import_module('planning.betaintegrated01.cockpit05-compact10.flight.compact')
decode_segment=_frozen_compact.decode_segment;encoded=_frozen_compact.encoded;need=_frozen_compact.need;sha=_frozen_compact.sha
from .native_chain import strict_json
MIB=2**20;TAR_LIMIT=168*MIB;RUN_LIMIT=160*MIB;MEMBER_LIMIT=1024;SEGMENT_LIMIT=MIB;DECODED_LIMIT=512*MIB
SESSION_KEYS=('format','version','run','epoch','segments','records','head','lastSeal','lastLogicalSeal','logicalBytes','physicalSegmentBytes','authorityRestorable','publicationAllowed')
SEAL_KEYS=('format','version','run','epoch','segment','file','bytes','sha256','first','last','head','previousSeal','logicalBytes','logicalSHA256','logicalSeal','logicalSealSHA256')
LOGICAL_KEYS=('format','version','run','epoch','segment','file','bytes','sha256','first','last','head','previousSeal')
def file_sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(MIB),b''):h.update(b)
 return h.hexdigest()
def schema(v,keys,fmt,version):
 need(type(v)is dict and tuple(v)==keys and v['format']==fmt and type(v['version'])is int and v['version']==version,'METADATA_SCHEMA_ORDER')
def count(v,minimum=0,maximum=2**63-1):need(type(v)is int and minimum<=v<=maximum,'METADATA_NUMERIC_TYPE')
def digest(v):need(type(v)is str and re.fullmatch('[a-f0-9]{64}',v)is not None,'METADATA_SHA')
class IndexedNative:
 def __init__(self,path,prefix):
  self.path=Path(path);need(self.path.is_file()and not self.path.is_symlink()and self.path.stat().st_size<=TAR_LIMIT,'NATIVE_TAR168MiB');need(type(prefix)is str and re.fullmatch(r'files/control-runs/[A-Za-z0-9_.:-]{1,128}/',prefix)is not None,'PREFIX');self.prefix=prefix;self.members={};self.tar_sha=file_sha(path);total=0
  with tarfile.open(path,mode='r:')as archive:
   for allcount,m in enumerate(archive,1):
    need(allcount<=2048,'TAR_GLOBAL_MEMBERS')
    if not m.name.startswith(prefix):continue
    if m.isdir():continue
    need(m.isfile(),'NONREGULAR_RUN_MEMBER');name=m.name[len(prefix):];need(re.fullmatch(r'session\.json|writer\.lock|seal-\d{6}\.json|segment-\d{6}\.bin',name)is not None and name not in self.members,'MEMBER_ALLOWLIST_DUPLICATE')
    bound=MIB if name.endswith('.bin')else(0 if name=='writer.lock'else 65536);need(0<=m.size<=bound,'MEMBER_BOUND');self.members[name]=m;total+=m.size;need(len(self.members)<=MEMBER_LIMIT and total<=RUN_LIMIT,'TOTAL_PHYSICAL160MiB')
  self.total=total;self.terminal_raw=self.raw('session.json');self.terminal=strict_json(self.terminal_raw);schema(self.terminal,SESSION_KEYS,'aeris-native-compact-session',2);t=self.terminal
  for k in('segments','records','logicalBytes','physicalSegmentBytes'):count(t[k],1,256 if k=='segments'else DECODED_LIMIT if k=='logicalBytes'else RUN_LIMIT if k=='physicalSegmentBytes'else 2**63-1)
  for k in('head','lastSeal','lastLogicalSeal'):digest(t[k])
  need(t['authorityRestorable']is False and t['publicationAllowed']is False and self.prefix=='files/control-runs/'+t['run']+'/','TERMINAL_CONTEXT_FLAGS');need(encoded(t)==self.terminal_raw,'CANONICAL_TERMINAL_BYTES')
  required={'session.json'}|({'writer.lock'}if'writer.lock'in self.members else set())|{f'{k}-{n:06}.{ext}'for n in range(t['segments'])for k,ext in(('segment','bin'),('seal','json'))};need(set(self.members)==required,'EXACT_PHYSICAL_SEGMENT_SET');self.segments={};self.verified=False
 def raw(self,name):
  need(self.path.stat().st_size<=TAR_LIMIT,'TAR_SIZE_CHANGED')
  with tarfile.open(self.path,mode='r:')as a:
   m=self.members[name];v=a.extractfile(m).read(m.size+1)
  need(len(v)==m.size,'SHORT_MEMBER');return v
 def unchanged(self):need(file_sha(self.path)==self.tar_sha,'TAR_CHANGED')
 def verify(self,external_anchor):
  digest(external_anchor);need(sha(self.terminal_raw)==external_anchor,'EXTERNAL_PHYSICAL_SESSION_ANCHOR');t=self.terminal;previous_physical=previous_logical=head='';n=1;at=-1;decodedTotal=physicalTotal=frameTotal=0
  for ordinal in range(t['segments']):
   sealraw=self.raw(f'seal-{ordinal:06}.json');s=strict_json(sealraw);schema(s,SEAL_KEYS,'aeris-native-compact-seal',2);need(encoded(s)==sealraw,'CANONICAL_PHYSICAL_SEAL');l=s['logicalSeal'];schema(l,LOGICAL_KEYS,'aeris-native-seal',1);logicalSeal=encoded(l)
   for obj in(s,l):
    need(obj['run']==t['run']and obj['epoch']==t['epoch']and type(obj['segment'])is int and obj['segment']==ordinal,'SEAL_CONTEXT')
    for k in('bytes','first','last'):count(obj[k],1)
    for k in('sha256','head'):digest(obj[k])
   for k in('logicalBytes',):count(s[k],1,8*MIB)
   for k in('logicalSHA256','logicalSealSHA256'):digest(s[k])
   need(s['file']==f'segment-{ordinal:06}.bin'and l['file']==f'segment-{ordinal:06}.jsonl'and s['previousSeal']==previous_physical and l['previousSeal']==previous_logical and sha(logicalSeal)==s['logicalSealSHA256'],'SEAL_CHAIN_FILE')
   raw=self.raw(s['file']);need(len(raw)==s['bytes']and sha(raw)==s['sha256'],'PHYSICAL_FILE_SHA');hd=hashlib.sha256();count0=0;localBytes=0;first=n;priorHead=head;priorAt=at;frameBytes=0
   for rec in decode_segment(raw,t['run'],t['epoch'],ordinal,previous_physical,previous_logical,n,head,at):hd.update(rec['line']);localBytes+=len(rec['line']);head=rec['head'];at=rec['monotonicNs'];n+=1;count0+=1;frameBytes+=rec['physicalFrameBytes']
   need(s['first']==l['first']==first and s['last']==l['last']==n-1 and s['head']==l['head']==head and s['logicalBytes']==l['bytes']==localBytes and s['logicalSHA256']==l['sha256']==hd.hexdigest(),'LOGICAL_SEAL_EXACT')
   self.segments[ordinal]=dict(seal=s,sealRaw=sealraw,logicalSeal=logicalSeal,previousPhysical=previous_physical,previousLogical=previous_logical,first=first,previousHead=priorHead,previousTime=priorAt)
   previous_physical=sha(sealraw);previous_logical=sha(logicalSeal);decodedTotal+=localBytes;physicalTotal+=len(raw);frameTotal+=frameBytes;need(decodedTotal<=DECODED_LIMIT,'TOTAL_DECODED512MiB')
  need(t['records']==n-1 and t['head']==head and t['lastSeal']==previous_physical and t['lastLogicalSeal']==previous_logical and t['logicalBytes']==decodedTotal and t['physicalSegmentBytes']==physicalTotal,'TERMINAL_FULL_COVERAGE')
  self.decodedTotal=decodedTotal;self.physicalFramesBytes=frameTotal;self.physicalMetadataBytes=self.total-frameTotal;self.verified=True;self.unchanged();return self
 def decoded(self,ordinal):
  need(self.verified,'PHYSICAL_VERIFICATION_REQUIRED');s=self.segments[ordinal];raw=self.raw(f'segment-{ordinal:06}.bin');need(sha(raw)==s['seal']['sha256'],'PHYSICAL_FILE_CHANGED')
  yield from decode_segment(raw,self.terminal['run'],self.terminal['epoch'],ordinal,s['previousPhysical'],s['previousLogical'],s['first'],s['previousHead'],s['previousTime'])
 def read(self,name):
  if name=='session.json':return self.terminal_raw
  m=re.fullmatch(r'(segment|seal)-(\d{6})\.(jsonl|json)',name);need(m is not None,'LOGICAL_VIEW_PATH');ordinal=int(m[2]);need(ordinal in self.segments,'LOGICAL_VIEW_ORDINAL')
  if m[1]=='seal':return self.segments[ordinal]['logicalSeal']
  return b''.join(r['line']for r in self.decoded(ordinal))
 def rows(self):
  for n in range(self.terminal['segments']):
   for rec in self.decoded(n):yield strict_json(rec['line'])
  self.unchanged()
 def physical_records(self):
  for n in range(self.terminal['segments']):
   for rec in self.decoded(n):yield rec['monotonicNs'],rec['physicalFrameBytes'],len(rec['line'])
  self.unchanged()
class LazyPath:
 def __init__(self,source,name=''):self.source,self.name=source,name
 def __truediv__(self,name):return LazyPath(self.source,self.name+'/'+name if self.name else name)
 def read_bytes(self):return self.source.read(self.name)
def closed_native(path,prefix,external_anchor):
 source=IndexedNative(path,prefix).verify(external_anchor)
 from . import native_chain
 cold=native_chain.native_cold(LazyPath(source),external_anchor);report={k:v for k,v in cold.items()if k not in('normalRC','RX')};report.update(normalRCCount=len(cold['normalRC']),RXCount=len(cold['RX']),nativeTarSHA256=source.tar_sha,selectedRunBytes=source.total,logicalDecodedBytes=source.decodedTotal,physicalMetadataBytes=source.physicalMetadataBytes,physicalFormatVersion=2,reader='STRICT_PHYSICAL_V2_EXACT09_LOGICAL_VIEW_NO_EXTRACTION_OR_V1_TERMINAL_SYNTHESIS',maximumTarBytes=TAR_LIMIT,maximumSelectedRunBytes=RUN_LIMIT,maximumDecodedStreamBytes=DECODED_LIMIT)
 from .transactions import resolve_rows
 transactionProof={}
 for _ in resolve_rows(source.rows(),summary=transactionProof):pass
 report['commitTransactions']=transactionProof;source.unchanged();return report,source.rows()
