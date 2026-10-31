"""Independent original-error preservation method fixtures, no actual actors."""
from pathlib import Path
import os,sys,json,hashlib,types
R=Path(__file__).resolve().parents[3];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(R/'planning/betasim-integrated01/runtime/source'),str(R)]
from aeris_runtime.product_runtime import WorkbenchRuntime
checks=[];target=R/'planning/betasim-integrated01/runtime/source/aeris_runtime/product_runtime.py';entry=R/'planning/betasim-integrated01/runtime/root-owner-ready02.py';budgetSource=R/'planning/betasim-integrated01/runtime/source/aeris_runtime/metadata_budget.py';pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[target,entry,budgetSource]}
class Budget:
 def __init__(self):self.rows=[]
 def write(self,owner,path,raw,**kw):self.rows.append((owner,str(path),bytes(raw),kw));return{'sha256':hashlib.sha256(raw).hexdigest()}
 def failure(self,*a,**kw):pass
def owner():return types.SimpleNamespace(root=Path('/QA_MEMORY_NO_WRITES'),budget=Budget())
def test(name,fn):
 try:fn();checks.append({'id':name,'pass':True})
 except BaseException as e:checks.append({'id':name,'pass':False,'error':str(e)})
def original():
 o=owner();s='Traceback\nValueError: original failure\n';r=WorkbenchRuntime.persist_owner_error(o,s);row=o.budget.rows[0];assert row[0]=='closure'and row[1].endswith('/reports/owner-error.txt')and row[2]==s.encode()and row[3]=={'closing':True};assert r['captureComplete']is True and r['truncatedPrefixNotFullTrace']is False and r['sha256']==hashlib.sha256(s.encode()).hexdigest()
test('exact-original-trace-bytes-bound-to-source-closure-reference',original)
def prefix():
 o=owner();s='ộ'*9000;r=WorkbenchRuntime.persist_owner_error(o,s);assert o.budget.rows[0][2]==s.encode()[:16384]and r['bytes']==16384 and r['originalBytes']==len(s.encode())and r['captureComplete']is False and r['truncatedPrefixNotFullTrace']is True
test('over16KiB-original-byte-prefix-never-called-complete',prefix)
def failed_persistence():
 o=owner();o.budget.write=lambda *a,**kw:(_ for _ in()).throw(OSError('QA_EIO'))
 try:WorkbenchRuntime.persist_owner_error(o,'original')
 except OSError:assert not hasattr(o,'owner_error_ref');return
 raise AssertionError('UNEXPECTED_STORAGE_SUCCESS')
test('EIO-does-not-manufacture-original-trace-reference',failed_persistence)
def terminal():
 o=owner();WorkbenchRuntime.persist_owner_error(o,'Traceback:PRIMARY');o.case=None;o.digest='a'*64;o.close_guardian=lambda **kw:(_ for _ in()).throw(RuntimeError('SECONDARY_CLEANUP'));rows=[];o.write=lambda name,value,**kw:rows.append((name,value,kw));primary=RuntimeError('PRIMARY');result=WorkbenchRuntime.fail_case(o,primary);row=rows[0];q=row[1];assert row[0]=='owner-terminal.json'and row[2]=={'closing':True}and q['primaryFailure']=='PRIMARY'and q['secondaryErrors'][0]['step']=='guardian-exceptional-disposal'and q['ownerErrorRef']==o.owner_error_ref and q['normalCompletedClosureClaimed']is False and q['APGroundProven']is False and q['APStarted']is False and q['automaticRetry']is False and result['flightAcceptance']is False
test('secondary-cleanup-keeps-primary-error-and-original-trace-join',terminal)
def source_order():
 s=entry.read_text();e=s[s.index('except BaseException as primary:'):];assert e.index('persist_owner_error(traceback.format_exc())')<e.index('owner.fail_case(primary)')and'owner-error.txt'in budgetSource.read_text()and'SOURCE_OWNER_TERMINAL_OR_TRACE_EXACT_BOUND'in budgetSource.read_text()
test('actual-entry-captures-trace-before-cleanup-and-exact-budget-paths',source_order)
report={'format':'aeris-independent-owner-original-error-closure','version':1,'status':'PASS_ACTOR_FREE_METHOD_FIXTURE_NOT_ACTUAL_CLOSURE'if all(x['pass']for x in checks)else'FAIL_SOURCE_CONTRACT','sourcePins':pins,'checks':checks,'actualWritesToRuntimeBudget':False,'actualADBAPOrActors':False,'sourceChanged':any(hashlib.sha256((R/p).read_bytes()).hexdigest()!=h for p,h in pins.items())}
n=1
while(out:=R/f'evidence/betasim-integrated01/qa/owner-terminal-{n:02}.json').exists():n+=1
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':checks,'path':str(out)}))
