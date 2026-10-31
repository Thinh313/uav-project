"""Cached engineering build for the stable mission runtime; never installs or launches."""
from pathlib import Path
import argparse, datetime, gzip, hashlib, json, os, shutil, subprocess, tarfile, zipfile

R = Path(__file__).resolve().parents[2]
N = R / 'native/mission-runtime'
E = R / 'evidence/runtime-unification01'
W = R / 'native/betaintegrated01/.build/native-development'
J = Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home')
B = Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0')
A = Path('/opt/homebrew/share/android-commandlinetools/platforms/android-37.0/android.jar')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def allocated_artifacts():
    """Every candidate object/original and directory, deduplicated only by actual inode."""
    root=E/'candidates';seen=set();total=0
    if not root.exists():return 0
    for path in [root,*root.rglob('*')]:
        st=path.lstat();assert not path.is_symlink(),'CANDIDATE_SYMLINK'
        key=(st.st_dev,st.st_ino)
        if key in seen:continue
        seen.add(key);total+=st.st_blocks*512
    return total

def inputs():
    return sorted([*N.joinpath('src').rglob('*.java'), N/'AndroidManifest.xml', Path(__file__).resolve(),
                   *[p for root in ('assets', 'resources', 'protocols') for p in (N/root).rglob('*') if p.is_file()]])

