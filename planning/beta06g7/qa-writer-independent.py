"""Independent bounded-file/ledger tests; no actual processes, ADB or runtime effects."""
from pathlib import Path
import importlib.util,json,hashlib,os,sys,shutil,stat
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation07'
name=sys.argv[1];assert name.startswith('qa-writer-independent-')and name.endswith('.json')and '/'not in name
output=E/name;assert not output.exists()
scratch=E/(name[:-5]+'-scratch');assert not scratch.exists();scratch.mkdir()
def module(name,p):
 s=importlib.util.spec_from_file_location(name,R/p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
q=module('qa_independent_g7_quota','pilot/beta06g7/quota.py')
b=module('qa_independent_g7_writer','planning/beta06g7/qa-native-budget.py')
rt=module('qa_independent_g7_runtime','pilot/beta06g7/flight/runtime.py')
paths=['pilot/beta06g7/quota.py','pilot/beta06g7/quota-policy.json','pilot/beta06g7/flight/runtime.py','planning/beta06g7/qa-native-budget.py']
hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest()for p in paths};groups=[]
def case(name,fn):
 try:fn();groups.append({'name':name,'status':'PASS'})
 except BaseException as e:groups.append({'name':name,'status':'FAIL','error':str(e)[:400]})
def refuse(fn):
 try:fn()
 except BaseException:return
 raise AssertionError('Expected refusal before write')
def fixture(label):
 root=scratch/label;scope=root/'evidence/beta06/generation07';scope.mkdir(parents=True)
 q.R=root;q.E=scope;b.R=root;b._quota=q;b._tickets.clear();return scope
def reserve(**kwargs):return q.reserve_write(claim_id=kwargs.pop('claim_id','one'),category=kwargs.pop('category','native'),entries=kwargs.pop('entries',1),bytes=kwargs.pop('bytes',0),**kwargs)
def ledger(scope):return scope/'quota-native-ledger.jsonl'
def corruption():
 for label,edit in [('negative',lambda r:r.update(entries=-1)),('bool',lambda r:r.update(bytes=True)),('badsha',lambda r:r.update(hash='0'*64)),('badprevious',lambda r:r.update(previous='x')),('extra',lambda r:r.update(extra=1))]:
  scope=fixture('corrupt-'+label);reserve();r=json.loads(ledger(scope).read_text());edit(r)
  if label in ['negative','bool','extra']:
   body={k:v for k,v in r.items()if k!='hash'};r['hash']=hashlib.sha256(json.dumps(body,separators=(',',':'),sort_keys=True).encode()).hexdigest()
  raw=(json.dumps(r)+'\n').encode();ledger(scope).write_bytes(raw);refuse(lambda:reserve(claim_id='two'));assert ledger(scope).read_bytes()==raw
case('ledger_corrupt_negative_bool_hash_previous_extra_refused',corruption)
def replay():
 scope=fixture('replay');reserve();raw=ledger(scope).read_bytes();refuse(lambda:reserve());assert ledger(scope).read_bytes()==raw
case('write_claim_replay_refused_without_append',replay)
def link_cases():
 for which in ['quota-native-ledger.lock','quota-native-ledger.jsonl']:
  scope=fixture(which);target=scope/'target';target.write_bytes(b'untouched');(scope/which).symlink_to(target);refuse(lambda:reserve());assert target.read_bytes()==b'untouched'
case('ledger_and_lock_symlink_refused',link_cases)
def near_bytes():
 scope=fixture('byte-close');p=q.load_policy()['categories']['native'];normal=p['bytes']-p['closureBytes'];reserve(bytes=normal-4096);reserve(bytes=2048,claim_id='normal-small');before=ledger(scope).read_bytes();refuse(lambda:reserve(bytes=4096,claim_id='normal-short'));assert ledger(scope).read_bytes()==before
 reserve(bytes=1024*1024,claim_id='closure:one',closure=True);refuse(lambda:reserve(bytes=p['closureBytes'],claim_id='closure:too-much',closure=True))
case('normal_byte_exhaustion_still_permits_reserved_closure_bytes',near_bytes)
def near_entries():
 scope=fixture('entry-close');p=q.load_policy()['categories']['native'];reserve(entries=p['normalFiles']);refuse(lambda:reserve(claim_id='normal-over'));reserve(entries=p['closureEntries'],claim_id='closure:close',closure=True);refuse(lambda:reserve(entries=p['entries'],claim_id='closure:over',closure=True))
case('normal_entry_exhaustion_still_permits_reserved_closure_entries',near_entries)
def png_subcounts():
 fixture('png-counts');p=q.load_policy()['categories']['screenshots']
 for kind in ['dispatch','prepare','direct']:
  for i in range(p[kind]):reserve(category='screenshots',claim_id='png-'+kind+':'+str(i))
  refuse(lambda:reserve(category='screenshots',claim_id='png-'+kind+':over'))
 refuse(lambda:reserve(category='screenshots',claim_id='png-bad:x'))
