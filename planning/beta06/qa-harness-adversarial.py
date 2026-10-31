"""Independent actual AST checks for cut, native handoff and clock/parent fences."""
from pathlib import Path
import ast,json,math,hashlib,datetime,re,types,importlib.util,sys,copy
uiPath=Path('planning/beta06/qa-ui.py');uTree=ast.parse(uiPath.read_text());phase=next(x for x in uTree.body if isinstance(x,ast.FunctionDef)and x.name=='phase_policy');ns={};exec(compile(ast.Module(body=[phase],type_ignores=[]),str(uiPath),'exec'),ns);rows=[]
def test(n,fn):
 try:fn();rows.append({'name':n,'status':'PASS'})
 except Exception as e:rows.append({'name':n,'status':'FAIL','error':str(e)})
def reject(fn,kind=(AssertionError,ValueError)):
 try:fn()
 except kind:return
 raise AssertionError('MISSING_REJECTION')
o={'run':'s'+'a'*20,'boot':'BOOT','modelSha256':'1'*64,'planSha256':'2'*64,'clientId':'CLIENT','clientEpoch':1,'clientInstance':'INSTANCE','phase':'AUTO','payloadSelection':{'stationId':'STATION','deviceId':'PAYLOAD'}}
lease={**{k:o[k]for k in ['modelSha256','planSha256','clientId','clientEpoch','clientInstance']},'flightRun':o['run'],'flightBoot':'BOOT','stationId':'STATION','payloadId':'PAYLOAD','untilHostMonoMs':10100,'remainingMs':10000}
s={'flight':{'positionAgeMs':1,'latestPosition':{'relativeHomeM':10},'live':{'stage':'AUTO','mode':'AUTO','armed':True}},'payloadLeaseObservation':{'observedAtHostMonoMs':100,'leases':[lease]}}
def cuts():
 for ident in ['field-cut','field-reboot']:
  ns['phase_policy']('DISARMED',o,ident,s)
  for change in [('positionAgeMs',1001),('latestPosition',{'relativeHomeM':5})]:
   z=copy.deepcopy(s);z['flight'][change[0]]=change[1];reject(lambda:ns['phase_policy']('DISARMED',o,ident,z))
  for key,value in [('remainingMs',4999),('clientInstance','WRONG'),('payloadId','WRONG'),('flightBoot','WRONG')]:
   z=copy.deepcopy(s);z['payloadLeaseObservation']['leases'][0][key]=value;reject(lambda:ns['phase_policy']('DISARMED',o,ident,z))
 test=True
test('cut_and_reboot_require_fresh_airborne_exact_current_live_lease',cuts)
def allowlists():
 f=next(x for x in uTree.body if isinstance(x,ast.FunctionDef)and x.name=='dispatch');body=[]
 for q in f.body:
  if isinstance(q,ast.Assign):break
  body.append(q)
 f2=copy.deepcopy(f);f2.name='precheck';f2.body=body;loc={'re':re};exec(compile(ast.Module(body=[f2],type_ignores=[]),str(uiPath),'exec'),loc);fn=loc['precheck']
 for ident in ['field-export-workspace','field-import-workspace','field-raw-s'+'a'*20,'field-capture-export-capture-12345678-1234-1234-1234-123456789abc-'+'a'*12,'field-delivery-file-s'+'a'*20+'-index-json']:
  fn('01','FAKE',ident,'NAME',handoff_only=True)
 for ident in ['field-arm','field-cut','field-reboot','field-connect','field-qa-bad-sha']:
  reject(lambda:fn('01','FAKE',ident,'NAME',handoff_only=True))
 fn('01','FAKE','field-qa-bad-sha','NAME',diagnostic_only=True)
 for ident in ['field-arm','field-cut','field-reboot']:reject(lambda:fn('01','FAKE',ident,'NAME',diagnostic_only=True))
 for ident in ['field-arm','field-connect']:reject(lambda:fn('01','FAKE',ident,'NAME'))
test('actual_native_picker_and_diagnostic_allowlists_do_not_waive_flight_input_fences',allowlists)
def parent():
 p=Path('planning/beta06/qa-runtime.py');t=ast.parse(p.read_text());a=next(x for x in ast.walk(t)if isinstance(x,ast.Assert)and isinstance(x.msg,ast.Constant)and x.msg.value=='PERSISTENT_ROOT_REQUIRED');code=compile(ast.Expression(a.test),str(p),'eval');assert eval(code,{'root_pid':123,'os':types.SimpleNamespace(getppid=lambda:123)});assert not eval(code,{'root_pid':123,'os':types.SimpleNamespace(getppid=lambda:1)});assert not eval(code,{'root_pid':None,'os':types.SimpleNamespace(getppid=lambda:123)});s=p.read_text();assert "os.kill(root_pid,0)"in s and "assert require_permit is True"in s and "PERSISTENT_ROOT_PID_ANCHOR_REQUIRED"in s
 test=True
