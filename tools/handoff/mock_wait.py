"""Portable, read-only mock of the selected navigation wait. No SDK or vehicle."""
from pathlib import Path
from unittest.mock import patch
import ast,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'planning/vidlife12/runtime/source'))
from aeris_runtime.public_ui_workload import PublicUIDriver
from aeris_runtime import public_ui_workload
script=ROOT/'planning/vidlife12/runtime/scenario-app09-r02.py'
call=next(n for n in ast.walk(ast.parse(script.read_text())) if isinstance(n,ast.Call) and any(k.arg=='description' and isinstance(k.value,ast.Constant) and k.value.value=='DISARMED_READ_ONLY_NAVIGATION_READINESS' for k in n.keywords))
predicate=eval(compile(ast.Expression(call.args[0]),str(script),'eval'))
budget=next(k.value.value for k in call.keywords if k.arg=='seconds')
assert budget==60
rows=[]
for seconds,can_converge,expected in [(30,True,False),(60,True,True),(60,False,False)]:
 now=[0.0];driver=PublicUIDriver.__new__(PublicUIDriver);driver.clock=lambda:int(now[0]*1e9);driver.check=lambda:None
 driver.state=lambda:{'flight':{'navigationReadiness':{'phase':'DISARMED_READ_ONLY_NAVIGATION_READINESS','ready':can_converge and 10+now[0]*.75>=41}}}
 with patch.object(public_ui_workload.time,'sleep',side_effect=lambda dt:now.__setitem__(0,now[0]+dt)):
  try:driver.wait(predicate,seconds=seconds,poll_seconds=.5,observe_native=False,description='DISARMED_READ_ONLY_NAVIGATION_READINESS');passed=True
  except TimeoutError:passed=False
 assert passed is expected
 rows.append({'seconds':seconds,'syntheticConvergenceEnabled':can_converge,'passed':passed})
print(json.dumps({'status':'PASS','kind':'MOCK_ONLY_NOT_LIVE_CONVERGENCE','cases':rows,'actorsStarted':False}))
