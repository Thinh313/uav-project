"""One fixed build, 3 polygon + 3 corridor. One attempt per case, stop on failure.
Every declared case appears in the receipt, including blocked NOT_RUN cases.
"""
import importlib.util,json,subprocess,sys,time,hashlib,os
from pathlib import Path
spec=importlib.util.spec_from_file_location('q',Path(__file__).with_name('android-journey.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
ownerPath=q.R/'.local/betavideo03/active/owner.json'
def owned_host():
 owner=json.loads(ownerPath.read_text());host=Path(owner['run'])/'host';assert host.is_relative_to(q.E/'launches'),'HOST_SCOPE';return owner,str(host)
owner,host=owned_host();hostPhases=[{'ownerId':owner['id'],'host':host}]
pinpath=q.E/'source-pins01.json';pinbytes=pinpath.read_bytes();pins=json.loads(pinbytes)
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify_fixed():
 assert pinpath.read_bytes()==pinbytes,'CAMPAIGN_PIN_FILE_DRIFT'
 for name,h in pins['files'].items():
  p=q.R/name
  assert p.is_file() and not p.is_symlink() and sha(p.read_bytes())==h,'CAMPAIGN_SOURCE_DRIFT:'+name
def rotate_after_polygon():
 oldOwner,oldHost=owned_host();oldObservation=q.obs();deadline=time.monotonic()+180
 request={'at':time.time(),'reason':'PLANNED_FIXED_BUILD_ROTATION_AFTER_3_POLYGON_FOR_BOUNDED_TRACE_AND_CLOCK_BUDGET_NOT_FAILED_CASE_RETRY','oldOwner':oldOwner,'oldHost':oldHost,'sourcePinsSha256':sha(pinbytes),'completedCases':cases[:3],'waitBoundSeconds':180,'authorityRestorationAllowed':False}
 with(q.E/'rotation-request01.json').open('x')as f:json.dump(request,f,indent=2);f.flush();os.fsync(f.fileno())
 q.log('PLANNED_ROTATION_REQUESTED',request)
 while time.monotonic()<deadline:
  verify_fixed()
  try:
   newOwner,newHost=owned_host()
   if newOwner['id']!=oldOwner['id']:
    observed=q.get('/api/ui-observation');v=observed.get('observation')
    if observed.get('ageMs')is not None and observed['ageMs']<2000 and v and v.get('platform')=='ANDROID'and v.get('foreground')is True and v.get('instance')!=oldObservation['instance']:
     state=q.state();assert state['flight']['run']is None and state['flight']['authority']is None,'ROTATION_MUST_NOT_RESTORE_FLIGHT';assert state['payloadAuthority']['current']['leaseCount']==0,'ROTATION_MUST_NOT_RESTORE_PAYLOAD'
     phase={'ownerId':newOwner['id'],'host':newHost,'previousOwnerId':oldOwner['id'],'freshAndroidInstance':v['instance'],'authorityRestored':False};hostPhases.append(phase)
     with(q.E/'rotation-observed01.json').open('x')as f:json.dump(phase,f,indent=2);f.flush();os.fsync(f.fileno())
     q.log('PLANNED_ROTATION_OBSERVED',phase);return
  except (FileNotFoundError,ConnectionError,TimeoutError,__import__('urllib.error').error.URLError):pass
  time.sleep(.5)
 raise RuntimeError('PLANNED_HOST_ROTATION_180S_NOT_COMPLETED')
cases=[{'kind':kind,'index':i,'status':'NOT_RUN','reason':'PRECEDING_CASE_OR_ADMISSION_NOT_COMPLETED'}for kind in ['polygon','corridor']for i in [1,2,3]]
started=time.time();error=None
# Lock is create-only and retained as evidence, never deleted to retry a campaign.
with(q.E/'final-campaign01.started.json').open('x')as f:
 json.dump({'at':started,'pid':os.getpid(),'host':host,'sourcePins':'source-pins01.json','sourcePinsSha256':sha(pinbytes),'declaredCases':cases},f,indent=2)
try:
 verify_fixed()
 for caseIndex,case in enumerate(cases):
  if caseIndex==3:rotate_after_polygon()
  currentOwner,host=owned_host()
  case.update(status='RUNNING',startedAt=time.time(),host=host,ownerId=currentOwner['id'])
  run=q.nominal(case['kind'],case['index']);case['run']=run
  target=q.E/('receiver-'+run+'.json')
  with target.open('x')as f:
   receiver=subprocess.run(['node','pilot/betavideo03/receiver.mjs',str(q.E/'history01'/(run+'.json'))],cwd=q.R,stdout=f,stderr=subprocess.STDOUT)
  assert owned_host()[0]['id']==currentOwner['id'],'OWNER_CHANGED_DURING_CASE'
  case['receiverExit']=receiver.returncode
  assert receiver.returncode==0,'COLD_RECEIVER_FAILED:'+run
  case['receiver']=json.loads(target.read_text())
  assert case['receiver'].get('traceCoverage',{}).get('status')=='PASS','FULL_STAGE_TRACE_COVERAGE_FAILED:'+run
  oracle=subprocess.run([sys.executable,'-B','planning/betavideo03/oracle-result.py',host,run],cwd=q.R,capture_output=True,text=True)
  with(q.E/('oracle-console-'+run+'.txt')).open('x')as f:f.write(oracle.stdout+oracle.stderr)
  case['oracleExit']=oracle.returncode
  assert oracle.returncode==0,'INDEPENDENT_VIDEO_ORACLE_FAILED:'+run
  case['videoOracle']=json.loads((q.E/('oracle-result-'+run+'.json')).read_text())
  verify_fixed()
  case.update(status='PASS',completedAt=time.time(),sourcePins='source-pins01.json',sourcePinsSha256=sha(pinbytes))
  q.log('FINAL_CASE_VERIFIED',case);print(json.dumps(case),flush=True)
except BaseException as e:
 error=repr(e)
 for case in cases:
  if case['status']=='RUNNING':case.update(status='FAIL',error=error,failedAt=time.time())
 q.log('CAMPAIGN_STOP_ON_FAILURE',{'error':error,'cases':cases})
finally:
 try:verify_fixed();integrity='PASS'
 except BaseException as e:integrity='FAIL';error=(error or '')+';FINAL_FIXED_SOURCE:'+repr(e)
 report={'results':cases,'status':'PASS'if all(c['status']=='PASS'for c in cases)and integrity=='PASS'else'NOT_READY',
  'completedCases':sum(c['status']=='PASS'for c in cases),'declaredCases':6,'fixedBuildIntegrity':integrity,
  'sourcePins':'source-pins01.json','sourcePinsSha256':sha(pinbytes),'noAutomaticRetry':True,'hostPhases':hostPhases,
  'startedAt':started,'finishedAt':time.time(),'error':error,'actualImages':0,
  'scope':'REPEATED_POLYGON_AND_CORRIDOR_SAME_DECLARED_CORPUS_NOT_HERA_OR_REAL_PAYLOAD'}
 with(q.E/'final-campaign01.json').open('x')as f:json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
 print(json.dumps({'campaignStatus':report['status'],'completedCases':report['completedCases'],'error':error}),flush=True)
if report['status']!='PASS':sys.exit(1)
