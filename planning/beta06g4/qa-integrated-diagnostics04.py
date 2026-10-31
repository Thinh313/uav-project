"""Independent current HTTP diagnostics,45minute reserve and one ground recovery fakes."""
from pathlib import Path
import json,hashlib,datetime,importlib.util,sys,os,types,math
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];P=Path(__file__).parent;E=R/'evidence/beta06/generation04'
def load(name,file):
 s=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
u=load('independent_g4_http_diag','qa-ui.py');ctl=load('independent_g4_deadline_diag','qa-root-controller.py');g=load('independent_g4_ground_diag','qa-ground-soak.py');rows=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def test(name,fn):
 try:fn();rows.append({'name':name,'status':'PASS'})
 except BaseException as e:rows.append({'name':name,'status':'FAIL','error':str(e)})
class Response:
 status=200
 def __init__(self,b):self.b=b;self.reads=[]
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,n):self.reads.append(n);return self.b[:n]
def request(b):
 r=Response(b)
 with patch.object(u.urllib.request,'urlopen',return_value=r)as net:
  try:value=u.observation();error=None
  except BaseException as e:value=None;error=e
  assert net.call_count==1 and r.reads==[65537]
 return value,error

def stale():
 raw=b'{"ok":true,"ageMs":1200.001,"observation":{"seq":99},"csrf":"CANARY_PRIVATE","nested":{"token":"CANARY_PRIVATE"}}';v,e=request(raw);assert v is None and str(e)=='STALE_OBSERVATION';d=e.raw_observation_diagnostic;assert d['rawResponseAgeMs']==1200.001 and d['responsePrefixSha256']==sha(raw)and d['responsePrefixBytes']==len(raw)and d['freshnessBoundMsUnchanged']==1200 and 'CANARY_PRIVATE'not in json.dumps(d);assert d['httpStatus']==200

def exactboundary():
 v,e=request(b'{"ok":true,"ageMs":1200,"observation":{"seq":99}}');assert e is None and v['ageMs']==1200

def invalidages():
 for age in ['NaN','Infinity','-1','true','null']:
  raw=('{"ok":true,"ageMs":'+age+',"observation":{"seq":99}}').encode();v,e=request(raw);assert v is None;json.dumps(e.raw_observation_diagnostic,allow_nan=False)

def malformed():
 raw=b'{"token":"CANARY_PRIVATE",';v,e=request(raw);assert v is None;d=e.raw_observation_diagnostic;assert d['responsePrefixSha256']==sha(raw)and 'CANARY_PRIVATE'not in json.dumps(d)and d['bodyKind']=='UNPARSEABLE_RESPONSE_PREFIX_SHA_AND_COUNT_ONLY'
def overflow():
 raw=b'{"token":"CANARY_PRIVATE",'+b'x'*70000;v,e=request(raw);assert v is None and str(e)=='OBSERVATION_HTTP_BOUND64KIB';d=e.raw_observation_diagnostic;assert d['responseOverflow']is True and d['responsePrefixBytes']==65536 and d['responsePrefixSha256']==sha(raw[:65536])and 'CANARY_PRIVATE'not in json.dumps(d)

def failurecollector():
 raw=b'{"ok":true,"ageMs":1401.25,"observation":{"seq":99}}';_,err=request(raw);calls=[]
 def observe():calls.append('one-observation');raise err
 fake=types.SimpleNamespace(observation=observe)
 with patch.object(g,'journal_rows',return_value=(b'PREFIX_MOCK',[{'seq':1}])):
  try:g.collect('qa-integrated-stale-failure04','MOCK-NO-HTTP',clock=lambda:100.,pause=lambda _:None,ui=fake)
  except AssertionError:pass
  else:raise AssertionError('STALE_NOT_REFUSED')
 p=E/'qa-integrated-stale-failure04-ground-soak.json';r=json.loads(p.read_text());assert r['status']=='REFUSED_GROUND_ADMISSION_NO_AP'and not r['samples']and r['failureObservation']['rawResponseAgeMs']==1401.25 and calls==['one-observation']

