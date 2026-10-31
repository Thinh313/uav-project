from pathlib import Path
from importlib import util
import sys,json,copy,hashlib
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));p=R/'planning/betaintegrated01/cockpit05-entry10/android/setup_ui.py';sp=util.spec_from_file_location('setup05',p);m=util.module_from_spec(sp);sp.loader.exec_module(m)
a,mp=m.expected_baseline();before=a['state'];after=copy.deepcopy(before);after['workspace']['draft']['revision']=6;after['workspace']['draft']['name']=m.NAME;H='a'*64;after['workspace']['draftSHA256']=H;newmp={**mp,'files/workspace03/draft-000006-'+H+'.json':H};tests=[]
def run(name,fn,reject=False):
 try:fn();passed=not reject
 except(m.OperatorError,KeyError,TypeError,ValueError):passed=reject
 tests.append({'id':name,'pass':passed})
run('positiveR5toR6pureSchemaNotSave',lambda:m.verify_r6(before,after,mp,newmp))
for label,change in [('changedGeometry',{'geometry':[[0,0],[0,1],[1,1]]}),('wrongAltitude',{'altitudeM':4}),('wrongName',{'name':'OTHER'}),('wrongRevision',{'revision':5})]:
 bad=copy.deepcopy(after);bad['workspace']['draft'].update(change);run(label,lambda b=bad:m.verify_r6(before,b,mp,newmp),True)
run('oldfilelost',lambda:m.verify_r6(before,after,mp,{k:v for k,v in newmp.items()if k!=next(iter(mp))}),True)
run('extraunknownfile',lambda:m.verify_r6(before,after,mp,{**newmp,'extra':'x'}),True)
state=copy.deepcopy(a['state']);layout=copy.deepcopy(a['layout']);run('NOSESSIONpresented',lambda:m.native_empty(state,layout,'survey'))
for label,target,key,value in [('owner','s','ownerActive',True),('epochBool','s','viewEpoch',True),('notReady','l','viewReady',False),('binding','l','bindingStagedSHA256','b'*64)]:
 s=copy.deepcopy(state);l=copy.deepcopy(layout);(s if target=='s'else l)[key]=value;run(label,lambda s=s,l=l:m.native_empty(s,l,'survey'),True)
line=next(iter(mp));text=mp[line]+'  '+line+'\n';run('shaMapactualLine',lambda:m.sha_map(text));run('shaMapduplicate',lambda:m.sha_map(text+text),True);run('shaMapTraversal',lambda:m.sha_map('a'*64+'  files/workspace03/../draft-000001-'+'a'*64+'.json\n'),True)
assert all(t['pass']for t in tests)
r={'status':'PASS_PURE_UI_SETUP_BOUNDARIES_NOT_ANDROID','tests':tests,'sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'ADBCalls':0,'scope':'Importedpurehelpers only; noSetupinstance/RootOperator/ADB/service invocation; actualR6notperformed.','actualThirtyMinuteAccepted':False};(R/'evidence/betaintegrated01-cockpit05-entry10/qa/setup01.json').open('x').write(json.dumps(r,indent=2)+'\n');print(r['status'],len(tests))
