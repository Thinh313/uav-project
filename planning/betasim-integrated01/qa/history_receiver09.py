"""Independent six-span cross-reference fixtures. In-memory, no device actor."""
from pathlib import Path
import copy,gzip,hashlib,io,json,sys,tarfile
R=Path(__file__).resolve().parents[3];helpers=Path(__file__).with_name('saf_receiver.py');ns={'__file__':str(helpers)};code=helpers.read_text();exec(compile(code[:code.index("run('valid-fragmented")],str(helpers),'exec'),ns)
H=ns['sha'];encode=ns['encode'];tar=ns['tar'];parts=ns['parts'];m=ns['m'];C=ns['C'];candidate=ns['candidate'];checks=[]
def fixture(corrupt=None):
 raw,bp,np=ns['fixture']();base=json.loads(raw);native=b''.join(np);body={k:v for k,v in base.items()if k not in('bundle','nativeStream','manifestKind')};body['nativeClosedFiles'].update(sourceSHA256='b'*64,APKSHA256='c'*64)
 with tarfile.open(fileobj=io.BytesIO(gzip.decompress(b''.join(bp))),mode='r:')as t:entries=[(v.name,t.extractfile(v).read())for v in t if v.name!='closed-raw-manifest.json']
 old=tar([('files/old-unknown.bin',b'UNRESOLVED_OLD_HISTORY_NOT_CURRENT_INPUT')]);member='android-api/retained-original-application.tar';entries.append((member,old));refs={}
 def put(label,name,value,prefix):
  data=value if type(value)is bytes else encode(value);r={'format':'aeris-original-byte-ref','version':3,'path':name,'offset':0,'bytes':len(data),'sha256':H(data)};entries.append((prefix+name,data));refs[label]={k:r[k]for k in('offset','bytes','sha256')};refs[label]['path']=prefix+name;return r
 arg=put('duArgv','argv.raw',['/fake/pinned-adb','-s','emulator-5582','shell','run-as','vn.rtr.aeris.mission','du','-k','-s','files'],'android-api/retained-original/');out=put('duStdout','stdout.raw',b'8\tfiles\n','android-api/retained-original/')
 du={'format':'aeris-command','captureComplete':True,'failure':None,'exit':0,'argvRef':copy.deepcopy(arg),'stdoutRef':copy.deepcopy(out)}
 if corrupt=='duArgvSHA':du['argvRef']['sha256']='f'*64
 if corrupt=='duStdoutOffset':du['stdoutRef']['offset']=1
 duref=put('du','du.json',du,'android-api/retained-original/');backup=put('backup','backup.json',{'format':'aeris-native-export','fullOriginalFiles':True,'captureComplete':True,'failure':None,'exit':0,'bytesRetained':len(old)},'android-api/retained-original/')
 original={'path':'SOURCE_HOST_PATH_NOT_GUEST_ATTESTATION','bytes':len(old),'sha256':H(old),'captureComplete':True,'captureReceiptRef':copy.deepcopy(backup)};inventory={'format':'aeris-retained-old-application-private-inventory','package':'vn.rtr.aeris.mission','sourceOriginalTAR':original,'sourceDUCommandRef':copy.deepcopy(duref),'sourceDUStdoutRef':copy.deepcopy(out),'sourceDUArgvRef':copy.deepcopy(arg),'allocatedBytes':8192}
 if corrupt=='inventoryDUPath':inventory['sourceDUCommandRef']['path']='other-du.json'
 if corrupt=='backupRefBytes':inventory['sourceOriginalTAR']['captureReceiptRef']['bytes']+=1
 inv=put('inventory','inventory.json',inventory,'android-api/');application={'format':'aeris-root-observed-development-application-domain','applicationId':'vn.rtr.aeris.betasim09','candidateSHA256':candidate,'sourceSHA256':'b'*64,'APKSHA256':'c'*64,'privateFilesDirectory':'/data/user/0/vn.rtr.aeris.betasim09/files','nativeReportedApplicationId':False,'retainedInventoryRef':copy.deepcopy(inv)}
 if corrupt=='applicationInventorySHA':application['retainedInventoryRef']['sha256']='f'*64
 put('application','application.json',application,'android-api/')
 body.update(files=[{'path':p,'bytes':len(b),'sha256':H(b)}for p,b in entries],totalOriginalBytes=sum(len(b)for _,b in entries),retainedOriginalApplication={'format':'aeris-retained-original-application-transfer','version':1,'path':member,'bytes':len(old),'sha256':H(old),'applicationId':'vn.rtr.aeris.mission','activeApplicationId':'vn.rtr.aeris.betasim09','role':'HISTORICAL_RETAINED_NOT_CURRENT_FLIGHT_INPUT','authorityGranted':False,'originalRefs':refs})
 compressed=gzip.compress(tar([('closed-raw-manifest.json',encode(body)),*entries]),mtime=0);bundle,bp=parts(compressed);bundle['encoding']='TAR_GZIP_LOSSLESS';nativeStream,np=parts(native);nativeStream['encoding']='TAR_UNCOMPRESSED_ORIGINAL';return encode({**body,'bundle':bundle,'nativeStream':nativeStream,'manifestKind':'SOURCE_CLOSED_RAW_EXPORT_NOT_INDEPENDENT_ACCEPTANCE'}),bp,np
def run(name,corrupt=None):
 raw,bp,np=fixture(corrupt);tracker={'opened':0,'closed':0};accepted=False;result=None;error=None
 try:result=m.verify_recipient(raw,manifest_sha=H(raw),expected_context=C,expected_candidate=candidate,bundle_openers=ns['openers'](bp,tracker),native_openers=ns['openers'](np,tracker));accepted=True
 except Exception as e:error=str(e)
 good=accepted if corrupt is None else not accepted;assert good and tracker['opened']==tracker['closed'],(name,accepted,error,tracker)
 if result is not None:assert result['historicalRetainedOriginalVerified']is True and result['historicalOldInputAuthorityGranted']is False and result['nativeInput']['selectedGenerations']==1
 checks.append({'id':name,'accepted':accepted,'error':error,'streamManagers':tracker})
run('valid_six_spans_bound_and_old_UNKNOWN_opaque_not_current_input')
for corruption in['duArgvSHA','duStdoutOffset','inventoryDUPath','backupRefBytes','applicationInventorySHA']:run('rehashed_valid_container_'+corruption+'_must_refuse',corruption)
source=R/'planning/betasim-integrated01/runtime/source/aeris_runtime/saf_receiver.py';out=R/(sys.argv[1]if len(sys.argv)>1 else'evidence/betasim-integrated01/qa/history-receiver09-01.json');assert not out.exists();out.write_bytes(encode({'format':'aeris-independent-historical-six-span-cold-join-qa','status':'PASS_IN_MEMORY_ORIGINAL_REF_BINDING_NOT_ACTUAL_SAF_OR_OLD_APPLICATION','checks':checks,'sourceSHA256':H(source.read_bytes()),'fixtureSHA256':H(Path(__file__).read_bytes()),'genuineCommandReadersOrURIs':False,'actorsStarted':False,'oldUNKNOWNAuthorityAccepted':False})+b'\n');print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(out.read_bytes()),'checks':len(checks)}))
