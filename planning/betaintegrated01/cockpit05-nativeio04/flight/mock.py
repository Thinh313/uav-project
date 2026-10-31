"""Static/pure new-package boundaries. No ADB/process/socket/AP invocation."""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
import ast,hashlib,json,subprocess,socket,shutil
R=Path(__file__).resolve().parents[4];H='planning.betaintegrated01.cockpit05-nativeio04.flight';C=import_module(H+'.contract');P=import_module(H+'.preservation');E=R/C.EVIDENCE/'host/mock01'
def denied(*a,**kw):raise AssertionError('NO_RUNTIME_ALLOWED')
def main():
 E.mkdir(parents=True,exist_ok=False);cases=[]
 def test(name,fn):
  try:cases.append({'case':name,'pass':True,'detail':fn()})
  except Exception as e:cases.append({'case':name,'pass':False,'error':repr(e)})
 def imports():
  with patch.object(subprocess,'run',denied),patch.object(subprocess,'Popen',denied),patch.object(socket,'socket',denied):
   for name in('contract','resources','android_guardian','actual_controller','actual_combined_cold','short_cold','capture_external','make_confirmation','setup_ui','receiver05','export_native'):
    import_module(H+'.'+name)
  return 'All imports without device/process/network'
 test('no import-time runtime',imports)
 def closure():
  v=C.build_input_contract();assert v['package']=='vn.rtr.aeris.cockpitio04'and v['newActualDraftRevision']==1 and v['runtimeEntryModule']==C.OLD.RUNTIME
  old=json.loads((R/'evidence/betaintegrated01-cockpit05-clockflight02/host/input-contract01.json').read_text());assert all(v['sourceSHA256'][k]==h for k,h in old['sourceSHA256'].items())
  assert all(v['metadataSHA256'][k]==h for k,h in old['metadataSHA256'].items());return {'oldInputsPreserved':len(old['sourceSHA256']),'newTotal':len(v['sourceSHA256']),'oldMetadata':len(old['metadataSHA256']),'newMetadata':len(v['metadataSHA256'])}
 test('exact frozen runtime+oldclosure+newAPK37 zip/providers',closure)
 def oldmap():
  m=P.expected_old();raw=''.join(h+'  '+name+'\n'for name,h in m.items()).encode();assert P.parse_private_map(raw)==m
  try:P.parse_private_map(raw.splitlines(keepends=True)[0])
  except ValueError:pass
  else:raise AssertionError('incompleteoldmapaccepted')
  return {'oldPrivateFiles':len(m),'rootCloseoutSHA256':C.sha(R/C.BASELINE_RECEIPT)}
 test('actual old233 baseline and incomplete-map reject',oldmap)
 def operators():
  for old,new in [('cockpit05_android_operator.py','cockpitio04_android_operator.py'),('cockpit05_root_operator.py','cockpitio04_root_operator.py')]:
   original=(R/'planning/betaintegrated01/cockpit05-soak/android'/old).read_text().replace('vn.rtr.aeris.cockpit05','vn.rtr.aeris.cockpitio04').replace('from cockpit05_android_operator import','from cockpitio04_android_operator import');assert original==(Path(__file__).parent/new).read_text()
  return 'Two explicit modules exact namespace substitution; no frozen-global monkeypatch'
 test('RootOperator package isolation exact control body',operators)
 def budget():
  for duration in(180,1960):
   b=C.case_budget(maximum_seconds=duration);assert b['requiredFreeBytes']==C.policy().case_budget(maximum_seconds=duration)['requiredFreeBytes']+4*2**20;assert not C.case_budget(b['requiredFreeBytes']-1,duration)['admitted'];assert C.case_budget(b['requiredFreeBytes'],duration)['admitted']
  return {'shortRequiredGiB':C.case_budget(maximum_seconds=180)['requiredFreeBytes']/2**30,'longRequiredGiB':C.case_budget(maximum_seconds=1960)['requiredFreeBytes']/2**30,'artifactArchiveReserveBytes':4*2**20}
 test('additional isolatedartifact/archive reserve and exact admission boundary',budget)
 def ui():
  s=import_module(H+'.setup_ui');tree=ast.parse(Path(s.__file__).read_text());klass=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='Setup');methods={x.name:x for x in klass.body if isinstance(x,ast.FunctionDef)}
  prepare=ast.unparse(methods['prepare_r1']);save=ast.unparse(methods['save_r1']);assert '270, 547'in prepare and 'SAVE['not in prepare;assert save.count('self.bytes(')==1 and 'reviewed' in save
  assert 'keyevent'not in save and 'STATE'not in save and '.evaluate'not in save;return 'Prepare referencequad/name then separate fresh-reviewed ONE save; no JS/native flight API'
 test('UI r1 preparation/save separated, no blind second save',ui)
 value={'status':'PASS'if all(x['pass']for x in cases)else'FAIL','cases':cases,'actualAndroidAPSITLOrServices':False,'actualUIVisualVerification':False};(E/'results.json').open('x').write(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2));assert value['status']=='PASS'
if __name__=='__main__':main()
