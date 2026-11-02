"""Actual WorkbenchRuntime.close_maintenance + ResourceMonitor + shared ledger.
Mock resource handles only; no Android/AP process or HostHealth thread starts.
"""
from pathlib import Path
import copy,hashlib,json,os,sys,tempfile,types,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(HERE/'source'),str(R)]
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.monitor import ResourceMonitor,host_power
from aeris_runtime.metadata_budget import MetadataBudget,encoded
class MaintenanceClose(unittest.TestCase):
 def fixture(self,base):
  root=Path(base)/'m101';root.mkdir();budget=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);budget.admit();monitor=ResourceMonitor(root/'sessions/mock-maint/resources',180,types.SimpleNamespace(check=lambda:None),inventory=lambda:{},power=host_power,guardian=lambda:(_ for _ in()).throw(AssertionError('NO_GUARDIAN_QUERY_FOR_NO_MONITOR_ACTOR')),budget=budget)
  owner=WorkbenchRuntime.__new__(WorkbenchRuntime);owner.root=root;owner.budget=budget;owner.manifest={'sourceSHA256':{'aeris_runtime/monitor.py':hashlib.sha256((HERE/'source/aeris_runtime/monitor.py').read_bytes()).hexdigest()}};owner.write=lambda name,v:budget.write('external_task',root/'reports'/name,encoded(v));owner.case={'APStarted':False,'resources':types.SimpleNamespace(children={},close_scene=lambda:{'closed':True}),'companion':None,'maintenanceRC01':{'originalPrivateBytesConserved':True,'pendingTransactions':0,'activityStarted':False},'device':types.SimpleNamespace(observer=types.SimpleNamespace(process=None)),'writer':types.SimpleNamespace(close=lambda:{'closed':True}),'native':types.SimpleNamespace(close=lambda:{'closed':True}),'monitor':monitor,'closed':False,'phase':'CREATED','monitorClosed':False,'admissionRevoked':False};return owner,monitor,budget
 def test_real_never_started_monitor_closes_as_no_actor_not_durable_drain(self):
  with tempfile.TemporaryDirectory(prefix='maintenance-close02-',dir=HERE)as base:
   o,m,b=self.fixture(base);before=b.snapshot()['writes'];r=o.close_maintenance();self.assertFalse(r['monitorDurableDrainClaimed']);self.assertFalse(r['monitorStarted']);self.assertFalse(r['monitor']['durablyDrained']);self.assertEqual(r['monitor']['status'],'CLOSED_NO_ACTOR_NOT_ACCEPTANCE');self.assertEqual(r['monitor']['noActorProof']['monitorLeaseClaims'],0);self.assertEqual(r['monitor']['noActorProof']['originalLedgerWrites'],before);self.assertEqual(b.snapshot()['writes'],before+2);self.assertIsNone(m.health);self.assertIsNone(m.thread);self.assertTrue(m.done.is_set());self.assertEqual(o.case['phase'],'NATIVE_MAINTENANCE_CLOSED');self.assertTrue(o.case['closed']);self.assertFalse(r['flightAcceptance'])
 def test_partial_monitor_start_does_not_become_no_actor(self):
  with tempfile.TemporaryDirectory(prefix='maintenance-close02-',dir=HERE)as base:
   o,m,b=self.fixture(base);m._start_attempted=True;m._start_attempts=1;m._start_phase='HEALTH_ALLOCATED'
   with self.assertRaisesRegex(RuntimeError,'HEALTH_NEVER_STARTED'):o.close_maintenance()
   self.assertFalse(o.case['closed'])
 def test_monitor_lease_prevents_no_actor_claim(self):
  with tempfile.TemporaryDirectory(prefix='maintenance-close02-',dir=HERE)as base:
   o,m,b=self.fixture(base);b.reserve_lease({'monitor':4096})
   with self.assertRaisesRegex(RuntimeError,'MONITOR_LEASE_UNKNOWN_OR_PRESENT'):o.close_maintenance()
   self.assertFalse(o.case['closed'])
 def test_no_actor_receipt_cannot_be_forged_as_durable(self):
  with tempfile.TemporaryDirectory(prefix='maintenance-close02-',dir=HERE)as base:
   o,m,b=self.fixture(base);real=m.close
   def forged():
    value=real();value['durablyDrained']=True;m.closure=copy.deepcopy(value);return value
   with patch.object(m,'close',forged),self.assertRaisesRegex(RuntimeError,'EXACT_NO_ACTOR_DISPOSITION'):o.close_maintenance()
   self.assertFalse(o.case['closed'])
 def test_foreign_monitor_source_or_ledger_refused(self):
  for key,value in [('monitorSourceSHA256','0'*64),('originalLedgerSourceIdentity','0'*64),('originalBudgetRoot','/foreign'),('originalLedgerWrites',False)]:
   with tempfile.TemporaryDirectory(prefix='maintenance-close02-',dir=HERE)as base:
    o,m,b=self.fixture(base);real=m.close
    def forged():
     result=real();result['noActorProof'][key]=value;m.closure=copy.deepcopy(result);return result
    with patch.object(m,'close',forged),self.subTest(key=key),self.assertRaisesRegex(RuntimeError,'LEDGER_SOURCE_BINDING'):o.close_maintenance()
    self.assertFalse(o.case['closed'])
if __name__=='__main__':unittest.main(verbosity=2)
