"""Deterministic deadline unit boundaries, no runtime actions or old evidence writes."""
from pathlib import Path
import importlib.util,sys,json
spec=importlib.util.spec_from_file_location('deadline05',Path(__file__).with_name('qa-deadline-guard.py'));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);cases=[];RUN='s'+'a'*20

def setup(connect=100):
    t=[0.0];g=m.DeadlineGuard(host_boot_id='host-boot-test',clock=lambda:t[0]);g.anchor_emulator_before_launch('emulator-test');t[0]=connect;g.anchor_before_connect('connect-test');t[0]+=1;g.note_connect_input_once('connect-test');t[0]+=1;g.bind_observed_run('connect-test',RUN);return g,t

def arm(g):return g.before_arm(run=RUN,emulator_id='emulator-test',current_host_boot_id='host-boot-test')
def bad(name,fn):
    try:fn();raise RuntimeError('MUST_REJECT_'+name)
    except m.DeadlineGuardError:cases.append(name)
g,t=setup();t[0]=415;r=arm(g);assert r['apRemainingConservativeS']==225;cases.append('AP_exact225_boundary_pass');t[0]=415.000001;bad('AP_below225_refused',lambda:arm(g))
g,t=setup(800);t[0]=960;r=arm(g);assert r['emulatorRemainingConservativeS']==240;cases.append('emulator_exact240_boundary_pass');t[0]=960.000001;bad('emulator_below240_refused',lambda:arm(g))
g,t=setup();t[0]=200;assert arm(g)['apRemainingConservativeS']==440;cases.append('AP_budget_starts_before_connect_admission_not_completion');bad('wrong_run_anchor',lambda:g.before_arm(run='s'+'b'*20,emulator_id='emulator-test',current_host_boot_id='host-boot-test'));bad('wrong_emulator_anchor',lambda:g.before_arm(run=RUN,emulator_id='other',current_host_boot_id='host-boot-test'));bad('wrong_host_boot',lambda:g.before_arm(run=RUN,emulator_id='emulator-test',current_host_boot_id='other'));bad('duplicate_connect_input',lambda:g.note_connect_input_once('connect-test'));bad('reset_emulator_deadline_forbidden',lambda:g.anchor_emulator_before_launch('new'));bad('rebind_wrong_run_forbidden',lambda:g.bind_observed_run('connect-test','s'+'b'*20))
t[0]=50;bad('future_anchor_or_clock_rollback',lambda:arm(g));t[0]=640;bad('expired_AP',lambda:arm(g));t[0]=1201;bad('expired_campaign',lambda:arm(g))
for value in[float('nan'),float('inf'),-1,True]:
    g=m.DeadlineGuard(host_boot_id='host-boot-test',clock=lambda:value);bad('invalid_clock_'+repr(value),lambda:g.anchor_emulator_before_launch('emulator-test'))
g,t=setup();t[0]=float('nan');bad('NaN_before_arm',lambda:arm(g));t[0]=float('inf');bad('infinite_before_arm',lambda:arm(g));t[0]=200;bad('nonstring_wrong_run',lambda:g.before_arm(run=[],emulator_id='emulator-test',current_host_boot_id='host-boot-test'))
g=m.DeadlineGuard(host_boot_id='host-boot-test',clock=lambda:0);bad('missing_all_anchors',lambda:arm(g));g.anchor_emulator_before_launch('emulator-test');bad('missing_connect_anchor',lambda:arm(g));bad('input_without_preinput_anchor',lambda:g.note_connect_input_once('absent'));g.anchor_before_connect('pending');bad('bind_before_input_refused',lambda:g.bind_observed_run('pending',RUN));bad('missing_boot_id',lambda:m.DeadlineGuard(host_boot_id=''))
r={'status':'PASS_MOCK_ONLY_NOT_USED_FOR_ENDED_RUNS','checks':len(cases),'cases':cases,'constants':{'APBudgetS':540,'emulatorBudgetS':1200,'minimumAPRemainingS':225,'minimumEmulatorRemainingS':240},'reserveIsEngineeringNotCertifiedDuration':True,'runtimeStarted':False,'adbCalls':0,'newConnectInputs':0,'noNodeOrUTCClockMix':True};print(json.dumps(r,indent=2))
