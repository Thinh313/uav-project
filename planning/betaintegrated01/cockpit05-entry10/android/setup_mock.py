"""Pure setup contract tests, no device/process/runtime actions."""
from pathlib import Path
import sys,importlib.util,subprocess,json,hashlib,copy
from unittest.mock import patch
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];S=Path(__file__).with_name('setup_ui.py');E=R/'evidence/betaintegrated01-cockpit05-entry10/native';cases=[]
def check(name,yes):
 if not yes:raise AssertionError(name)
 cases.append(name)
def reject(name,callback):
 try:callback();accepted=True
 except M.OperatorError:accepted=False
 check(name,not accepted)
calls=[]
def denied(*a,**k):calls.append((a,k));raise AssertionError('NO_SUBPROCESS_IN_TEST')
with patch.object(subprocess,'run',denied),patch.object(subprocess,'Popen',denied):
 spec=importlib.util.spec_from_file_location('cockpit05_entry10_setup_test',S);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);check('ImportNoADBOrProcess',not calls)
 accepted,old=M.expected_baseline();check('AcceptedEightAndR5',len(old)==8 and accepted['state']['workspace']['draft']['revision']==5)
 state=copy.deepcopy(accepted['state']);layout=copy.deepcopy(accepted['layout']);M.native_empty(state,layout,'survey');check('ActualAcceptedNO_SESSIONBaselineAllowed',True)
 for name,mut in [('owner',lambda s,l:s.update(ownerActive=True)),('binding',lambda s,l:l.update(bindingStagedSHA256='a'*64)),('session',lambda s,l:s['native'].update(phase='RUNNING')),('render',lambda s,l:l.update(viewReady=False)),('epochBoolean',lambda s,l:s.update(viewEpoch=True))]:
  s,l=copy.deepcopy(state),copy.deepcopy(layout);mut(s,l);reject(name+'Rejected',lambda:M.native_empty(s,l,'survey'))
 after=copy.deepcopy(state);after['workspace']['draft'].update(revision=6,name=M.NAME);raw=json.dumps(after['workspace']['draft'],ensure_ascii=False,separators=(',',':')).encode();digest=hashlib.sha256(raw).hexdigest();after['workspace']['draftSHA256']=digest;new={**old,'files/workspace03/draft-000006-'+digest+'.json':digest};result=M.verify_r6(state,after,old,new);check('R6OnlyNameRevisionChangesAccepted',result['revision']==6)
 for name,mut in [('geometry',lambda s:s['workspace']['draft'].update(geometry=[[0,0],[0,1],[1,1]])),('altitude',lambda s:s['workspace']['draft'].update(altitudeM=4)),('name',lambda s:s['workspace']['draft'].update(name='wrong')),('id',lambda s:s['workspace']['draft'].update(id='new'))]:
  invalid=copy.deepcopy(after);mut(invalid);reject(name+'NotSilentlyAccepted',lambda:M.verify_r6(state,invalid,old,new))
 bad=dict(new);bad[next(iter(old))]='f'*64;reject('OldEightChangedRejected',lambda:M.verify_r6(state,after,old,bad));reject('MissingOldFileRejected',lambda:M.verify_r6(state,after,old,{k:v for k,v in new.items()if k!=next(iter(old))}));reject('ExtraGenerationRejected',lambda:M.verify_r6(state,after,old,{**new,'files/workspace03/draft-000007-'+'a'*64+'.json':'a'*64}))
 reject('PendingForeignMapRejected',lambda:M.sha_map('a'*64+'  files/workspace03/x.pending\n'));reject('FilenameSHARefused',lambda:M.sha_map('b'*64+'  files/workspace03/draft-000001-'+'a'*64+'.json\n'))
 fake=M.Setup.__new__(M.Setup);observed={'screenSHA256':'a'*64,'screen':'test.png','state':{'viewEpoch':7}}
 fake.observe=lambda *a,**k:observed
 args=type('A',(),{'reviewed_current_screen_sha':'b'*64,'step':'save-r6'})()
 reject('FreshScreenSHAMismatchBeforeAnyAction',lambda:fake.reviewed(args,'survey'))
 from unittest.mock import patch as p
 with p.object(M,'exclusive',lambda *a,**k:None):
  args.reviewed_current_screen_sha='a'*64;check('ExactCurrentScreenshotApprovalAccepted',fake.reviewed(args,'survey')is observed)
 source=S.read_text();check('NoAXCDPEvalSeedClearInstallOrStageCommands',all(x not in source for x in ['uiautomator','evaluateJavascript','pm clear','STAGE_BINDING','am start','apksigner','adb root']))
 check('ExplicitSaveOnlyOneTap',source.count("self.bytes(['shell','input','tap',*SAVE])")==1)
 check('PreparedAndSaveOneShotIntentMarkers','prepare-r6-intent.json'in source and 'save-r6-intent.json'in source)
 check('OnlyNewEvidenceScope',str(M.E)==str(R/'evidence/betaintegrated01-cockpit05-entry10'))
 check('DevicePackage05Only',M.PACKAGE=='vn.rtr.aeris.cockpit05')
 check('NoDeviceSubprocessCalls',not calls)
 mapped=M.Setup.__new__(M.Setup);map_calls=[]
 def map_bytes(args,timeout=3):
  map_calls.append(args)
  if args[3]=='ls':return('\n'.join(path.split('/')[-1]for path in old)+'\n').encode()
  require_paths=args[4:];assert all(path in old for path in require_paths);return(''.join(old[path]+'  '+path+'\n'for path in require_paths)).encode()
 mapped.bytes=map_bytes;check('MapUsesDirectSafeExplicitPaths',mapped.workspace_map()==old and len(map_calls)==2 and all('sh'not in cmd for cmd in map_calls))
