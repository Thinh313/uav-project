"""Cached development-only CONTROL01 APK build; never install or launch."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,subprocess,zipfile
R=Path(__file__).resolve().parents[3];N=R/'native/betaintegrated01/control02';BASE=R/'native/betaintegrated01/control01';E=R/'evidence/betaintegrated01-m1control01/native'
W=R/'native/betaintegrated01/.build/control01-build';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');B=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0');A=Path('/opt/homebrew/share/android-commandlinetools/platforms/android-37.0/android.jar')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',required=True);args=parser.parse_args();assert args.attempt=='02'
    assert shutil.disk_usage(R).free>=20*2**30 and not W.exists()
    expected=R/'planning/betaintegrated01/m1control01/native/expected-providers02.json';bundle=json.loads(expected.read_text());assert set(bundle['profiles'])=={'M1-CONTROL01-NOMINAL','M1-CONTROL01-LOSS'}
    own=['ControlActivity.java','ControlAuthority.java','ControlConfig.java','ControlFlight.java','ControlOwner.java','ControlSession.java','RcWire.java','TouchControls.java']
    sources=[(N if name=='ControlFlight.java' else BASE)/'src/vn/rtr/aeris/control01'/name for name in own]
    sources += [R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/beta01runtime'/name for name in ['Mavlink.java','NativeSegments.java','Values.java']]
    sources += [R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/native98'/name for name in ['Dialect95.java','Json.java']]
    sources += [R/'native/betaintegrated01/runtime02/src/vn/rtr/aeris/beta01runtime/PendingExplicitAction.java']
    sources += [R/'native/betaintegrated01/src/vn/rtr/aeris/betaintegrated01'/name for name in ['ProviderDescriptor.java','RunLifecycle.java']]
    pinfiles=sources+[BASE/'AndroidManifest.xml',expected];assets={}
    for case in ('nominal','loss'):
        root=R/'runtime/betaintegrated01/control01'/case;profile=root/'run-profile02.json';typed=root/'typed-profile.json';data=json.loads(profile.read_text());p=bundle['profiles'][data['id']]
        assert p['configSHA256']==sha(profile) and p['typedSHA256']==sha(typed) and p['binarySHA256']==data['APSHA256'] and p['modelSHA256']==data['modelSHA256'] and p['manualCapability'] is True and p['capabilityProfile']=='M1_CONTROL01_NO_MEDIA'
        assets[p['typedAsset']]=typed;pinfiles.extend([profile,typed])
    prior=json.loads((E/'build-01.json').read_text());assert all(sha(R/path)==digest for path,digest in prior['sourcePins'].items());
    pins={str(p.relative_to(R)):sha(p) for p in pinfiles};logs=[];success=False;W.mkdir();target=N/'dist'/f'aeris-control01-development-{args.attempt}.apk';assert not target.exists()
    def run(argv):
        p=subprocess.run([str(x)for x in argv],cwd=R,env={**os.environ,'JAVA_HOME':str(J)},text=True,capture_output=True);logs.append({'argv':[str(x)for x in argv],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,logs[-1];return p.stdout+p.stderr
    try:
        classes=W/'classes';classes.mkdir();run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*sources])
        assetsDir=W/'assets';assetsDir.mkdir();shutil.copyfile(expected,assetsDir/'expected-providers.json')
        for name,p in assets.items():shutil.copyfile(p,assetsDir/name)
        run([B/'aapt2','link','-I',A,'--manifest',BASE/'AndroidManifest.xml','-A',assetsDir,'-o',W/'unsigned.apk']);dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*sorted(classes.rglob('*.class'))])
        with zipfile.ZipFile(W/'unsigned.apk','a')as z:z.write(dex/'classes.dex','classes.dex')
        run([B/'zipalign','-f','4',W/'unsigned.apk',W/'aligned.apk']);target.parent.mkdir(exist_ok=True);K=R/'.local/native31'
        run([B/'apksigner','sign','--ks',K/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(K/'password'),'--out',target,W/'aligned.apk'])
        signature=run([B/'apksigner','verify','--verbose','--print-certs',target]);assert '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'in signature
        with zipfile.ZipFile(W/'aligned.apk')as before,zipfile.ZipFile(target)as after:assert all(before.read(n)==after.read(n)for n in before.namelist())
        assert all(sha(R/path)==digest for path,digest in pins.items())
        with zipfile.ZipFile(R/prior['apk']) as old,zipfile.ZipFile(target) as new:
            assert set(old.namelist())==set(new.namelist())
            changedPayload=[name for name in old.namelist() if not name.startswith('META-INF/') and old.read(name)!=new.read(name)]
        assert changedPayload==['classes.dex'],changedPayload
        receipt={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'DEVELOPMENT_CONTROL_APK_BUILT_NOT_ACTUAL_ACCEPTED','apk':str(target.relative_to(R)),'sha256':sha(target),'bytes':target.stat().st_size,'sourcePins':pins,'sourceSHA256':hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest(),'signature':signature,'permissions':run([B/'aapt2','dump','permissions',target]),'expectedProfiles':bundle,'toolPins':{str(p):sha(p)for p in [J/'bin/javac',B/'aapt2',B/'d8',B/'zipalign',B/'apksigner',A]},'productionSigning':False,'installOrRuntimeLaunch':False,'buildScriptSHA256':sha(__file__),'revision':'VERSIONED_PREFLIGHT_GPS_SENTINEL_STATIC_FIX_EKF_UNKNOWN_MASK_ONLY','priorAPK':prior['apk'],'priorAPK_SHA256':prior['sha256'],'priorInputPinsUnchanged':True,'changedPayloadEntries':changedPayload}
        (E/f'build-{args.attempt}.json').open('x').write(json.dumps(receipt,indent=2)+'\n');success=True;print(json.dumps({k:receipt[k]for k in ['status','apk','sha256','bytes']}))
    finally:
        scratch={'files':len([p for p in W.rglob('*')if p.is_file()]),'bytes':sum(p.stat().st_size for p in W.rglob('*')if p.is_file())};assert scratch['bytes']<128*2**20;shutil.rmtree(W);(E/f'build-log-{args.attempt}.json').open('x').write(json.dumps({'success':success,'logs':logs,'scratchRemoved':str(W.relative_to(R)),'scratchBeforeCleanup':scratch,'existsAfter':W.exists()},indent=2)+'\n')
if __name__=='__main__':main()
