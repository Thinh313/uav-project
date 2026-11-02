"""One bounded Root closed-raw lossless export. No live-snapshot publication.
The sole compressed host file is split by immutable byte ranges for Android SAF;
range reads avoid making another host copy. Original192MiB host cap stays shared.
"""
from pathlib import Path
import gzip,hashlib,io,json,os,stat,tarfile,time
from .resources import OwnedResources
from .metadata_budget import MetadataBudget,encoded
MIB=2**20;MAX_EXPORT=168*MIB;PART=28*MIB;MAX_FILES=4096;MAX_ORIGINAL=16*2**30
NAME='product-full-raw.tar.gz'
def need(v,n):
 if not v:raise ValueError('RAW_EXPORT_'+n)
def digest(path,check_live=lambda:None):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(65536),b''):check_live();h.update(b)
 return h.hexdigest()
class LimitedOutput:
 def __init__(self,file,budget,maximum,check_live=lambda:None):self.file=file;self.budget=budget;self.bytes=0;self.maximum=maximum;self.check_live=check_live
 def write(self,b):
  need(self.bytes+len(b)<=self.maximum,'HOST168M_STREAM_LIMIT_PARTIAL_RETAINED');self.check_live();self.budget.check();n=self.file.write(b);need(n==len(b),'SHORT_WRITE_UNKNOWN_RETAINED');self.bytes+=n;return n
 def flush(self):return self.file.flush()
class DigestInput:
 def __init__(self,file,check_live=lambda:None):self.file=file;self.hash=hashlib.sha256();self.bytes=0;self.check_live=check_live
 def read(self,n=-1):
  need(0<=n<=2*MIB,'BOUNDED_TAR_READ');self.check_live();b=self.file.read(n);self.hash.update(b);self.bytes+=len(b);return b

