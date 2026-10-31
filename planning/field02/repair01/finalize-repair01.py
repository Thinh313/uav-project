"""Close this bounded repair without relabeling failed or unrun acceptance."""
from pathlib import Path
import datetime, hashlib, json, shutil, socket, subprocess

R = Path(__file__).resolve().parents[3]
E = R / 'evidence/field02/repair01'
def read(p): return json.loads((R / p).read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def size(p): return sum(f.stat().st_size for f in p.rglob('*') if f.is_file()) if p.is_dir() else p.stat().st_size
def drift(files): return [{'path':p,'expected':v,'actual':sha(R/p) if (R/p).is_file() else None} for p,v in files.items() if not (R/p).is_file() or sha(R/p)!=v]
assert shutil.disk_usage(R).free >= 20*2**30, 'STOP_NO_WRITES_UNDER_FLOOR'
protected = read('evidence/field02/preservation-before01.json')
native = read('evidence/field02/android-source-freeze02.json')
old = read('evidence/field02/repair01/preservation-before.json')
checks = {'protected':drift(protected['files']), 'native':drift(native['files']), 'oldEvidence':drift(old['oldEvidenceFiles'])}
media = read('evidence/field02/repair01/media-source-cadence-source-freeze07.json')
checks['media'] = drift({x['path']:x['sha256'] for x in media['checks']})
pins = read('evidence/field02/repair01/flight-source-pins.json')
checks['flight'] = drift(pins['files'])
ports = {}
for port in [8872,8873,5972,5582,5583]:
    with socket.socket() as s: ports[str(port)] = s.connect_ex(('127.0.0.1',port))==0
assert not any(ports.values()), ports
docker = subprocess.run(['docker','ps','-a','--filter','name=^/aeris-field02$','--format','{{.Names}} {{.Status}}'],capture_output=True,text=True,check=True)
assert not docker.stdout.strip(), docker.stdout
adb = subprocess.run(['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','devices','-l'],capture_output=True,text=True,check=True)
assert 'emulator-5582' not in adb.stdout
cleanup=[]
for name in ['pilot/field02/.stage','.local/field02/qa-ocr']:
    p=R/name
    assert not p.is_symlink()
    if p.exists():
        n=size(p)
        if p.is_dir(): shutil.rmtree(p)
        else: p.unlink()
        cleanup.append({'path':name,'bytesRemoved':n,'kind':'OWNED_REGENERABLE_SCRATCH'})
sources={str(p.relative_to(R)):sha(p) for p in (R/'pilot/field02').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
closures={str(p.relative_to(R)):json.loads(p.read_text()) for p in E.glob('host-app*/app-closure.json')}
for p in E.glob('android-closure*.json'): closures[str(p.relative_to(R))]=json.loads(p.read_text())
apk=R/'native/field02/dist/aeris-field02-development02.apk'
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'overallStatus':'NOT_READY','fullMilestoneAccepted':False,
     'protectedBaselineFiles':len(protected['files']),'nativeFiles':len(native['files']),'oldEvidenceFiles':len(old['oldEvidenceFiles']),
     'differences':checks,'preexistingGitDeletedCount':protected['preexistingGitDeletedCount'],'scopeNotWholeRepository':True,
     'finalIsolatedSourceFiles':sources,'apk':{'path':str(apk.relative_to(R)),'sha256':sha(apk),'bytes':size(apk),'newBuildOrSignature':False},
     'ownedPortsListening':ports,'ownedContainer':docker.stdout.strip(),'adbDevices':adb.stdout,'processClosures':closures,
     'cleanup':cleanup,'earlyCleanupReceipt':'evidence/field02/repair01/cleanup-cache-early.json','dockerImagePruneReclaimedBytes':0,
     'retainedAvdBytes':size(R/'.local/field02/avd'),'repairEvidenceBytes':size(E),'repairEvidenceBudgetBytes':192*2**20,
     'freeBytes':shutil.disk_usage(R).free,'continuous20GiBFloorMaintained':False,
     'resourceIncident':'evidence/field02/repair01/resource-incident01.json',
     'remainingBlockingGaps':['VIDEO_FINAL_FPS_BELOW24','VIDEO_FINAL_P95_ABOVE300MS','TRUE_COLD_START_FINAL_SOURCE_NOT_RETESTED','ACTUAL_AP_ACTIVE_LEASE_REBOOT_NOT_CHECKED','FINAL_ANDROID_SITL_AND_RESTART_SAF_REGRESSION_NOT_RUN'],
     'limits':['20GiB floor breach observed despite guard; no resource PASS','Last UI connect was mock, not SITL','Prior successful Android/SITL/SAF evidence remains historical, not regression proof for current source','No hardware, production, ENDURE or standalone native-direct acceptance']}
assert not any(checks.values()), checks
assert out['repairEvidenceBytes'] < out['repairEvidenceBudgetBytes']
with (E/'final-verification.json').open('x') as f: json.dump(out,f,indent=2,ensure_ascii=False)
print(json.dumps({'status':out['overallStatus'],'protected':len(protected['files']),'oldEvidence':len(old['oldEvidenceFiles']),'drift':checks,'cleanup':cleanup,'freeGiB':out['freeBytes']/2**30}))
