"""Shared metadata-only client identity. No flight/oracle/physics import or effects."""
from pathlib import Path
from importlib import import_module
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[3]
PACKAGE='vn.rtr.aeris.cockpitio14';ACTIVITY=PACKAGE+'/.CockpitActivity'
BUILD='evidence/betaintegrated01-cockpit05-clockterm14/native/build-01.json'
EXPECTED_BUILD_RECEIPT_SHA256='32811b61ffd73c3414691833062f970bc0477f084bedca588e29360fc5eb8f3a'
EXPECTED_APK_SHA256='36c73f774187748fd369e32668f6e429aa0b767f901f0561132765127cf25abf'
EXPECTED_SOURCE_SHA256='98615ff0f400b546c2f190305b79e41aa552e4d9c0bd3e1a81d7e71649711d0e'
CERT_SHA256='3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'
PROTOCOL=ROOT/'evidence/betaintegrated01-cockpit05-release12/native/RELEASE-PROTOCOL01.json'
IOPROTOCOL=ROOT/'evidence/betaintegrated01-cockpit05-ioadmit13/native/IOADMIT-PROTOCOL01.json'
TERMINAL_PROTOCOL=ROOT/'evidence/betaintegrated01-cockpit05-clockterm14/native/TERMINAL-PROTOCOL01.json'
POLICY='planning.betaintegrated01.cockpit05-metaval15.runtime.policy'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(path):
 p=Path(path)
 if p.is_symlink()or not p.is_file():raise ValueError('METAVAL15_REGULAR_METADATA_SOURCE_REQUIRED')
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def policy():return import_module(POLICY)
def build_receipt():
 p=ROOT/BUILD
 if sha(p)!=EXPECTED_BUILD_RECEIPT_SHA256 or not 1<=p.stat().st_size<=262144:raise ValueError('METAVAL15_EXACT_REUSED14_BUILD_RECEIPT')
 v=json.loads(p.read_bytes())
 if type(v.get('sourcePins'))is not dict or len(v['sourcePins'])!=45 or v.get('sha256')!=EXPECTED_APK_SHA256 or v.get('sourceSHA256')!=EXPECTED_SOURCE_SHA256 or type(v.get('productionSigning'))is not bool or v['productionSigning']is not False or CERT_SHA256 not in v.get('signature','').lower()or not v.get('apk','').startswith('native/betaintegrated01/cockpitio14/dist/'):raise ValueError('METAVAL15_REUSED14_NATIVE_BUILD_SHAPE')
 if sha(ROOT/v['apk'])!=EXPECTED_APK_SHA256:raise ValueError('METAVAL15_REUSED14_APK_BYTES')
 for name,h in v['sourcePins'].items():
  if type(name)is not str or Path(name).is_absolute()or '..'in Path(name).parts or type(h)is not str or re.fullmatch('[a-f0-9]{64}',h)is None or sha(ROOT/name)!=h:raise ValueError('METAVAL15_REUSED14_NATIVE_SOURCE_PIN')
 return v
def native_selection():
 r=build_receipt();protocols=(PROTOCOL,IOPROTOCOL,TERMINAL_PROTOCOL);hashes=[]
 for p in protocols:
  h=sha(p)
  if r['sourcePins'].get(str(p.relative_to(ROOT)))!=h:raise ValueError('METAVAL15_REUSED14_PROTOCOL_PIN')
  hashes.append(h)
 return dict(format='aeris-external-native-client-selection',version=1,package=PACKAGE,buildReceipt=BUILD,buildReceiptSHA256=EXPECTED_BUILD_RECEIPT_SHA256,APK_SHA256=r['sha256'],sourceSHA256=r['sourceSHA256'],devCertificateSHA256=CERT_SHA256,selectedNativeSourceSHA256=r['sourcePins'],cancellationProtocolPath=str(PROTOCOL.relative_to(ROOT)),cancellationProtocolSHA256=hashes[0],inputAdmissionProtocolPath=str(IOPROTOCOL.relative_to(ROOT)),inputAdmissionProtocolSHA256=hashes[1],terminalProtocolPath=str(TERMINAL_PROTOCOL.relative_to(ROOT)),terminalProtocolSHA256=hashes[2],inheritedHostPolicySHA256=policy().amendment()['amendmentSHA256'],reusedNativeClient=True,nativeClientOrigin='CLOCKTERM14_UNCHANGED_DEVELOPMENT_APK45',historicalNativePinsRemainHistorical=True)
def validate_native_selection(config):
 policy().validate_recording_policy(config);selected=native_selection()
 if canonical(config.get('externalNativeClientSelection'))!=canonical(selected):raise ValueError('METAVAL15_EXACT_REUSED14_CLIENT_AND_ACTUAL15_HOST_SELECTION')
 return selected
