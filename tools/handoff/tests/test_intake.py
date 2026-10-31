"""Portable unittest entry. Only tiny fixture helpers are copied/generated."""
import json,os,tempfile,unittest
from pathlib import Path
import private_bundle_test,source_verify_test
class IntakeTests(unittest.TestCase):
 def parent(self):
  p=Path(os.environ.get('HANDOFF_TEST_ROOT',tempfile.gettempdir())).resolve();self.assertTrue(p.is_dir());return p
 def test_private_bundle_adversarial(self):
  result=private_bundle_test.run(self.parent());self.assertEqual(result['status'],'PASS');self.assertGreaterEqual(result['checks'],30);print(json.dumps(result,sort_keys=True))
 def test_public_source_kind_and_containment(self):
  result=source_verify_test.run(self.parent());self.assertEqual(result['status'],'PASS');self.assertEqual(result['checks'],8);print(json.dumps(result,sort_keys=True))
if __name__=='__main__':unittest.main()
