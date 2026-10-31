"""Cached development-only CONTROL01 APK build; never install or launch."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,subprocess,zipfile,tarfile
R=Path(__file__).resolve().parents[3];N=R/'native/betaintegrated01/cockpit05';CONTROL04=R/'native/betaintegrated01/cockpit04';REUSE=R/'native/betaintegrated01/cockpit03';OWNER_BASE=R/'native/betaintegrated01/control03';FLIGHT_BASE=R/'native/betaintegrated01/control02';BASE=R/'native/betaintegrated01/control01';E=R/'evidence/betaintegrated01-cockpit05-native'
W=R/'native/betaintegrated01/.build/cockpit05-build';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');B=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0');A=Path('/opt/homebrew/share/android-commandlinetools/platforms/android-37.0/android.jar')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',required=True);args=parser.parse_args();assert args.attempt=='02'
    assert shutil.disk_usage(R).free>=20*2**30 and not W.exists()
    expected=R/'planning/betaintegrated01/m1cockpit04/native/expected-providers01.json';bundle=json.loads(expected.read_text());assert set(bundle['profiles'])=={'M1-COCKPIT04-NOMINAL','M1-COCKPIT04-LOSS'}
    own=['ControlAuthority.java','ControlFlight.java','ControlSession.java','RcWire.java']
    sources=[(FLIGHT_BASE if name=='ControlFlight.java' else N if name=='ControlOwner.java' else BASE)/'src/vn/rtr/aeris/control01'/name for name in own]
    sources += sorted((N/'src').rglob('*.java'))
    sources += [CONTROL04/'src/vn/rtr/aeris/control01'/name for name in ['ControlConfig.java','ControlOwner.java']]
    sources += [REUSE/'src/vn/rtr/aeris/cockpit03'/name for name in ['WorkspaceStore.java','WorkspaceDomain.java','NonFlightIntentFence.java','PresentationGate.java','BridgeGate.java']]
    sources += [REUSE/'src/vn/rtr/aeris/control01/TouchControls.java']
    sources += [R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/beta01runtime'/name for name in ['Mavlink.java','NativeSegments.java','Values.java']]
    sources += [R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/native98'/name for name in ['Dialect95.java','Json.java']]
    sources += [R/'native/betaintegrated01/runtime02/src/vn/rtr/aeris/beta01runtime/PendingExplicitAction.java']
    sources += [R/'native/betaintegrated01/src/vn/rtr/aeris/betaintegrated01'/name for name in ['ProviderDescriptor.java','RunLifecycle.java']]
    pinfiles=sources+[N/'AndroidManifest.xml',N/'build02.py',expected,*sorted((N/'assets').rglob('*'))];pinfiles=[p for p in pinfiles if p.is_file()];assets={}
    for case in ('nominal','loss'):
        root=R/'pilot/betaintegrated01/cockpit04/profiles'/case;profile=root/'run-profile02.json';typed=root/'typed-profile01.json';data=json.loads(profile.read_text());p=bundle['profiles'][data['id']]
        assert p['configSHA256']==sha(profile) and p['typedSHA256']==sha(typed) and p['binarySHA256']==data['APSHA256'] and p['modelSHA256']==data['modelSHA256'] and p['manualCapability'] is True and p['capabilityProfile']=='M1_COCKPIT04_NO_MEDIA' and p['durationSeconds']==2000
        assets[p['typedAsset']]=typed;pinfiles.extend([profile,typed])
    prior=json.loads((R/'evidence/betaintegrated01-m1cockpit04/native/build-02.json').read_text());assert all(sha(R/path)==digest for path,digest in prior['sourcePins'].items());
    uiSource=R/'planning/betaintegrated01/cockpit05-ui/assets';assert {str(p.relative_to(N/'assets')) for p in (N/'assets').rglob('*') if p.is_file()}=={str(p.relative_to(uiSource)) for p in uiSource.rglob('*') if p.is_file()}
    assert all(sha(p)==sha(uiSource/p.relative_to(N/'assets')) for p in (N/'assets').rglob('*') if p.is_file() and p.name not in ('index.html','cockpit.css'))
    error='<p id="draft-error" class="inline-error" role="status"></p>'
    assert (N/'assets/index.html').read_text()==(uiSource/'index.html').read_text().replace(error,'').replace('<footer><button id="draft-save"','<footer>'+error+'<button id="draft-save"')
    assert (N/'assets/cockpit.css').read_text()==(uiSource/'cockpit.css').read_text()+'\n.inline-error:empty{display:none}.work-panel>footer .inline-error{margin:0 0 10px}\n'
    assert not any(p.name in ('mock-bridge.js','mock.html','mock.css') for p in pinfiles)
    assert sum(p.stat().st_size for p in pinfiles)<32*2**20
    pins={str(p.relative_to(R)):sha(p) for p in pinfiles};logs=[];success=False;target=N/'dist'/('aeris-cockpit05-development.apk' if args.attempt=='01' else 'aeris-cockpit05-development-'+args.attempt+'.apk');assert not target.exists()
    W.mkdir()
    archive=E/('build-inputs-'+args.attempt+'.tar');assert not archive.exists()
    with tarfile.open(archive,'x')as tar:
        for path in pinfiles:tar.add(path,arcname=str(path.relative_to(R)),recursive=False)
    def run(argv):
        p=subprocess.run([str(x)for x in argv],cwd=R,env={**os.environ,'JAVA_HOME':str(J)},text=True,capture_output=True);logs.append({'argv':[str(x)for x in argv],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,logs[-1];return p.stdout+p.stderr
    try:
        classes=W/'classes';classes.mkdir();run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*sources])
        assetsDir=W/'assets';assetsDir.mkdir();(assetsDir/'source-identity.json').write_text(json.dumps({'format':'aeris-cockpit05-source-identity','sourceSHA256':hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest(),'OwnerRevision':'OWNER03_ALGORITHM_CAPACITY160_SHADOW','FlightRevision':'ACCEPTED_FLIGHT02','UIRevision':'UI05_VALIDATION_NOTICE_FOOTER_ONLY_NO_LOGIC_CHANGE'})+'\n');shutil.copytree(N/'assets',assetsDir/'cockpit');shutil.copyfile(expected,assetsDir/'expected-providers.json')
        for name,p in assets.items():shutil.copyfile(p,assetsDir/name)
        run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-A',assetsDir,'-o',W/'unsigned.apk']);dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*sorted(classes.rglob('*.class'))])
        with zipfile.ZipFile(W/'unsigned.apk','a')as z:z.write(dex/'classes.dex','classes.dex')
        with zipfile.ZipFile(W/'unsigned.apk')as selected:
            dexBytes=selected.read('classes.dex');assert not any(name in dexBytes for name in (b'DirectTransport95',b'UnifiedCore98',b'UnifiedTransport98'))
        run([B/'zipalign','-f','4',W/'unsigned.apk',W/'aligned.apk']);target.parent.mkdir(exist_ok=True);K=R/'.local/native31'
        run([B/'apksigner','sign','--ks',K/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(K/'password'),'--out',target,W/'aligned.apk'])
        assert target.stat().st_size<32*2**20
        signature=run([B/'apksigner','verify','--verbose','--print-certs',target]);assert '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'in signature
        with zipfile.ZipFile(W/'aligned.apk')as before,zipfile.ZipFile(target)as after:assert all(before.read(n)==after.read(n)for n in before.namelist())
        assert all(sha(R/path)==digest for path,digest in pins.items())
        receipt={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'DEVELOPMENT_CONTROL_APK_BUILT_NOT_ACTUAL_ACCEPTED','apk':str(target.relative_to(R)),'sha256':sha(target),'bytes':target.stat().st_size,'sourcePins':pins,'sourceSHA256':hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest(),'signature':signature,'permissions':run([B/'aapt2','dump','permissions',target]),'expectedProfiles':bundle,'toolPins':{str(p):sha(p)for p in [J/'bin/javac',B/'aapt2',B/'d8',B/'zipalign',B/'apksigner',A]},'inputArchive':str(archive.relative_to(R)),'inputArchiveSHA256':sha(archive),'productionSigning':False,'installOrRuntimeLaunch':False,'buildScriptSHA256':sha(__file__),'revision':'COCKPIT05_REVISION02_VALIDATION_NOTICE_FOOTER_ONLY','priorAPK':prior['apk'],'priorAPK_SHA256':prior['sha256'],'priorInputPinsUnchanged':True,'changedPayloadEntries':'VALIDATION_ERROR_MOVED_OUTSIDE_SCROLL_ABOVE_SAVE_ONLY'}
        (E/f'build-{args.attempt}.json').open('x').write(json.dumps(receipt,indent=2)+'\n');success=True;print(json.dumps({k:receipt[k]for k in ['status','apk','sha256','bytes']}))
    finally:
        scratch={'files':len([p for p in W.rglob('*')if p.is_file()]),'bytes':sum(p.stat().st_size for p in W.rglob('*')if p.is_file())};assert scratch['bytes']<128*2**20;shutil.rmtree(W);(E/f'build-log-{args.attempt}.json').open('x').write(json.dumps({'success':success,'logs':logs,'scratchRemoved':str(W.relative_to(R)),'scratchBeforeCleanup':scratch,'existsAfter':W.exists()},indent=2)+'\n')
if __name__=='__main__':main()
