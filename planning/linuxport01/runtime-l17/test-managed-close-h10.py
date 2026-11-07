"""Forced actual ACK-visible/reply-pending RPC closure, original200ms unchanged."""
from pathlib import Path
import json,os,subprocess,sys,tempfile,threading,time,types,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
from aeris_runtime.metadata_budget import MetadataBudget
from aeris_runtime.product_writer import ProductWriter,RPC_NS
from aeris_runtime.product_runtime import require_normal_writer_close
CONTEXT={'run':'mock-command-h10','epoch':'mock-epoch','boot':'mock-boot','operator':'mock-operator','generation':'1','profileId':'WORKBENCH_SIM_V1'}
class ManagedCloseH10(unittest.TestCase):
 def setup_writer(self,root):
  budget=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);budget.admit();budget.tick('cases');w=ProductWriter(budget,CONTEXT);(root/'fixture-writer-descriptor.json').write_text(json.dumps(w.start()));return w
 def start_node(self,root,mode='normal'):return subprocess.Popen(['/usr/local/bin/node',str(B/'test-command-real-wire.mjs'),str(root),str(os.getpid()),mode],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 def finish(self,w,p,root):
  w.begin_close();(root/'fixture-allow-managed-close').write_bytes(b'MOCK_ROOT_CLOSE')
  if p is not None:
   try:p.communicate(timeout=2)
   except subprocess.TimeoutExpired:p.terminate();p.communicate(timeout=2)
  return w.close()
 def test_ack_file_visible_frame_drain_waits_reply_and_trace_within_original200ms(self):
  with tempfile.TemporaryDirectory(prefix='w10-',dir=R/'planning/betarc01')as tmp:
   root=Path(tmp);w=self.setup_writer(root);committed=threading.Event();release=threading.Event();waiting=threading.Event();original_dispatch=w.dispatch;original_wait=w.data_condition.wait;results=[];errors=[];p=None;thread=None;frame=[None]
   def dispatch(request,**kwargs):
    result=original_dispatch(request,**kwargs)
    if request.get('path')=='reports/companion-progress.jsonl':frame[0]=w.active_data_frame;committed.set();release.wait(.12)
    return result
   def wait(timeout=None):waiting.set();return original_wait(timeout)
   w.dispatch=dispatch;w.data_condition.wait=wait
   def close():
    try:results.append(w.begin_managed_close())
    except BaseException as e:errors.append(e)
   try:
    p=self.start_node(root);self.assertTrue(committed.wait(2));ackfile=w.root/'reports/companion-progress.jsonl';self.assertTrue(ackfile.is_file());self.assertFalse((root/'fixture-wire-output.json').exists());thread=threading.Thread(target=close);thread.start();self.assertTrue(waiting.wait(.08));self.assertTrue(thread.is_alive());self.assertFalse(w.ending);release.set();thread.join(1);self.assertFalse(thread.is_alive());self.assertEqual(errors,[]);self.assertEqual(len(results),1);self.assertTrue(results[0]['waitedForOriginalFrame']);self.assertEqual(results[0]['originalFrameDeadlineNs'],frame[0]+RPC_NS);self.assertEqual(results[0]['maximumWaitNs'],200000000);self.assertTrue(w.ending);(root/'fixture-allow-managed-close').write_bytes(b'ROOT_MANAGED_DRAINED');out,err=p.communicate(timeout=3);self.assertEqual(p.returncode,0,err.decode());self.assertIsNone(w.failure)
   finally:
    release.set()
    if thread is not None:thread.join(1)
    receipt=self.finish(w,p,root)
   require_normal_writer_close(w,receipt);self.assertEqual(w.sequence,3)
 def test_original_deadline_failure_never_becomes_normal_close(self):
  with tempfile.TemporaryDirectory(prefix='w10-',dir=R/'planning/betarc01')as tmp:
   root=Path(tmp);w=self.setup_writer(root);committed=threading.Event();release=threading.Event();real=w.dispatch;p=None
   def dispatch(request,**kwargs):
    result=real(request,**kwargs)
    if request.get('path')=='reports/companion-progress.jsonl':committed.set();release.wait(.35)
    return result
   w.dispatch=dispatch
   try:
    p=self.start_node(root);self.assertTrue(committed.wait(2));start=time.monotonic_ns()
    with self.assertRaisesRegex(ValueError,'MANAGED_CLOSE_ORIGINAL_RPC200MS'):w.begin_managed_close()
    self.assertFalse(w.ending);self.assertTrue((w.root/'reports/companion-progress.jsonl').is_file());self.assertLess(time.monotonic_ns()-start,250000000)
   finally:release.set();receipt=self.finish(w,p,root)
   # The intentional failure is a refusal, never a normal scope acceptance.
   self.assertTrue(w.managed_closing);self.assertIsNone(w.active_data_frame);self.assertIsNotNone(w.failure)
   with self.assertRaises(RuntimeError):require_normal_writer_close(w,receipt)
 def test_preexisting_eof_and_postclose_failure_cannot_hide_as_normal(self):
  with tempfile.TemporaryDirectory(prefix='w10-',dir=R/'planning/betarc01')as tmp:
   root=Path(tmp);w=self.setup_writer(root);p=self.start_node(root,'unplanned-close')
   try:
    out,err=p.communicate(timeout=3);self.assertEqual(p.returncode,0,err.decode())
    with w.data_condition:w.data_condition.wait_for(lambda:w.failure is not None,timeout=1)
    self.assertIsNotNone(w.failure)
    with self.assertRaises(RuntimeError):w.begin_managed_close()
    self.assertFalse(w.ending)
   finally:receipt=self.finish(w,p,root)
   with self.assertRaises(RuntimeError):require_normal_writer_close(w,receipt)
  for field in ['failure','observerFailure','allRoleThreadsStopped','threadStopped']:
   writer=types.SimpleNamespace(failure=None,observer_failure=None);receipt={'closed':True,'failure':None,'observerFailure':None,'allRoleThreadsStopped':True,'threadStopped':True};receipt[field]='injected'if field.endswith('ailure')else False
   with self.subTest(field=field),self.assertRaises(RuntimeError):require_normal_writer_close(writer,receipt)
if __name__=='__main__':unittest.main(verbosity=2)
