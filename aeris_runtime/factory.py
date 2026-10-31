"""Concrete product assembly, fixed immutable audit and no test-only PASS injection."""
from pathlib import Path
import copy
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
  self.operator=OperatorUI(self)
 def prepare(self,provider,*,survey=None,expected_draft_sha=None):
  try:return self.supervisor.prepare(self.launcher,provider,survey=survey,expected_draft_sha=expected_draft_sha)
  except BaseException:
   try:self.close_guard()
   except BaseException as cleanup:self.supervisor.life.note_failure_detail('PREPARE_GUARD_CLOSE_FAILED',{'reason':str(cleanup)[:512]})
   raise
 def observe(self):self.monitor.check();return self.supervisor.observe_native()
 def finalize(self):
  self.supervisor.await_ground()
  if self.supervisor.scenario=='nominal':
   current=self.supervisor.native.status(context=self.supervisor.context.value())
   if current['state'].get('native',{}).get('closed') is not True:self.operator.tap('control01-close')
  return self.supervisor.finalize_nominal()
 def restart_and_verify(self):return self.supervisor.verify_restart(lambda:self.device.restart_normal(self.supervisor.native.apk_sha,deadline_ns=min(self.supervisor._deadline(),self.supervisor.now()+60_000_000_000)))
 def close_guard(self):
  errors=[];observation=None;monitor=None
  try:self.supervisor.close_watch()
  except BaseException as e:errors.append(e)
  try:observation=self.supervisor.life.stop_guard_observer()
  except BaseException as e:errors.append(e)
  try:monitor=self.monitor.close()
  except BaseException as e:errors.append(e)
  if errors:
   for e in errors:self.supervisor.life.note_failure_detail('PRODUCT_GUARD_CLOSE_ERROR',{'reason':str(e)[:512]})
   raise errors[0]
  return {**monitor,'lifecycleGuardObservation':observation}
 def __enter__(self):return self
 def __exit__(self,kind,value,trace):
  if kind is not None:self.supervisor.life.fail(value)
  try:self.close_guard()
  except BaseException as cleanup:
   self.supervisor.life.note_failure_detail('FINAL_GUARD_CLOSE_FAILED',{'reason':str(cleanup)[:512]})
   if kind is None:raise
  return False

def create_session(*,candidate_dir,candidate_sha,config,context,root,adb,serial,campaign_clock,candidate_attempt,container_image,planning,avd,avd_baseline,guardian_root):
 from .launch import need_budget
 need_budget(config)
 from .entry import module_origin_receipt
 module_origin_receipt(candidate_dir)
 config=copy.deepcopy(config)
 root=Path(root).resolve();expected_root=Path(campaign_clock).resolve().parent/'sessions'/context['run']
 if root!=expected_root or Path(config['evidence']).resolve()!=root/'raw':raise ValueError('FIXED_PRODUCT_CASE_AND_RAW_ROOT')
 manifest=load(candidate_dir,candidate_sha);validate_native_selection(config,candidate_dir);c=Context(**context);campaign=Campaign(campaign_clock);campaign.case(candidate_attempt,candidate_sha,context)
 if any(config.get(k)!=context[k] for k in ('run','epoch','boot')):raise ValueError('PRODUCT_CONFIG_CONTEXT')
 from .inventory import Inventory
 from .emulator import observe_guardian
 from .commands import HostCommands
 device=AndroidDevice(adb,serial,root/'android-api');native=NativeBridge(device,manifest['native']['sourceSHA256'],receipt_root=root/'public-api-receipts',apk_sha=manifest['native']['APK_SHA256']);resources=OwnedResources(candidate_dir,candidate_sha,root/'processes');inventory=Inventory(Path(campaign_clock).resolve().parent,planning,avd,avd_baseline,native=native);guardian=lambda:observe_guardian(guardian_root,manifest['sourceSHA256']['aeris_runtime/emulator.py']);query=HostCommands(root/'host-queries',campaign);monitor=ResourceMonitor(root/'resources',config['maximumSeconds'],campaign,inventory=inventory,power=host_power,guardian=guardian)
 receiver=FixedReceiver(candidate_dir,candidate_sha,config,device);supervisor=MissionSupervisor(c,manifest['native']['sourceSHA256'],root,native,resources,admission=monitor.start,verify_evidence=receiver,campaign=campaign,scenario=config['controlScenario'],check_live=monitor.check);launcher=SimulationLauncher(config,root/'simulation',image=container_image,query=query,check_live=monitor.check)
 return ProductSession(supervisor,launcher,monitor,device)
