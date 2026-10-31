"""Independent exceptional-owner orchestration test. Physical resource helpers
are replaced with recording stubs, never process/signal/ADB/Docker actors."""
from pathlib import Path
import hashlib,json,os,sys,time
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
sys.path[:0]=[str(HERE.parent/'runtime/source'),str(REPO)]
import aeris_runtime.product_runtime as mod
source=Path(mod.__file__);pin=hashlib.sha256(source.read_bytes()).hexdigest();checks=[];calls=[]
class Writer:
 def begin_close(self):calls.append('writer-revoke')
 def close(self):calls.append('writer-close');return {'closed':True,'mock':True}
class Native:
 def close(self):calls.append('native-close');raise IOError('INJECTED_NATIVE_EOF_MISSING')
class Monitor:
 def close(self):calls.append('monitor-close');return {'closed':True,'neverStarted':True,'mock':True}
class Budget:
 def failure(self,primary,detail=None):calls.append('failure-retained');self.primary=str(primary);self.detail=detail
class Process:
 pid=424242;args=['INJECTED_NOT_PROCESS'];
class Companion:
 process=Process();started=123
 def wait(self,deadline):calls.append('companion-EOF');return {'mock':True,'closed':True}
owner=mod.WorkbenchRuntime.__new__(mod.WorkbenchRuntime);owner.failure=None;owner.budget=Budget();owner.case={'writer':Writer(),'native':Native(),'monitor':Monitor(),'resources':object(),'companion':Companion(),'admissionRevoked':False,'phase':'CREATED'}
owner.close_guardian=lambda failed=False:calls.append('guardian-exceptional')or{'mock':True,'exceptional':failed}
previous_stop,previous_dispose=mod.stop_owned,mod.dispose_resources
def stop(child,deadline_ns):
 assert owner.case['admissionRevoked'] and 'writer-revoke'in calls
 calls.append('producer-stop');return {'mock':True,'closed':True}
def dispose(resources,**kwargs):
 assert owner.case['admissionRevoked'] and kwargs['admission_revoked']is True
 assert kwargs['primary_failure']=='INJECTED_SOURCE_FAILURE' and 'writer-close'in calls
 calls.append('simulator-dispose');return {'mock':True,'physicallyClosed':True,'groundProven':False}
try:
 mod.stop_owned=stop;mod.dispose_resources=dispose
 result=owner.fail_case('INJECTED_SOURCE_FAILURE')
 checks.append({'id':'source-failure-revokes-before-producer-disposal-no-flight-command','pass':calls.index('writer-revoke')<calls.index('producer-stop')<calls.index('writer-close')<calls.index('simulator-dispose'),'calls':calls})
 checks.append({'id':'observer-secondary-failure-does-not-skip-monitor-guardian-or-rewrite-primary','pass':result['primaryFailure']=='INJECTED_SOURCE_FAILURE'and len(result['secondaryErrors'])==1 and result['secondaryErrors'][0]['step']=='native-observer-close'and'monitor-close'in calls and'guardian-exceptional'in calls and result['APGroundProven']is False and result['flightAcceptance']is False and result['normalCompletedClosureClaimed']is False,'result':result})
finally:mod.stop_owned=previous_stop;mod.dispose_resources=previous_dispose
probe=mod.WorkbenchRuntime.__new__(mod.WorkbenchRuntime);probe.parent=os.getppid()+1000000;probe.owner_deadline=time.monotonic_ns()+10**9;probe.campaign=None
try:probe.check_deadline();error=None
except RuntimeError as e:error=str(e)
checks.append({'id':'changed-original-parent-revokes-admission','pass':error=='PRODUCT_RUNTIME_ROOT_PARENT_DIED_REVOKE_ADMISSION','error':error})
out=REPO/'evidence/betasim-integrated01/qa';n=1
while(out/f'runtime-failure-{n:02}.json').exists():n+=1
p=out/f'runtime-failure-{n:02}.json';report={'format':'aeris-independent-owner-failure-orchestration','version':1,'status':'PASS_ORCHESTRATION_STUB_NOT_PHYSICAL_DISPOSAL'if all(x['pass']for x in checks)else'FAIL_SOURCE_CONTRACT','sourceSHA256':pin,'sourceChanged':pin!=hashlib.sha256(source.read_bytes()).hexdigest(),'checks':checks,'physicalProcessesOrAP':False,'resourceHelpers':'INJECTED_RECORDING_STUBS'};p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'groups':len(checks),'path':str(p)}))
