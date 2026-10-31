"""Independent new adversarial pure G3 controller/quota checks. No UI/process action."""
from pathlib import Path
import importlib.util,sys,json,hashlib,datetime,types,os
R=Path(__file__).resolve().parents[2];P=Path(__file__).parent

def load(name,file):
 s=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
m=load('g3_independent_ctl_negative','qa-root-controller.py');d=load('g3_independent_device_negative','qa-device-actions.py');r=load('g3_independent_runtime_negative','qa-runtime.py');rows=[]
class Clock:
 t=100.
 def __call__(self):return self.t
clock=Clock()
def ctl():
 clock.t=100.;c=m.Controller('04',boot_reader=lambda:'actual-injected-mock-boot',clock=clock);c.host_anchor=100.;c.host_process=types.SimpleNamespace(pid=999,poll=lambda:None);c.guard.anchor_emulator_before_launch('emulator-5582');return c

def rejects(fn):
 try:fn()
 except (AssertionError,ValueError,KeyError):return
 raise AssertionError('EXPECTED_FAIL_CLOSED')
def test(name,fn):
 try:fn();rows.append({'name':name,'status':'PASS'})
 except Exception as e:rows.append({'name':name,'status':'FAIL','error':str(e)})

def fifth():
 c=ctl()
 for i in range(4):c.guard.anchor_before_connect('input'+str(i))
 before=c.guard.snapshot();rejects(lambda:c.guard.anchor_before_connect('fifth'));assert c.guard.snapshot()==before

def duplicates():
 c=ctl();c.guard.anchor_before_connect('once');c.guard.note_connect_input_once('once');rejects(lambda:c.guard.note_connect_input_once('once'));rejects(lambda:c.guard.anchor_before_connect('once'));a={'op':'action','commandId':'same-command','rootApproved':True};c.approved(a);rejects(lambda:c.approved(a))
def missing():
 c=ctl();run='s'+'a'*20;rejects(lambda:c.reserve(run));c.guard.anchor_before_connect('once');rejects(lambda:c.guard.bind_observed_run('once',run));c.guard.note_connect_input_once('once');c.guard.bind_observed_run('once',run);assert c.reserve(run)['authorityGranted']is False
 # New controller does not inherit anchors or budgets from receipt dictionaries.
 fresh=ctl();rejects(lambda:fresh.reserve(run))
def deadlines():
 for value in [99.,float('nan'),float('inf'),416.]:
  c=ctl();c.guard.anchor_before_connect('once');c.guard.note_connect_input_once('once');c.guard.bind_observed_run('once','s'+'a'*20);clock.t=value;rejects(lambda:c.reserve('s'+'a'*20))
 c=ctl();c.guard.anchor_before_connect('once');c.guard.note_connect_input_once('once');c.guard.bind_observed_run('once','s'+'a'*20);c.boot_reader=lambda:'new-boot';rejects(lambda:c.reserve('s'+'a'*20))
def persistence():
 c=ctl();c.persistence_only=True
 for target in ['field-connect','field-arm','field-auto','field-cut','field-reboot']:
  rejects(lambda:c.action({'target':target,'commandId':'attempt-'+target}))
def quota():
 assert d.quota_decision({'journalChain':{'pickerPendingCount':13}},3)['remaining']==3
 for used,n in [(13,4),(16,1),(17,0)]:rejects(lambda:d.quota_decision({'journalChain':{'pickerPendingCount':used}},n))
def admission():
 good=[{'mono':i,'free':40*2**30}for i in range(31)];r.budget_decision(good)
 for bad in [good[:-1],[{**v,'mono':v['mono']*.5}for v in good],[{**v,'free':28*2**30}for v in good],[{**v,'free':40*2**30-(257*2**20 if i==30 else 0)}for i,v in enumerate(good)]]:rejects(lambda:r.budget_decision(bad))
 for history,t,free in [([],0,27*2**30),([(0,40*2**30)],1,29*2**30)]:
  try:r.trend_decision(history,t,free)
  except RuntimeError:pass
  else:raise AssertionError('DISK_GUARD_NOT_REFUSED')
for name,fn in [('fifth_connect_refused_without_anchor_mutation',fifth),('duplicate_command_and_input_fail_closed',duplicates),('missing_or_restarted_parent_anchor_refuses_ARM',missing),('time_loss_nonfinite_wrong_boot_or_expired_AP_refuses',deadlines),('persistence05_cannot_allocate_AP_or_ARM',persistence),('native13_used3_remain_no_reset',quota),('stable_admission_and_runtime_forecast_failures',admission)]:test(name,fn)
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_PURE_CONTROLLER_NEGATIVES'if all(x['status']=='PASS'for x in rows)else'FAIL','rows':rows,'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [P/'qa-root-controller.py',P/'qa-deadline-guard.py',P/'qa-device-actions.py',P/'qa-runtime.py']},'scope':'Independent actual pure methods with injected clock/boot/fake host PID only. No subprocess, sysctl, network, runtime, UI, AP allocation or binary exec. Fifth actual request allocation enforced separately by adapter test.'}
p=R/'evidence/beta06/generation03/qa-controller-negative04.json'
with p.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(rows),'failed':[x for x in rows if x['status']=='FAIL']}));assert report['status'].startswith('PASS')