def make():return ctl.Controller('06',boot_reader=lambda:'G4-MOCK-BOOT',clock=lambda:100.)
def recovery():
 c=make();attempts=[]
 def collect(*args,**kw):attempts.append(args[0]);raise AssertionError('MOCK_STALE_OBSERVATION')
 def command(op,ident,**kw):return c.command({'op':op,'rootApproved':True,'commandId':ident,**kw})
 def refuses(fn):
  try:fn()
  except AssertionError:return
  raise AssertionError('EXPECTED_REFUSAL')
 with patch.object(ctl,'module',return_value=types.SimpleNamespace(collect=collect)):
  refuses(lambda:command('ground-soak','first',clockJournal='MOCK'))
  assert c.ground_failure is not None and not c.campaign_failed and len(attempts)==1
  refuses(lambda:command('ground-soak','forbidden-auto',clockJournal='MOCK'));assert len(attempts)==1
  refuses(lambda:command('authorize-ground-recovery','missing-diagnosis',rootInspectedRawGroundFailure=True))
  command('authorize-ground-recovery','explicit-once',rootInspectedRawGroundFailure=True,diagnosis='Retained mock stale response and observed recovery',explicitRecovery='One read-only fresh interval, no input or threshold change')
  refuses(lambda:command('authorize-ground-recovery','duplicate-auth',rootInspectedRawGroundFailure=True,diagnosis='x',explicitRecovery='x'))
  refuses(lambda:command('ground-soak','second-fails',clockJournal='MOCK'));assert len(attempts)==2 and c.ground_recovery_used and c.campaign_failed
  refuses(lambda:command('ground-soak','third-blocked',clockJournal='MOCK'));assert len(attempts)==2
 c=make();c.connect_count=1;c.ground_failure={'MOCK':True}
 try:c.command({'op':'authorize-ground-recovery','commandId':'after-AP','rootApproved':True,'rootInspectedRawGroundFailure':True,'diagnosis':'x','explicitRecovery':'x'})
 except AssertionError:pass
 else:raise AssertionError('RECOVERY_AFTER_AP_ALLOWED')

def reserves():
 class Clock:
  t=100.
  def __call__(self):return self.t
 clock=Clock();c=ctl.Controller('06',boot_reader=lambda:'BOOT',clock=clock);c.host_anchor=100.;c.host_process=types.SimpleNamespace(pid=999,poll=lambda:None);c.guard.anchor_emulator_before_launch('emulator-5582');clock.t=2560.;c.guard.anchor_before_connect('late');c.guard.note_connect_input_once('late');run='s'+'a'*20;c.guard.bind_observed_run('late',run);x=c.reserve(run);assert x['hostRemainingConservativeS']==240 and x['emulatorRemainingConservativeS']==240 and x['apRemainingConservativeS']==540
 clock.t=2560.001
 try:c.reserve(run)
 except(AssertionError,ValueError):pass
 else:raise AssertionError('45MIN_RESERVE_BORROWED')
 clock.t=2710.;assert c.closure_reserve()==90
 clock.t+=.001
 try:c.closure_reserve()
 except AssertionError:pass
 else:raise AssertionError('90S_CLOSURE_RESERVE_BORROWED')
 plan=ctl.plan();assert plan['attempts']==['06','07']and plan['hostBudgetSecondsAcrossBothBoots']==2700 and plan['emulatorSeconds']==2700 and plan['apBudgetSeconds']==540 and plan['newConnectIntentsBoot06']==4 and plan['connectIntentsBoot07']==0

for name,fn in [('stale_actualboundedresponse_age_SHA_redaction_no_reinput',stale),('unchanged1200_exactboundary_accepts',exactboundary),('nonfinite_bool_negative_absent_age_refused_strictJSONdiagnostic',invalidages),('malformedquotedsecretbody_SHAcountonly',malformed),('64KiBoverflow_prefix_SHA_redacted_noextrarequest',overflow),('groundcollector_keeps_exactfailedHTTPdiagnostic_no_extraHTTP',failurecollector),('only_one_explicit_groundrecovery_before_AP_then_stop',recovery),('original45min_host_emulator240_andclosure90_reserves_noreset',reserves)]:test(name,fn)
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_G4_DIAGNOSTICS_TIMING_GROUNDRECOVERY_MOCK_ONLY'if all(x['status']=='PASS'for x in rows)else'FAIL','classification':'SOURCE_MOCK_NO_ACTUAL_RUNTIME_OR_NETWORK','rows':rows,'sources':{str(p.relative_to(R)):sha(p.read_bytes())for p in [P/'qa-ui.py',P/'qa-ground-soak.py',P/'qa-root-controller.py',P/'qa-deadline-guard.py']},'scope':'Actual observation/redaction/ground/controller methods with fake HTTP response/local clock/collector only. No urlopen network, UI/ADB/AP/Docker/listener or G4allocation. The failed-ground fixture is explicitly mock; actual75s/renewals still required.'}
out=E/'qa-integrated-diagnostics04.json'
with out.open('x')as f:json.dump(report,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(rows),'failed':[x for x in rows if x['status']=='FAIL']}));assert report['status'].startswith('PASS')
