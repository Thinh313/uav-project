"""Actual native owner close order; no process or Android actor."""
from pathlib import Path
import os,sys,types,unittest
from unittest.mock import patch
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
from aeris_runtime.product_runtime import WorkbenchRuntime
class NativeCloseH10(unittest.TestCase):
 def fixture(self,*,pending=False,proof=True):
  calls=[]
  class Writer:
   ending=False;failure=None;observer_failure=None
   def begin_managed_close(self):
    calls.append('BEGIN_WRITER_CLOSE');self.ending=True;return{'commandAdmissionClosed':True,'originalDataFrameDrained':not pending,'inflight':{'uncertain':True}if pending else None}
   def close(self):calls.append('CLOSE_WRITER');return{'closed':True,'failure':None,'observerFailure':None,'allRoleThreadsStopped':True,'threadStopped':True}
  writer=Writer();job=types.SimpleNamespace(process=types.SimpleNamespace(pid=1,args=['mock']),started=1,wait=lambda d:calls.append('WAIT_COMPANION'));native=types.SimpleNamespace(latest={'input':{'closed':True,'configured':False,'pending':False,'failed':False,'workerTerminated':True,'journal':{'durablyDrained':True}}},close=lambda:{'closed':True});c={'APStarted':False,'resources':types.SimpleNamespace(children={},close_scene=lambda:{'closed':True}),'phase':'NATIVE_UI_READY','archiveProofRef17':{}if proof else None,'nativeCryptoProof':{},'native':native,'companion':job,'writer':writer,'monitor':types.SimpleNamespace(close=lambda:{'durablyDrained':True})};o=WorkbenchRuntime.__new__(WorkbenchRuntime);o.case=c;o.write=lambda *a:None;return o,c,calls
 def test_actual_order_after_cold_proofs_before_stop_and_pending_refusals(self):
  for pending,proof in [(False,True),(True,True),(False,False)]:
   with self.subTest(pending=pending,proof=proof):
    o,c,calls=self.fixture(pending=pending,proof=proof)
    def stop(*a,**kw):self.assertTrue(c['writer'].ending);calls.append('STOP_COMPANION');return{'exited':True}
    with patch('aeris_runtime.product_runtime.stop_owned',stop):
     if pending or not proof:
      with self.assertRaises(RuntimeError):o.close_native_only()
      self.assertNotIn('STOP_COMPANION',calls);self.assertNotIn('CLOSE_WRITER',calls)
      if not proof:self.assertNotIn('BEGIN_WRITER_CLOSE',calls)
     else:r=o.close_native_only();self.assertEqual(calls,['BEGIN_WRITER_CLOSE','STOP_COMPANION','WAIT_COMPANION','CLOSE_WRITER']);self.assertFalse(r['flightAcceptance']);self.assertTrue(c['closed'])
if __name__=='__main__':unittest.main(verbosity=2)
