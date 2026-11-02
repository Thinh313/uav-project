"""Receive-only interval from committed CRC-verified Root original transport.
Bounds intentionally enclose AUTO: command ingress precedes physical execution;
first complete disarmed/landed source group follows it. No ACK/elapsed oracle.
"""
from pathlib import Path
import hashlib,re,struct,json
from .telemetry import GroundWitness
from pilot.betaintegrated01.control01.mavlink import Framer
from .product_seal import original_rows,need
class FlightIntervalTracker:
 def __init__(self,context):
  self.context=dict(context);self.framer=Framer();self.ground=GroundWitness(context);self.start=None;self.auto=None;self.end=None;self.intent=None;self.end_ref=None;self.auto_ingresses=[];self.last_mode=None;self.pending_auto=False
 def event(self,kind,data,ref):
  if kind=='NATIVE_RX':
   n=data.get('hostNs');need(type(n)is int,'INTERVAL_NATIVE_ORIGINAL_CLOCK')
   for frame in self.framer.feed(bytes.fromhex(data['rawHex']),n):
    if frame['id']!=76:continue
    p=frame['payload'];command=struct.unpack_from('<H',p,28)[0];target=tuple(p[30:32]);a,b=struct.unpack_from('<ff',p)
    if command==176 and a==1 and b==3:
     need(frame['system']==255 and frame['component']==190 and target==(42,1),'INTERVAL_FIXED_SOURCE_TARGET')
     need(not self.pending_auto and len(self.auto_ingresses)<16 and(self.start is None or self.auto is not None and self.last_mode!=3 and self.end is None),'INTERVAL_EXPLICIT_RESUME_AFTER_OBSERVED_NON_AUTO_NOT_RETRY');intent={**ref,'wireSHA256':hashlib.sha256(bytes.fromhex(frame['wireHex'])).hexdigest()}
     self.auto_ingresses.append(intent);self.pending_auto=True
     if self.start is None:self.start=n;self.intent=intent;self.ground.begin_landing(n)
  if kind=='PASSIVE_FRAME':
   self.ground.feed(data,ref)
   f=data.get('fields')
   if f and f['kind']=='HEARTBEAT'and data.get('newSequenceObservation')is True:self.last_mode=f['customMode'];self.pending_auto=False if self.last_mode==3 else self.pending_auto
   if self.start is not None and f and f['kind']=='HEARTBEAT'and f['armed']and f['customMode']==3 and data['monotonicNs']>=self.start and data.get('newSequenceObservation')is True:self.auto=self.auto or dict(ref)
   if self.auto and self.end is None and self.ground.groups:
    self.end=self.ground.groups[0]['position']['hostNs'];self.end_ref=dict(ref)
 def proof(self,reader,product,mission,workspace_original=None):
  need(re.fullmatch('[a-f0-9]{64}',mission or'')is not None,'INTERVAL_MISSION_SHA')
  need(self.start is not None and self.auto is not None and self.end is not None and self.end>self.start and reader.witness.prefix=={'sequence':reader.seq,'sha256':reader.head},'INTERVAL_COMMITTED_AUTO_AND_GROUND')
  need(all(type(r.get('sequence'))is int and r['sequence']<=reader.seq for r in[*self.auto_ingresses,self.auto,self.end_ref]),'INTERVAL_ALL_EVENTS_INSIDE_COMMITTED_PREFIX')
  wal,records,wh=original_rows(workspace_original if workspace_original is not None else Path(product)/'journal/workspace.jsonl','hash','previousHash','seq');reviews=[r['data']for r in records if r['kind']=='BETA_FLIGHT_REVIEW'];need(reviews,'INTERVAL_ORIGINAL_REVIEW');review=reviews[-1];need(review.get('accepted')is True and review['run']==self.context['run']and review['boot']==self.context['boot']and review['missionSHA256']==mission,'INTERVAL_EXACT_ACCEPTED_REVIEW')
  segments=review['flightClose']['journal']['segments'];need(1<=len(segments)<=8,'INTERVAL_CLOSED_FILES');paths=[]
  for s in segments:
   need(s.get('closed')is True and re.fullmatch(r'journal/flight-[a-f0-9-]{36}-s[0-9]{2}\.ajz01',s.get('file',''))is not None,'INTERVAL_EXACT_CLOSED_REF');p=Path(product)/s['file'];need(p.stat().st_size==s['storedBytes'],'INTERVAL_CLOSED_BYTES');paths.append(p)
  raw,rows,head=original_rows(paths,'sha256','previous','n',zero='');short={k:self.context[k]for k in('run','epoch','boot','operator','generation')};need(len([r for r in rows if r['kind']=='ROOT_WIRE_SESSION'and r['data']['context']['context']==short])==1 and rows[-1]['kind']=='LINK_CLOSE'and rows[-1]['data']['failure']is None and rows[-1]['data']['completion']['complete']is True,'INTERVAL_ORIGINAL_CLOSED_FLIGHT');need(review['flightClose']['journal']['head']==head and review['flightClose']['journal']['records']==len(rows),'INTERVAL_CLOSED_HASH_JOIN');need(any(r['kind']=='AUTO_OBSERVED'for r in rows),'INTERVAL_NODE_AUTO_CORRELATION')
  tx=[hashlib.sha256(bytes.fromhex(r['data']['rawHex'])).hexdigest()for r in rows if r['kind']=='TX_INTENT'and r['data'].get('id')==76 and r['data'].get('fields',{}).get('command')==176 and r['data']['fields'].get('param2')==3]
  for ingress in self.auto_ingresses:
   need(ingress['wireSHA256']in tx,'INTERVAL_EACH_AUTO_ORIGINAL_DURABLE_TX_INTENT');tx.remove(ingress['wireSHA256'])
  return {'proofKind':'ROOT_COLD_JOIN_VERIFIED_FLIGHT_INTERVAL','version':1,'run':self.context['run'],'boot':self.context['boot'],'missionSHA256':mission,'rootStartNs':str(self.start),'rootEndNs':str(self.end),'originalRawRef':{'transportRelativePath':str(reader.root.relative_to(Path(product).parents[2])),'throughSequence':reader.seq,'headSHA256':reader.head,'autoIngress':self.intent,'autoIngressCount':len(self.auto_ingresses),'autoIngressesSHA256':hashlib.sha256(json.dumps(self.auto_ingresses,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'autoObserved':self.auto,'landedDisarmed':self.end_ref},'workspacePrefixBytes':len(wal),'workspaceSHA256':hashlib.sha256(wal).hexdigest(),'flightDecodedSHA256':hashlib.sha256(raw).hexdigest(),'clockBounds':'ROOT_COMMAND_INGRESS_THROUGH_FIRST_COMPLETE_LANDED_DISARMED_GROUP','flightAcceptance':False}
