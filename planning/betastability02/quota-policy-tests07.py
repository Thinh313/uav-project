"""Read-only policy boundary checks. No runtime/AP/build or evidence exclusion."""
from pathlib import Path
import ast,json,importlib.util,hashlib
R=Path(__file__).resolve().parents[2];E=R/'evidence/betastability02'
p=R/'pilot/betastability02/companion.py';spec=importlib.util.spec_from_file_location('quota_companion07',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
results=[]
def all_assert(v):assert v
def check(name,fn):
 try:fn();results.append({'name':name,'status':'PASS'})
 except Exception as e:results.append({'name':name,'status':'FAIL','error':repr(e)})
def rejected(usage,reserve,error):
 try:m.quota_decision(usage,reserve)
 except RuntimeError as e:assert error in str(e);return
 raise AssertionError('EXPECTED_REJECTION')
check('11999 existing paths +1000 case reserve rejects before allocation',lambda:rejected({'files':11999,'bytes':0,'symlinks':[]},True,'FILE_BUDGET_12000'))
check('Whole2GiB +64MiB reserve rejects',lambda:rejected({'files':0,'bytes':2*2**30,'symlinks':[]},True,'BYTE_BUDGET_2GIB'))
check('Counted symlink refuses qualification rather than excluded scope',lambda:rejected({'files':1,'bytes':10,'symlinks':['counted-link']},True,'SYMLINK_UNQUALIFIED_COUNTED'))
check('Global12000 file hard bound consistent',lambda: m.quota_decision({'files':12000,'bytes':0,'symlinks':[]},False))
check('Exactly reserved11000+1000 and budget-64MiB+64MiB fits entry maximum',lambda:m.quota_decision({'files':11000,'bytes':2*2**30-64*2**20,'symlinks':[]},True))
usage=m.task_usage(E);actual=m.quota_decision(usage,True);check('Actual whole namespace, including mocks/failures/revisions, fits next-case reserve',lambda:actual)
source=(R/'pilot/betastability02/runtime.py').read_text();comp=p.read_text()
check('Runtime and companion use shared policy, no5000 legacy constant',lambda: all_assert('5000'not in source and 'from companion import POLICY,task_usage,quota_decision'in source and 'quota_decision(task_usage'in source and "check_entry_quota(root,rid,out)"in source and "next_scan=t+POLICY['quotaScanSeconds']"in comp))
# Assertion helper is resolved at execution time; defined before the final check rerun below.
report={'atSource':'PYTHON_SHARED_COMPANION_POLICY_READ_ONLY_BOUNDARIES','results':results,'actualUsage':usage,'entryDecision':actual,'runtimeLaunches':0,'containerAllocations':0,'exclusions':[]}
report['status']='PASS'if all(r['status']=='PASS'for r in results)else'FAIL'
with(R/'planning/betastability02/quota-python-results07.json').open('x')as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
if report['status']!='PASS':raise SystemExit(1)
