"""Root-only bounded cached development build. No install, launch or SDK download."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,json,os,shutil,subprocess,tarfile,zipfile
R=Path(__file__).resolve().parents[2];N=Path(__file__).resolve().parent
E=R/'evidence/betasim-integrated01';OUT=E/'candidates';WORK=N/'.build'
JAVA=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home')
TOOLS=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0')
ANDROID=Path('/opt/homebrew/share/android-commandlinetools/platforms/android-37.0/android.jar')
CERT='3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'
SELECTED=['ProductActivity.java','WorkspaceStore.java','OperationGate.java','NativeInputBridge.java','FlightPads.java','ProductStatusReceiver.java','InputJournal.java','ExportBudget.java']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():return sorted([*(N/'src/vn/rtr/aeris/mission'/x for x in SELECTED),N/'AndroidManifest.xml',N/'protocols/product-protocol.json',Path(__file__).resolve()])
def pins():return {str(p.relative_to(R)):sha(p) for p in inputs()}
def source_digest(p):return hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
def artifact_union():
 roots=[R/'evidence/runtime-transport15/candidates',R/'evidence/runtime-transport15-atomic-prep/candidates',OUT];seen=set();total=0
 for root in roots:
  if not root.exists():continue
  for path in [root,*root.rglob('*')]:
   stat=path.lstat();assert not path.is_symlink(),'ARTIFACT_SYMLINK'
   identity=(stat.st_dev,stat.st_ino)
   if identity not in seen:seen.add(identity);total+=stat.st_blocks*512
 return total
def hold():
 value=pins();body={'format':'aeris-betasim-native-source-hold','version':1,'sourcePins':value,'sourceSHA256':source_digest(value),'selectedJava':SELECTED,'notSelectedLegacyIntake':'OtherJava/assets/protocols from originalf459 extraction are regression intake only, never selected by javac/aapt.','production':False}
 p=E/'product/native-source-HOLD01.json';assert not p.exists();p.write_text(json.dumps(body,indent=2)+'\n');return body
def build():
 assert shutil.disk_usage(R).free>=10*2**30+256*2**20+32*2**20,'HOST_DISK_FLOOR_RESERVE'
 source_hold=E/'product/native-source-HOLD01.json';frozen=json.loads(source_hold.read_bytes());value=pins();assert value==frozen['sourcePins'],'SELECTED_NATIVE_SOURCE_DRIFT'
 gate=E/'qa/NATIVE-SOURCE-GATE01.json';review=json.loads(gate.read_bytes());assert review['status']=='PASS'and review['sourceSHA256']==source_digest(value),'NATIVE_INDEPENDENT_SOURCE_GATE'
 receipt_path=E/'product/native-build01.json';log_path=E/'product/native-build-log01.json';assert not receipt_path.exists()and not log_path.exists()and not WORK.exists(),'ONE_BUILD_ATTEMPT_ONLY'
 source=source_digest(value);archive_bound=sum(p.stat().st_size+2048 for p in inputs())+131072;apk_bound=256*1024
 original_union=artifact_union();assert original_union+archive_bound+apk_bound+32768<=4*2**20,'UNION4MIB_PREFLIGHT'
 logs=[];success=False;failure=None;OUT.mkdir(exist_ok=True)
 def run(argv):
  assert shutil.disk_usage(R).free>=10*2**30+256*2**20,'HOST_DISK_FLOOR_RESERVE'
  env={k:v for k,v in os.environ.items()if k not in('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS')};env['JAVA_HOME']=str(JAVA)
  result=subprocess.run([str(x)for x in argv],cwd=R,env=env,capture_output=True,text=True,timeout=90)
  logs.append({'argv':[str(x)for x in argv],'exit':result.returncode,'stdout':result.stdout[-16384:],'stderr':result.stderr[-16384:]});assert result.returncode==0,'BUILD_TOOL_FAILED:'+str(argv[0]);return result.stdout+result.stderr
 try:
  WORK.mkdir();archive=OUT/(source+'-inputs.tar.gz');assert not archive.exists()
  with archive.open('xb')as target:
   with gzip.GzipFile(fileobj=target,mode='wb',mtime=0)as stream:
    with tarfile.open(fileobj=stream,mode='w')as tar:
     for p in inputs():tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
  assert archive.stat().st_size<=archive_bound
  classes=WORK/'classes';classes.mkdir();run([JAVA/'bin/javac','-J-Xmx256m','-source','8','-target','8','-bootclasspath',str(TOOLS/'core-lambda-stubs.jar')+os.pathsep+str(ANDROID),'-d',classes,*(N/'src/vn/rtr/aeris/mission'/x for x in SELECTED)])
  assets=WORK/'assets';assets.mkdir();protocol=N/'protocols/product-protocol.json';shutil.copyfile(protocol,assets/'product-protocol.json')
  identity={'format':'aeris-betasim-product-source-identity','version':1,'sourceSHA256':source,'package':'vn.rtr.aeris.mission','productKind':'BETASIM_INTEGRATED','productProtocolSHA256':sha(protocol),'production':False,'development':True,'M1OperationalProviderIncluded':False}
  (assets/'source-identity.json').write_text(json.dumps(identity,sort_keys=True)+'\n')
  run([TOOLS/'aapt2','link','-I',ANDROID,'--manifest',N/'AndroidManifest.xml','-A',assets,'-o',WORK/'unsigned.apk'])
  dex=WORK/'dex';dex.mkdir();run([TOOLS/'d8','-JXmx256m','--min-api','26','--lib',ANDROID,'--output',dex,*sorted(classes.rglob('*.class'))])
  with zipfile.ZipFile(WORK/'unsigned.apk','a')as z:z.write(dex/'classes.dex','classes.dex')
  with zipfile.ZipFile(WORK/'unsigned.apk')as z:
   code=z.read('classes.dex');assert b'Lvn/rtr/aeris/mission/ProductActivity;'in code and b'Lvn/rtr/aeris/mission/NativeInputBridge;'in code
   assert b'Lvn/rtr/aeris/control01/'not in code,'NO_HIDDEN_M1_OPERATIONAL_PROVIDER'
  run([TOOLS/'zipalign','-f','4',WORK/'unsigned.apk',WORK/'aligned.apk'])
  keys=R/'.local/native31';signed=WORK/'signed.apk'
  run([TOOLS/'apksigner','sign','--ks',keys/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(keys/'password'),'--out',signed,WORK/'aligned.apk'])
  signature=run([TOOLS/'apksigner','verify','--verbose','--print-certs',signed]);assert CERT in signature
  assert signed.stat().st_size<=apk_bound and artifact_union()+((signed.stat().st_size+4095)//4096)*4096+32768<=4*2**20,'APK_UNION4MIB'
  output=OUT/(sha(signed)+'.apk');assert not output.exists();shutil.copyfile(signed,output);assert pins()==value
  receipt={'format':'aeris-development-build','version':2,'productKind':'BETASIM_INTEGRATED','package':'vn.rtr.aeris.mission','activity':'.ProductActivity','sourcePins':value,'sourceSHA256':source,'sourceCount':len(value),'apk':str(output.relative_to(R)),'sha256':sha(output),'bytes':output.stat().st_size,'inputArchive':str(archive.relative_to(R)),'inputArchiveSHA256':sha(archive),'productProtocolSHA256':sha(protocol),'certificateSHA256':CERT,'signature':signature,'productionSigning':False,'installOrRuntimeLaunch':False,'artifactUnionBeforeBytes':original_union,'artifactUnionAfterBytes':artifact_union(),'entryFreeBytes':shutil.disk_usage(R).free,'sourceHoldSHA256':sha(source_hold),'sourceGateSHA256':sha(gate),'toolPins':{str(p):sha(p)for p in[TOOLS/'aapt2',TOOLS/'d8',TOOLS/'apksigner',TOOLS/'zipalign',JAVA/'bin/javac',JAVA/'bin/java',ANDROID]},'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  receipt_path.write_text(json.dumps(receipt,indent=2)+'\n');success=True;print(json.dumps({k:receipt[k]for k in('apk','sha256','sourceSHA256','bytes','artifactUnionAfterBytes')}))
 except BaseException as error:failure=type(error).__name__+':'+str(error);raise
 finally:
  scratch=sum(p.stat().st_size for p in WORK.rglob('*')if p.is_file())
  if WORK.exists():shutil.rmtree(WORK)
  log_path.write_text(json.dumps({'success':success,'failure':failure,'logs':logs,'scratchBytes':scratch,'within32MiB':scratch<=32*2**20,'scratchRemoved':str(WORK),'existsAfter':WORK.exists()},indent=2)+'\n')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--hold',action='store_true');parser.add_argument('--build',action='store_true');args=parser.parse_args();assert args.hold!=args.build
 print(json.dumps(hold()))if args.hold else build()
