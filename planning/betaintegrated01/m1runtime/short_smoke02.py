"""One admitted, read-only Android/native + external AP test; no flight grants.

Contractor test fixture. It never implements a MAVLink writer or retries CONNECT.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

R = Path(__file__).resolve().parents[3]
os.chdir(R)
sys.path.insert(0, str(R))
from pilot.betaintegrated01.runtime.capacity import estimate

E = R / 'evidence/betaintegrated01-m1runtime'
O = E / 'actual02'
C = O / 'control'
D = O / 'raw'
A = '/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
P = 'vn.rtr.aeris.beta01runtime'
NAME = 'aeris-beta-m1-short02'
STOP = False


def stop(*_):
    global STOP
    STOP = True


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def put(p, d):
    with Path(p).open('x') as f:
        json.dump(d, f, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def command(args, timeout=15, *, required=True):
    t = time.monotonic()
    try:
        p = subprocess.run(list(map(str, args)), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        def text(value):
            return value.decode(errors='replace') if isinstance(value, bytes) else (value or '')
        p = subprocess.CompletedProcess(args, 124, text(exc.stdout), text(exc.stderr) + '\nCOMMAND_TIMEOUT_NO_RETRY')
    with (C / 'commands.jsonl').open('a') as f:
        f.write(json.dumps({'monotonicNs': time.monotonic_ns(), 'argv': list(map(str, args)), 'exit': p.returncode,
                            'stdout': p.stdout[:65536], 'stderr': p.stderr[:65536], 'elapsedSeconds': time.monotonic()-t}) + '\n')
        f.flush()
        os.fsync(f.fileno())
    if required and p.returncode:
        raise RuntimeError('COMMAND_FAILED:' + repr(args) + ':' + p.stderr[:1024])
    return p


def adb(*args, **kw):
    return command([A, '-s', 'emulator-5582', *args], **kw)


def main():
    O.mkdir(exist_ok=False)
    C.mkdir()
    D.mkdir()
    state_dir = O / 'AP-state'
    state_dir.mkdir()
    source = json.loads((E / 'host02/runtime-manifest02.json').read_text())
    native = json.loads((E / 'native/build-05.json').read_text())
    provider = native['expectedProvider']
    assert provider['manualCapability'] is False
    assert provider['capabilityProfile'] == 'NO_MEDIA_M1_RUNTIME'
    for n, item in source['files'].items():
        assert sha(n) == item['sha256'], n
    for n, h in native['sourcePins'].items():
        assert sha(n) == h, n
    assert sha(native['apk']) == native['sha256']
    assert "'AC Power'" in command(['pmset', '-g', 'batt']).stdout
    assert adb('shell', 'getprop', 'sys.boot_completed').stdout.strip() == '1'
    installed = adb('shell', 'pm', 'path', P).stdout.strip()
    assert installed.startswith('package:') and '\n' not in installed, 'INSTALLED_APK_PATH'
    installed_hash = adb('shell', 'sha256sum', installed[len('package:'):]).stdout.split()[0]
    assert installed_hash == native['sha256'], 'INSTALLED_APK_DRIFT'
    put(C / 'installed-apk-observation.json', {'path': installed[len('package:'):], 'sha256': installed_hash})
    assert not (E / 'emulator02/closure.json').exists(), 'EMULATOR_ALREADY_CLOSED'
    available = shutil.disk_usage(R).free
    used = sum(p.stat().st_size for p in E.rglob('*') if p.is_file())
    capacities = [estimate(s, available, evidence_remaining=3*2**30-used) for s in [60, 300, 900, 1800]]
    assert capacities[0]['admittedByArithmetic'], 'SHORT_STORAGE_REFUSED'
    assert capacities[0]['originalCopyExportPeakBytesBound'] + 256*2**20 < available-10*2**30
    put(C / 'duration-admission.json', {'atUTC': datetime.now(timezone.utc).isoformat(), 'profiles': capacities,
                                        'currentEvidenceBytes': used, 'actualSelectedSeconds': 60})
    for port, kind in [(5961, socket.SOCK_STREAM), (9012, socket.SOCK_DGRAM), (9014, socket.SOCK_DGRAM)]:
        with socket.socket(socket.AF_INET, kind) as sock:
            sock.bind(('127.0.0.1', port))
    image = source['containerImageId']
    assert command(['docker', 'image', 'inspect', image, '--format', '{{.Id}}']).stdout.strip() == image
    assert not command(['docker', 'ps', '-aq', '--filter', 'name=^/' + NAME + '$']).stdout.strip(), 'CONTAINER_NAME_ALREADY_EXISTS'
    run = 'm1short02'
    epoch, boot = uuid.uuid4().hex, uuid.uuid4().hex
    profile_path = R / 'runtime/betaintegrated01/dist/run-profile03.json'
    profile = json.loads(profile_path.read_text())
    assert profile['APSHA256'] == provider['binarySHA256']
    assert sha(profile_path) == provider['configSHA256']
    config = {'run': run, 'epoch': epoch, 'boot': boot, 'evidence': str(D), 'maximumSeconds': 60,
              'bind': ['127.0.0.1', 9012], 'load': 'empty', 'wind': 'calm', 'seed': 32,
              'requestedSpeedup': 1, 'capMs': 500, 'APSHA256': profile['APSHA256'],
              'APArtifactName': profile['APArtifactName'], 'parameterSHA256': profile['parameterSHA256'],
              'clockprobeSHA256': profile['clockprobeSHA256']}
    put(D / 'run-config.json', config)
    binding = {k: provider[k] for k in ['version', 'mode', 'profileId', 'binarySHA256', 'modelSHA256', 'configSHA256', 'endpoint', 'firmware']}
    binding.update(rootOwnedContainer=True, targetSystem=42, run=run, epoch=epoch, boot=boot, operator='root-simulator-QA', generation=uuid.uuid4().hex)
    put(C / 'launch-binding.json', binding)
    inputs = {n: item['sha256'] for n, item in source['files'].items()}
    inputs.update(native['sourcePins'])
    inputs[native['apk']] = native['sha256']
    put(C / 'input-pins.json', {'files': inputs, 'controllerSHA256': sha(__file__), 'hostManifestSHA256': sha(E / 'host02/runtime-manifest02.json'),
                               'APK': native['apk'], 'APK_SHA256': native['sha256'], 'AP_SHA256': profile['APSHA256']})
    host_command = [source['hostInterpreter'], '-B', '-m', 'pilot.betaintegrated01.runtime02.backend', '--config', str(D / 'run-config.json')]
    docker_command = ['docker', 'run', '--rm', '--name', NAME, '--label', 'aeris.task=betaintegrated01', '--label', 'aeris.run=' + run,
                      '--cpus', '4', '--memory', '2g', '--pids-limit', '128', '--read-only', '--tmpfs', '/tmp:size=16m',
                      '-p', '127.0.0.1:5961:5760/tcp', '-p', '127.0.0.1:9014:9004/udp',
                      '-v', str(R) + ':/src:ro', '-v', str(R / 'runtime/betaintegrated01/dist') + ':/candidate:ro',
                      '-v', str(D) + ':/evidence:rw', '-v', str(state_dir) + ':/state:rw',
                      '-w', '/src', '-e', 'PYTHONDONTWRITEBYTECODE=1', image,
                      'python3', '-B', '-m', 'pilot.betaintegrated01.runtime.ap_supervisor', '--config', '/evidence/run-config.json']
    put(C / 'launch-plan.json', {'run': run, 'epoch': epoch, 'boot': boot, 'host': host_command, 'APContainer': docker_command,
                               'sourceFilesChecked': len(inputs), 'APKManualCapability': False, 'flightGrantAllowed': False,
                               'plannedAPStarts': 1, 'plannedHostStarts': 1, 'noCommandRetry': True})
    host = container = None
    connected = closed = False
    failure = None
    began = time.monotonic()
    last_free, last_time = available, began
    logs = [(C / 'backend-control-stdout.txt').open('xb'), (C / 'container-control-stdout.txt').open('xb')]
    try:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        host = subprocess.Popen(host_command, cwd=R, env=env, stdin=subprocess.DEVNULL, stdout=logs[0], stderr=subprocess.STDOUT, start_new_session=True)
        # Actual15s priming must finish before the unchanged10s clock bootstrap.
        with (C / 'priming-guard.jsonl').open('x') as priming_log:
            while not (D / 'backend-identity.json').exists():
                now = time.monotonic()
                free_now = shutil.disk_usage(R).free
                forecast = free_now-max(0,(last_free-free_now)/max(.001,now-last_time))*15
                priming_log.write(json.dumps({'monoNs':time.monotonic_ns(),'freeBytes':free_now,'forecastBytes':forecast,'hostExit':host.poll()})+'\n')
                priming_log.flush()
                os.fsync(priming_log.fileno())
                if STOP or host.poll() is not None or forecast<10*2**30+256*2**20 or now-began>25 or (E/'emulator02/closure.json').exists():
                    raise RuntimeError('PRIMING_OR_OWNED_ENVIRONMENT_REFUSED')
                last_free,last_time=free_now,now
                time.sleep(.5)
        identity=json.loads((D/'backend-identity.json').read_text())
        assert identity['guardPrimed'] is True and identity['guardPolicyVersion']==2
        assert identity['guardPriming']['elapsedRealMonotonicNs']>=15_000_000_000
        put(C/'observed-real-guard-prime.json',identity)
        container = subprocess.Popen(docker_command, cwd=R, stdin=subprocess.DEVNULL, stdout=logs[1], stderr=subprocess.STDOUT, start_new_session=True)
        put(C / 'process-launch.json', {'hostPID': host.pid, 'dockerClientPID': container.pid, 'atUTC': datetime.now(timezone.utc).isoformat()})
        native_started = None
        with (C / 'guard.jsonl').open('x') as guard:
            while True:
                now = time.monotonic()
                available = shutil.disk_usage(R).free
                forecast = available - max(0, (last_free-available)/max(.001, now-last_time))*15
                power = subprocess.check_output(['pmset', '-g', 'batt'], text=True)
                row = {'monotonicNs': time.monotonic_ns(), 'freeBytes': available, 'forecastFreeBytes': forecast,
                       'ACObserved': "'AC Power'" in power, 'hostExit': host.poll(), 'containerClientExit': container.poll(), 'nativeCONNECTIntentAttempted': connected}
                guard.write(json.dumps(row)+'\n')
                guard.flush()
                os.fsync(guard.fileno())
                if STOP or forecast < 10*2**30+256*2**20 or not row['ACObserved'] or (E / 'emulator02/closure.json').exists():
                    raise RuntimeError('OWNER_STOP_OR_STORAGE_POWER_EMULATOR_GUARD')
                if now-began > 100:
                    raise RuntimeError('WALL_BUDGET100S')
                if not connected and (D / 'ap-supervisor-launch.json').exists():
                    ap = json.loads((D / 'ap-supervisor-launch.json').read_text())
                    info = json.loads(command(['docker', 'inspect', NAME]).stdout)[0]
                    assert info['Config']['Labels']['aeris.run'] == run and info['State']['Running']
                    executable = command(['docker', 'exec', NAME, 'sha256sum', '/proc/' + str(ap['APPID']) + '/exe']).stdout
                    assert executable.split()[0] == provider['binarySHA256']
                    put(C / 'live-container-observation.json', {'containerId': info['Id'], 'imageId': info['Image'], 'AP': ap,
                        'liveAPExecutableHashOutput': executable, 'trustedLocalProcessObservationNotRemoteAuthentication': True})
                    adb('push', C / 'launch-binding.json', '/data/local/tmp/aeris-m1-binding02.json')
                    adb('shell', 'run-as', P, 'cp', '/data/local/tmp/aeris-m1-binding02.json', 'files/launch-binding.json')
                    observed = adb('shell', 'run-as', P, 'sha256sum', 'files/launch-binding.json').stdout.split()[0]
                    assert observed == sha(C / 'launch-binding.json')
                    connected, native_started = True, time.monotonic()
                    adb('shell', 'am', 'start', '-n', P+'/.RuntimeActivity', '--es', 'm1Action', 'CONNECT', '--es', 'm1ActionId', 'm1short02-connect-01', '--es', 'launchBindingSHA256', observed)
                if connected:
                    q = adb('shell', 'run-as', P, 'cat', 'files/latest-state.json', required=False)
                    if q.returncode == 0:
                        with (C / 'native-live-states.jsonl').open('a') as f:
                            f.write(json.dumps({'observedMonoNs': time.monotonic_ns(), 'state': json.loads(q.stdout)})+'\n')
                    if not closed and (time.monotonic()-native_started >= 35 or host.poll() is not None):
                        adb('shell', 'am', 'start', '-n', P+'/.RuntimeActivity', '--es', 'm1Action', 'CLOSE', '--es', 'm1ActionId', 'm1short02-close-01')
                        closed = True
                if host.poll() is not None:
                    if host.returncode:
                        raise RuntimeError('HOST_FAILED_RETAINED_PREFIX')
                    if container.poll() is not None:
                        break
                if container.poll() is not None and host.poll() is None:
                    raise RuntimeError('AP_CONTAINER_ENDED_BEFORE_HOST')
                last_free, last_time = available, now
                time.sleep(1)
    except Exception as exc:
        failure = type(exc).__name__ + ':' + str(exc)
    finally:
        if connected and not closed:
            adb('shell', 'am', 'start', '-n', P+'/.RuntimeActivity', '--es', 'm1Action', 'CLOSE', '--es', 'm1ActionId', 'm1short02-close-01', required=False)
        if host is not None and host.poll() is None:
            os.killpg(host.pid, signal.SIGTERM)
            try:
                host.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(host.pid, signal.SIGKILL)
                host.wait(timeout=5)
        if container is not None and container.poll() is None:
            command(['docker', 'stop', '--time', '6', NAME], required=False)
            try:
                container.wait(timeout=10)
            except subprocess.TimeoutExpired:
                container.terminate()
                container.wait(timeout=5)
        for f in logs:
            f.flush()
            os.fsync(f.fileno())
            f.close()
        put(C / 'controller-closure.json', {'atUTC': datetime.now(timezone.utc).isoformat(), 'failure': failure,
            'hostExit': host.poll() if host else None, 'dockerClientExit': container.poll() if container else None,
            'nativeCONNECTSentOnce': connected, 'nativeCloseRequested': closed, 'elapsedSeconds': time.monotonic()-began,
            'allPinnedInputsUnchanged': all(sha(n)==h for n,h in inputs.items()), 'flightCommandsSentByController': False,
            'scope': 'READ_ONLY_MINIMAL_NATIVE_EXTERNAL_SMOKE_NOT_M1_OR_BETA_ACCEPTANCE'})
    print(json.dumps({'failure': failure, 'connectIntentAttempted': connected, 'closedRequested': closed, 'path': str(O)}), flush=True)
    raise SystemExit(0 if failure is None else 1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    main()
