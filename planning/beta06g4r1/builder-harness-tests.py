"""Minimal recheck harness SOURCE/MOCK tests. No AP/ADB/listener/UI effects."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys,types,unittest
from unittest.mock import patch
P=Path(__file__).parent;R=P.parents[1];E=R/'evidence/beta06/generation04';rows=[]
def check(name,fn):
 try:fn();rows.append({'name':name,'status':'PASS'})
 except BaseException as e:rows.append({'name':name,'status':'FAIL','error':str(e)})
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
c=mod('g4r1_controller_tests','qa-root-controller.py');d=mod('g4r1_device_tests','qa-device-actions.py')
def normalized():
 files=list(P.glob('qa-*.py'));assert len(files)==12
 for p in files:
  expected=(R/'planning/beta06g4'/p.name).read_text().replace("['06','07']","['08','09']").replace("attempt=='06'","attempt=='08'").replace("self.attempt='07'","self.attempt='09'").replace("sys.argv[2]=='06'","sys.argv[2]=='08'")
  expected=expected.replace('BOOT06','BOOT08').replace('BOOT07','BOOT09').replace('BEFORE07','BEFORE09').replace('boot06','boot08').replace('boot07','boot09').replace('android-closure06','android-closure08').replace('android-attempt07','android-attempt09').replace('newConnectIntentsBoot06','newConnectIntentsBoot08').replace('connectIntentsBoot07','connectIntentsBoot09')
  if p.name=='qa-root-controller.py':expected=expected.replace('host-app04-restart','host-app04-recheck01-restart').replace("'host-app04'","'host-app04-recheck01'").replace("'host-console'","'g4r1-host-console'")
  if p.name=='qa-android.py':expected=expected.replace("'qa-adb-commands.jsonl'","'g4r1-qa-adb-commands.jsonl'")
  if p.name=='qa-device-actions.py':expected=expected.replace("G3_BASELINE='evidence/beta06/generation03/android-store-after-failed-launch-04.json'", "G3_BASELINE='evidence/beta06/generation04/android-store-after-browser-pending-06.json'").replace('CLOSED_G3','CLOSED_G4').replace('closedG3','closedG4').replace('ClosedG3','ClosedG4').replace('AtG3Closure','AtG4Closure')
  actual=p.read_text()
  if p.name=='qa-root-controller.py':
   tree=ast.parse(actual);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Controller');fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='workspace_before_first_writer');lines=actual.splitlines(keepends=True);actual=''.join(lines[:fn.lineno-1]+lines[fn.end_lineno:]);actual=actual.replace("self.host_out=out;\n  if self.host_instances==1:self.workspace_before_first_writer()\n  self.host_process=subprocess.Popen", "self.host_out=out;self.host_process=subprocess.Popen")
  assert actual==expected,'UNENUMERATED_DIFF:'+p.name
check('all12helpers_exact_normalized_attempt_output_closedbaseline_diffs_only_plus_explicit_workspace_guard',normalized)
def plan():
 p=c.plan();assert p['attempts']==['08','09']and p['newConnectIntentsBoot08']==4 and p['connectIntentsBoot09']==0 and p['hostBudgetSecondsAcrossBothBoots']==2700 and p['apBudgetSeconds']==540;assert 'pilot/beta06g4/app.mjs'in(P/'qa-root-controller.py').read_text();assert '.local/beta06g3/arducopter'in(P/'qa-ap-admission.py').read_text()
check('sameG4production_globalAPbudget_45min08_09_plan',plan)
def workspace():
 ctl=c.Controller('08',boot_reader=lambda:'BOOT',clock=lambda:100);v=ctl.workspace_before_first_writer();assert v['files']==17 and v['bytes']==798359
 with patch.object(c.hashlib,'sha256',return_value=types.SimpleNamespace(hexdigest=lambda:'BAD')):
  try:ctl.workspace_before_first_writer()
  except AssertionError as e:assert 'DRIFT'in str(e);return
  raise AssertionError('WORKSPACE_DRIFT_ACCEPTED')
check('exact_closed_workspace_before_first_writer_and_tamper_refusal',workspace)
def native():
 old=json.loads((R/d.G3_BASELINE).read_text());proof=d.retained_g3_store_decision(old['files'],(R/old['journalFile']).read_bytes());assert proof['nativeStoreExactAtRead']and proof['remainingPickerOperationsAtG4Closure']==3;assert d.G3_BASELINE.endswith('android-store-after-browser-pending-06.json')
check('actual_closed_G4native34_19_13_baseline_readonly_exact',native)
# Reuse frozen Builder test recipes in-memory, adapting only the harness path,
# explicit attempt labels and exclusive mock output names. Never modify old tests.
def recipe(name,run_main=False):
 src=(R/'planning/beta06g4'/name).read_text().replace('planning/beta06g4/qa-','planning/beta06g4r1/qa-').replace("'06'","'08'").replace('BOOT07','BOOT09').replace('boot07','boot09')
 if name=='builder-host-window-mock.py':src=src.replace("m.module=module", "m.module=module\nm.Controller.workspace_before_first_writer=lambda self:{'classification':'FAKE_FILESYSTEM_WORKSPACE_CHECK_SEPARATE_TEST'}").replace('builder-host-window01.json','g4r1-builder-host-window01.json').replace("startswith('evidence/beta06/generation04/builder-')","startswith('evidence/beta06/generation04/g4r1-builder-')")
 if name=='builder-ground-mock.py':src=src.replace('qa-ground-fixture01','g4r1-ground-fixture02').replace('qa-ground-collect-mock01','g4r1-ground-collect-mock02').replace('builder-ground01.json','g4r1-builder-ground02.json')
 ns={'__file__':str(P/name),'__name__':'__main__'if run_main else'g4r1_recipe_'+name.replace('-','_')}
 prior=list(sys.argv);sys.argv=[str(P/name)]
 try:exec(compile(src,str(P/name),'exec'),ns)
 finally:sys.argv=prior
 if name=='builder-native-tests.py':
  result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(ns['Tests']));assert result.wasSuccessful();return result.testsRun
 if name=='builder-airborne-tests.py':
  result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(ns['Tests']));assert result.wasSuccessful();return result.testsRun
 assert all(r.get('status')=='PASS'for r in ns['rows']);return len(ns['rows'])
counts={}
for name in ['builder-native-tests.py','builder-host-window-mock.py','builder-airborne-tests.py','builder-ground-mock.py']:
 def run(name=name):counts[name]=recipe(name)
 check('frozen_recipe_inmemory_'+name,run)
report={'classification':'SOURCE_MOCK_RECHECK_HARNESS_NO_ACTUAL_RUNTIME','status':'PASS_G4R1_MINIMAL_HARNESS_NORMALIZATION_CONTRACTS'if all(r['status']=='PASS'for r in rows)else'FAIL','rows':rows,'reusedRecipeGroups':counts,'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(P.glob('*'))if p.is_file()},'scope':'12namespace/baseline/output-only helper adaptations, explicit firstwriter workspace hash guard, frozen Builder recipes in-memory. Existing G4production/replayers/pins untouched; noAP/ADB/listener/browser or actual45min test.'};out=E/'g4r1-builder-harness-tests02.json';out.open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'rows':len(rows),'recipeGroups':counts,'failures':[r for r in rows if r['status']=='FAIL']}));assert report['status'].startswith('PASS')
