"""Independent restart provenance policy using actual report schema and virtual bytes only."""
from pathlib import Path
import importlib.util,json,hashlib,copy,datetime
p=Path('planning/beta06g3/qa-restart-proof.py');s=importlib.util.spec_from_file_location('independent_restart_proof',p);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
N='s'+'1'*20;F='s'+'2'*20;A='a'*64;B='b'*64
def sha(b):return hashlib.sha256(b).hexdigest()
class VPath:
 def __init__(self,s):self.s=s
 def __truediv__(self,s):return VPath(self.s+'/'+str(s))
 def __str__(self):return self.s
 def glob(self,pattern):return[VPath(k)for k in data if k.startswith('/G2/flight/runs/')and k.endswith('/request.json')]
data={}
def jb(v):return json.dumps(v,separators=(',',':')).encode()
def raw(run,fault=False):
 rows=[{'kind':'SESSION','data':{},'hostNs':'1000000'if not fault else'10000000'}]
 if fault:rows +=[{'kind':'FIELD01_INTENT','data':{'route':'cut','request':{'confirmSimulation':True}},'hostNs':'11000000'},{'kind':'FIELD02_C2_SOCKET_CUT','data':{'actualTCPDisconnect':True},'hostNs':'12000000'}]
 rows.append({'kind':'LINK_CLOSE','data':{},'hostNs':'2000000'if not fault else'13000000'});head='';out=b''
 for i,r in enumerate(rows):
  body={**r,'n':i+1,'previous':head};b=jb(body);head=sha(b);out+=b[:-1]+b',"sha256":"'+head.encode()+b'"}\n'
 return out,head,len(rows)
def setup():
 global data
 data={};reports={}
 for run,fault in[(N,False),(F,True)]:
  root='/G2/flight/runs/'+run;rb,head,count=raw(run,fault);binding={'modelSha256':A,'planSha256':B,'documentSha256':'c'*64,'missionSha256':'d'*64,'modelRevision':7};request={'run':run,'mode':'sitl','instance':'host','binding':binding,'source':'HOST_NODE_GCS_SIM_ONLY','at':'MOCK_FIXTURE'};review={'run':run,'mode':'sitl',**binding,'rawHead':head,'rawRecords':count,'accepted':not fault,'aborted':fault,'execution':{'complete':not fault},'failure':'INJECTED_CUT_NO_AUTHORITY_RESTORE'if fault else None};inputs={'raw.jsonl':rb,'review.json':jb(review),'request.json':jb(request),'closure.json':jb({'stopped':True,'error':None})}
  for name,b in inputs.items():data[root+'/'+name]=b
  reports[run]={'run':run,'status':'PASS_ACTUAL_TCP_CUT_DURABLE_LIVE_LEASE_INVALIDATION_INCOMPLETE_FLIGHT'if fault else'PASS_ACTUAL_RAW_NOMINAL_EXECUTION_GENERIC_SITL','input':{n:{'sha256':sha(b),'bytes':len(b)}for n,b in inputs.items()},'errors':[]}
 reports[N].update(canonicalSharedReplay={'executionVerified':True},independentChecks={'chronology':{'actualArmedAutoHeartbeats':1,'autoCommandRecords':[1],'lastHeartbeatArmed':False,'lastGroundState':1},'wire':{'parameterWrites':0,'readbackCommandsExact':True}})
 data['/ROOT/evidence/beta06/generation03/fixture-WAL.jsonl']=b'MOCK_WAL_BYTES_ONLY'
 reports[F].update(checks={'liveLeaseProofs':[{'unexpiredRemainingAtPreMs':5000}],'afterCutWireRecords':0,'laterLeaseRegains':0,'laterOldRunCommandIntents':0});reports[F]['input']['wal']={'path':'evidence/beta06/generation03/fixture-WAL.jsonl','sha256':sha(data['/ROOT/evidence/beta06/generation03/fixture-WAL.jsonl']),'bytes':len(data['/ROOT/evidence/beta06/generation03/fixture-WAL.jsonl'])}
 data['/G2/qa-nominal.json']=jb(reports[N]);data['/G2/qa-fault.json']=jb(reports[F]);return reports
