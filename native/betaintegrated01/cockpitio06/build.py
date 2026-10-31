"""Cached isolated NativeIO04 development APK; no install, device or runtime launch."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,subprocess,zipfile,tarfile
R=Path(__file__).resolve().parents[3];N=R/'native/betaintegrated01/cockpitio06';CONTROL04=R/'native/betaintegrated01/cockpit04';REUSE=R/'native/betaintegrated01/cockpit03';OWNER_BASE=R/'native/betaintegrated01/control03';FLIGHT_BASE=R/'native/betaintegrated01/control02';BASE=R/'native/betaintegrated01/control01';E=R/'evidence/betaintegrated01-cockpit05-nativeio06/native'
W=R/'native/betaintegrated01/.build/cockpitio06-build';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');B=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0');A=Path('/opt/homebrew/share/android-commandlinetools/platforms/android-37.0/android.jar')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',required=True);args=parser.parse_args();assert args.attempt=='01'
    entryFree=shutil.disk_usage(R).free;assert entryFree>=10*2**30+256*2**20+32*2**20 and not W.exists()
    # Small cached build only; actual flight admission remains separate.
    power=subprocess.check_output(['pmset','-g','batt'],text=True,timeout=3)
    expected=R/'planning/betaintegrated01/m1cockpit04/native/expected-providers01.json';bundle=json.loads(expected.read_text());assert set(bundle['profiles'])=={'M1-COCKPIT04-NOMINAL','M1-COCKPIT04-LOSS'}
    own=['ControlAuthority.java','ControlFlight.java','ControlSession.java','RcWire.java']
    sources=[(FLIGHT_BASE if name=='ControlFlight.java' else N if name=='ControlOwner.java' else BASE)/'src/vn/rtr/aeris/control01'/name for name in own]
    sources += sorted((N/'src').rglob('*.java'))
    sources += [CONTROL04/'src/vn/rtr/aeris/control01/ControlConfig.java',R/'native/betaintegrated01/nativeio06-core/src/vn/rtr/aeris/control01/ControlOwner.java']
    sources += [REUSE/'src/vn/rtr/aeris/cockpit03'/name for name in ['WorkspaceStore.java','WorkspaceDomain.java','NonFlightIntentFence.java','PresentationGate.java','BridgeGate.java']]
    sources += [REUSE/'src/vn/rtr/aeris/control01/TouchControls.java']
    sources += [R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/beta01runtime'/name for name in ['Mavlink.java','Values.java']]
    sources += [R/'native/betaintegrated01/nativeio06-core/src/vn/rtr/aeris/beta01runtime'/name for name in ['NativeSegments.java','IoTiming.java']]
    sources += [R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/native98'/name for name in ['Dialect95.java','Json.java']]
    sources += [R/'native/betaintegrated01/runtime02/src/vn/rtr/aeris/beta01runtime/PendingExplicitAction.java']
    sources += [R/'native/betaintegrated01/src/vn/rtr/aeris/betaintegrated01'/name for name in ['ProviderDescriptor.java','RunLifecycle.java']]
    pinfiles=sources+[N/'AndroidManifest.xml',N/'build.py',expected,*sorted((N/'assets').rglob('*'))];pinfiles=[p for p in pinfiles if p.is_file()];assets={}
    for case in ('nominal','loss'):
        root=R/'pilot/betaintegrated01/cockpit04/profiles'/case;profile=root/'run-profile02.json';typed=root/'typed-profile01.json';data=json.loads(profile.read_text());p=bundle['profiles'][data['id']]
        assert p['configSHA256']==sha(profile) and p['typedSHA256']==sha(typed) and p['binarySHA256']==data['APSHA256'] and p['modelSHA256']==data['modelSHA256'] and p['manualCapability'] is True and p['capabilityProfile']=='M1_COCKPIT04_NO_MEDIA' and p['durationSeconds']==2000
        assets[p['typedAsset']]=typed;pinfiles.extend([profile,typed])
    prior=json.loads((R/'evidence/betaintegrated01-cockpit05-native/build-02.json').read_text());assert all(sha(R/path)==digest for path,digest in prior['sourcePins'].items())
    protectedPath=R/'evidence/betaintegrated01-cockpit05-observer05/host/input-contract01.json';protected=json.loads(protectedPath.read_text());protectedPins={**protected['sourceSHA256'],**protected['metadataSHA256']};assert len(protected['sourceSHA256'])==263 and all(sha(R/path)==digest for path,digest in protectedPins.items())
    # Reviewed core source hashes are added after independent QA source freeze.
    coreManifest=json.loads((R/'evidence/betaintegrated01-cockpit05-nativeio06/native/core-freeze01.json').read_text())
    assert all(sha(R/path)==digest for path,digest in coreManifest['sourceSHA256'].items())
    uiSource=R/'native/betaintegrated01/cockpit05/assets'
    assert {str(p.relative_to(N/'assets')) for p in (N/'assets').rglob('*') if p.is_file()}=={str(p.relative_to(uiSource)) for p in uiSource.rglob('*') if p.is_file()}
    assert all(sha(p)==sha(uiSource/p.relative_to(N/'assets')) for p in (N/'assets').rglob('*') if p.is_file())
    assert not any(p.name in ('mock-bridge.js','mock.html','mock.css') for p in pinfiles)
    assert sum(p.stat().st_size for p in pinfiles)<32*2**20
    pins={str(p.relative_to(R)):sha(p) for p in pinfiles};logs=[];success=False;target=N/'dist'/'aeris-cockpitio06-development.apk';assert not target.exists()
    W.mkdir()
    archive=E/('build-inputs-'+args.attempt+'.tar');assert not archive.exists()
    with tarfile.open(archive,'x')as tar:
        for path in pinfiles:tar.add(path,arcname=str(path.relative_to(R)),recursive=False)
    def run(argv):
        assert shutil.disk_usage(R).free>=10*2**30+256*2**20
        try:p=subprocess.run([str(x)for x in argv],cwd=R,env={**os.environ,'JAVA_HOME':str(J)},text=True,capture_output=True,timeout=90)
        except subprocess.TimeoutExpired as e:
            logs.append({'argv':[str(x)for x in argv],'exit':None,'timeoutSeconds':90,'stdout':str(e.stdout or b''),'stderr':str(e.stderr or b'')});raise
        logs.append({'argv':[str(x)for x in argv],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,logs[-1];return p.stdout+p.stderr
    try:
        classes=W/'classes';classes.mkdir();run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*sources])
        assetsDir=W/'assets';assetsDir.mkdir();(assetsDir/'source-identity.json').write_text(json.dumps({'format':'aeris-cockpitio06-source-identity','sourceSHA256':hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest(),'OwnerRevision':'NATIVEIO06_GLOBAL16_INTER_IO_FIFO_CAPACITY160_BOUNDED_DIAGNOSTICS','FlightRevision':'ACCEPTED_FLIGHT02','UIRevision':'EXACT_UI05_ASSETS_PACKAGE06_WITH_READONLY_SOURCE_DIAGNOSTIC_BINDING'})+'\n');shutil.copytree(N/'assets',assetsDir/'cockpit');shutil.copyfile(expected,assetsDir/'expected-providers.json')
        for name,p in assets.items():shutil.copyfile(p,assetsDir/name)
        run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-A',assetsDir,'-o',W/'unsigned.apk']);dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*sorted(classes.rglob('*.class'))])
        with zipfile.ZipFile(W/'unsigned.apk','a')as z:z.write(dex/'classes.dex','classes.dex')
        with zipfile.ZipFile(W/'unsigned.apk')as selected:
            dexBytes=selected.read('classes.dex');assert not any(name in dexBytes for name in (b'DirectTransport95',b'UnifiedCore98',b'UnifiedTransport98',b'Lvn/rtr/aeris/cockpit05/',b'Lvn/rtr/aeris/cockpit04/',b'Lvn/rtr/aeris/cockpitio04/'))
            assert b'Lvn/rtr/aeris/cockpitio06/CockpitActivity;'in dexBytes
        run([B/'zipalign','-f','4',W/'unsigned.apk',W/'aligned.apk']);target.parent.mkdir(exist_ok=True);K=R/'.local/native31'
        run([B/'apksigner','sign','--ks',K/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(K/'password'),'--out',target,W/'aligned.apk'])
        assert target.stat().st_size<32*2**20
        signature=run([B/'apksigner','verify','--verbose','--print-certs',target]);assert '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'in signature
        with zipfile.ZipFile(W/'aligned.apk')as before,zipfile.ZipFile(target)as after:assert all(before.read(n)==after.read(n)for n in before.namelist())
        assert all(sha(R/path)==digest for path,digest in pins.items())
        assert all(sha(R/path)==digest for path,digest in protectedPins.items())
        receipt={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'DEVELOPMENT_NATIVEIO06_APK_BUILT_NOT_ACTUAL_ACCEPTED','apk':str(target.relative_to(R)),'sha256':sha(target),'bytes':target.stat().st_size,'sourcePins':pins,'sourceSHA256':hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest(),'signature':signature,'permissions':run([B/'aapt2','dump','permissions',target]),'expectedProfiles':bundle,'toolPins':{str(p):sha(p)for p in [J/'bin/javac',B/'aapt2',B/'d8',B/'zipalign',B/'apksigner',A]},'inputArchive':str(archive.relative_to(R)),'inputArchiveSHA256':sha(archive),'productionSigning':False,'installOrRuntimeLaunch':False,'buildScriptSHA256':sha(__file__),'revision':'COCKPITIO06_GLOBAL16_INTER_IO_INSTRUMENTED_PREPARATION','priorAPK':prior['apk'],'priorAPK_SHA256':prior['sha256'],'priorInputPinsUnchanged':True,'protected263SourcesAnd12MetadataUnchanged':True,'protectedManifestSHA256':sha(protectedPath),'protectedSourceCount':len(protected['sourceSHA256']),'protectedMetadataCount':len(protected['metadataSHA256']),'changedPayloadEntries':'NATIVEIO06_OWNER_IOTIMING_TWO_WRITE_HOOKS_AND_DIAGNOSTIC_SOURCE_BINDING_NEWPACKAGE','entryFreeBytes':entryFree,'buildBudgetBytes':32*2**20,'entryBytes':10*2**30,'liveFloorAndReserveBytes':10*2**30+256*2**20,'powerObservation':power}
        (E/f'build-{args.attempt}.json').open('x').write(json.dumps(receipt,indent=2)+'\n');success=True;print(json.dumps({k:receipt[k]for k in ['status','apk','sha256','bytes']}))
    finally:
        scratch={'files':len([p for p in W.rglob('*')if p.is_file()]),'bytes':sum(p.stat().st_size for p in W.rglob('*')if p.is_file())};shutil.rmtree(W);(E/f'build-log-{args.attempt}.json').open('x').write(json.dumps({'success':success,'logs':logs,'scratchRemoved':str(W.relative_to(R)),'scratchBeforeCleanup':scratch,'existsAfter':W.exists(),'declaredBuildBudgetBytes':32*2**20,'scratchWithinDeclaredBudget':scratch['bytes']<32*2**20},indent=2)+'\n')
if __name__=='__main__':main()
