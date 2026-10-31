"""Small prebuild policy/inventory mock, explicit synthetic native selection, no device/runtime."""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
import json,copy,hashlib,shutil
R=Path(__file__).resolve().parents[3];H='planning.betaintegrated01.cockpit05-clockterm14.flight';C=import_module(H+'.contract');I=import_module(H+'.private_inventory');X=import_module(H+'.cancellation');E=R/'evidence/betaintegrated01-cockpit05-clockterm14/host';S=E/'helpers-scratch01'
def run():
 E.mkdir(parents=True,exist_ok=True);S.mkdir(exist_ok=False);results=[]
 def check(name,fn,ok=True):
  try:fn();passed=ok;error=None
  except Exception as e:passed=not ok;error=type(e).__name__+':'+str(e)
  results.append(dict(case=name,pass_=passed,error=error));assert passed,(name,error)
 class Op:
  def __init__(self,dirs,rows=b''):self.dirs=dirs;self.rows=rows;self.commands=[]
  def command(self,args,**kw):
   self.commands.append(args)
   if args[:4]==['shell','run-as',C.PACKAGE,'ls']:
    root=args[-1];value=self.dirs.get(root,'missing')
    if value=='missing':return b'',('ls: '+root+': No such file or directory\n').encode(),1,S
    if value=='denied':return b'',b'Permission denied\n',1,S
    if value=='link':return ('lrwx '+root+'\n').encode(),b'',0,S
    return ('drwx------ 2 uid uid 4096 '+root+'\n').encode(),b'',0,S
   if args[:4]==['exec-out','run-as',C.PACKAGE,'find']:return self.rows,b'',0,S
   raise AssertionError('NON_READ_COMMAND:'+repr(args))
 try:
  op=Op({});check('all_real_absence_is_empty_without_find_or_mkdir',lambda:None if I.inventory(op,allow_empty=True)['files']=={}and not any('find'in x or 'mkdir'in x for x in op.commands)else(_ for _ in()).throw(AssertionError()))
  check('unknown_permission_is_not_empty',lambda:I.inventory(Op({'files/control-runs':'denied'}),allow_empty=True),False)
  check('symlink_is_not_directory',lambda:I.inventory(Op({'files/control-runs':'link'}),allow_empty=True),False)
  check('empty_requires_declared_empty_phase',lambda:I.inventory(Op({})),False)
  op=Op({'files/workspace03':'dir'},('a'*64+'  files/workspace03/draft-000001-'+('a'*64)+'.json\n').encode());check('real_r1_with_other_dirs_absent',lambda:None if len(I.inventory(op)['files'])==1 else(_ for _ in()).throw(AssertionError()))
  check('find_error_never_empty',lambda:I.inventory(Op({'files/workspace03':'dir'},b'find: bad path\n'),allow_empty=True),False)
  check('unsafe_root_before_command',lambda:I.inventory(Op({}),['files/../outside'],allow_empty=True),False)
  proto=S/'protocol.json';proto.write_text('{"format":"SYNTHETIC_UNIT_PROTOCOL_NOT_SELECTED_NATIVE"}\n');fake={'sha256':'a'*64,'sourceSHA256':'b'*64,'sourcePins':{'synthetic-unit.java':'c'*64,str(proto.relative_to(R)):hashlib.sha256(proto.read_bytes()).hexdigest()}}
  with patch.object(C,'build_receipt',lambda:fake),patch.object(C,'PROTOCOL',proto),patch.object(C,'IOPROTOCOL',proto),patch.object(C,'TERMINAL_PROTOCOL',proto):
   cfg=C.build_config(R,'nominal','ioadmit13-unit','epoch','boot',S/'raw','unit-case',maximum_seconds=180);before=json.dumps(cfg,sort_keys=True)
   check('actual_new_host_top_accepts_client_overlay',lambda:C.policy().validate_recording_policy(cfg))
   check('exact_new_native_client_overlay',lambda:C.validate_native_selection(cfg))
   for name,key,value in [('bool_version','version',True),('old_package','package','vn.rtr.aeris.cockpitio10'),('wrong_apk','APK_SHA256','0'*64),('wrong_protocol','cancellationProtocolSHA256','0'*64)]:
    bad=copy.deepcopy(cfg);bad['externalNativeClientSelection'][key]=value;check(name,lambda bad=bad:C.validate_native_selection(bad),False)
   bad=copy.deepcopy(cfg);del bad['externalNativeClientSelection'];check('missing_client_selection',lambda:C.validate_native_selection(bad),False)
   assert json.dumps(cfg,sort_keys=True)==before
  for seconds in(180,1960):
   base=C.policy().case_budget(maximum_seconds=seconds);b=C.case_budget(maximum_seconds=seconds);assert b['taskHardPeakBytes']==base['taskHardPeakBytes']+4*2**20 and b['requiredFreeBytes']==base['requiredFreeBytes']+4*2**20;assert b['nativeExportCapBytes']==(23.75 if seconds==180 else 167.75)*2**20
   check('artifact4MiB_exact_admission_'+str(seconds),lambda seconds=seconds,b=b:None if C.case_budget(b['requiredFreeBytes'],seconds)['admitted']and not C.case_budget(b['requiredFreeBytes']-1,seconds)['admitted']else(_ for _ in()).throw(AssertionError()))
  campaign=C.campaign_budget();assert sum(campaign['nativeOriginalParts'].values())==512*2**20 and campaign['globalMetadataCapBytes']==64*2**20 and campaign['globalExportCapBytes']==192*2**20;check('native_parts_and_global_caps_exact',lambda:None)
  for raw in (b'{"raw":{"x":-0.0,"y":1e-7,"s":"\\u00e9"}}',b'{"p":1,"raw":{"x":-0,"y":1E+9,"s":"\xc3\xa9"}}',b'{"raw":{"n":{"a":["a\\\"b",1.0]}},"tail":0}'):
   got=X.exact_member_bytes(raw,'raw');assert X.strict(got)==X.strict(raw)['raw'];check('exact_raw_numeric_and_escape_lexeme',lambda:None)
  result=dict(status='PASS_PREBUILD_HELPER_SEAMS_ONLY',cases=results,fixture='SYNTHETIC_NATIVE_SELECTION_WITH_REAL_NEW_EXPLICIT_HOST_POLICY;NOT_REAL_NATIVE_SOURCE_OR_ADMISSION',runtimeExecuted=False,deviceCommands=False,actualGuardPrime=False,frozenModulesPatched=False,newModuleUnitSeamsPatched=True,scratchRemoved=True)
  (E/'helper-unit01.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],cases=len(results))))
 finally:shutil.rmtree(S)
if __name__=='__main__':run()