g.E=VPath('/G2');g.R=Path('/ROOT');g.blob=lambda p,bound=96*2**20:data[str(p)]
def authorize():return g.authorize('/G2/qa-nominal.json','/G2/qa-fault.json')
def edit_report(which,fn):
 key='/G2/qa-'+which+'.json';x=json.loads(data[key]);fn(x);data[key]=jb(x)
def edit_input(run,name,fn):
 key='/G2/flight/runs/'+run+'/'+name;x=json.loads(data[key]);fn(x);data[key]=jb(x);edit_report('nominal'if run==N else'fault',lambda r:r['input'].__setitem__(name,{'sha256':sha(data[key]),'bytes':len(data[key])}))
def refuses(fn):
 try:fn()
 except(AssertionError,KeyError,ValueError):return
 raise AssertionError('EXPECTED_RESTART_REFUSAL')
rows=[]
def test(name,fn):
 try:setup();fn();rows.append({'name':name,'status':'PASS'})
 except Exception as e:rows.append({'name':name,'status':'FAIL','error':str(e)})
def positive():
 r=authorize();assert r['nominalRun']==N and r['faultRun']==F and r['modelSha256']==A and r['planSha256']==B and r['noAuthorityGranted']and r['noHostOrClockReset']
test('exact_actual_nested_request_binding_schema_and_distinct_closed_runs_positive_mock',positive)
tests=[
 ('nominal_not_accepted',lambda:edit_input(N,'review.json',lambda r:r.update(accepted=False))),
 ('fault_failed_preparation_not_deliberate_cut',lambda:edit_input(F,'review.json',lambda r:r.update(failure='RX_CONTEXT_OR_CLOCK'))),
 ('nominal_source_only_status',lambda:edit_report('nominal',lambda r:r.update(status='MOCK_PASS'))),
 ('no_canonical_execution',lambda:edit_report('nominal',lambda r:r['canonicalSharedReplay'].update(executionVerified=False))),
 ('request_nested_plan_changed',lambda:edit_input(F,'request.json',lambda r:r['binding'].update(planSha256='e'*64))),
 ('fault_livelease_missing',lambda:edit_report('fault',lambda r:r['checks'].update(liveLeaseProofs=[]))),
 ('postcutwire_present',lambda:edit_report('fault',lambda r:r['checks'].update(afterCutWireRecords=1))),
 ('later_authority_regain',lambda:edit_report('fault',lambda r:r['checks'].update(laterLeaseRegains=1))),
 ('actual_WAL_changed',lambda:data.__setitem__('/ROOT/evidence/beta06/generation03/fixture-WAL.jsonl',b'CHANGED')),
 ('later_third_preparation_cannot_borrow_oldproof',lambda:data.__setitem__('/G2/flight/runs/s'+'3'*20+'/request.json',jb({'run':'s'+'3'*20,'mode':'sitl'}))),
 ('closure_error',lambda:edit_input(F,'closure.json',lambda r:r.update(error='OWNED_DEADLINE'))),
 ('raw_bytes_tamper',lambda:data.__setitem__('/G2/flight/runs/'+F+'/raw.jsonl',b'changed\n')),
]
for name,mutation in tests:
 def f(mutation=mutation):mutation();refuses(authorize)
 test(name,f)
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_RESTART_PROVENANCE_VIRTUAL_BYTES_MOCK_ONLY'if all(r['status']=='PASS'for r in rows)else'FAIL','sources':{str(p):sha(p.read_bytes())},'rows':rows,'scope':'Actual authorize/exact_run_inputs/report functions; virtual files use actual nested request.binding and hashed raw/report format. These synthetic reports are not real nominal/lease/cut proof. No filesystem input fixture, AP, subprocess, UI, listener or authority operation.'};out=Path('evidence/beta06/generation03/qa-restart-proof-mock04.json');out.open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'groups':len(rows),'failures':[r for r in rows if r['status']=='FAIL']}));assert result['status'].startswith('PASS')
