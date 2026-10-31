"""Pure source/budget/baseline/projection tests; noRootOperator or guardian instantiated."""
from pathlib import Path
from importlib import import_module
import json,hashlib,copy,sys,ast
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));H='planning.betaintegrated01.cockpit05-observer05.flight'

def main():
 tests=[]
 def check(ok,name):
  if not ok:raise AssertionError(name)
  tests.append(name)
 c=import_module(H+'.contract');s=import_module(H+'.setup_ui');f=import_module(H+'.feasibility');a=import_module(H+'.actual_controller')
 check(c.ROOT==s.R==a.R==R,'correct-root')
 accepted=json.loads((R/c.CURRENT_BASELINE_RECEIPT).read_text());check(s.validate_current_baseline(accepted['state'],accepted['allPrivateMap'],accepted),'real15-r1-closedshort-baseline')
 for kind in('missing-file','changed-file','changed-draft','missing-prior-review'):
  state=copy.deepcopy(accepted['state']);files=copy.deepcopy(accepted['allPrivateMap'])
  if kind=='missing-file':files.pop(next(iter(files)))
  if kind=='changed-file':files[next(iter(files))]='0'*64
  if kind=='changed-draft':state['workspace']['draft']['revision']=2
  if kind=='missing-prior-review':state['workspace']['reviews']=[]
  try:s.validate_current_baseline(state,files,accepted)
  except Exception:tests.append('baseline-refuses-'+kind)
  else:raise AssertionError(kind)
 check(len(import_module(H+'.preservation').expected_old())==233,'separate-old233-baseline')
 check(c.APK_SHA256=='1f43da9cc6732bc27e0e4877b4c52b3faed15b8e22ee8b4a5ea59109cea33f39','same-selected-apk')
 for duration in(180,1960):
  b=c.case_budget(maximum_seconds=duration);old=c.policy().case_budget(maximum_seconds=duration)
  check(b['requiredFreeBytes']==old['requiredFreeBytes']+5*2**20,'overlay1M-plus-artifact4M-budget-'+str(duration))
  cfg=c.build_config(R,'nominal','mock-observer','e','b',R/'no-created-output','case',maximum_seconds=duration)
  check(cfg['expectedConfigSHA256']=='6e8b3093e9802e20b4220fa872d57d9260bf02bd2ae40304ac161a53a0b6b17e','physical-config-unchanged-'+str(duration))
  check(cfg['externalObserverRecordingPolicy']['amendment']['intervalsMs']=={'0':200,'245':250,'242':1000},'explicit-cadence-'+str(duration))
  check(cfg['externalObserverRecordingPolicy']['amendment']['passiveApplicationTXBytes']==0,'zero-passive-tx-'+str(duration))
 def project(rtf,warm):return f.project({'chosenRTF':rtf},0,int(warm*1e9),0,int(warm*1e9))
 check(project(1,50)['status']=='CONDITIONAL_DURATION_FEASIBLE','nominal-rtf1-projection')
 check(project(.575,50)['status']=='DURATION_NOT_FEASIBLE_STOP_BEFORE_LONG','observed-e04-lowrtf-stop')
 check(project(1.1,150)['hostProjectionSeconds']==2002 and project(1.1,150)['status']=='DURATION_NOT_FEASIBLE_STOP_BEFORE_LONG','fast-rtf-no-hosttime-credit')
 check(project(1,108)['hostProjectionSeconds']==1960,'exact-host1960-boundary')
 check(project(1,109)['status']=='DURATION_NOT_FEASIBLE_STOP_BEFORE_LONG','host1960-one-second-over')
 for v in(0,-1,float('nan'),True):
  try:project(v,1)
  except ValueError:tests.append('invalid-rtf-refused-'+str(v))
  else:raise AssertionError(v)
 ev=lambda kind,data:{'body':{'kind':'EVENT','payload':{'eventKind':kind,'data':data}}}
 rows=[ev('TIMING_ORIGIN',{'hostMonotonicNs':1000})]+[ev('STAGE',{'frame':i,'fields':{'wireFrame':i,'receiveSinceOriginNs':i*1000000000//1200}})for i in range(12001)]
 m=f.stage_rtf(rows);check(abs(m['fullRTF']-1)<1e-8 and abs(m['minimumRolling5sRTF']-1)<1e-8,'allstage-full-min5s-rtf')
 q=copy.deepcopy(rows);q[100]['body']['payload']['data']['frame']+=1
 try:f.stage_rtf(q)
 except ValueError:tests.append('rtf-frame-gap-refused')
 else:raise AssertionError('gap')
 src=(Path(__file__).parent/'actual_controller.py').read_text();setup=(Path(__file__).parent/'setup_ui.py').read_text()
 check('short-independent01.json'in src and'duration-feasibility01.json'in src,'three-distinct-long-gates')
 check('def save_r1'not in setup and'def prepare_r1'not in setup and'def empty_baseline'not in setup,'no-install-seed-save-empty-path')
 check('cockpit05-observer05.ap_supervisor'in src and'contract.OBSERVER'in src,'new-supervisor-state-adapter')
 check(len(c.observer().feature_proof()['sourceSHA256'])==5,'cached-ap-feature5-sourceclosure')
 for p in Path(__file__).parent.glob('*.py'):ast.parse(p.read_text())
 out={'status':'PASS','checks':len(tests),'names':tests,'sourceSHA256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in Path(__file__).parent.glob('*.py')},'actualStarts':0,'ADBCommands':0,'APKChanged':False,'scope':'PURE_HELPER_MOCK_NOT_RUNTIME_CADENCE_OR_RTF_ACCEPTANCE'}
 target=R/'evidence/betaintegrated01-cockpit05-observer05/native/builder-mock01.json'
 with target.open('x')as z:json.dump(out,z,indent=2);z.write('\n')
 print(json.dumps({'status':'PASS','checks':len(tests),'actualStarts':0}))
if __name__=='__main__':main()
