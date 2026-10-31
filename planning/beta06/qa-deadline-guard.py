"""Future-controller pre-arm engineering reserve, pure/no runtime actions.

Integration MUST create one guard before the emulator launch, call
anchor_emulator_before_launch(), and anchor_before_connect() BEFORE each one
visible connect input. After that input, call note_connect_input_once(), then
bind_observed_run() using the actual observed run. The same guard/host boot must
survive until before_arm(). Missing state after controller restart fails closed.

No JSON/Node/UTC anchor import exists. Python time.monotonic is sampled here;
clock injection is for deterministic mocks/trusted Python test clocks only.
This module grants no flight authority, launches nothing, and was NOT used for
the ended CLOCKVIDEO05 runs; this isolated BETA06 copy uses the new authorized30min budget. 225/240s are engineering reserves, not certified
flight duration or a guarantee that a mission will finish.
"""
from dataclasses import dataclass,replace
import math,re,time

AP_BUDGET_S=540.0
EMULATOR_BUDGET_S=1800.0
MIN_AP_REMAINING_S=225.0
MIN_EMULATOR_REMAINING_S=240.0
CLOCK_BASIS='PYTHON_TIME_MONOTONIC_SAME_HOST_BOOT'

class DeadlineGuardError(ValueError):pass

def require(value,reason):
    if not value:raise DeadlineGuardError(reason)

def finite_time(value):
    require(isinstance(value,(int,float))and not isinstance(value,bool)and math.isfinite(value)and value>=0,'FINITE_NONNEGATIVE_PYTHON_MONOTONIC_REQUIRED')
    return float(value)

@dataclass(frozen=True)
class ConnectAnchor:
    intent_id:str
    before_input_s:float
    input_observed_s:float|None=None
    bound_s:float|None=None
    run:str|None=None