with patch.object(subprocess,'run',denied),patch.object(subprocess,'Popen',denied):
 fixture=E/'guardian-fixture04';fixture.mkdir();(fixture/'guard.jsonl').write_text(json.dumps({'hostNs':10000000000,'freeBytes':12*2**30,'forecastFreeBytes':12*2**30,'AC':False,'batteryPercent':70})+'\n')
 launch={'scope':'ANDROID_UI_SUBSET_NO_AP_NO_FLIGHT','serial':'emulator-5582','maximumSeconds':900,'guardianPID':111,'guardianProcessStart':'guardian-start','pid':222,'processStart':'emulator-start','processGroup':222,'guardianSourceSHA256':hashlib.sha256(M.GUARD_SOURCE.read_bytes()).hexdigest()}
 admission={'scope':'ANDROID_UI_SUBSET_NO_AP_NO_FLIGHT','metadataBudgetBytes':32*2**20,'maximumSeconds':900}
 def fake_read(path):
  if Path(path).name=='launch.json':return launch
  if Path(path).name=='admission.json':return admission
  raise AssertionError('Unexpectedgatepath')
 def process_field(pid,field):return'00:20'if field=='etime'else'guardian-start'if pid==111 else'emulator-start'
 with patch.object(M,'GUARD',fixture),patch.object(M,'read',fake_read),patch.object(M,'ps_field',process_field),patch.object(M.os,'getpgid',lambda pid:222),patch.object(M.time,'monotonic_ns',lambda:11000000000),patch.object(M,'allocated',lambda path:0):
  check('GuardianLiveScopeFreshFloorPowerAccepted',M.guard_ready()['guardianPID']==111)
  with patch.object(M.time,'monotonic_ns',lambda:14000000000):reject('GuardianStaleRefused',M.guard_ready)
  with patch.object(M,'ps_field',lambda pid,field:'wrong'):reject('GuardianPIDReusedRefused',M.guard_ready)
  with patch.object(M,'allocated',lambda path:32*2**20):reject('MetadataBudgetRefusedBeforeWrite',M.guard_ready)
  row=json.loads((fixture/'guard.jsonl').read_text());row['forecastFreeBytes']=12*2**30+.25;(fixture/'guard.jsonl').write_text(json.dumps(row)+'\n');check('FiniteFractionalForecastAcceptedWithoutRounding',M.guard_ready()['guardianPID']==111)
  for invalid in (float('nan'),float('inf'),True):
   row['forecastFreeBytes']=invalid;(fixture/'guard.jsonl').write_text(json.dumps(row)+'\n');reject('InvalidForecast_'+str(invalid)+'_Refused',M.guard_ready)
  row['forecastFreeBytes']=12*2**30;(fixture/'guard.jsonl').write_text(json.dumps(row)+'\n')
  (fixture/'closure.json').write_text('{}');reject('GuardianClosedRefused',M.guard_ready)
 check('GuardianTestsNoProcesses',not calls)
report={'status':'PASS_PURE_MOCK_NOT_ANDROID_EXECUTION','groups':len(cases),'cases':cases,'sourceSHA256':hashlib.sha256(S.read_bytes()).hexdigest(),'ADBCalls':0,'processesStarted':0,'AndroidStateWritten':False};(E/'setup-mock04.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','groups':len(cases),'ADBCalls':0}))
