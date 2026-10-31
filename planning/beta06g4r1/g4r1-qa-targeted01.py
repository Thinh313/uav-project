"""Targeted independent G4R1 mock replay; no actual Popen/ADB/listen/UI."""
from pathlib import Path
import json,hashlib,datetime,os,unittest,io
R=Path(__file__).resolve().parents[2];P=Path(__file__).parent;E=R/'evidence/beta06/generation04'
rows=[];recipes=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def recipe(name,old,stop=None):
 source=(R/old).read_text();source=source.replace('planning/beta06g4/','planning/beta06g4r1/').replace("'06'","'08'").replace("'07'","'09'").replace('BOOT07','BOOT09').replace('BOOT06','BOOT08').replace('boot07','boot09').replace('boot06','boot08')
 if stop:source=source.split(stop)[0]
 scope={'__name__':'independent_g4r1_'+name,'__file__':str(P/Path(old).name)}
 if name=='hostwindow':source=source.replace("rows=[]", "m.Controller.workspace_before_first_writer=lambda self:{'classification':'MOCK_WORKSPACE_GUARD_TESTED_SEPARATELY'}\nrows=[]")
 exec(compile(source,str(P/Path(old).name),'exec'),scope)
 recipes.append({'name':name,'sourceRecipe':old,'sourceSHA256':digest(R/old),'adaptation':'In-memory helper namespace and attempt IDs only; hostwindow isolates first-writer filesystem guard, separately tested.'})
 if 'Tests'in scope:
  result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(scope['Tests']))
  rows.append({'name':name,'groups':result.testsRun,'status':'PASS'if result.wasSuccessful()else'FAIL','failures':[(str(t),e)for t,e in result.failures+result.errors]})
 else:
  rows.append({'name':name,'groups':len(scope['rows']),'status':'PASS'if all(x['status']=='PASS'for x in scope['rows'])else'FAIL','cases':scope['rows']})
recipe('hostwindow','planning/beta06g4/qa-integrated-host-window04.py','result=')
recipe('controller','planning/beta06g4/qa-integrated-controller-negative04.py','report=')
recipe('native_fault_admission','planning/beta06g4/builder-native-tests.py')
recipe('airborne','planning/beta06g4/builder-airborne-tests.py')
# Ground functions use original immutable synthetic fixtures, excluding fixture IO/collect.
recipe('ground','planning/beta06g4/builder-ground-mock.py','fixture_dir=')
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_TARGETED_NEW_HARNESS_MOCKS'if all(x['status']=='PASS'for x in rows)else'FAIL','classification':'SOURCE_MOCK_NO_ACTUAL_RUNTIME','groups':sum(x['groups']for x in rows),'rows':rows,'recipes':recipes,'sources':{str(p.relative_to(R)):digest(p)for p in sorted(P.glob('qa-*.py'))},'scope':'Existing independent recipes and shared Builder fixtures adapted in memory only to new actual helper modules/attempts. Fake clock/process/UI/filesystem. No production source tests repeated; no real Popen, ADB, Docker, listener, browser or flight. Airborne tiny synthetic reference directories automatically removed. Hostwindow filesystem guard tested separately.'}
p=E/'g4r1-qa-targeted01.json'
with p.open('x')as f:json.dump(report,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(p),'status':report['status'],'groups':report['groups'],'failed':[r for r in rows if r['status']!='PASS']}));assert report['status'].startswith('PASS')
