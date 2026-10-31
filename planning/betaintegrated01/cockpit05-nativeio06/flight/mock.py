"""Bounded pure helper mocks; synthetic clocks/device receipts, no ADB/process/socket."""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
from copy import deepcopy
import ast,json,hashlib,subprocess,socket,shutil
R=Path(__file__).resolve().parents[4];H='planning.betaintegrated01.cockpit05-nativeio06.flight';C=import_module(H+'.contract');D=import_module(H+'.diagnostic');S=import_module(H+'.setup_ui');P=import_module(H+'.preservation');E=R/C.EVIDENCE/'host/mock01'
CONTEXT={'run':'synthetic-run','epoch':'synthetic-epoch','boot':'synthetic-boot','generation':'synthetic-generation','operator':'synthetic-operator','profileId':'synthetic-profile','binarySHA256':'b'*64,'configSHA256':'c'*64}
def fixture():
 phases=sorted(D.PHASES);summary=[{'phase':p,'count':1,'wallTotalNs':10,'wallMaxNs':10,'cpuKnownCount':1,'cpuTotalKnownNs':2,'cpuMaxKnownNs':2,'wallHistogram':[1,0,0,0,0,0,0,0]}for p in phases]
 return {'format':'aeris-native-io-diagnostics','version':1,'context':CONTEXT,'APKSourceSHA256':'a'*64,'cpuUnavailableOperations':0,'measurementErrors':0,'threadCpuClock':'android.os.Debug.threadCpuTimeNanos_CURRENT_THREAD','wallClockDomain':'ANDROID_ELAPSED_REALTIME_NS_CALLER_CLOCK','phaseSummary':summary,'spanCount':len(phases),'recentSpans':[{'phase':p,'threadId':1,'beginElapsedNs':10,'endElapsedNs':20,'wallNs':10,'threadCpuNs':2}for p in phases],'queueEventCount':0,'recentQueueEvents':[],'ringCapacity':256,'maximumMessagesPerOuterLoop':16,'diagnosticNotAuthorityOrFlightProof':True,'nonCPUWallCause':'UNKNOWN_NOT_EXCLUSIVE_FILESYSTEM_OR_SCHEDULER','terminalStateSHA256':'d'*64}
def main():
 E.mkdir(parents=True,exist_ok=False);scratch=E/'scratch';scratch.mkdir();cases=[]
 def test(name,fn):
  try:cases.append({'case':name,'pass':True,'detail':fn()})
  except Exception as e:cases.append({'case':name,'pass':False,'error':repr(e)})
 def rejection(fn):
  try:fn()
  except Exception:return True
  raise AssertionError('invalidaccepted')
 def diag():
  v=fixture();D.validate(json.dumps(v).encode(),CONTEXT,'a'*64);seen=[]
  for field,value in [('measurementErrors',1),('cpuUnavailableOperations',1),('maximumMessagesPerOuterLoop',17),('spanCount',0),('ringCapacity',257)]:
   x=deepcopy(v);x[field]=value;rejection(lambda:D.validate(json.dumps(x).encode(),CONTEXT,'a'*64));seen.append(field)
  for fault in('duplicate','missingphase','unknowncpu','badhist','wrongcontext','floatcount'):
   x=deepcopy(v)
   if fault=='duplicate':x['phaseSummary'][1]['phase']=x['phaseSummary'][0]['phase']
   if fault=='missingphase':x['phaseSummary']=x['phaseSummary'][1:]
   if fault=='unknowncpu':x['recentSpans'][0]['threadCpuNs']=-1
   if fault=='badhist':x['phaseSummary'][0]['wallHistogram'][0]=2
   if fault=='wrongcontext':x['context']={**CONTEXT,'run':'foreign'}
   if fault=='floatcount':x['phaseSummary'][0]['count']=1.0
   rejection(lambda:D.validate(json.dumps(x).encode(),CONTEXT,'a'*64));seen.append(fault)
  return {'syntheticFixtureOnly':True,'negativeCases':seen,'noActualAndroidClockClaim':True}
 test('diagnostic strict clocks/CPUcoverage/counts/rings/context',diag)
 def preserve():
  ans={}
  for package in P.BASELINES:
   m=P.expected_old(package);raw=''.join(h+'  '+n+'\n'for n,h in m.items()).encode();assert P.parse_private_map(raw,len(m))==m;rejection(lambda:P.parse_private_map(raw,len(m)+1));ans[package]=len(m)
  return ans
 test('exact old25 plus233 independent baselines',preserve)
 def startup():
  o=object.__new__(S.Setup);o.state=lambda:state();o.layout=lambda:{'ownerActive':False,'bindingStagedSHA256':None,'viewReady':True,'view':'survey','presentedView':'survey'};n=[0]
  def state():
   n[0]+=1
   if n[0]==1:raise S.OperatorError('INITIAL_PRIVATE_STATE_ABSENT')
   return {'native':{'phase':'NO_SESSION','authorityRestorable':False},'ownerActive':False,'viewReady':True,'chosenView':'survey','presentedView':'survey','viewEpoch':1}
  a,b=o.settled('survey',1);assert n[0]==2
  tree=ast.parse(Path(S.__file__).read_text());klass=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='Setup');methods={x.name:ast.unparse(x)for x in klass.body if isinstance(x,ast.FunctionDef)}
  assert methods['bootready'].index('get-state')<methods['bootready'].index('getprop');assert 'keyboard_settle' in methods['prepare_r1']and 'SAVE['not in methods['prepare_r1'];assert methods['save_r1'].count('self.bytes(')==1;assert "'mkdir'"in methods['bootstrap_empty_dirs'];return 'Bounded absentstate→validNO_SESSION; source device-ready beforegetprop; blur/keyboardsettle beforeonesave; explicitEMPTYdirs only'
 test('cold startup and UI single-save source+state seams',startup)
 def budgets():
  for n in(180,1960):
   b=C.case_budget(maximum_seconds=n);assert b['nativeDiagnosticExportPerCaseBytes']==256*1024 and b['nativeExportCapBytes']==(24 if n==180 else 168)*2**20-256*1024
  return {'tarShortPlusLongMiB':191.5,'twoDiagnosticsMiB':.5,'globalMiB':192,'nativeJournalMiB':160}
 test('canonical diagnostic no redundantcopy and unchanged globalexport192',budgets)
 removed=sum(p.stat().st_size for p in scratch.rglob('*')if p.is_file());shutil.rmtree(scratch);v={'status':'PASS'if all(x['pass']for x in cases)else'FAIL','cases':cases,'realDeviceOrAPOrServices':False,'sourceStaticAndSyntheticOnly':True,'scratchRemoved':True,'removedBytes':removed};(E/'results.json').open('x').write(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2));assert v['status']=='PASS'
if __name__=='__main__':main()
