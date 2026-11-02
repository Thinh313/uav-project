"""Finite disarmed Android navigation probe, never a flight/media workload.

The60s cold-init observation bound does not alter any original flight freshness,
health,authority orcase lifetime. Timeout preserves a failure, never readiness.
"""
from aeris_runtime.public_ui_workload import PublicUIDriver,need
import re
NAVIGATION_WAIT_SECONDS=60
NAVIGATION_PHASE='DISARMED_READ_ONLY_NAVIGATION_READINESS'
DIAGNOSTIC_STATUS='DISARMED_ANDROID_NAVIGATION_OBSERVED_READY_NOT_FLIGHT_ACCEPTANCE'

def navigation_ready(state):
 flight=state.get('flight')or{};live=flight.get('live')or{};navigation=flight.get('navigationReadiness')or{}
 return live.get('armed')is False and navigation.get('phase')==NAVIGATION_PHASE and navigation.get('ready')is True

def preflight_ready(state):
 flight=state.get('flight')or{};live=flight.get('live')or{};preflight=flight.get('preflight')or{}
 return live.get('armed')is False and preflight.get('ready')is True

def run(owner,case,check):
 need(case.get('plannedSeconds')==180,'NAVIGATION_PROBE_EXACT180S_CASE')
 ui=PublicUIDriver(owner,case,check);case['uiDriver']=ui
 ui.bind_geometry();ui.observation();ui.tap('workspace');ui.tap('sitl-fixture')
 ui.wait_ui(lambda o:o.get('currentView')=='plan'and o.get('modal')is False and o.get('workbenchBusy')is False and o.get('planSha256')is None,description='FIXTURE_MODEL_AND_MODAL')
 ui.checked('datum');ui.tap('compile')
 ui.wait_ui(lambda o:o.get('currentView')=='plan'and o.get('modal')is False and o.get('workbenchBusy')is False and type(o.get('planSha256'))is str and re.fullmatch('[a-f0-9]{64}',o['planSha256'])is not None,description='COMPILE_COMPLETED')
 ui.tap('workspace');saved=ui.save_workspace();ui.tap('close-modal');ui.tap('next-preflight');ui.checked('consent');ui.tap('approve');ui.tap('b-activate');ui.checked('b-home');ui.tap('b-connect')
 ui.wait(lambda s:bool(s['flight']['run']),seconds=15,description='CONNECTED')
 ui.event('DISARMED_NAVIGATION_PROBE_BEGIN',{'coldInitializationObservationSeconds':NAVIGATION_WAIT_SECONDS,'allOriginalGuardsUnchanged':True,'flightCommandsPermitted':False,'manualIntervention':False})
 observed=ui.wait(navigation_ready,seconds=NAVIGATION_WAIT_SECONDS,poll_seconds=.5,description=NAVIGATION_PHASE)
 need(navigation_ready(observed),'NAVIGATION_OBSERVATION_MUST_STILL_BE_DISARMED')
 # Originalpreflight is requested onlyafter genuinely fresh navigationready.
 ui.tap('b-preflight');checked=ui.wait(preflight_ready,seconds=10,description='TYPED_PREFLIGHT_DISARMED')
 need(preflight_ready(checked),'ORIGINAL_PREFLIGHT_MUST_STILL_BE_DISARMED')
 result={'status':DIAGNOSTIC_STATUS,'nativeUI':True,'manualIntervention':False,'navigationReadiness':checked['flight'].get('navigationReadiness'),'preflight':checked['flight'].get('preflight'),'savedPlanSHA256':saved.get('planSHA256'),'originalHealthAndNavigationGuardsApplied':True,'flightAcceptance':False,'recordingAccepted':False,'ARMOrManualOrUploadOrVideoRequested':False,'physicalHeraCalibration':False,'requiresOriginalExceptionalPhysicalDisposal':True}
 ui.event('DISARMED_NAVIGATION_PROBE_OBSERVED_READY',result)
 return result
