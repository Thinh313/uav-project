"""Workspace-bound macOS Beta companion. No download, auto flight or evidence cleanup."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, re, shutil, signal, socket, subprocess, sys, time, uuid

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/missionbeta01'
CONTROL = ROOT / '.local/missionbeta01'
LOCK = CONTROL / 'active'
POLICY = json.loads((ROOT / 'pilot/missionbeta01/resource-policy.json').read_text())
ADB = Path('/opt/homebrew/share/android-commandlinetools/platform-tools/adb')
SDK = ROOT / '.local/native86-android/sdk'
ANDROID = ROOT / '.local/field02'
APK = ROOT / 'native/missionbeta01/dist/aeris-missionbeta01-development01.apk'
SERIAL = 'emulator-5582'
PORTS = (8895, 8896, 5582, 5583, 5984)
IMAGE = 'sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def put(p, value):
    with Path(p).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n'); f.flush(); os.fsync(f.fileno())


def command(args, timeout=15):
    p = subprocess.run(list(map(str, args)), cwd=ROOT, capture_output=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError('COMMAND_FAILED: ' + str(args[0]) + ': ' + p.stderr.decode(errors='replace')[:500])
    return p.stdout.decode(errors='replace').strip()


def process_stamp(pid):
    p = subprocess.run(['ps', '-p', str(pid), '-o', 'lstart=', '-o', 'args='], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def child_owned(x):
    current=process_stamp(x['process'].pid)
    return current is not None and x['stamp'] is not None and current.split()[:5]==x['stamp'].split()[:5] and os.getpgid(x['process'].pid)==x['process'].pid


def owner():
    p = LOCK / 'owner.json'
    if not p.exists():
        return None
    q = json.loads(p.read_text())
    q['liveIdentityMatches'] = process_stamp(q['pid']) == q['processStamp']
    return q


def check_ports(ports):
    for port in ports:
        with socket.socket() as s:
            s.bind(('127.0.0.1', port))


def verify_pins():
    data=json.loads((EVIDENCE/'source-pins07.json').read_text())
    for n,h in data['files'].items():
        if sha(ROOT/n)!=h:raise RuntimeError('PIN_DRIFT: '+n)
    return len(data['files'])


def doctor(mode='mock', emulator=False):
    free = shutil.disk_usage(ROOT).free
    result = {'format': 'aeris-beta05-doctor', 'freeBytes': free, 'policy': POLICY,
              'mode': mode, 'emulator': emulator, 'downloads': False,
              'workspaceBound': True, 'production': False, 'checks': []}
    def check(name, fn):
        try:
            value = fn(); result['checks'].append({'name': name, 'status': 'PASS', 'value': value})
        except Exception as e:
            result['checks'].append({'name': name, 'status': 'FAIL', 'error': str(e)[:500]})
    check('admission20GiB', lambda: free >= POLICY['admissionBytes'] or (_ for _ in ()).throw(RuntimeError('BELOW20GiB')))
    check('node', lambda: command(['node', '--version']))
    check('ui_projection_inverse', lambda: command(['node','--input-type=module','-e',"import{uiProjection}from'./pilot/missionbeta01/ui-projection.mjs';console.log(uiProjection().inverseExact)"]))
    check('no_active_owner', lambda: not LOCK.exists() or (_ for _ in ()).throw(RuntimeError('OWNER_LOCK_EXISTS; use status, no automatic stale-lock removal')))
    check('owned_ports_available', lambda: check_ports(PORTS if emulator else (8895,8896,5984)))
    def pins():
        data = json.loads((EVIDENCE / 'source-pins07.json').read_text())
        for n, h in data['files'].items():
            if sha(ROOT / n) != h: raise RuntimeError('PIN_DRIFT: ' + n)
        return len(data['files'])
    check('source_and_dependency_pins', verify_pins)
    if emulator:
        check('cached_emulator', lambda: (SDK/'emulator/emulator').is_file() or (_ for _ in ()).throw(RuntimeError('CACHED_EMULATOR_MISSING')))
        check('cached_AVD', lambda: (ANDROID/'avd/aeris-field02.ini').is_file() or (_ for _ in ()).throw(RuntimeError('CACHED_AVD_MISSING')))
        check('development_APK', lambda: sha(APK))
        check('ADB', lambda: command([ADB,'version']))
    if mode == 'sitl':
        check('cached_ARM_AP', lambda: sha(ROOT/'.local/beta06g3/arducopter') == '1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41' or (_ for _ in ()).throw(RuntimeError('AP_SHA')))
        check('cached_ARM_image', lambda: command(['/usr/local/bin/docker','image','inspect',IMAGE,'--format','{{.Id}}']) == IMAGE or (_ for _ in ()).throw(RuntimeError('IMAGE_ID')))
    result['status'] = 'PASS' if all(x['status']=='PASS' for x in result['checks']) else 'FAIL'
    return result


def start(args):
    result = doctor(args.mode, args.emulator)
    if result['status'] != 'PASS':
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 2
    CONTROL.mkdir(parents=True, exist_ok=True)
    LOCK.mkdir()  # Exclusive ownership before any process or admission interval.
    tag = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    run = EVIDENCE/'launches'/tag
    run.mkdir(parents=True)
    ident = {'pid':os.getpid(),'processStamp':process_stamp(os.getpid()),'id':tag,'run':str(run),'mode':args.mode}
    put(run/'owner.json', ident); put(LOCK/'owner.json', ident); put(run/'doctor.json', result)
    children=[]; handles=[]; stopped=False; error=None; started=time.monotonic()
    def stop(*_):
        nonlocal stopped
        stopped=True
    for sig in (signal.SIGINT,signal.SIGTERM): signal.signal(sig,stop)
    try:
        samples=[]
        for i in range(31):
            if stopped: raise RuntimeError('OPERATOR_STOP_BEFORE_LAUNCH')
            free=shutil.disk_usage(ROOT).free; samples.append({'mono':time.monotonic(),'freeBytes':free})
            if free<POLICY['admissionBytes']: raise RuntimeError('ADMISSION20')
            if max(x['freeBytes'] for x in samples)-free>POLICY['maxDeclineBytes']: raise RuntimeError('DISK_TREND')
            if i<30: time.sleep(1)
        put(run/'admission.json',{'samples':samples,'policy':POLICY})
        verify_pins() # Recheck after admission, before process creation.
        with (run/'source-pins.json').open('xb') as f:
            f.write((EVIDENCE/'source-pins07.json').read_bytes());f.flush();os.fsync(f.fileno())
        check_ports(PORTS if args.emulator else (8895,8896,5984))
        host=['node','pilot/missionbeta01/server.mjs',str(run/'host')]
        if args.mode=='sitl': host.append('--sitl')
        commands=[host]
        if args.emulator:
            commands.append([str(SDK/'emulator/emulator'),'-avd','aeris-field02','-port','5582','-no-window','-accel','on','-gpu','host','-no-snapshot','-no-boot-anim','-no-audio','-camera-back','none','-camera-front','none','-memory','2048','-cores','4','-no-metrics'])
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','ANDROID_AVD_HOME':str(ANDROID/'avd'),'ANDROID_USER_HOME':str(ANDROID/'android-user'),'ANDROID_SDK_ROOT':str(SDK),'ANDROID_HOME':str(SDK)}
        for i,argv in enumerate(commands):
            f=(run/('child-'+str(i)+'.txt')).open('xb'); handles.append(f)
            p=subprocess.Popen(argv,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            children.append({'process':p,'argv':argv,'stamp':process_stamp(p.pid)})
        put(run/'launch.json',{'owner':ident,'children':[{'pid':x['process'].pid,'argv':x['argv'],'processStamp':x['stamp']} for x in children], 'ports':PORTS,'policy':POLICY,'deadlineMono':started+2700})
        print('AERIS Beta05 started. Cockpit http://127.0.0.1:8896/ | Video source http://127.0.0.1:8895/publisher',flush=True)
        print('No automatic flight. Start the video source, then use Android.command for the owned emulator. Ctrl+C or Stop Beta.command closes only this runtime.',flush=True)
        trail=[]; last=-1; next_scan=0
        with (run/'guard.jsonl').open('x') as log:
            while not stopped:
                t=time.monotonic(); free=shutil.disk_usage(ROOT).free; trail.append((t,free));trail=[x for x in trail if t-x[0]<=2]
                rate=max(0,(trail[0][1]-free)/max(.001,t-trail[0][0]));forecast=free-rate*15
                if min(free,forecast)<POLICY['hardFloorBytes']+POLICY['writeReserveBytes']:raise RuntimeError('FLOOR10_OR_FORECAST_WITH_RESERVE')
                if t>started+2700:raise RuntimeError('BOUNDED_45MIN_SESSION')
                if any(x['process'].poll() is not None for x in children):raise RuntimeError('OWNED_CHILD_EXIT')
                if any(f.tell()>4*2**20 for f in handles):raise RuntimeError('CONSOLE4MIB')
                if t>=next_scan:
                    files=[p for p in EVIDENCE.rglob('*') if p.is_file()];next_scan=t+2
                    if len(files)>12000 or sum(p.stat().st_size for p in files)>=POLICY['evidenceBudgetBytes']:raise RuntimeError('TASK2GIB')
                if t-last>=1:
                    log.write(json.dumps({'mono':t,'freeBytes':free,'forecastBytes':forecast})+'\n');log.flush();last=t
                time.sleep(.25)
    except BaseException as e:
        error=str(e); print('AERIS stopped: '+error,flush=True)
    finally:
        closure=[]
        for x in children:
            p=x['process']
            if p.poll() is None and child_owned(x):p.send_signal(signal.SIGTERM)
        for x in children:
            p=x['process']
            try:p.wait(timeout=25)
            except subprocess.TimeoutExpired:
                # No broad kill or PID-only escalation after an unconfirmed closure.
                error=error or 'CHILD_CLOSURE_UNKNOWN'
            closure.append({'pid':p.pid,'exit':p.returncode,'argv':x['argv']})
        for f in handles:f.flush();os.fsync(f.fileno());f.close()
        put(run/'closure.json',{'error':error,'children':closure,'freeBytes':shutil.disk_usage(ROOT).free,'evidenceRetained':True,'authorityRestored':False})
        if all(x['exit'] is not None for x in closure) and json.loads((LOCK/'owner.json').read_text())==ident:
            (LOCK/'owner.json').unlink();LOCK.rmdir() # Runtime ownership token, duplicate receipt retained in run/owner.json.
    return 1 if error else 0


def android():
    q=owner()
    if not q or not q['liveIdentityMatches']:raise RuntimeError('OWNED_COMPANION_NOT_RUNNING')
    launch=json.loads((Path(q['run'])/'launch.json').read_text())
    if not any('emulator/emulator' in x['argv'][0] and (process_stamp(x['pid']) or '').split()[:5]==x['processStamp'].split()[:5] for x in launch['children']):raise RuntimeError('NO_OWNED_EMULATOR; physical devices are not admitted')
    log=[]; deadline=time.monotonic()+60
    def adb(*a):
        v=command([ADB,'-s',SERIAL,*a],timeout=25);log.append({'args':a,'result':v});return v
    while adb('shell','getprop','sys.boot_completed')!='1':
        if time.monotonic()>deadline:raise RuntimeError('OWNED_EMULATOR_BOOT_DEADLINE')
        time.sleep(1)
    for port in (8895,8896):adb('reverse','tcp:'+str(port),'tcp:'+str(port))
    expected=json.loads((EVIDENCE/'source-pins07.json').read_text())['files'][str(APK.relative_to(ROOT))]
    if sha(APK)!=expected:raise RuntimeError('APK_DRIFT_BEFORE_INSTALL')
    adb('install','-r',str(APK));adb('shell','am','start','-W','-n','vn.rtr.aeris.missionbeta01/.ShellActivity')
    put(Path(q['run'])/('android-'+uuid.uuid4().hex[:8]+'.json'),{'steps':log,'apkSha256':sha(APK),'serial':SERIAL,'physicalDevice':False})
    print('Owned Android emulator ready. No authority or flight commands were restored.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['doctor','start','status','stop','android']);p.add_argument('--mode',choices=['mock','sitl'],default='mock');p.add_argument('--emulator',action='store_true');a=p.parse_args()
    if a.action=='doctor':
        r=doctor(a.mode,a.emulator);print(json.dumps(r,ensure_ascii=False,indent=2));return 0 if r['status']=='PASS' else 2
    if a.action=='start':return start(a)
    if a.action=='android':android();return 0
    q=owner();print(json.dumps(q or {'state':'STOPPED','automaticResume':False},ensure_ascii=False,indent=2))
    if a.action=='stop' and q:
        if not q['liveIdentityMatches']:raise RuntimeError('STALE_OWNER_REFUSED; do not delete lock automatically')
        os.kill(q['pid'],signal.SIGTERM)
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print('AERIS: '+str(e),file=sys.stderr);sys.exit(2)
