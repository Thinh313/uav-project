"""Read-only prelaunch diagnosis plus one exclusive JSON in the NEW evidence root.
No ADB, Docker, sockets, runtime, builds, signing, priming or device actions.
"""
from pathlib import Path
from importlib import import_module
import argparse,hashlib,json,os,re,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
E=R/'evidence/betaintegrated01-cockpit05-prelaunch02'
FULL=R/'evidence/betaintegrated01-cockpit05-entry10-flight'
MANIFEST=FULL/'host/input-contract01.json'
MANIFEST_SHA='852d19e22f69f76cc8d16927dc95f56456bed0652b44b5b19f165c075b279d10'
SEAL=R/'evidence/betaintegrated01-cockpit05-entry10/handoff-final.json'
SEAL_SHA='28110b8ecb84dc7c6307d93fb6c053259a7a09aca9a36019accd405c3928ae43'
POLICY=import_module('planning.betaintegrated01.cockpit05-entry10.host.policy02')


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()


def check_sources():
    if digest(MANIFEST)!=MANIFEST_SHA or digest(SEAL)!=SEAL_SHA:raise ValueError('FROZEN_MANIFEST_OR_SEAL_CHANGED')
    manifest=json.loads(MANIFEST.read_bytes());seal=json.loads(SEAL.read_bytes())
    if len(manifest['sourceSHA256'])!=178 or seal['entries']!=385:raise ValueError('EXPECTED178_SOURCE_AND385_HANDOFF')
    bad=[]
    for name,expected in manifest['sourceSHA256'].items():
        path=R/name
        if path.is_symlink()or not path.is_file()or digest(path)!=expected:bad.append({'path':name,'scope':'178SOURCE'})
    for name,expected in seal['inventory'].items():
        path=R/name
        if path.is_symlink()or not path.is_file()or path.stat().st_size!=expected['bytes']or digest(path)!=expected['sha256']:bad.append({'path':name,'scope':'385HANDOFF'})
    return {'status':'PASS'if not bad else'FAIL','sourceFiles':178,'handoffFiles':385,'mismatches':bad[:32],'mismatchCount':len(bad),'manifestSHA256':MANIFEST_SHA,'handoffSHA256':SEAL_SHA}


def power():
    result=subprocess.run(['pmset','-g','batt'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3)
    if result.returncode or len(result.stdout)>4096:raise ValueError('READONLY_POWER_PROBE_FAILED')
    raw=result.stdout.decode();ac="'AC Power'"in raw;match=re.search(r'(\d+)%',raw);percent=int(match[1])if match else None
    return {'AC':ac,'batteryPercent':percent,'raw':raw,'powerEntrySatisfied':ac or type(percent)is int and percent>=30,'readOnlyCommand':['pmset','-g','batt']}


def inspect():
    free=shutil.disk_usage(R).free;budget=POLICY.task_budget(free);p=power();sources=check_sources();blockers=[]
    if not budget['admitted']:blockers.append('WHOLE_CASE_BUDGET_REQUIRES18.792526841GiB')
    if not p['powerEntrySatisfied']:blockers.append('POWER_REQUIRES_AC_OR_BATTERY30_PERCENT')
    if sources['status']!='PASS':blockers.append('SOURCE_OR_PRIOR_HANDOFF_DRIFT')
    absent={'actualCaseNotCreated':not(FULL/'actual-combined01').exists(),'fullGuardianNotLaunched':not(FULL/'emulator01/launch.json').exists()}
    if not all(absent.values()):blockers.append('PRIOR_ACTUAL_OR_LAUNCH_EXISTS_REVIEW_REQUIRED_NO_RETRY')
    return {'format':'aeris-cockpit05-readonly-prelaunch-doctor','version':1,'hostMonotonicNs':time.monotonic_ns(),'status':'BLOCKED_NO_LAUNCH'if blockers else'ENVIRONMENT_CHECKS_PASS_STILL_REQUIRES_REAL_PRIME_AND_ROOT_UI','actualFreeBytes':free,'actualFreeGiB':free/2**30,'requiredFreeBytes':budget['requiredFreeBytes'],'requiredFreeGiB':budget['requiredFreeBytes']/2**30,'entryGiB':10,'liveFloorAndReserveGiB':10.25,'power':p,'sourceClosure':sources,'absenceChecks':absent,'blockers':blockers,'actualPrimePerformed':False,'actualRuntimeAdmission':False,'ADBOrDockerOrSocketCalls':0,'runtimeLaunches':0,'correctedRunner':'planning/betaintegrated01/cockpit05-prelaunch02/OPERATOR.md'}


def save_new(name,value):
    if type(name)is not str or re.fullmatch(r'[a-z0-9-]+\.json',name)is None:raise ValueError('NEW_DIAGNOSTIC_NAME')
    raw=(json.dumps(value,indent=2)+'\n').encode()
    if len(raw)>65536:raise ValueError('NEW_DIAGNOSTIC64KiB_BOUND')
    E.mkdir(exist_ok=True)
    allocated=sum(p.stat().st_size for p in E.rglob('*')if p.is_file())
    if allocated+len(raw)>128*2**10:raise ValueError('NEW_ARTIFACT128KiB_BOUND')
    with(E/name).open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='doctor01.json');args=parser.parse_args();value=inspect();save_new(args.output,value);print(json.dumps(value,indent=2))
