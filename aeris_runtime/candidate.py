"""Immutable selected source/native archives; active implementation stays repairable."""
from pathlib import Path
import gzip,hashlib,io,json,os,re,shutil,tarfile,zipfile
from .paths import PACKAGE_ROOT,repository
from .dependencies import LEAVES
from pilot.betaintegrated01.runtime.ap_stage import canonical
MIB=2**20;CAP=4*MIB;CERT='3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for block in iter(lambda:f.read(MIB),b''):h.update(block)
 return h.hexdigest()
def safe_relative(name,prefix=None):
 if type(name)is not str or Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name or (prefix and not name.startswith(prefix)):raise ValueError('CANDIDATE_RELATIVE_PATH')
 return name
def allocated_unique(root):
 seen=set();n=0
 for p in [Path(root),*Path(root).rglob('*')]:
  if p.is_symlink():raise ValueError('CANDIDATE_SYMLINK')
  st=p.stat();key=(st.st_dev,st.st_ino)
  if key not in seen:seen.add(key);n+=st.st_blocks*512
 return n
def put(path,raw):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 fd=os.open(path.parent,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
def _object(store,raw):
 h=hashlib.sha256(raw).hexdigest();target=store/h
 if target.exists():
  if target.is_symlink() or sha(target)!=h:raise ValueError('IMMUTABLE_OBJECT_CONFLICT')
 else:put(target,raw);target.chmod(0o444)
 return h,target

def _native_verify(receipt,archive,apk):
 if receipt.get('productionSigning') is not False or receipt.get('certificateSHA256')!=CERT or receipt.get('sourceCount')!=50 or type(receipt.get('sourceCount')) is not int or type(receipt.get('sourcePins')) is not dict or len(receipt['sourcePins'])!=50:raise ValueError('DEVELOPMENT_NATIVE50_RECEIPT')
 if hashlib.sha256(apk).hexdigest()!=receipt['sha256'] or len(apk)!=receipt['bytes']:raise ValueError('NATIVE_APK_HASH_SIZE')
 if hashlib.sha256(json.dumps(receipt['sourcePins'],sort_keys=True).encode()).hexdigest()!=receipt['sourceSHA256']:raise ValueError('NATIVE_SOURCE_IDENTITY')
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as t:
  members=t.getmembers();names=[x.name for x in members]
  if set(names)!=set(receipt['sourcePins']) or len(names)!=50 or any(not x.isfile() or x.size>2*MIB for x in members):raise ValueError('NATIVE50_INPUT_ARCHIVE')
  for x in members:
   safe_relative(x.name,'native/mission-runtime/')
   if hashlib.sha256(t.extractfile(x).read()).hexdigest()!=receipt['sourcePins'][x.name]:raise ValueError('NATIVE_RETAINED_INPUT_SHA')
 with zipfile.ZipFile(io.BytesIO(apk)) as z:
  identity=json.loads(z.read('assets/source-identity.json'))
  if identity.get('sourceSHA256')!=receipt['sourceSHA256'] or identity.get('package')!='vn.rtr.aeris.mission' or identity.get('production') is not False:raise ValueError('NATIVE_APK_PACKAGED_IDENTITY')
  for key,field in [('release','releaseProtocolSHA256'),('ioadmit','ioadmitProtocolSHA256'),('terminal','terminalProtocolSHA256'),('mission-bootstrap','missionProtocolSHA256')]:
   h=hashlib.sha256(z.read('assets/'+key+'-protocol.json')).hexdigest()
   if h!=receipt[field] or identity[field]!=h:raise ValueError('NATIVE_PACKAGED_PROTOCOL')
 return receipt

def freeze(root,native_receipt,qa_gate,*,label):
 root=Path(root).resolve();repo=repository();receipt_raw=Path(native_receipt).read_bytes();native=json.loads(receipt_raw);gate=json.loads(Path(qa_gate).read_bytes())
 if type(label)is not str or re.fullmatch('[a-z0-9-]{1,64}',label)is None or gate.get('status')!='PASS':raise ValueError('INDEPENDENT_CHANGED_CLOSURE_GATE_REQUIRED')
 payload={str(Path('aeris_runtime')/p.relative_to(PACKAGE_ROOT)):p.read_bytes() for p in sorted(PACKAGE_ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.json','.txt')}
 source_pins={n:hashlib.sha256(raw).hexdigest() for n,raw in payload.items()}
 if gate.get('sourceSHA256')!=source_pins or gate.get('nativeBuildReceiptSHA256')!=hashlib.sha256(receipt_raw).hexdigest():raise ValueError('INDEPENDENT_GATE_EXACT_CHANGED_CLOSURE')
 apk_path=(repo/native['apk']).resolve();archive_path=(repo/native['inputArchive']).resolve()
 if root!=apk_path.parent or root!=archive_path.parent:raise ValueError('ONE_SHARED_CUMULATIVE_NATIVE_AND_RUNTIME_ARTIFACT_ROOT_REQUIRED')
 apk=apk_path.read_bytes();original=archive_path.read_bytes()
 if hashlib.sha256(original).hexdigest()!=native['inputArchiveSHA256']:raise ValueError('NATIVE_BUILD_INPUT_ARCHIVE_SHA')
 archive=original if original[:2]==b'\x1f\x8b' else gzip.compress(original,mtime=0);_native_verify(native,archive,apk)
 extras={'native.apk':apk,'native-inputs.tar.gz':archive,'native-build-receipt.json':receipt_raw,'qa-gate.json':Path(qa_gate).read_bytes()}
 # Bound before writes, including worst-case filesystem4KiB blocks and dirs.
 root.mkdir(parents=True,exist_ok=True);store=root/'objects';store.mkdir(exist_ok=True)
 unique={hashlib.sha256(v).hexdigest():v for v in [*payload.values(),*extras.values()]}
 additional=sum(((len(v)+4095)//4096)*4096 for h,v in unique.items() if not (store/h).exists())+262144
 if allocated_unique(root)+additional>CAP or shutil.disk_usage(repo).free-additional<10*2**30+256*MIB:raise ValueError('CANDIDATE_PREFLIGHT_ARTIFACT4MiB_DISK10GiB')
 objects={name:_object(store,raw) for name,raw in payload.items()};extra_objects={name:_object(store,raw) for name,raw in extras.items()}
 external={name:sha(repo/name) for name in LEAVES}
 for variant in ('nominal','loss'):
  for name in ('run-profile02.json','control.parm','typed-profile.json'):
   rel='pilot/betaintegrated01/cockpit04/profiles/'+variant+'/'+name;external[rel]=sha(repo/rel)
 for rel in ('runtime/betaintegrated01/dist/arducopter-m1-stagepipe-03','runtime/betaintegrated01/dist/clockprobe','runtime/betaintegrated01/dist/copter.parm'):external[rel]=sha(repo/rel)
 manifest={'format':'aeris-runtime-candidate','version':1,'label':label,'sourceSHA256':{n:h for n,(h,p) in objects.items()},'externalFrozenSHA256':external,'native':{'package':'vn.rtr.aeris.mission','APK_SHA256':native['sha256'],'sourceSHA256':native['sourceSHA256'],'buildReceiptSHA256':hashlib.sha256(receipt_raw).hexdigest(),'sourcePins':native['sourcePins'],'developmentOnly':True},'retainedObjects':{n:h for n,(h,p) in extra_objects.items()},'qaGateSHA256':sha(qa_gate),'activeSourceMayChangeAfterAttempt':True,'artifactCapBytes':CAP,'simulationOnly':True}
 digest=hashlib.sha256(canonical(manifest)).hexdigest();target=root/digest
 if target.exists():raise ValueError('CANDIDATE_EXISTS_NO_REWRITE')
 target.mkdir();(target/'source').mkdir()
 for name,(h,obj) in objects.items():dest=target/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);os.link(obj,dest)
 for name,(h,obj) in extra_objects.items():os.link(obj,target/name)
 for directory in sorted([p for p in target.rglob('*') if p.is_dir()],key=lambda p:len(p.parts),reverse=True):
  fd=os.open(directory,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
 put(target/'candidate.json',canonical(manifest)+b'\n');put(target/'candidate.sha256',(digest+'\n').encode())
 if allocated_unique(root)>CAP:raise ValueError('ARTIFACT4MiB_FAILED_PREFIX_RETAINED')
 return {'path':str(target),'sha256':digest,'allocatedUniqueBytes':allocated_unique(root),'sourceFiles':len(payload),'nativeAPKSHA256':native['sha256']}
def load(path,expected_sha):
 path=Path(path).resolve();manifest_raw=(path/'candidate.json').read_bytes();v=json.loads(manifest_raw)
 if manifest_raw!=canonical(v)+b'\n':raise ValueError('EXACT_CANONICAL_MANIFEST_BYTES')
 if type(expected_sha)is not str or re.fullmatch('[a-f0-9]{64}',expected_sha)is None or hashlib.sha256(canonical(v)).hexdigest()!=expected_sha or v.get('format')!='aeris-runtime-candidate' or type(v.get('version'))is not int or v['version']!=1 or v.get('simulationOnly')is not True:raise ValueError('CANDIDATE_DIGEST_SCHEMA')
 for name,h in v['sourceSHA256'].items():
  safe_relative(name,'aeris_runtime/');p=path/'source'/name
  if p.is_symlink() or sha(p)!=h:raise ValueError('CANDIDATE_CODE_DRIFT:'+name)
 for name,h in v['externalFrozenSHA256'].items():
  safe_relative(name)
  if sha(repository()/name)!=h:raise ValueError('FROZEN_LEAF_DRIFT:'+name)
 for name,h in v['retainedObjects'].items():
  safe_relative(name)
  if sha(path/name)!=h:raise ValueError('RETAINED_CANDIDATE_OBJECT_DRIFT')
 receipt=json.loads((path/'native-build-receipt.json').read_bytes());_native_verify(receipt,(path/'native-inputs.tar.gz').read_bytes(),(path/'native.apk').read_bytes())
 if sha(path/'native-build-receipt.json')!=v['native']['buildReceiptSHA256'] or receipt['sourcePins']!=v['native']['sourcePins'] or receipt['sourceSHA256']!=v['native']['sourceSHA256'] or receipt['sha256']!=v['native']['APK_SHA256']:raise ValueError('RETAINED_NATIVE_MANIFEST_BINDING')
 return v
