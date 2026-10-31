"""Pure AST execution of actual harness guards, with fake reads/screens/taps."""
import ast,json,hashlib,datetime,math,copy,types,base64
from pathlib import Path
source=Path('planning/clockvideo05/qa-ui.py');tree=ast.parse(source.read_text());wanted=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in ['target','mapping','native_point','workspace_document','phase_policy','dispatch']];ns={'base64':base64,'math':math,'json':json,'hashlib':hashlib,'time':types.SimpleNamespace(monotonic=lambda:0)};exec(compile(ast.Module(body=wanted,type_ignores=[]),'<actual-guards>','exec'),ns);rows=[]
def test(name,fn):
 try:fn();rows.append({'name':name,'status':'PASS'})
 except Exception as e:rows.append({'name':name,'status':'FAIL','error':str(e)})
def rejects(fn):
 try:fn()
 except AssertionError:return
 raise AssertionError('MISSING_REJECTION')
o={'documentId':'doc','viewport':{'width':1280,'height':720,'dpr':1},'tab':'payload','clientId':'client','clientEpoch':2,'clientInstance':'instance','run':'s-run','boot':'boot','configId':'config','modelSha256':'1'*64,'planSha256':'2'*64,'payloadSelection':{'stationId':'station','deviceId':'payload'},'phase':'AUTO','format':'clockvideo05-ui-observation-v1','foreground':True,'targets':[{'id':'field-gimbal','enabled':True,'visible':True,'fullyVisible':True,'unoccluded':True,'rect':{'x':10,'y':20,'width':100,'height':48}}]}
s={'flight':{'run':'s-run','positionAgeMs':10,'latestPosition':{'relativeHomeM':10},'authority':{},'live':{'stage':'AUTO','mode':'AUTO','armed':True},'request':{'boot':'boot'}},'client':{'id':'client','epoch':2,'instance':'instance'},'workspace':json.loads(Path('evidence/field02/clockvideo05/qa-actual-ws-contract01.json').read_text())['workspace'],'payloadLeaseObservation':{'observedAtHostMonoMs':100,'leases':[{'flightRun':'s-run','flightBoot':'boot','modelSha256':'1'*64,'planSha256':'2'*64,'clientId':'client','clientEpoch':2,'clientInstance':'instance','stationId':'station','payloadId':'payload','untilHostMonoMs':10100,'remainingMs':10000}]}}
def valid():ns['phase_policy']('DISARMED',o,'field-gimbal',s)
test('declaredDISARMEDtoAUTOgimbalrequiresfreshairborneexactlease',valid)
def negatives():
 for change in [{'positionAgeMs':1001},{'latestPosition':{'relativeHomeM':5}}]:
  z=copy.deepcopy(s);z['flight'].update(change);rejects(lambda:ns['phase_policy']('DISARMED',o,'field-gimbal',z))
 for k,v in [('armed',False),('mode','RTL')]:
  z=copy.deepcopy(s);z['flight']['live'][k]=v;rejects(lambda:ns['phase_policy']('DISARMED',o,'field-gimbal',z))
 z=copy.deepcopy(s);z['payloadLeaseObservation']['leases'][0]['remainingMs']=4999;rejects(lambda:ns['phase_policy']('DISARMED',o,'field-gimbal',z))
 rejects(lambda:ns['phase_policy']('OTHER',o,'field-gimbal',s))
test('badphaseheightfreshnessmodearmedandnear-expiredleaseblock',negatives)
def home():
 z=copy.deepcopy(s);z['flight']['live']['stage']='ARMED_HOME_REVIEW';z['flight']['autoGate']={'eligible':True,'effectiveRemainingMs':1801};a={**o,'phase':'ARMED_HOME_REVIEW'};ns['phase_policy']('DISARMED',a,'field-auto',z);z['flight']['autoGate']['effectiveRemainingMs']=1800;rejects(lambda:ns['phase_policy']('DISARMED',a,'field-auto',z))
test('explicitpostarmHomeprogressionpreservesstrict1800mswindow',home)
class Image:
 def read_bytes(self):return b'QA_FAKE_IMAGE'
 def __str__(self):return'QA_FAKE_IMAGE_PATH'
class FakePath:
 def __init__(self,p):self.p=p
 def read_bytes(self):return b'QA_FAKE_IMAGE'
 def read_text(self):return json.dumps({'image':'fake','imageSha256':hashlib.sha256(b'QA_FAKE_IMAGE').hexdigest(),'observed':{'observation':copy.deepcopy(o)},'nativeMapping':ns['mapping'](o['viewport'],[0,24,1280,744],[1280,800]),'nativeWindow':{'QA':'stablefake'}})
def reference_context():
 for k in ['run','boot','configId','modelSha256','planSha256','clientId','clientEpoch','clientInstance']:
  seen=copy.deepcopy(o);seen[k]='wrong';counts={'tap':0,'capture':0}
  ns.update(Path=FakePath,observation=lambda:{'observation':seen},q=types.SimpleNamespace(state=lambda:(_ for _ in()).throw(AssertionError('UNEXPECTED_STATE_GET')),adb=lambda *a:counts.update(tap=counts['tap']+1)))
  rejects(lambda:ns['dispatch']('01','fake','field-gimbal','name'));assert counts['tap']==0
 testdone=True
test('oldreferencewrongAPbootmodelplanconfigclientrejectedbeforetap',reference_context)
ns['png_size']=lambda path:[1280,800]
ns['ground_frame_signature']=lambda:{'QA':'stablefake'}
def screenshot_change():
 for key in ['boot','configId','modelSha256','planSha256']:
  old=copy.deepcopy(o);new=copy.deepcopy(o);new[key]='changed';calls=iter([{'observation':old},{'observation':new}]);counts={'tap':0};ns.update(Path=FakePath,observation=lambda:next(calls),q=types.SimpleNamespace(state=lambda:copy.deepcopy(s),capture=lambda*a:Image(),adb=lambda*a:counts.update(tap=counts['tap']+1)));rejects(lambda:ns['dispatch']('01','fake','field-gimbal','name'));assert counts['tap']==0
test('afterfreshscreenshotchangedbootconfigmodelplanrejectbeforetap',screenshot_change)
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_PURE_HARNESS_GUARDS'if all(x['status']=='PASS'for x in rows)else'FAIL','source':str(source),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rows':rows,'scope':'ActualPythonfunctionASTwithfakePath/state/screen/tap only; noimportsfromAndroidmodule/ADB/HTTP/process/UI. Doesnotproveactualpixelgeometry.'}
with Path(__import__('sys').argv[1]).open('x')as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r));assert r['status'].startswith('PASS')
