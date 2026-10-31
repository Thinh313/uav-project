"""Actual selected export + independent recipient with tiny original fixtures."""
from pathlib import Path
from contextlib import contextmanager
import copy,gzip,hashlib,importlib.util,io,json,sys,tarfile,shutil
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(P.parent),str(T/'source'),str(R)]
import test_raw_export_events05 as f
from aeris_runtime.raw_export import prepare_export
from aeris_runtime.product_native09 import ProductNativeProbe09
from aeris_runtime.saf_receiver import verify_recipient
from aeris_runtime.metadata_budget import encoded
LAB=R/'evidence/betasim-integrated01/runtime/.historical09';H=lambda b:hashlib.sha256(b).hexdigest()
def main():
 assert not LAB.exists();LAB.mkdir();old_lab=f.LAB;f.LAB=LAB;groups=[]
 try:
  b,res,case=f.fixture('case');root=b.evidence
  for name in('media-engineering-selection-01.json','product-descriptor-01.json'):b.write('external_task',root/'reports'/name,b'{"fixture":true}\n')
  old=case/'native-original-before-quarantine.tar'
  with tarfile.open(old,'w',format=tarfile.USTAR_FORMAT)as tar:
   q=tarfile.TarInfo('files/old-unknown-journal.bin');q.size=12;tar.addfile(q,io.BytesIO(b'UNKNOWN_OLD!\n'))
  magic=b'AERIS_INPUT_JOURNAL_V2\n';gen='d'*32;native=case/'native-closed.tar'
  with tarfile.open(native,'w',format=tarfile.USTAR_FORMAT)as tar:
   q=tarfile.TarInfo('files/product-input01/'+gen+'.aj02');q.size=len(magic);tar.addfile(q,io.BytesIO(magic))
  n=ProductNativeProbe09.__new__(ProductNativeProbe09);n.closed_export={'export':{'path':str(native),'bytes':native.stat().st_size,'sha256':H(native.read_bytes()),'captureComplete':True},'sourceSHA256':'b'*64,'APKSHA256':'c'*64,'journal':{'generations':[{'path':'files/product-input01/'+gen+'.aj02','bytes':len(magic),'sha256':H(magic),'sequence':0,'head':'0'*64,'unresolvedIntentSequence':None}]}}
  current=case/'android-api';legacy=case/'android-api-retained';legacy.mkdir()
  def ref(directory,name,data):
   raw=data if type(data)is bytes else encoded(data);b.write('command_receipts',directory/name,raw);return{'format':'aeris-original-byte-ref','version':3,'path':name,'offset':0,'bytes':len(raw),'sha256':H(raw)}
  capture={'format':'aeris-native-export','fullOriginalFiles':True,'captureComplete':True,'failure':None,'exit':0,'bytesRetained':old.stat().st_size};capref=ref(legacy,'capture.json',capture);argv=['/fake/pinned-adb','-s','emulator-5582','shell','run-as','vn.rtr.aeris.mission','du','-k','-s','files'];argref=ref(legacy,'du-argv.raw',argv);outref=ref(legacy,'du-stdout.raw',b'8\tfiles\n');duref=ref(legacy,'du.json',{'format':'aeris-command','captureComplete':True,'failure':None,'exit':0,'stdoutRef':outref,'argvRef':argref})
  source_old={'path':str(old),'bytes':old.stat().st_size,'sha256':H(old.read_bytes()),'captureComplete':True,'captureReceiptRef':capref};n.retained_inventory={'format':'aeris-retained-old-application-private-inventory','package':'vn.rtr.aeris.mission','sourceOriginalTAR':source_old,'sourceDUCommandRef':duref,'sourceDUStdoutRef':outref,'sourceDUArgvRef':argref,'allocatedBytes':8192};n.retained_inventory_ref=ref(current,'inventory.json',n.retained_inventory);application={'format':'aeris-root-observed-development-application-domain','applicationId':'vn.rtr.aeris.betasim09','candidateSHA256':res.digest,'sourceSHA256':'b'*64,'APKSHA256':'c'*64,'privateFilesDirectory':'/data/user/0/vn.rtr.aeris.betasim09/files','nativeReportedApplicationId':False,'retainedInventoryRef':n.retained_inventory_ref};n.application_domain_ref=ref(current,'application.json',application)
  result=prepare_export(b,res,f.C,n);manifest_original=Path(result['manifestPath']).read_bytes();manifest=json.loads(manifest_original);history=manifest['retainedOriginalApplication'];assert history['path']=='android-api/retained-original-application.tar'and history['role']=='HISTORICAL_RETAINED_NOT_CURRENT_FLIGHT_INPUT';groups.append('actual-export-streams-existing-original-TAR-once-existing-android-api-namespace-six-original-proof-spans-no-second-copy')
  @contextmanager
  def opener(path,part):
   with Path(path).open('rb')as stream:stream.seek(part['offset']);yield io.BytesIO(stream.read(part['bytes']))
  proof=verify_recipient(manifest_original,manifest_sha=H(manifest_original),expected_context=f.C,expected_candidate=res.digest,bundle_openers=[lambda p=p:opener(result['bundlePath'],p)for p in manifest['bundle']['parts']],native_openers=[lambda p=p:opener(native,p)for p in manifest['nativeStream']['parts']]);assert proof['historicalRetainedOriginalVerified']is True and proof['historicalOldInputAuthorityGranted']is False;groups.append('independent-real-gzip-TAR-byte-SHA-span-cold-application-backup-DU-join-current-AJ02-separate-no-old-authority')
  for field,value in [('sha256','f'*64),('role','CURRENT_AUTHORITY')]:
   bad=copy.deepcopy(manifest);bad['retainedOriginalApplication'][field]=value;raw=encoded(bad)
   try:verify_recipient(raw,manifest_sha=H(raw),expected_context=f.C,expected_candidate=res.digest,bundle_openers=[],native_openers=[])
   except ValueError as e:assert'HISTORICAL'in str(e)
   else:raise AssertionError('historical context accepted')
  groups.append('wrong-historical-SHA-or-authority-role-rejected-before-stream-or-publication')
  # Re-sign only fixture transport/file hashes after changing an ORIGINAL
  # internal reference; the receiver must reject cross-binding, not just SHA.
  with tarfile.open(result['bundlePath'],'r:gz')as tar:original_members={q.name:tar.extractfile(q).read()for q in tar if q.isfile()}
  @contextmanager
  def memory(data):yield io.BytesIO(data)
  for role,field in [('application','retainedInventoryRef'),('du','argvRef'),('du','stdoutRef')]:
   bad=copy.deepcopy(manifest);members=dict(original_members);item=bad['retainedOriginalApplication']['originalRefs'][role];body=json.loads(members[item['path']]);body[field]['sha256']='f'*64;changed=encoded(body);members[item['path']]=changed;item['bytes']=len(changed);item['sha256']=H(changed)
   for row in bad['files']:
    if row['path']==item['path']:row['bytes']=len(changed);row['sha256']=H(changed)
   bad['totalOriginalBytes']=sum(q['bytes']for q in bad['files']);embedded={k:v for k,v in bad.items()if k not in('bundle','nativeStream','manifestKind')};members['closed-raw-manifest.json']=encoded(embedded);buffer=io.BytesIO()
   with gzip.GzipFile(fileobj=buffer,mode='wb',mtime=0)as gz:
    with tarfile.open(fileobj=gz,mode='w|',format=tarfile.USTAR_FORMAT)as tar:
     for name,data in members.items():q=tarfile.TarInfo(name);q.size=len(data);tar.addfile(q,io.BytesIO(data))
   bundle=buffer.getvalue();bad['bundle'].update(bytes=len(bundle),sha256=H(bundle),parts=[{'index':0,'offset':0,'bytes':len(bundle),'sha256':H(bundle)}]);raw=encoded(bad)
   try:verify_recipient(raw,manifest_sha=H(raw),expected_context=f.C,expected_candidate=res.digest,bundle_openers=[lambda:memory(bundle)],native_openers=[lambda p=p:opener(native,p)for p in bad['nativeStream']['parts']])
   except ValueError as e:assert'HISTORICAL_EXACT_CROSS_REFERENCE_JOIN'in str(e),str(e)
   else:raise AssertionError('mutated internal original ref accepted')
  groups.append('original-application-inventory-and-DU-argv-stdout-reference-mutations-refused-even-with-recomputed-file-TAR-part-manifestSHA')
  assert H(old.read_bytes())==source_old['sha256'];out=R/'evidence/betasim-integrated01/runtime/application09-historical-raw-mock04.json';assert not out.exists();report={'format':'aeris-historical-original-application09-raw-transfer-seam','status':'PASS_REAL_TINY_EXPORT_AND_INDEPENDENT_RECIPIENT_NOT_FLIGHT_OR_SAF_DEVICE','groups':groups,'sourcePins':{name:H((T/'source/aeris_runtime'/name).read_bytes())for name in('raw_export.py','saf_receiver.py')},'oldOriginalUnchanged':True,'actualDeviceOrSDK':False,'genuineSAFOrigin':False,'secondHistoricalTARCopyCreated':False,'scratchRemoved':str(LAB.relative_to(R))};out.write_bytes(encoded(report));print(json.dumps(report))
 finally:f.LAB=old_lab;shutil.rmtree(LAB)
if __name__=='__main__':main()
