"""Small isolated development build; no source/candidate/ENDURE or SDK mutation."""
from pathlib import Path
import subprocess, os, json, hashlib, shutil, zipfile, datetime
R=Path(__file__).resolve().parents[2]; N=R/'native/flightops35'; E=R/'evidence/airspace35'
J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home')
S=Path('/opt/homebrew/share/android-commandlinetools'); B=S/'build-tools/36.0.0'; A=S/'platforms/android-37.0/android.jar'
W=N/'.build'; D=N/'dist'; K=R/'.local/native31'; h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
FLOOR=20*1024**3; BUDGET=128*1024**2
def admit():
    free=shutil.disk_usage(R).free
    if free<FLOOR+BUDGET: raise RuntimeError('Storage floor + small build budget unavailable')
    return free
attempt=1
while (E/f'build{attempt:02d}.json').exists() or (E/f'build{attempt:02d}.txt').exists(): attempt+=1
assert not W.exists(), 'Previous owned scratch must be inspected'
for p in (N/'core').glob('*.mjs'):
    assert p.read_bytes()==(R/'pilot/airspace35/core'/p.name).read_bytes(), 'Core clone drift'
initial=admit(); W.mkdir(); D.mkdir(exist_ok=True); logs=[]; sampled=[initial]; scratch_samples=[]
def run(args, allow=False):
    sampled.append(admit()); scratch_samples.append(sum(p.stat().st_blocks*512 for p in W.rglob('*') if p.is_file())); p=subprocess.run([str(x) for x in args],cwd=R,env={**os.environ,'JAVA_HOME':str(J)},text=True,capture_output=True)
    logs.append(p.stdout+p.stderr)
    if p.returncode and not allow: raise RuntimeError(logs[-1])
    return p
try:
    host=W/'host'; host.mkdir(); pure=[p for p in (N/'src').rglob('*.java') if p.name not in ['ShellActivity.java','AndroidProbe.java']]; tests=list((N/'tests').rglob('*.java'))
    run([J/'bin/javac','--release','8','-d',host,*pure,*tests])
    result=run([J/'bin/java','-cp',host,'vn.rtr.aeris.flightops35.DraftStoreTest',W/'test-store'])
    (E/f'java-tests{attempt:02d}.txt').write_text(result.stdout+result.stderr)
    jar=D/'journal-host.jar'; run([J/'bin/jar','cf',jar,'-C',host,'.'])
    assets=W/'assets/editor'; assets.mkdir(parents=True)
    paths=[N/'index.html',N/'shell.css',N/'shell.mjs',N/'capsule.mjs',N/'route.mjs',N/'journey.mjs',N/'editor.mjs',N/'pins.mjs',*list((N/'core').glob('*.mjs')),*list((N/'vendor').glob('*.mjs')),N/'assets/IBMPlexSans.ttf']
    for p in paths:
        dst=assets/p.relative_to(N); dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,dst)
    classes=W/'classes'; classes.mkdir()
    run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*list((N/'src').rglob('*.java')),*tests])
    run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-A',W/'assets','-o',W/'raw.apk'])
    dex=W/'dex'; dex.mkdir(); run([B/'d8','--min-api','26','--lib',A,'--output',dex,*classes.rglob('*.class')])
    with zipfile.ZipFile(W/'raw.apk','a') as z: z.write(dex/'classes.dex','classes.dex')
    run([B/'zipalign','-f','4',W/'raw.apk',W/'aligned.apk'])
    assert (K/'development.p12').is_file() and (K/'password').is_file(), 'Only previously authorized development identity'
    apk=D/f'aeris-native35-development-{attempt:02d}.apk'
    run([B/'apksigner','sign','--ks',K/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(K/'password'),'--out',apk,W/'aligned.apk'])
    signature=run([B/'apksigner','verify','--verbose','--print-certs',apk]).stdout
    assert '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800' in signature, 'Dedicated development identity drift'
    (E/f'signature{attempt:02d}.txt').write_text(signature)
    permissions=run([B/'aapt2','dump','permissions',apk]).stdout
    assert 'uses-permission:' not in permissions
    (E/f'permissions{attempt:02d}.txt').write_text(permissions)
    manifest=run([B/'aapt2','dump','badging',apk]).stdout
    (E/f'badging{attempt:02d}.txt').write_text(manifest)
    with zipfile.ZipFile(apk) as z,zipfile.ZipFile(W/'aligned.apk') as u:
        assert all(z.read(p)==u.read(p) for p in u.namelist())
        assert all(z.read('assets/editor/'+str(p.relative_to(N)))==p.read_bytes() for p in paths)
    report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'attempt':attempt,'status':'BUILT_DEVELOPMENT_HOST_VERIFIED_ANDROID_NOT_CHECKED','apk':str(apk.relative_to(R)),'sha256':h(apk),'bytes':apk.stat().st_size,'hostJournalChecks':result.stdout.count('PASS '),'signaturePayloadExact':True,'zeroPermissions':True,'developmentIdentity':'Existing native31 certificate; no release signature','sources':{str(p.relative_to(R)):h(p) for p in [*paths,*list((N/'src').rglob('*.java')),*tests,N/'AndroidManifest.xml',N/'build.py']},'minimumObservedFreeBytes':min(sampled),'peakSampledScratchAllocatedBytes':max(scratch_samples),'smallBuildBudgetBytes':BUDGET,'androidRuntime':'NOT_CHECKED'}
    (E/f'build{attempt:02d}.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report|{'sources':'see receipt'}))
finally:
    (E/f'build{attempt:02d}.txt').write_text('\n'.join(logs)); shutil.rmtree(W)
    (E/f'build-cleanup{attempt:02d}.json').write_text(json.dumps({'removed':['native/flightops35/.build'],'freeBytes':shutil.disk_usage(R).free,'wholeProjectCopies':0,'SDKDownloads':0})+'\n')
