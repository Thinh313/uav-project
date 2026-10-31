"""Root-only read-only proofs: existing cockpitio04=25 and cockpit05=233 files."""
from pathlib import Path
import hashlib,json,re
from . import contract
BASELINES={'vn.rtr.aeris.cockpit05':('evidence/betaintegrated01-cockpit05-clockflight02/root-closeout01/device-final.json',233),'vn.rtr.aeris.cockpitio04':('evidence/betaintegrated01-cockpit05-observer05/root-closeout01/device-final.json',25),'vn.rtr.aeris.cockpitio06':('evidence/betaintegrated01-cockpit05-nativeio06/actual-short01/control/all-private-after-restart-SHA.json',10)}
def parse_private_map(raw,count):
 values={}
 for line in raw.decode().splitlines():
  h,name=line.split(None,1);name=name.strip()
  if re.fullmatch('[0-9a-f]{64}',h)is None or not name.startswith(('files/control-runs/','files/workspace03/','files/review-links/'))or '..'in Path(name).parts or name in values:raise ValueError('OLD_PACKAGE_MAP_SCHEMA')
  values[name]=h
 if len(values)!=count:raise ValueError('OLD_PACKAGE_EXACT_COUNT_REQUIRED')
 return values

def expected_old(package='vn.rtr.aeris.cockpit05'):
 path,count=BASELINES[package];value=json.loads((contract.ROOT/path).read_text());files=value['allPrivateMap']if 'allPrivateMap'in value else value
 if type(files)is not dict or len(files)!=count:raise ValueError('OLD_CLOSEOUT_COUNT_REQUIRED')
 return files

def argv(package):return ['exec-out','run-as',package,'find','files/control-runs','files/workspace03','files/review-links','-type','f','-exec','sha256sum','{}','+']
def observe(op,target):
 proofs=[]
 for package,(path,count)in BASELINES.items():
  obs=op.command(argv(package),timeout=30);raw=obs[0];files=parse_private_map(raw,count)
  if files!=expected_old(package):raise ValueError('OLD_PACKAGE_CHANGED_OR_MISSING:'+package)
  proofs.append({'package':package,'files':files,'fileCount':count,'baselineReceipt':path,'baselineReceiptSHA256':contract.sha(contract.ROOT/path),'readOnly':True,'authorityRestored':False,'commandReceipt':str(obs[3]/'receipt.json'),'commandReceiptSHA256':contract.sha(obs[3]/'receipt.json'),'stdoutSHA256':hashlib.sha256(raw).hexdigest()})
 value={'status':'OLD_PACKAGES_EXACT268_PLUS_DIAGNOSTIC_PRESERVED','packages':proofs,'priorDiagnostic':observe_diagnostic(op),'packageDataImportedIntoNewPackage':False}
 with Path(target).open('x')as f:json.dump(value,f,indent=2);f.write('\n')
 return value

def verify_observation(path):
 value=json.loads(Path(path).read_text());proofs=value.get('packages')
 if type(proofs)is not list or len(proofs)!=3 or {x.get('package')for x in proofs}!=set(BASELINES):raise ValueError('PRIOR_PACKAGES_REQUIRED')
 for v in proofs:
  package=v['package'];p=Path(v['commandReceipt']);raw=(p.parent/'stdout.bin').read_bytes();rec=json.loads(p.read_text());bp,count=BASELINES[package]
  if contract.sha(p)!=v['commandReceiptSHA256']or hashlib.sha256(raw).hexdigest()!=v['stdoutSHA256']or rec['exit']!=0 or rec['timedOut']is not False:raise ValueError('PRIOR_PACKAGE_COMMAND_PROOF')
  expected=['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','-s','emulator-5582',*argv(package)]
  if rec['argv']!=expected or rec['stdoutSHA256']!=v['stdoutSHA256']or len(raw)!=rec['stdoutBytes']or parse_private_map(raw,count)!=v['files']or v['files']!=expected_old(package)or v['baselineReceipt']!=bp or v['baselineReceiptSHA256']!=contract.sha(contract.ROOT/bp):raise ValueError('PRIOR_PACKAGE_COMMAND_BINDING')
 verify_diagnostic(value['priorDiagnostic'])
 return value

DIAG_RECOVERY='evidence/betaintegrated01-cockpit05-nativeio06/root-diagnostic-recovery01.json'
DIAG_DEVICE='files/native-io-diagnostics/cockpit05-nativeio06-short-01.json'
DIAG_BASE_COMMAND='evidence/betaintegrated01-cockpit05-nativeio06/android-setup01/operator/0170-adb-7aec7ed6/receipt.json'
def observe_diagnostic(op):
 baseline=json.loads((contract.ROOT/DIAG_RECOVERY).read_text());package='vn.rtr.aeris.cockpitio06';proofs=[]
 expected=[['shell','run-as',package,'sha256sum',DIAG_DEVICE],['shell','run-as',package,'wc','-c',DIAG_DEVICE]];outputs=[]
 for args in expected:
  o=op.command(args,timeout=10);outputs.append(o[0]);proofs.append({'receipt':str(o[3]/'receipt.json'),'receiptSHA256':contract.sha(o[3]/'receipt.json')})
 if outputs[0].decode().split()!=[baseline['artifactSHA256'],DIAG_DEVICE]or outputs[1].decode().split()!=[str(baseline['bytes']),DIAG_DEVICE]:raise ValueError('PRIOR_NATIVE06_DIAGNOSTIC_CHANGED')
 return {'package':package,'devicePath':DIAG_DEVICE,'sha256':baseline['artifactSHA256'],'bytes':baseline['bytes'],'recoveryReceiptSHA256':contract.sha(contract.ROOT/DIAG_RECOVERY),'originalAll11MapCommandSHA256':contract.sha(contract.ROOT/DIAG_BASE_COMMAND),'commands':proofs}
def verify_diagnostic(value):
 baseline=json.loads((contract.ROOT/DIAG_RECOVERY).read_text());expected=[['shell','run-as','vn.rtr.aeris.cockpitio06','sha256sum',DIAG_DEVICE],['shell','run-as','vn.rtr.aeris.cockpitio06','wc','-c',DIAG_DEVICE]];outputs=[]
 if value.get('sha256')!=baseline['artifactSHA256']or value.get('bytes')!=baseline['bytes']or value.get('recoveryReceiptSHA256')!=contract.sha(contract.ROOT/DIAG_RECOVERY)or value.get('originalAll11MapCommandSHA256')!=contract.sha(contract.ROOT/DIAG_BASE_COMMAND)or len(value.get('commands',[]))!=2:raise ValueError('PRIOR_DIAGNOSTIC_BASELINE_BINDING')
 for p,args in zip(value['commands'],expected):
  path=Path(p['receipt']);r=json.loads(path.read_text());raw=(path.parent/'stdout.bin').read_bytes()
  if contract.sha(path)!=p['receiptSHA256']or r['argv']!=['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','-s','emulator-5582',*args]or r['exit']!=0 or r['timedOut']is not False or hashlib.sha256(raw).hexdigest()!=r['stdoutSHA256']or len(raw)!=r['stdoutBytes']:raise ValueError('PRIOR_DIAGNOSTIC_COMMAND_BINDING')
  outputs.append(raw.decode().split())
 if outputs!=[[baseline['artifactSHA256'],DIAG_DEVICE],[str(baseline['bytes']),DIAG_DEVICE]]:raise ValueError('PRIOR_DIAGNOSTIC_ACTUAL_BYTES')
 return value
