#!/usr/bin/env python3
"""Finite real-file mocks; never Android, AP, browser or signing."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,shutil,sys,tempfile,unittest
from unittest.mock import patch
REPO=Path(__file__).resolve().parents[3];SOURCE=Path(__file__).parent/'source';os.environ['AERIS_REPOSITORY_ROOT']=str(REPO);sys.path[:0]=[str(SOURCE),str(REPO)]
from aeris_runtime import mission16 as m
from aeris_runtime.lifecycle import Context
from aeris_runtime.policy import case_budget
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
OLD=REPO/'evidence/writerstage15/candidates/da4b32e4a7703c7a99079cddc7982f04f600c68a5d392b5802474cf45fb1bf39'
class Contracts(unittest.TestCase):
 def setUp(self):
  self.tmp=Path(tempfile.mkdtemp(prefix='mock16-',dir=REPO/'evidence/missionintegrated16'));self.repo=self.tmp;self.scope=self.repo/'evidence/missionintegrated16';self.short=self.scope/'s01';self.short.mkdir(parents=True);self.manifest=json.loads((OLD/'candidate.json').read_bytes());self.candidate='a'*64
  self.context=Context('mock-nominal','a'*32,'b'*32,'ROOT-LAB','c'*32,'WORKBENCH_SIM_V1').value()
  seal={'format':'aeris-root-verified-workbench-seal','candidateSHA256':self.candidate,'runtimeContext':self.context,'authorityRevoked':True,'providerClosed':True,'journalClosed':True,'nominalOutcomeEligible':True,'flightAcceptance':False,'missionSHA256':'b'*64}
  self.rows={'ownerterminal':{'status':'UI_WORKLOAD_CLOSED_AWAITING_INDEPENDENT_BETA_ACCEPTANCE','candidateSHA256':self.candidate,'normalCompletedClosureClaimed':True,'flightAcceptance':False},'productseal':seal,'case':{'status':'CASE_MANAGED_CLOSED_AWAITING_INDEPENDENT_ACCEPTANCE','flightAcceptance':False,'monitor':{'durablyDrained':True},'resources':{'workbenchSealProof':seal}},'guardian':{'failure':None,'exit':0,'durablyDrained':True,'exceptionalPhysicalDisposal':False,'cleanupNotes':[],'health':{'failure':None,'durablyDrained':True,'audit':{'durablyDrained':True,'pendingRows':0}}},'fullraw':{'format':'aeris-betasim-closed-raw-manifest','version':1,'context':self.context,'sourceCandidateSHA256':self.candidate,'authorityRestorable':False,'allOriginalRawAndAPStateIncluded':True,'productSemanticAndMediaIncluded':True,'closure':{'workbenchSealProof':seal}},'video':{'format':'aeris-integrated-video-qualification','status':'PASS','authorityRestorable':False,'originalFlightInterval':{'proofKind':'ROOT_COLD_JOIN_VERIFIED_FLIGHT_INTERVAL','run':self.context['run'],'boot':self.context['boot'],'missionSHA256':'b'*64}},'saf':{'format':'aeris-independent-recipient-byte-verification','status':'RECIPIENT_BYTES_COMPLETE_NOT_FLIGHT_CERTIFICATION','sourceCandidateSHA256':self.candidate,'originalRawComplete':True,'documentBytesVerified':True,'actualSAFBytesVerified':True,'authorityRestorable':False}}
  self.rows['saf']['manifestSHA256']=hashlib.sha256(enc(self.rows['fullraw'])).hexdigest()
 def tearDown(self):shutil.rmtree(self.tmp)
 def proof(self):
  refs=[]
  for role,row in sorted(self.rows.items()):
   path=self.short/(role+'.json');raw=enc(row);path.write_bytes(raw);refs.append({'role':role,'path':str(path.relative_to(self.repo)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
  v={'format':'aeris-independent-missionintegrated16-short-acceptance','version':1,'status':'ROOT_VERIFIED_NOMINAL_ANDROID_SITL_SHORT','candidateSHA256':self.candidate,'profileId':'WORKBENCH_SIM_V1','simulationOnly':True,'slot':'s01','maximumSeconds':180,'expectedFault':False,'recordingStatus':'COMPLETE_RECORDING','normalManagedClosed':True,'actualSignedInput':True,'videoPayload':True,'SAFImport':True,'allActorsClosed':True,'commonBindings':m.common_bindings(self.manifest),'originalEvidence':refs,'context':self.context};return v
 def check_proof(self,v):
  path=self.scope/'root-short.json';raw=enc(v);path.write_bytes(raw);return m.verify_short(str(path),hashlib.sha256(raw).hexdigest(),self.manifest,self.candidate,self.repo)
 def test_nominal_receipt(self):self.assertFalse(self.check_proof(self.proof())['authorityGranted'])
 def test_valid_unicode_original_manifest(self):
  self.rows['fullraw']['unicodeMission']='Khảo sát điện lực';self.rows['saf']['manifestSHA256']=hashlib.sha256(enc(self.rows['fullraw'])).hexdigest();self.assertFalse(self.check_proof(self.proof())['authorityGranted'])
 def test_wrong_candidate(self):
  v=self.proof();v['candidateSHA256']='c'*64
  with self.assertRaises(ValueError):self.check_proof(v)
 def test_disarmed_not_prerequisite(self):
  v=self.proof();v['recordingStatus']='INCOMPLETE_RECORDING'
  with self.assertRaises(ValueError):self.check_proof(v)
 def test_hash_mutation(self):
  v=self.proof();(self.short/'video.json').write_bytes(b'{}')
  with self.assertRaises(ValueError):self.check_proof(v)
 def test_correctly_hashed_fail_roles(self):
  for role in ('video','saf','guardian','productseal','case'):
   original=copy.deepcopy(self.rows);self.rows[role]['status']='FAIL'
   if role=='guardian':self.rows[role]['failure']='EIO'
   if role=='productseal':self.rows[role]['nominalOutcomeEligible']=False
   with self.subTest(role=role),self.assertRaises(ValueError):self.check_proof(self.proof())
   self.rows=original
 def test_other_boot_rejected(self):
  self.rows['video']['originalFlightInterval']['boot']='d'*32
  with self.assertRaises(ValueError):self.check_proof(self.proof())
 def test_saf_manifest_replaced(self):
  self.rows['saf']['manifestSHA256']='e'*64
  with self.assertRaises(ValueError):self.check_proof(self.proof())
 def test_missing_role(self):
  v=self.proof();v['originalEvidence'].pop()
  with self.assertRaises(ValueError):self.check_proof(v)
 def test_duplicate_role(self):
  v=self.proof();v['originalEvidence'].append(v['originalEvidence'][0])
  with self.assertRaises(ValueError):self.check_proof(v)
 def test_scope_escape(self):
  v=self.proof();v['originalEvidence'][0]['path']='../foreign.json'
  with self.assertRaises(ValueError):self.check_proof(v)
 def test_common_immutable_changed(self):
  v=self.proof();v['commonBindings']['AP']='f'*64
  with self.assertRaises(ValueError):self.check_proof(v)
 def test_typed_duration_and_fault_refusal(self):
  for slot,seconds in [('s01',180),('s02',180),('l01',760)]:self.assertEqual(m.nominal_duration(slot,seconds),seconds)
  for slot,seconds in [('l01',180),('s01',760),('f01',180),('f02',180),('s03',180),('s01',True),('s01',180.0)]:
   with self.subTest(slot=slot,seconds=seconds),self.assertRaises(ValueError):m.nominal_duration(slot,seconds)
 def test_existing_numeric_case_budgets(self):
  self.assertEqual(case_budget(100*2**30,180)['requiredFreeBytes'],12616295040);self.assertEqual(case_budget(100*2**30,760)['requiredFreeBytes'],15075000960)
 def test_all_budget_consumers_select_duration(self):
  runtime=(SOURCE/'aeris_runtime/product_runtime.py').read_text();guardian=(SOURCE/'aeris_runtime/emulator.py').read_text();preview=(SOURCE/'aeris_runtime/preview10.py').read_text()
  self.assertIn("'--seconds',str(self.planned_seconds)",runtime);self.assertIn('free,self.planned_seconds)',runtime);self.assertIn('free,seconds)',guardian);self.assertIn('free,seconds)',preview);self.assertIn("p.add_argument('--seconds',required=True",guardian)
  for s in (runtime,guardian,preview):self.assertNotIn('free,180)',s)
 def test_original_guard_and_durability_bytes(self):
  for name in ('product_writer.py','product_trace15.py','metadata_budget.py','host_health.py','monitor.py','policy.py','resources.py','flight_interval.py','foundation/transport.py'):
   with self.subTest(name=name):self.assertEqual((SOURCE/'aeris_runtime'/name).read_bytes(),(REPO/'planning/writerstage15/runtime/source/aeris_runtime'/name).read_bytes())
 def test_new_pool_still_charges_all_historical(self):
  from aeris_runtime.candidate import artifact_roots,CAP
  roots=artifact_roots(REPO/'evidence/missionintegrated16/candidates');self.assertEqual(len(roots),10);self.assertEqual(roots[-2],REPO/'evidence/writerstage15/candidates');self.assertEqual(CAP,11*2**20)
 def test_owner_self_pin_and_normal_closure(self):
  s=(Path(__file__).parent/'root-owner-mission16.py').read_text();self.assertIn('EXACT_SOURCE_HELD_OWNER_ENTRY',s);self.assertIn("command('SEAL_PRODUCT')",s);self.assertIn('module.handoff(owner,case,raw,check)',s);self.assertNotIn('READ_ONLY_DIAGNOSTIC_COMPLETE',s)
 def test_scenario_public_only_and_restart_selected(self):
  s=(Path(__file__).parent/'scenario-mission16.py').read_text();self.assertIn("'force-stop',case['device'].APPLICATION_PACKAGE",s);self.assertIn('GENUINE_PUBLISHER_VIDEO_ADMISSION',s);self.assertIn('MOCK_GIMBAL_DURING_VIDEO',s);self.assertIn('VIDEO_AND_PAYLOAD_SERVICE_CONTINUITY',s);self.assertIn('duration=5;',s);self.assertIn('INTEGRATED_AIRBORNE_VIDEO_PAYLOAD_INTERVAL',s);self.assertIn('NO_PAYLOAD_TAP_DURING_POINTER',s);self.assertNotIn("ui.tap('b-cut')",s);self.assertNotIn("ui.tap('b-reboot')",s)
if __name__=='__main__':unittest.main(verbosity=2)
