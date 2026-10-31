from pathlib import Path
import importlib.util,json,hashlib,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];P=R/'planning/betaintegrated01/cockpit05-entry10/android/setup_ui.py';spec=importlib.util.spec_from_file_location('setupnew',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
O=R/'evidence/betaintegrated01-cockpit05-entry10/qa/helper-guard03';O.mkdir();g=O/'fakeguard';g.mkdir();row={'hostNs':10000000000,'freeBytes':12*2**30,'forecastFreeBytes':12*2**30+.125,'AC':False,'batteryPercent':55};launch={'scope':'ANDROID_UI_SUBSET_NO_AP_NO_FLIGHT','serial':'emulator-5582','maximumSeconds':900,'guardianPID':111,'guardianProcessStart':'G','pid':222,'processStart':'E','processGroup':222,'guardianSourceSHA256':hashlib.sha256(m.GUARD_SOURCE.read_bytes()).hexdigest()};ad={'scope':'ANDROID_UI_SUBSET_NO_AP_NO_FLIGHT','metadataBudgetBytes':32*2**20,'maximumSeconds':900};cases=[]
def read(p):return launch if p.name=='launch.json'else ad
def ps(pid,key):return'00:20'if key=='etime'else'G'if pid==111 else'E'
def run(name,mut=None,fail=False):
 global row
 value=dict(row)
 if mut:mut(value)
 (g/'guard.jsonl').write_text(json.dumps(value)+'\n')
 try:m.guard_ready(mutation=True);ok=not fail
 except(m.OperatorError,KeyError,TypeError,ValueError):ok=fail
 cases.append({'id':name,'pass':ok})
with patch.object(m,'GUARD',g),patch.object(m,'read',read),patch.object(m,'ps_field',ps),patch.object(m.os,'getpgid',lambda pid:222),patch.object(m.time,'monotonic_ns',lambda:11000000000),patch.object(m,'allocated',lambda p:0):
 run('fractionalRealForecastPositive')
 for label,val in [('NaN',float('nan')),('Inf',float('inf')),('bool',True),('belowreserve',10*2**30+256*2**20-.01)]:run(label,lambda r,v=val:r.update(forecastFreeBytes=v),True)
 run('futureSample',lambda r:r.update(hostNs=12000000000),True);run('staleSample',lambda r:r.update(hostNs=8000000000),True);run('battery20',lambda r:r.update(batteryPercent=20),True)
 with patch.object(m,'ps_field',lambda pid,key:'16:00'if key=='etime'else ps(pid,key)):run('deadlineHeadroom',fail=True)
 with patch.object(m,'allocated',lambda p:32*2**20):run('wholeMetadataReserve',fail=True)
 (g/'closure.json').write_text('{}');run('closedGuardian',fail=True)
assert all(t['pass']for t in cases)
report={'status':'PASS_INDEPENDENT_HELPER_GUARD_MOCK_NOT_PROCESS_OR_ANDROID','cases':cases,'sourceSHA256':hashlib.sha256(P.read_bytes()).hexdigest(),'source':'Currentfractionalforecastfixguardsrealfloatwithoutfloorrelaxation; monkeypatchedread-onlyPID/time only no commands','ADBCalls':0,'processesStarted':0};(O/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(report['status'],len(cases))
