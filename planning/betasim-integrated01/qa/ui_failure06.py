"""Independent cached-original UI failure and causality methods. No actors."""
from pathlib import Path
import os,sys,json,hashlib,types,base64,zlib,shutil,ast,re
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(R/'planning/betasim-integrated01/runtime/source'),str(R)]
import aeris_runtime.public_ui_workload as U
import aeris_runtime.product_runtime as P
from aeris_runtime.metadata_budget import MetadataBudget,encoded
files=[Path(U.__file__),Path(P.__file__),R/'planning/betasim-integrated01/runtime/source/aeris_runtime/metadata_budget.py',R/'planning/betasim-integrated01/runtime/scenario-ui06.py'];H=lambda b:hashlib.sha256(b).hexdigest();pins={str(p.relative_to(R)):H(p.read_bytes())for p in files};checks=[];LAB=R/'planning/betasim-integrated01/qa/.ui-failure-fixture06';assert not LAB.exists()
class Owner:
 digest='a'*64
 def __init__(self):self.rows=[];self.writes=[]
 def persist_ui_failure(self,q):self.rows.append(q);return{'sha256':H(encoded(q)),'bytes':len(encoded(q)),'QA_MEMORY_ONLY':True}
 def write(self,*a,**kw):self.writes.append((a,kw))
class Clock:
 def __init__(self,n=3_000_000_000):self.n=n
 def __call__(self):return self.n
class Device:
 def __init__(self):self.calls=[];self.last_command_ref={'QA_COMMAND':1}
 def command(self,*a,**kw):self.calls.append((a,kw));return b''
def driver():
 clock=Clock();owner=Owner();device=Device();probe=types.SimpleNamespace(source='b'*64,last_ref={'QA_NATIVE':1});case={'context':{'run':'qa-ui-failure','epoch':'e','boot':'b','operator':'A','generation':'g','profileId':'WORKBENCH_SIM_V1'},'device':device,'native':probe};d=U.PublicUIDriver(owner,case,lambda:None,clock=clock,opener=lambda *a,**kw:(_ for _ in()).throw(AssertionError('NO_HTTP_ALLOWED')));d.geometry={'x':0,'y':24,'width':1280,'height':716};d.geometry_epoch='c'*32;d.geometry_view_epoch='view';return d,clock,owner,device
obs={'instance':'ui','foreground':True,'platform':'ANDROID','currentView':'plan','noticeText':'source notice','modal':False,'workbenchBusy':False,'controls':{'datum':{'x':10,'y':20,'w':30,'h':40,'enabled':True,'visible':False,'checked':False}},'scrollRegions':{'modal':None},'nativeViewBinding':{'instance':'view','processEpoch':'c'*32,'sourceSHA256':'b'*64}}
def capture(d,raw=None):
 o=json.loads(json.dumps(obs));raw=encoded({'ok':True,'observation':o,'observationAgeMs':35})if raw is None else raw;d.last_ui_capture={'path':'/api/ui-observation?nativeViewEpoch=view','startedNs':2_000_000_000,'receivedNs':2_005_000_000,'raw':raw,'responseComplete':True,'validated':True,'ageMs':35,'observation':o};d.active_target='datum';d.target_started_ns=1_900_000_000;return raw
def test(n,fn):
 try:fn();checks.append({'id':n,'pass':True})
 except BaseException as e:checks.append({'id':n,'pass':False,'error':type(e).__name__+':'+str(e)})
def deny(fn,code):
 try:fn()
 except BaseException as e:assert code in str(e),(code,str(e));return
 raise AssertionError('UNEXPECTED_ACCEPT:'+code)
def exact():
 d,c,o,dev=driver();raw=capture(d);r=d.persist_failure(TimeoutError('TARGET'));q=o.rows[0];assert q['originalResponseSHA256']==H(raw)and zlib.decompress(base64.b64decode(q['originalResponseZlibBase64']))==raw;assert q['ageUpperMsAtFailure']==1035 and q['sourceCurrentView']=='plan'and q['sourceNoticeText']=='source notice'and q['sourceModalOpen']is False and q['sourceWorkbenchBusy']is False;assert not dev.calls and d.observer_requests==0 and q['retainedCompleteOriginalResponse']is True;assert d.persist_failure(RuntimeError('SECOND'))==r and len(o.rows)==1
