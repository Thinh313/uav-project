"""Pure Builder checks. Never constructs a guardian/operator or invokes ADB."""
from pathlib import Path
from importlib import import_module
import ast,copy,hashlib,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R));H='planning.betaintegrated01.cockpit05-clockflight02'

def main():
 names=[]
 def check(ok,name):
  if not ok:raise AssertionError(name)
  names.append(name)
 controller=import_module(H+'.actual_controller');setup=import_module(H+'.setup_ui');contract=import_module(H+'.contract');duration=import_module(H+'.durations')
 check(controller.R==setup.R==contract.ROOT==R,'repository-root')
 s={'viewEpoch':2,'native':{'phase':'NO_SESSION','authorityRestorable':False},'ownerActive':False,'viewReady':True,'chosenView':'review','presentedView':'review'}
 l={'ownerActive':False,'bindingStagedSHA256':None,'viewReady':True,'view':'review','presentedView':'review'}
 check(controller.restart_inert_ready(s,l,1),'fresh-epoch-inert-positive')
 for field,value in [('native',{}),('viewEpoch',1),('viewEpoch',True),('ownerActive',True),('viewReady',False)]:
  q=copy.deepcopy(s);q[field]=value;check(not controller.restart_inert_ready(q,l,1),'restart-refuses-'+field+'-'+str(value))
 q=copy.deepcopy(s);q.pop('chosenView');q.pop('presentedView');z=copy.deepcopy(l);z.pop('view');z.pop('presentedView');check(not controller.restart_inert_ready(q,z,1),'missing-view-names-refused')
 for epoch in(1,True):
  z=copy.deepcopy(l);z['viewEpoch']=epoch;check(not controller.restart_inert_ready(s,z,1),'layout-epoch-refused-'+str(epoch))
 q=copy.deepcopy(l);q['bindingStagedSHA256']='f'*64;check(not controller.restart_inert_ready(s,q,1),'restart-no-staged-binding')
 t={'run':'r','epoch':'e','boot':'b','generation':'g','closed':True,'authorityRestorable':False,'input':{'consent':False,'leaseId':None,'authorityRestorable':False},'journal':{'run':'r','epoch':'e','closed':True,'commitAnchor':'a'*64,'records':9}}
 check(controller.native_terminal_ready(t,{'ownerActive':False},'r','e','b','g'),'outside-terminal-positive')
 for key,value in [('closed',False),('commitAnchor',None),('commitAnchor',True),('records',True)]:
  q=copy.deepcopy(t);q['journal'][key]=value;check(not controller.native_terminal_ready(q,{'ownerActive':False},'r','e','b','g'),'terminal-refuses-'+key+'-'+str(value))
 for key,value in [('run','other'),('generation','old'),('closed',False)]:
  q=copy.deepcopy(t);q[key]=value;check(not controller.native_terminal_ready(q,{'ownerActive':False},'r','e','b','g'),'terminal-context-refuses-'+key)
 check(not controller.native_terminal_ready(t,{'ownerActive':True},'r','e','b','g'),'terminal-owner-refusal')
 accepted,m=setup.expected_baseline();check(len(m)==134 and accepted['currentUI']['workspace']['draft']['revision']==6,'actual134-r6-baseline')
 for case,seconds in [('short',180),('long',1960)]:
  check(contract.CASES[case]['maximumSeconds']==seconds,'case-duration-'+case)
  v=contract.build_config(R,'nominal','mock-'+case,'e','b',R/'not-created','mock-case',maximum_seconds=seconds)
  check(v['requestedSpeedup']==1 and v['capMs']==500 and v['maximumSeconds']==seconds,'unchanged-profile-plus-duration-'+case)
  check(v['externalRecordingPolicy']['amendment']['clockFreshNs']==250000000,'clock250-unchanged-'+case)
 # Independent streams contain no CLOCK event in main.
 ctx={'run':'r','epoch':'e','boot':'b'};start=NS=1_000_000_000;end=start+NS
 event=lambda kind,data:{'body':{'kind':'EVENT','payload':{'eventKind':kind,'data':data}}}
 mainrows=[event('TIMING_ORIGIN',{'hostMonotonicNs':start})]+[event('STAGE',{'frame':i,'fields':{'wireFrame':i,'receiveSinceOriginNs':i*NS//1200}})for i in range(1201)]
 clocks=[]
 for i in range(3):
  at=start+i*NS//2;raw=struct.pack('<7Q',i+1,at,at,0,0,0,0);d={**ctx,'kind':'RESPONSE','status':'MATCHED','hostReceiveNs':at,'guestReceiveNs':at,'guestSendNs':at,'rawHex':raw.hex(),'rawSHA256':hashlib.sha256(raw).hexdigest()};clocks.append(event('CLOCK',d))
 v=duration.window_rows(mainrows,clocks,start,end,ctx);check(v['modelWindowNs']==NS and v['APGuestWindowNs']==NS and v['syntheticRows']==0,'separate-original-stream-duration-positive')
 for name,a,b in [('missing-clock',mainrows,[]),('missing-main',[],clocks),('foreign-clock',mainrows,copy.deepcopy(clocks)),('rawSHA',mainrows,copy.deepcopy(clocks)),('clock-order',mainrows,list(reversed(clocks))),('frame-gap',mainrows[:3]+mainrows[4:],clocks)]:
  if name=='foreign-clock':b[0]['body']['payload']['data']['boot']='foreign'
  if name=='rawSHA':b[0]['body']['payload']['data']['rawSHA256']='0'*64
  try:duration.window_rows(a,b,start,end,ctx)
  except(ValueError,AssertionError):names.append('duration-refuses-'+name)
  else:raise AssertionError(name)
 # Source wiring checks distinguish current run export from all-history SHA proofs.
 src=(Path(__file__).parent/'actual_controller.py').read_text();export=(Path(__file__).parent/'export_native.py').read_text()
 check("all-private-before-case-SHA.json"in src and "CASE_PRIOR_PRIVATE_HISTORY_CHANGED"in src,'prior-short-retention-per-case')
 check("clockGuardPriming"in src and "clockowner02.runtime.ap_supervisor"in src,'three-prime-new-supervisor-wiring')
 check("CHUNK=256*1024"in export and "GLOBAL=192*MIB"in export and "deadline=time.monotonic()+120"in export,'export-caps-and-deadline')
 check("files/control-runs/'+self.run"in export and "files/control-runs','files/workspace03"not in export,'tar-only-selected-run-not-prior-history')
 for p in Path(__file__).parent.glob('*.py'):ast.parse(p.read_text())
 check(True,'all-source-syntax')
 result={'status':'PASS','checks':len(names),'names':names,'sourceSHA256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in Path(__file__).parent.glob('*.py')},'ADBCommands':0,'APStarts':0,'AndroidStarts':0,'scope':'PURE_MOCK_NOT_RUNTIME_ACCEPTANCE'}
 out=R/'evidence/betaintegrated01-cockpit05-clockflight02/native/builder-mock03.json'
 with out.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'status':'PASS','checks':len(names),'actualStarts':0}))
if __name__=='__main__':main()
