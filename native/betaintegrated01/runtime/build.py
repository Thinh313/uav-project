"""Cached-toolchain development APK, no launch/install. Preserve build logs."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import zipfile

R=Path(__file__).resolve().parents[3]
N=R/'native/betaintegrated01/runtime'
E=R/'evidence/betaintegrated01-m1runtime/native'
W=R/'native/betaintegrated01/.build/m1runtime-native-build'
J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home')
SDK=Path('/opt/homebrew/share/android-commandlinetools')
B=SDK/'build-tools/36.0.0'
A=SDK/'platforms/android-37.0/android.jar'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--expected',required=True);p.add_argument('--attempt',required=True)
    args=p.parse_args();assert args.attempt in ('01','02','03')
    expected=Path(args.expected).resolve();data=json.loads(expected.read_text())
    assert data['binarySHA256']=='1f8ef6fd3ac2490d65d1750c5eb42ddb3c124aba7d1ebe70cfa575beffb0b828'
    assert data['mode']=='CANDIDATE_EXTERNAL' and data['capabilityProfile']=='NO_MEDIA_M1_RUNTIME'
    assert len(data['modelSHA256'])==64 and len(data['configSHA256'])==64 and data['endpoint']=='tcp://10.0.2.2:5961'
    assert shutil.disk_usage(R).free>=20*2**30 and not W.exists()
    sources=sorted((N/'src').rglob('*.java'))+sorted((R/'native/betaintegrated01/src').rglob('*.java'))
    assert len(sources)<=20
    pins={str(x.relative_to(R)):sha(x) for x in sources}
    pins[str((N/'AndroidManifest.xml').relative_to(R))]=sha(N/'AndroidManifest.xml')
    pins[str(expected.relative_to(R))]=sha(expected)
    logs=[];success=False;target=N/'dist'/f'aeris-m1-runtime-development-{args.attempt}.apk'
    assert not target.exists();assert not (E/f'build-{args.attempt}.json').exists();W.mkdir()
    env={**os.environ,'JAVA_HOME':str(J)}
    def run(argv):
        proc=subprocess.run([str(x)for x in argv],cwd=R,env=env,text=True,capture_output=True)
        logs.append({'argv':[str(x)for x in argv],'exit':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
        if proc.returncode:raise RuntimeError('BUILD_STEP_FAILED:'+str(argv[0]))
        return proc.stdout+proc.stderr
    try:
        classes=W/'classes';classes.mkdir()
        run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*sources])
        assets=W/'assets';assets.mkdir();shutil.copyfile(expected,assets/'expected-provider.json')
        run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-A',assets,'-o',W/'unsigned.apk'])
        dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*sorted(classes.rglob('*.class'))])
        with zipfile.ZipFile(W/'unsigned.apk','a')as z:z.write(dex/'classes.dex','classes.dex')
        run([B/'zipalign','-f','4',W/'unsigned.apk',W/'aligned.apk'])
        target.parent.mkdir(exist_ok=True);K=R/'.local/native31'
        run([B/'apksigner','sign','--ks',K/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(K/'password'),'--out',target,W/'aligned.apk'])
        signature=run([B/'apksigner','verify','--verbose','--print-certs',target])
        assert '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800' in signature
        with zipfile.ZipFile(W/'aligned.apk')as before,zipfile.ZipFile(target)as after:
            assert all(before.read(n)==after.read(n)for n in before.namelist())
        permissions=run([B/'aapt2','dump','permissions',target]);assert 'android.permission.INTERNET' in permissions
        assert pins=={key:sha(R/key)for key in pins}
        receipt={'status':'DEVELOPMENT_APK_BUILT_NOT_RUNTIME_ACCEPTED','atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'apk':str(target.relative_to(R)),'bytes':target.stat().st_size,'sha256':sha(target),'sourcePins':pins,
                 'sourceSHA256':hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest(),'expectedProvider':data,
                 'signature':signature,'permissions':permissions,'toolPins':{str(x):sha(x)for x in [J/'bin/javac',B/'aapt2',B/'d8',B/'zipalign',B/'apksigner',A]},
                 'capabilityScope':'NO_MEDIA_M1_RUNTIME_NOT_FINAL_COCKPIT_NOT_CONTINUOUS_MANUAL_QUALIFIED',
                 'productionSigning':False,'launchInstall':False}
        (E/f'build-{args.attempt}.json').open('x').write(json.dumps(receipt,indent=2)+'\n');success=True
        print(json.dumps({'apk':receipt['apk'],'bytes':receipt['bytes'],'sha256':receipt['sha256'],'status':receipt['status']}))
    finally:
        beforeCleanup={'files':len([x for x in W.rglob('*')if x.is_file()]),'bytes':sum(x.stat().st_size for x in W.rglob('*')if x.is_file())}
        assert beforeCleanup['bytes']<32*2**20
        shutil.rmtree(W)
        (E/f'build-log-{args.attempt}.json').open('x').write(json.dumps({'success':success,'logs':logs,'scratchRemoved':str(W.relative_to(R)),'beforeCleanup':beforeCleanup,'existsAfter':W.exists()},indent=2)+'\n')


if __name__=='__main__':main()