test('original-exactbytes-ageupper-modal-target-no-poll-and-no-repeat',exact)
def latest_badjson():
 d,c,o,dev=driver();capture(d);raw=b'NEWEST_BAD_JSON';
 class Response:
  status=200
  def __enter__(self):return self
  def __exit__(self,*a):pass
  def read(self,n):return raw
 d.opener=lambda *a,**kw:Response()
 try:d.get('/api/ui-observation?newest=true')
 except json.JSONDecodeError:pass
 else:raise AssertionError('BADJSON_ACCEPTED')
 d.persist_failure(RuntimeError('JSON'));q=o.rows[0];assert q['originalResponseSHA256']==H(raw)and q['originalObservationValidated']is False and q['sourceCurrentView']is None and zlib.decompress(base64.b64decode(q['originalResponseZlibBase64']))==raw
 test_nothing=None
test('newest-raw-before-parse-retained-not-older-valid-observation',latest_badjson)
def prefix():
 d,c,o,dev=driver();raw=os.urandom(65536);capture(d,raw);d.persist_failure(RuntimeError('oversize'));q=o.rows[0];assert q['originalEncoding']=='BASE64_INCOMPLETE_ORIGINAL_PREFIX'and q['retainedCompleteOriginalResponse']is False and q['retainedBytes']==16384 and q['omittedCapturedBytes']==49152 and base64.b64decode(q['originalResponsePrefixBase64'])==raw[:16384]and q['originalResponseSHA256']==H(raw)and q['retainedSHA256']==H(raw[:16384])and len(encoded(q))<=32768
test('incompressible-original-prefix-explicitly-incomplete-under32KiB',prefix)
def no_poll():
 d,c,o,dev=driver();d.persist_failure(RuntimeError('beforefirstpoll'));q=o.rows[0];assert q['originalResponseCapturedBytes']==0 and q['originalHTTPResponseComplete']is False and q['retainedCompleteOriginalResponse']is False and q['sourceCurrentView']is None and d.observer_requests==0 and not dev.calls
test('no-original-poll-remains-unknown-no-fabricated-observation',no_poll)
def eio():
 d,c,o,dev=driver();capture(d);calls=[]
 def fail(q):calls.append(q);raise OSError('QA_EIO')
 o.persist_ui_failure=fail;deny(lambda:d.persist_failure(RuntimeError('PRIMARY')),'QA_EIO');assert d.persist_failure(RuntimeError('SECOND'))is None and len(calls)==1 and not dev.calls
test('storage-EIO-no-second-attempt-or-ref-or-new-poll',eio)
def closure_order():
 order=[];owner=Owner();owner.root=Path('/QA_MEMORY');owner.case={'context':{},'writer':types.SimpleNamespace(begin_close=lambda:order.append('REVOKE'),close=lambda:order.append('WRITER')),'uiDriver':types.SimpleNamespace(persist_failure=lambda e:order.append('UI_ORIGINAL')),'companion':None,'resources':object(),'native':types.SimpleNamespace(close=lambda:order.append('NATIVE')),'monitor':types.SimpleNamespace(close=lambda:order.append('MONITOR')),'device':types.SimpleNamespace(last_command_ref=None,root=Path('/QA_MEMORY/android-api')),'APStarted':False};owner.close_interval=lambda:order.append('INTERVAL');owner.close_guardian=lambda **kw:order.append('GUARDIAN');owner.budget=types.SimpleNamespace(failure=lambda *a,**kw:None)
 with patch.object(P,'dispose_resources',side_effect=lambda *a,**kw:order.append('DISPOSE')):result=P.WorkbenchRuntime.fail_case(owner,RuntimeError('PRIMARY'))
 assert order==['REVOKE','UI_ORIGINAL','INTERVAL','WRITER','DISPOSE','NATIVE','MONITOR','GUARDIAN']and result['primaryFailure']=='PRIMARY'and result['normalCompletedClosureClaimed']is False
