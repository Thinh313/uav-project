"""Read-only audit. Never repairs, resumes or certifies transmission from an intent."""
from pathlib import Path
import json,gzip,hashlib,struct
from wal_journal import read_wal,unpack_intent,encode

def recover(out):
 parsed=read_wal(out/'frames.wal');records=parsed['records'];errors=[];intents={};rx={};sent={};outcomes={};close=None;metadata=None;unadmitted=set()
 for r in records:
  kind,frame=r['kind'],r['frame']
  try:
   if kind=='HEADER':
    if metadata is not None or r['seq']!=0:raise ValueError('Repeated/late HEADER')
    metadata=json.loads(r['payload']);assert metadata['format']=='aeris-journal04'and metadata['version']==1
   elif kind=='RX':
    d=json.loads(r['payload']);rx[r['seq']]={**d,'frame':frame}
   elif kind=='INTENT':
    body,snapshot=unpack_intent(r['payload']);row=json.loads(body);assert frame==row['frame']and frame not in intents
    assert row['epoch']==metadata['epoch']and row['rxSeq']in rx and rx[row['rxSeq']]['rawHex']==row['servoHex']and rx[row['rxSeq']]['frame']==frame
    assert row['source']=='MOCK_REFERENCE_PHYSICS_NOT_SITL'and'sensorSent'not in row
    assert row['clockDomain']=='mock-backend-python-monotonic'
    servo=bytes.fromhex(row['servoHex']);magic,rate,count,*pwm=struct.unpack('<HHI16H',servo);assert magic==18458 and rate==1200 and count==frame
    sensor=json.loads(row['sensorUtf8']);assert isinstance(sensor['timestamp'],float)
    if snapshot:assert json.loads(snapshot)['epoch']==metadata['epoch']
    intents[frame]={'seq':r['seq'],'row':row,'body':body,'snapshot':snapshot}
   elif kind=='SENT':
    d=json.loads(r['payload']);assert frame in intents and d['intentSeq']==intents[frame]['seq']and frame not in sent
    assert d['outcome']=='UDP_SEND_RETURNED_LENGTH'and d['returnedBytes']==len(intents[frame]['row']['sensorUtf8'].encode());sent[frame]=d
   elif kind=='OUTCOME':
    d=json.loads(r['payload']);assert frame not in outcomes and frame not in sent;outcomes[frame]=d
    if'intentSeq'in d and d['intentSeq']is not None:assert frame in intents and d['intentSeq']==intents[frame]['seq']
   elif kind=='CLOSE':
    if close is not None:raise ValueError('Multiple CLOSE')
    close=json.loads(r['payload']);assert r is records[-1]
   elif kind=='ERROR':
    d=json.loads(r['payload'])
    if d.get('reason')=='UNADMITTED_AT_MANAGED_STOP'and d.get('modelAdmitted')is False and d.get('rxSeq')in rx:unadmitted.add(d['rxSeq'])
    else:errors.append({'record':r['seq'],'frame':frame,'reportedError':d})
  except Exception as e:errors.append({'record':r['seq'],'kind':kind,'frame':frame,'semanticError':str(e)or'assertion'})
 raw=[];archive_error=None;digest=hashlib.sha256()
 if(out/'physics-raw.jsonl.gz').exists():
  try:
   with gzip.open(out/'physics-raw.jsonl.gz','rb')as f:
    for line in f:digest.update(line);raw.append(json.loads(line))
  except Exception as e:archive_error=str(e)
 seen=set()
 for row in raw:
  frame=row.get('frame')
  if frame in seen or frame not in sent or frame not in intents:errors.append({'archiveFrame':frame,'semanticError':'Duplicate/uncommitted archive'});continue
  seen.add(frame);expected={**intents[frame]['row'],'sensorSent':True,'sendObservation':'UDP_SEND_RETURNED_LENGTH'}
  if row!=expected:errors.append({'archiveFrame':frame,'semanticError':'Archive bytes/row differ from intent'})
 if close:
  if close.get('archiveRows')!=len(raw)or close.get('sentFrames')!=len(sent)or len(raw)!=len(sent)or close.get('archiveSha256')!=digest.hexdigest():errors.append({'semanticError':'Closure counts/hash do not reconcile'})
 ambiguous=[f for f in intents if f not in sent and outcomes.get(f,{}).get('outcome')!='NO_SEND_CALLED']
 uncomputed=[seq for seq,d in rx.items()if seq not in {x['row']['rxSeq']for x in intents.values()}]
 if close and any(seq not in unadmitted for seq in uncomputed):errors.append({'semanticError':'Unaccounted RX at complete closure'})
 complete=bool(close)and not parsed['error']and not archive_error and not errors and not ambiguous
 return {'status':'COMPLETE_ACCEPTED_MOCK_CAPTURE'if complete else'INCOMPLETE_CAPTURE_READ_ONLY','walError':parsed['error'],'archiveError':archive_error,'semanticErrors':errors,'metadata':metadata,'verifiedWalRecords':len(records),'verifiedPrefixBytes':parsed['verifiedPrefixBytes'],'walChainHex':parsed['chainHex'],'intents':intents,'rx':rx,'sent':sent,'outcomes':outcomes,'archiveRows':len(raw),'archiveFrames':sorted(seen),'sendOutcomeUnknownFrames':sorted(ambiguous),'rxWithoutIntentSeq':uncomputed,'explicitUnadmittedRxSeq':sorted(unadmitted),'completeAcceptedCapture':complete,'source':'MOCK_ONLY_NO_SITL','originalUnchanged':True}

def public(result):
 return {k:v for k,v in result.items()if k not in ['intents','rx','sent','outcomes','metadata']}
