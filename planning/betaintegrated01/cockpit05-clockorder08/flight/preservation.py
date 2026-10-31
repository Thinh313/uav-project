"""Root-only immutable old-package maps and two separately observed diagnostics."""
from pathlib import Path
import hashlib,json,re
from . import contract
BASELINES={'vn.rtr.aeris.cockpit05':('evidence/betaintegrated01-cockpit05-clockflight02/root-closeout01/device-final.json',233),'vn.rtr.aeris.cockpitio04':('evidence/betaintegrated01-cockpit05-observer05/root-closeout01/device-final.json',25),'vn.rtr.aeris.cockpitio06':('evidence/betaintegrated01-cockpit05-nativeio06/actual-short01/control/all-private-after-restart-SHA.json',10),'vn.rtr.aeris.cockpitio07':('evidence/betaintegrated01-cockpit05-nativeio07/actual-short01/control/all-private-after-restart-SHA.json',11)}
DIAGNOSTICS={'vn.rtr.aeris.cockpitio06':('evidence/betaintegrated01-cockpit05-nativeio06/root-diagnostic-recovery01.json','files/native-io-diagnostics/cockpit05-nativeio06-short-01.json','bytes'),'vn.rtr.aeris.cockpitio07':('evidence/betaintegrated01-cockpit05-nativeio07/actual-short01/control/native-io-diagnostic-export.json','files/native-io-diagnostics/cockpit05-nativeio07-short-01.json','artifactBytes')}
STATUS='OLD_PACKAGES_EXACT279_PLUS_TWO_DIAGNOSTICS_PRESERVED'
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
 value={'status':STATUS,'packages':proofs,'priorDiagnostics':[observe_diagnostic(op,p)for p in DIAGNOSTICS],'packageDataImportedIntoNewPackage':False}
 with Path(target).open('x')as f:json.dump(value,f,indent=2);f.write('\n')
 return value

def verify_observation(path):
 value=json.loads(Path(path).read_text());proofs=value.get('packages')
 if value.get('status')!=STATUS or type(proofs)is not list or len(proofs)!=4 or {x.get('package')for x in proofs}!=set(BASELINES):raise ValueError('PRIOR_PACKAGES_REQUIRED')
 for v in proofs:
  package=v['package'];p=Path(v['commandReceipt']);raw=(p.parent/'stdout.bin').read_bytes();rec=json.loads(p.read_text());bp,count=BASELINES[package]
  if contract.sha(p)!=v['commandReceiptSHA256']or hashlib.sha256(raw).hexdigest()!=v['stdoutSHA256']or rec['exit']!=0 or rec['timedOut']is not False:raise ValueError('PRIOR_PACKAGE_COMMAND_PROOF')
  expected=['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','-s','emulator-5582',*argv(package)]
  if rec['argv']!=expected or rec['stdoutSHA256']!=v['stdoutSHA256']or len(raw)!=rec['stdoutBytes']or parse_private_map(raw,count)!=v['files']or v['files']!=expected_old(package)or v['baselineReceipt']!=bp or v['baselineReceiptSHA256']!=contract.sha(contract.ROOT/bp):raise ValueError('PRIOR_PACKAGE_COMMAND_BINDING')
 diags=value.get('priorDiagnostics')
 if type(diags)is not list or len(diags)!=2 or {x.get('package')for x in diags}!=set(DIAGNOSTICS):raise ValueError('TWO_PRIOR_DIAGNOSTICS_REQUIRED')
 for diag in diags:verify_diagnostic(diag)
 return value

def diagnostic_baseline(package):
 path,device,sizekey=DIAGNOSTICS[package];b=json.loads((contract.ROOT/path).read_text());return path,device,b['artifactSHA256'],b[sizekey]
def diagnostic_argv(package,device):return [['shell','run-as',package,'sha256sum',device],['shell','run-as',package,'wc','-c',device]]
def observe_diagnostic(op,package):
 path,device,h,size=diagnostic_baseline(package);proofs=[];outputs=[]
 for args in diagnostic_argv(package,device):
  o=op.command(args,timeout=10);outputs.append(o[0].decode().split());proofs.append({'receipt':str(o[3]/'receipt.json'),'receiptSHA256':contract.sha(o[3]/'receipt.json')})
 if outputs!=[[h,device],[str(size),device]]:raise ValueError('PRIOR_DIAGNOSTIC_CHANGED:'+package)
 return {'package':package,'devicePath':device,'sha256':h,'bytes':size,'baselineReceipt':path,'baselineReceiptSHA256':contract.sha(contract.ROOT/path),'commands':proofs}
def verify_diagnostic(value):
 package=value['package'];path,device,h,size=diagnostic_baseline(package);outputs=[]
 if value.get('devicePath')!=device or value.get('sha256')!=h or value.get('bytes')!=size or value.get('baselineReceipt')!=path or value.get('baselineReceiptSHA256')!=contract.sha(contract.ROOT/path)or len(value.get('commands',[]))!=2:raise ValueError('PRIOR_DIAGNOSTIC_BASELINE_BINDING')
 for proof,args in zip(value['commands'],diagnostic_argv(package,device)):
  p=Path(proof['receipt']);r=json.loads(p.read_text());raw=(p.parent/'stdout.bin').read_bytes()
  if contract.sha(p)!=proof['receiptSHA256']or r['argv']!=['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','-s','emulator-5582',*args]or r['exit']!=0 or r['timedOut']is not False or hashlib.sha256(raw).hexdigest()!=r['stdoutSHA256']or len(raw)!=r['stdoutBytes']:raise ValueError('PRIOR_DIAGNOSTIC_COMMAND_BINDING')
  outputs.append(raw.decode().split())
 if outputs!=[[h,device],[str(size),device]]:raise ValueError('PRIOR_DIAGNOSTIC_ACTUAL_BYTES')
 return value
