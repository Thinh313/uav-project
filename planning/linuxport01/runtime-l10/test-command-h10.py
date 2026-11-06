"""Actual Node result publication + actual Root reader; mock writer only."""
from pathlib import Path
import ast,copy,hashlib,json,os,subprocess,sys,tempfile,time,types,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
from aeris_runtime.command_results_h10 import read_command_progress
from aeris_runtime.product_runtime import WorkbenchRuntime
class CommandsH10(unittest.TestCase):
 def fixture(self,tmp,mode='large'):
  root=Path(tmp);p=subprocess.run(['/usr/local/bin/node',str(B/'test-command-fixture.mjs'),str(root),mode,str(os.getpid())],cwd=R,capture_output=True,timeout=15);self.assertEqual(p.returncode,0,p.stderr.decode());v=json.loads((root/'fixture-meta.json').read_bytes());c={'context':v['context'],'companion':types.SimpleNamespace(process=types.SimpleNamespace(pid=v['companionPID'])),'writer':types.SimpleNamespace(committed_files=v['committed'])};o=types.SimpleNamespace(root=root,digest=v['candidateSHA256'],case=c);control=root/'reports'/('companion-control-'+v['context']['run']+'.jsonl');control.parent.mkdir(exist_ok=True);control.write_text(json.dumps({'sequence':1,'ownerPID':os.getpid(),'run':v['context']['run'],'candidateSHA256':o.digest,'action':'SEAL_PRODUCT'})+'\n');return o,v
 def progress(self,o):return(o.root/'sessions'/o.case['context']['run']/'product/reports/companion-progress.jsonl').read_bytes()
 def test_actual_large_seal_function_and_lossless_multi_frame_root_reconstruction(self):
  for mode in ['small','large']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory(prefix='command-',dir=B)as tmp:
    o,v=self.fixture(tmp,mode);self.assertIsNone(v['error']);self.assertEqual(v['closedCalls'],1);raw=self.progress(o);self.assertLessEqual(len(raw),4096);self.assertGreater(v['ack']['data']['resultRef']['bytes'],4096);r=WorkbenchRuntime.command_progress(o,v['ack'],raw);self.assertEqual(r['data']['result'],json.loads((o.root/'expected-result.json').read_bytes()));self.assertFalse(r['data']['result']['authorityRestorable']);self.assertEqual(v['writes'],1 if mode=='small'else 2);self.assertFalse(v['originalG105FullSealLengthClaimed'])
 def test_partial_and_ack_faults_retain_prefix_no_success_ack_or_retry(self):
  for mode in ['partialFault','ackFault','badReceipt','duplicateFile','undefinedValue','overFile']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory(prefix='command-',dir=B)as tmp:
    o,v=self.fixture(tmp,mode);self.assertIsNone(v['ack']);self.assertIn('ACTION_MAY_HAVE_EXECUTED',v['error']);self.assertEqual(v['closedCalls'],1);self.assertFalse((o.root/'sessions'/o.case['context']['run']/'product/reports/companion-progress.jsonl').exists())
    if mode=='partialFault':self.assertEqual(v['writes'],1);self.assertEqual((o.root/'sessions'/o.case['context']['run']/'product/reports/command-result-01-SEAL_PRODUCT.json').stat().st_size,65536)
    if mode=='ackFault':self.assertEqual(v['writes'],2)
    if mode=='duplicateFile':self.assertEqual((o.root/'sessions'/o.case['context']['run']/'product/reports/command-result-01-SEAL_PRODUCT.json').read_bytes(),b'held-original')
 def test_ref_control_integrity_and_duplicate_refusals(self):
  with tempfile.TemporaryDirectory(prefix='command-',dir=B)as tmp:
   o,v=self.fixture(tmp);row=v['ack'];raw=self.progress(o)
   for mode in ['sha','bytes','path','pending','crosscase','candidate','sequence','action','lastSHA','version','duplicateACK','pid']:
    q=copy.deepcopy(row);rr=raw
    if mode=='sha':q['data']['resultRef']['sha256']='0'*64
    elif mode=='bytes':q['data']['resultRef']['bytes']-=1
    elif mode=='path':q['data']['resultRef']['path']='../foreign.json'
    elif mode=='pending':q['data']['resultRef']['path']+='.pending'
    elif mode=='crosscase':q['run']='foreign'
    elif mode=='candidate':o.digest='f'*64
    elif mode=='sequence':q['data']['sequence']=2
    elif mode=='action':q['data']['action']='STATUS'
    elif mode=='lastSHA':q['data']['resultRef']['finalWriteRef']['sha256']='0'*64
    elif mode=='version':q['data']['resultRef']['version']=True
    elif mode=='duplicateACK':rr=raw+raw
    else:q['pid']+=1
    if mode!='duplicateACK':rr=(json.dumps(q)+'\n').encode()
    with self.subTest(mode=mode),self.assertRaises(Exception):read_command_progress(o,q,rr)
    o.digest=v['candidateSHA256'];o.case.pop('commandResultsH10',None)
   out=read_command_progress(o,row,raw);self.assertEqual(out['data']['action'],'SEAL_PRODUCT')
   with self.assertRaisesRegex(ValueError,'NO_DUPLICATE'):read_command_progress(o,row,raw)
 def test_both_actual_root_consumers_use_same_reader_after_matching_ack(self):
  for entry in ['root-native-h10.py','root-owner-h10.py']:
   with self.subTest(entry=entry),tempfile.TemporaryDirectory(prefix='command-',dir=B)as tmp:
    o,v=self.fixture(tmp);o.case['root']=o.root/'sessions'/o.case['context']['run'];o.command_progress=lambda row,raw:read_command_progress(o,row,raw);tree=ast.parse((B/entry).read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='wait_progress');env={'owner':o,'args':types.SimpleNamespace(run=o.case['context']['run']),'time':time,'json':json,'check':lambda:None,'need':lambda v,n:None if v else(_ for _ in()).throw(ValueError(n))};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_'+entry+'_wait_progress','exec'),env);r=env['wait_progress']('COMMAND_COMPLETE',lambda q:q['sequence']==1);self.assertEqual(r['data']['result'],json.loads((o.root/'expected-result.json').read_bytes()))
 def test_actual_node_client_python_writer_wire_commit_ref_and_root_join(self):
  from aeris_runtime.metadata_budget import MetadataBudget
  from aeris_runtime.product_writer import ProductWriter,MAX_PAYLOAD,RPC_NS,CAPS
  with tempfile.TemporaryDirectory(prefix='w10-',dir=R/'planning/betarc01')as tmp:
   root=Path(tmp);budget=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);budget.admit();budget.tick('cases');context={'run':'mock-command-h10','epoch':'mock-epoch','boot':'mock-boot','operator':'mock-operator','generation':'1','profileId':'WORKBENCH_SIM_V1'};w=ProductWriter(budget,context);desc=w.start();(root/'fixture-writer-descriptor.json').write_text(json.dumps(desc));closed=None
   proc=None
   try:
    proc=subprocess.Popen(['/usr/local/bin/node',str(B/'test-command-real-wire.mjs'),str(root),str(os.getpid())],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE);until=time.monotonic()+10
    while not(root/'fixture-wire-output.json').exists():
     if proc.poll()is not None:break
     self.assertLess(time.monotonic(),until);time.sleep(.01)
    self.assertTrue((root/'fixture-wire-output.json').exists());v=json.loads((root/'fixture-wire-output.json').read_bytes());o=types.SimpleNamespace(root=root,digest='d'*64,case={'context':context,'companion':types.SimpleNamespace(process=types.SimpleNamespace(pid=v['companionPID'])),'writer':w});q={'sequence':1,'ownerPID':os.getpid(),'run':context['run'],'candidateSHA256':o.digest,'action':'SEAL_PRODUCT'};(root/'reports'/('companion-control-'+context['run']+'.jsonl')).write_text(json.dumps(q)+'\n');raw=(w.root/'reports/companion-progress.jsonl').read_bytes();r=read_command_progress(o,v['ack'],raw);self.assertEqual(r['data']['result'],v['expected']);self.assertEqual(w.sequence,3);self.assertIsNone(w.failure);self.assertEqual((MAX_PAYLOAD,RPC_NS,CAPS['reports']),(65536,200000000,2**20));self.assertLessEqual(len(raw),4096);self.assertEqual(budget.snapshot()['counters']['commands'],0);self.assertEqual(budget.snapshot()['counters']['requests'],0);w.begin_managed_close();(root/'fixture-allow-managed-close').write_bytes(b'ROOT_SOURCE_PLANNED_CLOSE');out,err=proc.communicate(timeout=10);self.assertEqual(proc.returncode,0,err.decode())
   finally:
    w.begin_close()
    if proc is not None and proc.poll()is None:proc.terminate();proc.communicate(timeout=5)
    closed=w.close()
   self.assertTrue(closed['allRoleThreadsStopped']);self.assertIsNone(closed['failure']);self.assertFalse(w.socket_path.exists())
 def test_pending_symlink_truncated_and_rebound_envelope_refused(self):
  with tempfile.TemporaryDirectory(prefix='command-',dir=B)as tmp:
   o,v=self.fixture(tmp);row=v['ack'];raw=self.progress(o);p=o.root/row['data']['resultRef']['path'];held=p.read_bytes()
   p.write_bytes(held[:-1])
   with self.assertRaises(ValueError):read_command_progress(o,row,raw)
   p.write_bytes(held);other=p.with_name('foreign.json');other.write_bytes(held);p.unlink();p.symlink_to(other)
   with self.assertRaises(ValueError):read_command_progress(o,row,raw)
   p.unlink();p.write_bytes(held)
   for mode in ['candidate','context','action','duplicateJSON']:
    value=json.loads(held)
    if mode=='candidate':value['candidateSHA256']='f'*64
    elif mode=='context':value['context']['boot']='foreign'
    elif mode=='action':value['action']='STATUS'
    changed=(json.dumps(value)+'\n').encode()
    if mode=='duplicateJSON':changed=changed.replace(b'"version": 1',b'"version": 1,"version":1',1)
    p.write_bytes(changed);q=copy.deepcopy(row);ref=q['data']['resultRef'];ref.update(bytes=len(changed),sha256=hashlib.sha256(changed).hexdigest());offset=((len(changed)-1)//65536)*65536;ref['finalWriteRef'].update(offset=offset,bytes=len(changed)-offset,sha256=hashlib.sha256(changed[offset:]).hexdigest());o.case['writer'].committed_files['reports/command-result-01-SEAL_PRODUCT.json']['bytes']=len(changed)
    with self.subTest(mode=mode),self.assertRaises(ValueError):read_command_progress(o,q,(json.dumps(q)+'\n').encode())
   p.write_bytes(held)
if __name__=='__main__':unittest.main(verbosity=2)