test('failure-revokes-then-captures-before-any-owned-stop',closure_order)
def exact_cap():
 LAB.mkdir();b=MetadataBudget(LAB/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();b.write('closure',LAB/'reports/ui-failure-final.json',b'x'*32768,closing=True);deny(lambda:b.write('closure',LAB/'reports/ui-failure-final.json',b'x'*32769,closing=True),'SOURCE_OWNER_TERMINAL_OR_TRACE_EXACT_BOUND');deny(lambda:b.write('closure',LAB/'reports/not-approved.json',b'x',closing=True),'METADATA_OWNER_PATH')
test('source-closure-exact32KiB-path-cap-no-new-owner',exact_cap)
def barriers():
 d,c,o,dev=driver();d.last_action_finished_ns=1_000_000_000;assert not d.after_action(1_100_000_000,100)and not d.after_action(1_100_000_000,100.000001)and d.after_action(1_100_000_001,100);d.complete_action('TAP');assert d.last_action_finished_ns==c.n and d.last_action_ref==dev.last_command_ref
test('original-server-age-ceil-barrier-strictly-after-last-command-EOF',barriers)
def stale_scroll():
 d,c,o,dev=driver();d.last_action_finished_ns=1_000_000_000;hidden={**obs,'viewport':{'w':1280,'h':716},'scrollRegions':{'panel':{'x':10,'y':10,'w':400,'h':400}}};start=c.n;d.observation=lambda:(hidden,start,start+1_000_000,b'',1000)
 with patch.object(U.time,'sleep',side_effect=lambda s:setattr(c,'n',c.n+int(s*1e9))):deny(lambda:d.target('datum',seconds=.1),'PUBLIC_UI_TARGET_NOT_READY')
 assert not dev.calls
test('post-action-but-stale-hidden-control-never-dispatches-scroll',stale_scroll)
def semantic_predicates():
 source=files[-1].read_text();tree=ast.parse(source);predicates={call.keywords[0].value.value if call.keywords else'':call.args[0]for call in ast.walk(tree)if isinstance(call,ast.Call)and isinstance(call.func,ast.Attribute)and call.func.attr=='wait_ui'and call.args and isinstance(call.args[0],ast.Lambda)}
 for label,lam in predicates.items():
  fn=eval(compile(ast.Expression(lam),'actual-scenario-predicate','eval'),{'re':re});base={'currentView':'plan','modal':False,'workbenchBusy':False,'planSha256':None if label=='FIXTURE_MODEL_AND_MODAL'else'a'*64};assert fn(base)
  for field,value in [('currentView','review'),('modal',True),('workbenchBusy',True),('planSha256','prior'if label=='COMPILE_COMPLETED'else'a'*64)]:assert not fn({**base,field:value})
 assert set(predicates)=={'FIXTURE_MODEL_AND_MODAL','COMPILE_COMPLETED'}
test('actual-scenario-waits-known-view-closed-modal-notbusy-null-or64hex-plan',semantic_predicates)
try:pass
finally:
 if LAB.exists():shutil.rmtree(LAB)
report={'format':'aeris-independent-cached-ui-failure-and-causality06','version':1,'status':'PASS_SOURCE_METHOD_FIXTURES_NOT_ANDROID_OR_BROWSER'if all(x['pass']for x in checks)else'FAIL_SOURCE_CONTRACT','sourcePins':pins,'checks':checks,'actualHTTPADBAndroidAP':False,'runtimeBudgetWrites':'OWN_QA_MOCK_ONLY','scratchRemoved':str(LAB),'sourceChanged':any(H((R/p).read_bytes())!=h for p,h in pins.items())}
n=1
while(out:=R/f'evidence/betasim-integrated01/qa/ui-failure06-{n:02}.json').exists():n+=1
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':checks,'path':str(out)}))
