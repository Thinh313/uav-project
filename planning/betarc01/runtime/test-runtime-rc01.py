"""No actors: pure RC contracts, strict native boundary and source invariants."""
from pathlib import Path
import ast,hashlib,json,os,sys,tempfile,time,unittest
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;os.environ['AERIS_REPOSITORY_ROOT']=str(ROOT);sys.path[:0]=[str(HERE/'source'),str(ROOT)]
from aeris_runtime.rc01 import generation_forecast,GENERATIONS,REMAINING
from aeris_runtime.fault_rc01 import reboot_request,airborne
from aeris_runtime.mission16 import nominal_duration
class RCContracts(unittest.TestCase):
 def test_source_fixed_generation_plan(self):
  for slot,active in [('g201',0),('g203',2),('g301',0),('g302',1),('g303',2),('g401',4)]:
   p=generation_forecast(active,slot,remaining_generations=REMAINING[slot]);self.assertLessEqual(p['projectedMaximumActive'],8);self.assertEqual(p['repairReserve'],2);self.assertFalse(p['refundOrReset'])
 def test_caller_cannot_discount_remaining(self):
  for slot in ['g201','g301','g302','g303']:
   with self.assertRaisesRegex(ValueError,'NO_CALLER_DISCOUNT'):generation_forecast(0,slot,remaining_generations=0)
 def test_full_active_refuses_before_start(self):
  for slot in GENERATIONS:
   with self.assertRaises(ValueError):generation_forecast(8,slot,remaining_generations=REMAINING[slot])
 def test_bool_count_is_not_integer(self):
  with self.assertRaises(ValueError):generation_forecast(True,'g401',remaining_generations=0)
 def test_exact_source_slots_and_durations(self):
  for slot,seconds in [('m101',180),('m201',180),('g101',180),('g201',180),('g301',180),('g401',760)]:self.assertEqual(nominal_duration(slot,seconds),seconds)
  for slot,seconds in [('g401',180),('g201',760),('l01',760),('g201',True)]:
   with self.assertRaises(ValueError):nominal_duration(slot,seconds)
 def test_numeric_guard_core_byte_exact(self):
  base=ROOT/'planning/nativejournal17/runtime/source/aeris_runtime';current=HERE/'source/aeris_runtime'
  for name in ['policy.py','host_power14.py','product_writer.py','backend.py','foundation/transport.py','resources.py','foundation/journal_base.py']:
   if not(base/name).exists():continue
   self.assertEqual((base/name).read_bytes(),(current/name).read_bytes(),name)
 def test_present_only_install_selected_contains_no_install_command(self):
  p=HERE/'source/aeris_runtime/product_native09.py';t=ast.parse(p.read_text());f=next(n for n in ast.walk(t)if isinstance(n,ast.FunctionDef)and n.name=='install_selected');text=ast.get_source_segment(p.read_text(),f);self.assertIn('RC01_PRESENT_REVIEWED_APK_REQUIRED_NO_INSTALL',text)
  for n in ast.walk(f):
   if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='command'and n.args and isinstance(n.args[0],ast.List)and n.args[0].elts and isinstance(n.args[0].elts[0],ast.Constant):self.assertNotEqual(n.args[0].elts[0].value,'install')
 def test_source_native_only_condition_preserved(self):
  s=(ROOT/'planning/betarc01/product/main-session-codec09c.mjs').read_text();self.assertIn("if(descriptor.nativeOnlyScope17)throw Error('RC01_NATIVE_GATE_FLIGHT_FORBIDDEN')",s);self.assertIn("if(descriptor.nativeOnlyScope17)throw Error('RC01_NATIVE_GATE_PAYLOAD_FORBIDDEN')",s)
 def test_only_fullflight_uses_new_archive_verifier(self):
  s=(HERE/'source/aeris_runtime/product_runtime.py').read_text();self.assertIn("if not self.root.name.startswith('g1'):",s);self.assertIn("value['journalLifecycle17']['archiveVerifierSHA256']",s);self.assertIn('planning/betarc01/archive/archive_rc01.py',s)
 def test_actual_fault_has_no_encoder_or_shell_kill(self):
  s=(HERE/'source/aeris_runtime/fault_rc01.py').read_text();self.assertNotIn('MAV_CMD',s);self.assertNotIn('docker',s);self.assertIn('raw/cut-request.json',s.replace("/'raw/cut-request.json'","/'raw/cut-request.json'"));self.assertIn('REBOOT_OWNED_AP',s)
 def test_no_generic_alive_guard_suppression(self):
  s=(HERE/'source/aeris_runtime/product_runtime.py').read_text();self.assertIn("for name in c['resources'].children:c['resources'].require_alive(name)",s)
 def test_long_interval_remains_airborne(self):
  s=(HERE/'scenario-rc01.py').read_text();self.assertIn('integrated_start+600_000_000_000',s);self.assertIn("'INTEGRATED_AIRBORNE_CONTINUITY'",s);self.assertIn("'INTEGRATED_VIDEO_PAYLOAD_CONTINUITY'",s);self.assertIn("'originalCRCAndVideoColdJoinRequired':True",s)
 def test_full_argv_sources_are_graph_located(self):
  s=(HERE/'root-owner-rc01.py').read_text();self.assertIn('module_origin_receipt(CANDIDATE)',s);self.assertIn('planning/nativejournal17/runtime/verified-loader.mjs',s);self.assertIn('planning/betarc01/runtime/product-companion-rc01.mjs',s)
 def test_corridor_chosen_through_public_ui(self):
  s=(HERE/'scenario-rc01.py').read_text();self.assertIn("ui.choose('sitl-kind','Corridor hành lang')",s);self.assertNotIn("api('native/sitl-fixture'",s)
 def test_reboot_request_strict_identity_and_clock(self):
  cfg={'run':'run','epoch':'e','boot':'a'*32};now=10_000_000_000;q={**cfg,'action':'REBOOT_OWNED_AP','nonce':'b'*32,'hostNs':now,'newAPBoot':'c'*32}
  with tempfile.TemporaryDirectory(prefix='rc01-request-',dir=HERE)as tmp:
   p=Path(tmp)/'request.json';p.write_text(json.dumps(q));self.assertEqual(reboot_request(p,cfg,now),q)
   for wrong in [{**q,'boot':'d'*32},{**q,'hostNs':now-2_000_000_001},{**q,'hostNs':now+1},{**q,'newAPBoot':cfg['boot']},{**q,'extra':1}]:
    p.write_text(json.dumps(wrong))
    with self.assertRaises(ValueError):reboot_request(p,cfg,now)
 def test_airborne_needs_original_crc_prefix(self):
  from types import SimpleNamespace
  now=10_000_000_000;h={'hostNs':now,'armed':True};p={'hostNs':now,'relativeAltitudeMm':4000};w=SimpleNamespace(h=h,p=p,prefix={'sequence':3,'sha256':'a'*64});case={'reader':SimpleNamespace(witness=w)};self.assertEqual(airborne(case,now)['position'],p);w.h={**h,'armed':False}
  with self.assertRaises(ValueError):airborne(case,now)
  w.h=h;w.prefix=None
  with self.assertRaises(ValueError):airborne(case,now)
 def test_additional_selected_inputs_charged_no_new_external_role(self):
  s=(HERE/'source/aeris_runtime/inventory.py').read_text();self.assertIn('for name in self.selected_input_names:',s);self.assertIn('metadata+=physical;source_bytes+=physical;selected_extra_bytes+=physical',s);self.assertIn("'additionalSelectedInputMetadataBytes':selected_extra_bytes",s)
 def test_long_cannot_start_from_short_alone(self):
  from aeris_runtime.acceptance_rc01 import require_prerequisites
  with self.assertRaisesRegex(ValueError,'MISSING_PREREQUISITES'):require_prerequisites('integrated',[],{},'a'*64)
 def test_g3_requires_both_shapes_and_native(self):
  from aeris_runtime.acceptance_rc01 import PREREQUISITES
  for kind in('link-loss','ap-reboot','native-restart'):self.assertEqual(PREREQUISITES[kind],{'native','polygon','corridor'})
 def test_whole_release_includes_g1_g3_not_only_long(self):
  from aeris_runtime.acceptance_rc01 import CASE_GATES
  self.assertEqual(set(CASE_GATES),{'native','polygon','corridor','link-loss','ap-reboot','native-restart','integrated'})
 def test_full_crypto_command_not_unused(self):
  s=(HERE/'root-owner-rc01.py').read_text();self.assertIn("command('VERIFY_NATIVE_INPUTS')",s);self.assertNotIn("command('VERIFY_NATIVE_UNUSED17')",s);self.assertIn("qualify_closed(owner,case,args.node)",s)
 def test_syntax_all_source(self):
  for p in (HERE/'source').rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
if __name__=='__main__':unittest.main()
