"""Bounded isolated idle AP probe. No MAVLink/arm/mode/mission control path."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, os, shutil, signal, socket, struct, subprocess, sys, time

R = Path(__file__).resolve().parents[2]
E = R / 'evidence/simtrain52-probe'
IMAGE = 'rtr-aeris-sim32-trace-builder:local'
NAME = 'aeris-simtrain52-idle-probe'
AP = R / 'runtime/sim32-instrument01-build/ardupilot/build/sitl/bin/arducopter'
sys.path[:0] = [str(R / 'pilot/sim32-pipe03'), str(R / 'pilot/sim32-journal04'),
                str(R / 'runtime/sim32-pipe03-build/host-native'), str(R / 'pilot/sim32')]


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()


def save(p, data):
    with p.open('x') as f: json.dump(data, f, indent=2); f.write('\n')


def command(args):
    return subprocess.check_output([str(x) for x in args], text=True, timeout=30).strip()


def backend(out):
    from fast_physics import Model, profile
    from wal_journal import Wal, encode
    from epoch import Epoch
    from clock_host import ClockObserver
    state = out / 'backend-state'; state.mkdir()
    model = Model(profile('empty', 'calm'))
    wal = Wal(out, {'source': 'ACTUAL_PINNED_AP_IDLE_PROBE', 'clockDomain': 'host-monotonic',
                    'epochScope': out.name, 'noFlightCommands': True}, limit=32*2**20)
    epoch = Epoch(state, out, out.name)
    clock = None; stopped = False; frames = 0; previous = None; peer = None; first = None; last = None
    error = None; stages = []
    def stop(*args):
        nonlocal stopped
        stopped = True
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('127.0.0.1', 9002)); s.settimeout(.1)
            clock = ClockObserver(out, out.name, epoch.id)
            save(out/'backend-ready.json', {'pid': os.getpid(), 'epoch': epoch.id, 'port': 9002})
            start = time.monotonic()
            while not stopped and frames < 4800:
                epoch.check()
                if clock.error: raise RuntimeError('CLOCK_OBSERVER:' + clock.error)
                if time.monotonic()-start > 25: raise RuntimeError('PROBE_DEADLINE')
                try: data, address = s.recvfrom(1024)
                except socket.timeout: continue
                rx = time.monotonic_ns()
                if stopped: save(out/'unadmitted-tail.json', {'rawHex': data.hex(), 'reason': 'STOP_OBSERVED'}); break
                if len(data) != 40: raise RuntimeError('SERVO_SHAPE')
                magic, rate, frame, *pwm = struct.unpack('<HHI16H', data)
                wal.append('RX', frame, encode({'source': 'ACTUAL_PINNED_AP_IDLE_PROBE', 'rawHex': data.hex(),
                                              'hostReceiveNs': rx, 'peer': address}))
                if magic != 18458 or rate != 1200: raise RuntimeError('SERVO_FORMAT_OR_RATE')
                if previous is not None and frame != previous+1: raise RuntimeError('FRAME_GAP_OR_DUPLICATE')
                if peer is not None and address != peer: raise RuntimeError('FOREIGN_PEER')
                epoch.check(); a = time.monotonic_ns()
                payload = ('\n'+json.dumps(model.step(pwm, 1/rate), separators=(',', ':'), allow_nan=False)+'\n').encode()
                computed = time.monotonic_ns()
                row = {'frame': frame, 'rate': rate, 'servoHex': data.hex(), 'sensorUtf8': payload.decode(),
                       'hostReceiveNs': rx, 'computeStartNs': a, 'computeEndNs': computed,
                       'modelAux': model.snapshot(), 'epoch': epoch.id, 'source': 'ACTUAL_AP_IDLE_NO_FLIGHT_COMMAND'}
                body = encode(row)
                wal.append('INTENT', frame, struct.pack('<II', len(body), 0)+body, flush=True)
                barrier = time.monotonic_ns(); epoch.check()
                returned = s.sendto(payload, address); sent = time.monotonic_ns()
                if returned != len(payload): raise RuntimeError('SEND_OUTCOME_UNKNOWN')
                wal.append('SENT', frame, encode({'returnedBytes': returned, 'expectedBytes': len(payload),
                                                'hostSendReturnNs': sent, 'observation': 'LOCAL_UDP_RETURN_NOT_EXECUTION'}))
                stages.append([frame, rx, a, computed, barrier, sent])
                previous = frame; peer = address; frames += 1; epoch.progress()
                if first is None: first = rx
                last = rx
                if frames % 200 == 0 and shutil.disk_usage(R).free < 20*2**30+512*2**20:
                    raise RuntimeError('RESOURCE_HEADROOM_LOST')
            wal.append('CLOSE', 0, encode({'intentAndSentFrames': frames, 'noAutomaticResume': True}), flush=True)
    except Exception as e:
        error = str(e)
    finally:
        if clock: clock.seal()
        epoch.close(); wal.close()
        save(out/'backend-stages.json', stages)
        wall = (last-first)/1e9 if frames > 1 else None
        save(out/'backend-result.json', {'status': 'CAPTURE_CLOSED' if error is None else 'FAILED', 'error': error,
              'frames': frames, 'activeReceiveWallSeconds': wall, 'modelSeconds': model.t,
              'idleReceiveRTF': (frames-1)/1200/wall if wall else None, 'epoch': epoch.id,
              'journalPolicy': 'fsync-before-publish', 'clockError': clock.error if clock else 'NOT_STARTED',
              'scope': 'Idle only; not armed, controlled flight, UI load,1x acceptance or hardware validation'})
    if error: raise SystemExit(1)


def launch(rid):
    assert rid.isalnum() and len(rid) <= 24
    assert shutil.disk_usage(R).free > 21.5*2**30, 'INHERITED_PEAK_FLOOR'
    assert subprocess.run(['docker','container','inspect',NAME],capture_output=True).returncode != 0
    for port, kind in [(9002,socket.SOCK_DGRAM),(9004,socket.SOCK_DGRAM),(9005,socket.SOCK_DGRAM)]:
        with socket.socket(socket.AF_INET,kind) as s: s.bind(('127.0.0.1',port))
    admission = json.loads((R/'evidence/simtrain52/admission1.json').read_text())
    for p, h in admission['pins'].items(): assert sha(R/p) == h, ('PIN',p)
    oracle = json.loads((R/'evidence/sim32-pipe03/integrator-oracle.json').read_text())
    assert oracle['status'] == 'PASS_EXACT_BYTES_ALL_INPUTS'
    for p, h in oracle['sourcePins'].items(): assert sha(R/p) == h
    image_id = command(['docker','image','inspect',IMAGE,'--format','{{.Id}}'])
    E.mkdir(exist_ok=True); out = E/rid; out.mkdir(); (out/'guest-state').mkdir()
    log = (out/'backend-console.txt').open('x')
    proc = subprocess.Popen([sys.executable,'-B',__file__,'backend',rid],stdout=log,stderr=subprocess.STDOUT,cwd=R)
    cid = None; failure = None; stop_info = None
    try:
        for _ in range(50):
            if (out/'backend-ready.json').exists(): break
            if proc.poll() is not None: raise RuntimeError('BACKEND_START_FAILED')
            time.sleep(.1)
        assert (out/'backend-ready.json').exists()
        args = ['docker','run','--rm','-d','--name',NAME,'--label','aeris.task=simtrain52-probe','--label','aeris.run='+rid,
                '--platform','linux/arm64','--pull','never','--network','bridge','--cpus','2','--memory','384m',
                '--cap-drop','ALL','--security-opt','no-new-privileges','--log-opt','max-size=2m',
                '-p','127.0.0.1:9004:9004/udp','-v',str(R/'runtime/sitl')+':/aeris:ro',
                '-v',str(AP)+':/aeris/arducopter:ro','-v',str(R/'pilot/sim32-pipe03')+':/instrument:ro',
                '-v',str(R/'pilot/sim32')+':/sim32:ro','-v',str(out)+':/evidence',
                '-v',str(out/'guest-state')+':/state','-e','AERIS_INSTRUMENT=1','-w','/state',IMAGE,
                '/bin/sh','/instrument/entry.sh','/aeris/arducopter','-w','--model','JSON:192.168.65.254',
                '--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/sim32/sitl.parm',
                '--serial0=tcp:5760:nowait','--rate','1200','--speedup','1']
        cid = command(args)
        save(out/'launch.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':args,
             'backendPid':proc.pid,'containerId':cid,'imageId':image_id,'apSha256':sha(AP),
             'driverSha256':sha(Path(__file__)),'rateHz':1200,'speedup':1,'negativeDebtCapUs':500000,
             'resourceFreeBytes':shutil.disk_usage(R).free,'peakBudgetBytes':int(1.5*2**30),
             'noFlightCommandEndpoint':True,'uiConnected':False,'noAutomaticRetry':True})
        proc.wait(timeout=30)
        if proc.returncode: raise RuntimeError('BACKEND_PROBE_FAILED')
    except Exception as e:
        failure = str(e)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait(); failure = 'BACKEND_MANAGED_CLOSE_FAILED'
        log.close()
        if cid:
            info=json.loads(command(['docker','container','inspect',NAME]))[0]
            assert info['Id']==cid and info['Config']['Labels']['aeris.run']==rid
            save(out/'container-before-stop.json',info)
            (out/'ap-console.txt').write_text(command(['docker','logs',NAME]))
            try: command(['docker','exec',NAME,'/instrument/traceflush','/evidence/ap-timing.bin'])
            except Exception as e: failure = 'TRACE_FLUSH_FAILED:'+str(e)
            stop_info=command(['docker','stop','-t','3',NAME])
        save(out/'closure.json',{'backendExited':proc.poll() is not None,'backendExitCode':proc.returncode,
             'ownedContainerStopped':bool(stop_info),'error':failure,'stateRetained':True,
             'freeBytes':shutil.disk_usage(R).free,'noFlightCommands':True})
        # Required disk hygiene; never prune volumes or containers.
        (out/'docker-image-prune.txt').write_text(command(['docker','image','prune','-f']))
    print(json.dumps({'out':str(out.relative_to(R)),'error':failure,'closed':bool(stop_info)}))
    if failure: raise SystemExit(1)


if __name__ == '__main__':
    mode, rid = sys.argv[1:3]
    if mode == 'backend': backend(E/rid)
    elif mode == 'launch': launch(rid)
    else: raise ValueError('backend|launch')