def prepare_export(budget,resources,context,native_probe=None,*,check_live=None):
 need(budget.mock or callable(check_live),'SOURCE_GUARDIAN_DELIVERY_CHECK_REQUIRED');callback=check_live;last_check=[-1]
 def live():
  now=time.monotonic_ns()
  if callback is not None and(last_check[0]<0 or now-last_check[0]>=100_000_000):callback();last_check[0]=now
 live()
 need(type(budget)is MetadataBudget and type(resources)is OwnedResources,'EXACT_SOURCE_OWNERS');closure=resources.completed_closure();need('workbenchSealProof'in closure and closure.get('outputCapture')and set(closure['children'])=={'ap','backend'},'NORMAL_WORKBENCH_SOURCE_DRAIN_REQUIRED')
 from .product_types import is_product_probe
 need(is_product_probe(native_probe) and native_probe.closed_export is not None,'GENUINE_NATIVE_CLOSED_FILE_EXPORT_REQUIRED')
 native=native_probe.closed_export;native_file=Path(native['export']['path']);need(native['export']['captureComplete']is True and native_file.stat().st_size==native['export']['bytes']and digest(native_file,live)==native['export']['sha256'],'NATIVE_FULL_FILES_SHA_CAPTURE');run=context['run'];case=budget.evidence/'sessions'/run;need(resources.root==case/'processes','SAME_REGISTERED_CASE');files=[];total=0
 roots=[(p,str(p.relative_to(case)))for p in(case/'raw',case/'simulation/AP-state',case/'product',case/'android-api',case/'processes')]
 historical=getattr(native_probe,'retained_inventory',None)
 if historical is not None:roots.append((case/'android-api-retained','android-api/retained-original'))
 for root,prefix in roots:
  need(root.is_dir()and not root.is_symlink(),'EXACT_RAW_ROOT_REQUIRED')
  for path in sorted(root.rglob('*')):
   value=path.lstat();need(not stat.S_ISLNK(value.st_mode),'NO_SYMLINK_INPUT')
   if stat.S_ISDIR(value.st_mode):continue
   need(stat.S_ISREG(value.st_mode)and len(files)<MAX_FILES,'REGULAR_FILE_COUNT_BOUND');total+=value.st_size;need(total<=MAX_ORIGINAL,'ORIGINAL16G_BOUND');files.append({'path':prefix+'/'+str(path.relative_to(root)),'bytes':value.st_size,'sha256':digest(path,live),'statIdentity':[value.st_dev,value.st_ino,value.st_mtime_ns,value.st_size],'_source':str(path)})
 registrations=sorted((budget.evidence/'reports').glob('native-producer-%02d-registration*.json'%budget.snapshot()['counters']['cases']));need(1<=len(registrations)<=2,'EXACT_NATIVE_REGISTRATION_GENERATIONS')
 from .product_runtime import event_original_files
 event_files=event_original_files(budget.evidence,resources.digest)
 case_number=budget.snapshot()['counters']['cases']
 for path in[*registrations,*sorted((budget.evidence/'reports').glob('native-closed-inputs-%02d.json'%case_number)),budget.evidence/'reports'/('media-engineering-selection-%02d.json'%case_number),budget.evidence/'reports'/('product-descriptor-%02d.json'%case_number),budget.evidence/'reports/product-clock-proofs.jsonl',*event_files]:
  need(path.is_file()and not path.is_symlink(),'SOURCE_ENROLLMENT_CLOCK_ORIGINALS_REQUIRED');value=path.stat();total+=value.st_size;files.append({'path':'root-management/'+path.name,'bytes':value.st_size,'sha256':digest(path,live),'statIdentity':[value.st_dev,value.st_ino,value.st_mtime_ns,value.st_size],'_source':str(path)})
 retained=None
 if historical is not None:
  old=historical['sourceOriginalTAR'];path=Path(old['path']);need(path==case/'native-original-before-quarantine.tar'and old['captureComplete']is True and not path.is_symlink()and path.is_file(),'HISTORICAL_EXACT_ORIGINAL_EXPORT');value=path.stat();need(value.st_size==old['bytes']and digest(path,live)==old['sha256'],'HISTORICAL_ORIGINAL_SHA_BYTES');member='android-api/retained-original-application.tar';files.append({'path':member,'bytes':value.st_size,'sha256':old['sha256'],'statIdentity':[value.st_dev,value.st_ino,value.st_mtime_ns,value.st_size],'_source':str(path)});total+=value.st_size
  def prefixed(prefix,ref):
   need(type(ref)is dict and type(ref.get('path'))is str and not Path(ref['path']).is_absolute()and'..'not in Path(ref['path']).parts and type(ref.get('offset'))is int and ref['offset']>=0 and type(ref.get('bytes'))is int and 0<ref['bytes']<=4096,'HISTORICAL_BOUNDED_ORIGINAL_REF');return {k:ref[k]for k in('offset','bytes','sha256')}|{'path':prefix+ref['path']}
  refs={k:prefixed(prefix,ref)for k,prefix,ref in [('application','android-api/',native_probe.application_domain_ref),('inventory','android-api/',native_probe.retained_inventory_ref),('backup','android-api/retained-original/',old['captureReceiptRef']),('du','android-api/retained-original/',historical['sourceDUCommandRef']),('duStdout','android-api/retained-original/',historical['sourceDUStdoutRef']),('duArgv','android-api/retained-original/',historical['sourceDUArgvRef'])]};need(sum(r['bytes']for r in refs.values())<=16384,'HISTORICAL_PROOF16K');retained={'format':'aeris-retained-original-application-transfer','version':1,'path':member,'bytes':old['bytes'],'sha256':old['sha256'],'applicationId':'vn.rtr.aeris.mission','activeApplicationId':'vn.rtr.aeris.betasim09','role':'HISTORICAL_RETAINED_NOT_CURRENT_FLIGHT_INPUT','authorityGranted':False,'originalRefs':refs}
 need(files and len(files)<=MAX_FILES and len({q['path']for q in files})==len(files)and total<=MAX_ORIGINAL,'NONEMPTY_UNIQUE_BOUNDED_RAW_INPUTS');body={'format':'aeris-betasim-closed-raw-manifest','version':1,'context':context,'sourceCandidateSHA256':resources.digest,'closure':closure,'files':[{k:v for k,v in r.items()if k not in('statIdentity','_source')}for r in files],'totalOriginalBytes':total,'allOriginalRawAndAPStateIncluded':True,'productSemanticAndMediaIncluded':True,'hostNativeObservationScope':'EXACT_PRE_EXPORT_PREFIX_FUTURE_SAF_RECEIPTS_SEPARATE','rootRuntimeEventScope':'EXACT_PRE_EXPORT_COMMITTED_PREFIX_POST_EXPORT_EVENT_AND_SAF_RECEIPTS_SEPARATE','nativeClosedFiles':native,'nativeTarTransportProfile':__import__('aeris_runtime.tar_profile_h7',fromlist=['profile']).profile(),**({'retainedOriginalApplication':retained}if retained is not None else{}),'independentAcceptance':'NOT_YET_COLD_VERIFIED','authorityRestorable':False};raw=encoded(body);need(len(raw)<=256*1024,'MANIFEST256K_BOUND');target=case/NAME;remaining=192*MIB-sum(v['reservedBytes']for v in budget.snapshot().get('exports',{}).values());maximum=min(MAX_EXPORT,remaining);need(maximum>0,'NO_REMAINING_HOST_EXPORT_CREDITS');budget.reserve_export(target,maximum)
 try:
  with target.open('xb')as f:
   output=LimitedOutput(f,budget,maximum,live)
   with gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0,compresslevel=6)as gz:
    with tarfile.open(fileobj=gz,mode='w|',format=tarfile.USTAR_FORMAT)as tar:
     info=tarfile.TarInfo('closed-raw-manifest.json');info.size=len(raw);info.mode=0o600;info.mtime=0;tar.addfile(info,io.BytesIO(raw))
     for row in files:
      path=Path(row['_source']);value=path.lstat();need([value.st_dev,value.st_ino,value.st_mtime_ns,value.st_size]==row['statIdentity'],'INPUT_CHANGED_BEFORE_ARCHIVE');info=tarfile.TarInfo(row['path']);info.size=row['bytes'];info.mode=0o600;info.mtime=0
      with path.open('rb')as source:
       actual=DigestInput(source,live);tar.addfile(info,actual);need(actual.bytes==row['bytes']and actual.hash.hexdigest()==row['sha256'],'INPUT_CHANGED_DURING_ARCHIVE')
   f.flush();os.fsync(f.fileno())
  fd=os.open(case,os.O_RDONLY|os.O_DIRECTORY)
  try:os.fsync(fd)
  finally:os.close(fd)
  export=budget.finish_export(target);parts=[]
  with target.open('rb')as f:
   offset=0
   while True:
    data=f.read(PART)
    if not data:break
    parts.append({'index':len(parts),'offset':offset,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()});offset+=len(data)
  need(1<=len(parts)<=6 and offset==export['reservedBytes'],'PART_COMPLETENESS');native_parts=[]
  with native_file.open('rb')as nf:
   native_offset=0
   while True:
    block=nf.read(PART)
    if not block:break
    native_parts.append({'index':len(native_parts),'offset':native_offset,'bytes':len(block),'sha256':hashlib.sha256(block).hexdigest()});native_offset+=len(block)
  native_stream={'id':'native-closed-files','path':str(native_file.relative_to(budget.evidence)),'bytes':native_offset,'sha256':native['export']['sha256'],'encoding':'TAR_UNCOMPRESSED_ORIGINAL','parts':native_parts,'maximumPartBytes':PART};need(native_offset+offset<=192*MIB,'JOINT_NATIVE_SAF_BYTES192M')
  manifest={**body,'nativeStream':native_stream,'bundle':{'path':str(target.relative_to(budget.evidence)),'bytes':offset,'sha256':export['sha256'],'encoding':'TAR_GZIP_LOSSLESS','parts':parts,'maximumPartBytes':PART},'manifestKind':'SOURCE_CLOSED_RAW_EXPORT_NOT_INDEPENDENT_ACCEPTANCE'};encoded_manifest=encoded(manifest);path=case/'product/reports/closed-raw-export.json';receipt=budget.write('external_task',path,encoded_manifest)
  return {'format':'aeris-root-closed-raw-export-reference','version':1,'context':context,'manifestPath':str(path),'manifestBytes':len(encoded_manifest),'manifestSHA256':hashlib.sha256(encoded_manifest).hexdigest(),'bundlePath':str(target),'bundleBytes':offset,'bundleSHA256':export['sha256'],'maximumPartBytes':PART,'parts':len(parts),'genuineSourceDrain':True,'independentRawAccepted':False,'originalWriteSequence':receipt['writeSequence'],'authorityRestorable':False}
 except BaseException as e:
  budget.failure(e,detail={'rawExport':str(target),'partialRetained':True,'noPublish':True});raise