def main(attempt):
    assert 1 <= attempt <= 3
    entry = shutil.disk_usage(R).free
    assert entry >= 10*2**30+256*2**20+32*2**20 and not W.exists()
    freeze = json.loads((E/f'native/core-freeze-{attempt:02d}.json').read_text())
    assert all(sha(R/p) == h for p,h in freeze['sourceSHA256'].items())
    files = inputs()
    assert all(str(p.relative_to(R)).startswith('native/mission-runtime/') for p in files)
    pins = {str(p.relative_to(R)):sha(p) for p in files}
    assert all(freeze['sourceSHA256'].get(p) == h for p,h in pins.items())
    source = hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest()
    # Before any tool, reserve a bounded compressed-input worst case plus the
    # enforced APK output ceiling; oversized output never enters candidates.
    archive_bound=sum(p.stat().st_size+2048 for p in files)+131072
    apk_bound=1048576
    artifact_before=allocated_artifacts()
    assert artifact_before+archive_bound+apk_bound+32768 <= 4*2**20,'GLOBAL_ARTIFACT_PREFLIGHT'
    logpath = E/f'native/build-log-{attempt:02d}.json'
    receiptpath = E/f'native/build-{attempt:02d}.json'
    assert not logpath.exists() and not receiptpath.exists()
    logs=[]; success=False; failure=None; scratch=False
    def run(argv):
        assert shutil.disk_usage(R).free >= 10*2**30+256*2**20
        try:
            p=subprocess.run(list(map(str,argv)),cwd=R,env={**os.environ,'JAVA_HOME':str(J)},capture_output=True,text=True,timeout=90)
        except subprocess.TimeoutExpired as ex:
            logs.append({'argv':list(map(str,argv)),'exit':None,'stdout':str(ex.stdout),'stderr':str(ex.stderr),'timeout':90});raise
        logs.append({'argv':list(map(str,argv)),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        assert p.returncode == 0,logs[-1]
        return p.stdout+p.stderr
    try:
        W.mkdir();scratch=True
        candidate=E/'candidates';candidate.mkdir(exist_ok=True)
        archive=candidate/(source+'-inputs.tar.gz');assert not archive.exists()
        with archive.open('xb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as compressed:
                with tarfile.open(fileobj=compressed,mode='w') as tar:
                    for p in files:tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
        assert archive.stat().st_size<=archive_bound
        assert allocated_artifacts()+apk_bound+32768<=4*2**20,'GLOBAL_ARTIFACT_AFTER_ARCHIVE'
        classes=W/'classes';classes.mkdir()
        sources=sorted((N/'src').rglob('*.java'))
        run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*sources])
        assets=W/'assets';assets.mkdir();shutil.copytree(N/'assets',assets/'cockpit')
        shutil.copyfile(N/'resources/expected-providers.json',assets/'expected-providers.json')
        for case in ('nominal','loss'):
            shutil.copyfile(N/f'resources/profiles/{case}/typed-profile01.json',assets/f'{case}-typed-profile.json')
        protocols={}
        for version,name in [('release12','release'),('ioadmit13','ioadmit'),('terminal14','terminal'),('mission-bootstrap-v1','mission-bootstrap')]:
            path=N/f'protocols/{version}.json';shutil.copyfile(path,assets/f'{name}-protocol.json');protocols[name]=sha(path)
        identity={'format':'aeris-mission-runtime-source-identity','version':1,'sourceSHA256':source,'package':'vn.rtr.aeris.mission',
                  'OwnerRevision':'EXACT_IOADMIT13_OWNER_INPUT_RELEASE_RX_AND_GUARDS','CheckpointRevision':'EXACT_TERMINAL14_WITH_PACKAGE_ONLY_CHANGE',
                  'releaseProtocolSHA256':protocols['release'],'ioadmitProtocolSHA256':protocols['ioadmit'],'terminalProtocolSHA256':protocols['terminal'],
                  'missionProtocolSHA256':protocols['mission-bootstrap'],'UIRevision':'UI05_VISUALS_EXACT_WITH_VERSIONED_WORKSPACE_RENDER_ACK','production':False}
        (assets/'source-identity.json').write_text(json.dumps(identity)+'\n')
        run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-A',assets,'-o',W/'unsigned.apk'])
        dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*sorted(classes.rglob('*.class'))])
        with zipfile.ZipFile(W/'unsigned.apk','a') as z:z.write(dex/'classes.dex','classes.dex')
        with zipfile.ZipFile(W/'unsigned.apk') as z:
            d=z.read('classes.dex');assert b'Lvn/rtr/aeris/mission/CockpitActivity;' in d and b'Lvn/rtr/aeris/control01/ReleaseControl;' in d
            assert all(s not in d for s in (b'DirectTransport95',b'UnifiedTransport98',b'Lvn/rtr/aeris/cockpitio14/',b'Lvn/rtr/aeris/cockpitio13/'))
        run([B/'zipalign','-f','4',W/'unsigned.apk',W/'aligned.apk'])
        keys=R/'.local/native31';signed=W/'signed.apk'
        run([B/'apksigner','sign','--ks',keys/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(keys/'password'),'--out',signed,W/'aligned.apk'])
        signature=run([B/'apksigner','verify','--verbose','--print-certs',signed])
        cert='3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800';assert cert in signature
        assert signed.stat().st_size<=apk_bound,'APK_OUTPUT_CEILING'
        assert allocated_artifacts()+((signed.stat().st_size+4095)//4096)*4096+32768<=4*2**20,'GLOBAL_ARTIFACT_BEFORE_PUBLICATION'
        target=candidate/(sha(signed)+'.apk');assert not target.exists();shutil.copyfile(signed,target)
        assert all(sha(R/p)==h for p,h in pins.items())
        artifactbytes=allocated_artifacts();assert artifactbytes<4*2**20
        receipt={'format':'aeris-development-build','version':1,'attempt':attempt,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'status':'MISSION_DEVELOPMENT_BUILT_NOT_RUNTIME_ACCEPTED','apk':str(target.relative_to(R)),'sha256':sha(target),'bytes':target.stat().st_size,
                 'sourcePins':pins,'sourceSHA256':source,'sourceCount':len(pins),'signature':signature,'certificateSHA256':cert,'protocolSHA256':protocols,
                 'releaseProtocolSHA256':protocols['release'],'ioadmitProtocolSHA256':protocols['ioadmit'],'terminalProtocolSHA256':protocols['terminal'],
                 'missionProtocolSHA256':protocols['mission-bootstrap'],'inputArchive':str(archive.relative_to(R)),'inputArchiveSHA256':sha(archive),
                 'buildScriptSHA256':sha(__file__),'productionSigning':False,'installOrRuntimeLaunch':False,'entryFreeBytes':entry,
                 'artifactBytesAcrossAllAttempts':artifactbytes,'toolPins':{str(p):sha(p) for p in [J/'bin/javac',B/'aapt2',B/'d8',B/'apksigner',A]}}
        receipt['globalArtifactAdmission']={'allocatedBefore':artifact_before,'archiveUpperBound':archive_bound,'APKCeiling':apk_bound,
                                          'directoryReserve':32768,'method':'recursive st_blocks including originals, objects and directories; actual inode dedup only'}
        receiptpath.open('x').write(json.dumps(receipt,indent=2)+'\n');success=True
        print(json.dumps({k:receipt[k] for k in ('status','apk','sha256','sourceSHA256','bytes','sourceCount')}))
    except BaseException as exc:
        failure=type(exc).__name__+':'+str(exc);raise
    finally:
        size=sum(p.stat().st_size for p in W.rglob('*') if p.is_file());count=sum(p.is_file() for p in W.rglob('*'))
        if scratch and W.exists():shutil.rmtree(W)
        logpath.open('x').write(json.dumps({'success':success,'failure':failure,'logs':logs,'scratchRemoved':str(W.relative_to(R)),
                                          'scratchBytes':size,'scratchFiles':count,'existsAfter':W.exists(),'within32MiB':size<32*2**20},indent=2)+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);main(ap.parse_args().attempt)
