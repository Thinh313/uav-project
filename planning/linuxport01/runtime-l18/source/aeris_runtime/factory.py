"""Concrete product assembly, fixed immutable audit and no test-only PASS injection."""
from pathlib import Path
import copy,threading
from .candidate import load
from .identity import validate_native_selection
from .resources import OwnedResources
from .android import AndroidDevice
from .native import NativeBridge
from .audit.receiver import FixedReceiver
from .supervisor import MissionSupervisor
from .lifecycle import Context
from .campaign import Campaign
from .monitor import ResourceMonitor,host_power
from .launch import SimulationLauncher
class ProductSession:
 def __init__(self,supervisor,launcher,monitor,device):
  self.supervisor=supervisor;self.launcher=launcher;self.monitor=monitor;self.device=device
  from .operator import OperatorUI
  self.operator=OperatorUI(self);self.abort_lock=threading.RLock();self.abort_result=None;self.guard_closure=None
 def prepare(self,provider,*,survey=None,expected_draft_sha=None):
  try:return self.supervisor.prepare(self.launcher,provider,survey=survey,expected_draft_sha=expected_draft_sha)
  except BaseException as primary:
   self.abort(primary);raise
 def abort(self,primary):
  """One failure exit. A blocked proof retains owned resources and observers."""
  with self.abort_lock:
   if self.abort_result is not None:return self.abort_result
   self.supervisor.life.fail(primary);started=self.supervisor.now();result={'status':'BLOCKED_OWNERSHIP_RETAINED','primaryFailure':str(self.supervisor.life.failure)if self.supervisor.life.failure is not None else str(primary),'primaryFailureType':self.supervisor.life.failureType or type(primary).__name__,'startedHostNs':started,'flightAcceptance':False,'authorityRestored':False,'cleanup':None,'cleanupError':None,'guardsClosed':False}
   try:
    if self.supervisor.resources.closure is not None:
     result['cleanup']=self.supervisor.resources.completed_closure();result['status']='FAILED_AFTER_VERIFIED_DRAIN_REUSED_NOT_ACCEPTANCE'
    else:
     connected=self.supervisor.has_connected_lifetime()
     result['cleanup']=self.supervisor.cleanup_failed_connected()if connected else self.supervisor.cleanup_failed_preparation();result['status']='FAILED_CONNECTED_RESOURCES_DRAINED_NOT_ACCEPTANCE'if connected else'FAILED_PREOWNER_RESOURCES_DRAINED_NOT_ACCEPTANCE'
   except BaseException as cleanup:
    result['cleanupError']=type(cleanup).__name__+':'+str(cleanup);self.supervisor.life.note_failure_detail('PRODUCT_FAILURE_CLEANUP_BLOCKED',{'reason':result['cleanupError'][:1024],'APNotDeclaredGround':True,'ownedResourcesRetained':True})
   result['failureEventCommitRef']=copy.deepcopy(self.supervisor.life.failureEventCommitRef);result['failureAppendError']=self.supervisor.life.failureAppendError;result['unpublishedDurableEvents']=copy.deepcopy(self.supervisor.life.unpublishedDurableEvents)
   result['finishedHostNs']=self.supervisor.now();result['children']={name:{'pid':c.process.pid,'exit':c.process.poll(),'startedHostNs':c.started_ns}for name,c in self.supervisor.resources.children.items()}
   result['cleanupReceiptCommitRef']=self.supervisor.life.note_failure_detail('PRODUCT_FAILURE_CLEANUP_RECEIPT',dict(result));result['cleanupReceiptDurable']=result['cleanupReceiptCommitRef']is not None
   if result['status']in('FAILED_PREOWNER_RESOURCES_DRAINED_NOT_ACCEPTANCE','FAILED_CONNECTED_RESOURCES_DRAINED_NOT_ACCEPTANCE','FAILED_AFTER_VERIFIED_DRAIN_REUSED_NOT_ACCEPTANCE'):
    try:result['guardClosure']=self.close_guard();result['guardsClosed']=True
    except BaseException as cleanup:result['guardCloseError']=type(cleanup).__name__+':'+str(cleanup)
   self.abort_result=result;return result
 def observe(self):self.monitor.check();return self.supervisor.observe_native()
 def finalize(self):
  self.supervisor.await_ground()
  if self.supervisor.scenario=='nominal':
   current=self.supervisor.native.status(context=self.supervisor.context.value())
   if current['state'].get('native',{}).get('closed') is not True:self.operator.tap('control01-close')
  return self.supervisor.finalize_nominal()
 def restart_and_verify(self):
  def fresh(old):
   new_device=AndroidDevice(old.device.adb,old.device.serial,self.supervisor.root/'android-api-restart-01',now=old.device.now,budget=old.device.budget)
   old.device.transfer_io_broker_to(new_device);new_device.host_query=old.device.host_query
   new_bridge=NativeBridge(new_device,old.source,now=old.now,receipt_root=self.supervisor.root/'public-api-restart-01',apk_sha=old.apk_sha)
   # Publish the fresh holder before preparation so its original failed prefix
   # is retained and close_guard can close it even if Android restart fails.
   self.device=new_device;self.supervisor.native=new_bridge
   self.supervisor.restart_evidence['afterStoreRoot']=str(new_device.store.root)
   operation=new_device.restart_normal(old.apk_sha,old_pid=old.latest['pid'],deadline_ns=min(self.supervisor._deadline(),self.supervisor.now()+60_000_000_000))
   return new_bridge,operation
  result=self.supervisor.verify_restart(fresh)
  from .operator import OperatorUI
  self.operator=OperatorUI(self)
  return result
 def close_guard(self):
  with self.abort_lock:
   if self.guard_closure is not None:return self.guard_closure
   resources=self.supervisor.resources
   if resources.children:
    resources.completed_closure()
   return self._close_guard_after_drain()
 def _close_guard_after_drain(self):
  # Unknown ACK closure retains the existing watch/monitor ownership. A failed
  # receipt cannot discharge guards even after the AP drain itself completed.
  try:
   close=self.device.close_observer()
   if getattr(self.device,'observer',None)is not None and(type(close)is not dict or close.get('receipt',{}).get('captureComplete')is not True):raise RuntimeError('PRODUCT_ACK_CLOSE_INCOMPLETE_OR_UNDURABLE')
  except BaseException as primary:
   self.supervisor.life.note_failure_detail('PRODUCT_ACK_CLOSE_GUARD_RETAINED',{'reason':str(primary)[:512],'guardClosureClaimed':False});raise
  try:
   broker_close=self.device.stop_io_broker(deadline_ns=self.device.now()+5_000_000_000)
   if broker_close is not None and broker_close.get('receipt',{}).get('drainComplete')is not True:raise RuntimeError('PRODUCT_BROKER_CLOSE_DRAIN_UNPROVEN')
  except BaseException as primary:
   self.supervisor.life.note_failure_detail('PRODUCT_BROKER_CLOSE_GUARD_RETAINED',{'reason':str(primary)[:512],'guardClosureClaimed':False});raise
  errors=[];observation=None;monitor=None
  try:self.supervisor.close_watch()
  except BaseException as e:errors.append(e)
  try:observation=self.supervisor.life.stop_guard_observer()
  except BaseException as e:errors.append(e)
  if errors:
   for e in errors:self.supervisor.life.note_failure_detail('PRODUCT_GUARD_CLOSE_ERROR',{'reason':str(e)[:512],'monitorRetained':True})
   raise errors[0]
  try:monitor=self.monitor.close()
  except BaseException as primary:
   self.supervisor.life.note_failure_detail('PRODUCT_GUARD_CLOSE_ERROR',{'reason':str(primary)[:512],'guardClosureClaimed':False});raise
  self.guard_closure={**monitor,'lifecycleGuardObservation':observation};return self.guard_closure
 def __enter__(self):return self
 def __exit__(self,kind,value,trace):
  if kind is not None:self.abort(value);return False
  try:self.close_guard()
  except BaseException as primary:
   self.abort(primary);raise
  return False

