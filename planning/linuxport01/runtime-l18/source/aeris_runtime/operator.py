"""Visible UI operator boundary; actual input events, no authority bypass/API flight command."""
import re,time,xml.etree.ElementTree as ET
from .proofs import need,navigation_measurement
class OperatorUI:
 def __init__(self,session):self.session=session;self.device=session.device;self.bridge=session.supervisor.native;self.last=None
 def snapshot(self):
  self.session.monitor.check();self.last=self.bridge.status(context=self.session.supervisor.context.value());return self.last
 def layout(self):return self.snapshot()['layout']
 def _nodes(self):
  deadline=min(self.session.supervisor._deadline(),time.monotonic_ns()+10_000_000_000);raw=self.device.command(['exec-out','uiautomator','dump','/dev/tty'],deadline_ns=deadline).decode();start=raw.find('<?xml');end=raw.rfind('</hierarchy>');need(start>=0 and end>=start,'ACTUAL_UIAUTOMATOR_TREE');return list(ET.fromstring(raw[start:end+12]).iter('node')),deadline
 def tap(self,identifier):
  snapshot=self.snapshot();layout=snapshot['layout'];node=layout.get('buttons',{}).get(identifier,{})
  need(node.get('visible') is True and node.get('enabled') is True and node.get('currentaction')==identifier,'SOURCE_BOUND_VISIBLE_ENABLED_NATIVE_BUTTON')
  bounds=node.get('bounds');need(type(bounds)is list and len(bounds)==4 and all(type(x)is int and 0<=x<8192 for x in bounds),'ACTUAL_NATIVE_LAYOUT_BOUNDS');x1,y1,x2,y2=bounds;need(x1<x2 and y1<y2,'NONZERO_VISIBLE_NODE')
  before=time.monotonic_ns();need(0<=before-self.bridge.trace[-1]['hostReceivedNs']<=200_000_000,'OPERATOR_CURRENT_LAYOUT_DISPATCH');deadline=min(self.session.supervisor._deadline(),before+2_000_000_000)
  self.device.command(['shell','input','tap',str((x1+x2)//2),str((y1+y2)//2)],deadline_ns=deadline);return {'identifier':identifier,'beforeActionHostNs':before,'afterActionHostNs':time.monotonic_ns(),'actualBounds':bounds,'sourceRevision':snapshot['revision'],'processEpoch':snapshot['processEpoch'],'viewEpoch':snapshot['viewEpoch'],'UIAutomatorDuringActiveTap':False}
 def navigate(self,view):
  need(view in ('survey','preflight','fly','review'),'PRODUCT_VIEW');identifier='nav-'+view
  deadline=min(self.session.supervisor._deadline(),time.monotonic_ns()+10_000_000_000)
  # Reserve the bounded proof BEFORE obtaining a time-sensitive measurement.
  with self.device.budget.operation({'command_receipts':1280+8192}):
   snapshot=self.snapshot();receipt=dict(self.bridge.trace[-1]);source_ref=self.bridge.last_receipt_ref
   need(receipt['action']=='STATUS'and source_ref is not None,'NAVIGATION_ORIGINAL_STATUS_REQUIRED')
   nav=navigation_measurement(snapshot,action=identifier);bounds=nav['targets'][identifier]['bounds'];before=time.monotonic_ns()
   navigation_measurement(snapshot,action=identifier,receipt=receipt,before_tap_ns=before)
   tap_ref=None;after_ref=None;after_tap=None;completed=False;primary=None;old_sequence=self.device.sequence
   try:
    self.device.command(['shell','input','tap',str((bounds[0]+bounds[2])//2),str((bounds[1]+bounds[3])//2)],deadline_ns=min(deadline,before+2_000_000_000),dispatch_deadline_ns=receipt['hostSentNs']+200_000_000)
    tap_ref=self.device.last_command_ref;after_tap=time.monotonic_ns()
    while time.monotonic_ns()<=deadline:
     value=self.snapshot();after_ref=self.bridge.last_receipt_ref
     if value['state'].get('chosenView')==view and value['state'].get('presentedView')==view and value['state'].get('viewReady')is True and value['state'].get('renderedWorkspaceVersion')==value['state'].get('workspaceProjection',{}).get('version'):
      completed=True;return value
     time.sleep(min(.5,max(0,(deadline-time.monotonic_ns())/1e9)))
    raise TimeoutError('CURRENT_VISIBLE_PRODUCT_VIEW')
   except BaseException as error:primary=error;raise
   finally:
    if tap_ref is None and self.device.sequence==old_sequence+1:tap_ref=self.device.last_command_ref
    if tap_ref is not None:
     proof={'format':'aeris-navigation-tap','version':1,'view':view,'ticket':nav['ticket'],'sourceRequestRef':source_ref,'tapCommandRef':tap_ref,'afterRequestRef':after_ref,'beforeTapHostNs':before,'afterTapHostNs':after_tap,'completed':completed,'failure':None if primary is None else type(primary).__name__+':'+str(primary)[:128]}
     try:
      from .metadata_budget import encoded
      need(len(encoded(proof))<=1280,'NAVIGATION_PROOF1280');self.device.store.receipt('navigation-tap.json',proof)
     except BaseException as secondary:
      if primary is None:raise
      primary.add_note('NAVIGATION_PROOF_UNDURABLE:'+type(secondary).__name__+':'+str(secondary)[:256])
 def stick_event(self,action,side,horizontal,vertical):
  need(action in ('DOWN','MOVE','UP') and side in ('left','right') and all(type(v)in(int,float) and -1<=v<=1 for v in (horizontal,vertical)),'NORMALIZED_OPERATOR_STICK_EVENT')
  if action=='DOWN':self.last=self.snapshot()
  need(self.last is not None and self.last['state'].get('chosenView')=='fly' and self.last['state'].get('ownerActive') is True,'CURRENT_FLY_STICK_LAYOUT')
  node=self.last['layout'].get('sticks',{}).get('control01-'+side+'-stick',{});b=node.get('bounds');need(node.get('visible') is True and type(b)is list and len(b)==4 and all(type(v)is int for v in b) and b[0]<b[2] and b[1]<b[3],'SOURCE_BOUND_STICK_BOUNDS')
  x=round((b[0]+b[2])/2+horizontal*(b[2]-b[0])*.4);y=round((b[1]+b[3])/2+vertical*(b[3]-b[1])*.4);self.session.monitor.check();before=time.monotonic_ns();self.device.command(['shell','input','touchscreen','motionevent',action,str(x),str(y)],deadline_ns=min(self.session.supervisor._deadline(),before+2_000_000_000));return {'action':action,'side':side,'x':x,'y':y,'beforeHostNs':before,'afterHostNs':time.monotonic_ns(),'HIDAttested':False,'nativeOwnsSamplerAndAuthority':True}
 def confirm_home(self):
  s=self.snapshot();f=s['state'].get('native',{}).get('flight',{});before=self.session.supervisor.begin_home_confirmation(f.get('homeHash'));action=self.tap('control01-confirm-home');receipt=self.session.supervisor.observed_home_confirmation(before);return {'action':action,'confirmation':receipt}
 def land(self):
  self.session.supervisor.landing_requested(time.monotonic_ns());return self.tap('control01-land')

 def preparation_snapshot(self):
  """Null-context UI is available only before any selected/uncertain stage."""
  supervisor=self.session.supervisor
  need(not supervisor.resources.children,'RECOVERY_BEFORE_AP_OR_BACKEND_DISPATCH')
  need(not supervisor.stage_attempted and not self.bridge.stage_attempted and not self.bridge.bootstrap_attempted,'RECOVERY_UNSELECTED_NO_STAGE_ATTEMPT')
  if self.session.monitor.health is not None:self.session.monitor.check()
  else:
   supervisor._deadline();g=self.session.monitor.guardian();need(g.get('alive')is True and g.get('sourceVerified')is True and g.get('closed')is False,'RECOVERY_LIVE_GENUINE_GUARDIAN')
  self.last=self.bridge.status(context=None);self.bridge.observe_unselected(self.last);return self.last
 def _preparation_tap(self,identifier):
  need(identifier in('recovery08-prepare','recovery08-backup-sha','recovery08-commit'),'EXACT_VISIBLE_RECOVERY_UI_ACTION')
  s=self.preparation_snapshot();n=s['layout'].get('buttons',{}).get(identifier,{})
  need(n.get('visible')is True and n.get('enabled')is True and n.get('currentaction')==identifier,'CURRENT_VISIBLE_RECOVERY_CONTROL')
  b=n.get('bounds');need(type(b)is list and len(b)==4 and all(type(v)is int and 0<=v<8192 for v in b)and b[0]<b[2]and b[1]<b[3],'RECOVERY_CURRENT_NATIVE_BOUNDS')
  before=time.monotonic_ns();need(0<=before-self.bridge.trace[-1]['hostReceivedNs']<=200_000_000,'RECOVERY_CURRENT_LAYOUT200MS')
  self.device.command(['shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2)],deadline_ns=min(self.session.supervisor._deadline(),before+2_000_000_000));return self.device.last_command_ref
 def quarantine_failed_checkpoint(self,backup_receipt_ref):
  """Explicit operator transaction, never an automatic FAILED-to-READY repair."""
  from .android import verify_cold_original_backup
  from .proofs import workspace_projection
  original=verify_cold_original_backup(self.device.store.root,backup_receipt_ref)
  need(original['serial']==self.device.serial,'RECOVERY_ORIGINAL_SAME_DEVICE')
  initial=self.preparation_snapshot();cp=initial['state'].get('checkpoint',{})
  need(cp.get('phase')=='FAILED'and cp.get('writerClosed')is True,'RECOVERY_ORIGINAL_FAILED_CLOSED_CHECKPOINT')
  deadline=min(self.session.supervisor._deadline(),time.monotonic_ns()+60_000_000_000);prepare=self._preparation_tap('recovery08-prepare')
  def wait(predicate):
   while True:
    s=self.preparation_snapshot()
    if predicate(s):return s
    need(time.monotonic_ns()<deadline,'RECOVERY_UI60S');time.sleep(min(.5,max(0,(deadline-time.monotonic_ns())/1e9)))
  prepared=wait(lambda s:s['state'].get('recovery',{}).get('phase')in('AWAITING_VERIFIED_BACKUP','FAILED_PRESERVED'))
  state=prepared['state']['recovery'];need(state.get('phase')=='AWAITING_VERIFIED_BACKUP'and state.get('originalTargetSHA256')==original['targetTableSHA256']and state.get('targetEntries')==original['targetEntryCount']and state.get('targetBytes')==original['targetLogicalBytes'],'RECOVERY_INDEPENDENT_BACKUP_EXACT_TARGET_TABLE')
  field=self._preparation_tap('recovery08-backup-sha');self.device.command(['shell','input','text',original['targetTableSHA256']],deadline_ns=deadline);text=self.device.last_command_ref;commit=self._preparation_tap('recovery08-commit')
  def complete_and_presented(s):
   state=s['state'];phase=state.get('recovery',{}).get('phase');checkpoint=state.get('checkpoint',{})
   if phase=='FAILED_PRESERVED':return True
   if phase!='COMPLETE':return False
   if checkpoint.get('phase')=='FAILED':return True
   projection=state.get('workspaceProjection',{})
   return checkpoint.get('phase')in('READY','RECOVERED_NOT_LIVE_ACK')and state.get('viewReady')is True and projection.get('initialized')is True and projection.get('pendingRefresh')is False and state.get('renderedWorkspaceVersion')==projection.get('version')
  after=wait(complete_and_presented)
  recovery=after['state']['recovery'];need(recovery.get('phase')=='COMPLETE'and recovery.get('authorityRestorable')is False and recovery.get('oldCompletionClaim')is False and recovery.get('originalTargetSHA256')==original['targetTableSHA256'],'RECOVERY_PRESERVED_ORIGINAL_NOT_OLD_COMPLETION')
  identity=recovery.get('newWorkspaceIdentity');need(type(identity)is str and re.fullmatch('[a-f0-9]{32}',identity)is not None and recovery.get('quarantineRelativePath')=='files/recovery08/'+identity,'RECOVERY_FRESH_WORKSPACE_IDENTITY')
  need(after['state']['checkpoint'].get('phase')in('READY','RECOVERED_NOT_LIVE_ACK')and after['state']['checkpoint'].get('bindAvailable')is True,'RECOVERY_NEW_CHECKPOINT_REAL_READY_CAPACITY')
  workspace_projection(after,ready=True);w=after['state']['workspace'];need(w.get('draft')is None and w.get('draftSHA256')is None and w.get('reviews')==[],'RECOVERY_FRESH_EMPTY_WORKSPACE_NOT_OLD_AUTHORITY')
  verify_cold_original_backup(self.device.store.root,backup_receipt_ref)
  proof={'format':'aeris-explicit-persistence-quarantine','version':1,'originalBackupReceiptRef':backup_receipt_ref,'originalExportSHA256':original['exportSHA256'],'originalTargetSHA256':original['targetTableSHA256'],'newWorkspaceIdentity':identity,'beforeRevision':initial['revision'],'afterRevision':after['revision'],'sourceSHA256':after['sourceSHA256'],'PID':after['pid'],'processEpoch':after['processEpoch'],'viewEpoch':after['viewEpoch'],'prepareTapRef':prepare,'digestFieldTapRef':field,'digestInputRef':text,'commitTapRef':commit,'statusReceiptRef':self.bridge.last_receipt_ref,'oldCompletionClaim':False,'authorityRestored':False,'APOrBackendDispatched':False}
  ref=self.device.store.receipt('explicit-quarantine.json',proof);return {**proof,'receiptRef':ref}
