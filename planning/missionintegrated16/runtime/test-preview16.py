"""Actual read-only Inventory+policy previews. No fabricated inventory or actors.
Candidate validation explicitly OFF here because packaging is separately blocked;
this is current-namespace arithmetic, not frozen-candidate/native admission.
"""
from pathlib import Path
import json,os,sys,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];S=Path(__file__).parent/'source';os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(S),str(R)]
from aeris_runtime.preview10 import preview
from aeris_runtime.inventory import Inventory,NOMINAL_SLOTS
from aeris_runtime.mission16 import SLOTS
class Preview(unittest.TestCase):
 def test_actual_namespace_short_and_long_real_inventory(self):
  root=R/'evidence/missionintegrated16';selected=root/'candidates'/('f'*64);self.assertTrue((root/'candidates').is_dir());self.assertFalse(selected.exists())
  results=[]
  with patch.dict(os.environ,{'AERIS_CANDIDATE_DIR':str(selected),'AERIS_CANDIDATE_SHA256':'f'*64}),patch.object(Path,'mkdir',side_effect=AssertionError('preview must notmkdir')),patch.object(Path,'write_bytes',side_effect=AssertionError('preview must notwrite')),patch.object(Path,'write_text',side_effect=AssertionError('preview must notwrite')):
   for slot,seconds in [('s01',180),('l01',760)]:
    self.assertFalse((root/slot).exists());v=preview(selected,'f'*64,root/slot,R/'planning/missionintegrated16',R/'evidence/navfix13/emulator-spec.json',validate_candidate=False,seconds=seconds);self.assertEqual(v['plannedSeconds'],seconds);self.assertFalse(v['slotCreated']);self.assertFalse(v['actorsStarted']);self.assertFalse(v['ledgerConstructed']);self.assertGreater(v['inventory']['artifactBytes'],0);self.assertEqual(v['diskBudget']['requiredFreeBytes'],12616295040 if seconds==180 else 15075000960);self.assertFalse((root/slot).exists());results.append({'slot':slot,'plannedSeconds':seconds,'metadataAdmitted':v['metadataAdmitted'],'metadataHeadroom':v['metadataHeadroom'],'diskAdmitted':v['diskAdmitted'],'requiredFreeBytes':v['diskBudget']['requiredFreeBytes'],'artifactUnionBytes':v['artifactUnionBytes']})
  print(json.dumps({'actualReadOnlyNamespacePreviews':results,'frozenCandidateAdmissionPerformed':False}))
 def test_wrong_duration_fault_unknown_refused_before_inventory(self):
  root=R/'evidence/missionintegrated16'
  with patch('aeris_runtime.preview10.Inventory',side_effect=AssertionError('no inventory forinvalidslot')):
   for slot,seconds in [('l01',180),('s01',760),('f01',180),('f02',180),('s03',180)]:
    with self.subTest(slot=slot,seconds=seconds),self.assertRaisesRegex(ValueError,'NOMINAL_SLOT_DURATION'):preview(root/'candidates'/('f'*64),'f'*64,root/slot,R/'planning/missionintegrated16',R/'evidence/navfix13/emulator-spec.json',validate_candidate=False,seconds=seconds)
 def test_inventory_and_allocation_share_exact_nominal_slotset(self):
  self.assertIs(NOMINAL_SLOTS,SLOTS);self.assertEqual(set(NOMINAL_SLOTS),{'s01','s02','l01'});self.assertNotIn('f01',NOMINAL_SLOTS);self.assertNotIn('f02',NOMINAL_SLOTS)
if __name__=='__main__':unittest.main(verbosity=2)