def create_session(*,candidate_dir,candidate_sha,config,context,root,adb,serial,campaign_clock,candidate_attempt,container_image,planning,avd,avd_baseline,guardian_root):
 if type(config.get('maximumSeconds'))is not int or config['maximumSeconds']not in(180,760):raise ValueError('PIPELINE06_ACTUAL_PROFILE180_OR760_BEFORE_CASE_OR_ACTOR')
 from .launch import need_budget
 need_budget(config)
 from .entry import module_origin_receipt
 module_origin_receipt(candidate_dir)
 config=copy.deepcopy(config)
 root=Path(root).resolve();expected_root=Path(campaign_clock).resolve().parent/'sessions'/context['run']
 if root!=expected_root or Path(config['evidence']).resolve()!=root/'raw':raise ValueError('FIXED_PRODUCT_CASE_AND_RAW_ROOT')
 manifest=load(candidate_dir,candidate_sha);validate_native_selection(config,candidate_dir);c=Context(**context)
 # Evaluate full source-derived writer/ownership contract before case metadata,
 # lifecycle construction, background threads or any native/process dispatch.
 from .inventory import Inventory
 from .pipeline_contract import admit_or_refuse
 initial_inventory=Inventory(Path(campaign_clock).resolve().parent,planning,avd,avd_baseline)
 metadata=admit_or_refuse(root/'pipeline-contract',initial_inventory,owner_root=Path(campaign_clock).resolve().parent)
 campaign=Campaign(campaign_clock,budget=metadata);campaign.case(candidate_attempt,candidate_sha,context)
 if any(config.get(k)!=context[k] for k in ('run','epoch','boot')):raise ValueError('PRODUCT_CONFIG_CONTEXT')
 from .inventory import Inventory
 from .host_health import GuardianClient
 from .commands import HostCommands
 device=AndroidDevice(adb,serial,root/'android-api',budget=metadata);native=NativeBridge(device,manifest['native']['sourceSHA256'],receipt_root=root/'public-api-receipts',apk_sha=manifest['native']['APK_SHA256']);resources=OwnedResources(candidate_dir,candidate_sha,root/'processes',budget=metadata);inventory=Inventory(Path(campaign_clock).resolve().parent,planning,avd,avd_baseline,native=native);guardian=GuardianClient(guardian_root,manifest['sourceSHA256']['aeris_runtime/emulator.py'],budget=metadata);query=HostCommands(root/'host-queries',campaign,budget=metadata);monitor=ResourceMonitor(root/'resources',config['maximumSeconds'],campaign,inventory=inventory,power=host_power,guardian=guardian,budget=metadata)
 device.host_query=query
 receiver=FixedReceiver(candidate_dir,candidate_sha,config,device,health_monitor=monitor);supervisor=MissionSupervisor(c,manifest['native']['sourceSHA256'],root,native,resources,admission=monitor.start,verify_evidence=receiver,campaign=campaign,scenario=config['controlScenario'],check_live=monitor.check,budget=metadata);launcher=SimulationLauncher(config,root/'simulation',image=container_image,query=query,check_live=monitor.check,budget=metadata)
 return ProductSession(supervisor,launcher,monitor,device)
