"""Bounded orchestration regression against actual selected driver/predicate."""
from pathlib import Path
from unittest.mock import patch
import ast,json,subprocess,sys
R=Path(__file__).resolve().parents[4];sys.path[:0]=[str(R/'planning/vidlife12/runtime/source'),str(R)]
from aeris_runtime.public_ui_workload import PublicUIDriver
from aeris_runtime import public_ui_workload
old=R/'planning/vidlife12/runtime/scenario-app09.py';new=R/'planning/vidlife12/runtime/scenario-app09-r02.py';a="seconds=30,poll_seconds=.5,description='DISARMED_READ_ONLY_NAVIGATION_READINESS'";b=a.replace('seconds=30','seconds=60');assert old.read_text().count(a)==1 and new.read_text()==old.read_text().replace(a,b)
node=json.loads(subprocess.run(['/usr/local/bin/node',str(Path(__file__).with_suffix('.mjs'))],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,text=True).stdout);assert node['status']=='PASS'and node['badEKFRejected']and node['expiredActualFreshnessRejected']
tree=ast.parse(new.read_text());call=next(x for x in ast.walk(tree)if isinstance(x,ast.Call)and any(k.arg=='description'and isinstance(k.value,ast.Constant)and k.value.value=='DISARMED_READ_ONLY_NAVIGATION_READINESS'for k in x.keywords));predicate=eval(compile(ast.Expression(call.args[0]),str(new),'eval'));seconds=next(k.value.value for k in call.keywords if k.arg=='seconds');assert seconds==60
checks=3;out=[]
def run(budget,health='healthy'):
 host=[0.0];driver=PublicUIDriver.__new__(PublicUIDriver);driver.clock=lambda:int(host[0]*1e9);driver.check=lambda:None
 def state():
  ap_boot=10+host[0]*.75;return{'flight':{'navigationReadiness':{'phase':'DISARMED_READ_ONLY_NAVIGATION_READINESS','ready':ap_boot>=41 and health=='healthy'}}}
 driver.state=state
 with patch.object(public_ui_workload.time,'sleep',side_effect=lambda delta:host.__setitem__(0,host[0]+delta)):
  try:PublicUIDriver.wait(driver,predicate,seconds=budget,description='DISARMED_READ_ONLY_NAVIGATION_READINESS',observe_native=False,poll_seconds=.5);passed=True
  except TimeoutError as e:assert str(e)=='PUBLIC_UI_WAIT_DISARMED_READ_ONLY_NAVIGATION_READINESS';passed=False
 return{'budgetHostSeconds':budget,'health':health,'passed':passed,'elapsedHostSeconds':host[0],'simulatedAPBootSeconds':10+host[0]*.75}
for budget,health,expected in[(30,'healthy',False),(seconds,'healthy',True),(seconds,'badEKF',False),(seconds,'expiredFreshness',False)]:
 result=run(budget,health);assert result['passed']is expected;out.append(result);checks+=1
print(json.dumps({'format':'aeris-cold-navigation-r02-bounded-initialization-mock','status':'PASS','checks':checks+node['checks'],'actualMethods':['PublicUIDriver.wait','scenario_r02_actual_lambda','FlightHealth.receive','FlightHealth.assess'],'scenarios':out,'fixtureAssumptions':{'initialAPBootSeconds':10,'simulatedAPSecondsPerHostSecond':.75,'healthyOnlyAfterAPBootSeconds':41,'source':'SYNTHETIC_REGRESSION_NOT_LIVE_PERFORMANCE_PREDICTION'},'onlySourceDifference':'Bounded startup navigation wait30→60 hostseconds','safetyGuardPolicyChanged':False,'SDKOrActorsStarted':False,'functionalAndroidVideoAccepted':False}))
