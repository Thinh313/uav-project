"""Synthetic command receipts around actual frozen package maps; no ADB invocation."""
from pathlib import Path
from importlib import import_module
import json,hashlib,shutil
R=Path(__file__).resolve().parents[3];H='planning.betaintegrated01.cockpit05-clockterm14.flight';C=import_module(H+'.contract');P=import_module(H+'.preservation');E=C.E/'host';S=E/'preservation-scratch01';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
def sha(b):return hashlib.sha256(b).hexdigest()
class FakeOp:
 def __init__(self,root,corrupt_map=False,corrupt_diag=False):self.root=root;root.mkdir();self.n=0;self.corrupt_map=corrupt_map;self.corrupt_diag=corrupt_diag
 def command(self,args,**kw):
  self.n+=1;p=self.root/str(self.n);p.mkdir();package=args[2];err=b''
  if args[:2]==['exec-out','run-as']:
   files=P.expected_old(package);raw=''.join(h+'  '+name+'\n'for name,h in files.items()).encode()
   if self.corrupt_map and package=='vn.rtr.aeris.cockpitio12':raw=raw.replace(next(iter(files.values())).encode(),b'0'*64,1)
  elif args[:2]==['shell','run-as']:
   path,device,h,size=P.diagnostic_baseline(package)
   if self.corrupt_diag and package=='vn.rtr.aeris.cockpitio12':h='0'*64
   if args[3]=='sha256sum':raw=(h+'  '+device+'\n').encode()
   elif args[3]=='wc':raw=(str(size)+' '+device+'\n').encode()
   else:raise AssertionError(args)
  else:raise AssertionError(args)
  (p/'stdout.bin').write_bytes(raw);(p/'stderr.bin').write_bytes(err)
  (p/'receipt.json').write_text(json.dumps(dict(argv=[ADB,'-s','emulator-5582',*args],exit=0,timedOut=False,stdoutSHA256=sha(raw),stdoutBytes=len(raw),stderrSHA256=sha(err),stderrBytes=0)))
  return raw,err,0,p

def main():
 S.mkdir(exist_ok=False);cases=[]
 def check(name,fn,ok=True):
  error=None
  try:fn();accepted=True
  except Exception as e:accepted=False;error=type(e).__name__+':'+str(e)
  cases.append(dict(case=name,expected=ok,accepted=accepted,error=error));assert accepted is ok,(name,error)
 try:
  assert len(P.BASELINES)==9 and sum(n for _,n in P.BASELINES.values())==331 and len(P.DIAGNOSTICS)==7
  op=FakeOp(S/'commands');path=S/'proof.json';proof=P.observe(op,path)
  check('nine_maps331files_and_seven_diagnostics_exact_fakecommands',lambda:P.verify_observation(path))
  assert sum(x['fileCount']for x in proof['packages'])==331 and len(proof['priorDiagnostics'])==7
  check('lost_release12_map_byte_rejected',lambda:P.observe(FakeOp(S/'bad-map',corrupt_map=True),S/'bad-map-proof.json'),False)
  check('lost_release12_diagnostic_rejected',lambda:P.observe(FakeOp(S/'bad-diag',corrupt_diag=True),S/'bad-diag-proof.json'),False)
  actual=Path(proof['packages'][-1]['commandReceipt']).parent/'stdout.bin';actual.write_bytes(actual.read_bytes()+b'bad\n');check('retained_command_stdout_mutation_rejected',lambda:P.verify_observation(path),False)
  result=dict(status='PASS_PRESERVATION_SCHEMA_SEAMS_ONLY',cases=cases,oldPackages=len(P.BASELINES),standardFiles=331,diagnostics=7,commandsSynthetic=True,deviceCommandsExecuted=False,provenance='REAL_FROZEN_EXPECTED_MAPS_WITH_SYNTHETIC_COMMAND_STDOUT_AND_RECEIPTS_NOT_ACTUAL_DEVICE_PRESENCE',scratchRemoved=True,oldSourceChanged=False)
  (E/'preservation-unit01.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],cases=len(cases))))
 finally:shutil.rmtree(S)
if __name__=='__main__':main()
