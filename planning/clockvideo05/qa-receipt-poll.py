"""Independent actual-function AST receipt waiting checks, no I/O or UI."""
import ast,json,hashlib,datetime,types,sys
from pathlib import Path
p=Path('planning/clockvideo05/qa-ui.py');tree=ast.parse(p.read_text());funcs=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['receipt_observation','post_tap_context','receipt_context']];assert len(funcs)==3
rows=[]
class Clock:
 def __init__(self):self.t=0;self.sleeps=[]
 def now(self):return self.t
 def sleep(self,n):assert n>=0;self.sleeps.append(n);self.t+=n
clock=Clock();ns={'time':types.SimpleNamespace(monotonic=clock.now,sleep=clock.sleep),'observation':lambda:None};exec(compile(ast.Module(body=funcs,type_ignores=[]),str(p),'exec'),ns);f=ns['receipt_observation']
def test(name,fn):
 try:fn();rows.append({'name':name,'status':'PASS'})
 except Exception as e:rows.append({'name':name,'status':'FAIL','error':type(e).__name__+': '+str(e)})
def reset():clock.t=0;clock.sleeps=[]
def expect_error(fn,msg):
 try:fn()
 except Exception as e:assert msg in str(e),(msg,str(e));return
 raise AssertionError('MISSING_REJECTION '+msg)
def valid_stale():
 reset();calls=[]
 def read():
  calls.append(clock.t)
  if len(calls)<=2:raise AssertionError('STALE_OBSERVATION')
  return {'fresh':'EXACT_ACK_CANDIDATE'}
 assert f(1,reader=read,clock=clock.now,pause=clock.sleep)=={'fresh':'EXACT_ACK_CANDIDATE'};assert len(calls)==3 and clock.t<1
test('stale_then_fresh_candidate_within_original_deadline',valid_stale)
def expiry():
 reset();calls=[]
 def read():calls.append(clock.t);raise AssertionError('STALE_OBSERVATION')
 expect_error(lambda:f(.2,reader=read,clock=clock.now,pause=clock.sleep),'STALE_UNTIL_EXISTING_RECEIPT_DEADLINE');assert clock.t<=.20000001 and len(calls)<=4
test('all_stale_expires_without_extending_deadline',expiry)
def late():
 reset()
 def read():clock.t=1.01;return {'fresh':'ACK_AFTER_DEADLINE'}
 expect_error(lambda:f(1,reader=read,clock=clock.now,pause=clock.sleep),'RECEIPT_AFTER_EXISTING_DEADLINE')
test('reader_resolves_after_deadline_cannot_return_success_candidate',late)
def errors():
 for exc in [TypeError('network'),ValueError('malformed'),AssertionError('OBSERVATION_REQUIRED'),AssertionError('WRONG_CONTEXT')]:
  reset()
  def read():raise exc
  expect_error(lambda:f(1,reader=read,clock=clock.now,pause=clock.sleep),str(exc));assert clock.sleeps==[]
test('network_parse_and_other_assertions_are_not_swallowed',errors)
def expired_start():
 reset();clock.t=1
 def read():raise RuntimeError('MUST_NOT_READ')
 expect_error(lambda:f(1,reader=read,clock=clock.now,pause=clock.sleep),'STALE_UNTIL_EXISTING_RECEIPT_DEADLINE');assert clock.sleeps==[]
test('expired_deadline_does_not_read_or_retry',expired_start)
d=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='dispatch');src=ast.get_source_segment(p.read_text(),d)
def dispatch_guards():
 assert src.count("q.adb('shell','input','tap'")==1
 assert 'receipt_observation(deadline)' in src
 # Receipt check must include origin boot, and only a stale wait can be swallowed.
 assert "receipt_context(o,n,receipt,ident)" in src and "post_tap_context(o,n,ident)"in src
 assert "'STALE_UNTIL_EXISTING_RECEIPT_DEADLINE_NO_REINPUT','RECEIPT_AFTER_EXISTING_DEADLINE_NO_REINPUT'"in src
 assert 'put(name+\'-receipt\'' in src and "receipt['status']=='ACKNOWLEDGED'" in src
 assert src.index('receipt_observation(deadline)')>src.index("q.adb('shell','input','tap'")
test('dispatch_has_single_actual_input_and_exact_receipt_boot_guard',dispatch_guards)
def contexts():
 origin={k:'same-'+k for k in ['documentId','clientId','clientEpoch','clientInstance','run','boot','modelSha256','planSha256','configId']}
 receipt=dict(origin)
 for key in origin:
  z=dict(origin);z[key]='WRONG'
  expect_error(lambda:ns['post_tap_context'](origin,z,'field-gimbal'),'CHANGED')
 for key in ['documentId','clientId','clientEpoch','clientInstance','run','boot','modelSha256','planSha256']:
  z=dict(receipt);z[key]='WRONG'
  expect_error(lambda:ns['receipt_context'](origin,origin,z,'field-gimbal'),'RECEIPT_CONTEXT_MISMATCH')
 ns['receipt_context'](origin,origin,receipt,'field-gimbal')
test('wrong_posttap_and_receipt_boot_identity_never_advance',contexts)
def transitions():
 origin={k:'same-'+k for k in ['documentId','clientId','clientEpoch','clientInstance','run','boot','modelSha256','planSha256','configId']};changed={**origin,'run':None,'boot':None}
 for ident in ['field-connect','field-close','field-reboot']:ns['receipt_context'](origin,changed,origin,ident)
 expect_error(lambda:ns['receipt_context'](origin,changed,origin,'field-tab-flight'),'CHANGED')
 # Changing client/config remains forbidden even for explicit AP run transitions.
 for ident in ['field-connect','field-close','field-reboot']:
  for key in ['documentId','clientId','clientEpoch','clientInstance','configId','modelSha256','planSha256']:
   expect_error(lambda:ns['receipt_context'](origin,{**changed,key:'WRONG'},origin,ident),'CONTEXT_CHANGED')
test('explicit_run_boot_transitions_only_keep_original_receipt_identity',transitions)

r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_RECEIPT_WAIT'if all(x['status']=='PASS'for x in rows)else'FAIL','source':str(p),'sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':rows,'scope':'Actual receipt_observation function executed via AST with fake clocks/readers; dispatch guard inspection. No ADB/UI/HTTP/server/runtime or production edits.'}
out=Path(sys.argv[1]);out.open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps(r));assert r['status'].startswith('PASS')
