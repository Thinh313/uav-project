"""Committed-prefix raw receiver for lifecycle evidence; no sending or authority API."""
from pathlib import Path
from collections import deque
import hashlib,json,zlib,time
from pilot.betaintegrated01.runtime.ap_stage import canonical
from .audit.native_chain_json import strict_json
from pilot.betaintegrated01.control01.mavlink import Framer,observe
class GroundWitness:
 def __init__(self,context):
  self.context=context;self.h=None;self.l=None;self.p=None;self.groups=deque(maxlen=2);self.used_h=set();self.used_l=set();self.after=None;self.incidents=[];self.prefix=None;self.last=-1;self.wire_sequence=None;self.boot_by_id={};self.last_group_boot=None
 def begin_landing(self,original_host_ns):
  if type(original_host_ns)is not int or original_host_ns<0:raise ValueError('ORIGINAL_LANDING_BOUNDARY')
  if self.after is None:self.after=original_host_ns
 def feed(self,item,ref):
  raw=bytes.fromhex(item['wireHex']);f=Framer();frames=f.feed(raw,item['monotonicNs'])
  if len(frames)!=1 or f.pending or frames[0]['wireHex']!=item['wireHex']:raise ValueError('ORIGINAL_AP_CRC_FRAME_REQUIRED')
  actual=observe(frames[0])
  if any(json.dumps(actual.get(k),sort_keys=True)!=json.dumps(item.get(k),sort_keys=True) for k in ('fields','wireSequence','id','system','component')):raise ValueError('OBSERVED_FIELDS_NOT_RAW')
  if actual['system']!=42 or actual['component']!=1:
   if item.get('newSequenceObservation')is not False:raise ValueError('FOREIGN_SOURCE_CANNOT_REFRESH')
   return
  seq=actual['wireSequence'];delta=None if self.wire_sequence is None else (seq-self.wire_sequence)&255
  accepted=delta is None or 0<delta<128
  if item.get('newSequenceObservation') is not accepted:raise ValueError('RAW_SEQUENCE_CLASSIFICATION_MISMATCH')
  if not accepted:return
  self.wire_sequence=seq
  if actual.get('fields') is not None and 'bootMs' in actual['fields']:
   boot=actual['fields']['bootMs'];previous=self.boot_by_id.get(actual['id'])
   if previous is not None and boot<previous:raise ValueError('AP_BOOT_REGRESSION')
   self.boot_by_id[actual['id']]=boot
  n=item['monotonicNs']
  if type(n)is not int or n<self.last:raise ValueError('PASSIVE_OBSERVATION_REGRESSION')
  self.last=n;fields=item.get('fields')
  if fields is None:return
  value={'hostNs':n,'wireSHA256':hashlib.sha256(raw).hexdigest(),'rawRecord':dict(ref),**fields};kind=fields['kind']
  if kind=='STATUSTEXT'and'failsafe'in fields['text'].lower():
   if len(self.incidents)>=128:raise ValueError('FAILSAFE_INCIDENT_CAP_NO_DROPS')
   self.incidents.append({**value,'APEventHostNs':None,'triggerOrAction':'UNKNOWN_FROM_STATUSTEXT'})
  if kind=='HEARTBEAT':self.h=value
  if kind=='EXTENDED_SYS_STATE':self.l=value
  if kind=='GLOBAL_POSITION_INT':self.p=value
  if kind!='GLOBAL_POSITION_INT'or self.after is None or n<self.after or abs(fields['relativeAltitudeMm'])>400:return
  if self.last_group_boot is not None and fields['bootMs']<=self.last_group_boot:return
  h,l=self.h,self.l
  if h is None or l is None or h['armed']or l['landedState']!=1 or h['hostNs']<self.after or l['hostNs']<self.after or h['hostNs']in self.used_h or l['hostNs']in self.used_l or not 0<=n-h['hostNs']<=1_500_000_000 or not 0<=n-l['hostNs']<=1_000_000_000:return
  self.last_group_boot=fields['bootMs'];self.used_h.add(h['hostNs']);self.used_l.add(l['hostNs']);self.groups.append({'heartbeat':h,'landed':l,'position':value})
  # Only two distinct groups are needed; old IDs are not authority/cache.
  if len(self.used_h)>16:self.used_h={g['heartbeat']['hostNs']for g in self.groups};self.used_l={g['landed']['hostNs']for g in self.groups}
 def proof(self,now_ns):
  if type(now_ns)is not int or len(self.groups)!=2:raise ValueError('TWO_DISTINCT_FRESH_GROUND_GROUPS_REQUIRED')
  latest=self.groups[-1]
  if self.h is None or self.l is None or self.p is None or abs(self.p['relativeAltitudeMm'])>400 or self.h['armed']or self.l['landedState']!=1 or any(not 0<=now_ns-v['hostNs']<=1_500_000_000 for v in latest.values()):raise ValueError('GROUND_STALE_OR_CONTRADICTED')
  if self.prefix is None:raise ValueError('DURABLE_PREFIX_REQUIRED')
  return {'format':'aeris-original-ground-proof','version':1,'context':dict(self.context),'afterHostNs':self.after,'groups':list(self.groups),'committedPrefix':dict(self.prefix),'currentProofHostNs':now_ns,'processExitUsedAsGround':False}
