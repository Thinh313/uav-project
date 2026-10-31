"""One fixed build, 3 polygon + 3 corridor. One attempt per case, stop on failure.
Every declared case appears in the receipt, including blocked NOT_RUN cases.
"""
import importlib.util,json,subprocess,sys,time,hashlib,os
from pathlib import Path
spec=importlib.util.spec_from_file_location('q',Path(__file__).with_name('android-journey.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
owner=json.loads((q.R/'.local/betastability02/active/owner.json').read_text());host=str(Path(owner['run'])/'host')
pinpath=q.E/'source-pins05.json';pinbytes=pinpath.read_bytes();pins=json.loads(pinbytes)
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify_fixed():
 assert pinpath.read_bytes()==pinbytes,'CAMPAIGN_PIN_FILE_DRIFT'
 for name,h in pins['files'].items():
  p=q.R/name
  assert p.is_file() and not p.is_symlink() and sha(p.read_bytes())==h,'CAMPAIGN_SOURCE_DRIFT:'+name
cases=[{'kind':kind,'index':i,'status':'NOT_RUN','reason':'PRECEDING_CASE_OR_ADMISSION_NOT_COMPLETED'}for kind in ['polygon','corridor']for i in [1,2,3]]
started=time.time();error=None
# Lock is create-only and retained as evidence, never deleted to retry a campaign.
with(q.E/'final-campaign01.started.json').open('x')as f:
 json.dump({'at':started,'pid':os.getpid(),'host':host,'sourcePins':'source-pins05.json','sourcePinsSha256':sha(pinbytes),'declaredCases':cases},f,indent=2)
try:
 verify_fixed()
 for case in cases:
  case.update(status='RUNNING',startedAt=time.time())
  run=q.nominal(case['kind'],case['index']);case['run']=run
  target=q.E/('receiver-'+run+'.json')
  with target.open('x')as f:
   receiver=subprocess.run(['node','pilot/betastability02/receiver.mjs',str(q.E/'history01'/(run+'.json'))],cwd=q.R,stdout=f,stderr=subprocess.STDOUT)
  case['receiverExit']=receiver.returncode
  assert receiver.returncode==0,'COLD_RECEIVER_FAILED:'+run
  case['receiver']=json.loads(target.read_text())
  assert case['receiver'].get('traceCoverage',{}).get('status')=='PASS','FULL_STAGE_TRACE_COVERAGE_FAILED:'+run
  oracle=subprocess.run([sys.executable,'-B','planning/betastability02/oracle-result.py',host,run],cwd=q.R,capture_output=True,text=True)
  with(q.E/('oracle-console-'+run+'.txt')).open('x')as f:f.write(oracle.stdout+oracle.stderr)
  case['oracleExit']=oracle.returncode
  assert oracle.returncode==0,'INDEPENDENT_VIDEO_ORACLE_FAILED:'+run
  case['videoOracle']=json.loads((q.E/('oracle-result-'+run+'.json')).read_text())
  verify_fixed()
  case.update(status='PASS',completedAt=time.time(),sourcePins='source-pins05.json',sourcePinsSha256=sha(pinbytes))
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
  'sourcePins':'source-pins05.json','sourcePinsSha256':sha(pinbytes),'noAutomaticRetry':True,'host':host,
  'startedAt':started,'finishedAt':time.time(),'error':error,'actualImages':0,
  'scope':'REPEATED_POLYGON_AND_CORRIDOR_SAME_DECLARED_CORPUS_NOT_HERA_OR_REAL_PAYLOAD'}
 with(q.E/'final-campaign01.json').open('x')as f:json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
 print(json.dumps({'campaignStatus':report['status'],'completedCases':report['completedCases'],'error':error}),flush=True)
if report['status']!='PASS':sys.exit(1)
