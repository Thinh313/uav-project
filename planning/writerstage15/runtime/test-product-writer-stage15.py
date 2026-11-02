"""Mock actors, genuine temporary filesystem, bounded faults. No Android/AP."""
from pathlib import Path
import ast,base64,hashlib,json,os,socket,stat,struct,sys,tempfile,time,types,unittest,zlib
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];S=Path(__file__).parent/'source';sys.path[:0]=[str(S),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.metadata_budget import MetadataBudget,encoded
from aeris_runtime.product_writer import ProductWriter,RPC_NS
from aeris_runtime import product_trace15 as T
CTX={'run':'case15','epoch':'epoch','boot':'boot','operator':'ROOT-LAB','generation':'g','profileId':'WORKBENCH_SIM_V1'}
class Fixture(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='m-',dir=R/'evidence/writerstage15');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.b=MetadataBudget(self.root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);self.b.admit();self.b.tick('cases');self.b.prepare_directory('external_task',self.root/'reports');self.w=ProductWriter(self.b,CTX);self.addCleanup(self.clean)
 def clean(self):
  try:self.w.close()
  except BaseException:pass
 def req(self,payload=b'X',path='journal/test.jsonl',op='append',offset=None,seq=None):
  target=self.w.root/path
  return {'version':1,'token':self.w.token,'sequence':self.w.sequence+1 if seq is None else seq,'context':dict(CTX),'op':op,'path':path,'payloadBase64':base64.b64encode(payload).decode(),'expectedOffset':target.stat().st_size if offset is None and target.exists()else 0 if offset is None else offset}
 def trace(self):return T.decode(self.w.stage_trace.snapshot(),context=CTX,pid=os.getpid())
class WriteTests(Fixture):
 def test_existing_append_fsync_file_parent_ledger_not_higher(self):
  target=self.w.root/'journal/test.jsonl';self.b.write('lifecycle',target,b'A',append=True);calls=[];real=os.fsync
  def sync(fd):s=os.fstat(fd);calls.append((s.st_dev,s.st_ino,stat.S_ISDIR(s.st_mode)));return real(fd)
  with patch('os.fsync',side_effect=sync):result=self.w.dispatch(self.req())
  self.assertTrue(result['committed']);self.assertTrue(result['ok']);self.assertEqual(len(calls),4);ps=target.parent.stat();self.assertIn((ps.st_dev,ps.st_ino,True),calls);higher=target.parent.parent.stat();self.assertNotIn((higher.st_dev,higher.st_ino,True),calls);self.assertEqual(target.read_bytes(),b'AX')
 def test_new_namespace_every_changed_parent_and_immediate_parent_syncs(self):
  calls=[];real=os.fsync
  def sync(fd):s=os.fstat(fd);calls.append((s.st_dev,s.st_ino,stat.S_ISDIR(s.st_mode)));return real(fd)
  with patch('os.fsync',side_effect=sync):result=self.w.dispatch(self.req())
  self.assertTrue(result['ok']);p=self.w.root/'journal'
  while p.is_relative_to(self.root):
   st=p.stat();self.assertIn((st.st_dev,st.st_ino,True),calls);p=p.parent
 def test_nonproduct_namespace_policy_is_unchanged(self):
  p=self.root/'reports/other.jsonl';self.b.write('external_task',p,b'A',append=True);calls=[];real=os.fsync
  def sync(fd):s=os.fstat(fd);calls.append((s.st_dev,s.st_ino));return real(fd)
  with patch('os.fsync',side_effect=sync):self.b.write('external_task',p,b'B',append=True)
  st=self.root.stat();self.assertIn((st.st_dev,st.st_ino),calls)
 def test_exclusive_create_then_duplicate_refuses_without_overwrite(self):
  q=self.req(op='exclusive');a=self.w.dispatch(q);self.assertTrue(a['committed'])
  with self.assertRaises(ValueError):self.w.dispatch(self.req(op='exclusive',offset=1))
  self.assertEqual((self.w.root/q['path']).read_bytes(),b'X')
 def test_symlink_ancestor_is_not_a_namespace_proof(self):
  out=self.root/'elsewhere';out.mkdir();self.w.root.mkdir(parents=True);(self.w.root/'journal').symlink_to(out,target_is_directory=True)
  with self.assertRaises(ValueError):self.w.dispatch(self.req())
  self.assertEqual(list(out.iterdir()),[])
 def test_ledger_fsync_EIO_never_accepts_or_retries(self):
  e=OSError('injected ledger fsync');real=os.fsync
  def fail(fd):
   if stat.S_ISREG(os.fstat(fd).st_mode):raise e
   return real(fd)
  with patch('os.fsync',side_effect=fail):
   with self.assertRaises(OSError):self.w.dispatch(self.req())
  self.assertIs(self.w.failure,e)
  with self.assertRaises(ValueError):self.w.dispatch(self.req())
 def test_payload_fsync_EIO_is_unknown_not_committed(self):
  target=self.w.root/'journal/test.jsonl';self.b.write('lifecycle',target,b'A',append=True);inode=target.stat().st_ino;real=os.fsync
  def fail(fd):
   if os.fstat(fd).st_ino==inode:raise OSError('injected payload fsync')
   return real(fd)
  with patch('os.fsync',side_effect=fail):
   with self.assertRaises(OSError):self.w.dispatch(self.req())
  row=self.trace()['rows'][-1]['operation'];self.assertIsNone(row['c']);self.assertIsNone(row['f']);self.assertIsNotNone(row['x'])
 def test_immediate_parent_fsync_EIO_still_refuses(self):
  target=self.w.root/'journal/test.jsonl';self.b.write('lifecycle',target,b'A',append=True);inode=target.parent.stat().st_ino;real=os.fsync
  def fail(fd):
   if os.fstat(fd).st_ino==inode:raise OSError('injected directory fsync')
   return real(fd)
  with patch('os.fsync',side_effect=fail):
   with self.assertRaises(OSError):self.w.dispatch(self.req())
  self.assertIsNone(self.trace()['rows'][-1]['operation']['c'])
 def test_late_real_payload_fsync_keeps_commit_and_refuses_retry(self):
  target=self.w.root/'journal/test.jsonl';self.b.write('lifecycle',target,b'A',append=True);inode=target.stat().st_ino;real=os.fsync;q=self.req()
  def slow(fd):
   if os.fstat(fd).st_ino==inode:time.sleep(.23)
   return real(fd)
  with patch('os.fsync',side_effect=slow):v=self.w.dispatch(q)
  self.assertTrue(v['committed']);self.assertFalse(v['ok']);self.assertIn('AFTER200MS',v['error']);row=self.trace()['rows'][-1];self.assertTrue(row['operation']['c']);self.assertEqual(row['operation']['f'][2],hashlib.sha256(b'X').hexdigest());self.assertGreaterEqual(row['stages']['payload_file_fsync']['maxWallNs'],230000000)
  with self.assertRaises(ValueError):self.w.dispatch(q)
  self.assertEqual(target.read_bytes(),b'AX')
 def test_metadata_quota_caps_refuse_before_payload_write(self):
  q=self.req();real=self.b._spend
  with patch.object(self.b,'_spend',side_effect=ValueError('injected existing quota refusal')):
   with self.assertRaises(ValueError):self.w.dispatch(q)
  self.assertFalse((self.w.root/q['path']).exists())
class TransportTests(Fixture):
 def call(self,request,raw=None,fail_send=False):
  body=encoded(request)if raw is None else raw;wire=struct.pack('!I',len(body))+body
  class Conn:
   def __init__(self):self.pending=bytearray(wire);self.sent=[]
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def settimeout(self,*a):pass
   def recv(self,n):part=bytes(self.pending[:n]);del self.pending[:n];return part
   def sendall(self,b):
    if fail_send:raise BrokenPipeError('injected send unknown partial')
    self.sent.append(b);self.w.begin_close()
  c=Conn();c.w=self.w;self.w.connections.add(c);self.w._serve_connection(c);return c,body
 def test_real_private_unix_socket_mock_roundtrip(self):
  self.w.start();q=self.req();raw=encoded(q)
  with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)as c:
   c.settimeout(2);c.connect(str(self.w.socket_path));c.sendall(struct.pack('!I',len(raw))+raw)
   def read(n):
    out=bytearray()
    while len(out)<n:out.extend(c.recv(n-len(out)))
    return bytes(out)
   n=struct.unpack('!I',read(4))[0];reply=read(n);self.assertTrue(json.loads(reply)['committed']);self.w.begin_close()
  result=self.w.close();data=T.decode((self.root/result['traceRef']['path']).read_bytes(),context=CTX,pid=os.getpid());self.assertEqual(data['rows'][-1]['operation']['q'],hashlib.sha256(raw).hexdigest());self.assertEqual(data['rows'][-1]['operation']['r'],hashlib.sha256(reply).hexdigest());self.assertEqual(data['rows'][-1]['operation']['u'],2)
 def test_transport_exact_request_response_hashes_and_stage_labels(self):
  q=self.req();c,raw=self.call(q);d=self.trace();row=d['rows'][-1];m=row['operation'];reply=c.sent[0][4:];self.assertEqual(m['q'],hashlib.sha256(raw).hexdigest());self.assertEqual(m['r'],hashlib.sha256(reply).hexdigest());self.assertEqual(m['u'],2);self.assertTrue(m['k']);self.assertFalse(d['authority'])
  for stage in ('rpc_receive','rpc_parse','rpc_validate','data_lock','ledger_serial','ledger_write','ledger_file_fsync','ledger_dir_fsync','payload_data_write','payload_file_fsync','payload_dir_fsync','reply_encode','reply_send'):self.assertIn(stage,row['stages'])
 def test_readonly_clock_proof_is_instrumented_without_authority(self):
  q=self.req(payload=encoded({'challenge':'a'*32,'nodeSentNs':'123'}),op='clock-proof',path='reports/clock-proof');c,raw=self.call(q);m=self.trace()['rows'][-1];self.assertEqual(m['operation']['o'],'clock-proof');self.assertTrue(m['operation']['c']);self.assertIsNone(m['operation']['d']);reply=json.loads(c.sent[0][4:]);self.assertFalse(reply['clock']['authorityGranted'])
 def test_send_error_not_delivery_and_keeps_commit(self):
  q=self.req();self.call(q,fail_send=True);m=self.trace()['rows'][-1]['operation'];self.assertEqual(m['u'],3);self.assertTrue(m['c']);self.assertIsInstance(self.w.failure,BrokenPipeError);self.assertIsNotNone(m['r'])
 def test_malformed_complete_body_keeps_original_sha(self):
  raw=b'{"invalid":';self.call(None,raw=raw);m=self.trace()['rows'][-1]['operation'];self.assertTrue(m['k']);self.assertEqual(m['q'],hashlib.sha256(raw).hexdigest());self.assertIsNotNone(m['x'])
 def test_finish_secondary_never_masks_original_send_failure(self):
  original=T.Operation.finish
  with patch.object(T.Operation,'finish',side_effect=OSError('injected trace finalizer')):self.call(self.req(),fail_send=True)
  self.assertIsInstance(self.w.failure,BrokenPipeError);self.assertIn('TRACE_FINISH_SECONDARY',' '.join(self.w.failure.__notes__))
