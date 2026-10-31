"""Owned Linux parent: AP stdout + lossless pipe drain outlive AP termination."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import selectors
import signal
import subprocess
import time
from pilot.betaintegrated01.runtime.ap_stage import StageDrainer, canonical, exclusive
from pilot.betaintegrated01.control01.state_binding import validate_state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    binary = Path('/candidate/arducopter-m1-stagepipe-03')
    if hashlib.sha256(binary.read_bytes()).hexdigest() != config['APSHA256']:
        raise ValueError('AP_ARTIFACT_MISMATCH')
    if config['requestedSpeedup'] != 1 or config['capMs'] != 500:
        raise ValueError('PACER_POLICY')
    duration = config['maximumSeconds']
    if type(duration) is not int or duration not in (60,90,1960):
        raise ValueError('DURATION')
    variant=config['controlScenario']
    if variant not in ('nominal','loss') or set(config['parameterSHA256'])!={'copter.parm','control.parm'}:raise ValueError('CONTROL_PROFILE')
    for name, expected in config['parameterSHA256'].items():
        p = (Path('/control')/variant/'control.parm') if name=='control.parm' else Path('/candidate')/name
        if name not in ('copter.parm', 'control.parm') or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise ValueError('PARAMETER_BINDING')
    if hashlib.sha256(Path('/candidate/clockprobe').read_bytes()).hexdigest() != config['clockprobeSHA256']:
        raise ValueError('CLOCK_PROBE_BINDING')
    out = Path('/evidence')
    state_binding=validate_state(config,'/state',out)
    drainer = StageDrainer(out / 'ap-stage', config['run'], config['epoch'], config['boot'],
                           max_events=duration * 1200 * 10 + 10)
    readfd, writefd = os.pipe()
    os.set_blocking(readfd, False)
    command = [str(binary), *(['-w'] if config['wipeState'] else []), '--model', 'JSON:192.168.65.254', '--home', '10.854,106.807,10,0',
               '--defaults', '/candidate/copter.parm,/control/'+variant+'/control.parm', '--serial0=tcp:5760:nowait',
               '--serial1=tcp:5762:nowait', '--serial2=tcp:5763:nowait', '--sim-port-out', '9012',
               '--rate', '1200', '--speedup', '1']
    environment = {**os.environ, 'AERIS_STAGE_FD': str(writefd)}
    log = (out / 'ap-console.txt').open('xb')
    clock_log = (out / 'clock-probe-console.txt').open('xb')
    clock_child = subprocess.Popen(['/candidate/clockprobe'], stdout=clock_log, stderr=subprocess.STDOUT)
    clock_deadline = time.monotonic() + 10
    while not (out / 'clock-ready.json').exists():
        if time.monotonic() >= clock_deadline or clock_child.poll() is not None:
            clock_child.terminate()
            clock_child.wait(timeout=3)
            raise RuntimeError('HOST_CLOCK_BOOTSTRAP_NOT_OBSERVED')
        time.sleep(.02)
    clock_ready = json.loads((out / 'clock-ready.json').read_text())
    if any(clock_ready.get(key) != config[key] for key in ('run', 'epoch', 'boot')):
        clock_child.terminate()
        clock_child.wait(timeout=3)
        raise RuntimeError('FOREIGN_HOST_CLOCK_BOOTSTRAP')
    child = subprocess.Popen(command, cwd='/state', env=environment, pass_fds=(writefd,),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    os.set_blocking(child.stdout.fileno(), False)
    os.close(writefd)
    stopping = None
    reason = None
    error = None
    eof = False
    console_eof = False
    console_bytes = 0
    selector = selectors.DefaultSelector()
    selector.register(readfd, selectors.EVENT_READ, 'stage')
    selector.register(child.stdout.fileno(), selectors.EVENT_READ, 'console')
    start = time.monotonic()

    def request_stop(signum, frame):
        nonlocal stopping, reason
        if stopping is None:
            stopping, reason = time.monotonic(), 'OWNED_SIGNAL_' + str(signum)
            child.terminate()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    exclusive(out / 'ap-supervisor-launch.json', canonical({
        'run': config['run'], 'epoch': config['epoch'], 'boot': config['boot'],
        'supervisorPID': os.getpid(), 'APPID': child.pid, 'command': command,
        'APSHA256': config['APSHA256'], 'parameterSHA256': config['parameterSHA256'],
        'pipeParentOwned': True, 'maxEvents': duration * 1200 * 10 + 10,'stateBinding':state_binding}) + b'\n')
    try:
        while not eof or not console_eof:
            now = time.monotonic()
            if stopping is None and clock_child.poll() is not None:
                raise RuntimeError('CLOCK_PROBE_EXIT')
            if stopping is None and (out / 'backend-result.json').exists():
                raw_backend = (out / 'backend-result.json').read_bytes()
                if len(raw_backend) > 262144:
                    raise RuntimeError('HOST_BACKEND_RESULT_BOUND')
                try:
                    backend_result = json.loads(raw_backend)
                except json.JSONDecodeError:
                    backend_result = None  # Exclusive writer may still be writing.
                if backend_result is not None:
                    if any(backend_result.get(key) != config[key] for key in ('run', 'epoch', 'boot')):
                        raise RuntimeError('FOREIGN_HOST_BACKEND_RESULT')
                    stopping = now
                    reason = ('HOST_BACKEND_CAPTURE_CLOSED' if backend_result.get('status') == 'HOST_CAPTURE_CLOSED_NOT_FLIGHT_ACCEPTANCE'
                              else 'HOST_BACKEND_FAILED')
                    child.terminate()
            if stopping is None and now - start > duration + 15:
                stopping, reason = now, 'MAXIMUM_SUPERVISED_DURATION'
                child.terminate()
            if stopping is not None and now - stopping > 3 and child.poll() is None:
                child.kill()
            for key, mask in selector.select(.05):
                raw = os.read(key.fd, 65536)
                if key.data == 'console':
                    if not raw:
                        console_eof = True
                        selector.unregister(key.fd)
                    else:
                        log.write(raw)
                        console_bytes += len(raw)
                        if console_bytes > 8 * 2**20:
                            raise RuntimeError('AP_CONSOLE_CAPACITY_PREFIX_RETAINED')
                    continue
                if not raw:
                    eof = True
                    selector.unregister(key.fd)
                    continue
                drainer.feed(raw)
            if child.poll() is not None and not eof and stopping is None:
                stopping, reason = now, 'AP_EXIT_OBSERVED'
            if stopping is not None and now - stopping > 6 and not eof:
                raise RuntimeError('PIPE_EOF_NOT_OBSERVED')
        ap_exit = child.wait(timeout=3)
        terminal = drainer.finish(ap_exit=ap_exit, eof=eof)
    except Exception as exc:
        error = type(exc).__name__ + ':' + str(exc)
        try:
            drainer.fail(error)
        except Exception:
            pass
        if child.poll() is None:
            child.kill()
        ap_exit = child.wait(timeout=3)
        terminal = {'status': 'FAILED_RETAINED_AP_PREFIX', 'events': drainer.total, 'publicationAllowed': False}
    finally:
        selector.close()
        child.stdout.close()
        os.close(readfd)
        log.flush()
        os.fsync(log.fileno())
        log.close()
        if clock_child.poll() is None:
            clock_child.terminate()
        clock_exit = clock_child.wait(timeout=3)
        clock_log.flush()
        os.fsync(clock_log.fileno())
        clock_log.close()
    exclusive(out / 'ap-supervisor-result.json', canonical({
        'run': config['run'], 'epoch': config['epoch'], 'boot': config['boot'],
        'APExit': ap_exit, 'EOF': eof, 'stopReason': reason, 'error': error,
        'clockProbeExit': clock_exit,
        'APConsoleBytes': console_bytes, 'APConsoleBoundBytes': 8 * 2**20 + 65536,
        'terminal': terminal, 'parentDrainFinished': error is None,
        'APExecutionAccepted': False, 'publicationAllowed': False}) + b'\n')
    print(json.dumps({'run': config['run'], 'epoch': config['epoch'], 'boot': config['boot'],
                      'APExit': ap_exit, 'error': error, 'parentDrainFinished': error is None,
                      'terminalSHA256': terminal.get('terminalSHA256') if error is None else None,
                      'events': drainer.total,
                      'scope': 'LIVE_PARENT_CHANNEL_LOCAL_SYNC_ACK_NOT_REMOTE_AUTH'}), flush=True)
    raise SystemExit(1 if error else 0)


if __name__ == '__main__':
    main()