case('png_160_48_32_subcounts_without_allocating_images',png_subcounts)
def future_native_files():
 for A,H in [(4,2),(1,0)]:
  fixture('future-native-'+str(A));p=q.load_policy();c=p['futureRecipe']['nativeFiles'];future=c[0]*A+c[1]*H+c[2];reserve(entries=p['categories']['native']['normalFiles']-future,claim_id='already-normal');proof=q.check_native_future(A,H);assert proof['normalFiles']['used']+proof['normalFiles']['future']==512
  reserve(claim_id='one-more-normal');refuse(lambda:q.check_native_future(A,H))
case('first_and_late_native_future512file_exact_and_one_short',future_native_files)
def future_png():
 for kind in ['dispatch','prepare','direct']:
  fixture('future-png-'+kind);p=q.load_policy();A,H=4,2;c=p['futureRecipe']['pngSubtypes'][kind];future=c[0]*A+c[1]*H+c[2];allowance=p['categories']['screenshots'][kind]-future
  for i in range(allowance):reserve(category='screenshots',claim_id='png-'+kind+':existing-'+str(i))
  q.check_native_future(A,H);reserve(category='screenshots',claim_id='png-'+kind+':one-more');refuse(lambda:q.check_native_future(A,H))
case('all_three_future_png_subtypes_exact_and_one_short_no_images',future_png)
def future_bad_counters():
 fixture('future-bad');
 for A,H in [(True,0),(-1,0),(5,0),(0,3),(0.5,1)]:refuse(lambda:q.check_native_future(A,H))
case('future_native_original_counter_types_bounds_refuse',future_bad_counters)
def tickets():
 scope=fixture('tickets');first=scope/'receipt.json';other=scope/'uncertain.json';b.preclaim(first,128,kind='receipt');b.alias(first,other);b.write_bytes(other,b'{}',maximum=128);refuse(lambda:b.write_bytes(first,b'{}',maximum=128));assert not first.exists()and other.read_bytes()==b'{}'
case('mutually_exclusive_receipt_alias_consumes_one_ticket',tickets)
def scoped():
 scope=fixture('scope');refuse(lambda:b.preclaim(scope.parent/'outside.json',128));target=scope/'real';target.mkdir();(scope/'linked').symlink_to(target,target_is_directory=True);refuse(lambda:b.preclaim(scope/'linked'/'new.json',128));assert not(target/'new.json').exists()
case('writer_outside_scope_and_ancestor_symlink_refused',scoped)
def bounded():
 scope=fixture('bounded');p=scope/'out.bin'
 with b.BoundedFile(p,4,binary=True)as f:f.write(b'abcd');refuse(lambda:f.write(b'e'))
 assert p.read_bytes()==b'abcd';refuse(lambda:b.write_bytes(scope/'before.bin',b'12345',maximum=4));assert not(scope/'before.bin').exists()
case('serialized_bytes_overflow_refuses_without_silent_truncation',bounded)
def capture_count():
 old=rt.Capture;calls=[]
 try:
  rt.Capture=lambda argv,p,budget:calls.append(str(p))or object();runner=rt.Runner(scratch/'not-created')
  for i in range(423):runner.capture([],str(i))
  refuse(lambda:runner.capture([],'normal-over'));runner.closing=True
  for label in ['closure-before','closure-stop','wait','terminal-inspect']:runner.capture([],label)
  refuse(lambda:runner.capture([],'closure-before'));assert len(calls)==427
 finally:rt.Capture=old
case('423_normal_captures_leave_all_four_owned_cleanup_commands',capture_count)
def serialized_metadata():
 scope=fixture('serialized');p=scope/'test-result.json';d={'x':['a']*1000};assert len(json.dumps(d).encode())<8192 and len(json.dumps(d,indent=2).encode())>8192;refuse(lambda:rt.put(p,d));assert not p.exists()
case('result_limit_checks_actual_pretty_serialized_bytes_before_open',serialized_metadata)
def fixed_closure():
 scope=fixture('fixed-close');run=scope/'run';run.mkdir();(run/'request.json').write_text('{}');(run/'fixed.bin').write_bytes(b'x'*(2*2**20-256*1024-1024));refuse(lambda:rt.put(run/'other.json',{'x':'x'*2048}));assert not(run/'other.json').exists();rt.put(run/'closure.json',{'closed':True});assert(run/'closure.json').is_file()
case('ap_fixed_near_normal_exhaustion_leaves_closure_record',fixed_closure)
try:
 for p,h in hashes.items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,'source changed during QA: '+p
finally:shutil.rmtree(scratch)
report={'status':'PASS_SOURCE_MOCK_ONLY'if all(g['status']=='PASS'for g in groups)else'FAIL_SOURCE_MOCK_ONLY','sourceHashes':hashes,'independentGroups':len(groups),'groups':groups,'temporaryFixtureRemoved':str(scratch.relative_to(R)),'noImageOrDiskFill':True,'actualRuntimeActions':0,'noAPAndroidOrPhysicalAcceptance':True}
with output.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(output),'status':report['status'],'groups':len(groups),'failed':[g for g in groups if g['status']!='PASS']}))
