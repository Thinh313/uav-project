"""Frozen old graph remains loadable; selected graph pins versioned entry paths."""
from pathlib import Path
import json,os,subprocess,sys,unittest
R=Path(__file__).resolve().parents[3];S=Path(__file__).parent/'source';sys.path[:0]=[str(S),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
class EntryVersioningTests(unittest.TestCase):
 def test_old_frozen_S01_full_load_in_exact_fresh_source_process(self):
  e=R/'evidence/writerstage15';f=json.loads((e/'FROZEN-CANDIDATE01.json').read_bytes());p=Path(f['path']);digest=f['sha256'];code="from pathlib import Path;import os,sys,json;source=Path(sys.argv[1]);repo=Path(sys.argv[2]);digest=sys.argv[3];os.environ.update(AERIS_REPOSITORY_ROOT=str(repo),AERIS_CANDIDATE_DIR=str(source),AERIS_CANDIDATE_SHA256=digest);sys.path[:0]=[str(source/'source'),str(repo)];from aeris_runtime.candidate import load;v=load(source,digest);print(json.dumps({'status':'OLD_FROZEN_FULL_LOAD_ONLY_NOT_STARTUP_OR_FLIGHT','candidate':digest,'sourceFiles':len(v['sourceSHA256']),'productPins':len(v['productSourceSHA256']),'artifactCapBytes':v['artifactCapBytes'],'actorsStarted':False}))"
  v=subprocess.run([sys.executable,'-B','-c',code,str(p),str(R),digest],capture_output=True,timeout=30,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'});self.assertEqual(v.returncode,0,v.stderr.decode());self.assertEqual(v.stderr,b'');out=json.loads(v.stdout);self.assertEqual(out['candidate'],digest);self.assertFalse(out['actorsStarted']);self.assertEqual(out['status'],'OLD_FROZEN_FULL_LOAD_ONLY_NOT_STARTUP_OR_FLIGHT')
 def test_new_graph_pins_only_versioned_new_entrypaths(self):
  from aeris_runtime.product_inputs import validate
  v=validate();pins=v['pins']
  for name in ('root-owner-writerstage15-r03.py','preview-admission-r03.py'):self.assertIn('planning/writerstage15/runtime/'+name,pins)
  for name in ('root-owner-writerstage15.py','preview-admission.py'):self.assertNotIn('planning/writerstage15/runtime/'+name,pins)
if __name__=='__main__':unittest.main(verbosity=2)