test('runtime_requires_exact_live_parent_and_nonoptional_prelaunch_permit',parent)
def nativeclock():
 p=Path('planning/beta06/qa-device-actions.py');t=ast.parse(p.read_text());f=next(x for x in t.body if isinstance(x,ast.FunctionDef)and x.name=='journal_chain');loc={'json':json,'hashlib':hashlib};exec(compile(ast.Module(body=[f],type_ignores=[]),str(p),'exec'),loc);head='ROOT';lines=[]
 for i,time in enumerate([1000000,10,11],1):
  body=json.dumps({'seq':i,'previous':head,'elapsedMs':time,'kind':'MOCK','data':{}},separators=(',',':'));head=hashlib.sha256(body.encode()).hexdigest();lines.append((json.dumps({'body':body,'sha256':head})+'\n').encode())
 before=loc['journal_chain'](lines[0]);after=loc['journal_chain'](b''.join(lines));app=loc['journal_chain'](b''.join(lines[1:]),previous=before['head'],start_seq=1,ordered=True);assert after['records']==3 and app['firstElapsedMs']==10 and app['lastElapsedMs']==11
 text=p.read_text();assert 'ordered=same_boot' in text and 'SAME_BOOT_JOURNAL_ELAPSED_ORDER'not in text and 'GUEST_BOOT_CHANGED_DURING_SNAPSHOT'in text
 test=True
test('native_chain_preserves_prefix_without_historical_elapsed_boundary_assumption',nativeclock)
p=Path('planning/beta06/qa-root-controller.py');sp=importlib.util.spec_from_file_location('qa_beta_harness_controller',p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)
def sequence():
 ctl=m.Controller('01',boot_reader=lambda:'BOOT',clock=lambda:0);seen=[]
 def action(c):
  seen.append(c['target'])
  if c['target']=='STOP':raise AssertionError('KNOWN_FAILURE')
  return {'status':'MOCK'}
 ctl.action=action;reject(lambda:ctl.command({'op':'sequence','rootApproved':True,'commandId':'seq','steps':[{'target':'FIRST'},{'target':'STOP'},{'target':'MUST_NOT_SEND'}]}));assert seen==['FIRST','STOP']
test('actual_explicit_sequence_stops_first_exception_no_later_input',sequence)
def nativecallback():
 base={k:'SAME-'+k for k in ['documentId','clientId','clientEpoch','clientInstance','run','boot','modelSha256','planSha256','configId']};base.update(run=None,boot=None,nativeResult={'seq':1});clock=types.SimpleNamespace(t=0);ui=types.SimpleNamespace(q=types.SimpleNamespace(state=lambda:{'flight':{},'payloadLeaseObservation':{'leaseCount':0}}),observation=lambda:{'observation':base})
 ctl=m.Controller('01',boot_reader=lambda:'BOOT',clock=lambda:clock.t,ui=ui);sent=[];ctl.action=lambda c:sent.append(c)or{'status':'ONE_NATIVE_DIAGNOSTIC_INPUT_NOT_RESULT'}
 def response(ok=False,code='OPERATION_NOT_CONFIRMED',message='SHA256_MISMATCH'):
  return {'observation':{**base,'nativeResult':{'seq':2,'ok':ok,'code':code,'message':message}}}
 ui.receipt_observation=lambda d:response();r=ctl.native_negative({'commandId':'negative'});assert len(sent)==1 and sent[0]['nativeDiagnosticHandoffOnly']is True and r['providerProof']is False and r['nativeJournalBeforeAfterStillRequired']is True
 for kw in [{'ok':True},{'code':'WRONG'},{'message':'QUOTA'}]:
  ui.receipt_observation=lambda d,kw=kw:response(**kw);reject(lambda:ctl.native_negative({'commandId':'negative-other'}))
test('native_negative_requires_new_actual_callback_kind_not_generic_dispatch_result',nativecallback)
def sourceguards():
 source=p.read_text();u=uiPath.read_text();assert "if c.get('nativePickerHandoffOnly')is True or c.get('nativeDiagnosticHandoffOnly')is True:"in source;assert 'NATIVE_PICKER_GROUND_IDLE_BEFORE_INPUT'in source;assert 'finally:ctl.close()'in source;assert "before_input(ident,latest,fresh)"in u
 test=True
test('picker_and_negative_fresh_ground_guard_and_controller_EOF_cleanup_are_wired',sourceguards)
paths=[uiPath,p,Path('planning/beta06/qa-runtime.py'),Path('planning/beta06/qa-device-actions.py')];r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_HARNESS_ADVERSARIAL_MOCK_ONLY'if all(x['status']=='PASS'for x in rows)else'FAIL','sources':{str(q):hashlib.sha256(q.read_bytes()).hexdigest()for q in paths},'rows':rows,'scope':'Actual function/assert AST and actual Controller sequence/native-callback methods with fake clocks/UI/state. No runtime, ADB, listeners, subprocess or actual native callback; provider receipt and guest state remain Root actual gates.'};out=Path('evidence/beta06/qa-harness-adversarial01.json');out.open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps(r));assert r['status'].startswith('PASS')
