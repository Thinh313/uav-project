"""Public Android Intent bridge. No private baseline, binding push, or input authority."""
import base64,json,secrets,time
from pathlib import Path
from collections import deque
from .candidate import put
from pilot.betaintegrated01.runtime.ap_stage import canonical
from .proofs import validate_native_ack,need,workspace_projection
PACKAGE='vn.rtr.aeris.mission'
COMPONENT=PACKAGE+'/.CockpitActivity'
class NativeBridge:
 """Injected bounded command/log adapter; only the product supervisor invokes it."""
 def __init__(self,device,source,*,now=time.monotonic_ns,receipt_root=None,apk_sha=None):
  self.device=device;self.source=source;self.apk_sha=apk_sha;self.now=now;self.latest=None;self.trace=deque(maxlen=8);self.receipt_root=Path(receipt_root) if receipt_root is not None else None;self.requests=0
 def prepare_normal(self,*,deadline_ns):
  need(type(self.apk_sha) is str and len(self.apk_sha)==64,'INSTALLED_APK_EXPECTATION_REQUIRED')
  return self.device.prepare_normal(self.apk_sha,deadline_ns=min(deadline_ns,self.now()+60_000_000_000))
 def request(self,action,body=None,*,context=None,deadline_ns=None):
  need(action in ('STATUS','BOOTSTRAP'),'PUBLIC_ACTION');request=dict(body or {});request.setdefault('version',1);request.setdefault('requestNonce',secrets.token_hex(16))
  raw=json.dumps(request,separators=(',',':'),ensure_ascii=False).encode();need(len(raw)<=(512 if action=='STATUS' else 32768),'INTENT_BOUNDED')
  sent=self.now();deadline=min(sent+10_000_000_000,deadline_ns or sent+10_000_000_000)
  # Subscription is active before Intent. It must retain its original matching live row.
  with self.device.live_log('AERIS_MISSION',deadline_ns=deadline) as stream:
   self.device.intent(COMPONENT,{'missionAction':action,'missionRequestBase64':base64.urlsafe_b64encode(raw).decode()},deadline_ns=deadline)
   ack=None
   for row in stream:
    need(self.now()<=deadline,'PUBLIC_NATIVE10S')
    if row.get('requestNonce')!=request['requestNonce']:continue
    ack=row;break
   need(ack is not None,'LIVE_ACK_REQUIRED')
   pid=self.device.pid(PACKAGE,deadline_ns=deadline)
   snapshot=self.device.read_private(PACKAGE,ack.get('snapshotPath'),maximum_bytes=131072,deadline_ns=deadline)
   received=self.now();need(received<=deadline,'PUBLIC_NATIVE10S')
   result=validate_native_ack(request,ack,snapshot,pid=pid,source=self.source,expected_context=context,host_sent_ns=sent,host_received_ns=received)
   receipt={'request':request,'action':action,'hostSentNs':sent,'hostReceivedNs':received,'ack':ack,'snapshotSHA256':ack['snapshotSHA256'],'snapshotBytes':len(snapshot),'rawSnapshotSHA256':ack['snapshotSHA256']}
   self.requests+=1
   if self.requests>2048:raise ValueError('PUBLIC_REQUEST2048_METADATA_BOUND_NO_DROPS')
   if self.receipt_root is not None:
    encoded=canonical(receipt)+b'\n'
    need(len(encoded)<=32768,'PUBLIC_RECEIPT32KiB_METADATA_BOUND')
    put(self.receipt_root/('request-%05d.json'%self.requests),encoded)
   self.trace.append(receipt)
   self.latest=result;return result
 def status(self,*,context=None,deadline_ns=None):return self.request('STATUS',context=context,deadline_ns=deadline_ns)
 def stage(self,status,context,provider,*,survey=None,expected_draft_sha=None,deadline_ns=None):
  need(status['sourceSHA256']==self.source and status['state'].get('ownerActive') is False,'INERT_CURRENT_STATUS')
  need(status['state'].get('viewReady') is True and status['state'].get('presentedView')==status['state'].get('chosenView'),'VISIBLE_CURRENT_VIEW')
  need(status['state'].get('checkpoint',{}).get('phase') in ('READY','RECOVERED_NOT_LIVE_ACK'),'CHECKPOINT_CAN_BIND')
  need((survey is None)!=(expected_draft_sha is None),'NEW_SURVEY_XOR_EXISTING_HASH')
  workspace_projection(status,ready=True)
  body={'version':1,'requestNonce':secrets.token_hex(16),'processEpoch':status['processEpoch'],'viewEpoch':status['viewEpoch'],'baseRevision':status['revision'],'sourceSHA256':self.source,'context':context,'provider':provider,'survey':survey,'expectedDraftSHA256':expected_draft_sha}
  result=self.request('BOOTSTRAP',body,context=context,deadline_ns=deadline_ns)
  need(result.get('lifecycle',{}).get('phase')=='READY' and result['state'].get('ownerActive') is False,'READY_IS_STAGED_NOT_CONNECTED')
  workspace=result['state']['workspace'];draft=workspace.get('draft');need(type(draft)is dict and type(workspace.get('draftSHA256'))is str and len(workspace['draftSHA256'])==64,'READY_ACTUAL_SAVED_DRAFT')
  if expected_draft_sha is not None:need(workspace['draftSHA256']==expected_draft_sha,'READY_EXACT_EXISTING_DRAFT_SHA')
  else:
   need(type(draft.get('revision'))is int and draft['revision']==1 and draft.get('trainingOnly')is True and draft.get('name')==survey['name'].strip(' '),'READY_NEW_DRAFT_REVISION_NAME')
   for key in ('kind','datum','altitudeDatum','units','geometry','altitudeM','corridorWidthM'):need(draft.get(key)==survey[key] and not isinstance(draft.get(key),bool),'READY_NEW_SURVEY_SEMANTICS_'+key)
  return result
