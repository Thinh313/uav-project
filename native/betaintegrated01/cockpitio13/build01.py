"""Isolated cached IOADMIT13 development build, never install/launch. Requires independent source freeze."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,tarfile,zipfile
R=Path(__file__).resolve().parents[3];N=R/'native/betaintegrated01/cockpitio13';CORE=R/'native/betaintegrated01/ioadmit13-core/src/vn/rtr/aeris';E=R/'evidence/betaintegrated01-cockpit05-ioadmit13/native';W=R/'native/betaintegrated01/.build/native-development';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');B=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0');A=Path('/opt/homebrew/share/android-commandlinetools/platforms/android-37.0/android.jar')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 entry=shutil.disk_usage(R).free;assert entry>=10*2**30+256*2**20+32*2**20 and not W.exists()
 parent=json.loads((R/'evidence/betaintegrated01-cockpit05-release12/native/build-01.json').read_text());assert all(sha(R/p)==s for p,s in parent['sourcePins'].items()) and sha(R/parent['apk'])==parent['sha256']
 protocol=R/'evidence/betaintegrated01-cockpit05-release12/native/RELEASE-PROTOCOL01.json';ioProtocol=E/'IOADMIT-PROTOCOL01.json';freeze=json.loads((E/'core-freeze01.json').read_text());assert all(sha(R/p)==s for p,s in freeze['sourceSHA256'].items())
 sources=[]
 for path in parent['sourcePins']:
  if not path.endswith('.java'):continue
  name=Path(path).name
  if name in ('ControlOwner.java','ControlAuthority.java','ControlSession.java','TouchControls.java','ReleaseControl.java'):p=CORE/'control01'/name
  elif name=='NativeSegments.java':p=CORE/'beta01runtime'/name
  elif name in ('CockpitActivity.java','ClosedReview.java'):p=N/'src/vn/rtr/aeris/cockpitio13'/name
  else:p=R/path
  sources.append(p)
 expected=R/'planning/betaintegrated01/m1cockpit04/native/expected-providers01.json';bundle=json.loads(expected.read_text())
 files=sources+[N/'AndroidManifest.xml',Path(__file__).resolve(),expected,protocol,ioProtocol,*sorted(p for p in (N/'assets').rglob('*')if p.is_file())];typed={}
 for case in ('nominal','loss'):
  profile=R/'pilot/betaintegrated01/cockpit04/profiles'/case/'run-profile02.json';t=profile.with_name('typed-profile01.json');data=json.loads(profile.read_text());pin=bundle['profiles'][data['id']];assert pin['configSHA256']==sha(profile)and pin['typedSHA256']==sha(t)and pin['durationSeconds']==2000 and pin['manualCapability'] is True;typed[pin['typedAsset']]=t;files.extend([profile,t])
 assert len(files)==43 and len(set(files))==43 and all(p.is_file()for p in files)
 oldAssets=R/'native/betaintegrated01/cockpitio12/assets';assert all(sha(p)==sha(oldAssets/p.relative_to(N/'assets'))for p in (N/'assets').rglob('*')if p.is_file())
 pins={str(p.relative_to(R)):sha(p)for p in files};sourceSHA=hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest();target=N/'dist/aeris-cockpitio13-development-01.apk';assert not target.exists();archive=E/'build-inputs-01.tar';assert not archive.exists();logs=[];success=False
 W.mkdir();
 with tarfile.open(archive,'x')as tar:
  for p in files:tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
 def run(argv):
  assert shutil.disk_usage(R).free>=10*2**30+256*2**20
  try:p=subprocess.run(list(map(str,argv)),cwd=R,env={**os.environ,'JAVA_HOME':str(J)},capture_output=True,text=True,timeout=90)
  except subprocess.TimeoutExpired as ex:logs.append({'argv':list(map(str,argv)),'exit':None,'stdout':str(ex.stdout),'stderr':str(ex.stderr),'timeout':90});raise
  logs.append({'argv':list(map(str,argv)),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,logs[-1];return p.stdout+p.stderr
 try:
  classes=W/'classes';classes.mkdir();run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*sources]);assets=W/'assets';assets.mkdir();shutil.copytree(N/'assets',assets/'cockpit');shutil.copyfile(expected,assets/'expected-providers.json');shutil.copyfile(protocol,assets/'release-protocol.json');shutil.copyfile(ioProtocol,assets/'ioadmit-protocol.json')
  for name,p in typed.items():shutil.copyfile(p,assets/name)
  (assets/'source-identity.json').write_text(json.dumps({'format':'aeris-cockpitio13-source-identity','sourceSHA256':sourceSHA,'OwnerRevision':'IOADMIT13_RX_GROUP_TWO_DURABLE_THREE_ROWS_FULL_PRECHECK_REJECTION','FlightRevision':'EXACT07_FLIGHT_GUARDS','UIRevision':'EXACT_UI05_ASSETS_ONLY_TYPED_RELEASE_CALLBACK_CHANGED','PhysicalJournal':'EXACT_COMPACT10_FORMAT2_PHYSICAL160_LOGICAL512','InputRevision':'EXACT08_SAMPLER_50MS_UI200_UPTIME_BEFORE_ELAPSED_NO_REFRESH','WireRevision':'IOADMIT13_ATOMIC_LOCAL_DISPATCH_ENTRY_EXPECTED_CANCEL_NOT_REMOTE_ATTESTATION','AuthorityRevision':'IOCOMMIT09_WITH_IOADMIT13_PREPUBLICATION_CANCELLED_RECEIPT','releaseProtocolSHA256':sha(protocol),'ioadmitProtocolSHA256':sha(ioProtocol)})+'\n')
  run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-A',assets,'-o',W/'unsigned.apk']);dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*sorted(classes.rglob('*.class'))])
  with zipfile.ZipFile(W/'unsigned.apk','a')as z:z.write(dex/'classes.dex','classes.dex')
  with zipfile.ZipFile(W/'unsigned.apk')as z:
   d=z.read('classes.dex');assert b'Lvn/rtr/aeris/cockpitio13/CockpitActivity;'in d and b'Lvn/rtr/aeris/control01/ReleaseControl;'in d;assert not any(x in d for x in (b'DirectTransport95',b'UnifiedTransport98',b'Lvn/rtr/aeris/cockpitio12/',b'Lvn/rtr/aeris/cockpitio10/',b'Lvn/rtr/aeris/cockpitio09/'))
  run([B/'zipalign','-f','4',W/'unsigned.apk',W/'aligned.apk']);target.parent.mkdir(exist_ok=True);k=R/'.local/native31';run([B/'apksigner','sign','--ks',k/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(k/'password'),'--out',target,W/'aligned.apk']);signature=run([B/'apksigner','verify','--verbose','--print-certs',target]);assert '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'in signature
  assert all(sha(R/p)==s for p,s in pins.items()) and all(sha(R/p)==s for p,s in parent['sourcePins'].items());assert sha(R/parent['apk'])==parent['sha256'];assert archive.stat().st_size+target.stat().st_size<4*2**20
  receipt={'format':'aeris-development-build','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'IOADMIT13_DEVELOPMENT_BUILT_NOT_RUNTIME_ACCEPTED','apk':str(target.relative_to(R)),'sha256':sha(target),'bytes':target.stat().st_size,'sourcePins':pins,'sourceSHA256':sourceSHA,'signature':signature,'inputArchive':str(archive.relative_to(R)),'inputArchiveSHA256':sha(archive),'buildScriptSHA256':sha(__file__),'parentAPK':parent['apk'],'parentSHA256':parent['sha256'],'parent42PinsUnchanged':True,'releaseProtocolSHA256':sha(protocol),'ioadmitProtocolSHA256':sha(ioProtocol),'productionSigning':False,'installOrRuntimeLaunch':False,'entryFreeBytes':entry,'scratchBudgetBytes':32*2**20,'toolPins':{str(p):sha(p)for p in[J/'bin/javac',B/'aapt2',B/'d8',B/'apksigner',A]}}
  (E/'build-01.json').open('x').write(json.dumps(receipt,indent=2)+'\n');success=True;print(json.dumps({k:receipt[k]for k in('status','apk','sha256','sourceSHA256','bytes')}))
 finally:
  size=sum(p.stat().st_size for p in W.rglob('*')if p.is_file());count=sum(p.is_file()for p in W.rglob('*'));shutil.rmtree(W);(E/'build-log-01.json').open('x').write(json.dumps({'success':success,'logs':logs,'scratchRemoved':str(W.relative_to(R)),'scratchBytes':size,'scratchFiles':count,'existsAfter':W.exists(),'within32MiB':size<32*2**20},indent=2)+'\n')
if __name__=='__main__':main()
