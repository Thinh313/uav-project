"""Root-only old-package read-only SHA observation. No installation or mutations."""
from pathlib import Path
from importlib import import_module
import hashlib,json,re
from . import contract
OLD_PACKAGE=contract.OLD_PACKAGE

def parse_private_map(raw):
 values={}
 for line in raw.decode().splitlines():
  h,name=line.split(None,1);name=name.strip()
  if re.fullmatch('[0-9a-f]{64}',h)is None or not name.startswith(('files/control-runs/','files/workspace03/','files/review-links/'))or '..'in Path(name).parts or name in values:raise ValueError('OLD_PACKAGE_MAP_SCHEMA')
  values[name]=h
 if len(values)!=233:raise ValueError('OLD_PACKAGE_EXACT233_REQUIRED')
 return values

def expected_old():
 value=json.loads((contract.ROOT/contract.BASELINE_RECEIPT).read_text());files=value.get('allPrivateMap')
 if type(files)is not dict or len(files)!=233:raise ValueError('OLD_CLOSEOUT233_REQUIRED')
 return files

def observe(op,target):
 observation=op.command(['exec-out','run-as',OLD_PACKAGE,'find','files/control-runs','files/workspace03','files/review-links','-type','f','-exec','sha256sum','{}','+'],timeout=30);raw=observation[0];files=parse_private_map(raw)
 if files!=expected_old():raise ValueError('OLD_PACKAGE233_CHANGED_OR_MISSING')
 value={'package':OLD_PACKAGE,'files':files,'fileCount':233,'baselineReceipt':contract.BASELINE_RECEIPT,'baselineReceiptSHA256':contract.sha(contract.ROOT/contract.BASELINE_RECEIPT),'readOnly':True,'authorityRestored':False,'commandReceipt':str(observation[3]/'receipt.json'),'commandReceiptSHA256':contract.sha(observation[3]/'receipt.json'),'stdoutSHA256':hashlib.sha256(raw).hexdigest()}
 with Path(target).open('x')as f:json.dump(value,f,indent=2);f.write('\n')
 return value


def verify_observation(path):
 value=json.loads(Path(path).read_text());receipt=Path(value['commandReceipt']);rawpath=receipt.parent/'stdout.bin';raw=rawpath.read_bytes();r=json.loads(receipt.read_text())
 if contract.sha(receipt)!=value['commandReceiptSHA256']or hashlib.sha256(raw).hexdigest()!=value['stdoutSHA256']or r['exit']!=0 or r['timedOut']is not False:raise ValueError('OLD_PACKAGE_OBSERVATION_COMMAND_PROOF')
 expected=['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','-s','emulator-5582','exec-out','run-as',OLD_PACKAGE,'find','files/control-runs','files/workspace03','files/review-links','-type','f','-exec','sha256sum','{}','+']
 if r['argv']!=expected or r['stdoutSHA256']!=value['stdoutSHA256']or len(raw)!=r['stdoutBytes']or parse_private_map(raw)!=value['files']or value['files']!=expected_old():raise ValueError('OLD_PACKAGE233_COMMAND_BINDING')
 return value