class TraceTests(Fixture):
 def test_tail_and_first_failure_not_full_history(self):
  self.w.dispatch(self.req());self.w.dispatch(self.req());self.w.dispatch(self.req());self.w.dispatch(self.req());self.assertEqual(len(self.trace()['rows']),2);self.assertEqual(self.trace()['header']['overwritten'],2)
  bad=self.req(offset=999)
  with self.assertRaises(ValueError):self.w.dispatch(bad)
  d=self.trace();self.assertTrue(d['header']['frozen']);self.assertFalse(d['fullHistory']);self.assertIsNotNone(d['rows'][-1]['operation']['x'])
 def test_close_file4KiB_ref_durable_and_no_second_flush(self):
  self.w.dispatch(self.req());v=self.w.close();ref=v['traceRef'];raw=(self.root/ref['path']).read_bytes();self.assertLessEqual(len(raw),4096);self.assertEqual(hashlib.sha256(raw).hexdigest(),ref['sha256']);d=T.decode(raw,context=CTX,pid=os.getpid(),expected_sha256=ref['sha256']);self.assertFalse(d['authority'])
  self.assertEqual(self.w.close()['traceRef'],ref)
  with self.assertRaisesRegex(RuntimeError,'SECOND_FLUSH'):self.w.stage_trace.flush(self.b)
 def test_close_trace_EIO_repeats_same_failure_and_preserves_primary(self):
  first=RuntimeError('original fault');self.w.failure=first;failure=OSError('injected trace fsync')
  with patch.object(self.w.stage_trace,'flush',side_effect=failure):
   with self.assertRaises(OSError):self.w.close()
  with self.assertRaises(OSError)as caught:self.w.close()
  self.assertIs(caught.exception,failure);self.assertIs(self.w.failure,first);self.assertIn('TRACE_CLOSE_SECONDARY',' '.join(first.__notes__))
 def test_crc_sha_trailing_duplicate_type_and_context_corpus(self):
  self.w.dispatch(self.req());raw=self.w.stage_trace.snapshot()
  for broken in (raw[:-1],raw+b'X',raw[:20]+bytes([raw[20]^1])+raw[21:]):
   with self.subTest(case=len(broken)):
    with self.assertRaises(ValueError):T.decode(broken)
  with self.assertRaisesRegex(ValueError,'FILE_SHA'):T.decode(raw,expected_sha256='0'*64)
  with self.assertRaisesRegex(ValueError,'CONTEXT'):T.decode(raw,context={**CTX,'boot':'foreign'})
  magic,hn,n=T.FILE.unpack_from(raw);header=json.loads(raw[T.FILE.size:T.FILE.size+hn]);tail=raw[T.FILE.size+hn:-4]
  for field,value in [('pid',True),('version',True),('total',False),('fullHistory',True),('overwritten',99),('candidate','bad')]:
   v={**header,field:value};h=encoded(v).strip();changed=T.FILE.pack(magic,len(h),n)+h+tail;changed+=struct.pack('<I',zlib.crc32(changed)&0xffffffff)
   with self.subTest(field=field):
    with self.assertRaises(ValueError):T.decode(changed)
  h=encoded(header).strip();h=h[:-1]+b',"pid":1}';changed=T.FILE.pack(magic,len(h),n)+h+tail;changed+=struct.pack('<I',zlib.crc32(changed)&0xffffffff)
  with self.assertRaisesRegex(ValueError,'DUPLICATE'):T.decode(changed)
 def test_bound_max_layout_is_under_original4KiB(self):
  self.assertLessEqual(T.FILE.size+T.MAX_HEADER+T.MAX_ROWS*T.MAX_RECORD+4,T.MAX_FILE);self.assertEqual(RPC_NS,200000000)
 def test_hosthealth_trace_codes_keep_old_indices_and_snapshot_bound(self):
  from aeris_runtime.stage_trace import CODES,StageTrace
  tree=ast.parse((R/'planning/hostisolate14/runtime/source/aeris_runtime/stage_trace.py').read_text());old=next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='CODES'for t in n.targets));prior=ast.literal_eval(old);self.assertEqual(CODES[:len(prior)],prior);t=StageTrace()
  for code in CODES:
   with t.span(code):pass
  self.assertLessEqual(len(json.dumps(t.snapshot(),separators=(',',':')).encode()),8192);t.check()
if __name__=='__main__':unittest.main(verbosity=2)
