"""Genuine public Android review gestures; no flight/payload/private JS calls."""
from aeris_runtime.public_ui_workload import PublicUIDriver,need
import re,time

def wait_closed(ui,check):
 end=time.monotonic_ns()+8_000_000_000
 while time.monotonic_ns()<end:
  check();snapshot=ui.native(True);inp=snapshot['input']
  need(inp['failed']is False and inp['configured']is False and inp['pending']is False,'UNUSED_PRODUCER_NO_INPUT_OR_UNKNOWN')
  if inp['closed']is True and inp.get('workerTerminated')is True and inp['journal']['closed']is True and inp['journal']['durablyDrained']is True:
   need(inp['sequence']==0 and inp['journal']['sequence']==0,'NO_INPUT_HISTORY_OR_FLIGHT_CREDIT');return snapshot
  time.sleep(.2)
 raise TimeoutError('NATIVE17_ORIGINAL_REVIEW_CLOSE8S')

def first(owner,case,check):
 ui=PublicUIDriver(owner,case,check);case['uiDriver']=ui;ui.bind_geometry();ui.observation()
 ui.tap('workspace');ui.tap('sitl-fixture')
 ui.wait_ui(lambda o:o.get('currentView')=='plan'and o.get('modal')is False and o.get('workbenchBusy')is False and o.get('planSha256')is None,description='NATIVE17_FRESH_FIXTURE')
 ui.checked('datum');ui.tap('compile')
 ui.wait_ui(lambda o:o.get('currentView')=='plan'and o.get('modal')is False and o.get('workbenchBusy')is False and type(o.get('planSha256'))is str and re.fullmatch('[a-f0-9]{64}',o['planSha256'])is not None,description='NATIVE17_PUBLIC_COMPILE')
 ui.tap('workspace');before=ui.save_workspace();ui.tap('close-modal');ui.tap('nav-review');snapshot=wait_closed(ui,check)
 state=ui.state();need(state['flight'].get('run')is None and state['flight'].get('authority')is None and state.get('authorityRestored')is False,'NATIVE_ONLY_NO_FLIGHT_OR_RESTORED_RIGHTS')
 value={'savedWorkspace':{'head':before['head'],'observation':{'workspaceSaveReceipt':before['observation']['workspaceSaveReceipt']}},'workspaceHead':before['head'],'planSHA256':before['planSHA256'],'processEpoch':snapshot['processEpoch'],'pid':snapshot['pid'],'keyId':snapshot['input']['producerKeyId'],'journalGeneration':snapshot['input']['journal']['generation'],'originalStatusRef':case['native'].last_ref,'sourceClosed':True,'unusedRecords':0,'flightAcceptance':False}
 case['firstNative17']=value;owner.write('native17-first-public-review.json',value);return value

def second(owner,case,check):
 ui=case['uiDriver'];ui.geometry=None;ui.last_native=None;ui.next_native=0;ui.bind_geometry();ui.observation();ui.tap('workspace');restored=ui.workspace_saved();ui.tap('close-modal')
 before=case['firstNative17'];need(restored['head']==before['workspaceHead']and restored['planSHA256']==before['planSHA256']and restored['observation'].get('consent')is False,'EXACT_PERSISTENCE_NO_CONSENT_RESTORE')
 state=ui.state();need(state['flight'].get('run')is None and state['flight'].get('authority')is None and state['client'].get('active')is not True and state.get('authorityRestored')is False,'NO_OPERATOR_OR_FLIGHT_RESTORE')
 ui.tap('nav-review');snapshot=wait_closed(ui,check);need(snapshot['pid']!=before['pid']and snapshot['processEpoch']!=before['processEpoch']and snapshot['input']['producerKeyId']!=before['keyId'],'GENUINE_NEW_ANDROID_PROCESS_EPOCH_KEY')
 value={'status':'PUBLIC_NATIVE_UNUSED_RESTART_PERSISTENCE_OBSERVED_NOT_FLIGHT','first':before,'second':{'pid':snapshot['pid'],'processEpoch':snapshot['processEpoch'],'keyId':snapshot['input']['producerKeyId'],'journalGeneration':snapshot['input']['journal']['generation'],'originalStatusRef':case['native'].last_ref},'workspaceHead':restored['head'],'planSHA256':restored['planSHA256'],'authorityRestored':False,'signedInputPayloads':0,'physicalHIDAttested':False,'flightAcceptance':False}
 owner.write('native17-public-restart.json',value);return value
