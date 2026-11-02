"""Strict constant-space METAVAL15 adjacent RX group barrier witness.

Raw and source-bound receipt are fsynced together. The completion witness is
written after the real barrier and becomes durable at the next strict barrier
or closed seal. It is not a second fsync timestamp or kernel attestation.
"""
import base64,hashlib
from .native_chain_json import strict_json

GROUP={'format','version','receiptElapsedNs','rawRecordN','rawPayloadSHA256','groupRecords','kernelNetworkAge'}
COMMIT={'format','version','receiptElapsedNs','rawRecordN','rawPayloadSHA256','groupRecordN','groupPayloadSHA256','groupDurableNs','parserAfterBarrier','completionWitnessDurability'}

def fail(s):raise ValueError('RXGROUP13:'+s)
def need(v,s):
 if not v:fail(s)
def integer(v):need(type(v)is int and 0<=v<2**63,'INTEGER');return v
def ordinal(row):return row.get('rawRecordN',row['n'])
def sha(raw):return hashlib.sha256(raw).hexdigest()

class RXAudit:
 def __init__(self):self.raw=None;self.group=None;self.groups=0;self.maxBarrierNs=0;self.maxReceiptToDurableNs=0
 def feed(self,row):
  kind=row['kind'];now=integer(row['monotonicNs']);n=integer(ordinal(row));data=base64.b64decode(row['base64'],validate=True)
  if kind=='AP_RX_RECEIPT':fail('LEGACY_TWO_BARRIER_RECEIPT_NOT_SELECTED13')
  if kind=='RX':
   need(self.raw is None and self.group is None,'OVERLAPPING_RX');need(1<=len(data)<=4096,'RAW_BOUND');self.raw=(row,data);return None
  if self.raw is None:
   need(kind not in('AP_RX_GROUP','AP_RX_GROUP_COMMIT'),'ORPHAN_GROUP_OR_COMPLETION');return None
  r,chunk=self.raw;raw_n=ordinal(r);raw_ns=r['monotonicNs']
  if self.group is None:
   need(kind=='AP_RX_GROUP'and n==raw_n+1,'GROUP_NOT_IMMEDIATELY_AFTER_RAW');v=strict_json(data)
   need(type(v)is dict and set(v)==GROUP and v['format']=='aeris-native-rx-group'and type(v['version'])is int and v['version']==1,'GROUP_SCHEMA')
   need(type(v['rawRecordN'])is int and v['rawRecordN']==raw_n and type(v['groupRecords'])is int and v['groupRecords']==2 and v['rawPayloadSHA256']==sha(chunk)and v['kernelNetworkAge']=='NOT_MEASURED','GROUP_RAW_BINDING')
   receipt=integer(v['receiptElapsedNs']);need(receipt<=raw_ns<=now,'GROUP_ORIGINAL_RECEIPT_CLOCK');self.group=(row,data,v);return None
  gr,gbytes,g=self.group
  need(kind=='AP_RX_GROUP_COMMIT'and n==ordinal(gr)+1,'COMPLETION_NOT_IMMEDIATELY_AFTER_GROUP');v=strict_json(data)
  need(type(v)is dict and set(v)==COMMIT and v['format']=='aeris-native-rx-group-commit'and type(v['version'])is int and v['version']==1,'COMPLETION_SCHEMA')
  for key in('receiptElapsedNs','rawRecordN','groupRecordN','groupDurableNs'):integer(v[key])
  need(v['receiptElapsedNs']==g['receiptElapsedNs']and v['rawRecordN']==raw_n and v['rawPayloadSHA256']==g['rawPayloadSHA256']and v['groupRecordN']==ordinal(gr)and v['groupPayloadSHA256']==sha(gbytes),'COMPLETION_RAW_GROUP_BINDING')
  need(v['parserAfterBarrier']is True and v['completionWitnessDurability']=='NEXT_STRICT_BARRIER_OR_CLOSED_SEAL','COMPLETION_SCOPE')
  durable=v['groupDurableNs'];need(g['receiptElapsedNs']<=raw_ns<=gr['monotonicNs']<=durable<=now,'COMPLETION_ACTUAL_CLOCK_ORDER')
  self.groups+=1;self.maxBarrierNs=max(self.maxBarrierNs,durable-raw_ns);self.maxReceiptToDurableNs=max(self.maxReceiptToDurableNs,durable-g['receiptElapsedNs'])
  event=dict(raw=chunk,rawRecordN=raw_n,rawAppendNs=raw_ns,groupRecordN=ordinal(gr),groupAppendNs=gr['monotonicNs'],completionRecordN=n,completionAppendNs=now,receiptElapsedNs=g['receiptElapsedNs'],rawPayloadSHA256=g['rawPayloadSHA256'],groupPayloadSHA256=sha(gbytes),groupDurableNs=durable)
  self.raw=self.group=None;return event
 def finish(self):
  need(self.raw is None and self.group is None,'INCOMPLETE_RX_GROUP_TAIL')
  return dict(format='aeris-ioadmit13-rx-group-audit',groups=self.groups,maxRawAppendToBarrierNs=self.maxBarrierNs,maxOriginalReceiptToBarrierNs=self.maxReceiptToDurableNs,groupRecords=2,groupFsyncCountFromSource=1,completionWitnessDurability='NEXT_STRICT_BARRIER_OR_CLOSED_SEAL',physicalClosedChainRequired=True,rawRewritten=False,remoteNetworkAge='NOT_MEASURED')
 def wrap(self,rows,summary=None):
  for row in rows:self.feed(row);yield row
  result=self.finish()
  if summary is not None:summary.update(result)