class DeadlineGuard:
    def __init__(self,*,host_boot_id,clock=time.monotonic):
        require(isinstance(host_boot_id,str)and 1<=len(host_boot_id)<=128,'TRUSTED_HOST_BOOT_ID_REQUIRED')
        self._boot=host_boot_id;self._clock=clock;self._emulator=None;self._emulator_id=None;self._intents={};self._runs={}
    def _now(self):return finite_time(self._clock())
    def anchor_emulator_before_launch(self,emulator_id):
        require(self._emulator is None,'EMULATOR_ANCHOR_ALREADY_CAPTURED_NO_RESET')
        require(isinstance(emulator_id,str)and 1<=len(emulator_id)<=128,'OWNED_EMULATOR_ID_REQUIRED')
        self._emulator=self._now();self._emulator_id=emulator_id
        return self.snapshot()
    def anchor_before_connect(self,intent_id):
        require(self._emulator is not None,'PRELAUNCH_EMULATOR_ANCHOR_MISSING')
        require(isinstance(intent_id,str)and 1<=len(intent_id)<=128,'CONNECT_INTENT_ID_REQUIRED')
        require(intent_id not in self._intents,'CONNECT_INTENT_ALREADY_ANCHORED')
        require(len(self._intents)<2,'TWO_CONNECT_ANCHORS_MAX_NOT_RUNTIME_AUTHORIZATION')
        now=self._now();require(now>=self._emulator,'FUTURE_OR_WRONG_CLOCK_EMULATOR_ANCHOR')
        self._intents[intent_id]=ConnectAnchor(intent_id,now)
        return self.snapshot()
    def note_connect_input_once(self,intent_id):
        require(intent_id in self._intents,'BEFORE_INPUT_CONNECT_ANCHOR_MISSING')
        a=self._intents[intent_id];require(a.input_observed_s is None,'SECOND_CONNECT_INPUT_FORBIDDEN')
        now=self._now();require(now>=a.before_input_s,'FUTURE_OR_WRONG_CLOCK_CONNECT_ANCHOR')
        self._intents[intent_id]=replace(a,input_observed_s=now)
        return self.snapshot()
    def bind_observed_run(self,intent_id,run):
        require(intent_id in self._intents,'BEFORE_INPUT_CONNECT_ANCHOR_MISSING')
        a=self._intents[intent_id];require(a.input_observed_s is not None,'CONNECT_INPUT_NOT_OBSERVED')
        require(a.run is None and run not in self._runs,'RUN_ANCHOR_ALREADY_BOUND')
        require(isinstance(run,str)and re.fullmatch(r's[a-f0-9]{20}',run),'ACTUAL_SITL_RUN_ID_REQUIRED')
        now=self._now();require(now>=a.input_observed_s,'FUTURE_OR_WRONG_CLOCK_INPUT_ANCHOR')
        self._intents[intent_id]=replace(a,run=run,bound_s=now);self._runs[run]=intent_id
        return self.snapshot()
    def before_arm(self,*,run,emulator_id,current_host_boot_id):
        require(self._emulator is not None,'PRELAUNCH_EMULATOR_ANCHOR_MISSING')
        require(current_host_boot_id==self._boot,'HOST_BOOT_ID_MISMATCH_NO_CLOCK_IMPORT')
        require(emulator_id==self._emulator_id,'OWNED_EMULATOR_ANCHOR_MISMATCH')
        require(isinstance(run,str)and re.fullmatch(r's[a-f0-9]{20}',run),'ACTUAL_SITL_RUN_ID_REQUIRED')
        require(run in self._runs,'EXACT_RUN_CONNECT_ANCHOR_MISSING')
        a=self._intents[self._runs[run]];require(a.run==run and a.input_observed_s is not None and a.bound_s is not None,'EXACT_RUN_CONNECT_ANCHOR_MISSING')
        now=self._now();ordered=[self._emulator,a.before_input_s,a.input_observed_s,a.bound_s,now]
        [finite_time(v)for v in ordered];require(all(x<=y for x,y in zip(ordered,ordered[1:])),'FUTURE_EXPIRED_OR_WRONG_CLOCK_ANCHOR_ORDER')
        ap=AP_BUDGET_S-(now-a.before_input_s);emu=EMULATOR_BUDGET_S-(now-self._emulator)
        require(ap>=MIN_AP_REMAINING_S,'AP_REMAINING_BELOW225S_NO_ARM')
        require(emu>=MIN_EMULATOR_REMAINING_S,'EMULATOR_REMAINING_BELOW240S_NO_ARM')
        return {'status':'ENGINEERING_RESERVE_AVAILABLE_NOT_FLIGHT_AUTHORITY','clockBasis':CLOCK_BASIS,'hostBootId':self._boot,'emulatorId':self._emulator_id,'run':run,'connectIntentId':a.intent_id,'observedPythonMonoS':now,'emulatorBeforeLaunchPythonMonoS':self._emulator,'connectBeforeInputPythonMonoS':a.before_input_s,'connectInputObservedPythonMonoS':a.input_observed_s,'runBoundPythonMonoS':a.bound_s,'apRemainingConservativeS':ap,'emulatorRemainingConservativeS':emu,'minimumApReserveS':MIN_AP_REMAINING_S,'minimumEmulatorReserveS':MIN_EMULATOR_REMAINING_S,'reserveIsEngineeringNotCertifiedDuration':True,'authorityGranted':False,'runtimeActionPerformed':False}
    def snapshot(self):
        return {'clockBasis':CLOCK_BASIS,'hostBootId':self._boot,'emulatorId':self._emulator_id,'emulatorBeforeLaunchPythonMonoS':self._emulator,'connectAnchors':[{'intentId':a.intent_id,'beforeInputPythonMonoS':a.before_input_s,'inputObservedPythonMonoS':a.input_observed_s,'boundPythonMonoS':a.bound_s,'run':a.run}for a in self._intents.values()],'authorityGranted':False,'restoreFromJsonSupported':False}
