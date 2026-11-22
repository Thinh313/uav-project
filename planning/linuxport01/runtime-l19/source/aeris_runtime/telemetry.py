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
 def __init__(self,root,context,event_observer=None):self.event_observer=event_observer;self.root=Path(root);self.context=context;self.seq=-1;self.head='0'*64;self.segment=0;self.offset=0;self.witness=GroundWitness(context);self.frames=0;self.cut_requested=None;self.cut_accepted=False;self.native_connection_seen=False;self.native_bytes_seen=False;self.pending_forward_seen=False;self.cut_request_ref=None;self.cut_accepted_ref=None;self.cut_closed_ref=None;self.failure_closed_ref=None;self.eof_ref=None;self.eof_pending=None;self.forward_pending={'toAP':b'','toNative':b''};self.forward_intent=None;self.forward_unknown=False;self.cut_pending=None
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
    kind=e['eventKind'];clean={k:v for k,v in d.items()if not k.startswith('_')};ref={'sequence':self.seq,'sha256':self.head,'observedHostNs':d.get('_observedHostNs')}
    self._forward_event(kind,clean,ref)
    if kind=='PENDING_FORWARD_BYTES':self.pending_forward_seen=True
    if kind=='CUT_REQUEST':
     if self.cut_request_ref is not None or set(clean)!={'run','epoch','boot','action','nonce','hostNs'} or any(clean[k]!=self.context[k]for k in('run','epoch','boot'))or clean['action']!='CUT_NATIVE_LINK' or type(clean['nonce'])is not str or not 1<=len(clean['nonce'])<=64 or type(clean['hostNs'])is not int or type(ref['observedHostNs'])is not int or not 0<=ref['observedHostNs']-clean['hostNs']<=2_000_000_000:raise ValueError('ORIGINAL_CUT_REQUEST_CONTEXT_CLOCK')
     self.cut_requested=clean;self.cut_request_ref=ref
    if kind=='CUT_ACCEPTED':
     pending=clean.get('pending',{});empty=hashlib.sha256(b'').hexdigest()
     if self.cut_request_ref is None or self.cut_accepted_ref is not None or clean.get('action')!='CUT_NATIVE_LINK' or clean.get('nativeReconnectAllowed')is not False or clean.get('restoredAuthority')is not False or clean.get('pendingOutcome')!='NOT_RETRIED_UNKNOWN_IF_PARTIAL' or set(pending)!={'toAPBytes','toAPSHA256','toNativeBytes','toNativeSHA256'} or any(type(pending[k])is not int or pending[k]<0 for k in('toAPBytes','toNativeBytes')):raise ValueError('ORIGINAL_CUT_ACCEPTED_SCHEMA')
     if any(pending[k]!=0 for k in('toAPBytes','toNativeBytes'))or any(pending[k]!=empty for k in('toAPSHA256','toNativeSHA256')):self.pending_forward_seen=True
     if type(ref['observedHostNs'])is not int or ref['observedHostNs']<self.cut_request_ref['observedHostNs']:raise ValueError('ORIGINAL_CUT_ACCEPTED_CLOCK')
     self.cut_accepted=True;self.cut_accepted_ref=ref
    if kind=='CUT_CONNECTIONS_CLOSED':
     a=clean.get('closeStartedHostNs');b=clean.get('closedHostNs');n=ref['observedHostNs']
     if self.cut_accepted_ref is None or self.cut_closed_ref is not None or any(type(v)is not int for v in(a,b,n))or not self.cut_accepted_ref['observedHostNs']<=a<=b<=n or clean.get('nativeReconnectAllowed')is not False or clean.get('FDMClockUntouched')is not True or type(clean.get('applicationPassiveTXBytes'))is not int or clean['applicationPassiveTXBytes']!=0:raise ValueError('ORIGINAL_CUT_CLOSED_CLOCK_SCHEMA')
     self.cut_closed_ref={**ref,'closedHostNs':b}
    if e['eventKind']=='PASSIVE_FRAME':self.witness.feed(d,{'sequence':self.seq,'sha256':self.head});self.frames+=1
    if self.event_observer is not None:self.event_observer(kind,d,ref)
  if self.seq==upto:
   if self.head!=expected:raise ValueError('COMMITTED_PREFIX_HEAD_MISMATCH')
   self.witness.prefix={'sequence':self.seq,'sha256':self.head};return True
  return False

 def _pending_summary(self,value):
  if type(value)is not dict or set(value)!={'toAPBytes','toAPSHA256','toNativeBytes','toNativeSHA256'}:raise ValueError('LIVE_PENDING_SCHEMA')
  for direction,raw in self.forward_pending.items():
   if type(value[direction+'Bytes'])is not int or value[direction+'Bytes']!=len(raw) or value[direction+'SHA256']!=hashlib.sha256(raw).hexdigest():raise ValueError('LIVE_PENDING_NOT_ORIGINAL_BYTES')
 def _forward_event(self,kind,data,ref):
  terminal=self.failure_closed_ref or self.cut_closed_ref
  cut_kind=kind in('CUT_REQUEST','CUT_ACCEPTED','CUT_CONNECTIONS_CLOSED')
  if self.eof_ref is not None and cut_kind or self.cut_request_ref is not None and kind in('NATIVE_PATH_EOF','NATIVE_FAILURE_CONNECTIONS_CLOSED')or terminal is not None and cut_kind:raise ValueError('MUTUALLY_EXCLUSIVE_TERMINAL_FENCE_ROUTES')
  if self.eof_ref is not None and kind in('NATIVE_CONNECTED','NATIVE_RX','AP_RELAY_RX','FORWARD_INTENT','FORWARD_LOCAL_RETURN','FORWARD_NOT_READY','FORWARD_UNKNOWN','NATIVE_PATH_EOF'):raise ValueError('NATIVE_OR_FORWARD_EVENT_AFTER_TERMINAL_EOF')
  if terminal is not None and kind in('NATIVE_CONNECTED','NATIVE_RX','AP_RELAY_RX','FORWARD_INTENT','FORWARD_LOCAL_RETURN','FORWARD_NOT_READY','FORWARD_UNKNOWN','NATIVE_PATH_EOF','NATIVE_FAILURE_CONNECTIONS_CLOSED'):raise ValueError('POST_FENCE_NATIVE_OR_FORWARD_EVENT')
  if kind in('NATIVE_RX','AP_RELAY_RX'):
   raw=bytes.fromhex(data['rawHex']);direction='toAP'if kind=='NATIVE_RX'else'toNative'
   if not raw or len(raw)>4096 or len(self.forward_pending[direction])+len(raw)>16384:raise ValueError('LIVE_FORWARD_ORIGINAL_CHUNK_BOUND')
   self.forward_pending[direction]+=raw
  elif kind=='FORWARD_INTENT':
   direction=data.get('direction');raw=bytes.fromhex(data['rawHex'])
   if self.forward_intent is not None or direction not in self.forward_pending or not raw or len(raw)>4096 or self.forward_pending[direction][:len(raw)]!=raw:raise ValueError('LIVE_FORWARD_INTENT_ORIGINAL_PREFIX')
   self.forward_intent=(direction,raw)
  elif kind in('FORWARD_LOCAL_RETURN','FORWARD_NOT_READY'):
   if self.forward_intent is None:raise ValueError('LIVE_FORWARD_RETURN_WITHOUT_INTENT')
   direction,raw=self.forward_intent;n=data.get('sentBytes')
   if data.get('direction')!=direction or type(n)is not int or not 0<=n<=len(raw) or kind=='FORWARD_LOCAL_RETURN'and n==0 or kind=='FORWARD_NOT_READY'and n!=0:raise ValueError('LIVE_FORWARD_ORIGINAL_RETURN_COUNT')
   self.forward_pending[direction]=self.forward_pending[direction][n:];self.forward_intent=None
  elif kind=='FORWARD_UNKNOWN':self.forward_unknown=True
  elif kind=='NATIVE_PATH_EOF':
   if self.eof_ref is not None or data.get('side')not in('native','upstream')or data.get('noRetry')is not True:raise ValueError('LIVE_ORIGINAL_EOF_SCHEMA')
   self._pending_summary(data.get('pending'));self.eof_ref={**ref,'side':data['side']};self.eof_pending=dict(data['pending'])
  elif kind=='NATIVE_FAILURE_CONNECTIONS_CLOSED':
   start=data.get('closeStartedHostNs');closed=data.get('closedHostNs');observed=ref.get('observedHostNs')
   if self.eof_ref is None or self.forward_intent is not None or self.forward_unknown or self.forward_pending['toAP']:raise ValueError('FAILURE_FENCE_ORIGINAL_EOF_NO_AMBIGUOUS_NATIVE_SEND')
   if any(type(v)is not int for v in(start,closed,observed,self.eof_ref.get('observedHostNs')))or not self.eof_ref['observedHostNs']<=start<=closed<=observed:raise ValueError('FAILURE_FENCE_ORIGINAL_CLOSE_CLOCK')
   if data.get('sourceSide')!=self.eof_ref['side']or data.get('socketFDsClosed')is not True or data.get('pending')!=self.eof_pending or data.get('pendingOutcome')!='NOT_RETRIED_UNKNOWN_IF_PARTIAL'or data.get('nativeReconnectAllowed')is not False or data.get('FDMClockUntouched')is not True or data.get('applicationPassiveTXBytes')!=0 or type(data.get('applicationPassiveTXBytes'))is not int or data.get('restoredAuthority')is not False:raise ValueError('FAILURE_FENCE_SOURCE_NO_AUTHORITY_SCHEMA')
   self._pending_summary(data['pending']);self.failure_closed_ref={**ref,'closedHostNs':closed,'eofRef':dict(self.eof_ref),'pending':dict(data['pending'])};self.forward_pending={'toAP':b'','toNative':b''};self.witness.begin_landing(closed)
  elif kind=='CUT_ACCEPTED':self._pending_summary(data.get('pending'));self.cut_pending=dict(data['pending'])
  elif kind=='CUT_CONNECTIONS_CLOSED':
   if self.forward_intent is not None or self.forward_unknown:raise ValueError('CUT_FENCE_UNRESOLVED_NATIVE_SEND')
   self.forward_pending={'toAP':b'','toNative':b''}

 def preowner_fence(self,request):
  if self.cut_requested!=request or self.cut_closed_ref is None or self.cut_accepted_ref is None or self.native_connection_seen or self.native_bytes_seen or self.pending_forward_seen:raise ValueError('FAILURE_ABORT_FENCE_OR_LIFETIME_NO_NATIVE_HISTORY')
  if self.witness.prefix is None or self.witness.prefix!={'sequence':self.seq,'sha256':self.head} or self.seq<self.cut_closed_ref['sequence']:raise ValueError('FENCE_COMPLETE_ORIGINAL_PREFIX_REQUIRED')
  return {'format':'aeris-failed-preowner-ingress-fence','version':1,'context':dict(self.context),'request':dict(request),'requestRef':dict(self.cut_request_ref),'acceptedRef':dict(self.cut_accepted_ref),'closedRef':dict(self.cut_closed_ref),'committedPrefix':dict(self.witness.prefix),'nativeConnectionEverSeen':False,'nativeBytesEverSeen':False,'pendingForwardEverSeen':False,'nativeReconnectAllowed':False,'FDMClockUntouched':True}
