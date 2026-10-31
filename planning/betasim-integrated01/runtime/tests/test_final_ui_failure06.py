"""Final original UI poll retention, no HTTP/ADB/Android actors."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import base64,hashlib,json,os,shutil,sys,zlib
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.public_ui_workload import PublicUIDriver
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.metadata_budget import MetadataBudget,encoded
from aeris_runtime.candidate import load
LAB=R/'evidence/betasim-integrated01/runtime/.uifailure06';C={'run':'mock','epoch':'a'*32,'boot':'b'*32,'generation':'c'*32,'operator':'ROOT-LAB','profileId':'WORKBENCH_SIM_V1'}
class Response:
 status=200
 def __init__(self,raw):self.raw=raw
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,n):return self.raw[:n]
class Opener:
 def __init__(self,rows):self.rows=list(rows);self.calls=[]
 def __call__(self,req,**kw):self.calls.append(req.full_url);return Response(self.rows.pop(0))
def deny(fn,phrase):
 try:fn()
 except(ValueError,RuntimeError):return
 raise AssertionError('not denied '+phrase)
def body(label,*,noise=''):
 return encoded({'ok':True,'observationAgeMs':12,'observation':{'instance':'view-one','foreground':True,'platform':'ANDROID','nativeViewBinding':{'instance':'native-view','processEpoch':'f'*32,'sourceSHA256':'d'*64},'viewport':{'w':1280,'h':800},'currentView':label,'noticeText':label,'controls':{'datum':{'visible':False,'enabled':True,'checked':False,'x':20,'y':30,'w':40,'h':50}},'noise':noise}})
def fixture(name,rows):
 root=LAB/name;root.mkdir();b=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();o=WorkbenchRuntime.__new__(WorkbenchRuntime);o.root=root;o.budget=b;o.digest='a'*64;d=SimpleNamespace(root=root/'sessions/mock/android-api',last_command_ref={'fixture':'last-adb-original-ref'});probe=SimpleNamespace(source='d'*64,last_ref={'fixture':'last-native-original-ref'});case={'context':C,'device':d,'native':probe};now=[1_000_000_000];opener=Opener(rows);driver=PublicUIDriver(o,case,lambda:None,clock=lambda:now[0],opener=opener);driver.geometry={'x':0,'y':0,'width':1280,'height':800};driver.geometry_epoch='f'*32;driver.geometry_view_epoch='native-view';driver.active_target='datum';driver.target_started_ns=now[0];return o,driver,opener,now

def main():
 assert not LAB.exists();LAB.mkdir(parents=True);groups=[]
 try:
  old=body('BEFORE_FIXTURE');new=body('AFTER_FIXTURE_BLOCKED');o,ui,opener,now=fixture('current',[old,new]);ui.observation();now[0]+=100_000_000;ui.observation();now[0]+=600_000_000
  with o.budget._locked():
   state=o.budget._state();state['remaining']['external_task']=0;o.budget._save(state)
  calls=len(opener.calls);ref=ui.persist_failure(RuntimeError('PUBLIC_UI_TARGET_NOT_READY:datum'));raw=(o.root/ref['path']).read_bytes();q=json.loads(raw);assert len(opener.calls)==calls==2 and zlib.decompress(base64.b64decode(q['originalResponseZlibBase64']))==new and q['originalResponseSHA256']==hashlib.sha256(new).hexdigest()and q['ageUpperMsAtFailure']==612 and q['originalObservationValidated']is True and q['retainedCompleteOriginalResponse']is True and q['target']=='datum'and q['sourceCurrentView']=='AFTER_FIXTURE_BLOCKED'and q['sourceNoticeText']=='AFTER_FIXTURE_BLOCKED'and q['sourceTargetPresent']is True;assert ui.persist_failure(RuntimeError('later'))==ref and (o.root/ref['path']).read_bytes()==raw;groups.append('latest-afterfixture-originalbytes-not-beforefixture-retained-with-age-and-no-newcall-or-retry-even-external-task-exhausted')
  o,ui,opener,now=fixture('incompressible',[body('NOISY',noise=base64.b64encode(os.urandom(40000)).decode())]);ui.observation();original=ui.last_ui_capture['raw'];ref=ui.persist_failure(ValueError('fail'));q=json.loads((o.root/ref['path']).read_bytes());prefix=base64.b64decode(q['originalResponsePrefixBase64']);assert q['originalEncoding']=='BASE64_INCOMPLETE_ORIGINAL_PREFIX'and prefix==original[:16384]and q['retainedCompleteOriginalResponse']is False and q['omittedCapturedBytes']==len(original)-16384 and len(encoded(q))<=32768;groups.append('incompressible-original-response-explicit-incomplete-prefix-32KiB-no-fake-completeness')
  o,ui,opener,now=fixture('bad-json',[b'{bad original response']);deny(ui.observation,'invalidjson');ref=ui.persist_failure(ValueError('parse'));q=json.loads((o.root/ref['path']).read_bytes());assert zlib.decompress(base64.b64decode(q['originalResponseZlibBase64']))==b'{bad original response' and q['originalObservationValidated']is False and q['observationAgeMsAtResponse']is None;groups.append('capture-before-JSON-validation-keeps-actual-bad-body-no-fabricated-observation')
  o,ui,opener,now=fixture('empty',[]);ref=ui.persist_failure(ValueError('beforefirstpoll'));q=json.loads((o.root/ref['path']).read_bytes());assert not opener.calls and q['retainedCompleteOriginalResponse']is False and q['originalObservationValidated']is False;groups.append('no-poll-explicitunknown-zero-network')
  o,ui,opener,now=fixture('eio',[new]);ui.observation()
  with patch.object(o.budget,'write',side_effect=OSError('EIO')):
   try:ui.persist_failure(ValueError('primary'))
   except OSError:pass
   else:raise AssertionError('not EIO')
  assert ui.failure_capture_attempted and ui.failure_capture_ref is None and ui.persist_failure(ValueError('repeat'))is None;assert len(opener.calls)==1;groups.append('failed-diagnostic-write-no-retry-no-newcalls-originalfailure-remains')
  o,ui,opener,now=fixture('ordering',[new]);ui.observation();steps=[];real=ui.persist_failure
  def record(error):steps.append('UI_CACHE_PRESERVED');return real(error)
  ui.persist_failure=record;o.closed=False;o.close_guardian=lambda **kw:steps.append('GUARDIAN_STOP');o.close_interval=lambda:steps.append('INTERVAL_CLOSE');o.case={**ui.case,'uiDriver':ui,'APStarted':True,'admissionRevoked':False,'phase':'ROOT_AP_READY','companion':None,'writer':SimpleNamespace(begin_close=lambda:steps.append('INGRESS_REVOKED'),close=lambda:steps.append('WRITER_CLOSED')),'resources':SimpleNamespace(),'monitor':SimpleNamespace(close=lambda:steps.append('MONITOR_CLOSED'))};o.case['native']=SimpleNamespace(close=lambda:steps.append('NATIVE_CLOSED'))
  with patch('aeris_runtime.product_runtime.dispose_resources',side_effect=lambda *a,**k:steps.append('PHYSICAL_DISPOSAL')):o.fail_case(ValueError('primary-target-failure'))
  assert steps[0:2]==['INGRESS_REVOKED','UI_CACHE_PRESERVED']and steps.index('UI_CACHE_PRESERVED')<steps.index('PHYSICAL_DISPOSAL');terminal=json.loads((o.root/'reports/owner-terminal.json').read_bytes());assert terminal['finalOriginalUIRef']['sha256']==o.ui_failure_ref['sha256']and terminal['primaryFailure']=='primary-target-failure'and terminal['flightAcceptance']is False;groups.append('ingress-revoked-then-original-cache-fsynced-before-actor-disposal-terminal-binds-SHA-primary-preserved')
  deny(lambda:o.budget.write('closure',o.root/'reports/ui-failure-final.json',b'x'*32769,closing=True),'oversize');groups.append('exact32KiB-sourceclosure-bound-rejects-oversize-no-reserveincrease')
  for digest in('924d3c6e658f1a89243827f578c9f7d25d1cab79439585a5df843c2a1412b6b4','4ce68ada8ca0abb57d4fd11e6b5907f620623442ef7ce701a3fa4f76551737c8','549c9877a9eb5eda413b43ea2ac29e7377942e03cfcf9621df38622e9d293c89'):load(R/'evidence/betasim-integrated01/candidates'/digest,digest)
  groups.append('three-old-candidates-transitive-source-readonly-load-PASS')
  assert (T/'root-owner-ui06.py').read_bytes().replace(b'product-companion-ui06.mjs',b'product-companion.mjs')==(T/'root-owner-ready02.py').read_bytes();assert (T/'product-companion-ui06.mjs').read_bytes().replace(b'product/server-csrf03.mjs',b'product/server.mjs')==(T/'product-companion.mjs').read_bytes();groups.append('new-versioned-owner-companion-only-selected-serverpath-delta-oldexternalentries-preserved')
  report={'format':'aeris-final-ui-failure-original-cache-mock','status':'PASS_CACHE_SOURCE_MOCK_NOT_ACTUAL_ANDROID_UI','groups':groups,'actualActors':False,'oldR03Rewritten':False,'extraHTTPOrADBCallsDuringFailure':0,'scratchRemoved':str(LAB.relative_to(R))}
 finally:shutil.rmtree(LAB)
 p=R/'evidence/betasim-integrated01/runtime/final-ui-failure-mock06-final03.json';assert not p.exists();p.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