class CommittedTransportReader:
 def __init__(self,root,context):self.root=Path(root);self.context=context;self.seq=-1;self.head='0'*64;self.segment=0;self.offset=0;self.witness=GroundWitness(context);self.frames=0;self.cut_requested=None;self.cut_accepted=False;self.native_connection_seen=False;self.native_bytes_seen=False
 def advance(self,projection,max_rows=4096):
  if any(projection.get(k)!=self.context[k]for k in('run','epoch','boot'))or projection.get('rawPrefixMeaning')!='APPEND_EVENT_RETURNED_AFTER_ORIGINAL_FSYNC':raise ValueError('ORIGINAL_COMMITTED_PREFIX_CONTEXT')
  upto=projection.get('rawJournalCommittedSequence');expected=projection.get('rawJournalCommittedHead')
  if type(upto)is not int or upto<self.seq or type(expected)is not str or len(expected)!=64:raise ValueError('COMMIT_PREFIX_REGRESSION')
  n=0
  while self.seq<upto and n<max_rows:
   p=self.root/('segment-%06d.jsonl'%self.segment)
   with p.open('rb')as f:
    f.seek(self.offset);line=f.readline(16385)
   if not line:
    nxt=self.root/('segment-%06d.jsonl'%(self.segment+1))
    if not nxt.exists():raise ValueError('COMMITTED_ROW_NOT_PRESENT')
    self.segment+=1;self.offset=0;continue
   if len(line)>16384 or not line.endswith(b'\n'):raise ValueError('COMMITTED_ROW_INCOMPLETE_OR_BOUND')
   row=strict_json(line);b=row['body'];
   if set(row)!={'body','crc32','sha256'} or set(b)!={'v','run','epoch','segment','seq','previous','kind','frame','payload'} or type(b.get('v'))is not int or b['v']!=2 or type(b.get('seq'))is not int or type(b.get('segment'))is not int or b['segment']!=self.segment:raise ValueError('LIVE_RAW_RECORD_SCHEMA')
   raw=canonical(b);h=hashlib.sha256(bytes.fromhex(self.head)+raw).hexdigest()
   if b.get('seq')!=self.seq+1 or b.get('previous')!=self.head or b.get('run')!=self.context['run']or b.get('epoch')!=self.context['epoch']or row.get('sha256')!=h or row.get('crc32')!=format(zlib.crc32(raw),'08x'):raise ValueError('LIVE_RAW_CHAIN_CRC_CONTEXT')
   self.seq=b['seq'];self.head=h;self.offset+=len(line);n+=1
   if b['kind']=='EVENT':
    e=b['payload'];d=e['data']
    if d.get('_boot')!=self.context['boot']:raise ValueError('LIVE_RAW_BOOT')
    if e['eventKind']=='NATIVE_CONNECTED':self.native_connection_seen=True
    if e['eventKind']=='NATIVE_RX':self.native_bytes_seen=True
    if e['eventKind']=='CUT_REQUEST':self.cut_requested={k:v for k,v in d.items() if not k.startswith('_')}
    if e['eventKind']=='CUT_ACCEPTED':self.cut_accepted=True
    if e['eventKind']=='PASSIVE_FRAME':self.witness.feed(d,{'sequence':self.seq,'sha256':self.head});self.frames+=1
  if self.seq==upto:
   if self.head!=expected:raise ValueError('COMMITTED_PREFIX_HEAD_MISMATCH')
   self.witness.prefix={'sequence':self.seq,'sha256':self.head};return True
  return False
