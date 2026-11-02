"""Real budget/audit writers under mock actor identity; no flight or helper process."""
from pathlib import Path
import hashlib,json,os,sys,tempfile,time,types,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];sys.path[:0]=[str(Path(__file__).parent/'source'),str(Path(__file__).parent),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime import host_health as H
from aeris_runtime.metadata_budget import MetadataBudget
from aeris_runtime.monitor import ResourceMonitor,host_power
from aeris_runtime.power_worker import PowerWorker
import importlib.util
spec=importlib.util.spec_from_file_location('mock_pipes',Path(__file__).with_name('test-power-isolation.py'));M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
class DrainTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='mock-drain-',dir=R/'evidence/hostisolate14');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.b=MetadataBudget(self.root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);self.b.admit();self.b.require_real_actor=lambda:None;self.health=None
 def health_rows(self,bad_power=False):
  root=self.root/'guardian';h=H.HostHealth(root,self.b,'guardian',inventory=lambda:None,check_inventory=lambda x:x);self.health=h
  h.power_worker=PowerWorker(self.b,'guardian',root,spawn=lambda*a,**k:M.MockProcess());h.power_worker.start();r=h.power_worker.query();h.audit.start();n=time.monotonic_ns();self.counters={'metadataBytes':0,'metadataAccountingUpperBoundAtScan':0,'metadataAccountingWriteSequenceAtScan':0,'exportBytes':0,'AVDPositiveGrowthBytes':0,'artifactBytes':0,'taskAllocatedBytes':0}
  h.audit.submit(1,H.DISK_ROW.pack(n,n,100*2**30,0.,float(100*2**30),1,0,0));h.audit.submit(2,H.POWER_ROW.pack(r['started'],r['ended'],0 if bad_power else 1,20 if bad_power else 65,len(r['stdout']),0)+r['stdout']+r['binding']);h.audit.submit(3,H._json({'startedHostNs':n,'completedHostNs':n,'counters':self.counters,'failure':None}));h.audit.barrier();return h
 def test_local_failed_drain_fsynamed_original_bytes_no_authority(self):
  h=self.health_rows();first=TimeoutError('original100ms');h.latch(first);a=h.drain_failure(RuntimeError('shutdown'));b=h.drain_failure(RuntimeError('later'));self.assertEqual(a,b);self.assertTrue(a['durablyDrained']);self.assertEqual(a['audit']['producedSeq'],a['audit']['committedSeq']);self.assertEqual(a['audit']['pendingRows'],0);self.assertIsNotNone(a['originalPrefixVerified']);self.assertIsNone(a['semanticPrefixFailure']);self.assertIn('original100ms',a['failure']);self.assertFalse(a['flightAcceptance']);self.assertFalse(a['authorityRestored']);self.assertEqual(a['guardianRPCsDuringFailureDrain'],0)
  with self.assertRaisesRegex(TimeoutError,'original100ms'):h.close()
 def test_bad_power_bytes_drained_but_semantically_not_healthy(self):
  h=self.health_rows(True);v=h.drain_failure(RuntimeError('powerguard'));self.assertTrue(v['durablyDrained']);self.assertIsNone(v['originalPrefixVerified']);self.assertIn('POWER_VALUES',v['semanticPrefixFailure']);self.assertFalse(v['flightAcceptance'])
 def test_old_row_without_binding_refused_by_new_decoder(self):
  h=self.health_rows();v=h.drain_failure(RuntimeError('diagnostic'));path=Path(v['audit']['path']);raw=path.read_bytes();rows=[];o=0
  while o<len(raw):
   n,kind,size=H.HEADER.unpack_from(raw,o);o+=H.HEADER.size;body=raw[o:o+size];o+=size
   if kind==2:body=body[:-H.POWER_BINDING.size]
   rows.append(H.HEADER.pack(n,kind,len(body))+body)
  p=self.root/'guardian-old';p.mkdir();target=p/'health-audit.bin';target.write_bytes(b''.join(rows));body=target.read_bytes();ref={'path':str(target),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'throughSeq':3,'durable':True}
  with self.assertRaisesRegex(ValueError,'POWER_CAPTURE'):H.verify_audit_prefix(ref,'guardian',expected_root=p)
 def test_corrupt_binding_magic_refused(self):
  h=self.health_rows();v=h.drain_failure(RuntimeError('diagnostic'));raw=bytearray(Path(v['audit']['path']).read_bytes());o=0
  while o<len(raw):
   n,kind,size=H.HEADER.unpack_from(raw,o);o+=H.HEADER.size
   if kind==2:raw[o+size-H.POWER_BINDING.size:o+size-H.POWER_BINDING.size+4]=b'OLD0'
   o+=size
  p=self.root/'guardian-mutated';p.mkdir();target=p/'health-audit.bin';target.write_bytes(raw);ref={'path':str(target),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'throughSeq':3,'durable':True}
  with self.assertRaisesRegex(ValueError,'HELPER_BINDING'):H.verify_audit_prefix(ref,'guardian',expected_root=p)
 def test_audit_writer_EIO_drain_not_success(self):
  h=self.health_rows();h.audit.failure=OSError('injected fsync EIO');v=h.drain_failure(TimeoutError('original'));self.assertFalse(v['durablyDrained']);self.assertIsNone(v['originalPrefixVerified']);self.assertTrue(v['drainErrors']);self.assertIn('fsync EIO',str(v['drainErrors']))
 def test_release_lease_fault_not_success(self):
  h=self.health_rows()
  with patch.object(self.b,'release_lease',side_effect=OSError('release EIO')):v=h.drain_failure(RuntimeError('original'))
  self.assertFalse(v['durablyDrained']);self.assertTrue(v['drainErrors']);self.assertFalse(v['flightAcceptance'])
 def test_partial_unstarted_audit_lease_release_no_fabricated_bytes(self):
  h=H.HostHealth(self.root/'guardian',self.b,'guardian',inventory=lambda:None,check_inventory=lambda x:x);v=h.drain_failure(RuntimeError('helperstartfailed'));self.assertFalse(v['durablyDrained']);self.assertEqual(v['audit']['status'],'NOT_STARTED_NO_ROWS');self.assertEqual(self.b.snapshot()['inFlight'],{})
 def test_health_check_detects_worker_death_before_old_power_can_be_used(self):
  h=self.health_rows();h.threads=[types.SimpleNamespace(is_alive=lambda:True)]*3;h.audit.snapshot=lambda:{'writerAlive':True,'failure':None};h.power_worker.process.returncode=99
  with self.assertRaisesRegex(RuntimeError,'DEAD'):h._failure_check(priming=True)
  h.power_worker.process.returncode=None;h.threads=[];h.drain_failure(RuntimeError('end'))
if __name__=='__main__':unittest.main(verbosity=2)
