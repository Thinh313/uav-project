"""Read-only reboot context/state contracts; real files, no AP/Android actors."""
from pathlib import Path
import copy,json,os,sys,tempfile,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(HERE/'source'),str(R)]
from aeris_runtime import state_binding as s
from aeris_runtime.reboot_rc01 import no_native_ingress
from aeris_runtime.telemetry import CommittedTransportReader
class RebootProbe(unittest.TestCase):
 def config(self):
  old={'run':'old','epoch':'1'*32,'boot':'2'*32,'operator':'ROOT-LAB','generation':'3'*32,'profileId':'WORKBENCH_SIM_V1'};new={**old,'run':'new','epoch':'4'*32,'boot':'5'*32,'generation':'6'*32};return {'run':new['run'],'epoch':new['epoch'],'boot':new['boot'],'caseID':'probe','wipeState':False,'readOnlyBootProbeRC01':{'format':'aeris-readonly-ap-boot-probe-rc01','version':1,'context':new,'priorContext':old,'oldFaultSHA256':'a'*64,'stateMode':'COLD_CONFIG_NO_EEPROM_OR_MISSION_RETENTION_CLAIM','oldStateUntouched':True,'authorityRestorable':False,'nativeActivityStarted':False}}
 def test_fresh_readonly_state_no_wipe_no_retention_claim(self):
  with tempfile.TemporaryDirectory(prefix='readonly-boot-mock-',dir=HERE)as tmp:
   p=Path(tmp)/'AP-state';cfg=self.config();before=copy.deepcopy(cfg);created=s.prepare_readonly_probe_state(p,cfg)
   with patch.object(s.policy,'validate_recording_policy',return_value={}),patch.object(s.identity,'validate_native_selection',return_value={}):proof=s.validate_state(cfg,p,Path(tmp)/'raw')
   self.assertEqual(cfg,before);self.assertFalse(proof['wipeState']);self.assertFalse(proof['missionRetentionProven']);self.assertFalse(proof['EEPROMRetentionProven']);self.assertEqual((p/'message-intervals-chan1.txt').read_bytes(),s.PROBE_INTERVAL_BYTES);self.assertIn(b'33 200\n',s.PROBE_INTERVAL_BYTES);self.assertIn(b'2 1000\n',s.PROBE_INTERVAL_BYTES);self.assertEqual(s.INTERVAL_BYTES,b'0 200\n245 250\n242 1000\n')
 def test_no_fake_native_or_command_writer(self):
  text=(HERE/'source/aeris_runtime/reboot_rc01.py').read_text();entry=(HERE/'root-observe-reboot-rc01.py').read_text();self.assertIn("c['native'].latest is None",text);self.assertIn("c['writer'].server is None",text);self.assertNotIn('start_writer(',entry);self.assertNotIn('start_companion(',entry);self.assertNotIn(".command([",entry);self.assertIn("originalCRCGlobalPositionWithBootMs",text);self.assertIn("'bootClockRegressionClaimed':False",text)
 def test_new_context_wipe_or_authority_forgery_refuses(self):
  base=self.config()
  for key,val in [('authorityRestorable',True),('nativeActivityStarted',True),('oldStateUntouched',False)]:
   cfg=copy.deepcopy(base);cfg['readOnlyBootProbeRC01'][key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):s.readonly_probe_marker(cfg)
  cfg=copy.deepcopy(base);cfg['wipeState']=True
  with self.assertRaises(ValueError):s.readonly_probe_marker(cfg)
  cfg=copy.deepcopy(base);cfg['readOnlyBootProbeRC01']['context']['boot']=cfg['readOnlyBootProbeRC01']['priorContext']['boot'];cfg['boot']=cfg['readOnlyBootProbeRC01']['context']['boot']
  with self.assertRaises(ValueError):s.readonly_probe_marker(cfg)
 def test_existing_state_never_erased_or_reused_as_fresh(self):
  with tempfile.TemporaryDirectory(prefix='readonly-boot-mock-',dir=HERE)as tmp:
   p=Path(tmp)/'AP-state';p.mkdir();f=p/'eeprom.bin';f.write_bytes(b'KEEP_ORIGINAL')
   with self.assertRaises(ValueError):s.prepare_readonly_probe_state(p,self.config())
   self.assertEqual(f.read_bytes(),b'KEEP_ORIGINAL')
 def test_native_zero_requires_complete_original_prefix_and_no_ingress(self):
  r=CommittedTransportReader(HERE, self.config()['readOnlyBootProbeRC01']['context']);r.witness.prefix={'sequence':r.seq,'sha256':r.head};self.assertEqual(no_native_ingress(r),r.witness.prefix)
  for key,value in [('native_connection_seen',True),('native_bytes_seen',True),('pending_forward_seen',True),('forward_unknown',True),('forward_intent',('toAP',b'x')),('forward_pending',{'toAP':b'x','toNative':b''})]:
   old=getattr(r,key);setattr(r,key,value)
   with self.subTest(key=key),self.assertRaises(ValueError):no_native_ingress(r)
   setattr(r,key,old)
  r.witness.prefix=None
  with self.assertRaises(ValueError):no_native_ingress(r)
 def test_old_fault_context_never_restarts_child(self):
  text=(HERE/'source/aeris_runtime/ap_supervisor.py').read_text();self.assertNotIn('observe_reboot(',text);self.assertIn("'replacementStartedInOldContext':False",text);self.assertIn("'requiresSeparatelyAdmittedNewContext':True",text)
if __name__=='__main__':unittest.main(verbosity=2)
