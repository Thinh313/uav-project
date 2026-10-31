"""Independent newest original state + separate DOM failure capture, no actors."""
from pathlib import Path
import os,sys,json,hashlib,base64,zlib,types
R=Path(__file__).resolve().parents[3];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(R/'planning/betasim-integrated01/runtime/source'),str(R)]
from aeris_runtime.public_ui_workload import PublicUIDriver
from aeris_runtime.metadata_budget import encoded
source=R/'planning/betasim-integrated01/runtime/source/aeris_runtime/public_ui_workload.py';H=lambda b:hashlib.sha256(b).hexdigest();pin=H(source.read_bytes());checks=[]
class Response:
 status=200
 def __init__(self,b):self.b=b
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,n):return self.b[:n]
def lab(raw):
 n=[2_000_000_000];saved=[];polls=[];device=types.SimpleNamespace(last_command_ref={'QA_CMD':1});probe=types.SimpleNamespace(source='a'*64,last_ref={'QA_NATIVE':1});owner=types.SimpleNamespace(digest='b'*64,persist_ui_failure=lambda q:saved.append(q)or{'QA_REF':1});case={'context':{'run':'qa-state','epoch':'e','boot':'b','operator':'A','generation':'g','profileId':'WORKBENCH_SIM_V1'},'device':device,'native':probe}
 def opener(req,**kw):polls.append(req.full_url);return Response(raw)
 d=PublicUIDriver(owner,case,lambda:None,clock=lambda:n[0],opener=opener);d.instance='observer';old=encoded({'ok':True,'observation':{'currentView':'olderDOM'}});d.last_ui_capture={'path':'/api/ui-observation?old','startedNs':1_000_000_000,'receivedNs':1_001_000_000,'raw':old,'responseComplete':True,'validated':True,'ageMs':10,'observation':{'currentView':'olderDOM'}};return d,n,saved,polls,old
def test(name,fn):
 try:fn();checks.append({'id':name,'pass':True})
 except BaseException as e:checks.append({'id':name,'pass':False,'error':type(e).__name__+':'+str(e)})
def original():
 raw=encoded({'ok':True,'result':{'error':'PREFLIGHT_WAIT','busy':False,'flight':{'preflight':{'ready':False,'missing':15},'live':{'failure':'source reason'}}}});d,n,out,polls,old=lab(raw);d.state();n[0]+=500_000_000;d.persist_failure(RuntimeError('PRIMARY'));q=out[0];state=q['lastState'];assert len(polls)==1 and state['originalResponseSHA256']==H(raw)and zlib.decompress(base64.b64decode(state['originalResponseZlibBase64']))==raw;assert state['originalStateResponseValidated']is True and state['ageAtFailureUpperRootMs']==500 and state['sourceStateSummary']['liveFailure']=='source reason';assert q['sourceCurrentView']=='olderDOM'and zlib.decompress(base64.b64decode(q['originalResponseZlibBase64']))==old and q['noAdditionalHTTPOrADBCalls']is True
test('newest-exact-state-separated-from-older-DOM-no-refresh',original)
def badjson():
 raw=b'newest malformed state';d,n,out,polls,old=lab(raw)
 try:d.state()
 except json.JSONDecodeError:pass
 else:raise AssertionError('INVALID_JSON_ACCEPTED')
 d.persist_failure(RuntimeError('JSON'));q=out[0]['lastState'];assert q['originalStateResponseValidated']is False and q['originalResponseSHA256']==H(raw)and zlib.decompress(base64.b64decode(q['originalResponseZlibBase64']))==raw and len(polls)==1
test('malformed-newest-state-retained-before-parse-not-replaced',badjson)
def nested():
 for live in [['invalid'],'invalid']:
  raw=encoded({'ok':True,'result':{'flight':{'live':live}}});d,n,out,polls,old=lab(raw);d.state();d.persist_failure(RuntimeError('SHAPE'));q=out[0]['lastState'];assert q['originalResponseSHA256']==H(raw)and q['sourceStateSummary']['liveFailure']is None and len(polls)==1
test('wrong-nested-live-type-does-not-lose-original-diagnostic',nested)
def prefixes():
 raw=os.urandom(131072);d,n,out,polls,old=lab(b'{}');ui=os.urandom(65536);d.last_ui_capture['raw']=ui;d.last_ui_capture['validated']=False;d.last_ui_capture['observation']=None;d.last_state_capture={'path':'/api/state?instance=observer','startedNs':n[0],'receivedNs':n[0]+1000,'raw':raw,'responseComplete':True,'validated':False,'result':None};d.persist_failure(RuntimeError('BIG'));q=out[0];assert len(encoded(q))<=32768
 for holder,original in[(q,ui),(q['lastState'],raw)]:assert holder['originalEncoding']=='BASE64_INCOMPLETE_ORIGINAL_PREFIX'and holder['retainedBytes']==8192 and base64.b64decode(holder['originalResponsePrefixBase64'])==original[:8192]and holder['originalResponseSHA256']==H(original)and holder['retainedCompleteOriginalResponse']is False
 assert not polls
test('joint-incompressible-prefixes-stay32KiB-and-explicitly-incomplete',prefixes)
report={'format':'aeris-independent-state-original-failure07','version':1,'status':'PASS_SOURCE_ORIGINAL_CACHE_FIXTURES_NOT_RUNTIME'if all(c['pass']for c in checks)else'FAIL_SOURCE_CONTRACT','sourceSHA256':pin,'sourceChanged':pin!=H(source.read_bytes()),'checks':checks,'actualHTTPADBAndroidAP':False}
n=1
while(out:=R/f'evidence/betasim-integrated01/qa/state-failure07-{n:02}.json').exists():n+=1
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':checks,'path':str(out)}))
