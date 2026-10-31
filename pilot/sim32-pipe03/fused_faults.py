"""Actual SITL guard gate before transport optimization; no retries."""
from pathlib import Path
import subprocess,sys,os,json,shutil,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/sim32-pipe03'
env=dict(os.environ,SIM32_ENGINE='fused',SIM32_SPEEDUP='1',AERIS_INSTRUMENT='1',SIM32_TEST_PAUSE_AT_FRAME='6000')
results=[]
for ms in [3200,1400,450,550,900]:
    name=f'fguard{ms}a1'
    assert shutil.disk_usage(R).free>20*2**30+768*2**20
    with(E/(name+'-console.txt')).open('x')as f:
        start=subprocess.run([sys.executable,'-B','pilot/sim32-pipe03/runtime.py','start',name,'offset','gust'],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=30)
        if start.returncode:raise RuntimeError('Start failed '+name)
        qa=subprocess.run(['node','pilot/sim32-pipe03/fault_probe.mjs',name,str(ms)],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=45)
    result=json.loads((E/'runs'/name/'fault-probe.json').read_text());results.append({'run':name,'status':result['status'],'exitCode':qa.returncode})
    print(name,result['status'],flush=True)
    if qa.returncode or result['status']!='PASS':break
with(E/'fused-faults.json').open('x')as f:json.dump({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if len(results)==5 and all(x['status']=='PASS'for x in results)else 'FAIL','results':results,'optimizationAuthorizedOnlyAfterGate':True},f,indent=2);f.write('\n')
