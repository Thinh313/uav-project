"""Pure helper/decision checks. NO ADB/device/process call; no product source edit."""
from pathlib import Path
import sys,json,hashlib,importlib,subprocess,ast
from unittest.mock import patch
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent;E=R/'evidence/betaintegrated01-cockpit05-soak/native';S=R/'planning/betaintegrated01/m1cockpit04/android';checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
base=(D/'cockpit05_android_operator.py').read_text();root=(D/'cockpit05_root_operator.py').read_text()
check('BaseOnlyPackageConstantChanged',base.replace("PACKAGE = 'vn.rtr.aeris.cockpit05'","PACKAGE = 'vn.rtr.aeris.cockpit04'")==(S/'android_operator.py').read_text())
check('RootOnlyLocalImportChanged',root.replace('from cockpit05_android_operator import','from android_operator import')==(S/'root_operator.py').read_text())
check('NoResidualOldPackageTarget','vn.rtr.aeris.cockpit04'not in base+root)
compile(base,str(D/'cockpit05_android_operator.py'),'exec');compile(root,str(D/'cockpit05_root_operator.py'),'exec');check('SyntaxInMemoryNoBytecodeCache',True)
external=[]
def denied(*a,**k):external.append((a,k));raise AssertionError('SUBPROCESS_NOT_ALLOWED_IN_MOCK')
sys.path.insert(0,str(D))
with patch.object(subprocess,'run',denied),patch.object(subprocess,'Popen',denied):
 A=importlib.import_module('cockpit05_android_operator');B=importlib.import_module('cockpit05_root_operator');check('ImportNoExternalCommands',not external);check('NamespacedLocalBaseResolved',B.AndroidOperator is A.AndroidOperator);check('Owned05EmulatorTarget',A.PACKAGE=='vn.rtr.aeris.cockpit05'and A.SERIAL=='emulator-5582'and A.ACTIVITY=='vn.rtr.aeris.cockpit05/.CockpitActivity')
 class Fake(A.AndroidOperator):
  def __init__(self,value):self.run='current-run';self.generation='current-generation';self.value=value;self.calls=[]
  def command(self,args,**kwargs):
   self.calls.append(args)
   if args==['shell','cat','/proc/uptime']:return b'101.00 0\n',b'',0,E
   check('NativeCheckpointReadOnlyCorrectTarget',args==['shell','run-as',A.PACKAGE,'cat','files/latest-state.json'])
   return json.dumps(self.value).encode(),b'',0,E
 state={'run':'current-run','generation':'current-generation','closed':False,'firstFailure':None,'preflightReady':True,'releaseState':'NONE','flight':{'heartbeatMs':100000,'positionMs':100000,'armed':False,'mode':4,'landedState':1},'input':{'consent':True}}
 f=Fake(state);snapshot=json.dumps(state,sort_keys=True);check('FreshCurrentContextAccepted',f._fresh_state()==state)
 for label,change in [('foreignRun',{'run':'old'}),('foreignGeneration',{'generation':'old'})]:
  v={**state,**change}
  try:Fake(v).state();accepted=True
  except A.OperatorError:accepted=False
  check(label+'Refused',not accepted)
 for label,field,value in [('staleHB','heartbeatMs',98000),('futurePosition','positionMs',102000),('booleanAge','positionMs',True)]:
  v={**state,'flight':{**state['flight'],field:value}}
  try:Fake(v)._fresh_state();accepted=True
  except A.OperatorError:accepted=False
  check(label+'Refused',not accepted)
 check('ARMNeedsCurrentConsentAndPreflight',f._native_ready('control01-arm',state)and not f._native_ready('control01-arm',{**state,'input':{'consent':False}}))
 check('ClosedAndFailedRefuse',not f._native_ready('control01-arm',{**state,'closed':True})and not f._native_ready('control01-arm',{**state,'firstFailure':'x'}))
 armed={**state,'flight':{**state['flight'],'armed':True,'landedState':2,'homeConfirmed':True,'hoverObservedMs':999}}
 check('LOITERObservedHoverThresholdUnchanged',not f._native_ready('control01-loiter',armed)and f._native_ready('control01-loiter',{**armed,'flight':{**armed['flight'],'hoverObservedMs':1000}}))
 check('LANDRequiresRCRelease',not f._native_ready('control01-land',{**armed,'rcOverrideActiveLocally':True})and f._native_ready('control01-land',{**armed,'rcOverrideActiveLocally':False}))
 check('ReadinessNeverMutatesOrGrants',json.dumps(state,sort_keys=True)==snapshot)
 check('NoExternalCommandsOrDeviceActions',not external)
report={'status':'PASS_PURE_STATIC_MOCK_NOT_DEVICE_QUALIFICATION','groups':len(checks),'cases':checks,'ADBCalls':0,'processesLaunched':0,'nativeAuthorityCreated':False,'sourceSHA256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [D/'cockpit05_android_operator.py',D/'cockpit05_root_operator.py']}}
(E/'static-mock-check01.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','groups':len(checks),'ADBCalls':0}))
