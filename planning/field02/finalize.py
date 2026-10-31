"""Read-only acceptance checks plus cleanup of explicitly owned generated scratch.

Never starts Android/AP, changes protected data, or upgrades a failed AC.
"""
from pathlib import Path
import datetime, hashlib, json, os, shutil, socket, subprocess

R = Path(__file__).resolve().parents[2]
E = R / 'evidence/field02'
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()
def read(n): return json.loads((E / n).read_text())
def put(n, d):
    with (E / n).open('x') as f:
        json.dump(d, f, indent=2, ensure_ascii=False); f.flush(); os.fsync(f.fileno())
def differences(files):
    return [{'path': p, 'expected': expected, 'actual': sha(R/p) if (R/p).is_file() else None}
            for p, expected in files.items() if not (R/p).is_file() or sha(R/p) != expected]
def size(p):
    return p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob('*') if f.is_file())

protected = read('preservation-before01.json')['files']
native = read('android-source-freeze02.json')['files']
host = read('host-source-check05.json')['sources']
drift = {'protected': differences(protected), 'native': differences(native), 'host': differences(host)}
assert not any(drift.values()), drift
closures = {}
for p in sorted(E.glob('host-app[0-9][0-9]/app-launch.json')):
    c = p.parent/'app-closure.json'
    assert c.is_file(), str(c)
    closures[str(c.relative_to(R))] = json.loads(c.read_text())
for n in ['01', '02']:
    c = read('android-closure'+n+'.json')
    assert c['exit'] == 0 and c['error'] is None and c['minFreeBytes'] >= 20*2**30
    closures['android-'+n] = c
listeners = {}
for port in [8872, 8873, 5972, 5582, 5583]:
    with socket.socket() as s: listeners[str(port)] = s.connect_ex(('127.0.0.1',port)) == 0
assert not any(listeners.values()), listeners
docker = subprocess.run(['docker','ps','-a','--filter','name=^/aeris-field02$','--format','{{.Names}} {{.Status}}'],capture_output=True,text=True,check=True)
assert not docker.stdout.strip(), docker.stdout
adb = subprocess.run(['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','devices','-l'],capture_output=True,text=True,check=True)
assert 'emulator-5582' not in adb.stdout
apk=R/'native/field02/dist/aeris-field02-development02.apk'
assert sha(apk)=='df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d'
assert read('qa-final-independent01.json')['overallRecommendation']=='NOT_READY'
assert read('qa-android-final-runtime01.json')['nativePackageInCrashBuffer'] is False
assert size(E) < 512*2**20

cleanup = []
for name in ['.local/field02/swift-cache','.local/field02/qa-ocr','pilot/field02/.stage']:
    p=R/name
    assert not p.is_symlink()
    if p.exists():
        n=size(p)
        if p.is_dir(): shutil.rmtree(p)
        else: p.unlink()
        cleanup.append({'path':name,'bytesRemoved':n,'kind':'OWNED_REGENERABLE_SCRATCH'})
assert shutil.disk_usage(R).free >= 20*2**30
assert not differences(protected) and not differences(native) and not differences(host)
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'overallStatus':'NOT_READY','fullMilestoneAccepted':False,
    'protectedBaseline':{'files':len(protected),'differences':[],'scope':'DECLARED_EXISTING_BASELINE_ONLY_NOT_WHOLE_REPOSITORY','preexistingGitDeletions':95},
    'source':{'nativeFiles':len(native),'nativeSourceId':read('android-source-freeze02.json')['sourceId'],'hostFiles':len(host),'differences':drift,'builderSyntaxCount':50,'builderFlightPinCount':57},
    'apk':{'path':str(apk.relative_to(R)),'bytes':apk.stat().st_size,'sha256':sha(apk),'signing':'DEVELOPMENT_ONLY_NOT_PRODUCTION'},
    'processClosure':closures,'ownedPortsListening':listeners,'ownedDockerContainer':docker.stdout.strip(),
    'adbDevices':adb.stdout,'cleanup':cleanup,'dockerImagePruneReclaimedBytes':0,
    'retainedOwnAvd':{'path':'.local/field02/avd','bytes':size(R/'.local/field02/avd'),'reason':'Reusable own emulator userdata and restart evidence; no automatic evidence deletion'},
    'evidenceBytesBeforeReport':size(E),'evidenceBudgetBytes':512*2**20,'freeBytes':shutil.disk_usage(R).free,
    'remainingBlockingGaps':['VIDEO_COLD_START_1500MS','VIDEO_FOREGROUND_FPS_BELOW24','DAY_VIDEO_ERROR_AND_AGE_CONTRAST','ACTIVE_PAYLOAD_LEASE_REVOCATION_AT_REBOOT_NOT_OBSERVED'],
    'noClaims':['No physical Hera/Xiaomi/camera qualification','No production or ENDURE acceptance','No standalone native-direct flight control','No more AP starts or new software signature']}
put('final-verification01.json',report)
print(json.dumps({'status':report['overallStatus'],'protectedFiles':len(protected),'drift':0,'cleanup':cleanup,'freeGiB':report['freeBytes']/2**30,'evidenceMiB':report['evidenceBytesBeforeReport']/2**20},ensure_ascii=False))
