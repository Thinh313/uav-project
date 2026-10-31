"""New APK closure + synthetic retained-command diagnostic export. No real device."""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
from copy import deepcopy
import json,hashlib,subprocess,socket,shutil
R=Path(__file__).resolve().parents[4];H='planning.betaintegrated01.cockpit05-nativeio06.flight';C=import_module(H+'.contract');D=import_module(H+'.diagnostic');M=import_module(H+'.mock');E=R/C.EVIDENCE/'host/integration-mock01'
def main():
 E.mkdir(parents=True,exist_ok=False);scratch=E/'scratch';scratch.mkdir();cases=[]
 def test(name,fn):
  try:cases.append({'case':name,'pass':True,'detail':fn()})
  except Exception as e:cases.append({'case':name,'pass':False,'error':repr(e)})
 def deny(*a,**kw):raise AssertionError('ACTUAL_RUNTIME_FORBIDDEN')
 def imports():
  with patch.object(subprocess,'run',deny),patch.object(subprocess,'Popen',deny),patch.object(socket,'socket',deny):
   for p in Path(__file__).parent.glob('*.py'):
    if p.stem not in('mock','integration_mock'):import_module(H+'.'+p.stem)
  return 'No ADB/process/socket calls on imports'
 test('no import-time runtime',imports)
 def closure():
  v=C.build_input_contract();old=json.loads((R/'evidence/betaintegrated01-cockpit05-observer05/host/input-contract01.json').read_text());assert all(v['sourceSHA256'][n]==h for n,h in old['sourceSHA256'].items());assert all(v['metadataSHA256'][n]==h for n,h in old['metadataSHA256'].items());assert v['selectedAPKInputs']==38 and v['package']=='vn.rtr.aeris.cockpitio06';return {'old263SourcesPreserved':len(old['sourceSHA256']),'old12MetadataPreserved':len(old['metadataSHA256']),'newSources':len(v['sourceSHA256']),'newMetadata':len(v['metadataSHA256']),'newAPK38Pins':True}
 test('newAPK02 exact38/source/zip/providers andold263+12 closure',closure)
 def diagnostic():
  control=scratch/'control';control.mkdir();android=control/'android';android.mkdir();context=M.CONTEXT;v=M.fixture();v['APKSourceSHA256']=C.SOURCE_SHA256;raw=json.dumps(v).encode();path=D.diagnostic_path(context['run']);state={**{k:context[k]for k in('run','epoch','boot','generation')},'closed':True,'journal':{'closed':True,'commitAnchor':'d'*64}};(control/'native-last-external-observation.json').write_text(json.dumps(state))
  class Resource:
   def check(self,*a):pass
  class Op:
   count=0
   def state(self,**kw):return state
   def command(self,args,**kw):
    self.count+=1;directory=android/('%04d-adb'%self.count);directory.mkdir()
    if args[-3:-1]==['wc','-c']:out=(str(len(raw))+' '+path+'\n').encode()
    elif 'sha256sum'in args:out=(D.sha(raw)+'  '+path+'\n').encode()
    elif 'cat'in args:out=raw
    else:raise AssertionError(args)
    (directory/'stdout.bin').write_bytes(out);(directory/'stderr.bin').write_bytes(b'');receipt={'argv':['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','-s','emulator-5582',*args],'exit':0,'timedOut':False,'stdoutSHA256':D.sha(out),'stdoutBytes':len(out)};(directory/'receipt.json').write_text(json.dumps(receipt));return out,b'',0,directory
  exporter=import_module(H+'.export_native')
  with patch.object(exporter,'exports',lambda:[]):result=D.capture(Op(),control,context,Resource())
  proof=D.verify(control,context);assert Path(result['artifactPath']).name=='stdout.bin'and len(list(control.glob('native-io-diagnostic*.json')))==1
  p=Path(result['artifactPath']);old=p.read_bytes();p.write_bytes(old+b' ')
  try:D.verify(control,context)
  except ValueError:pass
  else:raise AssertionError('diagnostictamperaccepted')
  p.write_bytes(old);proof['fixtureSyntheticDeviceOnly']=True;return proof
 test('canonicalbounded diagnostic deviceSHA/retainedcommands/context/cert/closedproof andtamper',diagnostic)
 removed=sum(p.stat().st_size for p in scratch.rglob('*')if p.is_file());shutil.rmtree(scratch);value={'status':'PASS'if all(x['pass']for x in cases)else'FAIL','cases':cases,'realDeviceOrAPOrNetworkServices':False,'syntheticCommandReceiptsNotActualADB':True,'scratchRemoved':True,'removedBytes':removed};(E/'results.json').open('x').write(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2));assert value['status']=='PASS'
if __name__=='__main__':main()
