"""Read-only launch-profile decision mocks. No Docker, AP, native or UI execution."""
from pathlib import Path
import copy,importlib.util,json,sys,unittest
P=Path(__file__).parent;E=P.parents[1]/'evidence/beta06/generation02';spec=importlib.util.spec_from_file_location('native_profile_gate',P/'qa-ap-admission.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixture():
 return {'qualifiedProfile':m.QUALIFIED_PROFILE,'binarySha256':m.QUALIFIED_BINARY,'binaryPath':m.QUALIFIED_PATH,'platform':'linux/arm64','observerEnabled':False,'imageId':m.QUALIFIED_IMAGE,'port':5972,'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_SIM32_OR_HERA','speedup':1,'hardDeadlineS':540,'attemptTotalMaximumS':600,'containerId':'a'*64,'pid':123,'command':['/usr/local/bin/docker','run','--platform','linux/arm64','--pull','never','--network','bridge','--cpus','1','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges','-p','127.0.0.1:5972:5760','-v',str(m.R/m.QUALIFIED_PATH)+':/aeris/arducopter:ro','-e','AERIS_DIRECT_TRACE=0','rtr-aeris-sim32-trace-builder@'+m.QUALIFIED_IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/task/sitl.parm','--speedup','1']}
class Tests(unittest.TestCase):
 def test_exact_recorded_qualified_profile(self):self.assertTrue(m.qualified_launch_decision(fixture())['liveRuntimeAndIncomingFirmwareGuardStillRequired'])
 def test_wrong_binary_profile_image_abi_observer(self):
  for key,val in [('binarySha256','0'*64),('qualifiedProfile','old-profile'),('imageId','sha256:'+'0'*64),('platform','linux/amd64'),('observerEnabled',True),('observerEnabled',0),('speedup',2),('hardDeadlineS',541),('pid',0),('pid',True)]:
   bad=fixture();bad[key]=val
   with self.assertRaises(AssertionError):m.qualified_launch_decision(bad)
 def test_wrong_actual_command(self):
  for old,new in [('linux/arm64','linux/amd64'),('AERIS_DIRECT_TRACE=0','AERIS_DIRECT_TRACE=1'),('256m','512m'),('1','2'),('/aeris/arducopter','/aeris/entry.sh'),(str(m.R/m.QUALIFIED_PATH)+':/aeris/arducopter:ro',str(m.R/m.QUALIFIED_PATH)+':/aeris/arducopter')]:
   bad=fixture();bad['command']=[new if x==old else x for x in bad['command']]
   with self.assertRaises(AssertionError):m.qualified_launch_decision(bad)
 def test_duplicate_option_or_extra_environment_refuses(self):
  for extra in [['--platform','linux/arm64'],['-e','AERIS_DIRECT_TRACE=1'],['--entrypoint','/aeris/entry.sh'],['--env','AERIS_DIRECT_TRACE=1']]:
   bad=fixture();bad['command']=extra+bad['command']
   with self.assertRaises(AssertionError):m.qualified_launch_decision(bad)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));report={'scope':'BUILDER_RECORDED_NATIVE_ARM_LAUNCH_GATE_MOCK_NO_RUNTIME','passed':result.wasSuccessful(),'tests':result.testsRun,'failures':[(str(t),e)for t,e in result.failures+result.errors]};(E/'builder-native-profile-tests02.json').open('x').write(json.dumps(report,indent=2)+'\n');sys.exit(0 if result.wasSuccessful()else 1)
